"""W-037: the 「기본 사진에서 고르기」 cards in studio step 4 (fresh profile, built dist/index.html).
At 1440, 768 and 390px: every thumbnail shows the whole photo at its own aspect ratio (no stretch, no crop), the cards
sit in one grid with equal widths >= 150px, the card heights stay bounded (long descriptions are clamped), nothing
overflows the card or the page; landscape and portrait photos are both present. Also checks the inserted body image
in the preview keeps its ratio. Usage: python tests/builtin_cards.py <outdir>"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
MEASURE = """() => [...document.querySelectorAll('.builtin')].map(b => {
  const img = b.querySelector('img'), r = img.getBoundingClientRect(), cs = getComputedStyle(img);
  const nw = img.naturalWidth, nh = img.naturalHeight, fit = cs.objectFit;
  // the drawn picture inside the img box: contain/scale-down keep the ratio; fill stretches; cover crops
  let drawnRatio = r.width / r.height, cropped = false;
  if (fit === 'contain' || fit === 'scale-down') drawnRatio = nw / nh;
  if (fit === 'cover' && Math.abs((r.width / r.height) / (nw / nh) - 1) > 0.01) { drawnRatio = nw / nh; cropped = true; }
  const card = b.getBoundingClientRect();
  const kids = [...b.querySelectorAll('*')].filter(e => { const k = e.getBoundingClientRect(); return k.right > card.right + 0.5 || k.left < card.left - 0.5 || k.bottom > card.bottom + 0.5; }).length;
  return { key: b.dataset.key, nw, nh, orient: nw >= nh ? 'landscape' : 'portrait', box: [Math.round(r.width), Math.round(r.height)], fit,
           distortion: +(drawnRatio / (nw / nh) - 1).toFixed(3), cropped, card: [Math.round(card.width), Math.round(card.height)], outside: kids,
           nameCut: (n => n.scrollWidth > n.clientWidth + 1)(b.querySelector('.bi-name')),
           desc: b.querySelector('small')?.scrollHeight > b.querySelector('small')?.clientHeight + 1 ? 'clamped' : 'full' };
})"""
fails, errors, report = [], [], {}
with sync_playwright() as p:
    b = p.chromium.launch()
    for w, hh in [(1440, 900), (768, 1024), (390, 844)]:
        pg = b.new_page(viewport={'width': w, 'height': hh}); pg.set_default_timeout(15000)
        pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.goto(URL + '#/studio'); pg.wait_for_selector('.stepper')
        pg.locator('.step').nth(3).click(); pg.wait_for_selector('.builtin img')
        pg.wait_for_function("[...document.querySelectorAll('.builtin img')].every(i => i.complete && i.naturalWidth)")
        r = pg.evaluate(MEASURE); report[w] = r
        for c in r:
            if abs(c['distortion']) > 0.01: fails.append(f"{w} {c['key']}: picture distorted {c['distortion']:+.1%}")
            if c['nameCut']: fails.append(f"{w} {c['key']}: name cut off")
            if c['cropped']: fails.append(f"{w} {c['key']}: picture cropped")
            if c['outside']: fails.append(f"{w} {c['key']}: {c['outside']} element(s) outside the card")
            if c['card'][0] < 150: fails.append(f"{w} {c['key']}: card only {c['card'][0]}px wide")  # two columns on a 390px phone
        widths = {c['card'][0] for c in r}; heights = [c['card'][1] for c in r]
        if max(widths) - min(widths) > 1: fails.append(f'{w}: unequal card widths {sorted(widths)}')
        if max(heights) - min(heights) > 2: fails.append(f'{w}: unequal card heights {heights}')
        if max(heights) > max(c['card'][0] for c in r) * 1.6: fails.append(f'{w}: cards too tall {max(heights)}px')
        if {c['orient'] for c in r} != {'landscape', 'portrait'}: fails.append(f'{w}: need both landscape and portrait photos')
        if pg.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth') > 0: fails.append(f'{w}: horizontal page scroll')
        pg.locator('.builtins').screenshot(path=str(OUT / f'{w}-builtins.png'))
        # one insertion: the stored asset and the preview figure keep the photo's own ratio
        if w == 1440:
            key = next(c['key'] for c in r if c['orient'] == 'portrait')
            pg.locator(f'.builtin[data-key="{key}"]').click(); pg.wait_for_timeout(300)
            lib = pg.evaluate("() => { const i = document.querySelector('.library .asset:last-child img'); return i ? [i.naturalWidth, i.naturalHeight] : null; }")
            nat = next(c for c in r if c['key'] == key)
            if not lib or abs(lib[0] / lib[1] - nat['nw'] / nat['nh']) > 0.01: fails.append(f'inserted asset ratio changed: {lib} vs {nat["nw"]}x{nat["nh"]}')
        print(w, json.dumps([(c['key'], c['orient'], c['box'], c['fit'], c['distortion'], c['card'], c['desc']) for c in r], ensure_ascii=False))
        pg.close()
    b.close()
(OUT / 'measure.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
print('errors:', errors or 0)
print('FAIL' if fails or errors else 'PASS', *fails, sep='\n')
sys.exit(1 if fails or errors else 0)
