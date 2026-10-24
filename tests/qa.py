"""QA: the 8 required scenarios of Development_Requirements_EN.md §12, run against dist/index.html
opened via file:// (the double-click case). webapp-testing skill pattern: static HTML -> file:// + sync Playwright.
Usage: python tests/qa.py [outdir]   -> prints a table, writes results.json + screenshots + book PDF to outdir."""
import json
import os
import struct
import sys
import time
import zlib
from pathlib import Path
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else LAB / 'docs' / 'evidence' / 'qa'
OUT.mkdir(parents=True, exist_ok=True)
results = []
UNLABELED = """() => [...document.querySelectorAll('input, select, textarea')]
  .filter((el) => el.offsetParent && !(el.labels?.length || el.getAttribute('aria-label')))
  .map((el) => el.outerHTML.slice(0, 80))"""


def png(path, w=1200, h=800, noise=False):
    row = lambda: b'\x00' + (os.urandom(w * 3) if noise else bytes([30, 80, 180]) * w)
    data = zlib.compress(b''.join(row() for _ in range(h)), 1)
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', data) + chunk(b'IEND', b''))
    return path


def check(sid, name, fn):
    t = time.time()
    try:
        notes = fn() or ''
        results.append({'id': sid, 'scenario': name, 'result': 'pass', 'notes': notes})
    except Exception as e:  # noqa: BLE001 - report every failure, keep going
        results.append({'id': sid, 'scenario': name, 'result': 'fail', 'notes': f'{type(e).__name__}: {e}'[:600]})
    results[-1]['seconds'] = round(time.time() - t, 1)
    print(f"[{results[-1]['result'].upper()}] {sid} {name} :: {results[-1]['notes'][:200]}")


def new_page(browser, w=1440, h=900):
    ctx = browser.new_context(viewport={'width': w, 'height': h}, accept_downloads=True)
    ctx.add_init_script('window.print = () => { window.__printed = (window.__printed || 0) + 1; };')
    pg = ctx.new_page()
    pg.errors = []
    pg.on('pageerror', lambda e: pg.errors.append(str(e)))
    pg.on('console', lambda m: m.type == 'error' and pg.errors.append(m.text))
    pg.goto(URL)
    pg.wait_for_selector('.scene')
    return ctx, pg


def wait_saved(pg):
    pg.wait_for_function("document.querySelector('.save-state')?.dataset.status === 'saved'", timeout=5000)


def saved_where(pg, ok, timeout=6):
    """Poll IndexedDB until the stored project satisfies ok(project). 'saved' status alone can be stale."""
    end = time.time() + timeout
    while time.time() < end:
        p = project(pg)
        if p and ok(p):
            return p
        pg.wait_for_timeout(150)
    raise AssertionError('IndexedDB never reached the expected state')


def go_finish(pg):
    """Journey start buttons live on the last scene."""
    if not pg.locator('.scene-finish').count():
        pg.locator('.pg-dot').last.click()
        pg.wait_for_selector('.scene-finish')


def step(pg, n):
    pg.locator('.step').nth(n - 1).click()
    pg.wait_for_selector(f'.step-kicker:has-text("{n}단계")')


def accept_modal(pg, label):
    pg.get_by_role('button', name=label).click()


def project(pg):
    """Read the saved project straight from IndexedDB (what survives a reload)."""
    return pg.evaluate("""() => new Promise((res, rej) => { const r = indexedDB.open('publishing-lab', 1);
      r.onsuccess = () => { const g = r.result.transaction('projects').objectStore('projects').get('current'); g.onsuccess = () => res(g.result); g.onerror = rej; }; r.onerror = rej; })""")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    # 1 -------------------------------------------------------------------
    def s1():
        ctx, pg = new_page(browser)
        import json as _j
        edu = _j.loads((LAB / 'src' / 'data' / 'education.json').read_text(encoding='utf-8'))
        pg.get_by_role('button', name='여행 시작하기').click()
        for i, ph in enumerate(edu['phases']):  # one scene per station: read, then pass its quiz
            pg.wait_for_selector(f'.scene.st-{ph["id"]}')
            assert pg.locator('.scene .art-scene').count() == 1, 'station illustration missing'
            assert pg.locator('.pg-dot[aria-current=step]').inner_text().find(ph['title']) >= 0, 'progress not on station'
            # W-030: the station quiz is in the station menu's 「확인해 보기」 topic; the pager leads to the next stage
            pg.locator('.tm-list button', has_text='확인해 보기').click()
            pg.locator('.quiz input[type=radio]').nth(ph['quiz']['answer']).check()
            pg.get_by_role('button', name='정답 확인').click()
            assert '통과' in pg.locator('.quiz-result').inner_text(), 'quiz pass not shown'
            pg.locator('.tp-pager button', has_text='다음 출판 단계').click()
        assert pg.locator('.pg-dot[data-passed=true]').count() == 4, 'passed stations not marked'
        pg.wait_for_selector('.scene-wide .fact-flip')
        pg.locator('.fact-flip').first.click()
        assert pg.locator('.fact-flip').first.get_attribute('aria-expanded') == 'true'
        pg.locator('.scene-nav .btn.primary').click()
        pg.locator('.scene-nav .btn.primary').click()
        assert pg.locator('.scene-finish').get_attribute('data-ready') == 'true', 'finish scene not unlocked'
        pg.get_by_role('button', name='일하는 사람 8명').click()
        pg.locator('dialog .flip').first.click()
        assert pg.locator('dialog .flip').first.get_attribute('aria-pressed') == 'true'
        pg.keyboard.press('Escape')
        go_finish(pg)
        pg.get_by_role('button', name='예시 책으로 시작하기').first.click()
        pg.wait_for_selector('.stepper')
        for n in range(1, 9):
            step(pg, n)
        step(pg, 7)
        assert pg.locator('.missions li[data-done=false]').count() == 1, 'step 7 mission list'
        pg.get_by_label('목차를 읽어 보고, 제목 순서와 단계가 맞는지 확인했어요').check()
        pg.wait_for_selector('.stamp-fixed')
        assert pg.locator('.missions li[data-done=false]').count() == 0, 'mission did not tick'
        step(pg, 8)
        pg.get_by_label('소개 글 (무슨 내용인지').fill('같은 길도 천천히 걸으면 다른 이야기가 보여요.')  # W-035: field moved into the 「뒤표지」 group
        pg.get_by_label('되돌아보기: 내가 고른 디자인의 이유를 한 문장으로').fill('읽기 편하게 명조 서체를 골랐다.')
        pg.wait_for_function("document.querySelector('.progress-n').textContent.startsWith('8 / 8')")
        pg.locator('.finish-row').get_by_role('button', name='완성본 보기').click()  # v5: the studio toolbar has the same button
        pg.wait_for_selector('dialog.book-dialog .full-book')
        pg.screenshot(path=str(OUT / 's1-complete-book.png'))
        pg.locator('dialog.book-dialog').get_by_role('button', name='인쇄 / PDF로 저장').click()
        assert pg.evaluate('window.__printed') >= 1, 'print not called'
        assert pg.evaluate("document.body.dataset.print") == 'book'
        pg.emulate_media(media='print')
        hidden_app = pg.evaluate("getComputedStyle(document.getElementById('app')).display")
        assert hidden_app == 'none', f'app UI visible in print: {hidden_app}'
        txt = pg.locator('#print-root').inner_text()
        assert '골목에서 찾은 이야기' in txt and '관리자' not in txt and '다음 단계' not in txt, 'print root content wrong'
        pg.pdf(path=str(OUT / 's1-book-print.pdf'), prefer_css_page_size=True)
        assert not pg.errors, pg.errors
        ctx.close()
        return '장면별 여행: 정거장 4곳 퀴즈 통과(일러스트·진행 표시), 숫자 카드, 마무리 장면 열림, 역할 카드 뒤집기, 예시 책 8/8 완료(미션 체크·완료 도장), 완성본 보기, 인쇄 미디어에서 책만 출력(PDF 저장)'
    check('S1', '처음 화면 → 과정 학습 → 예시 시작 → 8단계 → 완성 → 인쇄 미리보기', s1)

    # 2 -------------------------------------------------------------------
    def s2():
        ctx, pg = new_page(browser)
        go_finish(pg)
        pg.get_by_role('button', name='내 원고로 시작하기').first.click()
        pg.wait_for_selector('.stepper')
        pg.get_by_label('책 제목').fill('나의 첫 책')
        step(pg, 2)
        pg.get_by_role('button', name='+ 장').click()
        pg.keyboard.type('첫째 장')
        pg.get_by_role('button', name='+ 문단').click()
        ta = pg.locator('.blk-paragraph textarea').first
        ta.click()
        pg.keyboard.type('글자를 쓰는 동안 커서가 그대로 있어야 해요.')
        assert pg.evaluate("document.activeElement.tagName") == 'TEXTAREA', 'focus lost while typing'
        assert ta.input_value().endswith('있어야 해요.'), 'text lost'
        pg.get_by_role('button', name='+ 절').click()
        pg.keyboard.type('작은 절')
        step(pg, 7)
        toc = pg.locator('.preview .bk-toc').inner_text()
        assert '첫째 장' in toc and '작은 절' in toc, f'toc: {toc}'
        pg.locator('.toc-edit input').first.fill('바뀐 장 제목')
        pg.wait_for_timeout(200)
        assert '바뀐 장 제목' in pg.locator('.preview .bk-toc').inner_text(), 'toc did not update after heading edit'
        pg.locator('.toc-edit select').nth(1).select_option('1')
        pg.wait_for_selector('.preview .bk-toc .toc-l1 >> nth=1')
        step(pg, 3)
        pg.get_by_text('B6 (128×182mm)').click()
        pg.locator('.dz-choice', has_text='정보·학습').click()  # W-033: designs renamed (key modern)
        pg.wait_for_function("document.querySelector('.pv-strip')?.dataset.theme === 'modern'")
        step(pg, 1)
        assert pg.get_by_label('책 제목').input_value() == '나의 첫 책', 'title lost after typesetting change'
        assert not pg.errors, pg.errors
        ctx.close()
        return '입력 중 포커스 유지, 제목 수정·단계 변경이 목차에 즉시 반영, 조판 변경 후 입력 보존'
    check('S2', '내 원고 → 제목 구조 변경 → 목차 갱신 → 조판 변경 → 입력 보존', s2)

    # 3 -------------------------------------------------------------------
    def s3():
        ctx, pg = new_page(browser)
        go_finish(pg)
        pg.get_by_role('button', name='예시 책으로 시작하기').first.click()
        pg.wait_for_selector('.stepper')
        step(pg, 4)
        pg.locator('.step-body input[type=file]').set_input_files(str(png(OUT / 'upload.png')))
        n0 = len(project(pg)['assets'])  # W-034: the sample now also carries its cover photograph
        pg.wait_for_selector(f'.library .asset >> nth={n0}')
        pg.locator('.library .asset').last.get_by_label('출처와 이용 조건').fill('직접 만든 테스트 그림')
        saved = saved_where(pg, lambda p: any(a.get('data') and a.get('sourceNote') for a in p['assets']))
        up = [a for a in saved['assets'] if a.get('data')]
        assert up and up[0]['width'] <= 1600, 'upload not stored or not resized'
        pg.reload()
        pg.wait_for_selector('.stepper')
        step(pg, 4)
        assert pg.locator('.library .asset').count() == n0 + 1, 'images not restored after reload'
        with pg.expect_download() as d:
            pg.locator('.file-menu summary').click()
            pg.get_by_role('button', name='JSON 백업').first.click()
        path = OUT / 's3-backup.json'
        d.value.save_as(path)
        exported = json.loads(path.read_text(encoding='utf-8'))
        if not pg.locator('.file-menu[open]').count():
            pg.locator('.file-menu summary').click()
        pg.get_by_role('button', name='새 책 시작').click()
        accept_modal(pg, '백업 없이 바꾸기')
        pg.wait_for_function("document.querySelector('.progress-n').textContent.startsWith('0 / 8')")
        pg.locator('.studio-head input[type=file]').set_input_files(str(path))
        # a blank book has no work to protect, so the import replaces it without a confirm dialog
        pg.wait_for_function("document.querySelector('.progress-n').textContent.startsWith('6 / 8')")
        back = saved_where(pg, lambda p: p['id'] == exported['id'])
        keys = ['meta', 'blocks', 'layout', 'assets', 'frontMatter', 'cover', 'reflection', 'imagePrompt']
        diff = [k for k in keys if back[k] != exported[k]]
        assert not diff, f'round-trip mismatch in {diff}'
        assert not pg.errors, pg.errors
        ctx.close()
        return f'그림 업로드(긴 변 {up[0]["width"]}px) → 새로고침 후 복원 → JSON 내보내기 → 새 책 → 가져오기, 내용 {len(keys)}개 항목 일치'
    check('S3', '그림 포함 저장 → 새로고침 → 복원 → JSON 내보내기 → 새 프로젝트로 가져오기 → 내용 일치', s3)

    # 4 -------------------------------------------------------------------
    def s4():
        ctx, pg = new_page(browser)
        go_finish(pg)
        pg.get_by_role('button', name='예시 책으로 시작하기').first.click()
        pg.wait_for_selector('.stepper')
        wait_saved(pg)
        bad = OUT / 's4-broken.json'
        bad.write_text('{"schemaVersion": 1, "meta": ', encoding='utf-8')
        pg.locator('.studio-head input[type=file]').set_input_files(str(bad))
        pg.wait_for_selector('dialog.modal:has-text("불러오지 못했어요")')
        msg1 = pg.locator('dialog.modal').inner_text()
        accept_modal(pg, '확인')
        wrong = OUT / 's4-wrongver.json'
        wrong.write_text(json.dumps({'schemaVersion': 99}), encoding='utf-8')
        pg.locator('.studio-head input[type=file]').set_input_files(str(wrong))
        pg.wait_for_selector('dialog.modal:has-text("버전")')
        accept_modal(pg, '확인')
        assert project(pg)['meta']['title'] == '골목에서 찾은 이야기', 'existing work changed by bad import'
        step(pg, 4)
        big = OUT / 's4-big.png'
        big.write_bytes(png(OUT / 'tmp.png').read_bytes() + b'\0' * (5 * 1024 * 1024 + 10))
        pg.locator('.step-body input[type=file]').set_input_files(str(big))
        pg.wait_for_selector('#toast.show:has-text("5MB")')
        svg = OUT / 's4.svg'
        svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding='utf-8')
        pg.locator('.step-body input[type=file]').set_input_files(str(svg))
        pg.wait_for_selector('#toast.show:has-text("PNG, JPEG, WebP")')
        pg.evaluate("() => { IDBObjectStore.prototype.put = function () { throw new DOMException('full', 'QuotaExceededError'); }; }")
        step(pg, 1)
        pg.get_by_label('책 제목').fill('저장 실패 시험')
        pg.wait_for_function("document.querySelector('.save-state')?.dataset.status === 'error'", timeout=5000)
        toast = pg.locator('#toast').inner_text()
        assert 'JSON' in toast, f'no actionable guidance: {toast}'
        ctx.close()
        return f'깨진 JSON·다른 버전 거부(기존 작업 유지), 5MB 초과·SVG 거부, 저장 실패 안내: "{toast[:40]}…" / "{msg1.splitlines()[1][:40]}…"'
    check('S4', '잘못된 JSON / 너무 큰 이미지 / 저장 실패 → 기존 작업 보존과 안내', s4)

    # 5 -------------------------------------------------------------------
    def s5():
        ctx, pg = new_page(browser)
        go_finish(pg)
        pg.get_by_role('button', name='예시 책으로 시작하기').first.click()
        pg.wait_for_selector('.stepper')
        step(pg, 2)
        pg.locator('.blk-paragraph textarea').first.fill('관리자 모드를 다녀와도 남아 있어야 하는 문장')
        pg.get_by_role('button', name='관리자 모드').click()
        pg.wait_for_selector('.slide')
        assert pg.locator('.topnav').inner_text().count('개발 과정') == 1 and '나만의 책' not in pg.locator('.topnav').inner_text()
        while not pg.locator('.tl-btn').count():  # walk to the timeline slide
            pg.keyboard.press('ArrowRight')
        pg.locator('.tl-btn').first.click()
        pg.wait_for_selector('.sl-title:has-text("요구사항 정의")')
        pg.locator('.slide .chip').first.click()
        pg.wait_for_selector('.deck-title:has-text("사용한 프롬프트 기법")')
        pg.wait_for_selector('.slide pre')
        pg.screenshot(path=str(OUT / 's5-prompt-detail.png'))
        pg.get_by_role('button', name='학생 화면으로 돌아가기').first.click()
        pg.wait_for_selector('.stepper')
        assert '나만의 책 만들기' in pg.locator('.topnav').inner_text() and '개발 과정' not in pg.locator('.topnav').inner_text()
        assert pg.locator('.step[aria-current=step]').inner_text().find('원고') >= 0, 'current step lost'
        assert pg.locator('.blk-paragraph textarea').first.input_value() == '관리자 모드를 다녀와도 남아 있어야 하는 문장'
        ctx.close()
        return '편집 중 관리자 모드 → 개발 단계 → 관련 프롬프트 원문 → 학생 화면 복귀, 원고와 현재 단계 유지'
    check('S5', '편집 중 관리자 모드 → 개발 기록 → 프롬프트 상세 → 학생 화면 복귀 → 원고 유지', s5)

    # 6 -------------------------------------------------------------------
    def s6():
        ctx, pg = new_page(browser)
        pg.goto(URL + '#/admin/process')
        pg.wait_for_selector('.gate')
        gate = pg.locator('.gate').inner_text()
        assert '비밀번호' in gate, 'gate does not say it is not authentication'
        pg.get_by_role('button', name='관리자 모드로 전환').click()
        pg.wait_for_selector('.slide')
        pg.get_by_role('button', name='목록·검색').click()
        statuses = pg.locator('.deck-list .badge').all_inner_texts()
        pg.goto(URL + '#/admin/prompts')
        pg.wait_for_selector('.slide')
        pg.keyboard.press('o')  # slide list: the candidate-technique slide must exist and open
        pg.locator('.deck-overview button', has_text='검토했지만 쓰지 않은 기법').click()
        last = pg.locator('.sl-title').inner_text()
        pg.get_by_role('button', name='목록·검색').click()
        pg.get_by_label('사용 상태 필터').select_option('prepared')
        n_prepared = pg.locator('.deck-list .card').count()
        pg.get_by_label('사용 상태 필터').select_option('')
        pg.get_by_label('프롬프트 검색').fill('도서정가제')
        found = pg.locator('.deck-list .card').count()
        ctx.close()
        assert '검토했지만' in last, f'candidate slide missing: {last}'
        assert n_prepared >= 1, 'prepared (not executed) prompts not distinguished'
        return f'관리자 경로 직접 접근 시 안내(인증 아님 명시), 단계 상태 {sorted(set(statuses))}, 준비됨(실행 미확인) {n_prepared}건, 검토 후보 슬라이드 있음, 검색 결과 {found}건'
    check('S6', '관리자 페이지가 계획과 실제 수행을 구분하고 미수행을 완료로 표시하지 않음', s6)

    # 7 -------------------------------------------------------------------
    def s7():
        notes = []
        for w in (390, 768, 1440):
            ctx, pg = new_page(browser, w, 860)
            for route in ('#/journey', '#/studio'):
                pg.goto(URL + route)
                pg.wait_for_timeout(300)
                over = pg.evaluate('document.documentElement.scrollWidth - innerWidth')
                assert over <= 0, f'{w}px {route}: horizontal page scroll {over}px'
                pg.screenshot(path=str(OUT / f's7-{w}-{route[2:]}.png'), full_page=route == '#/journey')
            pg.get_by_role('button', name='관리자 모드').click()
            pg.wait_for_selector('.slide')
            over = pg.evaluate('document.documentElement.scrollWidth - innerWidth')
            assert over <= 0, f'{w}px admin: horizontal page scroll {over}px'
            pg.screenshot(path=str(OUT / f's7-{w}-admin.png'))
            if w == 390:
                pg.get_by_role('button', name='학생 화면으로 돌아가기').first.click()
                pg.wait_for_selector('.view-tabs')
                assert pg.locator('.workbench .preview').is_hidden(), 'preview should be hidden in edit view on phone'
                pg.locator('.studio-head ~ .view-tabs').get_by_role('button', name='미리보기').click()
                assert pg.locator('.workbench .preview').is_visible()
            ctx.close()
        notes.append('390/768/1440px에서 가로 스크롤 없음, 휴대폰 편집/미리보기 전환')
        ctx, pg = new_page(browser)
        pg.locator('.pg-dot').nth(1).click()
        pg.locator('.more-inline summary').click()
        term = pg.locator('.term').first
        term.focus()
        pg.keyboard.press('Enter')
        pg.wait_for_selector('dialog.modal')
        pg.keyboard.press('Escape')
        pg.wait_for_timeout(100)
        assert pg.evaluate("document.activeElement.classList.contains('term')"), 'focus not restored after Esc'
        unlabeled = pg.evaluate(UNLABELED)
        pg.goto(URL + '#/studio')
        pg.wait_for_selector('.stepper')
        for n in range(1, 9):
            step(pg, n)
            unlabeled += pg.evaluate(UNLABELED)
        assert not unlabeled, f'unlabeled controls: {unlabeled[:5]}'
        pg.keyboard.press('Tab')
        ring = pg.evaluate("getComputedStyle(document.activeElement).outlineStyle")
        ctx.close()
        notes.append(f'용어 대화상자 Esc로 닫으면 포커스 복귀, 모든 입력에 이름표, 키보드 포커스 표시({ring})')
        return '; '.join(notes)
    check('S7', '390/768/1440px 레이아웃, 키보드, 대화상자 닫기·포커스 복귀, 이름표', s7)

    # 8 -------------------------------------------------------------------
    def s8():
        ctx, pg = new_page(browser)
        go_finish(pg)
        pg.get_by_role('button', name='내 원고로 시작하기').first.click()
        pg.wait_for_selector('.stepper')
        payload = '<img src=x onerror="window.__xss=1"><script>window.__xss=2</script>'
        pg.get_by_label('책 제목').fill(payload)
        step(pg, 2)
        pg.get_by_role('button', name='+ 문단').click()
        pg.keyboard.type(payload)
        step(pg, 8)
        pg.locator('.finish-row').get_by_role('button', name='완성본 보기').click()  # v5: the studio toolbar has the same button
        pg.wait_for_selector('dialog.book-dialog')
        pg.wait_for_timeout(300)
        assert pg.evaluate('window.__xss') is None, 'user HTML executed'
        assert payload in pg.locator('dialog.book-dialog').inner_text(), 'payload not shown as text'
        assert pg.locator('dialog.book-dialog img[src="x"]').count() == 0
        ctx.close()
        return '제목과 문단의 HTML/스크립트 문자열이 실행되지 않고 글자로 보임'
    check('S8', '사용자가 입력한 HTML 문자열이 코드로 실행되지 않고 글자로 보임', s8)

    # 9 (regressions from team meeting MT-1, both were P0 data-loss bugs) --------
    def s9():

        ctx, pg = new_page(browser)
        go_finish(pg)
        pg.get_by_role('button', name='내 원고로 시작하기').first.click()
        pg.wait_for_selector('.stepper')
        step(pg, 2)
        pg.get_by_role('button', name='+ 문단').click()
        pg.locator('.blk-paragraph textarea').first.fill('가' * 19990)
        pg.get_by_role('button', name='+ 장').click()
        pg.keyboard.type('abcdefgh')
        step(pg, 5)
        pg.get_by_role('button', name='+ 표 넣기').click()
        pg.wait_for_selector('#toast.show:has-text("자에 가까워서")')
        assert pg.locator('.blk-table').count() == 0, 'table added past the character limit'
        step(pg, 7)  # MT-2 #1: the step-7 heading field must respect the same limit
        pg.locator('.toc-edit input').first.click()
        pg.keyboard.press('End')
        pg.keyboard.type('WXYZ')
        pg.wait_for_timeout(1200)
        total = sum(len(b.get('text') or '') for b in saved_where(pg, lambda p: any((b.get('text') or '').startswith('abcdefgh') for b in p['blocks']))['blocks'])
        assert total <= 20000, f'step 7 pushed the manuscript to {total} chars'
        # MT-2 #2: duplicate block ids in an imported file must not make edits land in another block
        dup = OUT / 's9-dup.json'
        dup.write_text(json.dumps({'schemaVersion': 1, 'meta': {'title': '중복'}, 'assets': [], 'blocks': [
            {'id': 'dup', 'type': 'heading', 'level': 1, 'text': '제목은 그대로'}, {'id': 'dup', 'type': 'paragraph', 'text': ''}]}), encoding='utf-8')
        pg.locator('.studio-head input[type=file]').set_input_files(str(dup))
        pg.wait_for_selector('dialog.modal')
        accept_modal(pg, '백업 없이 바꾸기')
        step(pg, 2)
        pg.locator('.blk-paragraph textarea').first.fill('문단 내용')
        blocks = saved_where(pg, lambda p: p['meta']['title'] == '중복' and any(b.get('text') == '문단 내용' for b in p['blocks']))['blocks']
        assert blocks[0]['text'] == '제목은 그대로' and blocks[1]['text'] == '문단 내용' and blocks[0]['id'] != blocks[1]['id'], f'dup ids: {blocks}'
        # a stored record that fails validation must be parked, not overwritten
        pg.evaluate("""() => new Promise((res) => { const r = indexedDB.open('publishing-lab', 1); r.onsuccess = () => {
          const t = r.result.transaction('projects', 'readwrite'); t.objectStore('projects').put({ schemaVersion: 1, meta: {}, blocks: [{ id: 'x', type: 'poem', text: '소중한 글' }], assets: [] }, 'current'); t.oncomplete = res; }; })""")
        pg.reload()
        pg.wait_for_selector('dialog.modal:has-text("저장된 책을 열지 못했어요")')
        keys = pg.evaluate("""() => new Promise((res) => { const r = indexedDB.open('publishing-lab', 1); r.onsuccess = () => {
          const g = r.result.transaction('projects').objectStore('projects').getAllKeys(); g.onsuccess = () => res(g.result); }; })""")
        rec = [k for k in keys if str(k).startswith('recovery')]
        assert rec, f'no recovery copy: {keys}'
        ctx.close()
        # four large noisy photos: the backup must stay importable
        ctx, pg = new_page(browser)
        go_finish(pg)
        pg.get_by_role('button', name='예시 책으로 시작하기').first.click()
        pg.wait_for_selector('.stepper')
        step(pg, 4)
        for i in range(4):
            f = png(OUT / f'noise{i}.png', 1200, 1200, noise=True)
            pg.locator('.step-body input[type=file]').set_input_files(str(f))
            pg.wait_for_timeout(1500)
        n_assets = pg.locator('.library .asset').count()
        pg.locator('.file-menu summary').click()
        with pg.expect_download() as d:
            pg.get_by_role('button', name='JSON 백업').click()
        path = OUT / 's9-big-backup.json'
        d.value.save_as(path)
        size = path.stat().st_size
        assert size <= 20 * 1024 * 1024, f'backup {size/1048576:.1f}MB exceeds import cap'
        pg.locator('.studio-head input[type=file]').set_input_files(str(path))
        pg.wait_for_selector('dialog.modal:has-text("지금 만들던 책이 있어요")')
        ctx.close()
        for i in range(4):
            (OUT / f'noise{i}.png').unlink()
        return f'표·캡션·7단계 제목 포함 글자 수 제한 작동(합계 {total}자), 중복 id 재발급, 검증 실패한 저장본은 {rec[0]}로 보관, 큰 사진 {n_assets - 2}장 백업 {size/1048576:.1f}MB(20MB 이하, 다시 불러오기 가능)'
    check('S9', '회귀(MT-1·MT-2 지적): 글자 수 제한 우회, 중복 id, 손상 저장본 보존, 백업 용량', s9)

    browser.close()

passed = sum(r['result'] == 'pass' for r in results)
(OUT / 'results.json').write_text(json.dumps({'url': URL, 'chromium': p.chromium.name, 'passed': passed, 'total': len(results), 'results': results}, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'{passed}/{len(results)} passed')
sys.exit(0 if passed == len(results) else 1)
