"""W-042: on PC the step-8 preview stays in view while the cover form scrolls. At 1366x768, 1440x900, 1920x1080 and
1280x720: the panel is sticky (not static), fits under the header (bottom <= window), the page and the page bar stay on
screen at every scroll position of the form, the preview never overlaps the content below the workbench; a change at the
bottom of the form (copy text) shows in the cover at once; steps 2 and 5 keep their sticky preview; 390px keeps the
vertical layout. Usage: python tests/step8_sticky.py <outdir>"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
fails, rep = [], {}
ST = """() => { const pv = document.querySelector('.preview'), r = pv.getBoundingClientRect(), v = document.querySelector('.preview .rd-view').getBoundingClientRect(), nav = document.querySelector('.preview .rd-nav').getBoundingClientRect();
  const hdr = document.querySelector('header, .topbar, .app-head')?.getBoundingClientRect().bottom || 0; const wb = document.querySelector('.workbench').getBoundingClientRect();
  return { pos: getComputedStyle(pv).position, top: Math.round(r.top), bottom: Math.round(r.bottom), h: Math.round(r.height), viewTop: Math.round(v.top), viewBottom: Math.round(v.bottom), navBottom: Math.round(nav.bottom), hdr: Math.round(hdr), wbBottom: Math.round(wb.bottom), inner: innerHeight, scrollY, where: document.querySelector('.preview .rd-where').textContent, b3d: document.querySelector('.b3d')?.offsetHeight || 0 }; }"""


def check(c, m):
    if not c: fails.append(m); print('  FAIL', m)


with sync_playwright() as p:
    b = p.chromium.launch()
    for w, hh in [(1366, 768), (1440, 900), (1920, 1080), (1280, 720)]:
        pg = b.new_page(viewport={'width': w, 'height': hh}); pg.set_default_timeout(15000)
        pg.goto(URL); pg.wait_for_selector('.scene'); pg.locator('.pg-dot').last.click()
        pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper'); pg.wait_for_timeout(500)
        pg.locator('.step').nth(7).click(); pg.wait_for_timeout(700)
        pg.evaluate('scrollTo(0, 400)'); pg.wait_for_timeout(200)  # a sticky panel sits in its normal place until the page scrolls
        s0 = pg.evaluate(ST); rep[f'{w}x{hh}'] = {'top': s0}
        check(s0['pos'] == 'sticky' and s0['bottom'] <= hh + 1, f'{w}x{hh}: preview not pinned inside the window ({s0["pos"]}, panel {s0["h"]}px, bottom {s0["bottom"]}, window {hh})')
        # scroll the form from top to bottom in steps; the page and its bar must stay on screen, below the header
        form_h = pg.evaluate("document.querySelector('.editor').scrollHeight"); worst = None
        for y in range(300, form_h + 1, 300):
            pg.evaluate(f'scrollTo(0, {y})'); pg.wait_for_timeout(120); s = pg.evaluate(ST)
            if s['scrollY'] < y - 5: break  # end of document
            pushed = abs(s['bottom'] - s['wbBottom']) <= 2  # at the end of the form the panel is pushed up by the workbench's end (it must not cover what follows)
            ok = pushed or (s['top'] >= s['hdr'] - 1 and s['navBottom'] <= hh + 1 and s['viewTop'] >= s['hdr'] and s['viewBottom'] <= hh + 1)
            if not ok and worst is None: worst = (y, s)
        check(worst is None, f'{w}x{hh}: preview left the screen while scrolling the form at y={worst[0] if worst else 0}: {worst[1] if worst else ""}')
        pg.screenshot(path=str(OUT / f'{w}x{hh}-step8-bottom.png'))
        # the preview does not cover content below the workbench
        pg.evaluate('scrollTo(0, document.body.scrollHeight)'); pg.wait_for_timeout(200); s = pg.evaluate(ST)
        check(s['bottom'] <= s['wbBottom'] + 1, f'{w}x{hh}: preview bottom {s["bottom"]} below the workbench end {s["wbBottom"]}')
        # a change at the bottom of the form shows at once in the cover
        copy = pg.get_by_label('카피', exact=False).first
        copy.scroll_into_view_if_needed(); copy.fill('검증용 카피 문장'); pg.wait_for_timeout(700)
        got = pg.evaluate("document.querySelector('.preview .cv-copy')?.textContent.trim()")
        s = pg.evaluate(ST)
        check(got == '검증용 카피 문장', f'{w}x{hh}: copy change not shown in the cover ({got!r})')
        check(s['viewTop'] >= s['hdr'] and s['viewBottom'] <= hh + 1, f'{w}x{hh}: after editing at the bottom the page is off screen {s}')
        pg.locator('.preview .rd-turn').nth(1).click(); pg.wait_for_timeout(300)
        check(pg.evaluate("document.querySelector('.preview .rd-where').textContent") != s['where'], f'{w}x{hh}: page bar not usable from the bottom of the form')
        # other steps keep a sticky preview
        for st in (2, 5):
            pg.evaluate('scrollTo(0,0)'); pg.locator('.step').nth(st - 1).click(); pg.wait_for_timeout(600); pg.evaluate('scrollTo(0, 400)'); pg.wait_for_timeout(200); s = pg.evaluate(ST)
            check(s['pos'] == 'sticky' and s['bottom'] <= hh + 1, f'{w}x{hh} step {st}: preview {s["pos"]}, bottom {s["bottom"]}')
            rep[f'{w}x{hh}'][f'step{st}'] = s
        pg.close()
    pg = b.new_page(viewport={'width': 390, 'height': 844}); pg.set_default_timeout(15000)
    pg.goto(URL); pg.wait_for_selector('.scene'); pg.locator('.pgp-sum').click(); pg.locator('.pgp-list button').last.click()
    pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper'); pg.wait_for_timeout(500)
    pg.locator('.step').nth(7).click(); pg.wait_for_timeout(500); pg.locator('.view-tabs button').nth(1).click(); pg.wait_for_timeout(500)
    check(pg.evaluate("getComputedStyle(document.querySelector('.preview')).position") == 'static', '390: the phone keeps the vertical layout (no sticky)')
    b.close()
(OUT / 'sticky.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
print('FAIL' if fails else 'PASS', *fails, sep='\n'); sys.exit(1 if fails else 0)
