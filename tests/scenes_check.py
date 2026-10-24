"""W-036: collaboration scenes in 「함께 일하는 장면」 (fresh profiles). For each station that has scenes: screenshot the
topic at 1440x900 and 390x844; check every scene has a picture (not a blank), a role label with a name, one action
sentence and a work-state line; pictures are at least 240px wide on screen (not squeezed); no horizontal scroll;
the old hand-off list is still reachable in the disclosure. Usage: python tests/scenes_check.py <outdir>"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
edu = json.loads((LAB / 'src' / 'data' / 'education.json').read_text(encoding='utf-8'))
fails, errors = [], []
with sync_playwright() as p:
    b = p.chromium.launch()
    for w, hh in [(1440, 900), (390, 844)]:
        pg = b.new_page(viewport={'width': w, 'height': hh}); pg.set_default_timeout(15000)
        pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.goto(URL); pg.wait_for_selector('.scene')
        for k, ph in enumerate(edu['phases'], start=1):
            if not ph.get('scenes'):
                continue
            if w > 560: pg.locator('.pg-dot').nth(k).click()
            else: pg.locator('.pgp-sum').click(); pg.locator('.pgp-list button').nth(k).click()
            pg.wait_for_selector(f'.station-v7.st-{ph["id"]}')
            if pg.locator('.tm-box').get_attribute('open') is None: pg.locator('.tm-sum').click()
            pg.locator('.tm-list button', has_text='함께 일하는 장면').click(); pg.wait_for_timeout(500)
            r = pg.evaluate("""() => [...document.querySelectorAll('.scn-item')].map(li => { const img = li.querySelector('.scn-img');
              return { img: !!img && img.naturalWidth > 0, w: img ? Math.round(img.getBoundingClientRect().width) : 0, roles: li.querySelectorAll('.scn-role').length,
                       act: (li.querySelector('.scn-act')?.textContent || '').trim(), work: (li.querySelector('.scn-work')?.textContent || '').trim() }; })""")
            n = len(ph['scenes']['steps'])
            where = f"{w} {ph['id']}"
            if len(r) != n: fails.append(f'{where}: {len(r)} scenes, expected {n}')
            for i, s in enumerate(r, 1):
                if not s['img']: fails.append(f'{where} scene {i}: no picture')
                if s['w'] < 240: fails.append(f'{where} scene {i}: picture only {s["w"]}px wide')
                if not s['roles'] or not s['act'] or not s['work']: fails.append(f'{where} scene {i}: missing role/action/work')
            if pg.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth') > 0: fails.append(f'{where}: horizontal scroll')
            if not pg.locator('.scn-more summary').count(): fails.append(f'{where}: hand-off list not reachable')
            pg.locator('.scn').screenshot(path=str(OUT / f'{w}-{ph["id"]}-scenes.png'))
            print(where, len(r), 'scenes, picture widths', [s['w'] for s in r])
        pg.close()
    b.close()
print('errors:', errors or 0)
print('FAIL' if fails or errors else 'PASS', *fails, sep='\n')
sys.exit(1 if fails or errors else 0)
