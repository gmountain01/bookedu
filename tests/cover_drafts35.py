"""W-035: the two cover drafts on the same photograph (A = full, B = band) as real print PDFs of the sample book,
plus the back cover, the flat cover and a contact sheet of every page (to review the new manuscript and figures).
Usage: python tests/cover_drafts35.py <outdir>"""
import sys
from pathlib import Path
import fitz
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
errors = []
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 1440, 'height': 1600}); ctx.add_init_script('window.print = () => {};')
    pg = ctx.new_page(); pg.set_default_timeout(15000)
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
    pg.goto(URL); pg.wait_for_selector('.scene'); pg.locator('.pg-dot').last.click()
    pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper')
    pg.locator('.step').nth(7).click(); pg.wait_for_timeout(800)
    for key, label in [('A-full', '사진 전면형'), ('B-band', '사진·띠 분리형')]:
        pg.locator('.cvl-choice', has_text=label).click(); pg.wait_for_timeout(700)
        if key == 'A-full':
            pg.locator('.editor').screenshot(path=str(OUT / 'step8.png'))
        pg.locator('.flat-cover summary').click() if not pg.locator('.flat-cover[open]').count() else None
        pg.wait_for_timeout(300)
        pg.locator('.cover-row').screenshot(path=str(OUT / f'{key}-flat.png'))
        pg.locator('.finish-row').get_by_role('button', name='인쇄 / PDF로 저장').click()
        pg.emulate_media(media='print'); pg.pdf(path=str(OUT / f'{key}.pdf'), prefer_css_page_size=True, print_background=True); pg.emulate_media(media='screen')
        pg.evaluate('delete document.body.dataset.print')
        doc = fitz.open(str(OUT / f'{key}.pdf'))
        doc[0].get_pixmap(matrix=fitz.Matrix(2, 2)).save(str(OUT / f'{key}-front.png'))
        doc[-1].get_pixmap(matrix=fitz.Matrix(2, 2)).save(str(OUT / f'{key}-back.png'))
        if key == 'A-full':
            z = .7; pix = [x.get_pixmap(matrix=fitz.Matrix(z, z)) for x in doc]
            cols = 8; w, hh = pix[0].width, pix[0].height; rows = -(-len(pix) // cols)
            sheet = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, cols * (w + 8), rows * (hh + 8)), False); sheet.clear_with(170)
            for i, px in enumerate(pix):
                px.set_origin((i % cols) * (w + 8), (i // cols) * (hh + 8)); sheet.copy(px, px.irect)
            sheet.save(str(OUT / 'book-sheet.png'))
            print('pages', doc.page_count)
    b.close()
print('errors:', errors or 0)
