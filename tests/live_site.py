"""W-046: verify the deployed public site (GitHub Pages) in a real browser session.
Checks: first screen loads; journey stations and a topic; fonts actually loaded (document.fonts) and no failed
requests; studio: type into the manuscript, the preview follows; cover preview (step 8) and the finished-book reader
(page turn); JSON export triggers a download; reload on a hash route and route changes; 390px phone layout; console
errors; the admin route shows the public notice (no presentation data). Usage: python tests/live_site.py <url> <outdir>"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = sys.argv[1].rstrip('/') + '/'
OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
fails, rep = [], {}


def check(c, m):
    if not c: fails.append(m); print('  FAIL', m)


with sync_playwright() as p:
    b = p.chromium.launch()
    for w, hh in [(1440, 900), (390, 844)]:
        ctx = b.new_context(viewport={'width': w, 'height': hh}, accept_downloads=True); pg = ctx.new_page(); pg.set_default_timeout(30000)
        errs, failed = [], []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        pg.on('requestfailed', lambda r: failed.append(r.url)); pg.on('response', lambda r: r.status >= 400 and failed.append(f'{r.status} {r.url}'))
        resp = pg.goto(URL, wait_until='load'); pg.wait_for_selector('.scene')
        check(resp and resp.status == 200, f'{w}: first load status {resp and resp.status}')
        fonts = pg.evaluate("document.fonts.ready.then(() => [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family)).then(a => [...new Set(a)])")
        check(any('Chaekgongbang' in f for f in fonts), f'{w}: embedded fonts not loaded {fonts}')
        rep[f'{w}'] = {'status': resp.status, 'fonts': fonts, 'bytes': len(resp.body())}
        pg.screenshot(path=str(OUT / f'{w}-01-first.png'))
        # journey: a station and a topic
        if w > 560: pg.locator('.pg-dot').nth(2).click()
        else: pg.locator('.pgp-sum').click(); pg.locator('.pgp-list button').nth(2).click()
        pg.wait_for_selector('.station-v7')
        if pg.locator('.tm-box').get_attribute('open') is None: pg.locator('.tm-sum').click()
        pg.locator('.tm-list button', has_text='함께 일하는 장면').click(); pg.wait_for_timeout(600)
        imgs_ok = pg.evaluate("[...document.querySelectorAll('.scn-img, .lc img, .station-v7 img')].every(i => i.complete && i.naturalWidth > 0)")
        check(pg.locator('.scn-item').count() == 5 and imgs_ok, f'{w}: collaboration scenes / images not all loaded')
        pg.screenshot(path=str(OUT / f'{w}-02-journey-scenes.png'))
        # studio: sample book, type, preview follows, cover, reader
        pg.goto(URL + '#/journey'); pg.wait_for_selector('.scene')
        if w > 560: pg.locator('.pg-dot').last.click()
        else: pg.locator('.pgp-sum').click(); pg.locator('.pgp-list button').last.click()
        pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper'); pg.wait_for_timeout(800)
        pg.locator('.step').nth(1).click(); pg.wait_for_timeout(400)
        ta = pg.locator('.blk-list textarea').nth(1); ta.fill(ta.input_value() + ' 공개 사이트에서 입력한 문장.'); pg.wait_for_timeout(900)
        if w < 900: pg.locator('.view-tabs button').nth(1).click(); pg.wait_for_timeout(600)
        check(pg.evaluate("document.body.textContent.includes('공개 사이트에서 입력한 문장')") and pg.locator('.preview .pv-flow .hl').count() >= 1, f'{w}: preview did not follow the typed text')
        pg.screenshot(path=str(OUT / f'{w}-03-studio-typing.png'))
        if w < 900: pg.locator('.view-tabs button').nth(0).click()
        pg.locator('.step').nth(7).click(); pg.wait_for_timeout(700)
        if w < 900: pg.locator('.view-tabs button').nth(1).click(); pg.wait_for_timeout(600)
        # step 8 shows the cover three times (page strip, 3D cover, production flat cover): the page strip's cover must be there with its photo loaded
        check(pg.locator('.preview .pg-cover .cv-front .cv-title').count() == 1 and pg.evaluate("(() => { const i = document.querySelector('.preview .pg-cover .cv-front img'); return !!i && i.complete && i.naturalWidth > 0; })()"), f'{w}: cover preview missing or photo not loaded')
        pg.screenshot(path=str(OUT / f'{w}-04-cover.png'))
        if w < 900: pg.locator('.view-tabs button').nth(0).click()
        pg.get_by_role('button', name='완성본 보기').first.click(); pg.wait_for_selector('dialog[open] .rd-where'); pg.wait_for_timeout(600)
        w0 = pg.locator('dialog .rd-where').inner_text(); pg.locator('dialog .rd-turn').nth(1).click(); pg.wait_for_timeout(300); w1 = pg.locator('dialog .rd-where').inner_text()
        check(w0 != w1, f'{w}: reader page turn did not move ({w0} -> {w1})')
        pg.screenshot(path=str(OUT / f'{w}-05-reader.png'))
        pg.locator('dialog[open] .bd-bar button', has_text='닫기').click(); pg.wait_for_timeout(300)
        # download (JSON backup)
        pg.locator('.file-menu > summary').click(); pg.wait_for_timeout(200)
        with pg.expect_download(timeout=15000) as dl:
            pg.get_by_role('button', name='JSON 백업').first.click()
        d = dl.value; path = OUT / f'{w}-backup.json'; d.save_as(str(path))
        check(path.exists() and path.stat().st_size > 1000 and json.loads(path.read_text(encoding='utf-8')).get('blocks'), f'{w}: JSON backup download failed')
        # reload on a hash route, then route change
        pg.reload(); pg.wait_for_selector('.stepper'); check('#/studio' in pg.url, f'{w}: reload lost the studio route')
        pg.locator('.step').nth(1).click(); pg.wait_for_timeout(400)  # the manuscript step: the text lives in textarea values (the phone shows the editor tab first)
        check(pg.evaluate("[...document.querySelectorAll('.blk-list textarea')].some(t => t.value.includes('공개 사이트에서 입력한 문장'))"), f'{w}: typed text not restored after reload (IndexedDB)')
        pg.goto(URL + '#/journey'); pg.wait_for_selector('.scene')
        pg.goto(URL + '#/admin/process'); pg.wait_for_timeout(500)
        check('관리자(발표) 화면이 없어요' in pg.locator('main h1').inner_text(), f'{w}: admin route did not show the public notice')
        check(pg.evaluate("!document.body.textContent.includes('AI융합교육전공')"), f'{w}: presenter text found on the public site')
        check(pg.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth') == 0, f'{w}: horizontal page scroll')
        check(not errs, f'{w}: console/page errors {errs[:3]}')
        check(not failed, f'{w}: failed requests {failed[:3]}')
        rep[f'{w}'].update({'errors': errs, 'failed': failed, 'reader': [w0, w1]})
        ctx.close()
    b.close()
(OUT / 'live.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps({k: {'status': v['status'], 'bytes': v['bytes'], 'fonts': v['fonts']} for k, v in rep.items()}, ensure_ascii=False))
print('FAIL' if fails else 'PASS', *fails, sep='\n'); sys.exit(1 if fails else 0)
