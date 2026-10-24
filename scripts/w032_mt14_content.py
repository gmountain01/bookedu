"""W-032 / MT-14 (T-043 #3): pins must follow reading order. In 피드백과 수정 the revised text says 「직접 여쭈어」
before 표 1, so the 'checked again' change comes second and the table third. Run once:
python scripts/w032_mt14_content.py"""
import json
from pathlib import Path

EDU = Path(__file__).resolve().parent.parent / 'src' / 'data' / 'education.json'
edu = json.loads(EDU.read_text(encoding='utf-8'))
c = next(c for p in edu['phases'] for c in p['case'] if c['id'] == 'plan-c2')
assert [x['mark'] for x in c['changes']] == ['세 곳', '표 1', '직접 여쭈어'], 'already applied'
c['changes'] = [c['changes'][0], c['changes'][2], c['changes'][1]]
# every case: marks appear in the revised text in pin order
for p in edu['phases']:
    for k in p['case']:
        text = ' '.join(k['after']['lines'])
        at = [text.index(x['mark']) for x in k.get('changes', []) if x.get('mark')]
        assert at == sorted(at), k['id']
EDU.write_text(json.dumps(edu, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok')
