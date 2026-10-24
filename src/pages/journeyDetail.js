// Shared pieces of the journey's sub-step reader (W-028 content, W-029 structure): the running-case chain,
// before/after artifacts, the typeset and proof visuals, and the situation-judgement form.
// Everything is plain HTML (keyboard + touch); the key facts are also given as text.
import { h, fill } from '../dom.js';
import { BODY_PHOTOS } from '../images.js';

export const STEP_NAMES = ['기획', '원고', '조판', '이미지 준비', '본문 배치', '앞부속', '목차', '표지와 완성'];
// The running case, in order. Each phase's comparisons sit somewhere on this chain.
const CHAIN = ['아이디어', '기획안', '차례·초고', '수정 원고', '조판된 본문·표지', '교정지·완성 책', '책 소개 자료'];
const PHASE_CHAIN = { plan: [0, 1, 2, 3], edit: [3, 4], print: [4, 5], market: [6] };

export function chainStrip(phaseId) {
  const on = PHASE_CHAIN[phaseId] || [];
  return h('ol', { class: 'chain', 'aria-label': '예시 책이 바뀌는 순서' },
    CHAIN.map((c, k) => h('li', { 'data-on': String(on.includes(k)) }, c, on.includes(k) ? h('span', { class: 'chain-here' }, ' · 이 단계') : null)));
}

export function artifact(side, a, kind, numbered) {
  const lines = (a.lines || []).map((l) => h(numbered ? 'li' : 'p', {}, l));
  return h('figure', { class: `artifact ${kind}` },
    h('figcaption', {}, h('span', { class: 'art-side' }, side), ' ', a.label),
    h('div', { class: 'art-body' }, numbered ? h('ol', {}, lines) : lines));
}

// Editor comments inside an artifact read as margin notes, so the draft text and the comments do not blur together.
export function noteLines(root) {
  root.querySelectorAll('.art-body p').forEach((el) => { if (/^(기획)?편집자 의견/.test(el.textContent)) el.classList.add('note'); });
  return root;
}

// A rendered page for the "typeset" comparison: the same sample text, unplaced vs placed on an A5 page.
export function typesetVisual() {
  const img = BODY_PHOTOS['builtin:photo-alley']?.src;
  return h('div', { class: 'ts-wrap' }, h('p', { class: 'sr' }, '조판 전후 그림: 왼쪽은 제목, 본문, 골목길 그림, 그림 설명이 따로 흩어져 있고, 오른쪽은 같은 내용이 A5 한 쪽에 제목, 본문, 그림, 그림 1 설명, 쪽 번호 12 순서로 놓여 있어요.'), h('div', { class: 'ts-visual', 'aria-hidden': 'true' },
    h('div', { class: 'ts-loose' },
      h('p', {}, '천천히 걸으면 보이는 것'),
      h('p', {}, '빠르게 지나갈 때는 몰랐던 간판, 화분, 고양이가 눈에 들어왔다. 같은 길인데도 걸음의 속도가 바뀌니 전혀 다른 장소처럼 느껴졌다.'),
      img ? h('img', { src: img, alt: '' }) : null, h('p', {}, '햇빛이 비스듬히 드는 골목')),
    h('div', { class: 'ts-page' },
      h('p', { class: 'ts-h' }, '천천히 걸으면 보이는 것'),
      h('p', { class: 'ts-p' }, '빠르게 지나갈 때는 몰랐던 간판, 화분, 고양이가 눈에 들어왔다. 같은 길인데도 걸음의 속도가 바뀌니 전혀 다른 장소처럼 느껴졌다.'),
      img ? h('img', { src: img, alt: '' }) : null,
      h('p', { class: 'ts-cap' }, '그림 1. 햇빛이 비스듬히 드는 골목'),
      h('p', { class: 'ts-no' }, '12'))));
}

// A pre-print proof of the sample book with the four problems of the print case, numbered to match the list.
export function proofVisual(marks = true) {
  const img = BODY_PHOTOS['builtin:photo-alley']?.src;
  const tree = BODY_PHOTOS['builtin:photo-pots']?.src;
  const m = (n) => (marks ? h('span', { class: `pf-mark pf-m${n}` }, String(n)) : null);
  const page = (no, ...kids) => h('div', { class: 'pf-page' }, h('span', { class: 'pf-trim' }), ...kids,
    h('p', { class: no ? 'pf-no' : 'pf-no pf-missing' }, no));
  return h('div', { class: 'pf-visual' },
    h('div', { class: 'pf-spread', tabindex: '0', role: 'img', 'aria-label': '교정지 12·13·14쪽 그림. 같은 내용을 아래 글로도 설명해요.' },
      page('12', h('p', { class: 'pf-h' }, '천천히 걸으면 보이는 것'), h('p', { class: 'pf-t' }, '빠르게 지나갈 때는 몰랐던 간판, 화분, 고양이가…'),
        img ? h('img', { class: 'pf-img1', src: img, alt: '' }) : null, h('p', { class: 'pf-cap' }, '그림 1. 햇빛이 비스듬히 드는 골목'), m(1)),
      page('13', h('p', { class: 'pf-run' }, '2장'), h('p', { class: 'pf-h' }, '2장 골목의 나무'), m(2), h('p', { class: 'pf-t' }, '골목 끝에는 큰 나무가 한 그루 있다…'),
        tree ? h('img', { class: 'pf-img2', src: tree, alt: '' }) : null, m(3)),
      page('', h('p', { class: 'pf-run' }, '1장'), h('p', { class: 'pf-h' }, '골목의 가게들'), h('p', { class: 'pf-t' }, '골목에는 작은 가게가 세 곳 있었다. 나는 수첩에 가게 이름과 문을 연 해를 적었다…'), m(4))),
    h('p', { class: 'pf-legend' }, '12·13·14쪽 교정지예요. 점선은 재단선(종이를 자르는 자리), 위쪽 작은 글씨는 장 이름이에요.', marks ? ' 번호는 아래 「전」 목록의 번호와 같아요.' : ''),
    h('p', { class: 'sr' }, '교정지 그림: 12쪽은 그림 1과 설명 글이 재단선 밖으로 나가 있어요. 13쪽에 2장 첫 쪽이 오고 그림 2가 흐려요. 14쪽에는 1장의 골목의 가게들이 이어지고 쪽 번호가 없어요.'));
}

export function judgeForm(j, key) {
  const name = `judge-${key}`;
  const type = j.multi ? 'checkbox' : 'radio';
  const result = h('div', { class: 'judge-result', role: 'status', 'aria-live': 'polite', tabindex: '-1' });
  const opts = j.options.map((o, i) => h('label', { class: 'j-opt' },
    h('input', { type, name, value: String(i) }), h('span', { class: 'j-text' }, o.text), h('span', { class: 'j-why', hidden: true })));
  const form = h('form', {
    class: 'judge',
    onsubmit: (e) => {
      e.preventDefault();
      const picked = new Set(new FormData(form).getAll(name).map(Number));
      if (!picked.size) { result.dataset.state = 'need'; result.textContent = j.multi ? '해당하는 것을 하나 이상 골라 주세요.' : '하나를 골라 주세요.'; return; }
      const right = j.options.every((o, i) => o.correct === picked.has(i));
      opts.forEach((lab, i) => {
        const o = j.options[i];
        lab.dataset.verdict = o.correct ? 'good' : 'poor';
        lab.dataset.picked = String(picked.has(i));
        const why = lab.querySelector('.j-why');
        why.hidden = false;
        const missed = j.multi && o.correct && !picked.has(i);
        why.textContent = `${o.correct ? (missed ? '! 놓쳤어요. 고쳐야 해요: ' : j.multi ? '✓ 고쳐야 해요: ' : '✓ 알맞아요: ') : (j.multi ? '✗ 문제가 아니에요: ' : '✗ 덜 알맞아요: ')}${o.why}`;
      });
      result.dataset.state = right ? 'right' : 'wrong';
      fill(result,
        h('p', {}, h('strong', {}, right ? '좋은 판단이에요.' : '다시 생각해 볼 부분이 있어요.'), ' 선택지마다 붙은 설명을 읽어 보세요.'),
        j.criteria ? h('p', {}, h('strong', {}, '판단 기준 '), j.criteria) : null,
        j.otherwise ? h('p', {}, h('strong', {}, '이럴 때는 달라져요 '), j.otherwise) : null);
      retry.hidden = false;
      result.focus({ preventScroll: true });
      result.scrollIntoView({ block: 'nearest', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    },
  },
  h('p', { class: 'j-situation' }, h('span', { class: 'ex-badge' }, '상황'), ' ', j.situation),
  h('fieldset', {}, h('legend', {}, j.question, j.multi ? h('span', { class: 'muted' }, ' (해당하는 것을 모두 골라요)') : null), h('div', { class: 'j-opts' }, opts)),
  h('div', { class: 'row' },
    h('button', { class: 'btn primary', type: 'submit' }, '판단 확인'),
    h('button', { class: 'btn', type: 'reset', hidden: true, onclick: () => { setTimeout(() => { opts.forEach((l) => { delete l.dataset.verdict; delete l.dataset.picked; l.querySelector('.j-why').hidden = true; }); result.replaceChildren(); delete result.dataset.state; retry.hidden = true; opts[0].querySelector('input').focus(); }); } }, '다시 고르기')),
  result);
  const retry = form.querySelector('button[type=reset]');
  return form;
}
