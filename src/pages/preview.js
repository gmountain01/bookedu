// The live preview beside the editor (W-033, W-039): the shared book view in editor mode plus what writing needs —
// the page of the block being edited comes into view (no turn effect, no focus taken from the inputs) and is
// flashed; each step opens on its part of the book; step 8 adds the 3D cover and the production flat cover.
// The page engine (pages.js) and the completed-book reader (reader.js) share the same pages and controls.
import { h } from '../dom.js';
import { getProject, PAGE_SIZES, lastEdit } from '../state.js';
import { coverNodes, bookVars, applyVars } from '../book.js';
import { bookView } from './bookView.js';
export { pagedBook, paginate, PX_PER_MM } from './pages.js';

export function preview() {
  const phone = () => !matchMedia('(min-width: 561px)').matches;
  const wide = () => matchMedia('(min-width: 901px)').matches;
  const coverBox = h('div', { class: 'cover-flat', hidden: true });
  let el = null;
  // the sticky panel (bar + note + page) must fit the window so the page and its controls stay in view (desktop);
  // phones scroll the panel, so the page takes its natural height
  const room = () => {
    if (!wide() || !el) return Infinity;
    const others = el.scrollHeight - bv.view.offsetHeight - (bv.panHint.hidden ? 0 : bv.panHint.offsetHeight); // everything in the panel but the page and the hint: bar, cover box (step 8), gaps, padding
    return Math.max(coverBox.hidden ? 320 : 220, innerHeight - 72 - others - 44); // 44: room for the zoom hint that appears when the page pans
  };
  // the pages are rebuilt on every change (focus, field, blocks) and on a resize, so the flash is re-applied after each
  let flash = { id: '', until: 0 };
  const reapplyFlash = () => { if (flash.id && performance.now() < flash.until) bv.flow.querySelector(`[data-bid="${CSS.escape(flash.id)}"]`)?.classList.add('hl'); };
  const bv = bookView({ mode: 'editor', prefix: 'pv', room, onPages: reapplyFlash });
  // step 8: the cover box sits between the heading and the page controls, so the controls stay directly above the
  // page they turn and the panel still fits the window (MT-23 re-check)
  el = h('section', { class: 'preview paper', 'aria-label': '미리보기', onkeydown: bv.onKey },
    h('div', { class: 'pv-head' }, h('h2', { class: 'pv-title' }, '미리보기'), bv.info, bv.zoomNote),
    coverBox,
    h('div', { class: 'pv-ctl' }, bv.nav, bv.tools),
    bv.el);

  // Turn (without effect) to the page that holds the block being edited and flash it (shows cause -> effect);
  // a new step opens on its part of the book; otherwise the page being read stays. Runs inside the page engine's
  // callback, before the window is placed (MT-23).
  let seen = 0;
  let shownStep = 0;
  function follow() {
    const step = getProject().progress.currentStep;
    const f = bv.flow;
    const edited = lastEdit.at && lastEdit.at !== seen && f.querySelector(`[data-bid="${CSS.escape(lastEdit.id)}"]`); // an edit not yet shown wins over the step's first page (phone: the tab is shown after the edit)
    if (step !== shownStep && !edited) {
      shownStep = step;
      const target = step === 1 || step === 8 ? bv.front : step === 6 ? f.querySelector('.bk-sec-title') : step === 7 ? f.querySelector('.bk-tocpage') : f.querySelector('.bk-body');
      bv.goNode(target);
      seen = lastEdit.at;
      flash = { id: '', until: 0 };
      return;
    }
    shownStep = step;
    if (edited) {
      seen = lastEdit.at;
      f.querySelectorAll('.hl').forEach((e) => e.classList.remove('hl')); // the previous flash (re-applied by onPages) ends here
      bv.goNode(edited);
      flash = { id: lastEdit.id, until: performance.now() + 2600 }; // timed from now: on a phone this runs when the preview tab is shown
    }
    reapplyFlash(); // only the latest edit flashes
  }

  let wasStep8 = false;
  let autoFit = false; // step 8 shows the whole (small) page: 읽기 좋은 크기 becomes 쪽 맞춤 there and comes back on leaving (MT-23)
  function render() {
    const p = getProject();
    const step = p.progress.currentStep;
    if (step === 8 && !wasStep8 && bv.zoom === 'read') { autoFit = true; bv.setZoom('fit'); }
    if (step !== 8 && wasStep8 && autoFit) { autoFit = false; if (bv.zoom === 'fit') bv.setZoom('read'); }
    wasStep8 = step === 8;
    coverBox.hidden = step !== 8; // before the page: the height budget must not include a cover box that is going away (MT-23)
    if (!coverBox.hidden) {
      const size = PAGE_SIZES[p.layout.pageSize] || PAGE_SIZES.A5;
      const avail = Math.max(240, el.clientWidth - (phone() ? 12 : 28));
      const c = coverNodes(p);
      const c2 = coverNodes(p);
      applyVars(coverBox, bookVars(p));
      coverBox.dataset.theme = p.layout.theme || 'classic';
      coverBox.style.setProperty('--mm', `${Math.min(1.6, avail / (size.w * 2 + 14))}px`);
      // desktop: the 3D cover takes what the window height leaves after the bar, the cover extras and a 240px page, so the
      // whole panel fits beside the form and stays sticky (W-042); never below 0.6 (cover ≈ 126px tall)
      const mm3 = wide() ? Math.max(0.6, Math.min(1, (innerHeight - 72 - 530) / size.h)) : 1.5;
      coverBox.style.setProperty('--mm3', `${Math.min(mm3, (avail * 0.45) / size.w)}px`);
      coverBox.replaceChildren(book3d(c2), h('details', { class: 'flat-cover' }, h('summary', {}, '제작용 펼친 표지 보기 (뒤표지 · 책등 · 앞표지, 인쇄소에 넘기는 모양)'),
        h('div', { class: 'cover-row book' }, c.back, c.spine, c.front)),
        h('p', { class: 'muted' }, '책등 두께는 계산값이 아닌 모형이에요. 읽을 때의 쪽은 아래 미리보기에 있어요.'));
      applyVars(coverBox.querySelector('.cover-row'), bookVars(p));
    }
    bv.render(follow);
    // a panel taller than the window (step 8: page + cover box) scrolls with the document instead of sticking
    el.classList.toggle('is-tall', wide() && el.offsetHeight + 72 > innerHeight);
  }

  let ry = 28;
  function book3d(c) {
    const obj = h('div', { class: 'b3d book' },
      h('div', { class: 'b3d-face b3d-front' }, c.front), h('div', { class: 'b3d-face b3d-spine' }, c.spine), h('div', { class: 'b3d-face b3d-back' }, c.back));
    obj.style.setProperty('--ry', `${ry}deg`);
    const turn = (deg) => { ry = deg; obj.style.setProperty('--ry', `${deg}deg`); };
    const stageEl = h('div', { class: 'b3d-stage', title: '끌어서 돌려 보세요' }, obj);
    let dragX = null;
    stageEl.addEventListener('pointerdown', (e) => { dragX = e.clientX; stageEl.setPointerCapture(e.pointerId); });
    stageEl.addEventListener('pointermove', (e) => { if (dragX == null) return; turn(ry + (e.clientX - dragX) * 0.6); dragX = e.clientX; });
    stageEl.addEventListener('pointerup', () => { dragX = null; });
    return h('div', { class: 'b3d-wrap' }, stageEl,
      h('div', { class: 'row small b3d-btns', role: 'group', 'aria-label': '입체 표지 돌리기' },
        h('button', { class: 'btn sm', type: 'button', onclick: () => turn(28) }, '앞표지'),
        h('button', { class: 'btn sm', type: 'button', onclick: () => turn(90) }, '책등'),
        h('button', { class: 'btn sm', type: 'button', onclick: () => turn(180) }, '뒤표지'),
        h('span', { class: 'muted' }, '버튼을 누르거나 책을 끌어서 돌려 보세요')));
  }

  return { el, render, destroy: () => bv.destroy() };
}
