// Level 0 of the journey (W-031, docs/DESIGN.md Plan v8): the whole process and the people as pictures.
// Two views on one scene: 출판 과정 지도 (what each stage makes, what it hands on, where work goes back) and
// 함께 일하는 사람들 (the eight roles in their stage, the key hand-offs and checks). HTML/CSS, text stays text.
import { h, fill } from '../dom.js';
import edu from '../data/education.json';
import { artImg } from '../art.js';
import { roleFig } from './station.js';

const roleById = Object.fromEntries(edu.roles.map((r) => [r.id, r]));
const phaseById = Object.fromEntries(edu.phases.map((p) => [p.id, p]));
let view = 'map'; // remembered for the visit
const fin = (w) => { const c = w.trim().slice(-1).charCodeAt(0) - 0xac00; return c >= 0 && c <= 11171 && c % 28 !== 0; };
const ga = (w) => `${w}${fin(w) ? '이' : '가'}`;
const ro = (w) => `${w}${fin(w) && (w.trim().slice(-1).charCodeAt(0) - 0xac00) % 28 !== 8 ? '으로' : '로'}`;
const egeseo = (w) => `${w}에서`;
let highlight = null; // phase id to mark when coming back from a station

export function showOverview(v, phaseId) { view = v || view; highlight = phaseId || null; }
const openStage = (goStage, i) => { highlight = null; goStage(i); };

// small artifact thumbnails: a shape that says "what kind of thing" + a readable label under it
const stageBtn = (p, i, goStage) => h('button', { type: 'button', class: 'mp-stage', 'aria-label': `${i + 1}단계 ${p.title} 자세히 보기${highlight === p.id ? ' (방금 본 단계)' : ''}`, onclick: () => openStage(goStage, i + 1) },
  h('span', { class: 'mp-n', 'aria-hidden': 'true' }, String(i + 1)), h('span', { class: 'mp-t', 'aria-hidden': 'true' }, p.title), h('span', { class: 'mp-go', 'aria-hidden': 'true' }, '자세히 ›'));
const hint = () => h('p', { class: 'mp-hint' }, '단계 이름 단추를 누르면 그 단계를 자세히 배워요. 세부 절차는 단계 안에서 하나씩 봐요.');

// The three return loops drawn under the columns (wide screens), each bar spanning target → source stage.
function loopBars(loops) {
  const idx = Object.fromEntries(edu.phases.map((p, i) => [p.id, i]));
  return h('div', { class: 'mp-bars', 'aria-hidden': 'true' }, loops.map((l) => {
    const t = idx[l.to], s = idx[l.from];
    return h('div', { class: 'mp-bar', style: { gridColumn: `${2 * t + 1} / ${2 * s + 2}` } }, h('span', { class: 'mb-head' }, '↩'), h('span', {}, l.bar));
  }));
}

const thumb = ([kind, label]) => h('li', { class: `at at-${kind}` }, h('span', { class: 'at-shape', 'aria-hidden': 'true' }, kind === 'book' ? h('i') : null), h('span', { class: 'at-l' }, label));

function mapView(goStage) {
  const M = edu.map;
  const cols = edu.phases.map((p, i) => {
    const st = M.stages[p.id];
    return [
      h('section', { class: 'mp-col', 'data-current': String(highlight === p.id), 'aria-label': p.title },
        h('h3', { id: `mp-${p.id}` }, stageBtn(p, i, goStage)),
        h('p', { class: 'mp-q' }, p.tagline),
        h('ul', { class: 'at-list', 'aria-label': `${p.title}에서 만들어지는 것` }, st.makes.map(thumb)),
        h('p', { class: 'mp-sub' }, h('span', { class: 'sr' }, '세부 절차: '), p.substeps.map((s) => s.title).join(' · '))),
      st.hands ? h('p', { class: 'mp-hand' }, h('span', { class: 'mp-arrow', 'aria-hidden': 'true' }, '→'), h('span', { class: 'sr' }, `${p.title}에서 다음 단계로 넘기는 것: `), h('span', {}, st.hands), st.via ? h('small', {}, st.via) : null) : null,
    ];
  });
  return h('div', { class: 'mp' },
    h('p', { class: 'ov-lead' }, M.lead),
    hint(),
    h('div', { class: 'mp-row' }, cols),
    loopBars(M.loops),
    h('div', { class: 'mp-loops' },
      h('h3', {}, '이렇게 되돌아가기도 해요'),
      h('ul', {}, M.loops.map((l) => h('li', {},
        h('span', { class: 'lp-tag', 'aria-hidden': 'true' }, `↩ ${phaseById[l.from].title} → ${phaseById[l.to].title}`),
        h('span', { class: 'sr' }, `${egeseo(phaseById[l.from].title)} ${ro(phaseById[l.to].title)} 되돌아가요: `),
        h('span', {}, l.text)))),
      h('p', { class: 'mp-overlap' }, M.overlap)));
}

function rolesView(goStage) {
  const rel = edu.relations;
  const cols = edu.phases.map((p, i) => {
    const roles = edu.roles.filter((r) => r.phaseId === p.id);
    const together = rel.find((x) => x.type === 'together' && x.phase === p.id);
    const pass = rel.find((x) => x.type === 'pass' && x.phase === p.id);
    // W-044: the expanded description lives in the column's notes row (below the cards), not inside the card, so the
    // cards row — and the pass arrow centred on it — keeps its height when a description opens.
    const notes = h('div', { class: 'rl-notes' });
    const card = (r) => {
      const note = h('p', { class: 'rl-note', id: `rl-note-${r.id}`, hidden: true }, h('b', {}, `${r.name}: `), r.detail);
      notes.append(note);
      const btn = h('button', { class: 'rl-more-btn', type: 'button', 'aria-expanded': 'false', 'aria-controls': note.id, onclick: () => {
        const open = btn.getAttribute('aria-expanded') !== 'true';
        btn.setAttribute('aria-expanded', String(open)); btn.textContent = open ? '하는 일 접기' : '하는 일 더 보기'; note.hidden = !open;
      } }, '하는 일 더 보기');
      return h('li', { class: 'rl-card' }, roleFig(r.id, 'fig-md'), h('strong', {}, r.name), h('span', {}, r.oneLine), btn);
    };
    return [
      h('section', { class: 'rl-col', 'data-current': String(highlight === p.id), 'aria-label': p.title },
        h('h3', { id: `rl-${p.id}` }, stageBtn(p, i, goStage)),
        h('ul', { class: 'rl-cards' },
          card(roles[0]),
          together ? h('li', { class: 'rl-with' }, h('span', { class: 'rw-mark', 'aria-hidden': 'true' }, '↔'), h('span', {}, h('span', { class: 'sr' }, `${roleById[together.a].name}, ${roleById[together.b].name} 함께: `), together.what)) : null,
          roles[1] ? card(roles[1]) : null),
        notes),
      pass ? h('p', { class: 'mp-hand rl-pass' },
        h('span', { class: 'mp-arrow', 'aria-hidden': 'true' }, '→'), h('span', { class: 'sr' }, '다음 단계로 넘기는 것: '), h('span', {}, pass.what),
        h('small', {}, pass.a ? `${roleById[pass.a].name} → ${roleById[pass.b].name}` : pass.via)) : null,
    ];
  });
  const far = rel.filter((x) => x.type === 'back' || x.type === 'pass-far');
  return h('div', { class: 'rl' },
    h('p', { class: 'ov-lead' }, '출판에는 여러 사람이 참여해요. 위아래가 있는 조직도가 아니라, 무엇을 넘기고 함께 확인하는지로 이어진 관계예요.'),
    h('p', { class: 'rl-key' }, h('span', {}, '→ 넘겨줘요'), h('span', {}, '↔ 함께 확인해요'), h('span', {}, '↩ 되돌려 고쳐요')),
    hint(),
    h('div', { class: 'mp-row rl-row' }, cols),
    h('div', { class: 'mp-loops' },
      h('h3', {}, '단계를 건너 이어지는 관계'),
      h('ul', {}, far.map((x) => h('li', {},
        h('span', { class: `lp-tag ${x.type === 'back' ? '' : 'fwd'}`, 'aria-hidden': 'true' }, `${roleById[x.a].name} ${x.type === 'back' ? '↩' : '→'} ${roleById[x.b].name}`),
        h('span', { class: 'sr' }, `${ga(roleById[x.a].name)} ${roleById[x.b].name}에게 ${x.type === 'back' ? '되돌려요' : '넘겨요'}: `),
        h('span', {}, x.what))))),
    h('p', { class: 'mp-overlap' }, edu.rolesNote, ' ', edu.sharedNote));
}

export function overviewScene(ctx) {
  const body = h('div', { class: 'ov-body' });
  const tabs = h('div', { class: 'ov-switch', role: 'group', 'aria-label': '보기 바꾸기' });
  const render = (focus) => {
    fill(tabs,
      h('button', { type: 'button', 'aria-pressed': String(view === 'map'), onclick: () => { view = 'map'; render(true); } }, '출판 과정 지도'),
      h('button', { type: 'button', 'aria-pressed': String(view === 'roles'), onclick: () => { view = 'roles'; render(true); } }, '함께 일하는 사람들'));
    fill(body, view === 'map' ? mapView(ctx.goStage) : rolesView(ctx.goStage));
    if (focus) tabs.querySelector('[aria-pressed=true]').focus();
    const cur = body.querySelector('[data-current=true]');
    if (cur && highlight) requestAnimationFrame(() => cur.scrollIntoView({ block: 'nearest', inline: 'center' }));
  };
  render(false);
  const root = h('div', { class: 'scene scene-overview' },
    h('header', { class: 'ov-top' },
      h('div', { class: 'ov-art' }, artImg('hero', 'art-scene')),
      h('div', {},
        h('h1', { class: 'scene-title big' }, '책 한 권은 어떻게 만들어질까'),
        h('p', { class: 'scene-lead' }, '먼저 전체 그림을 보고, 궁금한 단계를 골라 자세히 배워요.'))),
    tabs, body,
    h('div', { class: 'scene-actions ov-actions' },
      h('button', { class: 'btn primary lg', type: 'button', onclick: () => openStage(ctx.goStage, 1) }, '여행 시작하기'),
      h('button', { class: 'btn', type: 'button', onclick: ctx.startSample }, '바로 책 만들러 가기')));
  return root;
}
