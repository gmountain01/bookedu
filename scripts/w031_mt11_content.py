"""W-031 / MT-11: content fixes from the representative review (docs/meetings/MT-11.md). Run once:
python scripts/w031_mt11_content.py"""
import json
from pathlib import Path

EDU = Path(__file__).resolve().parent.parent / 'src' / 'data' / 'education.json'
edu = json.loads(EDU.read_text(encoding='utf-8'))
M = edu['map']
assert 'bar' not in M['loops'][0], 'already applied'
sub = {s['id']: s for p in edu['phases'] for s in p['substeps']}

# T-033 #1, #4: loops say where the work really goes; short bar labels for the drawn return lines
M['loops'][0].update(text='편집자의 교정 의견을 받아 저자가 원고를 다시 고쳐요. 편집 단계 안에서도 저자가 함께해요.', bar='교정 의견 → 저자가 원고 수정')
M['loops'][1].update(text='인쇄 교정지에서 찾은 문제는 편집·디자인으로 돌아가 파일을 고쳐요.', bar='교정지 문제 → 파일 수정')
M['loops'][2].update(text='독자 반응은 다음 쇄 수정(편집·제작)과 다음 기획으로 돌아가요.', bar='독자 반응 → 다음 쇄·다음 기획')
# T-033 #5 / T-034 #2: the plan column shows the revised manuscript it hands on
M['stages']['plan']['makes'][2] = ['draft', '초고·수정 원고']
# T-033 #3 (print stage term) — lead decision: the map says 인쇄 교정지; the station already says 교정지 (MT-6)
M['stages']['print']['makes'][0] = ['proof', '인쇄 교정지']
# T-033 #2 / T-034 #3: books reach shops through distribution; the receiving role is named
M['stages']['print']['hands'] = '완성된 책'
M['stages']['print']['via'] = '창고·도매상을 거쳐 서점으로'
r = next(x for x in edu['relations'] if x['type'] == 'pass' and x['phase'] == 'print')
r.update(what='완성된 책', via='출판사 → 유통 → 서점 담당자')
sub['print-5']['output'] = '창고와 유통사로 보낼 완성 도서'
for f in ('what', 'why', 'output', 'check'):
    sub['print-4'][f] = sub['print-4'][f].replace('교정쇄', '교정지')
# T-034 #5: the result matches the example
sub['market-1']['output'] = '책 소개 자료(보도자료의 바탕이 돼요)'
# T-033 Q2: roles that work across stages
edu['rolesNote'] = '한 사람이 한 단계에만 머무르지는 않아요. 예를 들어 편집자는 인쇄 전 확인과 책 소개 자료 준비에도 함께해요.'

EDU.write_text(json.dumps(edu, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok')
