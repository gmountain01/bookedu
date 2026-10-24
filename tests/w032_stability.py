"""W-032 (Plan v9 + MT-13): core/details and layout stability on every sub-step, fresh profile, file:// build.
Per sub-step at 1440x900 and 390x844 (top of the screen, nothing scrolled): title / points / picture top and the
다음 button's box. Checks: 다음 is inside the first screen on every sub-step (sticky pager), the title stays put,
points come before the picture on phones, numbered pins sit inside the revised text, 표 1 is a table,
「자세히 보기」 is never empty, role figures are drawings (no initial badge), no horizontal scroll, no console errors.
Usage: python tests/w032_stability.py [outdir]"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else LAB / 'docs' / 'evidence' / 'c16' / 'stability'
OUT.mkdir(parents=True, exist_ok=True)
edu = json.loads((LAB / 'src' / 'data' / 'education.json').read_text(encoding='utf-8'))
HS = 'document.documentElement.scrollWidth - document.documentElement.clientWidth'
TOP = lambda sel: f"(() => {{ const e = document.querySelector('{sel}'); return e ? Math.round(e.getBoundingClientRect().top) : null; }})()"
rows, errors, fails = [], [], []


def check(ok, msg):
    if not ok:
        fails.append(msg)


with sync_playwright() as p:
    b = p.chromium.launch()
    for w, hh in [(1440, 900), (390, 844)]:
        pg = b.new_page(viewport={'width': w, 'height': hh})
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.goto(URL); pg.wait_for_selector('.scene')
        for k, ph in enumerate(edu['phases'], start=1):
            if w > 560:
                pg.locator('.pg-dot').nth(k).click()
            else:
                pg.locator('.pgp-sum').click(); pg.locator('.pgp-list button').nth(k).click()
            pg.wait_for_selector(f'.station-v7.st-{ph["id"]}')
            for i, s in enumerate(ph['substeps']):
                if pg.locator('.tm-box').get_attribute('open') is None:
                    pg.locator('.tm-sum').click()
                pg.locator('.tm-sub button').nth(i).click()
                pg.evaluate('window.scrollTo(0, 0)'); pg.wait_for_timeout(60)
                nb = pg.locator('.tp-pager .btn').last.bounding_box()
                r = {'w': w, 'id': s['id'], 'title': pg.evaluate(TOP('.tp-title')), 'points': pg.evaluate(TOP('.sc-points')),
                     'vis': pg.evaluate(TOP('.sc-vis')), 'next_bottom': round(nb['y'] + nb['height']),
                     'height': pg.evaluate('document.documentElement.scrollHeight')}
                rows.append(r)
                where = f"{w} {s['id']}"
                check(r['next_bottom'] <= hh, f'{where}: 다음 below the first screen ({r["next_bottom"]})')
                if w <= 560:
                    check(r['points'] < r['vis'], f'{where}: points after the picture')
                    pt = pg.evaluate(TOP('.tp-pager'))
                    r['pager_top'] = pt
                    check(r['vis'] + 40 <= pt, f'{where}: picture top hidden under the pager ({r["vis"]} vs {pt})')
                check(pg.evaluate(HS) <= 0, f'{where}: horizontal scroll')
                check(pg.locator('.sc-who .fig-ph').count() == 0, f'{where}: initial badge instead of a figure')
                check(pg.locator('.sc-more-b > *').count() > 0, f'{where}: empty 자세히 보기')
                check('null' not in pg.locator('main').inner_text(), f'{where}: null')
                if s['id'] == 'plan-5':
                    check(pg.locator('.cf-p.after .pin-m').count() == 3, f'{where}: 3 pins in the revised text')
                    check(pg.locator('.cf-p.after table.cf-table tr').count() == 3, f'{where}: 표 1 as a 3-row table')
                if s['id'] in ('plan-5', 'market-1', 'edit-4', 'print-3'):
                    pg.screenshot(path=str(OUT / f'{s["id"]}-{w}.png'), full_page=False)
        pg.close()
    b.close()

ys = {w: sorted({r['title'] for r in rows if r['w'] == w}) for w in (1440, 390)}
for w in (1440, 390):
    nbs = [r['next_bottom'] for r in rows if r['w'] == w]
    print(f'{w}: title y {ys[w]}, 다음 bottom {min(nbs)}–{max(nbs)}')
check(len(ys[1440]) == 1, f'1440 title moves: {ys[1440]}')
check(len(ys[390]) == 1, f'390 title moves: {ys[390]}')
(OUT / 'measure.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
print('console/page errors:', errors or 0)
print('FAIL' if fails or errors else 'PASS', *fails, sep='\n')
sys.exit(1 if fails or errors else 0)
