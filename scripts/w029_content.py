"""W-029: content for the journey reading structure (docs/DESIGN.md Plan v6). Run once:
python scripts/w029_content.py
- hand-offs get who-said-it (`by`), the words (`says`) and what is revised (`revise`); `feedback` is replaced
- a new case for 「피드백과 수정」 built from the sample book's real text (sample.js)
- each sub-step may name its visual (`visual`); the promo sheet and the distribution flow carry their own text
- print-stage wording: 교정쇄 -> 교정지 in hand-offs (MT-6 renamed the sub-step to 인쇄 전 교정지 확인)"""
import json
from pathlib import Path

EDU = Path(__file__).resolve().parent.parent / 'src' / 'data' / 'education.json'
edu = json.loads(EDU.read_text(encoding='utf-8'))
ph = {p['id']: p for p in edu['phases']}
assert 'says' not in ph['plan']['handoffs'][0], 'already applied'


def H(frm, item, to, by, says, revise=None):
    x = {'from': frm, 'item': item, 'to': to, 'by': by, 'says': says, 'back': bool(revise)}
    if revise:
        x['revise'] = revise
    return x


ph['plan']['handoffs'] = [
    H('author', '아이디어 메모(골목을 천천히 걸어 본 경험)', 'planner', 'planner', '좋은 소재예요. 독자와 목적을 정해 기획안으로 만들어 봐요.'),
    H('author', '기획안 초안', 'planner', 'planner', "독자가 '누구나'라서 너무 넓어요. 독자를 좁혀 다시 정리해 주세요.",
      "저자가 독자를 '매일 같은 길로 등교하는 중학생'으로 좁혀 기획안을 고쳐요."),
    H('author', '초고', 'planner', 'planner', '가게 이름과 문을 연 해는 사장님께 다시 확인해 주세요.',
      '저자가 사장님께 다시 여쭈어 가게 이름과 문을 연 해를 표로 정리해요.'),
    H('planner', '수정 원고', 'editor', 'editor', '기획 방향을 확인했어요. 이제 편집을 시작할게요.'),
]
ph['edit']['handoffs'] = [
    H('author', '초고', 'editor', 'editor', '첫 문장이 너무 길어요. 문장을 나누고 띄어쓰기를 고쳐 주세요.',
      '저자가 의견을 읽고 첫 문단을 짧은 문장 네 개로 고쳐요.'),
    H('author', '수정 원고', 'editor', 'editor', '의견이 잘 반영됐어요. 디자이너에게 넘길게요.'),
    H('editor', '확정 원고와 그림 목록', 'designer', 'editor', 'A5 판형에 차분한 수필 느낌으로 조판해 주세요.'),
    H('designer', '조판된 본문과 표지 시안', 'editor', 'editor', '그림 1의 설명이 다음 쪽으로 밀렸어요. 같은 쪽에 맞춰 주세요.',
      '디자이너가 그림과 설명을 같은 쪽에 다시 앉혀요.'),
]
ph['print']['handoffs'] = [
    H('editor', '확정된 인쇄용 파일', 'production', 'editor', '쪽수와 판형을 보고 종이와 제본 방식을 정해 주세요.'),
    H('production', '인쇄용 파일과 제작 사양서', 'printer', 'production', '본 인쇄 전에 교정지를 먼저 뽑아 주세요.'),
    H('printer', '교정지', 'production', 'printer', '그림 2가 흐릿하게 나왔어요. 확인이 필요해요.'),
    H('production', '교정지 문제 목록', 'designer', 'production', '그림 2를 해상도가 충분한 파일로 바꿔 다시 보내 주세요.',
      '디자이너가 그림 2를 원본 파일로 바꿔 인쇄용 파일을 다시 보내요.'),
]
ph['market']['handoffs'] = [
    H('editor', '책 정보와 핵심 내용 정리', 'marketer', 'editor', '목표 독자가 누구인지 소개 자료에 꼭 담아 주세요.'),
    H('marketer', '책 소개 자료', 'bookseller', 'bookseller', '매대 소개에 쓸게요. 한 줄 문구도 있으면 좋겠어요.'),
    H('bookseller', '독자 반응', 'marketer', 'bookseller', '학생보다 선생님과 학부모가 더 많이 찾고 있어요.'),
    H('marketer', '독자 반응 정리', 'planner', 'marketer', '다음 쇄 소개 문구와 다음 기획에 반영해 주세요.',
      '기획편집자가 다음 쇄 소개 문구와 다음 책 기획에 반영해요.'),
]

# New case for 「피드백과 수정」: the after-text is the sample book's real paragraph and table (src/sample.js).
ph['plan']['case'].append({
    'id': 'plan-c2', 'stage': '초고 → 수정 원고', 'title': '기획편집자 의견을 받고 가게 이야기가 바뀌어요', 'label': '학습용 예시',
    'before': {'label': '초고와 기획편집자 의견(학습용 예시)', 'lines': [
        '초고: 골목에는 가게가 몇 군데 있었다. 오래된 가게도 있고 새로 생긴 가게도 있었다.',
        '기획편집자 의견: 어떤 가게인지, 언제 문을 열었는지 독자가 알 수 있게 써 주세요. 들은 내용은 사장님께 다시 확인해 주세요.']},
    'after': {'label': '수정 원고(예시 책의 실제 본문)', 'lines': [
        '골목에는 작은 가게가 세 곳 있었다. 나는 수첩에 가게 이름과 문을 연 해를 적었다. 사장님들께 직접 여쭈어 본 내용이다.',
        '표 1. 골목 가게 조사: 동네 문구점 1998년 · 작은 세탁소 2005년 · 꽃집 2019년']},
    'changes': [
        {'what': "'몇 군데'를 '세 곳'으로 정확히 썼어요.", 'why': '독자가 골목을 구체적으로 떠올릴 수 있어요.'},
        {'what': '가게 이름과 문을 연 해를 표로 정리했어요.', 'why': '여러 가게를 한눈에 비교할 수 있어요.'},
        {'what': '직접 여쭈어 확인한 내용이라고 밝혔어요.', 'why': '사실을 확인하는 것은 저자의 몫이고, 독자가 믿고 읽을 수 있어요.'}],
    'openEnded': False})


def sub(pid, sid):
    return next(s for s in ph[pid]['substeps'] if s['id'] == sid)


sub('plan', 'plan-3')['visual'] = {'type': 'compare', 'caseId': 'plan-c1', 'caption': '독자·주제·차례가 분명해지면 무엇을 쓸지 정해져요.'}
sub('plan', 'plan-5')['visual'] = {'type': 'compare', 'caseId': 'plan-c2', 'caption': '분홍 상자가 기획편집자의 의견, 오른쪽이 의견을 반영한 원고예요.'}
sub('edit', 'edit-2')['visual'] = {'type': 'compare', 'caseId': 'edit-c1', 'caption': '편집자 의견 세 개가 각각 어떤 수정으로 이어졌는지 비교해 보세요.'}
sub('edit', 'edit-3')['visual'] = {'type': 'sizes', 'caption': '같은 글도 판형이 바뀌면 한 줄에 들어가는 글자 수와 쪽수가 달라져요. 어느 쪽이 맞는지는 책의 성격에 따라 달라요.'}
sub('edit', 'edit-4')['visual'] = {'type': 'typeset', 'caseId': 'edit-c2', 'caption': '흩어져 있던 제목·본문·그림·설명이 한 쪽 안에 자리를 잡아요.'}
sub('print', 'print-3')['visual'] = {'type': 'proof', 'caseId': 'print-c1', 'caption': '점선(재단선) 밖으로 나간 곳, 쪽 순서, 흐린 그림, 빠진 쪽 번호를 찾아보세요.'}
sub('market', 'market-1')['visual'] = {
    'type': 'promo', 'caseId': 'market-c1',
    'caption': '책 소개 자료에는 표지, 소개 문구, 지은이 소개, 차례, 읽을 사람이 한 장에 모여요.',
    'author': '학교 앞 골목을 천천히 걸으며 만난 가게와 사람들을 직접 묻고 기록한 예시 책의 지은이예요.',
}
sub('market', 'market-2')['visual'] = {
    'type': 'flow',
    'caption': '책은 보통 이 길을 따라 독자에게 가고, 독자 반응은 다시 출판사로 돌아와요. 출판사와 거래 방식에 따라 길이 달라요.',
    'nodes': ['출판사', '도매상·유통사', '서점(온라인·오프라인)', '독자'],
    'notes': ['출판사가 서점에 직접 공급하기도 해요.', '책을 펴내면 30일 안에 국립중앙도서관에 납본해요.', '서평, 독자 질문, 판매 흐름이 다음 쇄와 다음 기획에 반영돼요.'],
}

EDU.write_text(json.dumps(edu, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok', sum(1 for p in edu['phases'] for s in p['substeps'] if 'visual' in s), 'visuals')
