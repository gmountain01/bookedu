"""Check the 'why' and 'next' process slides: find them in the main track, measure size/overflow/min font,
save screenshots. Usage: python tests/slides_check.py [outdir]"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else LAB / 'docs' / 'evidence' / 'slides'
OUT.mkdir(parents=True, exist_ok=True)
WANT = {'만드는 과정은 멀다': 'why', '보완할 점과 다음 계획': 'next'}
MEASURE = """() => { const s = document.querySelector('.slide'); const r = s.getBoundingClientRect();
  const z = r.width / s.offsetWidth;
  const over = [...s.querySelectorAll('*')].filter((e) => e.scrollHeight > e.clientHeight + 2 && getComputedStyle(e).overflow !== 'visible').length
    + [...s.querySelectorAll('*')].filter((e) => { const b = e.getBoundingClientRect(); return b.width && (b.right > r.right + 1 || b.bottom > r.bottom + 1); }).length;
  const fonts = [...s.querySelectorAll('*')].filter((e) => e.childNodes.length && [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()))
    .map((e) => parseFloat(getComputedStyle(e).fontSize) * z);
  return { title: s.innerText.slice(0, 120), w: s.offsetWidth, h: s.offsetHeight, overflow: over, minFontPx: Math.round(Math.min(...fonts) * 10) / 10 }; }"""

errors, found = [], []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(URL)
    pg.wait_for_selector('.scene')
    pg.get_by_role('button', name='관리자 모드').click()
    pg.wait_for_selector('.slide')
    pg.keyboard.press('Home')
    total = int(pg.locator('.deck-count').inner_text().split('/')[-1])
    for i in range(total):
        pg.wait_for_timeout(150)
        text = pg.locator('.slide').inner_text()
        for key, name in WANT.items():
            if key in text and name not in {f['id'] for f in found}:
                m = pg.evaluate(MEASURE)
                m.update(id=name, counter=pg.locator('.deck-count').inner_text())
                pg.locator('.slide').screenshot(path=str(OUT / f'{name}-{i + 1:02d}.png'))
                found.append(m)
        pg.keyboard.press('ArrowRight')
    b.close()

(OUT / 'slides.json').write_text(json.dumps({'found': found, 'errors': errors}, ensure_ascii=False, indent=2), encoding='utf-8')
for f in found:
    print(f['id'], f['counter'], f"{f['w']}x{f['h']}", 'overflow', f['overflow'], 'minFont', f['minFontPx'])
print('console errors:', errors or 'none')
assert {f['id'] for f in found} == set(WANT.values()), 'slide missing'
assert all(f['overflow'] == 0 and (f['w'], f['h']) == (1280, 720) for f in found)
