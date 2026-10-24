"""W-038: the completed book as an e-book reader (fresh profiles, built dist/index.html).
Checks, per book (sample + short/long/images/no-images/odd cases from tests/book_cases.py):
- views: front cover alone, then facing pages (left even, right odd), last interior page alone when it falls left,
  back cover alone; the views visit every page exactly once in order (nothing skipped or repeated)
- every block sits on the same page number in the reader as in the editor's live preview (the PDF's numbering)
- the window holds exactly the view's pages (aligned to a page edge, no part of a neighbour page)
- buttons disabled at the ends; label shows the page or range
Sample book only: rapid presses, keys (←/→/Home/End), reader contents menu, the book's own contents page link,
one page <-> spread keeps the page, window resize keeps the page, zoom pans and still turns, touch swipe (sideways turns,
vertical does not) on a 390px phone, reduced motion (no animation), close + reopen returns to the page.
Usage: python tests/reader_check.py <outdir>"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
ns = {'__file__': str(LAB / 'tests' / 'book_cases.py')}
src = (LAB / 'tests' / 'book_cases.py').read_text(encoding='utf-8')
exec(src[:src.index('def check_pdf')], ns)  # the case books and the import helper (no test run)
CASES = {k: ns['CASES'][k] for k in ('short', 'long', 'images', 'no-images', 'b6-12pt')}
fails, errors, rep = [], [], {}

STATE = """() => { const w = document.querySelector('dialog .rd-win'), v = document.querySelector('dialog .rd-view'), s = document.querySelector('dialog .rd-win .pv-scale');
  const pg = document.querySelector('dialog .rd-win .pg-cover').getBoundingClientRect().width;
  const wr = w.getBoundingClientRect(), vr = v.getBoundingClientRect(), tx = new DOMMatrix(getComputedStyle(s).transform).m41;
  const len = +w.dataset.len, shown = document.querySelector('dialog .rd-endpaper').hidden ? len : 2;
  return { where: document.querySelector('dialog .rd-where').textContent, len, a: Math.round(-tx / pg * 100) / 100, winOk: Math.abs(wr.width - shown * pg) < 0.5, endpaper: !document.querySelector('dialog .rd-endpaper').hidden,
    scrolled: w.scrollLeft + w.scrollTop + s.scrollLeft, intPage: Math.abs(pg - Math.round(pg)) < 0.02,
    inside: wr.left >= vr.left - 1 && wr.right <= vr.right + 1 && wr.top >= vr.top - 1 && wr.bottom <= vr.bottom + 1,
    fold: !document.querySelector('dialog .rd-fold').hidden, prev: document.querySelector('dialog .rd-turn').disabled, next: document.querySelectorAll('dialog .rd-turn')[1].disabled,
    pageW: pg, textPx: parseFloat(getComputedStyle(document.querySelector('dialog .rd-win .bk-p') || document.body).fontSize) * (pg / document.querySelector('dialog .rd-win .pg-cover').offsetWidth) }; }"""
# block -> page (1 = front cover) in the reader's own pages / in the editor preview (which has no lead page when single)
READER_BLOCKS = """() => { const st = document.querySelector('dialog .rd-win .pv-strip').getBoundingClientRect().left, pg = document.querySelector('dialog .rd-win .pg-cover').getBoundingClientRect().width;
  return Object.fromEntries([...document.querySelectorAll('dialog .rd-win .pv-flow [data-bid]')].map(e => [e.dataset.bid, Math.floor((e.getBoundingClientRect().left - st + 1) / pg) + 1])); }"""
PREVIEW_BLOCKS = """() => { const f = document.querySelector('.preview .pv-flow'), pg = document.querySelector('.preview .pg-cover').getBoundingClientRect().width, x0 = f.getBoundingClientRect().left;
  return Object.fromEntries([...f.querySelectorAll('[data-bid]')].map(e => [e.dataset.bid, Math.floor((e.getBoundingClientRect().left - x0 + 1) / pg) + 2])); }"""


def fail(msg):
    fails.append(msg); print('  FAIL', msg)


def state(pg):
    return pg.evaluate(STATE)


def open_reader(pg):
    pg.get_by_role('button', name='완성본 보기').first.click(); pg.wait_for_selector('dialog[open] .rd-where'); pg.wait_for_timeout(600)


def walk(pg, name, count):
    """Press next to the end; check the view sequence and the window each time."""
    seq, s = [], state(pg)
    for _ in range(count + 2):
        seq.append((round(s['a']), round(s['len'])))
        if not s['inside']: fail(f'{name}: window not inside the reader at {s["where"]}')
        if not s['winOk'] or not s['intPage']: fail(f'{name}: window width / page width wrong at {s["where"]}: {s}')
        if s['endpaper'] != (round(s['len']) == 1 and round(s['a']) == count - 2 and round(s['a']) % 2 == 1 and len(seq) > 0 and any(l == 2 for _, l in seq)): fail(f'{name}: blank facing page wrong at {s["where"]}')
        if abs(s['a'] - round(s['a'])) > 0.01 or abs(s['len'] - round(s['len'])) > 0.01: fail(f'{name}: window not on a page edge {s}')
        if s['next']: break
        pg.locator('dialog .rd-turn').nth(1).click(); pg.wait_for_timeout(60); s = state(pg)
    pages = [a + k for a, l in seq for k in range(l)]
    if pages != list(range(count)): fail(f'{name}: views do not visit pages 1..{count} once in order: {seq}')
    if seq[0] != (0, 1): fail(f'{name}: front cover not alone: {seq[0]}')
    if seq[-1] != (count - 1, 1): fail(f'{name}: back cover not alone: {seq[-1]}')
    spread = any(l == 2 for _, l in seq)
    for a, l in seq[1:-1]:
        if spread and l == 2 and a % 2 != 1: fail(f'{name}: a pair does not start on an even page: {a + 1}')
        if spread and l == 1 and (a % 2 != 1 or a != count - 2): fail(f'{name}: single page {a + 1} in the middle of spreads')
    if not s['next'] or s['prev'] is True and len(seq) > 1: fail(f'{name}: end button state wrong {s}')
    return seq


with sync_playwright() as p:
    b = p.chromium.launch()

    # ---------- the sample book, all interactions ----------
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}); ctx.add_init_script('window.print = () => {};')
    pg = ctx.new_page(); pg.set_default_timeout(15000)
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
    pg.goto(URL); pg.wait_for_selector('.scene'); pg.locator('.pg-dot').last.click()
    pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper'); pg.wait_for_timeout(800)
    pv_blocks = pg.evaluate(PREVIEW_BLOCKS)
    count_pv = int(pg.locator('.pv-head .muted').first.inner_text().split('쪽')[0])
    open_reader(pg)
    s = state(pg); rep['sample-open'] = s
    pg.screenshot(path=str(OUT / '1440-01-cover.png'))
    if not s['prev'] or s['next']: fail(f'sample: start buttons {s}')
    if '앞표지' not in s['where']: fail(f'sample: label at cover {s["where"]}')
    rd_blocks = pg.evaluate(READER_BLOCKS)
    diff = {k: (pv_blocks.get(k), v) for k, v in rd_blocks.items() if pv_blocks.get(k) != v}
    if diff or set(rd_blocks) != set(pv_blocks): fail(f'sample: block pages differ from the preview: {list(diff.items())[:4]}')
    count = int(s['where'].split('/')[1].split('쪽')[0])
    if count != count_pv: fail(f'sample: {count} pages in the reader, {count_pv} in the preview')
    pg.locator('dialog .rd-turn').nth(1).click(); pg.wait_for_timeout(250)
    s = state(pg); pg.screenshot(path=str(OUT / '1440-02-spread.png'))
    if s['where'] != f'2–3 / {count}쪽' or not s['fold'] or round(s['len']) != 2: fail(f'sample: first spread {s}')
    rep['sample-spread-textPx'] = round(s['textPx'], 1)
    pg.keyboard.press('Home'); pg.wait_for_timeout(100)
    seq = walk(pg, 'sample', count); rep['sample-views'] = seq
    pg.screenshot(path=str(OUT / '1440-03-back.png'))
    # every spread screenshot (for the visual review)
    pg.keyboard.press('Home')
    for k in range(len(seq)):
        pg.locator('dialog .rd-view').screenshot(path=str(OUT / f'1440-view-{k:02d}.png')); pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(220)
    # rapid presses: 6 clicks without waiting land on view 6
    pg.keyboard.press('Home'); pg.wait_for_timeout(50)
    for _ in range(6): pg.locator('dialog .rd-turn').nth(1).click(delay=0)
    s = state(pg); want = seq[min(6, len(seq) - 1)]
    if (round(s['a']), round(s['len'])) != want: fail(f'sample: rapid presses landed on {s["where"]}, expected view {want}')
    # keys
    pg.locator('dialog .rd-view').focus(); pg.keyboard.press('End'); s = state(pg)
    if round(s['a']) != count - 1: fail(f'sample: End -> {s["where"]}')
    pg.keyboard.press('ArrowLeft'); pg.keyboard.press('Home'); s = state(pg)
    if round(s['a']) != 0: fail(f'sample: Home -> {s["where"]}')
    pg.keyboard.press('PageDown'); s = state(pg)
    if round(s['a']) != 1: fail(f'sample: PageDown -> {s["where"]}')
    # reader contents menu: chapter 2 is on screen afterwards
    pg.locator('dialog .rd-toc > summary').click()
    items = [t.split(chr(10))[0] for t in pg.locator('dialog .rd-toc-list button').all_inner_texts()]; rep['toc'] = items
    ch2 = next((t for t in items if t.startswith('2장')), None)
    if not ch2: fail(f'sample: no chapter 2 in the contents menu {items}')
    else:
        pg.locator('dialog .rd-toc-list button', has_text=ch2).click(); pg.wait_for_timeout(250); s = state(pg)
        hp = pg.evaluate("""(t) => { const e = [...document.querySelectorAll('dialog .rd-win .pv-flow .bk-h')].find(x => x.textContent.replace(/\\s/g, '').startsWith(t.replace(/\\s/g, '')));
          const st = document.querySelector('dialog .rd-win .pv-strip').getBoundingClientRect().left, pg = document.querySelector('dialog .rd-win .pg-cover').getBoundingClientRect().width;
          return e ? Math.floor((e.getBoundingClientRect().left - st + 1) / pg) : null; }""", ch2[:4])
        if hp is None or not (round(s['a']) <= hp < round(s['a']) + round(s['len'])): fail(f'sample: contents menu -> {s["where"]}, chapter on page {hp}')
        pg.screenshot(path=str(OUT / '1440-04-toc-jump.png'))
    # the book's own contents page: click its first entry
    pg.keyboard.press('Home')
    for _ in range(len(seq)):
        if pg.evaluate("(() => { const a = document.querySelector('dialog .rd-win .bk-toc a'); if (!a) return false; const r = a.getBoundingClientRect(), w = document.querySelector('dialog .rd-win').getBoundingClientRect(); return r.left >= w.left && r.right <= w.right; })()"): break
        pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(30)
    last = pg.locator('dialog .rd-win .bk-toc a').last; target = last.get_attribute('href')[1:]
    last.click(); pg.wait_for_timeout(250); s = state(pg)
    tp = pg.evaluate("""(id) => { const e = document.getElementById(id), st = document.querySelector('dialog .rd-win .pv-strip').getBoundingClientRect().left,
      pg = document.querySelector('dialog .rd-win .pg-cover').getBoundingClientRect().width; return Math.floor((e.getBoundingClientRect().left - st + 1) / pg); }""", target)
    if not (round(s['a']) <= tp < round(s['a']) + round(s['len'])): fail(f'sample: contents page link -> {s["where"]}, heading on page {tp + 1}')
    # Tab onto a link on another page: the window must not scroll and the page with the link is shown (MT-22 T-063 #1)
    pg.keyboard.press('Home'); pg.locator('dialog .rd-view').focus()
    for _ in range(12):
        pg.keyboard.press('Tab')
        if pg.evaluate("!!document.activeElement.closest('dialog .rd-win')"): break
    s = state(pg)
    vis = pg.evaluate("(() => { const r = document.activeElement.getBoundingClientRect(), w = document.querySelector('dialog .rd-win').getBoundingClientRect(); return document.activeElement.closest('dialog .rd-win') ? r.left >= w.left - 1 && r.right <= w.right + 1 : null; })()")
    if vis is None: fail('sample: Tab never reached a link in the book')
    elif s['scrolled'] or not vis: fail(f'sample: Tab into the book scrolled the window ({s["scrolled"]}px) or the link is off screen at {s["where"]}')
    # one page at page 3 -> spread -> one page: back on page 3 (T-063 #2)
    pg.locator('dialog .rd-mode button', has_text='한 쪽').click(); pg.wait_for_timeout(500)
    pg.keyboard.press('Home'); pg.keyboard.press('ArrowRight'); pg.keyboard.press('ArrowRight')
    a3 = state(pg)['where']
    pg.locator('dialog .rd-mode button', has_text='펼침면').click(); pg.wait_for_timeout(500)
    pg.locator('dialog .rd-mode button', has_text='한 쪽').click(); pg.wait_for_timeout(500)
    if state(pg)['where'] != a3: fail(f'sample: one page -> spread -> one page drifted {a3} -> {state(pg)["where"]}')
    pg.locator('dialog .rd-mode button', has_text='펼침면').click(); pg.wait_for_timeout(500)
    # a key right after a zoom change is not lost (T-063 #3)
    pg.keyboard.press('Home'); w0 = state(pg)['where']
    pg.locator('dialog .rd-zoom').select_option('actual'); pg.locator('dialog .rd-view').focus(); pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(600)
    if state(pg)['where'] == w0: fail(f'sample: a turn right after a zoom change was lost ({w0})')
    pg.locator('dialog .rd-zoom').select_option('fit'); pg.wait_for_timeout(500)
    # Esc in the contents menu closes the menu, not the book (T-063 #6)
    pg.locator('dialog .rd-toc > summary').click(); pg.locator('dialog .rd-toc-list button').first.focus(); pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    if not pg.locator('dialog[open]').count() or pg.evaluate("document.querySelector('dialog .rd-toc').open"): fail('sample: Esc in the contents menu closed the book or left the menu open')
    pg.keyboard.press('End'); pg.wait_for_timeout(200)  # focus is back on the 차례 button: the keys still turn
    if '뒤표지' not in state(pg)['where']: fail(f'sample: End after closing the menu -> {state(pg)["where"]}')
    pg.locator('dialog .rd-toc > summary').click()
    rep['toc-pages'] = [t.strip() for t in pg.locator('dialog .rd-toc-list .rd-toc-pg').all_inner_texts()]
    pg.locator('dialog .rd-toc > summary').click()
    # one page <-> spread keeps the page
    pg.keyboard.press('Home'); pg.keyboard.press('ArrowRight'); pg.keyboard.press('ArrowRight')  # pages 4-5
    s0 = state(pg)
    pg.locator('dialog .rd-mode button', has_text='한 쪽').click(); pg.wait_for_timeout(500); s1 = state(pg)
    pg.locator('dialog .rd-mode button', has_text='펼침면').click(); pg.wait_for_timeout(500); s2 = state(pg)
    if round(s1['a']) != round(s0['a']) or round(s1['len']) != 1 or s2['where'] != s0['where']: fail(f'sample: mode switch lost the page {s0["where"]} -> {s1["where"]} -> {s2["where"]}')
    # window resize keeps the page (auto falls back to one page when two would be too small)
    pg.locator('dialog .rd-mode button', has_text='펼침면').click()
    pg.set_viewport_size({'width': 760, 'height': 900}); pg.wait_for_timeout(700); s3 = state(pg)
    pg.screenshot(path=str(OUT / '760-after-resize.png'))
    rep['resize-760'] = s3
    if not (round(s3['a']) <= round(s0['a']) < round(s3['a']) + round(s3['len'])) and round(s3['a']) != round(s0['a']): fail(f'sample: resize lost the page {s0["where"]} -> {s3["where"]}')
    pg.set_viewport_size({'width': 1440, 'height': 900}); pg.wait_for_timeout(700)
    # zoom: pans, hint shown, arrows still turn, a turn starts at the top
    pg.locator('dialog .rd-zoom').select_option('large'); pg.wait_for_timeout(600)
    pan = pg.evaluate("document.querySelector('dialog .rd-view').classList.contains('pan') && !document.querySelector('dialog .rd-panhint').hidden")
    pg.evaluate("document.querySelector('dialog .rd-view').scrollTo(200, 150)"); w0 = state(pg)['where']
    pg.locator('dialog .rd-view').focus(); pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(250)
    z = pg.evaluate("[document.querySelector('dialog .rd-view').scrollLeft, document.querySelector('dialog .rd-view').scrollTop]")
    pg.screenshot(path=str(OUT / '1440-05-zoom150.png'))
    if not pan: fail('sample: zoom 150% did not switch to panning with a hint')
    if pg.evaluate("[...document.querySelectorAll('dialog .rd-side')].some(e => e.offsetParent)"): fail('sample: side turn targets shown over a zoomed page')
    if state(pg)['where'] == w0 or z != [0, 0]: fail(f'sample: zoomed turn {w0} -> {state(pg)["where"]}, scroll {z}')
    pg.locator('dialog .rd-zoom').select_option('fit'); pg.wait_for_timeout(400)
    # close and reopen: the same page
    pg.keyboard.press('Home'); pg.keyboard.press('ArrowRight'); pg.keyboard.press('ArrowRight'); w1 = state(pg)['where']
    pg.locator('dialog[open] .bd-bar button', has_text='닫기').click(); pg.wait_for_timeout(300)
    open_reader(pg); w2 = state(pg)['where']
    if w1 != w2: fail(f'sample: reopen {w1} -> {w2}')
    rep['reopen'] = [w1, w2]
    ctx.close()

    # ---------- phone: touch swipe, one page ----------
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True, device_scale_factor=2)
    pg = ctx.new_page(); pg.set_default_timeout(15000)
    pg.on('pageerror', lambda e: errors.append(f'390: {e}'))
    pg.goto(URL); pg.wait_for_selector('.scene'); pg.locator('.pgp-sum').click(); pg.locator('.pgp-list button').last.click()
    pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper'); pg.wait_for_timeout(600)
    open_reader(pg); s = state(pg); rep['390-open'] = s
    pg.screenshot(path=str(OUT / '390-01-cover.png'))
    if round(s['len']) != 1: fail(f'390: not one page {s}')
    cdp = ctx.new_cdp_session(pg)
    box = pg.locator('dialog .rd-view').bounding_box(); cx, cy = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2

    def swipe(dx, dy):
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': cx, 'y': cy}]})
        for k in range(1, 6): cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': cx + dx * k / 5, 'y': cy + dy * k / 5}]})
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []}); pg.wait_for_timeout(300)
    swipe(-160, 10); s1 = state(pg)
    swipe(0, -200); s2 = state(pg)
    swipe(160, 0); s3 = state(pg)
    pg.locator('dialog .rd-turn').nth(1).click(); pg.locator('dialog .rd-turn').nth(1).click(); pg.wait_for_timeout(250)
    pg.screenshot(path=str(OUT / '390-02-page3.png'))
    rep['390-swipe'] = [s1['where'], s2['where'], s3['where']]
    if not s1['where'].startswith('2 /'): fail(f'390: left swipe -> {s1["where"]}')
    if s2['where'] != s1['where']: fail(f'390: vertical swipe turned the page -> {s2["where"]}')
    if not s3['where'].startswith('1 /'): fail(f'390: right swipe -> {s3["where"]}')
    if pg.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth') > 0: fail('390: horizontal page scroll')
    ctx.close()

    # ---------- reduced motion ----------
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce'); pg = ctx.new_page(); pg.set_default_timeout(15000)
    pg.goto(URL); pg.wait_for_selector('.scene'); pg.locator('.pg-dot').last.click()
    pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper'); pg.wait_for_timeout(600)
    open_reader(pg); pg.locator('dialog .rd-turn').nth(1).click()
    n_anim = pg.evaluate("document.querySelector('dialog .rd-win').getAnimations().length")
    ctx.close()
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}); pg = ctx.new_page(); pg.set_default_timeout(15000)
    pg.goto(URL); pg.wait_for_selector('.scene'); pg.locator('.pg-dot').last.click()
    pg.get_by_role('button', name='예시 책으로 시작하기').first.click(); pg.wait_for_selector('.stepper'); pg.wait_for_timeout(600)
    open_reader(pg); pg.locator('dialog .rd-turn').nth(1).click()
    n_anim_on = pg.evaluate("document.querySelector('dialog .rd-win').getAnimations().length")
    ctx.close()
    rep['animations'] = {'reduce': n_anim, 'normal': n_anim_on}
    if n_anim != 0 or n_anim_on != 1: fail(f'motion: reduce {n_anim} animations, normal {n_anim_on}')

    # ---------- case books ----------
    for name, proj in CASES.items():
        path = OUT / f'{name}.json'; path.write_text(json.dumps(proj, ensure_ascii=False), encoding='utf-8')
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}); pg = ctx.new_page(); pg.set_default_timeout(15000)
        pg.on('pageerror', lambda e, n=name: errors.append(f'{n}: {e}'))
        ns['URL'] = URL; ns['open_studio'](pg); ns['import_case'](pg, path)
        pg.locator('.step').nth(4).click(); pg.wait_for_timeout(600)
        pvb = pg.evaluate(PREVIEW_BLOCKS); cnt = int(pg.locator('.pv-head .muted').first.inner_text().split('쪽')[0])
        open_reader(pg)
        rdb = pg.evaluate(READER_BLOCKS)
        d = {k: (pvb.get(k), v) for k, v in rdb.items() if pvb.get(k) != v}
        if d or set(rdb) != set(pvb): fail(f'{name}: block pages differ {list(d.items())[:3]}')
        c2 = int(state(pg)['where'].split('/')[1].split('쪽')[0])
        if c2 != cnt: fail(f'{name}: {c2} pages in the reader, {cnt} in the preview')
        seq = walk(pg, name, cnt)
        rep[name] = {'pages': cnt, 'views': seq}
        pg.locator('dialog .rd-view').screenshot(path=str(OUT / f'case-{name}-last.png'))
        pg.keyboard.press('Home'); pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(250)
        pg.locator('dialog .rd-view').screenshot(path=str(OUT / f'case-{name}-spread1.png'))
        print(name, cnt, 'pages, views', seq)
        ctx.close()
    b.close()

(OUT / 'reader.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps({k: rep[k] for k in ('sample-views', 'sample-spread-textPx', 'toc', 'reopen', 'animations') if k in rep}, ensure_ascii=False))
print('errors:', errors or 0)
print('FAIL' if fails or errors else 'PASS', *fails, sep='\n')
sys.exit(1 if fails or errors else 0)
