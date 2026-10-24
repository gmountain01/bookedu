"""W-030 / MT-9: every sub-step gets its own example next to its text, and hand-offs say which sub-step they belong to.
Run once: python scripts/w030_content.py
New visual types: doc (a document card), check (a checklist with ✓/! marks), cover (front/spine/back from the
sample book), binding (perfect binding vs saddle stitch). All learning examples; invented numbers say 학습용 가정."""
import json
from pathlib import Path

EDU = Path(__file__).resolve().parent.parent / 'src' / 'data' / 'education.json'
edu = json.loads(EDU.read_text(encoding='utf-8'))
ph = {p['id']: p for p in edu['phases']}
sub = {s['id']: s for p in edu['phases'] for s in p['substeps']}
assert 'visual' not in sub['plan-1'], 'already applied'

sub['plan-1']['visual'] = {'type': 'doc', 'title': '독자·주제 메모', 'caption': '독자와 주제를 한두 문장으로 적어 두면 이후 모든 결정의 기준이 돼요.', 'rows': [
    ['읽을 사람', '매일 같은 길로 등교하는 중학생'],
    ['그 독자가 궁금해할 것', '날마다 지나는 골목에 무엇이 있는지'],
    ['전하고 싶은 것', '늘 지나던 길도 천천히 보면 새롭다는 것'],
    ['한 문장 주제', '학교 앞 골목을 천천히 걸으며 발견한 작은 가게와 사람들']]}
sub['plan-2']['visual'] = {'type': 'doc', 'title': '비슷한 책 조사 메모', 'caption': '실제 책 이름이 아닌 학습용 가정이에요. 비슷한 책과 무엇이 다른지 한 줄로 정리해요.', 'rows': [
    ['비슷한 책 A(가정)', '어른을 위한 동네 여행 안내서, 사진이 중심이에요.'],
    ['비슷한 책 B(가정)', '오래된 건물의 역사를 다룬 골목 이야기책이에요.'],
    ['우리 책의 다른 점', '중학생이 등굣길 골목에서 직접 묻고 기록한 수필이에요.']]}
sub['plan-4']['visual'] = {'type': 'doc', 'title': '차례와 초고 첫 부분', 'caption': '기획안의 차례에 맞춰 첫 원고를 써요. 아직 다듬지 않은 글이어도 괜찮아요.', 'rows': [
    ['차례 1장', '늘 지나던 길(천천히 걸으면 보이는 것 · 골목의 가게들 · 조사하며 배운 점)'],
    ['차례 2장', '골목의 나무(다시 걷는 길)'],
    ['초고 첫 문장', '나는 매일 아침 학교에 가는데 학교 앞에는 골목이 있고 그 골목은 교문까지 걸어서 칠분 정도 걸리는데…']]}
sub['edit-1']['visual'] = {'type': 'check', 'title': '구성 검토 메모', 'caption': '편집자는 장의 순서와 흐름, 빠진 내용을 살펴 의견을 적어요.', 'items': [
    [True, '1장(골목) 다음 2장(나무) 순서가 실제로 걷는 순서와 맞아요.'],
    [True, '가게 조사 내용이 표로 정리되어 비교하기 쉬워요.'],
    [False, "'조사하며 배운 점'이 짧아요. 무엇을 다시 확인했는지 한 문장 더 있으면 좋겠어요."]]}
sub['edit-5']['visual'] = {'type': 'cover', 'caption': '앞표지는 첫인상, 책등은 책꽂이에 꽂혔을 때, 뒤표지는 소개 글을 보여 줘요. 색과 그림은 여러 답이 가능해요.'}
sub['edit-6']['visual'] = {'type': 'check', 'title': '최종 확인 목록', 'caption': '인쇄용 파일로 넘기기 전에 앞부속·목차·본문·표지가 서로 맞는지 마지막으로 봐요.', 'items': [
    [True, '목차의 장·절 제목과 본문 제목이 같아요.'],
    [True, '판권지의 제목·지은이가 표지와 같아요.'],
    [True, '그림 1·2에 모두 설명이 붙어 있어요.'],
    [False, "표제지 부제 '등굣길 칠 분의 기록'을 표지에도 넣을지 아직 정하지 않았어요."]]}
sub['print-1']['visual'] = {'type': 'doc', 'title': '제작 사양서', 'caption': '판형과 제본 말고는 학습용 가정이에요. 실제 값은 책과 예산에 따라 제작 담당자가 정해요.', 'rows': [
    ['판형', 'A5(148×210mm)'],
    ['쪽수', '약 48쪽(학습용 가정)'],
    ['본문 종이 · 인쇄', '눈이 편한 미색 종이, 흑백(학습용 가정)'],
    ['표지', '두꺼운 종이, 컬러(학습용 가정)'],
    ['제본', '무선제본'],
    ['부수', '300부(학습용 가정)']]}
sub['print-2']['visual'] = {'type': 'check', 'title': '인쇄용 파일 확인', 'caption': '화면에서는 괜찮아 보여도 인쇄하면 문제가 되는 것을 미리 찾아요.', 'items': [
    [True, '쓴 글꼴이 파일에 함께 들어 있어요.'],
    [True, '글자와 중요한 그림이 재단선 안쪽에 있어요.'],
    [False, '그림 2의 해상도가 낮아요. 원본 파일로 바꿔야 해요.']]}
sub['print-4']['visual'] = {'type': 'binding', 'caption': '예시 책은 무선제본을 가정했어요. 얇은 책이나 잡지는 중철로 만드는 경우가 많아요.'}
sub['print-5']['visual'] = {'type': 'check', 'title': '완성품 확인', 'caption': '완성된 책 몇 권을 골라 끝까지 넘겨 보며 확인해요.', 'items': [
    [True, '빠진 쪽이나 겹친 쪽이 없어요.'],
    [True, '표지 색이 확인한 교정지와 같아요.'],
    [True, '책등 글씨가 가운데에 반듯하게 있어요.'],
    [True, '찢어지거나 구겨진 곳이 없어요.']]}

ph['market']['case'] += [
    {'id': 'market-c2', 'stage': '책 소개 자료 → 홍보 문구', 'title': '부풀린 문구가 책 내용에 맞는 문구로 바뀌어요', 'label': '학습용 예시',
     'before': {'label': '처음 쓴 홍보 문구(학습용 예시)', 'lines': ['올해 최고의 베스트셀러!', '모두가 읽은 바로 그 책!']},
     'after': {'label': '고친 홍보 문구(학습용 예시)', 'lines': ["서점 매대 한 줄 문구: '같은 길도 천천히 걸으면 다른 이야기가 보인다.'", "서점 누리집: '등굣길 칠 분, 어제 보지 못한 것 하나를 찾아보세요.'"]},
     'changes': [
         {'what': '근거 없는 과장을 뺐어요.', 'why': '사실이 아닌 문구는 독자를 속이고 책을 믿지 못하게 해요.'},
         {'what': '책의 핵심 문장을 한 줄로 썼어요.', 'why': '매대 앞에서 몇 초 만에 어떤 책인지 알 수 있어요.'},
         {'what': '독자가 해 볼 일을 제안했어요.', 'why': '읽고 나서 무엇을 얻는지 떠올리게 해요.'}],
     'openEnded': True},
    {'id': 'market-c3', 'stage': '독자 반응 → 다음 쇄와 다음 기획', 'title': '독자 반응이 다음 쇄와 다음 기획으로 이어져요', 'label': '학습용 예시',
     'before': {'label': '모은 독자 반응(학습용 예시)', 'lines': ['서점 담당자: 학생보다 선생님과 학부모가 더 많이 찾아요.', '독자 서평: 수업 시간에 같이 읽고 등굣길을 관찰하기 좋았어요.', '독자 질문: 다른 동네 골목도 이렇게 써 볼 수 있나요?']},
     'after': {'label': '다음 쇄와 다음 기획에 반영한 것(학습용 예시)', 'lines': ["뒤표지에 '수업에서 함께 읽고 등굣길을 관찰해 보기 좋은 책'이라는 문장을 더해요.", '선생님·학부모용 소개 자료를 따로 만들어요.', "다음 기획 메모: '우리 동네 골목 기록하기' 활동 책"]},
     'changes': [
         {'what': '반응을 모아 실제로 누가 읽는지 다시 봤어요.', 'why': '처음 정한 독자와 실제 독자가 다를 수 있어요.'},
         {'what': '소개 문구와 자료를 실제 독자에게 맞췄어요.', 'why': '책을 찾는 사람에게 필요한 정보를 줘요.'},
         {'what': '독자 질문을 다음 기획의 출발점으로 삼았어요.', 'why': '반응이 다음 책을 만드는 힌트가 돼요.'}],
     'openEnded': False},
]
sub['market-3']['visual'] = {'type': 'compare', 'caseId': 'market-c2', 'caption': '어느 문구가 책 내용과 맞고, 매대 앞의 독자에게 바로 읽힐까요?'}
sub['market-4']['visual'] = {'type': 'compare', 'caseId': 'market-c3', 'caption': '왼쪽(위)의 반응이 오른쪽(아래)의 결정으로 이어져요.'}

# MT-9 (content): each hand-off names the sub-step it belongs to (1-based).
links = {'plan': [1, 3, 5, 5], 'edit': [2, 2, 4, 4], 'print': [1, 3, 3, 2], 'market': [1, 3, 4, 4]}
for pid, steps in links.items():
    for x, n in zip(ph[pid]['handoffs'], steps):
        x['step'] = n

EDU.write_text(json.dumps(edu, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
missing = [s['id'] for s in sub.values() if 'visual' not in s]
print('ok; sub-steps without visual:', missing)
