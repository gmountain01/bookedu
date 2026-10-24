// "책은 어떻게 만들어질까": one scene at a time — intro, 4 stations, numbers, myths, finish.
import { h, modal } from '../dom.js';
import edu from '../data/education.json';
import { hasWork, replaceProject, blankProject, setField } from '../state.js';
import { sampleProject } from '../sample.js';
import { exportJson } from './studio.js';
import { artImg } from '../art.js';
import { stationV7 } from './station.js';
import { overviewScene, showOverview } from './overview.js';

let stationKeys = null; // a v7 station handles page-level arrow keys (topic by topic)


const roleById = Object.fromEntries(edu.roles.map((r) => [r.id, r]));
const srcById = Object.fromEntries(edu.sources.map((s) => [s.id, s]));
const SCENES = [
  { id: 'intro', label: '한눈에 보기' },
  ...edu.phases.map((p) => ({ id: p.id, label: p.title, phase: p })),
  { id: 'numbers', label: '숫자' },
  { id: 'myths', label: '오해' },
  { id: 'finish', label: '마무리' },
];
// Kept in memory for this visit, so leaving and coming back resumes where the student was.
const passed = new Set();
let current = 0;

const sourceLinks = (ids = []) => ids.length
  ? h('p', { class: 'src' }, '근거: ', ids.map((id, i) => [i ? ', ' : '',
    h('a', { href: srcById[id]?.url, target: '_blank', rel: 'noopener' }, srcById[id]?.title || id), ` (확인 ${srcById[id]?.checkedAt})`]))
  : null;

// Asks before replacing existing work (SIM-02). Returns true when the caller may proceed.
export async function confirmReplace(what) {
  if (!hasWork()) return true;
  const r = await modal({
    title: '지금 만들던 책이 있어요',
    body: h('p', {}, `${what}으로 바꾸면 지금 책은 이 브라우저에서 사라져요. 먼저 JSON 파일로 백업해 둘 수 있어요.`),
    actions: [
      { label: '백업하고 바꾸기', value: 'backup', primary: true },
      { label: '백업 없이 바꾸기', value: 'replace', danger: true },
      { label: '취소', value: 'cancel' },
    ],
  });
  if (r === 'backup') { exportJson(); return true; }
  return r === 'replace';
}
export async function startSample() {
  if (!(await confirmReplace('예시 책'))) return;
  replaceProject(sampleProject());
  location.hash = '#/studio';
}
export async function startBlank() {
  if (!(await confirmReplace('빈 책'))) return;
  replaceProject(blankProject());
  setField('progress.currentStep', 1);
  location.hash = '#/studio';
}

// ---------- pop-up references (kept out of the main flow) ----------
const close = [{ label: '닫기', value: 'close', primary: true }];
const termModal = (t) => modal({
  title: t.term,
  body: [t.aka ? h('p', { class: 'muted' }, `다른 이름: ${t.aka}`) : null, h('p', {}, t.definition), h('p', {}, h('strong', {}, '예: '), t.example), sourceLinks(t.sourceIds)],
  actions: close,
});
const termButton = (t) => h('button', { type: 'button', class: 'term', 'aria-haspopup': 'dialog', onclick: () => termModal(t) }, t.term);
function roleCard(r) {
  const card = h('button', {
    type: 'button', class: 'flip', 'aria-pressed': 'false',
    onclick: () => card.setAttribute('aria-pressed', String(card.getAttribute('aria-pressed') !== 'true')),
  },
  h('span', { class: 'flip-front' }, h('strong', {}, r.name), h('span', {}, r.oneLine), h('small', {}, '눌러서 자세히')),
  h('span', { class: 'flip-back' }, r.detail));
  return card;
}
const peopleModal = (roles, title) => modal({ title, body: h('div', { class: 'flips' }, roles.map(roleCard)), actions: close });
function glossaryModal() {
  const list = h('dl', { class: 'glossary' });
  const render = (q = '') => {
    const hits = edu.terms.filter((t) => `${t.term} ${t.aka || ''} ${t.definition}`.includes(q.trim()));
    list.replaceChildren(...(hits.length ? hits.map((t) => h('div', {}, h('dt', {}, t.term, t.aka ? h('span', { class: 'muted' }, ` (${t.aka})`) : null), h('dd', {}, t.definition)))
      : [h('p', { class: 'muted' }, `'${q}'와(과) 맞는 용어가 없어요.`)]));
  };
  render();
  return modal({
    title: `출판 용어 사전 (${edu.terms.length}개)`,
    body: [h('label', { class: 'field' }, h('span', {}, '용어 검색'), h('input', { type: 'search', placeholder: '예: 판권, 조판', oninput: (e) => render(e.target.value) })), list],
    actions: close,
  });
}
const sourcesModal = () => modal({
  title: `참고한 자료 (${edu.sources.length}개)`,
  body: h('ul', { class: 'sources' }, edu.sources.map((s) => h('li', {}, h('a', { href: s.url, target: '_blank', rel: 'noopener' }, s.title), ` · ${s.publisher} · 확인 ${s.checkedAt}`))),
  actions: close,
});

// ---------- scenes ----------
function quizForm(phase, onPass) {
  const q = phase.quiz;
  const name = `quiz-${phase.id}`;
  const result = h('div', { class: 'quiz-result', role: 'status', 'aria-live': 'polite' });
  const form = h('form', {
    class: 'quiz',
    onsubmit: (e) => {
      e.preventDefault();
      const picked = new FormData(form).get(name);
      if (picked == null) { result.textContent = '답을 하나 골라 주세요.'; result.dataset.state = 'need'; return; }
      const right = +picked === q.answer;
      result.dataset.state = right ? 'right' : 'wrong';
      result.replaceChildren(h('strong', {}, right ? '정답이에요. 이 단계 통과! ' : `아쉬워요. 정답은 '${q.options[q.answer]}'${/[가-힣]$/.test(q.options[q.answer]) && (q.options[q.answer].slice(-1).charCodeAt(0) - 0xac00) % 28 ? '이에요' : '예요'}. 해설을 읽고 다시 골라 보세요. `), q.explanation);
      if (right) onPass();
    },
  },
  h('fieldset', {},
    h('legend', {}, h('span', { class: 'quiz-tag' }, q.type === 'ox' ? 'O/X 퀴즈' : '퀴즈'), ' ', q.question),
    h('div', { class: 'quiz-opts' }, q.options.map((o, i) => h('label', {}, h('input', { type: 'radio', name, value: String(i) }), h('span', {}, o))))),
  h('button', { class: 'btn primary', type: 'submit' }, '정답 확인'), result);
  return form;
}

function stationScene(p, idx, refresh, go) {
  const stage = (k, word) => (SCENES[k] ? { label: word === 'prev' ? `← 이전 출판 단계: ${SCENES[k].label}` : `다음 출판 단계: ${SCENES[k].label} →`, go: () => go(k) } : null);
  return stationV7(p, idx, {
    quizForm, stamp, peopleModal, termButton,
    isPassed: () => passed.has(p.id),
    onPass: () => { passed.add(p.id); refresh(); },
    prevStage: stage(idx - 1, 'prev'), nextStage: stage(idx + 1, 'next'),
    setKeys: (fn) => { stationKeys = fn; },
    toMap: (v) => { showOverview(v, p.id); go(0); },
  });
}
function stamp(parent) {
  const s = h('span', { class: 'stamp', 'aria-hidden': 'true' }, '통과');
  parent.append(s);
  setTimeout(() => s.remove(), 1600);
}

function factCard(f) {
  const back = h('div', { class: 'fact-back', hidden: true }, h('p', {}, f.explain),
    f.verified ? null : h('p', { class: 'warn' }, '확인되지 않은 내용이에요.'), sourceLinks(f.sourceIds));
  const card = h('button', {
    type: 'button', class: 'fact-flip', 'aria-expanded': 'false',
    onclick: () => { const open = card.getAttribute('aria-expanded') !== 'true'; card.setAttribute('aria-expanded', String(open)); back.hidden = !open; },
  }, h('span', { class: 'fact-l' }, f.label), h('span', { class: 'fact-hint' }, '생각해 보고 눌러 보세요'), h('span', { class: 'fact-v' }, f.value));
  return h('li', { class: 'fact' }, card, back);
}

function sceneFor(i, refresh, go) {
  const sc = SCENES[i];
  if (sc.phase) return stationScene(sc.phase, i, refresh, go);
  if (sc.id === 'intro') return overviewScene({ goStage: go, startSample });
  if (sc.id === 'numbers') {
    return h('div', { class: 'scene scene-wide' },
      h('div', { class: 'scene-head' }, h('p', { class: 'scene-kicker' }, '숫자로 맞혀 보기'), h('h2', { class: 'scene-title' }, '책에 숨은 숫자들'), h('p', { class: 'scene-lead' }, '먼저 답을 떠올린 다음 카드를 눌러 확인해요.')),
      h('ul', { class: 'facts' }, edu.facts.map(factCard)));
  }
  if (sc.id === 'myths') {
    return h('div', { class: 'scene scene-myths' },
      h('div', { class: 'scene-art' }, artImg('slide-meeting', 'art-scene', 'slide')),
      h('div', { class: 'scene-text' }, h('p', { class: 'scene-kicker' }, '오해 바로잡기'), h('h2', { class: 'scene-title' }, '이런 생각, 해 본 적 있나요?'),
        h('p', { class: 'scene-lead' }, '질문을 눌러 답을 확인해 보세요.'),
        h('div', { class: 'myths' }, edu.misconceptions.map((m) => h('details', { class: 'myth' }, h('summary', {}, h('span', { class: 'myth-q' }, 'Q'), m.q), h('p', {}, m.a), sourceLinks(m.sourceIds))))));
  }
  const all = passed.size === edu.phases.length;
  return h('div', { class: 'scene scene-finish', id: 'cta', 'data-ready': String(all) },
    h('div', { class: 'scene-art' }, artImg('finish', 'art-scene')),
    h('div', { class: 'scene-text' },
      h('p', { class: 'scene-kicker cta-state' }, all ? '네 정거장을 모두 통과했어요!' : `정거장 ${passed.size} / ${edu.phases.length} 통과 · 다 돌지 않아도 바로 시작할 수 있어요`),
      h('h2', { class: 'scene-title' }, '이제 내 책을 만들 차례예요'),
      h('p', { class: 'scene-lead' }, '8단계를 따라가면 기획부터 표지까지 나만의 디지털 책이 완성돼요. 예시 책으로 먼저 연습해도 좋아요.'),
      h('div', { class: 'scene-actions' },
        h('button', { class: 'btn primary lg', type: 'button', onclick: startSample }, '예시 책으로 시작하기'),
        h('button', { class: 'btn', type: 'button', onclick: startBlank }, '내 원고로 시작하기')),
      h('div', { class: 'refs-row' },
        h('button', { class: 'linklike', type: 'button', onclick: glossaryModal }, `용어 사전 ${edu.terms.length}개`),
        h('button', { class: 'linklike', type: 'button', onclick: () => peopleModal(edu.roles, '출판에서 일하는 사람들') }, `일하는 사람 ${edu.roles.length}명`),
        h('button', { class: 'linklike', type: 'button', onclick: sourcesModal }, `참고 자료 ${edu.sources.length}개`))));
}

export function mountJourney(root) {
  const progress = h('ol', { class: 'scene-progress', 'aria-label': '장면 목록' });
  const holder = h('section', { class: 'scene-holder' });
  const prev = h('button', { class: 'btn', type: 'button', onclick: () => go(current - 1) }, '이전');
  const next = h('button', { class: 'btn primary', type: 'button', onclick: () => go(current + 1), onanimationend: (e) => e.currentTarget.classList.remove('pulse') }, '다음');
  const where = h('span', { class: 'scene-count' });
  const progressCap = h('p', { class: 'pg-cap', 'aria-hidden': 'true' });
  const stageList = h('ol', { class: 'pgp-list' });
  const stageSum = h('summary', { class: 'pgp-sum' });
  const stagePhone = h('details', { class: 'pg-phone', onkeydown: (e) => { if (e.key === 'Escape' && stagePhone.open) { stagePhone.open = false; stageSum.focus(); } } }, stageSum, stageList);

  function renderProgress() {
    progress.replaceChildren(...SCENES.map((sc, i) => h('li', {}, h('button', {
      type: 'button', class: 'pg-dot', 'aria-current': i === current ? 'step' : null,
      'data-passed': String(!!sc.phase && passed.has(sc.id)), 'data-station': String(!!sc.phase),
      onclick: () => go(i), 'aria-label': `${i + 1}/${SCENES.length} ${sc.label}${sc.phase && passed.has(sc.id) ? ' (통과)' : ''}`,
    }, h('span', { class: 'pg-mark', 'aria-hidden': 'true' }, sc.phase && passed.has(sc.id) ? '✓' : ''), h('span', { class: 'pg-label' }, sc.label)))));
    progressCap.textContent = `${current + 1}/${SCENES.length} · ${SCENES[current].label}`;
    stageSum.textContent = `출판 단계 ${current + 1}/${SCENES.length} · ${SCENES[current].label}`;
    stageList.replaceChildren(...SCENES.map((sc, i) => h('li', {}, h('button', {
      type: 'button', 'aria-current': i === current ? 'step' : null,
      onclick: () => { stagePhone.open = false; go(i); },
    }, sc.label, sc.phase && passed.has(sc.id) ? ' ✓' : ''))));
    const sc = SCENES[current];
    const stationNo = edu.phases.findIndex((p) => p.id === sc.id) + 1;
    where.textContent = sc.phase ? `정거장 ${stationNo} / ${edu.phases.length}` : `${current + 1} / ${SCENES.length}`;
    prev.disabled = current === 0;
    // On a station, "다음" stays secondary until its quiz is passed; then it becomes the main action.
    const waiting = !!sc.phase && !passed.has(sc.id);
    next.classList.toggle('primary', !waiting);
    if (sc.phase && passed.has(sc.id) && next.dataset.pulsed !== sc.id) { next.dataset.pulsed = sc.id; next.classList.add('pulse'); }
    // The intro scene has its own start button; a second "여행 시작" below it would compete (MT-5).
    next.hidden = current === 0 || current === SCENES.length - 1;
    next.textContent = `다음: ${SCENES[current + 1]?.label || ''}`;
    prev.textContent = current > 0 ? `이전: ${SCENES[current - 1].label}` : '이전';
  }
  function go(i, focus = true) {
    current = Math.max(0, Math.min(SCENES.length - 1, i));
    stationKeys = null;
    holder.replaceChildren(sceneFor(current, renderProgress, go));
    holder.firstChild.dataset.enter = 'true';
    renderProgress();
    const head = holder.querySelector('[data-current=true] .mp-stage') || holder.querySelector('.tp-title, .scene-title');
    if (focus) head?.setAttribute('tabindex', '-1');
    if (focus) head?.focus({ preventScroll: true });
    window.scrollTo({ top: 0 });
  }
  const onKey = (e) => {
    // Arrows belong to the focused control (tabs, lists, buttons, forms); only page-level focus changes scenes (MT-6).
    if (e.target.closest('input, textarea, select, dialog, .journey button, .journey a, .journey summary') || e.altKey || e.ctrlKey || e.metaKey) return;
    const dir = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
    if (!dir) return;
    if (stationKeys) stationKeys(dir);
    else go(current + dir);
  };
  addEventListener('keydown', onKey);

  root.append(h('div', { class: 'journey' }, progress, progressCap, stagePhone, holder,
    h('div', { class: 'scene-nav' }, prev, where, next)));
  go(current, false);
  return () => removeEventListener('keydown', onKey);
}
