"""W-044: in 「한눈에 보기」 (roles view) the pass arrows (.rl-pass) between the stage columns must not move when 「하는 일 더 보기」
opens or closes; the expanded text must not overlap figures or arrows and must not be clipped. PC (1440, 1024) and
phone (390): open one, open all, close all. Usage: python tests/overview_arrows.py <outdir> [before]"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
BEFORE = len(sys.argv) > 2 and sys.argv[2] == 'before'
fails, rep = [], {}
ARROWS = "() => [...document.querySelectorAll('.rl-pass')].map(e => Math.round(e.querySelector('.mp-arrow').getBoundingClientRect().top + scrollY))"
OVERLAP = """() => { const boxes = [...document.querySelectorAll('.rl-row .fig-md, .rl-pass .mp-arrow, .rl-card strong')].map(e => e.getBoundingClientRect());
  const notes = [...document.querySelectorAll('.rl-more[open] > p, .rl-note:not([hidden])')].map(e => e.getBoundingClientRect());
  const hit = notes.some(n => boxes.some(b => n.left < b.right - 1 && b.left < n.right - 1 && n.top < b.bottom - 1 && b.top < n.bottom - 1));
  const clipped = [...document.querySelectorAll('.rl-more[open] > p, .rl-note:not([hidden])')].some(e => e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1);
  return { hit, clipped, open: notes.length, sideways: document.documentElement.scrollWidth - document.documentElement.clientWidth }; }"""


def check(c, m):
    if not c: fails.append(m); print('  FAIL', m)


with sync_playwright() as p:
    b = p.chromium.launch()
    for w, hh in [(1440, 900), (1024, 800), (390, 844)]:
        pg = b.new_page(viewport={'width': w, 'height': hh}); pg.set_default_timeout(15000)
        pg.goto(URL); pg.wait_for_selector('.scene')
        if w > 560: pg.locator('.pg-dot').nth(1).click()
        else: pg.locator('.pgp-sum').click(); pg.locator('.pgp-list button').nth(1).click()
        pg.wait_for_selector('.station-v7'); pg.locator('.tm-map').click(); pg.wait_for_timeout(500)
        if pg.locator('.rl-row').count() == 0:
            # the roles view is a tab of the overview
            pg.get_by_role('button', name='함께 일하는 사람들', exact=False).first.click(); pg.wait_for_timeout(500)
        toggles = pg.locator('.rl-more summary, .rl-more-btn')
        n = toggles.count(); check(n > 0, f'{w}: no 하는 일 더 보기 toggles found')
        a0 = pg.evaluate(ARROWS); rep[w] = {'closed': a0}
        pg.locator('.rl-row').screenshot(path=str(OUT / f'{w}-closed.png'))
        toggles.first.click(); pg.wait_for_timeout(300); a1 = pg.evaluate(ARROWS); o1 = pg.evaluate(OVERLAP)
        pg.locator('.rl-row').screenshot(path=str(OUT / f'{w}-one-open.png'))
        for i in range(1, n): toggles.nth(i).click()
        pg.wait_for_timeout(300); a2 = pg.evaluate(ARROWS); o2 = pg.evaluate(OVERLAP)
        pg.locator('.rl-row').screenshot(path=str(OUT / f'{w}-all-open.png'))
        for i in range(n): toggles.nth(i).click()
        pg.wait_for_timeout(300); a3 = pg.evaluate(ARROWS)
        rep[w].update({'one': a1, 'all': a2, 'closed_again': a3, 'overlap_one': o1, 'overlap_all': o2})
        moved = [i for i, (x, y) in enumerate(zip(a0, a2)) if abs(x - y) > 1] if w > 560 else []
        print(w, 'arrows closed', a0, 'one open', a1, 'all open', a2, 'moved', moved, 'overlap', o1['hit'] or o2['hit'], 'clipped', o1['clipped'] or o2['clipped'])
        if not BEFORE:
            if w > 560: check(not moved and a0 == a1, f'{w}: arrows moved when details opened {a0} -> {a1} -> {a2}')
            check(not (o1['hit'] or o2['hit']), f'{w}: expanded text overlaps a figure, name or arrow')
            check(not (o1['clipped'] or o2['clipped']), f'{w}: expanded text clipped')
            check(o2['open'] == n, f'{w}: {o2["open"]} notes open after opening all {n}')
            check(a3 == a0, f'{w}: arrows did not return after closing {a0} -> {a3}')
            check(o2['sideways'] == 0, f'{w}: horizontal scroll')
        pg.close()
    b.close()
(OUT / 'arrows.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
print('BEFORE (no assertions)' if BEFORE else ('FAIL' if fails else 'PASS'), *fails, sep='\n'); sys.exit(1 if fails else 0)
