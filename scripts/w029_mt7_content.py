"""W-029 / MT-7: content fixes from the representative-screen review (docs/meetings/MT-7.md). Run once:
python scripts/w029_mt7_content.py"""
import json
from pathlib import Path

EDU = Path(__file__).resolve().parent.parent / 'src' / 'data' / 'education.json'
edu = json.loads(EDU.read_text(encoding='utf-8'))
ph = {p['id']: p for p in edu['phases']}
assert ph['edit']['handoffs'][0]['from'] == 'author', 'already applied'

# T-023 #1: the book does not go back to a draft between stations.
e0 = ph['edit']['handoffs'][0]
e0.update({'from': 'editor', 'to': 'author', 'item': '교정 의견을 단 원고', 'by': 'editor'})
# T-023 #2, #3: natural verbs and concrete follow-ups.
m = ph['market']['handoffs']
m[0]['item'] = '책 정보와 핵심 내용을 정리한 자료'
m[1].update({'back': True, 'revise': "출판 마케터가 '같은 길도 천천히 걸으면 다른 이야기가 보인다.'를 한 줄 문구로 뽑아 보내요."})
m[2]['verb'] = '전해요'
m[3]['revise'] = "기획편집자가 다음 쇄 뒤표지에 '수업에서 함께 읽고 등굣길을 관찰해 보기 좋은 책'이라는 문장을 더하고, 선생님·학부모용 소개 자료를 따로 만들어요."
ph['print']['handoffs'][3]['revise'] = '북디자이너가 그림 2를 원본 파일로 바꿔 인쇄용 파일을 다시 보내요.'
ph['edit']['handoffs'][3]['revise'] = '북디자이너가 그림과 설명을 같은 쪽에 다시 앉혀요.'
# T-023 #6: the comment matches the plan-c2 draft (which has no shop names yet).
ph['plan']['handoffs'][2]['says'] = '어떤 가게인지, 언제 문을 열었는지 독자가 알 수 있게 써 주세요. 들은 내용은 사장님께 다시 확인해 주세요.'
c2 = next(c for c in ph['plan']['case'] if c['id'] == 'plan-c2')
c2['after']['label'] = '수정 원고(예시 책 본문 그대로)'
c2['changes'][2]['why'] = '직접 확인한 내용이라 독자가 믿고 읽을 수 있어요.'
# T-023 #4: the author note explains who 「책공방 편집부」 is and matches the blurb's 「한 학생」.
sub = {s['id']: s for p in edu['phases'] for s in p['substeps']}
sub['market-1']['visual']['author'] = '이 앱의 예시 책을 만든 편집부예요. 한 학생의 눈으로 학교 앞 골목의 가게 세 곳과 큰 나무를 찾아가 묻고 기록했어요.'
# T-023 #7: the text names what the figure shows.
sub['market-2']['what'] = '책이 출판사에서 도매상이나 서점을 거쳐 독자에게 가는 길과, 법으로 정한 납본을 알아봐요.'
# T-023 #8 / T-022 #5: the correct judge option is no longer a copy of the blurb shown in the reader.
j = ph['market']['judge'][0]
k = next(i for i, o in enumerate(j['options']) if o['correct'])
j['options'][k]['text'] = '학교 앞 문구점, 세탁소, 꽃집과 큰 나무를 직접 찾아가 묻고 쓴 수필. 등굣길을 새롭게 보고 싶은 중학생에게 권해요.'

EDU.write_text(json.dumps(edu, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok')
# (applied by hand on 2026-10-22 after the apply-to-all check, see W-029: print-stage 교정쇄 -> 교정지 in
#  substep print-3 output, case print-c1 title/stage/labels and the print judge situation)
