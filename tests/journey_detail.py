"""W-030 check of the journey (docs/DESIGN.md Plan v7), fresh browser profile, file:// build.
Per station: a station menu by learning topic in the same place, one topic per screen, each sub-step's explanation
with its own example (beside it on wide screens, after the explanation on narrow ones), one pager whose ends move
between 출판 단계, no internal values or studio-open buttons, no role buttons, no horizontal scroll, page height
per topic reported. Plus the user's tasks and the keyboard path. Usage: python tests/journey_detail.py [outdir]"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else LAB / 'docs' / 'evidence' / 'journey-detail'
OUT.mkdir(parents=True, exist_ok=True)
edu = json.loads((LAB / 'src' / 'data' / 'education.json').read_text(encoding='utf-8'))
BAD = ['null', 'undefined', 'NaN', '[object']
HS = 'document.documentElement.scrollWidth - document.documentElement.clientWidth'
log, errors, heights = [], [], {}


def stage(pg, w, k):
    """Go to 출판 단계 k (0 = 시작) with the control that the viewport shows."""
    if w > 560:
        pg.locator('.pg-dot').nth(k).click()
    else:
        pg.locator('.pgp-sum').click(); pg.locator('.pgp-list button').nth(k).click()


def open_menu(pg):
    """Narrow screens: the station menu is a disclosure (open by default on 「이 단계 소개」)."""
    if pg.locator('.tm-box').get_attribute('open') is None:
        pg.locator('.tm-sum').click()


def clean(pg, where):
    t = pg.locator('main').inner_text()
    hits = [x for x in BAD if x in t]
    assert not hits, f'{where}: {hits}'
    assert '단계 열기' not in t and '「열기」' not in t, f'{where}: studio-open button/note'
    assert pg.evaluate(HS) <= 0, f'{where}: horizontal scroll'


with sync_playwright() as p:
    b = p.chromium.launch()
    for w, hh in [(1440, 900), (768, 1024), (390, 844)]:
        pg = b.new_page(viewport={'width': w, 'height': hh})
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errors.append(m.text))
        pg.goto(URL); pg.wait_for_selector('.scene')
        assert pg.locator('.pg-phone').is_visible() == (w <= 560), 'one stage control per viewport'
        for k, ph in enumerate(edu['phases']):
            stage(pg, w, k + 1)
            pg.wait_for_selector(f'.station-v7.st-{ph["id"]}')
            assert pg.evaluate("document.activeElement.classList.contains('tp-title')"), 'focus not moved after stage change'
            assert not pg.locator('.scene-nav').is_visible(), 'only the topic pager on a station'
            n_topics = len(ph['substeps']) + 4
            ids = ['overview'] + [x['id'] for x in ph['substeps']] + ['team', 'app', 'check']
            assert pg.locator('.tm-list button').count() == n_topics
            hs = []
            for t in range(n_topics):
                if w <= 900:
                    open_menu(pg)
                pg.locator('.tm-list button').nth(t).click()
                assert pg.locator('.tm-list button[aria-current=page]').count() == 1
                assert pg.evaluate("document.activeElement.classList.contains('tp-title')"), 'focus not on topic title'
                if 1 <= t <= len(ph['substeps']):
                    s = ph['substeps'][t - 1]
                    assert pg.locator('.tp-title').inner_text() == s['title']
                    assert pg.locator('.sc-vis figure.vz').count() == 1, f'{s["id"]}: example missing'
                    tb, vb = pg.locator('.rd-what').bounding_box(), pg.locator('.sc-vis').bounding_box()
                    if w >= 901:
                        assert vb['x'] > tb['x'] + tb['width'] - 1, f'{s["id"]}: example not beside text'
                    else:
                        assert pg.locator('.sc-points').bounding_box()['y'] < vb['y'], f'{s["id"]}: points before the example (Plan v9)'
                    if w != 768: pg.screenshot(path=str(OUT / f'{w}-{s["id"]}.png'), full_page=True)
                if ids[t] == 'team':
                    assert pg.locator('.story button').count() == 0 and pg.locator('.story li').count() == len(ph['handoffs'])
                    assert pg.locator('.st-step').count() == len(ph['handoffs']), 'hand-off not linked to a sub-step'
                if ids[t] == 'check':
                    assert pg.locator('.quiz').count() == 1 and pg.locator('.judge').count() == len(ph['judge'])
                clean(pg, f'{w} {ph["id"]} {ids[t]}')
                hs.append(pg.evaluate('document.documentElement.scrollHeight'))
                if w != 768 and ids[t] in ('overview', 'team', 'check'): pg.screenshot(path=str(OUT / f'{w}-{ph["id"]}-{ids[t]}.png'), full_page=True)
            heights[f'{w} {ph["id"]}'] = hs
            # judgement on the last topic: a wrong pick explains every option; reset; the right set is accepted
            j = ph['judge'][0]
            wrong = next(i for i, o in enumerate(j['options']) if not o['correct'])
            pg.locator('.judge .j-opt input').nth(wrong).check(); pg.locator('.judge button[type=submit]').click()
            assert pg.locator('.judge-result').get_attribute('data-state') == 'wrong'
            assert pg.locator('.j-why:visible').count() == len(j['options'])
            pg.locator('.judge button[type=reset]').click(); pg.wait_for_timeout(50)
            for i, o in enumerate(j['options']):
                if o['correct']: pg.locator('.judge .j-opt input').nth(i).check()
            pg.locator('.judge button[type=submit]').click()
            assert pg.locator('.judge-result').get_attribute('data-state') == 'right'
            assert '다음 출판 단계' in pg.locator('.tp-pager').inner_text(), 'last topic should lead to the next 출판 단계'
        log.append(f'{w}: 4 stations, every topic: one menu item current, focus on title, example beside/after text, clean, 0 hscroll')
        pg.close()

    pg = b.new_page(viewport={'width': 1440, 'height': 900})
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(URL); pg.wait_for_selector('.scene')
    # W-031 task A: the map alone tells the flow (4 stages, things made, things handed on, loops)
    assert pg.locator('.mp-col').count() == 4 and pg.locator('.mp-hand').count() == 3 and pg.locator('.at').count() >= 9
    assert pg.locator('.mp-bar').count() == 3 and pg.locator('.mp-loops li').count() == 3
    flow = pg.locator('.mp-row').inner_text()
    for word in ('초고·수정 원고', '확정된 인쇄용 파일', '완성된 책', '책 소개 자료'):
        assert word in flow, word
    log.append('Task A: map shows 4 stages, artifacts, 3 hand-overs (수정 원고 → 인쇄용 파일 → 완성된 책) and 3 drawn loops')
    # task B: editor + book designer, which stage, what they check together
    pg.locator('.ov-switch button', has_text='함께 일하는 사람들').click()
    col = pg.locator('.rl-col').nth(1).inner_text()
    assert '편집자' in col and '북디자이너' in col and '함께 확인' in col
    assert pg.locator('.rl-card').count() == 8 and pg.locator('.rl-card .rl-more-btn[aria-expanded]').count() == 8  # W-044: the extra text opens in the column's notes row
    assert pg.evaluate("[...document.querySelectorAll('.rl-card')].every(c => c.querySelector('strong').offsetHeight && c.querySelector('span').offsetHeight)"), 'role cards must not need a click for the core text'
    log.append('Task B: roles view, column 2 shows 편집자 ↔ 북디자이너 with what they check; 8 roles, core text visible without clicks')
    # task C: 책 소개 자료 준비 then back to the whole map with the stage marked
    pg.locator('.ov-switch button', has_text='출판 과정 지도').click()
    pg.locator('.mp-col .mp-stage').nth(3).click()
    pg.locator('.tm-list button', has_text='책 소개 자료 준비').click()
    assert pg.locator('.promo').count() == 1
    pg.locator('.tm-map').click()
    pg.wait_for_selector('.scene-overview')
    assert pg.locator('.mp-col[data-current=true] .mp-t').inner_text() == '유통과 홍보', 'stage not marked on return'
    assert pg.evaluate("document.activeElement.closest('.mp-col')?.dataset.current === 'true'"), 'focus not on the stage just seen'
    snap = pg.locator('.ov-body').aria_snapshot()
    assert '수정 원고' in snap and '확정된 인쇄용 파일' in snap, 'hand-overs not exposed to assistive tech'
    # the view the student used last is restored: roles → stage → back
    pg.locator('.ov-switch button', has_text='함께 일하는 사람들').click()
    pg.locator('.rl-col .mp-stage').nth(1).click()
    pg.locator('.tm-map').click(); pg.wait_for_selector('.scene-overview')
    assert pg.locator('.ov-switch button[aria-pressed=true]').inner_text() == '함께 일하는 사람들', 'last view not restored'
    pg.locator('.ov-switch button', has_text='출판 과정 지도').click()
    assert pg.locator('.tm-list').count() == 0
    log.append('Task C: map → 유통과 홍보 → 책 소개 자료 준비 (example beside text) → 「← 한눈에 보기」 marks 유통과 홍보, focus on it, hand-overs readable by assistive tech, last view restored')
    pg.locator('.pg-dot').nth(1).click()
    pg.locator('.tm-list button', has_text='피드백과 수정').click()
    core = pg.locator('.sc').inner_text()
    assert '기획편집자의 의견' in core and '세 곳' in core and pg.locator('.cf-p.after .pin-m').count() == 3  # Plan v9: core
    pg.locator('.sc-more > summary').click()
    assert '무엇을, 왜 바꿨나요' in pg.locator('.sc-more').inner_text()  # details layer
    log.append('Task D: 피드백과 수정 shows the planner comment, the revised text and the reasons')
    pg.locator('.pg-dot').nth(2).click(); pg.locator('.pg-dot').nth(1).click()
    assert pg.locator('.tp-title').inner_text() == '피드백과 수정', 'last topic not remembered'
    log.append('returning to a station opens its last topic')
    pg.locator('.tp-title').focus(); pg.keyboard.press('ArrowRight')
    assert pg.locator('.tp-title').inner_text() == '함께 일하는 장면'
    assert pg.locator('.tm-list button').first.inner_text() == '이 단계 소개', 'stage overview must not reuse 「한눈에 보기」'
    pg.locator('.tm-list button').first.focus(); pg.keyboard.press('ArrowRight')
    assert pg.locator('.tp-title').inner_text() == '함께 일하는 장면', 'arrow on a control changed the topic'
    pg.locator('.tm-list button').first.press('Enter')
    assert pg.evaluate("document.activeElement.classList.contains('tp-title')")
    log.append('keyboard: page arrows step topics; arrows on controls ignored; Enter on a menu item focuses the topic title')
    pg.close()

    pg = b.new_page(viewport={'width': 390, 'height': 844})
    pg.goto(URL); pg.wait_for_selector('.scene')
    stage(pg, 390, 4)
    open_menu(pg); pg.locator('.tm-list button', has_text='유통 경로 이해').click()
    ys = [pg.locator(s).bounding_box()['y'] for s in ('.tp-title', '.rd-what', '.sc-points', '.sc-vis')]
    assert ys == sorted(ys), ys
    pg.locator('.tp-pager .btn.primary').click()
    assert pg.locator('.tp-title').inner_text() == '홍보'
    open_menu(pg); pg.locator('.tm-list button').first.click()
    pg.locator('.tp-pager button').first.click()
    assert pg.locator('.station-v7.st-print').count() == 1
    pg.locator('.tm-map').click(); pg.wait_for_selector('.scene-overview')
    assert pg.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth') <= 0
    pg.locator('.ov-switch button', has_text='함께 일하는 사람들').click()
    assert pg.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth') <= 0
    log.append('Task E (390): map and roles readable without sideways scroll; back from a detail screen to the map')
    log.append('Task E (390, cont.): labelled stage control → 유통 경로 이해 (text → details → example) → 다음: 홍보 → 이전 출판 단계: 인쇄와 제작')
    b.close()

(OUT / 'journey_detail.json').write_text(json.dumps({'log': log, 'heights': heights, 'errors': errors}, ensure_ascii=False, indent=2), encoding='utf-8')
print('\n'.join(log)); print('heights per topic:', json.dumps(heights, ensure_ascii=False)); print('console errors:', errors or 'none')
assert not errors
