"""W-032 / MT-13: content fixes from the representative review (docs/meetings/MT-13.md). Run once:
python scripts/w032_mt13_content.py
- each change gets `mark`: the phrase in the revised text where its numbered pin sits (when there is one)
- 피드백과 수정: pin ③ says what was done; caption names the boxes by colour
- promo sheet: the legend says what each part is for (labels are already on the sheet)"""
import json
from pathlib import Path

EDU = Path(__file__).resolve().parent.parent / 'src' / 'data' / 'edu.json'.replace('edu.json', 'education.json')
edu = json.loads(EDU.read_text(encoding='utf-8'))
cases = {c['id']: c for p in edu['phases'] for c in p['case']}
sub = {s['id']: s for p in edu['phases'] for s in p['substeps']}
assert 'mark' not in cases['plan-c2']['changes'][0], 'already applied'

MARKS = {
    'plan-c1': ['매일 같은 길로 등교하는 중학생', '작은 가게와 사람들', '목적:'],
    'plan-c2': ['세 곳', '표 1', '직접 여쭈어'],
    'edit-c1': ['아침마다 지나는 골목이 있다.', '칠 분', '그러던 어느 날'],
    'market-c1': ['같은 길도 천천히 걸으면', '동네 문구점, 작은 세탁소, 꽃집', '중학생이라면'],
    'market-c2': [None, '같은 길도 천천히 걸으면 다른 이야기가 보인다.', '어제 보지 못한 것 하나를 찾아보세요'],
    'market-c3': [None, '선생님·학부모용 소개 자료', '우리 동네 골목 기록하기'],
}
for cid, marks in MARKS.items():
    after = ' '.join(cases[cid]['after']['lines'])
    for x, m in zip(cases[cid]['changes'], marks):
        if m:
            assert m in after, (cid, m)
            x['mark'] = m

cases['plan-c2']['changes'][2]['short'] = '사장님께 다시 확인함'
sub['plan-5']['visual']['caption'] = '분홍 상자가 기획편집자의 의견이고, 초록 상자가 의견을 반영한 수정 원고예요. 번호는 바뀐 곳이에요.'
sub['market-1']['visual']['parts'] = [
    ['표지', '첫눈에 어떤 책인지'], ['책 소개', '어떤 내용인지'], ['지은이 소개', '누가 썼는지'],
    ['차례', '무엇이 들어 있는지'], ['이런 독자에게', '누구에게 맞는지'],
]
EDU.write_text(json.dumps(edu, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok')
