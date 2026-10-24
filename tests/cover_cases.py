"""W-034 cover matrix (fresh profiles, the real JSON import). Each case is a small book with different cover inputs;
the front cover is captured from the preview, and the print PDF page 1 / last page are rendered. A contact sheet puts
all fronts side by side for the visual review. Checks: title text present, no text outside the cover box, the picture
drawn with object-fit: cover (never stretched), the credit on the back cover when a picture is used.
Usage: python tests/cover_cases.py <outdir>"""
import base64
import json
import sys
from pathlib import Path
import fitz
from PIL import Image
from playwright.sync_api import sync_playwright

LAB = Path(__file__).resolve().parent.parent
URL = (LAB / 'dist' / 'index.html').as_uri()
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
NOW = '2026-10-23T00:00:00.000Z'
src = LAB / 'docs' / 'evidence' / 'c18' / 'sources' / 'daegu-namgu-alley.jpg'   # public domain, stands in for a student's upload
up = Image.open(src); up.thumbnail((900, 900)); up.save(OUT / '_upload.jpg', quality=82)
UPLOAD = 'data:image/jpeg;base64,' + base64.b64encode((OUT / '_upload.jpg').read_bytes()).decode()
WALK = {'id': 'cv', 'builtin': 'builtin:cover-walk', 'name': '골목 산책', 'sourceNote': 'socialwalker, CC BY 2.0', 'mimeType': 'image/jpeg', 'width': 1500, 'height': 2128}
HORIZON = {'id': 'cv', 'builtin': 'builtin:cover-horizon', 'name': '노을 바다', 'sourceNote': 'Ahmed Saffu, CC0', 'mimeType': 'image/jpeg', 'width': 1240, 'height': 1759}
WINDOW = {'id': 'cv', 'builtin': 'builtin:cover-window', 'name': '창가의 빛', 'sourceNote': 'Florian Pérennès, CC0', 'mimeType': 'image/jpeg', 'width': 1240, 'height': 1759}
OWN = {'id': 'cv', 'data': UPLOAD, 'name': '내 사진', 'sourceNote': '내가 찍은 사진', 'mimeType': 'image/jpeg', 'width': up.width, 'height': up.height}


def book(name, title, sub, author, cover, assets=(), size='A5', theme='classic'):
    return {'schemaVersion': 1, 'id': f'cover-{name}', 'createdAt': NOW, 'updatedAt': NOW,
            'meta': {'title': title, 'authorAlias': author, 'genre': '수필', 'topic': '', 'targetReader': ''},
            'blocks': [{'id': 'h1', 'type': 'heading', 'level': 1, 'text': '1장 시작'}, {'id': 'p1', 'type': 'paragraph', 'text': '본문입니다.'}],
            'layout': {'pageSize': size, 'theme': theme, 'fontFamily': 'myeongjo', 'fontSize': 10, 'lineHeight': 1.75, 'margin': 18},
            'assets': list(assets), 'imagePrompt': '',
            'frontMatter': {'titlePage': sub, 'copyrightText': f'{title}\nISBN은 발급받지 않았습니다.', 'preface': ''},
            'cover': {'backgroundColor': '#e6dccf', 'backText': '뒤표지 소개 글입니다.', **cover},
            'reflection': {'designReason': ''}, 'progress': {'currentStep': 8, 'tocReviewed': False}}


W = dict(imageId='cv', layout='full', textY=0.565, textAlign='right', ink='#2a221c', accentColor='#a8322d')
CASES = {
    'full-sample': book('a', '골목에서 찾은 이야기', '등굣길 칠 분의 기록', '책공방 편집부', W, [WALK]),
    'full-long-title': book('b', '등굣길 칠 분 동안 골목에서 만난 가게와 나무와 사람들의 이야기', '', '책공방 편집부', W, [WALK]),
    'full-no-author': book('c', '짧은 책', '', '', W, [WALK]),
    'full-horizon-center': book('d', '바다를 건너는 말', '시 모음', '이름이 아주 긴 지은이 한사람 그리고 친구들', dict(imageId='cv', layout='full', textY=0.2, textAlign='center', ink='#fff6ef', backgroundColor='#b94a3f', accentColor='#b94a3f'), [HORIZON]),
    'panel-upload': book('e', '우리 동네 골목 지도', '노란 담벼락을 따라', '3학년 2반', dict(imageId='cv', layout='panel', focusX=50, focusY=60, backgroundColor='#efe7d6', accentColor='#9a5b1e'), [OWN]),
    'panel-long-title': book('f', '사진으로 남긴 우리 학교 앞 골목의 사계절 기록과 사람들', '부제가 있는 경우', '책공방', dict(imageId='cv', layout='panel', backgroundColor='#eceee2'), [OWN]),
    'full-upload-top': book('g', '노란 담벼락', '', '내 이름', dict(imageId='cv', layout='full', textY=0.07, textAlign='left', ink='#ffffff', backgroundColor='#3a3226'), [OWN]),
    'type-no-image': book('h', '그림 없는 책', '글자만으로 만든 표지', '지은이', dict(imageId='', layout='', backgroundColor='#1d4fb8')),
    'type-long': book('i', '그림이 없고 제목이 아주 긴 경우에도 표지가 무너지지 않는지 보는 책', '', '', dict(imageId='', layout='type', backgroundColor='#2f6b4f')),
    'b6-full': book('j', '골목에서 찾은 이야기', '등굣길 칠 분의 기록', '책공방 편집부', W, [WALK], size='B6'),
    # MT-18: the window photo keeps the author under the title; a long title falls back to the panel layout
    'window-full': book('l', '창가의 오후', '짧은 소설', '이름이 꽤 긴 지은이 한 사람', dict(imageId='cv', layout='full', textY=0.06, textAlign='left', ink='#f3eee4', backgroundColor='#1f2a24', accentColor='#3f8a5a'), [WINDOW]),
    'window-long-title': book('m', '창가에 앉아 오래도록 바라본 바깥 풍경과 그 사이의 이야기들', '', '지은이', dict(imageId='cv', layout='full', textY=0.06, textAlign='left', ink='#f3eee4', backgroundColor='#1f2a24', accentColor='#3f8a5a'), [WINDOW]),
    # W-035: band layout with subtitle + copy; a back introduction longer than the back cover (step 8 must warn)
    'band-copy': book('n', '골목에서 찾은 이야기', '등굣길 칠 분의 기록', '책공방 편집부', dict(imageId='cv', layout='band', copy='같은 길도 천천히 걸으면 다른 이야기가 보인다', backHeadline='땅만 보고 걷던 칠 분이, 어느 날 조금 느려졌다.'), [WALK]),
    'long-back': book('o', '긴 소개 글', '', '지은이', dict(imageId='', layout='type', backHeadline='뒤표지 소개가 너무 긴 경우', backText=chr(10).join(['소개 글이 아주 길어서 뒤표지에 다 들어가지 않는 경우에도 내용을 몰래 자르지 않고, 8단계에서 줄이라고 알려 주는지 확인하는 문단입니다.'] * 22))),
    'modern-panel': book('k', '정보 책 표지', '고딕 제목', '정보반', dict(imageId='cv', layout='panel', backgroundColor='#e6dccf'), [WALK], theme='modern'),
}
OVER = """() => { const f = document.querySelector('.pv-strip .pg-cover .cv-front'); const b = f.getBoundingClientRect();
  return [...f.querySelectorAll('.cv-title, .cv-sub, .cv-author')].filter(e => { const r = e.getBoundingClientRect(); return r.left < b.left - 1 || r.right > b.right + 1 || r.top < b.top - 1 || r.bottom > b.bottom + 1; }).map(e => e.className); }"""
FIT = "() => [...document.querySelectorAll('.pv-strip .pg-cover .cv-img')].map(i => getComputedStyle(i).objectFit)"
rows, errors, shots = [], [], []
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, proj in CASES.items():
        path = OUT / f'{name}.json'; path.write_text(json.dumps(proj, ensure_ascii=False), encoding='utf-8')
        ctx = b.new_context(viewport={'width': 1440, 'height': 1000}); ctx.add_init_script('window.print = () => {};')
        pg = ctx.new_page(); pg.set_default_timeout(15000)
        pg.on('pageerror', lambda e, n=name: errors.append(f'{n}: {e}'))
        pg.on('console', lambda m, n=name: m.type == 'error' and errors.append(f'{n}: {m.text}'))
        pg.goto(URL); pg.wait_for_selector('.scene'); pg.locator('.pg-dot').last.click()
        pg.get_by_role('button', name='내 원고로 시작하기').first.click(); pg.wait_for_selector('.stepper')
        pg.locator('input[type=file][accept*="json"]').set_input_files(str(path)); pg.wait_for_timeout(500)
        if pg.locator('dialog[open]').count(): pg.locator('dialog[open] button').first.click()
        pg.locator('.step').nth(7).click(); pg.wait_for_timeout(900)
        pg.locator('.preview .rd-view').screenshot(path=str(OUT / f'{name}-preview.png')); shots.append(name)
        over = pg.evaluate(OVER); fits = pg.evaluate(FIT)
        back_warn = pg.locator('.cvp-warn', has_text='뒤표지 글이').count()
        pg.locator('.finish-row').get_by_role('button', name='인쇄 / PDF로 저장').click()
        pg.emulate_media(media='print'); pg.pdf(path=str(OUT / f'{name}.pdf'), prefer_css_page_size=True, print_background=True); pg.emulate_media(media='screen')
        doc = fitz.open(str(OUT / f'{name}.pdf'))
        front = doc[0].get_text().strip(); back = doc[-1].get_text().strip()
        doc[0].get_pixmap(matrix=fitz.Matrix(1, 1)).save(str(OUT / f'{name}-pdf1.png'))
        rows.append({'case': name, 'title_in_pdf': proj['meta']['title'].replace(' ', '')[:6] in front.replace(' ', '').replace('\n', ''),
                     'outside_cover': over, 'object_fit': fits, 'credit_on_back': ('CC' in back or '사진' in back or '그림' in back) if proj['cover'].get('imageId') else None,
                     'pdf_pages': doc.page_count, 'back_overflow_warned': back_warn, 'copy_in_pdf': (proj['cover'].get('copy') or '').replace(' ', '')[:6] in front.replace(chr(10), '').replace(' ', '') if proj['cover'].get('copy') else None})
        ctx.close()
    b.close()
# contact sheet of the fronts (preview captures)
ims = [Image.open(OUT / f'{n}-pdf1.png').convert('RGB') for n in shots]   # the printed front (the preview strip is transform-scaled)
th = 330
ims = [im.resize((round(im.width * th / im.height), th)) for im in ims]
sheet = Image.new('RGB', (sum(i.width + 12 for i in ims[:8]) + 12, 2 * (th + 12) + 12), '#8a9099')
x, y = 12, 12
for k, im in enumerate(ims):
    if k % 8 == 0 and k: x, y = 12, y + th + 12
    sheet.paste(im, (x, y)); x += im.width + 12
sheet.save(OUT / 'covers-sheet.png')
(OUT / 'cover-cases.json').write_text(json.dumps({'rows': rows, 'errors': errors}, ensure_ascii=False, indent=1), encoding='utf-8')
bad = 0
for r in rows:
    flags = [k for k, v in (('long back text not warned', r['case'] == 'long-back' and not r['back_overflow_warned']), ('false overflow warning', r['case'] != 'long-back' and r['back_overflow_warned']), ('copy missing in PDF', r['copy_in_pdf'] is False), ('title missing in PDF', not r['title_in_pdf']), ('text outside cover', bool(r['outside_cover'])), ('picture not object-fit: cover', any(f != 'cover' for f in r['object_fit'])), ('no credit on back', r['credit_on_back'] is False)) if v]
    bad += bool(flags)
    print(f"{r['case']:<22} {'FAIL ' + ', '.join(flags) if flags else 'ok'}")
print('console/page errors:', errors or 0)
sys.exit(1 if bad or errors else 0)
