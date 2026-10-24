// A publishing station (W-030, docs/DESIGN.md Plan v7): a station menu by learning topic (한눈에 보기 / 세부 절차 /
// 함께 일하는 장면 / 앱 실습과 실제 출판 규칙 / 확인해 보기) and one topic per screen, each explanation beside its example.
import { h, fill } from '../dom.js';
import edu from '../data/education.json';
import { assetSrc } from '../images.js';
import { sampleProject } from '../sample.js';
import { coverNodes, bookVars, applyVars } from '../book.js';
import { artImg, art } from '../art.js';
import { STEP_NAMES, typesetVisual, proofVisual, artifact, noteLines, judgeForm, chainStrip } from './journeyDetail.js';

const roleById = Object.fromEntries(edu.roles.map((r) => [r.id, r]));
const srcById = Object.fromEntries(edu.sources.map((s) => [s.id, s]));
const caseById = Object.fromEntries(edu.phases.flatMap((p) => p.case || []).map((c) => [c.id, c]));
const STATION_ART = { plan: 'station-plan', edit: 'station-edit', print: 'station-print', market: 'station-market' };
const SAMPLE = sampleProject();
// The sample's cover on the learning screens is the same cover the studio and the completed book draw (W-040):
// coverNodes + bookVars + book.css, scaled with --mm from the CSS class, so every cover change reaches these screens.
function sampleCover(part, cls) {
  const box = h('div', { class: `book lc ${cls}`, 'data-theme': SAMPLE.layout.theme || 'classic', 'aria-hidden': 'true' }, coverNodes(SAMPLE)[part]);
  applyVars(box, bookVars(SAMPLE));
  return box;
}
const roleName = (id) => roleById[id]?.name || '';

// Korean particles after a name: 이/가, 을/를, 은/는 depend on the last syllable's final consonant.
// A trailing note in brackets does not count: 「아이디어 메모(…)를」.
const hasFinal = (w) => { const c = w.replace(/\([^)]*\)\s*$/, '').trim().slice(-1).charCodeAt(0) - 0xac00; return c >= 0 && c <= 11171 && c % 28 !== 0; };
const josa = (w, withFinal, without) => `${w}${hasFinal(w) ? withFinal : without}`;

const appLine = (s) => (s.app === 'do' && s.appStep
  ? `이 앱의 ${s.appStep}단계 「${STEP_NAMES[s.appStep - 1]}」에서 직접 해 봐요.`
  : s.app === 'real' ? '실제 출판에서 하는 일이에요. 이 앱에서는 해 보지 않아요.' : '이 앱에서는 예시를 보며 배워요.');

function sourceLine(ids = []) {
  const list = ids.map((id) => srcById[id]).filter(Boolean);
  return list.length ? h('p', { class: 'src' }, '근거: ', list.map((s, i) => [i ? ', ' : '',
    h('a', { href: s.url, target: '_blank', rel: 'noopener' }, s.title), ` (확인 ${s.checkedAt})`])) : null;
}

// ---------- people: a role figure (the illustrator's drawing when it exists) ----------
export function roleFig(id, cls = 'fig') {
  const src = art(`role-${id}`);
  const name = roleName(id);
  return src ? h('img', { class: cls, src, alt: '', 'aria-hidden': 'true', width: 240, height: 200, draggable: 'false' })
    : h('span', { class: `${cls} fig-ph`, 'aria-hidden': 'true' }, name.slice(0, 1));
}

// numbered short labels that carry the meaning of each change on the picture; full reasons go to 「자세히 보기」
const pins = (labels, title = '바뀐 점') => h('div', { class: 'pins' }, h('p', { class: 'pins-t' }, title),
  h('ol', {}, labels.map((t, i) => h('li', {}, h('span', { class: 'pin-n', 'aria-hidden': 'true' }, String(i + 1)), h('span', {}, h('span', { class: 'sr' }, `${i + 1}번: `), t)))));

// the numbered pin sits on the phrase that changed (changes[].mark, W-032 MT-13); the legend under the picture repeats it
function marked(text, marks) {
  const out = [];
  let rest = text;
  for (;;) {
    const hit = marks.map((m, i) => ({ i, at: m ? rest.indexOf(m) : -1, m })).filter((x) => x.at >= 0).sort((a, b) => a.at - b.at)[0];
    if (!hit) return [...out, rest];
    out.push(rest.slice(0, hit.at), h('mark', { class: 'pin-m' }, h('span', { class: 'pin-n', 'aria-hidden': 'true' }, String(hit.i + 1)), h('span', { class: 'sr' }, `바뀐 곳 ${hit.i + 1}번: `), hit.m));
    rest = rest.slice(hit.at + hit.m.length);
  }
}
// 「표 1. 제목: 가 1998년 · 나 2005년」 is drawn as a real table
function lineEl(l, marks) {
  const t = /^(표 \d+\.[^:]*):\s*(.+)$/.exec(l);
  if (!t) return h('p', { class: 'cf-x' }, marked(l, marks));
  const rows = t[2].split(' · ').map((r) => /^(.*\S)\s+(\S+)$/.exec(r) || [r, r, '']);
  return h('table', { class: 'cf-table' }, h('caption', {}, marked(t[1], marks)),
    h('tbody', {}, rows.map(([, k, v]) => h('tr', {}, h('th', { scope: 'row' }, k), h('td', {}, v)))));
}

// before → (comments) → after as three panels; the comments are the editor's or planner's notes in the draft
const isNote = (l) => /^(기획)?편집자 의견/.test(l);
function changeFlow(c) {
  const draft = c.before.lines.filter((l) => !isNote(l));
  const notes = c.before.lines.filter(isNote);
  const marks = (c.changes || []).map((x) => x.mark);
  const panel = (cls, label, lines, mk = []) => h('div', { class: `cf-p ${cls}` }, h('p', { class: 'cf-l' }, label), lines.map((l) => lineEl(l, mk)));
  const who = notes[0]?.startsWith('기획편집자') ? 'planner' : 'editor';
  return h('div', { class: 'cf' },
    h('div', { class: `cf-row ${notes.length ? 'three' : 'two'}` },
      panel('before', c.before.label, draft),
      h('span', { class: 'cf-ar', 'aria-hidden': 'true' }, '→'),
      notes.length ? [h('div', { class: 'cf-p notes' }, h('p', { class: 'cf-l' }, `${roleName(who)}의 의견`),
        notes.map((l) => h('p', { class: 'cf-n' }, l.replace(/^(기획)?편집자 의견( \d+)?:\s*/, ''))))
      , h('span', { class: 'cf-ar', 'aria-hidden': 'true' }, '→')] : null,
      panel('after', c.after.label, c.after.lines, marks)),
    c.changes?.[0]?.short ? pins(c.changes.map((x) => x.short)) : null);
}

// ---------- visuals (all HTML/CSS; the key facts are also in text) ----------
const figure = (v, ...body) => h('figure', { class: `vz vz-${v.type}` },
  h('figcaption', {}, h('span', { class: 'ex-badge' }, '학습용 예시'), ' ', v.caption), ...body,
  h('p', { class: 'vz-note' }, '이 앱을 위해 만든 자료예요. 실제 출판사가 만들거나 검토한 자료가 아니에요.'));

function compareBlock(c, numbered) {
  return noteLines(h('div', { class: 'compare' }, artifact('전', c.before, 'before', numbered), artifact('후', c.after, 'after', numbered)));
}
function changesBlock(c) {
  if (!c?.changes?.length) return null;
  return h('section', { class: 'changes', 'aria-label': '무엇을, 왜 바꿨나요' }, h('h3', {}, `무엇을, 왜 바꿨나요 · ${c.title}`),
    h('ol', {}, c.changes.map((x) => h('li', {}, h('strong', {}, x.what), h('span', {}, x.why)))),
    c.openEnded ? h('p', { class: 'open-note' }, '답이 하나로 정해진 것은 아니에요. 다른 선택도 이유가 분명하면 괜찮아요.') : null);
}

function sizesVisual(v) {
  const text = SAMPLE.blocks.find((b) => b.type === 'paragraph').text;
  const page = (label, w, hgt) => h('div', { class: 'sz-col' },
    h('div', { class: 'sz-page', style: { width: `${w * 1.25}px`, height: `${hgt * 1.25}px` } },
      h('p', { class: 'sz-h' }, '1장 늘 지나던 길'), h('p', { class: 'sz-p' }, text)),
    h('p', { class: 'sz-label' }, label));
  return figure(v, h('div', { class: 'sz-row', 'aria-hidden': 'true' }, page('A5 · 148×210mm', 148, 210), page('B6 · 128×182mm', 128, 182)),
    h('p', { class: 'sr' }, '같은 첫 문단을 A5와 B6 쪽에 놓은 그림이에요. B6가 더 작아서 한 줄에 들어가는 글자가 적고 줄이 더 많아져요.'));
}

function promoVisual(v) {
  const m = SAMPLE.meta;
  const blurb = caseById[v.caseId]?.after?.lines || [];
  const chapters = SAMPLE.blocks.filter((b) => b.type === 'heading' && b.level === 1).map((b) => b.text);
  const n = (i) => h('span', { class: 'pin-n', 'aria-hidden': 'true' }, String(i));
  return figure(v, h('div', { class: 'promo' },
    h('div', { class: 'promo-cover', 'aria-hidden': 'true' }, n(1), sampleCover('front', 'lc-promo')),
    h('div', { class: 'promo-body' },
      h('p', { class: 'promo-title' }, m.title),
      h('p', { class: 'promo-meta' }, `${m.authorAlias} · ${m.genre} · A5`),
      h('p', { class: 'promo-meta' }, '실제 자료에는 쪽수, 정가, 출간일, ISBN 같은 서지 정보도 들어가요.'),
      h('dl', { class: 'promo-dl' },
        h('dt', {}, n(2), '책 소개'), h('dd', {}, blurb.slice(0, 3).join(' ')),
        h('dt', {}, n(3), '지은이 소개'), h('dd', {}, v.author),
        h('dt', {}, n(4), '차례'), h('dd', {}, chapters.join(' / ')),
        h('dt', {}, n(5), '이런 독자에게'), h('dd', {}, m.targetReader)))),
    v.parts ? pins(v.parts.map(([, why]) => why), '번호마다 알려 주는 것') : null);
}

function flowVisual(v) {
  const [pub, mid, shop, reader] = v.nodes;
  const [direct, deposit, back] = v.notes;
  return figure(v,
    h('div', { class: 'flow-wrap' },
      h('ol', { class: 'flow', 'aria-label': '책이 독자에게 가는 길' },
        h('li', { class: 'fl-node' }, pub),
        h('li', { class: 'fl-node fl-opt' }, mid),
        h('li', { class: 'fl-node' }, shop),
        h('li', { class: 'fl-node' }, reader)),
      h('p', { class: 'fl-direct' }, '도매상·유통사(점선 상자)를 거치지 않고 ', direct),
      h('p', { class: 'fl-dep' }, h('span', { class: 'fl-arrow', 'aria-hidden': 'true' }, '↓'), h('strong', {}, '출판사 → 국립중앙도서관'), ' ', deposit),
      h('p', { class: 'fl-back' }, h('span', { class: 'fl-arrow', 'aria-hidden': 'true' }, '↩'), h('strong', {}, '독자 → 출판사'), ' ', back)));
}

function docVisual(v) {
  return figure(v, h('div', { class: 'doc' }, h('p', { class: 'doc-t' }, v.title),
    h('dl', {}, v.rows.map(([k, val]) => [h('dt', {}, k), h('dd', {}, val)]))));
}
function checkVisual(v) {
  return figure(v, h('div', { class: 'doc' }, h('p', { class: 'doc-t' }, v.title),
    h('ul', { class: 'chk-list' }, v.items.map(([ok, text]) => h('li', { 'data-ok': String(ok) },
      h('span', { class: 'ck-mark', 'aria-hidden': 'true' }, ok ? '✓' : '!'), h('span', { class: 'sr' }, ok ? '확인함: ' : '고칠 점: '), text)))));
}
function coverVisual(v) {
  const m = SAMPLE.meta;
  const C = SAMPLE.cover;
  return figure(v,
    h('div', { class: 'cvz-row', 'aria-hidden': 'true' },
      h('div', { class: 'cvz-col' }, sampleCover('back', 'lc-page'), h('p', { class: 'cvz-l' }, '뒤표지')),
      h('div', { class: 'cvz-col' }, sampleCover('spine', 'lc-page'), h('p', { class: 'cvz-l' }, '책등')),
      h('div', { class: 'cvz-col' }, sampleCover('front', 'lc-page'), h('p', { class: 'cvz-l' }, '앞표지'))),
    h('p', { class: 'sr' }, `표지 그림(완성본과 같은 표지): 앞표지에는 골목 사진 위에 부제 「${SAMPLE.frontMatter.titlePage}」, 제목 「${m.title}」, 카피 「${C.copy}」, 지은이 ${m.authorAlias}가 있고, 책등에는 제목과 지은이가, 뒤표지에는 사진 띠와 강조 문장 「${C.backHeadline}」, 소개 글 「${C.backText}」, 「이런 독자에게」가 있어요.`));
}
function bindingVisual(v) {
  const bind = edu.terms.find((t) => t.id === 'binding');
  return figure(v,
    h('div', { class: 'bd-row', 'aria-hidden': 'true' },
      h('div', { class: 'bd-col' }, h('div', { class: 'bd-perfect' }, Array.from({ length: 7 }, () => h('span'))), h('p', { class: 'cvz-l' }, '무선제본: 낱장을 모아 책등을 풀로 붙여요')),
      h('div', { class: 'bd-col' }, h('div', { class: 'bd-saddle' }, Array.from({ length: 4 }, () => h('span')), h('i')), h('p', { class: 'cvz-l' }, '중철: 접은 종이 가운데를 철심으로 박아요'))),
    bind ? h('p', { class: 'vz-text' }, bind.definition) : null);
}

function visualFor(v) {
  const c = caseById[v.caseId];
  if (v.type === 'doc') return docVisual(v);
  if (v.type === 'check') return checkVisual(v);
  if (v.type === 'cover') return coverVisual(v);
  if (v.type === 'binding') return bindingVisual(v);
  if (v.type === 'compare') return figure(v, changeFlow(c));
  if (v.type === 'sizes') return sizesVisual(v);
  if (v.type === 'typeset') return figure(v, typesetVisual(), c?.changes?.[0]?.short ? pins(c.changes.map((x) => x.short)) : null);
  if (v.type === 'proof') return figure(v, proofVisual(), v.problems ? pins(v.problems, '그림 속 번호가 가리키는 문제') : null);
  if (v.type === 'promo') return promoVisual(v);
  if (v.type === 'flow') return flowVisual(v);
  return null;
}

// ---------- collaboration as continuous scenes (W-036) ----------
// The same people appear in every scene (illustrator's scene-*.svg keep each role's face, hair and clothes); each scene
// shows one action and the state of the work it passes on. Every role has a name and a second colour, never colour alone.
// The colour follows each figure's top. The market strip has no before/after box: its cases are about wording, not this flow.
const ROLE_COLOR = { author: '#00A95C', editor: '#0078BF', planner: '#0078BF', designer: '#9A7000', production: '#FF48B0', printer: '#00A95C', marketer: '#00A95C', bookseller: '#FF48B0' };
const roleTag = (id) => h('span', { class: 'scn-role', style: `--rc:${ROLE_COLOR[id] || '#545b77'}` }, roleName(id));
function sceneStrip(p) {
  const sc = p.scenes;
  if (!sc?.steps?.length) return null;
  const c = caseById[sc.caseId];
  return h('section', { class: 'scn', 'aria-labelledby': `scn-h-${p.id}` },
    h('h2', { id: `scn-h-${p.id}`, class: 'scn-title' }, sc.title),
    h('ol', { class: 'scn-list' }, sc.steps.map((st, i) => h('li', { class: 'scn-item' },
      h('span', { class: 'sr' }, `장면 ${i + 1}. `),
      h('span', { class: 'scn-no', 'aria-hidden': 'true' }, String(i + 1)),
      h('div', { class: 'scn-pic' }, artImg(st.img, 'scn-img')),
      h('p', { class: 'scn-who', 'aria-hidden': 'true' }, st.give ? [roleTag(st.give[0]), h('span', { class: 'scn-give' }, '→'), roleTag(st.give[1])] : st.who.map(roleTag)),
      h('p', { class: 'scn-act' }, st.act),
      h('p', { class: 'scn-work' }, h('span', { class: 'scn-sheet', 'aria-hidden': 'true' }), h('span', {}, '작업물: '), h('b', {}, st.work))))),
    c && sc.change ? changeBox(c, sc) : null);
}

// The case's text before and after, with the reviewer's notes between them (from the case lines or the scene data).
function changeBox(c, sc) {
  const ch = sc.change;
  const isNote = (l) => /^편집자 의견/.test(l);
  const notes = sc.notes || c.before.lines.filter(isNote).map((l) => l.replace(/^편집자 의견 \d+:\s*/, ''));
  const box = (cls, label, lines) => h('div', { class: cls }, h('p', { class: 'scn-label' }, label), lines.map((l) => h('p', {}, l)));
  const arrow = () => h('span', { class: 'scn-arrow', 'aria-hidden': 'true' }, '→');
  return h('div', { class: 'scn-change' },
    h('p', { class: 'scn-change-t' }, ch.title),
    h('div', { class: 'scn-change-row' + (ch.notes && notes.length ? '' : ' no-notes') },
      box('scn-before', ch.before, c.before.lines.filter((l) => !isNote(l)).map((l) => l.replace(/^초고:\s*/, ''))),
      arrow(),
      ch.notes && notes.length ? [h('div', { class: 'scn-notes' }, h('p', { class: 'scn-label' }, ch.notes), h('ul', {}, notes.map((n) => h('li', {}, n)))), arrow()] : null,
      box('scn-after', ch.after, c.after.lines)));
}

// ---------- hand-offs as sentences ----------
function story(p) {
  return h('ol', { class: 'story' }, p.handoffs.map((x) => {
    const from = roleName(x.from);
    const to = roleName(x.to);
    const s = x.step ? p.substeps[x.step - 1] : null;
    return h('li', { 'data-back': String(!!x.back) },
      s ? h('p', { class: 'st-step' }, `세부 절차 ${x.step} · ${s.title}`) : null,
      h('p', { class: 'st-line' }, h('b', { class: 'role-tag' }, from), `${hasFinal(from) ? '이' : '가'} `, h('b', {}, josa(x.item, '을', '를')), ' ',
        h('b', { class: 'role-tag' }, to), `에게 ${x.verb || '넘겨요'}.`),
      h('p', { class: 'st-says' }, roleFig(x.by, 'fig-sm'), h('span', { class: 'st-by' }, x.by === x.from ? `${from}의 말` : `${roleName(x.by)}의 돌아온 의견`), `“${x.says}”`),
      x.back ? h('p', { class: 'st-revise' }, h('strong', {}, '↩ 다시 고쳐요 '), x.revise) : null);
  }));
}

// ---------- Plan v7 (W-030): one learning topic per screen, one station menu in the same place ----------
const lastTopic = {}; // phaseId -> topic index, so leaving and coming back lands where the student was

// Core (always shown): core sentence, the picture, three one-line points, who (as people). Details: one 「자세히 보기」.
function substepCore(s) {
  const vis = s.visual ? visualFor(s.visual) : null;
  return h('article', { class: 'sc' },
    h('div', { class: 'sc-text' },
      h('p', { class: 'rd-what' }, s.what),
      h('ul', { class: 'sc-points' },
        h('li', {}, h('span', { class: 'sp-k' }, '왜'), h('span', {}, s.why)),
        h('li', {}, h('span', { class: 'sp-k' }, '남는 것'), h('span', {}, s.output)),
        h('li', {}, h('span', { class: 'sp-k' }, '넘기기 전 확인'), h('span', {}, s.check))),
      h('div', { class: 'sc-who' }, h('p', { class: 'sp-k' }, '누가 해요'),
        h('ul', {}, (s.who || []).filter((id) => roleName(id)).map((id) => h('li', {}, roleFig(id, 'fig-sm'), h('span', {}, roleName(id)))))),
      h('p', { class: `rd-app ${s.app}` }, appLine(s))),
    vis ? h('div', { class: 'sc-vis' }, vis) : null);
}
function substepMore(s) {
  const c = s.visual?.caseId ? caseById[s.visual.caseId] : null;
  const type = s.visual?.type;
  return h('details', { class: 'sc-more' }, h('summary', {}, '자세히 보기'),
    h('div', { class: 'sc-more-b' },
      c && type === 'promo' ? h('div', { class: 'rd-blurb' }, h('h3', {}, '소개 문구는 이렇게 고쳤어요'), compareBlock(c)) : null,
      c && type === 'proof' ? h('div', {}, h('h3', {}, '교정지에서 찾은 문제와 고친 모습'), compareBlock(c, true)) : null,
      c && type === 'typeset' ? h('div', {}, h('h3', {}, '조판 전후에 무엇이 있었나요'), compareBlock(c)) : null,
      c ? changesBlock(c) : null,
      h('section', { class: 'sc-roles', 'aria-label': '이 절차의 사람들' }, h('h3', {}, '이 절차의 사람들'),
        h('dl', {}, (s.who || []).map((id) => roleById[id]).filter(Boolean).map((r) => [h('dt', {}, r.name), h('dd', {}, `${r.oneLine} ${r.detail}`)])))));
}

export function stationV7(p, idx, ctx) {
  const roles = p.roleIds.map((id) => roleById[id]).filter(Boolean);
  const terms = edu.terms.filter((t) => t.phaseId === p.id);
  const topics = [
    { id: 'overview', label: '이 단계 소개' },
    ...p.substeps.map((s, i) => ({ id: `s${i}`, label: s.title, step: i })),
    { id: 'team', label: '함께 일하는 장면' },
    { id: 'app', label: '앱 실습과 실제 출판 규칙' },
    { id: 'check', label: passed() ? '확인해 보기 ✓' : '확인해 보기' },
  ];
  function passed() { return ctx.isPassed(); }
  let cur = Math.min(lastTopic[p.id] ?? 0, topics.length - 1);

  const menuList = h('ol', { class: 'tm-list' });
  const menuSum = h('summary', { class: 'tm-sum' });
  const menu = h('nav', { class: 'tm', 'aria-label': `이 단계의 내용: ${p.title}` },
    h('button', { class: 'btn sm tm-map', type: 'button', onclick: () => ctx.toMap() }, '← 한눈에 보기'),
    h('details', { class: 'tm-box', open: true, onkeydown: (e) => { const d = e.currentTarget; if (e.key === 'Escape' && d.open && !matchMedia('(min-width: 901px)').matches) { d.open = false; menuSum.focus(); } } }, menuSum,
      h('p', { class: 'tm-h', id: `tm-h-${p.id}` }, h('span', {}, '이 단계의 내용'), h('strong', {}, p.title)), menuList));
  const body = h('div', { class: 'tp' });
  const root = h('div', { class: `scene station-v7 st-${p.id}` }, menu, body);

  function renderMenu() {
    const item = (t, k) => h('li', { class: t.step != null ? 'tm-sub' : '' }, h('button', {
      type: 'button', 'aria-current': k === cur ? 'page' : null, onclick: () => show(k, true),
    }, t.step != null ? h('span', { class: 'sub-n' }, String(t.step + 1)) : null, h('span', {}, t.label)));
    const first = topics.findIndex((t) => t.step != null);
    const last = first + p.substeps.length;
    fill(menuList,
      item(topics[0], 0),
      h('li', { class: 'tm-group' }, h('p', { class: 'tm-group-t', id: `tm-g-${p.id}` }, '세부 절차'),
        h('ol', { 'aria-labelledby': `tm-g-${p.id}` }, topics.slice(first, last).map((t, j) => item(t, first + j)))),
      topics.slice(last).map((t, j) => item(t, last + j)));
    const t = topics[cur];
    // phones only (one row beside 「← 한눈에 보기」); the title right below names the topic
    menuSum.textContent = `이 단계의 내용${t.step != null ? ` · 절차 ${t.step + 1}/${p.substeps.length}` : ''}`;
  }

  function pager() {
    const prev = cur > 0 ? { label: `← 이전: ${topics[cur - 1].label}`, go: () => show(cur - 1, true) } : ctx.prevStage;
    const next = cur < topics.length - 1 ? { label: `다음: ${topics[cur + 1].label} →`, go: () => show(cur + 1, true) } : ctx.nextStage;
    return h('nav', { class: 'tp-pager', 'aria-label': '이전·다음 내용' },
      prev ? h('button', { class: 'btn', type: 'button', onclick: prev.go }, prev.label) : h('span'),
      next ? h('button', { class: `btn ${cur < topics.length - 1 ? 'primary' : 'stage'}`, type: 'button', onclick: next.go }, next.label) : h('span'));
  }

  function topicContent(t) {
    if (t.id === 'overview') {
      return [
        h('div', { class: 'ov-head' },
          h('div', { class: 'sv-art' }, artImg(STATION_ART[p.id], 'art-scene')),
          h('div', {},
            h('p', { class: 'scene-tag' }, p.tagline),
            p.goal ? h('p', { class: 'scene-goal' }, h('strong', {}, '알게 될 것 '), p.goal) : null,
            h('p', { class: 'scene-lead' }, p.summary))),
        h('section', { class: 'ov-sec', 'aria-labelledby': `ov-flow-${p.id}` },
          h('h2', { id: `ov-flow-${p.id}` }, '이 단계의 세부 절차'),
          h('p', { class: 'sv-hint' }, '각 절차의 설명과 예시 자료는 「이 단계의 내용」 목록에서 골라 읽어요.'),
          h('table', { class: 'ov-table' }, h('thead', {}, h('tr', {}, h('th', { scope: 'col' }, '순서'), h('th', { scope: 'col' }, '세부 절차'), h('th', { scope: 'col' }, '남는 것'))),
            h('tbody', {}, p.substeps.map((s, i) => h('tr', {}, h('td', {}, String(i + 1)), h('td', {}, s.title), h('td', {}, s.output))))),
          p.flowNote ? h('p', { class: 'flow-note' }, h('span', { 'aria-hidden': 'true' }, '↺ '), p.flowNote) : null),
        h('section', { class: 'ov-sec', 'aria-labelledby': `ov-case-${p.id}` },
          h('h2', { id: `ov-case-${p.id}` }, '예시 책 「골목에서 찾은 이야기」가 바뀌는 순서'), chainStrip(p.id)),
        h('details', { class: 'more-inline' }, h('summary', {}, '예시와 용어'),
          h('p', { class: 'example' }, h('strong', {}, '예를 들면 '), p.example),
          terms.length ? h('div', { class: 'terms' }, terms.map(ctx.termButton)) : null)];
    }
    if (t.step != null) return [substepCore(p.substeps[t.step])];
    if (t.id === 'team') {
      return [
        h('p', { class: 'tp-lead' }, h('span', { class: 'ex-badge' }, '학습용 예시'), ' 누가 무엇을 넘기고, 어떤 의견을 받아, 무엇을 고치는지 차례대로 읽어 보세요.'),
        sceneStrip(p),
        p.scenes ? h('details', { class: 'more-inline scn-more' }, h('summary', {}, '이 단계에서 주고받은 말 모두 보기'), story(p)) : story(p),
        edu.sharedNote ? h('p', { class: 'shared-note' }, edu.sharedNote) : null]; // W-043: no jump to the overview from here (it broke the learning flow); 「← 한눈에 보기」 in the topic bar remains
    }
    if (t.id === 'app') {
      return [
        h('div', { class: 'sv-app' },
          h('div', {}, h('h2', {}, '이 앱에서'), p.practice?.do?.length ? h('ul', {}, p.practice.do.map((d) => h('li', {}, d.text))) : h('p', { class: 'muted' }, '이 단계는 예시를 보며 배워요.')),
          h('div', {}, h('h2', {}, '실제 출판에서'), h('ul', {}, (p.practice?.real || []).map((x) => h('li', {}, x))))),
        sourceLine(p.sourceIds)];
    }
    // check
    return [
      (p.judge || []).map((j, k) => h('section', { class: 'chk' }, h('h2', {}, `${k + 1}. 상황 판단`),
        p.id === 'print' ? proofVisual(false) : null, judgeForm(j, `${p.id}-${k}`))),
      h('section', { class: 'chk sv-quiz' }, h('h2', { class: 'sv-quiz-t' }, `${(p.judge || []).length + 1}. 단계 퀴즈 · `, passed() ? '통과했어요 ✓' : '맞히면 이 단계를 통과해요'),
        ctx.quizForm(p, () => {
          ctx.onPass();
          root.querySelector('.sv-quiz-t').lastChild.textContent = '통과했어요 ✓';
          topics[topics.length - 1].label = '확인해 보기 ✓';
          renderMenu();
          ctx.stamp(root.querySelector('.sv-quiz'));
        }))];
  }

  function show(k, focus) {
    cur = k;
    lastTopic[p.id] = k;
    const t = topics[k];
    const where = t.step != null ? `세부 절차 ${t.step + 1}/${p.substeps.length}` : t.label.replace(' ✓', '');
    renderMenu();
    fill(body,
      h('p', { class: 'scene-kicker' }, `${p.title} · ${where}`),
      h('h1', { class: 'tp-title', tabindex: '-1' }, t.id === 'overview' ? p.title : t.label.replace(' ✓', '')),
      topicContent(t),
      pager(),
      t.step != null ? substepMore(p.substeps[t.step]) : null);
    if (focus) {
      menu.querySelector('details').open = matchMedia('(min-width: 901px)').matches; // phones: menu folds after a choice
      body.querySelector('.tp-title').focus({ preventScroll: true });
      window.scrollTo({ top: 0 }); // keep level 1 (출판 단계) in view above the station menu
    }
  }
  ctx.setKeys((dir) => {
    const k = cur + dir;
    if (k >= 0 && k < topics.length) show(k, true);
    else (dir < 0 ? ctx.prevStage : ctx.nextStage)?.go();
  });
  show(cur, false);
  if (!matchMedia('(min-width: 901px)').matches) menu.querySelector('details').open = cur === 0;
  return root;
}
