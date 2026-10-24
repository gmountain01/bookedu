"""W-034 cover check (fresh profiles). Sample book: step 8 screen, preview front cover, flat cover (back | spine |
front), completed-book dialog, real print PDF front/back pages rendered to PNG, and the cover image as drawn (natural
size vs drawn size, so a stretched picture would show). Usage: python tests/cover_check.py <outdir>"""
import json
import sys
from pathlib import Path
import fitz
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
rep, errors = {}, []
STRETCH = """() => [...document.querySelectorAll('.cv-img')].filter(i => i.offsetWidth).map(i => { const cs = getComputedStyle(i);
  return { fit: cs.objectFit, pos: cs.objectPosition, natural: [i.naturalWidth, i.naturalHeight], box: [i.offsetWidth, i.offsetHeight] }; })"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for w, hh in [(1440, 1600), (390, 844)]:   # 1440: tall so the sticky step-8 panel (3D + flat cover) is fully in view
        ctx = b.new_context(viewport={'width': w, 'height': hh}); ctx.add_init_script('window.print = () => {};')
        pg = ctx.new_page(); pg.set_default_timeout(15000)
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.goto(URL); pg.wait_for_selector('.scene')
        if w > 560: pg.locator('.pg-dot').last.click()
        else: pg.locator('.pgp-sum').click(); pg.locator('.pgp-list button').last.click()
        pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper')
        pg.locator('.step').nth(7).click(); pg.wait_for_timeout(900)
        pg.locator('.editor').screenshot(path=str(OUT / f'{w}-step8.png'))
        if w < 900:
            pg.locator('.view-tabs button').nth(1).click(); pg.wait_for_timeout(700)
        pg.locator('.preview').screenshot(path=str(OUT / f'{w}-preview.png'))
        rep[f'{w}-images'] = pg.evaluate(STRETCH)
        if w == 1440:
            pg.locator('.flat-cover summary').click(); pg.wait_for_timeout(400)
            pg.locator('.cover-row').screenshot(path=str(OUT / 'flat-cover.png'))
            pg.locator('.finish-row').get_by_role('button', name='완성본 보기').click(); pg.wait_for_selector('dialog[open]'); pg.wait_for_timeout(700)
            pg.locator('dialog').screenshot(path=str(OUT / 'dialog.png'))
            pg.keyboard.press('Escape')
            pg.locator('.finish-row').get_by_role('button', name='인쇄 / PDF로 저장').click()
            pg.emulate_media(media='print')
            pg.pdf(path=str(OUT / 'print.pdf'), prefer_css_page_size=True, print_background=True)
            pg.emulate_media(media='screen')
            doc = fitz.open(str(OUT / 'print.pdf'))
            for i, name in [(0, 'print-front'), (doc.page_count - 1, 'print-back')]:
                doc[i].get_pixmap(matrix=fitz.Matrix(2, 2)).save(str(OUT / f'{name}.png'))
            rep['pdf'] = {'pages': doc.page_count, 'front_text': doc[0].get_text().strip(), 'back_text': doc[-1].get_text().strip(),
                          'front_images': [(im[2], im[3]) for im in doc[0].get_images(full=True)]}
        ctx.close()
    b.close()
(OUT / 'cover.json').write_text(json.dumps({**rep, 'errors': errors}, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps(rep, ensure_ascii=False, indent=1)[:2500])
print('errors:', errors or 0)
