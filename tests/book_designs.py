"""W-033: the sample book printed in each of the three designs (step 3 cards -> real PDF), plus the step 3
screen at 1440 and 390, for the visual comparison. Fresh browser profiles. Usage: python tests/book_designs.py <outdir>"""
import sys
from pathlib import Path
import fitz
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
DESIGNS = {'classic': '문학·에세이', 'modern': '정보·학습', 'warm': '사진·기록'}
errors = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for w, hh in [(1440, 900), (390, 844)]:
        ctx = b.new_context(viewport={'width': w, 'height': hh}); ctx.add_init_script('window.print = () => {};')
        pg = ctx.new_page(); pg.set_default_timeout(15000)
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.goto(URL); pg.wait_for_selector('.scene')
        if w > 560: pg.locator('.pg-dot').last.click()
        else: pg.locator('.pgp-sum').click(); pg.locator('.pgp-list button').last.click()
        pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper')
        pg.locator('.step').nth(2).click(); pg.wait_for_timeout(600)
        pg.locator('.editor').screenshot(path=str(OUT / f'{w}-step3.png'))
        if w == 1440:
            for key, label in DESIGNS.items():
                pg.locator('.dz-choice', has_text=label).click(); pg.wait_for_timeout(700)
                pg.locator('.preview').screenshot(path=str(OUT / f'{key}-preview.png'))
                pg.locator('.step').nth(7).click(); pg.wait_for_timeout(400)
                pg.locator('.finish-row').get_by_role('button', name='인쇄 / PDF로 저장').click()
                pg.emulate_media(media='print')
                pg.pdf(path=str(OUT / f'{key}.pdf'), prefer_css_page_size=True, print_background=True)
                pg.emulate_media(media='screen'); pg.evaluate('delete document.body.dataset.print')
                doc = fitz.open(str(OUT / f'{key}.pdf'))
                z = 0.8; pix = [x.get_pixmap(matrix=fitz.Matrix(z, z)) for x in doc]
                cols = 7; pw, ph = pix[0].width, pix[0].height; rows = -(-len(pix) // cols)
                sheet = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, cols * (pw + 10), rows * (ph + 10)), False); sheet.clear_with(170)
                for i, px in enumerate(pix):
                    px.set_origin((i % cols) * (pw + 10), (i // cols) * (ph + 10)); sheet.copy(px, px.irect)
                sheet.save(str(OUT / f'{key}-sheet.png'))
                print(key, doc.page_count, 'pages', sorted({f[3] for x in doc for f in x.get_fonts() if f[3]}))
                pg.locator('.step').nth(2).click(); pg.wait_for_timeout(400)
        ctx.close()
    b.close()
print('errors:', errors or 0)
