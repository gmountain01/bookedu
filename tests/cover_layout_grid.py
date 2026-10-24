"""W-041: the cover layout picker (.cvl-grid) in step 8. Across viewport widths 1920 → 901 (and 768, 390): every card
holds its 141px cover thumbnail without overflow, cards never overlap, the grid never scrolls sideways, the column count
follows the panel width; choosing a layout updates the cover in the preview (data-layout / class) at once; the thumbnail
keeps the 148:210 ratio; names stay readable (not clipped). Usage: python tests/cover_layout_grid.py <outdir>"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
fails = []
M = """() => { const g = document.querySelector('.cvl-grid'); const cards = [...g.querySelectorAll('.cvl-choice')].map(c => { const r = c.getBoundingClientRect(), th = c.querySelector('.cvs-page').getBoundingClientRect(), nm = c.querySelector('b');
  const over = [...c.querySelectorAll('*')].some(e => { const k = e.getBoundingClientRect(); return k.width && (k.right > r.right + 1 || k.left < r.left - 1); });
  return { l: r.left, r: r.right, t: r.top, b: r.bottom, w: Math.round(r.width), thumb: [Math.round(th.width), Math.round(th.height)], over, nameClipped: nm.scrollWidth > nm.clientWidth + 1 }; });
  const overlap = cards.some((a, i) => cards.some((b, j) => i < j && a.l < b.r - 1 && b.l < a.r - 1 && a.t < b.b - 1 && b.t < a.b - 1));
  return { gridW: Math.round(g.getBoundingClientRect().width), cols: getComputedStyle(g).gridTemplateColumns.split(' ').length, cards, overlap, sideways: g.scrollWidth > g.clientWidth + 1, page: document.documentElement.scrollWidth - document.documentElement.clientWidth }; }"""


def check(c, m):
    if not c: fails.append(m); print('  FAIL', m)


with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1440, 'height': 900}); pg.set_default_timeout(15000)
    pg.goto(URL); pg.wait_for_selector('.scene'); pg.locator('.pg-dot').last.click()
    pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper'); pg.wait_for_timeout(500)
    pg.locator('.step').nth(7).click(); pg.wait_for_timeout(500)
    for w in list(range(1920, 900, -40)) + [901, 768, 390]:
        pg.set_viewport_size({'width': w, 'height': 900}); pg.wait_for_timeout(250)
        if w < 900 and pg.locator('.view-tabs button').first.is_visible(): pg.locator('.view-tabs button').nth(0).click()
        m = pg.evaluate(M)
        bad = [c for c in m['cards'] if c['over'] or c['nameClipped'] or abs(c['thumb'][0] / c['thumb'][1] - 148 / 210) > 0.02]
        check(not bad and not m['overlap'] and not m['sideways'] and m['page'] == 0, f'{w}px: grid {m["gridW"]}px, {m["cols"]} cols, overflow/clip {len(bad)}, overlap {m["overlap"]}, sideways {m["sideways"]}, page scroll {m["page"]}')
        check(m['cols'] * 168 + (m['cols'] - 1) * 10 <= m['gridW'] + 1, f'{w}px: {m["cols"]} columns do not fit {m["gridW"]}px')
        if w in (1920, 1440, 1280, 1180, 1024, 901, 768, 390): pg.locator('.cvl-grid').scroll_into_view_if_needed(); pg.locator('.cvl-grid').screenshot(path=str(OUT / f'{w}.png')); print(w, 'grid', m['gridW'], 'cols', m['cols'], 'card', m['cards'][0]['w'])
    # choosing a layout updates the cover in the preview
    pg.set_viewport_size({'width': 1440, 'height': 900}); pg.wait_for_timeout(300)
    for v in ('band', 'panel', 'full'):
        pg.locator(f'.cvl-choice input[value="{v}"]').check(force=True); pg.wait_for_timeout(600)
        got = pg.evaluate("document.querySelector('.preview .cv-front')?.dataset.layout || [...document.querySelector('.preview .cv-front').classList].join(' ')")
        check(v in got, f'layout {v} not reflected in the preview cover ({got})')
    b.close()
print('FAIL' if fails else 'PASS', *fails, sep='\n'); sys.exit(1 if fails else 0)
