"""W-033 visual/functional verification of the student's book across manuscript conditions (fresh browser
profiles; the real JSON import path; no real student data is touched).
Cases: short, long (many chapters/sections), long titles, no images, landscape+portrait images with long
captions, Korean+English+numbers (long URL), B6 12pt / A5 9pt, a legacy saved file, design change + reload.
Per case: preview pages = PDF pages, page of every block preview = PDF, no line or figure wider than its page
(overflow), no blank interior PDF page, no heading left alone at a page end, figure and caption on one page,
fonts actually used (CDP), screenshots + PDF contact sheet for the visual review.
Usage: python tests/book_cases.py <outdir>"""
import base64
import json
import sys
from pathlib import Path
import fitz
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
NOW = '2026-10-23T00:00:00.000Z'


def png(w, h, rgb):
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, w, h), False)
    pix.clear_with(255)
    band = fitz.Pixmap(fitz.csRGB, fitz.IRect(w // 8, h // 8, w - w // 8, h - h // 8), False)
    band.set_rect(band.irect, rgb)
    pix.copy(band, band.irect)
    return 'data:image/png;base64,' + base64.b64encode(pix.tobytes('png')).decode()


def project(name, title, blocks, layout=None, assets=None, cover=None, fm=None, author='시험 지은이'):
    n = iter(range(1, 999))
    bl = []
    for b in blocks:
        b = dict(b); b['id'] = f'{name}-{next(n)}'; bl.append(b)
    return {
        'schemaVersion': 1, 'id': f'case-{name}', 'createdAt': NOW, 'updatedAt': NOW,
        'meta': {'title': title, 'authorAlias': author, 'genre': '수필', 'topic': '시험', 'targetReader': '시험 독자'},
        'blocks': bl,
        'layout': layout or {'pageSize': 'A5', 'theme': 'classic', 'fontFamily': 'myeongjo', 'fontSize': 10, 'lineHeight': 1.75, 'margin': 18},
        'assets': assets or [], 'imagePrompt': '',
        'frontMatter': fm or {'titlePage': '', 'copyrightText': f'{title}\n지은이 {author}\n시험용 책입니다. ISBN은 발급받지 않았습니다.', 'preface': '시험용 머리말입니다.'},
        'cover': cover or {'backgroundColor': '#2f6b4f', 'imageId': '', 'backText': '시험용 뒤표지 글입니다.'},
        'reflection': {'designReason': ''}, 'progress': {'currentStep': 3, 'tocReviewed': False},
    }


H = lambda lv, t: {'type': 'heading', 'level': lv, 'text': t}
_pn = iter(range(1, 9999))
P = lambda t: {'type': 'paragraph', 'text': f'[문단 {next(_pn)}] {t}'}  # unique start: lets the test find each paragraph in the PDF
LOREM = ('골목을 걷는 일은 생각보다 많은 것을 알려 준다. 같은 길이라도 계절과 시간에 따라 빛이 다르고, 가게 앞에 놓인 화분의 자리도 조금씩 바뀐다. '
         '나는 그런 작은 차이를 수첩에 적기 시작했다. 처음에는 한 줄이던 기록이 어느새 한 쪽을 넘었다. ')
CASES = {
    'short': project('short', '짧은 책', [H(1, '1장 시작'), P('제목과 본문만 있는 아주 짧은 원고입니다. 한 쪽 안에 모두 들어가요.')]),
    'long': project('long', '긴 원고의 책', [b for c in range(1, 6) for b in (
        [H(1, f'{c}장 기록의 {c}번째 묶음'), P(LOREM * 3)] + [x for s in range(1, 4) for x in (H(2, f'{c}.{s} 작은 절 제목'), P(LOREM * 2), H(3, f'중제목 {c}-{s}'), P(LOREM))])]),
    'long-titles': project('longtitle', '등굣길 칠 분 동안 골목에서 만난 가게와 나무와 사람들에 대한 아주 긴 제목의 기록',
                           [H(1, '1장 아침마다 지나던 골목에서 처음으로 걸음을 멈추고 오래 바라본 날에 생긴 일'), P(LOREM * 2), H(2, '절 제목도 아주 길게 써서 두 줄 이상으로 넘어가는 경우를 확인해 봅니다'), P(LOREM)],
                           fm={'titlePage': '부제도 조금 길게: 중학생이 쓴 동네 관찰 기록', 'copyrightText': '긴 제목 시험', 'preface': '머리말'}),
    'no-images': project('noimg', '그림 없는 책', [H(1, '1장 글만 있는 장'), P(LOREM * 4), H(2, '절 제목 1'), P(LOREM * 3), {'type': 'paragraph', 'style': 'quote', 'text': '“인용문도 글만 있는 책에서 구별되어야 해요.”'}, P(LOREM)]),
    'images': project('img', '그림이 많은 책', [
        H(1, '1장 가로 그림과 세로 그림'), P(LOREM),
        {'type': 'image', 'assetId': 'wide', 'caption': '그림 1. 가로로 긴 그림. 캡션이 길어서 두 줄 이상이 되는 경우에도 그림의 폭 안에서 줄이 바뀌어야 해요. 출처: 시험용으로 만든 그림', 'alt': '가로 그림'},
        P(LOREM),
        {'type': 'image', 'assetId': 'tall', 'caption': '그림 2. 세로로 긴 그림', 'alt': '세로 그림'},
        P(LOREM * 2),
        {'type': 'table', 'caption': '표 1. 숫자와 영문이 섞인 표', 'rows': [['항목', 'Value', '비고'], ['A-1', '1,234', 'https://example.org/a-very-long-path/for-testing'], ['B-2', '56.7%', '한글과 English']]},
        P(LOREM)],
        assets=[{'id': 'wide', 'data': png(1200, 600, (70, 120, 180)), 'mimeType': 'image/png', 'width': 1200, 'height': 600, 'name': '가로', 'sourceNote': '시험용'},
                {'id': 'tall', 'data': png(600, 1000, (200, 120, 60)), 'mimeType': 'image/png', 'width': 600, 'height': 1000, 'name': '세로', 'sourceNote': '시험용'}],
        cover={'backgroundColor': '#e0a400', 'imageId': 'wide', 'backText': '노란 표지에서는 글자가 어두운 색으로 바뀌어야 해요.'}),
    'mixed': project('mixed', 'Hello 책공방 2026', [H(1, 'Chapter 1 섞인 글'), P('2026년 10월 23일, 우리는 Playwright와 PyMuPDF로 PDF를 확인했다. URL은 https://www.example.com/very/long/path/that/should/wrap/inside/the/text/block?query=1234567890 이고, 숫자 3.14159와 영어 단어 internationalization도 들어 있다. “따옴표”, 『책 제목』, 「작품」, …(말줄임표)도 확인한다.'), P(LOREM)]),
    'b6-12pt': project('b6', 'B6 판형 12pt', [H(1, '1장 작은 판형'), P(LOREM * 3), H(2, '큰 글자 제목 2'), P(LOREM * 2)],
                       layout={'pageSize': 'B6', 'theme': 'classic', 'fontFamily': 'myeongjo', 'fontSize': 12, 'lineHeight': 1.75, 'margin': 18}),
    'a5-9pt-modern': project('a5m', 'A5 9pt 정보·학습', [H(1, '1장 정보 책'), P(LOREM * 3), H(2, '절 제목 3'), P(LOREM), H(3, '중제목 제목 4'), P(LOREM), H(4, '소제목 제목 5'), P(LOREM)],
                             layout={'pageSize': 'A5', 'theme': 'modern', 'fontFamily': 'gothic', 'fontSize': 9, 'lineHeight': 1.7, 'margin': 18}),
    # MT-16: empty preface/copyright and an empty heading print nothing; a 1:4 portrait picture keeps a readable caption
    'empty-parts': project('empty', '빈 부분이 있는 책', [H(1, ''), P('짧다.'), {'type': 'image', 'assetId': 'thin', 'caption': '그림 1. 아주 좁고 긴 세로 그림에도 캡션은 읽을 만한 폭이 있어야 해요', 'alt': '세로 그림'},
                                                      {'type': 'table', 'caption': '표 1. 짧은 칸', 'rows': [['이름', '비고'], ['없음', '123456789012']]}],
                           assets=[{'id': 'thin', 'data': png(200, 800, (90, 140, 90)), 'mimeType': 'image/png', 'width': 200, 'height': 800, 'name': '좁은 그림', 'sourceNote': '시험용'}],
                           fm={'titlePage': '', 'copyrightText': '', 'preface': ''}, cover={'backgroundColor': '#1d4fb8', 'imageId': '', 'backText': ''}),
    # a saved file as the old app wrote it: old design key + settings the student had chosen, no new fields
    'legacy': project('legacy', '예전에 저장한 책', [H(1, '1장 예전 원고'), P(LOREM * 2), H(2, '절 제목 6'), P(LOREM)],
                      layout={'pageSize': 'A5', 'theme': 'warm', 'fontFamily': 'gothic', 'fontSize': 12, 'lineHeight': 2, 'margin': 24}),
}

PV = """() => { const f = document.querySelector('.pv-flow'); const cs = getComputedStyle(f.closest('.book'));
  const pw = f.closest('.book').querySelector('.pg-cover').getBoundingClientRect().width;  // on-screen page width (the strip is scaled)
  const ms = parseFloat(cs.getPropertyValue('--ms')) * pw / parseFloat(cs.getPropertyValue('--pw'));
  const x0 = f.getBoundingClientRect().left; const col = (x) => Math.floor((x - x0 + 1) / pw);
  const blocks = [...f.querySelectorAll('[data-bid]')].map(e => { const r = e.getBoundingClientRect();
    return { bid: e.dataset.bid, tag: e.tagName, text: (e.querySelector('figcaption,caption') || e).textContent.replace(/\\s+/g, '').slice(0, 10), page: col(r.left) + 2 }; });
  // a block split over two pages has one client rect per page fragment: check each against its own page
  const over = [...f.querySelectorAll('.bk-body *')].filter(e => [...e.getClientRects()].some(r => r.width && r.right > x0 + col(r.left) * pw + pw - ms + 1.5))
    .map(e => e.tagName + ':' + (e.textContent || '').slice(0, 20));
  const figs = [...f.querySelectorAll('.bk-fig')].map(fg => { const i = fg.querySelector('img'), c = fg.querySelector('figcaption'); return !c || col(i.getBoundingClientRect().left) === col(c.getBoundingClientRect().left); });
  const hs = [...f.querySelectorAll('.bk-body > .bk-h')].map(hd => { const n = hd.nextElementSibling; return !n || col(hd.getBoundingClientRect().left) === col(n.getBoundingClientRect().left); });
  return { blocks, over, figsOk: figs.every(Boolean), headsOk: hs.every(Boolean), theme: f.closest('.book').dataset.theme }; }"""


def fonts_for(cdp, sel):
    root = cdp.send('DOM.getDocument', {'depth': 1})['root']['nodeId']
    nid = cdp.send('DOM.querySelector', {'nodeId': root, 'selector': sel})['nodeId']
    return {f['familyName']: f['glyphCount'] for f in cdp.send('CSS.getPlatformFontsForNode', {'nodeId': nid})['fonts']} if nid else None


def open_studio(pg):
    pg.goto(URL); pg.wait_for_selector('.scene')
    pg.locator('.pg-dot').last.click(); pg.wait_for_selector('.scene-finish')
    pg.get_by_role('button', name='내 원고로 시작하기').first.click(); pg.wait_for_selector('.stepper')


def import_case(pg, path):
    pg.locator('input[type=file][accept*="json"]').set_input_files(str(path))
    if pg.locator('dialog[open]').count():  # replace confirmation when the current book has content
        pg.locator('dialog[open] button').first.click()
    pg.wait_for_timeout(700)


def check_pdf(pg, name, pv):
    pg.locator('.step').nth(7).click()  # the print button lives in step 8 (and in the completed-book view)
    pg.locator('.finish-row').get_by_role('button', name='인쇄 / PDF로 저장').click()
    pg.emulate_media(media='print')
    pdf = OUT / f'{name}.pdf'
    pg.pdf(path=str(pdf), prefer_css_page_size=True, print_background=True)
    pg.emulate_media(media='screen')
    pg.evaluate("delete document.body.dataset.print")
    doc = fitz.open(str(pdf))
    texts = [''.join(doc[i].get_text().split()) for i in range(doc.page_count)]
    empty = [i + 1 for i in range(1, doc.page_count - 1) if not texts[i] and not doc[i].get_images()]
    # intended: an empty left-hand (even) page before a part that starts on a right-hand page; anything else is a fault
    blank = [n for n in empty if n % 2 or n + 1 in empty or not texts[n]]
    diff = []
    for b in pv['blocks']:
        hits = [i + 1 for i, t in enumerate(texts[:-1]) if b['text'] and b['text'] in t]
        if hits and hits[-1] != b['page']:
            diff.append((b['tag'], b['text'], b['page'], hits[-1]))
    return doc.page_count, blank, diff, doc


rows, errors = [], []
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, proj in CASES.items():
        path = OUT / f'{name}.json'
        path.write_text(json.dumps(proj, ensure_ascii=False), encoding='utf-8')
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}); ctx.add_init_script('window.print = () => {};')
        pg = ctx.new_page(); pg.set_default_timeout(15000)
        pg.on('pageerror', lambda e, n=name: errors.append(f'{n}: {e}'))
        pg.on('console', lambda m, n=name: m.type == 'error' and errors.append(f'{n}: {m.text}'))
        cdp = ctx.new_cdp_session(pg); cdp.send('DOM.enable'); cdp.send('CSS.enable')
        open_studio(pg)
        import_case(pg, path)
        pg.locator('.step').nth(4).click(); pg.wait_for_timeout(600)
        pv = pg.evaluate(PV)
        info = pg.locator('.pv-head .muted').first.inner_text()
        pv_pages = int(info.split('쪽')[0])
        pg.locator('.preview').screenshot(path=str(OUT / f'{name}-preview.png'))
        body_font = fonts_for(cdp, '.pv-flow .bk-body .bk-p')
        n, blank, diff, doc = check_pdf(pg, name, pv)
        z = 0.55
        pix = [x.get_pixmap(matrix=fitz.Matrix(z, z)) for x in doc]
        cols = min(8, len(pix)); w, hh = pix[0].width, pix[0].height; rws = -(-len(pix) // cols)
        sheet = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, cols * (w + 8), rws * (hh + 8)), False); sheet.clear_with(170)
        for i, px in enumerate(pix):
            px.set_origin((i % cols) * (w + 8), (i // cols) * (hh + 8)); sheet.copy(px, px.irect)
        sheet.save(str(OUT / f'{name}-sheet.png'))
        layout_after = pg.evaluate("JSON.stringify(document.querySelector('.pv-flow').closest('.book').dataset.theme)")
        all_text = ''.join(''.join(x.get_text().split()) for x in doc)
        placeholder = [t for t in ('아직쓰지않았어요', '제목없음', '써보세요') if t in all_text]
        cap_w = pg.evaluate("Math.min(...[...document.querySelectorAll('.pv-flow figcaption')].map(c => c.getBoundingClientRect().width / document.querySelector('.pv-strip .pg-cover').getBoundingClientRect().width * parseFloat(getComputedStyle(document.querySelector('.pv-strip')).getPropertyValue('--pw'))), 999)")
        row = {'case': name, 'pv_pages': pv_pages, 'pdf_pages': n, 'same_pages': n == pv_pages, 'block_page_diff': diff,
               'overflow': pv['over'][:5], 'blank_pdf_pages': blank, 'figure_caption_together': pv['figsOk'], 'no_stranded_heading': pv['headsOk'],
               'body_font': body_font, 'theme': pv['theme'], 'placeholder_text': placeholder, 'min_caption_mm': round(cap_w, 1)}
        rows.append(row)
        ctx.close()

    # design change -> saved -> reload: the design stays and the manuscript is unchanged
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}); pg = ctx.new_page(); pg.set_default_timeout(15000)
    pg.on('pageerror', lambda e: errors.append(f'reload: {e}'))
    pg.goto(URL); pg.wait_for_selector('.scene'); pg.locator('.pg-dot').last.click()
    pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper')
    pg.locator('.step').nth(2).click(); pg.wait_for_timeout(400)
    before = pg.evaluate("(() => [...document.querySelectorAll('.pv-flow [data-bid]')].map(e => e.dataset.bid + '|' + e.textContent).sort().join(' || '))()")  # per block (a paragraph may be set before a figure that moved, W-033)
    pg.locator('.dz-choice', has_text='정보·학습').click(); pg.wait_for_timeout(1500)
    pg.reload(); pg.wait_for_selector('.stepper'); pg.wait_for_timeout(800)
    after = pg.evaluate("(() => [...document.querySelectorAll('.pv-flow [data-bid]')].map(e => e.dataset.bid + '|' + e.textContent).sort().join(' || '))()")  # per block (a paragraph may be set before a figure that moved, W-033)
    theme = pg.evaluate("document.querySelector('.pv-strip').dataset.theme")
    rows.append({'case': 'design-change-reload', 'theme_after_reload': theme, 'manuscript_same': before == after,
                 'font_after_reload': pg.evaluate("getComputedStyle(document.querySelector('.pv-flow .bk-p')).fontFamily")[:40]})
    ctx.close()
    b.close()

(OUT / 'cases.json').write_text(json.dumps({'rows': rows, 'errors': errors}, ensure_ascii=False, indent=1), encoding='utf-8')
bad = 0
for r in rows:
    flags = []
    if r.get('same_pages') is False: flags.append('page count differs')
    if r.get('block_page_diff'): flags.append(f"block pages differ {r['block_page_diff'][:3]}")
    if r.get('overflow'): flags.append(f"overflow {r['overflow']}")
    if r.get('blank_pdf_pages'): flags.append(f"blank pages {r['blank_pdf_pages']}")
    if r.get('figure_caption_together') is False: flags.append('figure/caption split')
    if r.get('no_stranded_heading') is False: flags.append('heading stranded')
    if r.get('placeholder_text'): flags.append(f"instruction text printed {r['placeholder_text']}")
    if r.get('min_caption_mm', 999) < 50: flags.append(f"caption only {r['min_caption_mm']}mm wide")
    if 'body_font' in r and not any('Chaekgongbang' in k for k in (r['body_font'] or {})): flags.append(f"body font {r['body_font']}")
    if r['case'] == 'design-change-reload' and not (r['theme_after_reload'] == 'modern' and r['manuscript_same']): flags.append('reload lost design or text')
    bad += bool(flags)
    print(f"{r['case']:<22} {'FAIL ' + '; '.join(flags) if flags else 'ok'}  {json.dumps({k: v for k, v in r.items() if k in ('pv_pages', 'pdf_pages', 'theme', 'body_font', 'theme_after_reload', 'font_after_reload')}, ensure_ascii=False)}")
print('console/page errors:', errors or 0)
sys.exit(1 if bad or errors else 0)
