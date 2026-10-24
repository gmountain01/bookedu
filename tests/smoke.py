"""Smoke check: open dist/index.html via file:// (double-click equivalent), visit all routes,
collect console errors, save screenshots. Usage: python tests/smoke.py [outdir]"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else LAB / 'docs' / 'evidence' / 'smoke'
OUT.mkdir(parents=True, exist_ok=True)

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(URL)
    pg.wait_for_selector('.scene')
    pg.screenshot(path=str(OUT / 'journey.png'), full_page=True)
    pg.locator('.pg-dot').last.click()
    pg.get_by_role('button', name='예시 책으로 시작하기').first.click()
    pg.wait_for_selector('.stepper')
    pg.wait_for_timeout(400)
    pg.screenshot(path=str(OUT / 'studio-step1.png'))
    for n in range(2, 9):
        pg.locator('.step').nth(n - 1).click()
        pg.wait_for_timeout(250)
        pg.screenshot(path=str(OUT / f'studio-step{n}.png'))
    pg.get_by_role('button', name='관리자 모드').click()
    pg.wait_for_selector('.slide')
    pg.screenshot(path=str(OUT / 'admin-process.png'))
    pg.keyboard.press('ArrowRight')
    pg.screenshot(path=str(OUT / 'admin-process-2.png'))
    pg.goto(URL + '#/admin/prompts')
    pg.wait_for_selector('.slide')
    pg.screenshot(path=str(OUT / 'admin-prompts.png'))
    b.close()

print('console errors:', errors or 'none')
sys.exit(1 if errors else 0)
