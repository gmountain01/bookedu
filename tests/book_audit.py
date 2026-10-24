"""W-033 book audit: what the student's book really looks like, in a fresh (isolated) browser profile.
For the sample book at 1440x900 and 390x844: preview screenshots per book part, the fonts the browser actually
used for body text / headings / cover (CDP CSS.getPlatformFontsForNode, not the CSS name), the on-screen body
text size, the completed-book dialog, and the real print output: page.pdf() of the print layout, every PDF page
rendered to PNG (PyMuPDF), blank-page and text checks.
Usage: python tests/book_audit.py <outdir>"""
import json
import sys
from pathlib import Path
import fitz
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
rep = {'fonts': {}, 'preview': {}, 'pdf': {}, 'errors': []}
PV_PAGES = """() => { const f = document.querySelector('.pv-flow'); const bk = f.closest('.book'); const cs = getComputedStyle(bk);
  const pw = bk.querySelector('.pg-cover').getBoundingClientRect().width; const x0 = f.getBoundingClientRect().left;  // on-screen page width (the strip is scaled)
  return [...f.querySelectorAll('[data-bid]')].map(e => ({ bid: e.dataset.bid, text: (e.querySelector('figcaption,caption') || e).textContent.replace(/\s+/g, '').slice(0, 10),
    page: Math.floor((e.getBoundingClientRect().left - x0 + 1) / pw) + 2 })); }"""
pv_pages = []


def fonts_for(pg, cdp, sel):
    """Platform fonts the renderer used for the first element matching sel (name -> glyph count)."""
    if not pg.locator(sel).count():
        return None
    root = cdp.send('DOM.getDocument', {'depth': 1})['root']['nodeId']
    nid = cdp.send('DOM.querySelector', {'nodeId': root, 'selector': sel})['nodeId']
    if not nid:
        return None
    fs = cdp.send('CSS.getPlatformFontsForNode', {'nodeId': nid})['fonts']
    return {f['familyName']: f['glyphCount'] for f in fs}


def page_png(pdf, i, name, zoom=2):
    pix = pdf[i].get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    pix.save(str(OUT / name))
    return pix


with sync_playwright() as p:
    b = p.chromium.launch()
    for w, hh in [(1440, 900), (390, 844)]:
        ctx = b.new_context(viewport={'width': w, 'height': hh})
        ctx.add_init_script('window.print = () => {};')
        pg = ctx.new_page(); pg.set_default_timeout(10000)
        pg.on('pageerror', lambda e: rep['errors'].append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and rep['errors'].append(m.text))
        cdp = ctx.new_cdp_session(pg); cdp.send('DOM.enable'); cdp.send('CSS.enable')
        pg.goto(URL); pg.wait_for_selector('.scene')
        if w > 560: pg.locator('.pg-dot').nth(7).click()
        else: pg.locator('.pgp-sum').click(); pg.locator('.pgp-list button').nth(7).click()
        pg.get_by_role('button', name='예시 책으로 시작하기').first.click()
        pg.wait_for_selector('.stepper')
        show_pv = (lambda: pg.locator('.view-tabs button').nth(1).click()) if w < 900 else (lambda: None)
        show_ed = (lambda: pg.locator('.view-tabs button').nth(0).click()) if w < 900 else (lambda: None)
        info = {}
        for step, label in [(1, 'cover-planning'), (3, 'body'), (6, 'titlepage'), (7, 'toc'), (8, 'cover')]:
            show_ed(); pg.locator('.step').nth(step - 1).click(); show_pv(); pg.wait_for_timeout(500)
            pg.locator('.preview').screenshot(path=str(OUT / f'{w}-pv-{step}-{label}.png'))
            if step == 3:
                info['body_px'] = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.pv-flow .bk-p')).fontSize)")
                info['page_info'] = pg.locator('.pv-head .muted').first.inner_text()
                info['mm_px'] = pg.evaluate("getComputedStyle(document.querySelector('.pv-flow')).getPropertyValue('--mm')")
                if w == 1440:
                    # page of every body block in the preview, in the PDF's numbering (front cover = 1)
                    pv_pages = pg.evaluate(PV_PAGES)
                    rep['fonts']['body'] = fonts_for(pg, cdp, '.pv-flow .bk-p')
                    rep['fonts']['h1'] = fonts_for(pg, cdp, '.pv-flow .bk-h1')
                    rep['fonts']['caption'] = fonts_for(pg, cdp, '.pv-flow figcaption')
                    rep['fonts']['table'] = fonts_for(pg, cdp, '.pv-flow .bk-table td')
            if step == 8 and w == 1440:
                rep['fonts']['cover_title'] = fonts_for(pg, cdp, '.cv-title')
        rep['preview'][w] = info
        show_ed()
        pg.get_by_role('button', name='완성본 보기').first.click()
        pg.wait_for_selector('dialog[open]'); pg.wait_for_timeout(400)
        pg.screenshot(path=str(OUT / f'{w}-dialog.png'))
        pg.locator('.bd-read').screenshot(path=str(OUT / f'{w}-dialog-full.png')) if w == 1440 else None
        pg.keyboard.press('Escape')
        if w == 1440:
            # the real print layout: the app's own print path, then Chromium's PDF engine with the CSS page size
            pg.get_by_role('button', name='인쇄 / PDF로 저장').first.click()
            pg.emulate_media(media='print')
            pdf_path = OUT / 'print.pdf'
            pg.pdf(path=str(pdf_path), prefer_css_page_size=True, print_background=True)
            pg.emulate_media(media='screen')
            doc = fitz.open(str(pdf_path))
            pages = []
            for i in range(doc.page_count):
                pix = page_png(doc, i, f'print-p{i + 1:02d}.png', zoom=1.4)
                text = doc[i].get_text().strip()
                smp = pix.samples  # one copy (each .samples access copies the buffer)
                ink = sum(1 for k in range(0, len(smp), pix.n * 7) if smp[k] < 200)
                pages.append({'n': i + 1, 'chars': len(text), 'ink': ink, 'first': text[:30].replace('\n', ' '),
                              'size_mm': [round(doc[i].rect.width / 72 * 25.4), round(doc[i].rect.height / 72 * 25.4)]})
            fonts = sorted({f[3] for i in range(doc.page_count) for f in doc[i].get_fonts()})
            rep['pdf'] = {'pages': pages, 'fonts': fonts}
            texts = [''.join(doc[i].get_text().split()) for i in range(doc.page_count)]
            cmp = []
            for blk in pv_pages:
                # headings also appear in the contents page: take the last hit before the back cover (the body)
                hits = [i + 1 for i, t in enumerate(texts[:-1]) if blk['text'] and blk['text'] in t]
                hit = hits[-1] if hits else None
                cmp.append({**blk, 'pdf': hit})
            rep['pdf']['same_page'] = sum(1 for c in cmp if c['pdf'] == c['page'])
            rep['pdf']['blocks'] = cmp
        ctx.close()
    b.close()

(OUT / 'audit.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps({k: rep[k] for k in ('fonts', 'preview')}, ensure_ascii=False))
print('pdf pages:', len(rep['pdf'].get('pages', [])), 'fonts:', rep['pdf'].get('fonts'))
print('preview page == PDF page for', rep['pdf'].get('same_page'), 'of', len(rep['pdf'].get('blocks', [])), 'blocks')
for c in rep['pdf'].get('blocks', []):
    if c['pdf'] != c['page']:
        print('  differs:', c)
for pgi in rep['pdf'].get('pages', []):
    print(pgi)
print('errors:', rep['errors'] or 0)
