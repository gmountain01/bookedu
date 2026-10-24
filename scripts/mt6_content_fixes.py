"""W-028 / MT-6: content fixes decided by the lead after review (docs/meetings/MT-6.md). Run once:
python scripts/mt6_content_fixes.py"""
import json
from pathlib import Path

EDU = Path(__file__).resolve().parent.parent / 'src' / 'data' / 'education.json'
edu = json.loads(EDU.read_text(encoding='utf-8'))
ph = {p['id']: p for p in edu['phases']}
assert not any('back' in x for p in edu['phases'] for x in p['handoffs']), 'already applied'


def sub(pid, sid):
    return next(s for s in ph[pid]['substeps'] if s['id'] == sid)


# MT-6 #B: "되돌아가기" is now an explicit field; the label is drawn by the UI, not repeated in the text.
for p in edu['phases']:
    for x in p['handoffs']:
        x['back'] = x['feedback'].startswith('되돌아가기:')
        x['feedback'] = x['feedback'].removeprefix('되돌아가기:').strip()

# MT-6 #F: the proof shows 3 pages (12, 13, 14); the missing number is on an ordinary body page, not a chapter opener.
c = ph['print']['case'][0]
c['before']['lines'][1] = "2장 첫 쪽(13쪽)이 1장의 '골목의 가게들'(14쪽)보다 앞에 끼어 있어요."
c['before']['lines'][3] = '글이 이어지는 보통 본문 쪽(14쪽)에 쪽 번호가 빠져 있어요.'
c['after']['lines'][1] = '쪽 순서를 차례와 하나씩 맞춰 1장이 모두 끝난 뒤에 2장이 오게 했어요.'
c['after']['lines'][3] = '글이 이어지는 본문 쪽마다 쪽 번호가 들어갔는지 확인했어요.'
j = ph['print']['judge'][0]
j['options'][1]['text'] = "2장 첫 쪽이 1장 '골목의 가게들'보다 앞에 끼어 있어요."
j['options'][3]['text'] = '글이 이어지는 보통 본문 쪽에 쪽 번호가 빠져 있어요.'
j['options'][3]['why'] = '독자가 목차를 보고 쪽을 찾기 어려워요. 다만 장이 시작되는 쪽은 일부러 쪽 번호를 빼기도 해요.'

# MT-6 #G: the print-stage check is the printer's proof (and press check), not the editing proof; no page-number promise.
s = sub('print', 'print-3')
s['title'] = '인쇄 전 교정지 확인'
s['what'] = '인쇄소가 뽑은 교정지로 쪽 순서, 색, 그림을 살펴요.'
s['why'] = '많이 찍기 전에 고쳐야 비용과 종이를 아낄 수 있어요.'
s['check'] = '쪽 순서와 그림 위치를 차례와 하나씩 맞춰 봤나요?'

# MT-6 #H, #I, #J
sub('edit', 'edit-6')['check'] = '목차와 본문 제목이 서로 같나요?'
ph['edit']['judge'][0]['options'][0]['text'] = '긴 문장을 뜻이 끊기는 곳에서 여러 문장으로 나눈다.'
m = ph['market']['case'][0]['after']['lines']
m[2] = '학교가 일찍 끝난 날 천천히 걸으며 만난 동네 문구점, 작은 세탁소, 꽃집, 골목 끝의 큰 나무 이야기를 직접 묻고 적었다.'

# Source check (lead, 2026-10-22): the policy-briefing link returns HTTP 404. Use the statute for the same claims.
dead = 'korea-kr-fixedprice'
edu['sources'] = [x for x in edu['sources'] if x['id'] != dead]
for k in ('facts', 'terms', 'misconceptions', 'phases'):
    for x in edu[k]:
        if dead in x.get('sourceIds', []):
            x['sourceIds'] = list(dict.fromkeys(['law-publishing-22' if i == dead else i for i in x['sourceIds']]))

ids = {x['id'] for x in edu['sources']}
assert all(set(x.get('sourceIds', [])) <= ids for k in ('facts', 'terms', 'misconceptions', 'phases') for x in edu[k])
EDU.write_text(json.dumps(edu, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok: back loops', sum(x['back'] for p in edu['phases'] for x in p['handoffs']), 'sources', len(edu['sources']))
