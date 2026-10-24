"""W-033 / MT-16: screen-side checks of the book views (fresh profiles).
1440x900 and 390x844: step 3 replacement notice inside the viewport after a design change (with the student's own
size set first); the preview page bottom inside the window (wide); a zoom change keeps the page; the panning page
is not cut at the bottom; completed-book dialog page inside the dialog; step 3 sample body text size.
Usage: python tests/book_ux.py"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
fails, errors, rows = [], [], []


def check(ok, msg):
    rows.append(('ok  ' if ok else 'FAIL') + ' ' + msg)
    if not ok:
        fails.append(msg)


with sync_playwright() as p:
    b = p.chromium.launch()
    for w, hh in [(1440, 900), (390, 844)]:
        pg = b.new_page(viewport={'width': w, 'height': hh}); pg.set_default_timeout(15000)
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.goto(URL); pg.wait_for_selector('.scene')
        if w > 560: pg.locator('.pg-dot').last.click()
        else: pg.locator('.pgp-sum').click(); pg.locator('.pgp-list button').last.click()
        pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper')
        pg.locator('.step').nth(2).click(); pg.wait_for_timeout(500)
        pg.locator('.dz-detail select').first.select_option('12')
        pg.locator('.dz-choice', has_text='사진·기록').click(); pg.wait_for_timeout(500)
        r = pg.evaluate("(() => { const n = document.querySelector('.dz-notice'); if (!n) return null; const b = n.getBoundingClientRect(); return [b.top, b.bottom]; })()")
        check(r is not None and r[0] >= 0 and r[1] <= hh, f'{w}: replacement notice in view {r}')
        sample = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.dz-page .bk-p')).fontSize) * (document.querySelector('.dz-page').getBoundingClientRect().width / document.querySelector('.dz-page').offsetWidth)")
        rows.append(f'info {w}: step 3 sample body {sample:.2f}px')
        if w < 900:
            pg.locator('.view-tabs button').nth(1).click(); pg.wait_for_timeout(500)
        pv = pg.locator('.preview')
        if w > 900:
            bottom = pg.evaluate("document.querySelector('.preview .rd-view').getBoundingClientRect().bottom")
            check(bottom <= hh, f'{w}: preview page bottom {bottom:.0f} within the {hh}px window')
        # zoom keeps the page
        pg.locator('.preview .rd-turn').nth(1).click(); pg.wait_for_timeout(500)
        pg.locator('.preview .rd-turn').nth(1).click(); pg.wait_for_timeout(500)
        before = pv.locator('.rd-where').inner_text()
        pg.locator('.preview .rd-zoom').select_option('read' if w < 900 else 'fit'); pg.wait_for_timeout(700)
        after = pv.locator('.rd-where').inner_text()
        check(before.split(' /')[0].split('–')[0] == after.split(' /')[0].split('–')[0], f'{w}: zoom keeps the page ({before} -> {after})')
        crop = pg.evaluate("(() => { const s = document.querySelector('.preview .rd-view'); return s.classList.contains('pan') ? 0 : s.scrollHeight - s.clientHeight; })()")
        check(crop <= 1, f'{w}: page not cut at the bottom (scrollHeight - clientHeight = {crop})')
        if w < 900:
            pg.locator('.view-tabs button').nth(0).click()
        pg.locator('.step').nth(7).click(); pg.wait_for_timeout(300)
        pg.locator('.finish-row').get_by_role('button', name='완성본 보기').click(); pg.wait_for_selector('dialog[open]'); pg.wait_for_timeout(700)
        d = pg.evaluate("(() => { const s = document.querySelector('dialog .rd-win').getBoundingClientRect(); const dl = document.querySelector('dialog').getBoundingClientRect(); return [s.bottom, dl.bottom]; })()")
        check(d[0] <= d[1] + 1, f'{w}: completed-book page bottom {d[0]:.0f} inside the dialog ({d[1]:.0f})')
        check(pg.evaluate("document.activeElement.textContent") == '닫기', f'{w}: dialog focus on 닫기')
        pg.close()
    b.close()
print('\n'.join(rows))
print('console/page errors:', errors or 0)
sys.exit(1 if fails or errors else 0)
