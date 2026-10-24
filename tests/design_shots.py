"""Design review screenshots of the main screens at 1440 / 768 / 390 px, in a fresh (isolated) browser
profile so no real student data is touched. Also reports horizontal overflow per screen.
Usage: python tests/design_shots.py <outdir>"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
HSCROLL = 'document.documentElement.scrollWidth - document.documentElement.clientWidth'
report, errors = [], []


def shot(pg, name, full=False):
    pg.wait_for_timeout(350)
    pg.screenshot(path=str(OUT / f'{name}.png'), full_page=full)
    report.append({'shot': name, 'hscroll_px': pg.evaluate(HSCROLL)})


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    for w, hgt in [(1440, 900), (768, 1024), (390, 844)]:
        ctx = b.new_context(viewport={'width': w, 'height': hgt})
        ctx.add_init_script('window.print = () => {};')
        pg = ctx.new_page()
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.goto(URL); pg.wait_for_selector('.scene')
        shot(pg, f'{w}-journey-intro')
        stage = lambda k: pg.locator('.pg-dot').nth(k).click() if w > 560 else (pg.locator('.pgp-sum').click(), pg.locator('.pgp-list button').nth(k).click())
        stage(1); shot(pg, f'{w}-journey-station1')
        stage(5); shot(pg, f'{w}-journey-numbers')
        stage(7); shot(pg, f'{w}-journey-finish')
        pg.get_by_role('button', name='예시 책으로 시작하기').first.click()
        pg.wait_for_selector('.stepper')
        shot(pg, f'{w}-studio-step1')
        pg.locator('.step').nth(1).click(); shot(pg, f'{w}-studio-step2')
        if w < 900:
            pg.locator('.view-tabs button').nth(1).click(); shot(pg, f'{w}-studio-step2-preview')
            pg.locator('.view-tabs button').nth(0).click()
        pg.locator('.step').nth(7).click(); shot(pg, f'{w}-studio-step8')
        shot(pg, f'{w}-studio-step8-full', full=True)
        if w < 900:
            pg.locator('.view-tabs button').nth(1).click(); shot(pg, f'{w}-studio-step8-preview')
            pg.locator('.view-tabs button').nth(0).click()
        files = pg.locator('.file-menu > summary, .file-actions')
        if pg.locator('.file-menu > summary').count():
            pg.locator('.file-menu > summary').click(); shot(pg, f'{w}-studio-filemenu')
            pg.keyboard.press('Escape')
        pg.get_by_role('button', name='완성본 보기').first.click()
        pg.wait_for_selector('dialog[open]'); shot(pg, f'{w}-book-dialog')
        pg.keyboard.press('Escape')
        pg.get_by_role('button', name='관리자 모드').click(); pg.wait_for_selector('.slide')
        shot(pg, f'{w}-deck-cover')
        for _ in range(3): pg.keyboard.press('ArrowRight')
        shot(pg, f'{w}-deck-4')
        ctx.close()
    b.close()

(OUT / 'shots.json').write_text(json.dumps({'report': report, 'errors': errors}, ensure_ascii=False, indent=2), encoding='utf-8')
bad = [r for r in report if r['hscroll_px'] > 0]
print(len(report), 'shots; horizontal overflow:', bad or 'none', '; console errors:', errors or 'none')
