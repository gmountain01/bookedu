"""W-028: merge the T-018 draft (docs/evidence/c12/T-018_process_detail.json) into src/data/education.json.
Lead decisions applied here: substeps<-steps rename, factUpdates, new terms/sources, re-checked dates,
drop the newsis source (T-018: does not support the 15% rule). Run once: python scripts/merge_process_detail.py"""
import json
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
EDU = LAB / 'src' / 'data' / 'education.json'
edu = json.loads(EDU.read_text(encoding='utf-8'))
draft = json.loads((LAB / 'docs' / 'evidence' / 'c12' / 'T-018_process_detail.json').read_text(encoding='utf-8'))
assert 'sharedNote' not in edu, 'already merged'

for ph in edu['phases']:
    d = draft['phases'][ph['id']]
    ph.update(goal=d['goal'], flowNote=d['flowNote'], substeps=d['steps'], case=d['case'],
              handoffs=d['handoffs'], practice=d['practice'], judge=d['judge'])
edu['sharedNote'] = draft['sharedNote']
edu['terms'] += draft['newTerms']
edu['sources'] += draft['newSources']

by_id = {x['id']: x for k in ('facts', 'terms', 'sources') for x in edu[k]}
for u in draft['factUpdates']:
    target = by_id[u['id']]
    target[u['field']] = u['sourceIds'] if u['field'] == 'sourceIds' else u['new']

# Sources T-018 opened on 2026-10-22 (docs/evidence/c12/T-018_verification.md).
rechecked = {'nl-isbn-structure', 'nl-isbn-publisher', 'nl-isbn-apply', 'nl-napbon', 'nl-napbon-copies', 'korea-kr-fixedprice', 'kpipa-price'}
for s in edu['sources']:
    if s['id'] in rechecked:
        s['checkedAt'] = '2026-10-22'
edu['sources'] = [s for s in edu['sources'] if s['id'] != 'newsis-fixedprice-2023']
for k in ('facts', 'terms', 'phases', 'misconceptions'):
    for x in edu[k]:
        if 'sourceIds' in x:
            x['sourceIds'] = [i for i in x['sourceIds'] if i != 'newsis-fixedprice-2023']
# Market's practice cites the law pages and the supply-rate article.
market = next(p for p in edu['phases'] if p['id'] == 'market')
market['sourceIds'] = list(dict.fromkeys(market['sourceIds'] + ['law-publishing-22', 'law-library-21', 'law-library-decree-15']))
edu['checkedAt'] = '2026-10-22'

ids = {s['id'] for s in edu['sources']}
for k in ('facts', 'terms', 'phases', 'misconceptions'):
    for x in edu[k]:
        missing = set(x.get('sourceIds', [])) - ids
        assert not missing, (x.get('id') or x.get('q'), missing)
EDU.write_text(json.dumps(edu, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('merged:', {p['id']: len(p['substeps']) for p in edu['phases']}, 'terms', len(edu['terms']), 'sources', len(edu['sources']))
