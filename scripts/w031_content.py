"""W-031: content for the whole-process map and the role diagram (docs/DESIGN.md Plan v8). Run once:
python scripts/w031_content.py
Built from data already in education.json (phases, roles, hand-offs, cases); no new facts."""
import json
from pathlib import Path

EDU = Path(__file__).resolve().parent.parent / 'src' / 'data' / 'education.json'
edu = json.loads(EDU.read_text(encoding='utf-8'))
assert 'map' not in edu, 'already applied'

edu['map'] = {
    'lead': '네 단계를 거치며 아이디어 한 줄이 손에 드는 책이 되고, 다시 독자에게 닿아요. 각 단계에서 무엇이 만들어지는지 먼저 보세요.',
    'stages': {
        'plan': {'makes': [['memo', '아이디어 메모'], ['doc', '기획안·차례'], ['draft', '초고']], 'hands': '수정 원고'},
        'edit': {'makes': [['draft-red', '편집 의견을 단 원고'], ['page', '조판된 본문'], ['cover', '표지 시안']], 'hands': '확정된 인쇄용 파일'},
        'print': {'makes': [['proof', '교정지'], ['book', '완성된 책']], 'hands': '완성된 책'},
        'market': {'makes': [['promo', '책 소개 자료'], ['talk', '독자 반응']], 'hands': None},
    },
    'loops': [
        {'from': 'edit', 'to': 'plan', 'text': '편집 의견을 받아 저자가 원고를 다시 고쳐요.'},
        {'from': 'print', 'to': 'edit', 'text': '교정지에서 찾은 문제는 편집·디자인으로 돌아가 파일을 고쳐요.'},
        {'from': 'market', 'to': 'plan', 'text': '독자 반응은 다음 쇄와 다음 기획으로 돌아가요.'},
    ],
    'overlap': '모든 일이 한 줄로만 진행되지는 않아요. 홍보를 기획 때부터 준비하기도 하고, 종이와 제본 같은 제작 사양을 편집 중에 정하기도 해요.',
}

# Key relations only (not every role with every role). type: pass (→), together (↔), back (↩).
edu['relations'] = [
    {'a': 'author', 'b': 'planner', 'type': 'together', 'phase': 'plan', 'what': '기획안과 초고를 주고받으며 의견을 나눠요'},
    {'a': 'planner', 'b': 'editor', 'type': 'pass', 'phase': 'plan', 'to': 'edit', 'what': '수정 원고'},
    {'a': 'editor', 'b': 'designer', 'type': 'together', 'phase': 'edit', 'what': '조판된 본문과 표지 시안을 함께 확인해요'},
    {'a': 'editor', 'b': 'production', 'type': 'pass', 'phase': 'edit', 'to': 'print', 'what': '확정된 인쇄용 파일'},
    {'a': 'production', 'b': 'printer', 'type': 'together', 'phase': 'print', 'what': '제작 사양서와 교정지를 함께 확인해요'},
    {'a': 'printer', 'b': 'bookseller', 'type': 'pass', 'phase': 'print', 'to': 'market', 'what': '완성된 책'},
    {'a': 'marketer', 'b': 'bookseller', 'type': 'together', 'phase': 'market', 'what': '책 소개 자료와 독자 반응을 주고받아요'},
    {'a': 'editor', 'b': 'author', 'type': 'back', 'what': '교정 의견을 단 원고 → 저자가 고쳐요'},
    {'a': 'production', 'b': 'designer', 'type': 'back', 'what': '교정지 문제 목록 → 북디자이너가 파일을 고쳐요'},
    {'a': 'editor', 'b': 'marketer', 'type': 'pass-far', 'what': '책 정보와 핵심 내용 → 소개 자료의 바탕이 돼요'},
    {'a': 'marketer', 'b': 'planner', 'type': 'back', 'what': '독자 반응 정리 → 다음 쇄와 다음 기획에 반영해요'},
]
EDU.write_text(json.dumps(edu, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ok')
# (lead, same day: the print→market pass is drawn between stages without a role pair — books reach shops through
#  the publisher's distribution, not directly from the printer: {'type':'pass','phase':'print','to':'market','what':'완성된 책(유통을 거쳐 서점으로)'})
