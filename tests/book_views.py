"""W-039 cross-screen consistency: the same book in every screen that shows it (fresh profiles, built dist/index.html).
Books: the sample + short / long / images / no-images (odd last page) / b6-12pt / legacy from tests/book_cases.py.
Per book: (1) editor preview at every step 1-8: page count, block -> page, contents text, cover title, theme, page kept
across steps 2->5; (2) completed-book reader: the same count and block pages; (3) print: #print-root flow has the same
structure as the preview flow (blank pages, moved paragraphs, shrunk figures, block order) and the PDF has the same
heading pages. Sample only: edit a heading (contents follow, page kept), add paragraphs until the count changes (no
block lost or doubled), design change (theme / 12pt / B6) reflected in preview + reader, resize 1440 -> 760 -> 390
(count unchanged, page kept), 한 쪽/펼침면 toggle keeps the page in both screens, legacy JSON import keeps its text.
Writes the screen x check table (docs brief §5) to <outdir>/table.json. Usage: python tests/book_views.py <outdir>"""
import json
import sys
from pathlib import Path
import fitz
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
ns = {'__file__': str(LAB / 'tests' / 'book_cases.py')}
src = (LAB / 'tests' / 'book_cases.py').read_text(encoding='utf-8')
exec(src[:src.index('def check_pdf')], ns)
CASES = {k: ns['CASES'][k] for k in ('short', 'long', 'images', 'no-images', 'b6-12pt', 'legacy')}
fails, errors = [], []
table = {}  # screen -> check -> 'ok' | 'FAIL: ...'


def mark(screen, check, ok, detail=''):
    table.setdefault(screen, {})[check] = 'ok' if ok else f'FAIL: {detail}'
    if not ok: fails.append(f'{screen} / {check}: {detail}'); print('  FAIL', screen, check, detail)


# book facts from a page strip (.pv-strip inside `root`): count, block -> page (1 = front cover), structure, texts
FACTS = """(root) => { const r = document.querySelector(root), f = r.querySelector('.pv-flow'), pg = r.querySelector('.pg-cover').getBoundingClientRect().width, x0 = f.getBoundingClientRect().left;
  const col = (e) => Math.floor((e.getBoundingClientRect().left - x0 + 1) / pg) + 2;
  const blocks = Object.fromEntries([...f.querySelectorAll('[data-bid]')].map(e => [e.dataset.bid, col(e)]));
  const struct = [...f.querySelectorAll('.bk-blank, [data-bid], .bk-sec')].map(e => (e.className.split(' ')[0]) + (e.dataset.bid ? ':' + e.dataset.bid : '') + (e.dataset.moved ? '+moved' : '') + (e.dataset.fit ? '+' + e.dataset.fit : ''));
  const n = Math.round(f.getBoundingClientRect().width / pg) + 2;
  return { count: n, blocks, struct, toc: (f.querySelector('.bk-toc')?.textContent || '').replace(/\\s+/g, ' ').trim(), title: (r.querySelector('.cv-title')?.textContent || '').trim(),
    theme: r.querySelector('.pv-strip')?.dataset.theme || r.querySelector('.book')?.dataset.theme, bids: [...f.querySelectorAll('[data-bid]')].map(e => e.dataset.bid) }; }"""
PRINT_FACTS = """() => { const r = document.querySelector('#print-root'), b = r.querySelector('.book-print');
  const kids = [...b.children].slice(1, -1); const els = [];
  for (const k of kids) { if (k.matches('.bk-blank, [data-bid], .bk-sec')) els.push(k); els.push(...k.querySelectorAll('.bk-blank, [data-bid], .bk-sec')); }
  const struct = els.map(e => (e.className.split(' ')[0]) + (e.dataset.bid ? ':' + e.dataset.bid : '') + (e.dataset.moved ? '+moved' : '') + (e.dataset.fit ? '+' + e.dataset.fit : ''));
  return { struct, toc: (b.querySelector('.bk-toc')?.textContent || '').replace(/\\s+/g, ' ').trim(), title: (b.querySelector('.cv-title')?.textContent || '').trim(), theme: b.dataset.theme }; }"""
ED, RD = '.preview', 'dialog .reader'


def where(pg, root): return pg.locator(f'{root} .rd-where').inner_text()


def open_reader(pg):
    pg.get_by_role('button', name='완성본 보기').first.click(); pg.wait_for_selector('dialog[open] .rd-where'); pg.wait_for_timeout(600)


def close_reader(pg):
    pg.locator('dialog[open] .bd-bar button', has_text='닫기').click(); pg.wait_for_timeout(300)


def pdf_heading_pages(pg, name, headings):
    pg.locator('.step').nth(7).click(); pg.wait_for_timeout(400)
    pg.locator('.finish-row').get_by_role('button', name='인쇄 / PDF로 저장').click()
    pfacts = pg.evaluate(PRINT_FACTS)
    pg.emulate_media(media='print')
    pdf = OUT / f'{name}.pdf'; pg.pdf(path=str(pdf), prefer_css_page_size=True, print_background=True)
    pg.emulate_media(media='screen'); pg.evaluate("delete document.body.dataset.print")
    doc = fitz.open(str(pdf))
    texts = [''.join(doc[i].get_text().split()) for i in range(doc.page_count)]
    pages = {}
    for bid, t in headings.items():
        hits = [i + 1 for i, tx in enumerate(texts[:-1]) if t and t in tx]
        pages[bid] = hits[-1] if hits else None
    return pfacts, doc.page_count, pages


def book_in_all_screens(pg, name, w=1440):
    """editor (every step) vs reader vs print for the book currently loaded"""
    per_step = {}
    for step in range(1, 9):
        pg.locator('.step').nth(step - 1).click(); pg.wait_for_timeout(450)
        if w < 900: pg.locator('.view-tabs button').nth(1).click(); pg.wait_for_timeout(500)
        per_step[step] = {**pg.evaluate(FACTS, ED), 'where': where(pg, ED)}
        if w < 900: pg.locator('.view-tabs button').nth(0).click()
    base = per_step[1]
    same = all(s['count'] == base['count'] and s['blocks'] == base['blocks'] and s['toc'] == base['toc'] and s['title'] == base['title'] and s['theme'] == base['theme'] for s in per_step.values())
    mark('작성 중 미리보기 (1~8단계)', f'{name}: 같은 쪽 구성·차례·표지·디자인', same, {k: (v['count'], v['title'][:10]) for k, v in per_step.items() if v['count'] != base['count']})
    opened = {s: v['where'] for s, v in per_step.items()}
    mark('작성 중 미리보기 (1~8단계)', f'{name}: 단계별 첫 쪽 (1·8 표지, 6 표제지, 7 차례, 2~5 본문)',
         '앞표지' in opened[1] and '앞표지' in opened[8] and opened[2] == opened[3] == opened[4] == opened[5] and opened[7] != opened[1], opened)
    open_reader(pg)
    rd = {**pg.evaluate(FACTS, RD), 'where': where(pg, RD)}
    pg.locator(f'{RD} .rd-view').screenshot(path=str(OUT / f'{name}-reader.png'))
    close_reader(pg)
    mark('완성본 보기', f'{name}: 미리보기와 같은 쪽 수·블록 쪽·차례·표지·디자인', rd['count'] == base['count'] and rd['blocks'] == base['blocks'] and rd['toc'] == base['toc'] and rd['title'] == base['title'] and rd['theme'] == base['theme'],
         f"reader {rd['count']} vs preview {base['count']}; blocks differ {[k for k in rd['blocks'] if rd['blocks'][k] != base['blocks'].get(k)][:3]}")
    heads = pg.evaluate("() => Object.fromEntries([...document.querySelectorAll('.preview .pv-flow .bk-h[data-bid]')].map(e => [e.dataset.bid, e.textContent.replace(/\\s+/g, '')]))")
    pfacts, n, pages = pdf_heading_pages(pg, name, heads)
    mark('인쇄 / PDF', f'{name}: 쪽 수 {n} = 미리보기 {base["count"]}', n == base['count'])
    mark('인쇄 / PDF', f'{name}: 제목 블록의 PDF 쪽 = 미리보기 쪽', all(pages[b] == base['blocks'].get(b) for b in pages), {b: (pages[b], base['blocks'].get(b)) for b in pages if pages[b] != base['blocks'].get(b)})
    mark('인쇄 / PDF', f'{name}: 흐름 구조(빈 쪽·옮긴 문단·줄인 그림·순서) = 미리보기', pfacts['struct'] == base['struct'], f"print {len(pfacts['struct'])} vs preview {len(base['struct'])}")
    mark('인쇄 / PDF', f'{name}: 차례·표지 제목·디자인 = 미리보기', pfacts['toc'] == base['toc'] and pfacts['title'] == base['title'] and pfacts['theme'] == base['theme'])
    return base, rd


with sync_playwright() as p:
    b = p.chromium.launch()

    # ---------- the sample, every interaction ----------
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}); ctx.add_init_script('window.print = () => {};')
    pg = ctx.new_page(); pg.set_default_timeout(15000)
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
    pg.goto(URL); pg.wait_for_selector('.scene'); pg.locator('.pg-dot').last.click()
    pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper'); pg.wait_for_timeout(800)
    base, rd = book_in_all_screens(pg, 'sample')
    # step 3 design samples and step 8 cover samples use the same design + cover data
    pg.locator('.step').nth(2).click(); pg.wait_for_timeout(400)
    dz = pg.evaluate("() => [...document.querySelectorAll('.dz-page')].map(e => [e.dataset.theme, getComputedStyle(e.querySelector('.bk-p')).fontFamily.split(',')[0]])")
    mark('3단계 디자인 샘플', '디자인 3개가 각자의 글꼴로 같은 원고의 첫 문단을 보임 (쪽 나누기 없음: 용도상 유지)', len(dz) == 3 and len({d[1] for d in dz}) >= 2, dz)
    pg.locator('.step').nth(7).click(); pg.wait_for_timeout(500)
    cvs = pg.evaluate("() => ({ samples: [...document.querySelectorAll('.cvs-page .cv-title')].map(e => e.textContent.trim()), flat: document.querySelector('.cover-row .cv-title')?.textContent.trim(), b3d: document.querySelector('.b3d-front .cv-title')?.textContent.trim(), label: document.querySelector('.flat-cover summary')?.textContent })")
    mark('8단계 표지 샘플·입체·제작용 펼친 표지', '같은 표지 제목 (미리보기 표지와 같음)', all(t == base['title'] for t in cvs['samples'] + [cvs['flat'], cvs['b3d']]), cvs)
    mark('8단계 표지 샘플·입체·제작용 펼친 표지', '제작용 펼친 표지가 독서용 펼침면과 구분되어 이름 붙음', '제작용' in (cvs['label'] or ''), cvs['label'])
    # editing: heading text -> contents follow, the edited block's page shown, no first-page jump
    pg.locator('.step').nth(1).click(); pg.wait_for_timeout(400)
    pg.locator('.preview .rd-turn').nth(1).click(); pg.locator('.preview .rd-turn').nth(1).click(); pg.wait_for_timeout(300)
    h1 = pg.locator('.blk-list textarea, .blk-list input[type=text]').nth(0)
    h1.fill('바뀐 장 제목'); pg.wait_for_timeout(900)
    f2 = pg.evaluate(FACTS, ED)
    mark('작성 중 미리보기 (편집 반영)', '제목을 고치면 차례가 바뀌고 고친 블록의 쪽이 보임', '바뀐 장 제목' in f2['toc'] and pg.evaluate("!!document.querySelector('.preview .pv-flow .hl')"), f2['toc'][:40])
    # add paragraphs until the page count changes: no block lost or doubled, the edited block stays on screen
    before_n = f2['count']; added = 0
    last_ta = pg.locator('.blk-list textarea').last
    while added < 6 and pg.evaluate(FACTS, ED)['count'] == before_n:
        last_ta.fill(last_ta.input_value() + '\n' + ('새로 쓴 문단이에요. ' * 40)); added += 1; pg.wait_for_timeout(700)
    f3 = pg.evaluate(FACTS, ED)
    mark('작성 중 미리보기 (편집 반영)', f'문단을 늘려 쪽 수가 {before_n} -> {f3["count"]}로 바뀜: 블록 누락·중복 없음, 고친 블록의 쪽이 보임',
         f3['count'] != before_n and len(f3['bids']) == len(set(f3['bids'])) and pg.evaluate("(() => { const hl = document.querySelector('.preview .pv-flow .hl'); if (!hl) return false; const w = document.querySelector('.preview .rd-win').getBoundingClientRect(); return [...hl.getClientRects()].some(r => r.left >= w.left - 1 && r.right <= w.right + 1); })()"),
         f'count {before_n}->{f3["count"]}, added {added}, dup {len(f3["bids"]) - len(set(f3["bids"]))}')
    mark('작성 중 미리보기 (편집 반영)', '입력 초점이 미리보기로 넘어가지 않음', pg.evaluate("document.activeElement.tagName") in ('TEXTAREA', 'INPUT'), pg.evaluate("document.activeElement.tagName"))
    # design change reflected in preview and reader
    pg.locator('.step').nth(2).click(); pg.wait_for_timeout(400)
    pg.locator('.dz-choice', has_text='정보·학습').click(); pg.wait_for_timeout(800)
    pg.locator('.dz-detail select').first.select_option('12'); pg.wait_for_timeout(800)
    f4 = pg.evaluate(FACTS, ED); open_reader(pg); r4 = pg.evaluate(FACTS, RD); close_reader(pg)
    mark('설정 변경 (디자인·글자 크기)', '미리보기와 완성본이 같은 디자인·쪽 수·블록 쪽', f4['theme'] == r4['theme'] == 'modern' and f4['count'] == r4['count'] and f4['blocks'] == r4['blocks'], (f4['theme'], f4['count'], r4['theme'], r4['count']))
    # one page <-> spread in both screens keeps the page; resize keeps count and page
    pg.locator('.step').nth(1).click(); pg.wait_for_timeout(400)
    pg.locator('.preview .rd-turn').nth(1).click(); pg.locator('.preview .rd-turn').nth(1).click(); pg.wait_for_timeout(300)
    w0 = where(pg, ED)
    pg.locator('.preview .rd-mode button', has_text='펼침면').click(); pg.wait_for_timeout(600); w1 = where(pg, ED)
    pg.locator('.preview .rd-mode button', has_text='한 쪽').click(); pg.wait_for_timeout(600); w2 = where(pg, ED)
    p0 = int(w0.split(' /')[0].split('–')[0]); lo, hi = [int(x) for x in (w1.split(' /')[0].split('–') * 2)[:2]]
    mark('작성 중 미리보기 (보기 방식)', '한 쪽 -> 펼침면 -> 한 쪽에서 읽던 쪽 유지', lo <= p0 <= hi and w2 == w0, (w0, w1, w2))
    open_reader(pg)
    pg.locator(f'{RD} .rd-turn').nth(1).click(); pg.locator(f'{RD} .rd-turn').nth(1).click(); pg.wait_for_timeout(300); r0 = where(pg, RD)
    pg.locator(f'{RD} .rd-mode button', has_text='한 쪽').click(); pg.wait_for_timeout(500); r1 = where(pg, RD)
    pg.locator(f'{RD} .rd-mode button', has_text='펼침면').click(); pg.wait_for_timeout(500); r2 = where(pg, RD)
    mark('완성본 보기 (보기 방식)', '펼침면 -> 한 쪽 -> 펼침면에서 읽던 쪽 유지', r1.split(' /')[0] == r0.split(' /')[0].split('–')[0] and r2 == r0, (r0, r1, r2))
    close_reader(pg)
    c0 = pg.evaluate(FACTS, ED)['count']; w3 = where(pg, ED)
    pg.set_viewport_size({'width': 760, 'height': 900}); pg.wait_for_timeout(500)
    pg.locator('.view-tabs button').nth(1).click(); pg.wait_for_timeout(700); c1 = pg.evaluate(FACTS, ED)['count']; w4 = where(pg, ED)
    pg.set_viewport_size({'width': 390, 'height': 844}); pg.wait_for_timeout(700); c2 = pg.evaluate(FACTS, ED)['count']; w5 = where(pg, ED)
    pg.locator('.preview .rd-view').screenshot(path=str(OUT / 'sample-390-preview.png'))
    pg.locator('.preview .rd-turn').nth(1).click(); pg.wait_for_timeout(300); w6 = where(pg, ED)
    mark('창 크기 변경 (1440 -> 760 -> 390)', '쪽 수가 그대로이고 읽던 쪽이 유지됨, 390px에서도 다음 쪽으로 넘어감', c0 == c1 == c2 and w3 == w4 == w5 and w6 != w5, (c0, c1, c2, w3, w4, w5, w6))
    pg.set_viewport_size({'width': 1440, 'height': 900}); pg.wait_for_timeout(500)
    ctx.close()

    # ---------- the case books (including a legacy file) ----------
    for name, proj in CASES.items():
        path = OUT / f'{name}.json'; path.write_text(json.dumps(proj, ensure_ascii=False), encoding='utf-8')
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}); ctx.add_init_script('window.print = () => {};')
        pg = ctx.new_page(); pg.set_default_timeout(15000)
        pg.on('pageerror', lambda e, n=name: errors.append(f'{n}: {e}'))
        ns['URL'] = URL; ns['open_studio'](pg); ns['import_case'](pg, path)
        base, rd = book_in_all_screens(pg, name)
        if name == 'legacy':
            txt = pg.evaluate("[...document.querySelectorAll('.preview .pv-flow .bk-p')].map(e => e.textContent).join('')")
            mark('기존 저장 파일', '예전 파일의 원고가 그대로 보이고 디자인 키가 유지됨', '예전 원고' in pg.evaluate("document.querySelector('.preview .pv-flow').textContent") and base['theme'] == 'warm', base['theme'])
        if name == 'images':
            imgs = pg.evaluate("[...document.querySelectorAll('.preview .pv-flow .bk-fig img')].map(i => [i.naturalWidth, i.naturalHeight, Math.round(i.getBoundingClientRect().width / i.getBoundingClientRect().height * 100) / 100])")
            mark('작성 중 미리보기 (1~8단계)', 'images: 가로·세로 그림이 원래 비율로 보임', all(abs(r - w / h) < 0.02 for w, h, r in imgs), imgs)
        print(name, 'pages', base['count'], 'reader', rd['count'])
        ctx.close()
    b.close()

(OUT / 'table.json').write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding='utf-8')
for screen, checks in table.items():
    print(f'[{screen}]'); [print('  ', 'ok  ' if v == 'ok' else 'FAIL', k, '' if v == 'ok' else v) for k, v in checks.items()]
print('errors:', errors or 0)
print('FAIL' if fails or errors else 'PASS', *fails, sep='\n')
sys.exit(1 if fails or errors else 0)
