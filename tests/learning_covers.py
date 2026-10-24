"""W-040: the sample's cover on the learning screens (편집 정거장 「표지 디자인」, 유통 정거장 「책 소개 자료」) is the shared
cover: same title / subtitle / copy / author / back headline as the studio's cover, drawn by the same renderer, no text
clipped, the photo not distorted; at 1440 and 390px. Also checks the deployed 책공방.html carries the same markup.
Usage: python tests/learning_covers.py <outdir>"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
fails, errors, rep = [], [], {}
COVER = """(root) => { const r = document.querySelector(root); if (!r) return null; const t = (s) => (r.querySelector(s)?.textContent || '').trim();
  const img = r.querySelector('.cv-front img, .cv-front .cv-photo img'); const clipped = [...r.querySelectorAll('.cv-title, .cv-sub, .cv-copy, .cv-author, .cv-headline')].filter(e => e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1).map(e => e.className);
  const fr = r.querySelector('.cv-front')?.getBoundingClientRect();
  return { title: t('.cv-title'), sub: t('.cv-sub'), copy: t('.cv-copy'), author: t('.cv-author'), headline: t('.cv-headline'), spine: t('.cv-spine-t'), renderer: !!r.querySelector('.cv-front'),
    img: img ? { nw: img.naturalWidth, nh: img.naturalHeight, fit: getComputedStyle(img).objectFit, w: Math.round(img.getBoundingClientRect().width), h: Math.round(img.getBoundingClientRect().height) } : null,
    front: fr ? [Math.round(fr.width), Math.round(fr.height)] : null, titlePx: parseFloat(getComputedStyle(r.querySelector('.cv-title') || r).fontSize), clipped }; }"""


def check(cond, msg):
    if not cond: fails.append(msg); print('  FAIL', msg)


def open_topic(pg, w, station_idx, topic):
    if w > 560: pg.locator('.pg-dot').nth(station_idx).click()
    else: pg.locator('.pgp-sum').click(); pg.locator('.pgp-list button').nth(station_idx).click()
    pg.wait_for_selector('.station-v7')
    if pg.locator('.tm-box').get_attribute('open') is None: pg.locator('.tm-sum').click()
    pg.locator('.tm-list button', has_text=topic).click(); pg.wait_for_timeout(500)


for fname in ('dist/index.html', '책공방.html'):
    URL = (LAB / fname).as_uri()
    with sync_playwright() as p:
        b = p.chromium.launch()
        for w, hh in [(1440, 900), (390, 844)]:
            pg = b.new_page(viewport={'width': w, 'height': hh}); pg.set_default_timeout(15000)
            pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
            pg.goto(URL); pg.wait_for_selector('.scene')
            # the studio's cover is the reference
            pg.locator('.pg-dot').last.click() if w > 560 else (pg.locator('.pgp-sum').click(), pg.locator('.pgp-list button').last.click())
            pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper'); pg.wait_for_timeout(600)
            pg.locator('.step').nth(7).click(); pg.wait_for_timeout(600)
            if w < 900: pg.locator('.view-tabs button').nth(1).click(); pg.wait_for_timeout(500)
            pg.locator('.flat-cover summary').click(); pg.wait_for_timeout(300)  # the studio's production flat cover: back + spine + front
            ref = pg.evaluate(COVER, '.preview .cover-row')
            pg.goto(URL); pg.wait_for_selector('.scene')
            key = f'{fname}@{w}'; rep[key] = {'studio': ref}
            for name, idx, topic, root in [('cover', 2, '표지 디자인', '.cvz-row'), ('promo', 4, '책 소개 자료', '.promo-cover')]:
                pg.goto(URL); pg.wait_for_selector('.scene')
                open_topic(pg, w, idx, topic)
                got = pg.evaluate(COVER, root); rep[key][name] = got
                pg.locator(root).screenshot(path=str(OUT / f'{"dist" if fname.startswith("dist") else "deploy"}-{w}-{name}.png'))
                check(got and got['renderer'], f'{key} {name}: not drawn by the shared cover renderer')
                if not got or not got['renderer']: continue
                for k in ('title', 'sub', 'copy', 'author'):
                    check(got[k] == ref[k], f'{key} {name}: {k} differs ({got[k]!r} vs studio {ref[k]!r})')
                check(not got['clipped'], f'{key} {name}: text clipped {got["clipped"]}')
                if got['img']:
                    check(got['img']['fit'] == 'cover' and got['img']['w'] > 0, f'{key} {name}: photo not shown with object-fit cover {got["img"]}')
                check(got['front'] and abs(got['front'][0] / got['front'][1] - 148 / 210) < 0.02, f'{key} {name}: front cover ratio {got["front"]}')
                if name == 'cover': check(got['headline'] == ref['headline'] and got['spine'] == ref['spine'], f'{key} cover: back headline / spine differ')
                print(key, name, 'front', got['front'], 'title px', round(got['titlePx'], 1), 'copy', got['copy'][:12])
            check(pg.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth') == 0, f'{key}: horizontal scroll')
            pg.close()
        b.close()
(OUT / 'covers.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
print('errors:', errors or 0)
print('FAIL' if fails or errors else 'PASS', *fails, sep='\n')
sys.exit(1 if fails or errors else 0)
