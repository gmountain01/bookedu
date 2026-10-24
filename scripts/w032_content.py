"""W-032: short pin labels so the meaning of each change can sit on the picture (docs/DESIGN.md Plan v9),
and named parts for the promo sheet and the proof. The full sentences stay in the data for 「자세히 보기」.
Run once: python scripts/w032_content.py"""
import json
from pathlib import Path

EDU = Path(__file__).resolve().parent.parent / 'src' / 'data' / 'education.json'
edu = json.loads(EDU.read_text(encoding='utf-8'))
cases = {c['id']: c for p in edu['phases'] for c in p['case']}
assert 'short' not in cases['plan-c1']['changes'][0], 'already applied'

SHORT = {
    'plan-c1': ['독자를 좁혔어요', '주제를 좁혔어요', '목적·차례를 더했어요'],
    'plan-c2': ['세 곳으로 정확히', '가게를 표로 정리', '직접 확인했다고 밝힘'],
    'edit-c1': ['긴 문장을 나눔', '띄어쓰기 고침', '말투를 다듬음'],
    'edit-c2': ['제목을 크게', '그림 아래 설명', '쪽 번호'],
    'print-c1': ['재단선 안으로', '쪽 순서 바로잡기', '선명한 원본으로', '쪽 번호 채우기'],
    'market-c1': ['핵심 문장을 앞에', '책 속 내용을 구체적으로', '독자와 얻는 것'],
    'market-c2': ['과장을 뺌', '한 줄 핵심 문구', '해 볼 일 제안'],
    'market-c3': ['실제 독자 확인', '소개 자료를 맞춤', '다음 기획으로'],
}
for cid, shorts in SHORT.items():
    for x, s in zip(cases[cid]['changes'], shorts):
        x['short'] = s
    assert len(shorts) == len(cases[cid]['changes']), cid

sub = {s['id']: s for p in edu['phases'] for s in p['substeps']}
# the promo sheet: name each part and what it is for (the picture carries the labels)
sub['market-1']['visual']['parts'] = [
    ['표지', '첫눈에 어떤 책인지 보여 줘요'],
    ['책 소개', '핵심 문장 한두 줄'],
    ['지은이 소개', '누가 썼는지'],
    ['차례', '무엇이 들어 있는지'],
    ['이런 독자에게', '누구에게 맞는 책인지'],
]
# the proof: what each numbered marker points at (short)
sub['print-3']['visual']['problems'] = ['그림이 재단선 밖', '쪽 순서가 뒤바뀜', '흐릿한 그림', '쪽 번호 빠짐']

EDU.write_text(json.dumps(edu, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok')
