// One book view for every screen (W-039). The pages come from pages.js (print-size columns, the same breaks as the
// PDF); this module only decides which page or facing pair is in the window and turns to the next one. Nothing is
// cut out of the flow: every page stays in the DOM (screen readers read the whole book).
// Views: front cover alone; facing pages (left = even page, right = odd page, as printed); the last interior page on
// the left facing a blank inside page when it falls there; back cover alone. One page per view when two pages would
// make the body text too small, or when the screen asks for 한 쪽.
// Modes: 'reader' (the completed book: keys anywhere in its dialog, turn targets beside the book) and 'editor' (the live
// preview beside the inputs: keys only while the preview has focus, no turn effect on a re-render, the page kept).
import { h } from '../dom.js';
import { getProject, PAGE_SIZES } from '../state.js';
import { pagedBook, PX_PER_MM } from './pages.js';

export const ZOOMS = [['fit', '쪽 맞춤'], ['read', '읽기 좋은 크기'], ['actual', '실제 크기'], ['large', '크게 (140%)']];
const READ_PX = 10.5; // 읽기 좋은 크기: body text never below this at a 10pt reference (MT-15/16)
const MIN_TEXT_PX = READ_PX; // below this at page fit a spread falls back to one page, so 읽기 좋은 크기 never pans a spread (MT-23)
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

/**
 * @param {object} o
 * @param {'reader'|'editor'} o.mode
 * @param {string} o.prefix anchor prefix for the book's own contents links
 * @param {{page?: number, single?: boolean|null, zoom?: string}} [o.initial]
 * @param {() => number} [o.room] available height for the window (editor: the sticky panel); default = the view's own height
 * @param {(st: {page: number, single: boolean|null, zoom: string}) => void} [o.onPlace] after every placement (memory)
 * @param {(count: number) => void} [o.onPages] after every pagination, before placement (reader: the contents menu)
 */
export function bookView({ mode = 'reader', prefix = 'pv', initial = {}, room, onPlace, onPages } = {}) {
  const editor = mode === 'editor';
  let single = initial.single ?? null; // null = automatic (spread when the text stays readable)
  let zoom = initial.zoom ?? (editor && matchMedia('(min-width: 561px)').matches ? 'read' : 'fit');
  let views = [];
  let vi = 0;
  // the page being read: set only by turning (buttons, keys, swipe, contents, follow), so a mode, zoom or window change
  // returns to the same page instead of drifting to the left page of a pair (MT-22 T-063 #2)
  let reading = initial.page ?? 1;
  let spread = false;
  let anim = null;

  const book = pagedBook({ prefix, onJump: (id) => jumpTo(id) });
  const fold = h('div', { class: 'rd-fold', 'aria-hidden': 'true' });
  const endpaper = h('div', { class: 'rd-endpaper', 'aria-hidden': 'true' }); // the blank inside page opposite a lone last page
  const win = h('div', { class: 'rd-win' }, book.el, endpaper, fold);
  const frame = h('div', { class: 'rd-frame' }, win);
  const view = h('div', { class: 'rd-view', tabindex: '0', role: 'region', 'aria-label': editor ? '미리보기 책 쪽 (← → 키로 넘겨요)' : '책 읽기 화면 (← → 키로 넘겨요)' }, frame);
  const turn = (d) => go(vi + d, d, true);
  // mouse targets beside the book (the same action as the page bar; hidden from keyboard and screen readers to avoid doubles)
  const side = (d) => h('button', { class: `rd-side rd-side-${d < 0 ? 'prev' : 'next'}`, type: 'button', tabindex: '-1', 'aria-hidden': 'true', onclick: () => turn(d) }, d < 0 ? '‹' : '›');
  const sidePrev = side(-1);
  const sideNext = side(1);
  const where = h('span', { class: 'rd-where', 'aria-live': 'polite' });
  const prevBtn = h('button', { class: `btn rd-turn${editor ? ' sm' : ''}`, type: 'button', 'aria-label': '이전 쪽', onclick: () => turn(-1) }, '‹ 이전');
  const nextBtn = h('button', { class: `btn rd-turn${editor ? ' sm' : ''}`, type: 'button', 'aria-label': '다음 쪽', onclick: () => turn(1) }, '다음 ›');
  const nav = h('div', { class: 'rd-nav', role: 'group', 'aria-label': '쪽 넘기기' }, prevBtn, where, nextBtn);
  const modeBtns = [['1', '한 쪽'], ['2', '펼침면']].map(([v, l]) => h('button', {
    class: 'btn sm', type: 'button', 'data-mode': v, onclick: () => { single = v === '1'; render(); },
  }, l));
  const modeGroup = h('div', { class: 'rd-mode', role: 'group', 'aria-label': '보기 방식' }, modeBtns);
  const zoomSel = h('select', { class: 'rd-zoom', 'aria-label': '확대', onchange: (e) => { zoom = e.target.value; render(); } },
    ZOOMS.map(([v, l]) => h('option', { value: v, selected: v === zoom }, l)));
  const zoomLabel = h('label', { class: 'rd-zoomlbl' }, h('span', {}, '확대'), zoomSel);
  const tools = h('div', { class: 'rd-tools' }, modeGroup, zoomLabel);
  const info = h('span', { class: 'muted rd-info' }); // 「N쪽 · A5 · 표지 포함」
  const zoomNote = h('span', { class: 'muted rd-zoomnote' });
  const panHint = h('p', { class: 'rd-panhint', hidden: true }, '확대 중 · 끌어서 쪽 안을 보고, 이전·다음으로 넘겨요');
  const stage = h('div', { class: 'rd-stage' }, sidePrev, view, sideNext);
  const el = h('div', { class: `bookview${editor ? ' is-editor' : ''}` }, panHint, stage);

  // ---------- views ----------
  function buildViews(count) {
    const v = [];
    if (!spread) { for (let i = 0; i < count; i++) v.push({ a: i, len: 1, slot: 'center' }); return v; }
    v.push({ a: 0, len: 1, slot: 'center' }); // front cover alone
    let i = 1;
    while (i <= count - 2) {
      if (i + 1 <= count - 2) { v.push({ a: i, len: 2, slot: 'both' }); i += 2; } else { v.push({ a: i, len: 1, slot: 'left' }); i += 1; }
    }
    if (count > 1) v.push({ a: count - 1, len: 1, slot: 'center' }); // back cover alone
    return v;
  }
  const viewOf = (page) => Math.max(0, views.findIndex((v) => page - 1 >= v.a && page - 1 < v.a + v.len));

  function place() {
    const v = views[vi];
    if (!v) return;
    const u = book.st.pagePx; // a whole number of pixels (render), so no sliver of the next page shows at the edge
    const shown = v.slot === 'left' ? 2 : v.len; // a lone left page is shown with its blank facing page
    win.style.left = `${v.slot === 'center' ? Math.round((frame.offsetWidth - shown * u) / 2) : 0}px`;
    win.style.width = `${shown * u}px`;
    win.dataset.a = String(v.a);
    win.dataset.len = String(v.len);
    book.el.style.transform = `translateX(${-v.a * u}px)`;
    win.scrollLeft = 0; win.scrollTop = 0; book.el.scrollLeft = 0; // focus can scroll even a clipped box in some browsers
    fold.hidden = shown < 2;
    endpaper.hidden = v.slot !== 'left';
    const count = book.st.count;
    const label = v.a === 0 ? ' · 앞표지' : v.a === count - 1 ? ' · 뒤표지' : '';
    where.textContent = v.len === 2 ? `${v.a + 1}–${v.a + 2} / ${count}쪽` : `${v.a + 1} / ${count}쪽${label}`;
    const had = document.activeElement;
    prevBtn.disabled = vi === 0;
    nextBtn.disabled = vi === views.length - 1;
    sidePrev.disabled = prevBtn.disabled;
    sideNext.disabled = nextBtn.disabled;
    // a focused button that turns off would drop focus to the page and the keys would stop; the inputs are never touched
    if (had?.disabled && (had === prevBtn || had === nextBtn)) view.focus({ preventScroll: true });
    onPlace?.({ page: reading, single, zoom, view: v, count });
  }

  /** turn to view `to`; `user` = a deliberate turn (short effect unless reduced motion); re-renders never animate */
  function go(to, dir, user = false) {
    if (to < 0 || to >= views.length || to === vi) return;
    vi = to;
    reading = views[to].a + 1;
    anim?.cancel(); // a quick second press is never slowed by the first one's animation
    place();
    view.scrollTo(0, 0); // zoomed: a new page starts at its top
    if (user && !reduced()) {
      // a short, plain turn: the new page slides in a little and settles; translate + opacity only (text is not scaled)
      anim = win.animate([{ opacity: 0.35, transform: `translateX(${dir * 22}px)` }, { opacity: 1, transform: 'none' }], { duration: 170, easing: 'ease-out' });
    }
  }
  const goPage = (page, user = false) => { const to = viewOf(page); go(to, to > vi ? 1 : -1, user); };
  const goNode = (node, user = false) => { if (node) goPage(book.pageOf(node) + 1, user); };

  function jumpTo(id) {
    goNode(book.flow.querySelector(`#${CSS.escape(id)}`), true);
  }

  // ---------- size ----------
  let pending = null; // after(): extra work once the pages exist (editor: follow the edit), run before placement
  function render(after) {
    if (!view.clientWidth) { pending = after || pending; return; } // hidden (phone edit view): render once shown
    const p = getProject();
    const size = PAGE_SIZES[p.layout.pageSize] || PAGE_SIZES.A5;
    const availW = Math.max(200, view.clientWidth - 16);
    const roomH = room ? room() : view.clientHeight;
    const availH = roomH === Infinity ? Infinity : Math.max(240, roomH - 16);
    const fit = (per) => Math.min(availW / (size.w * per), availH / size.h);
    const textPx = (mm) => p.layout.fontSize * 0.3528 * mm;
    spread = single == null ? textPx(fit(2)) >= MIN_TEXT_PX : !single;
    modeBtns.forEach((b) => b.setAttribute('aria-pressed', String((b.dataset.mode === '2') === spread)));
    const per = spread ? 2 : 1;
    const want = zoom === 'actual' ? PX_PER_MM : zoom === 'large' ? PX_PER_MM * 1.4 : zoom === 'read' ? Math.max(fit(per), READ_PX / (10 * 0.3528)) : fit(per);
    const U = Math.floor(size.w * want); // whole pixels per page (MT-22 T-062 #1)
    const mm = U / size.w;
    const pageH = Math.round(size.h * mm);
    frame.style.width = `${per * U}px`;
    frame.style.height = `${pageH}px`;
    win.style.height = `${pageH}px`;
    const pan = per * U > availW + 1 || pageH > availH + 1;
    view.classList.toggle('pan', pan);
    panHint.hidden = !pan;
    // editor: the view is as tall as the page (phone) or as the sticky panel allows (desktop); reader: flex-filled
    if (editor) view.style.height = roomH === Infinity ? `${pan ? Math.min(pageH + 16, Math.round(innerHeight * 0.72)) : pageH + 16}px` : `${Math.min(roomH, pageH + 16)}px`;
    stage.classList.toggle('no-side', pan || (view.clientWidth - per * U) / 2 < 56); // the side targets never cover the page
    info.textContent = `${book.st.count || '…'}쪽 · ${size.label} · 표지 포함`;
    zoomNote.textContent = `화면 배율 ${Math.round((mm / PX_PER_MM) * 100)}% · 책의 글자 크기 ${p.layout.fontSize}pt는 그대로예요`;
    const extra = after || pending; pending = null;
    book.render(p, mm, true, (count) => {
      views = buildViews(count);
      vi = viewOf(Math.min(reading, count)); // read here, not before the frame: a turn made meanwhile is kept (T-063 #3)
      info.textContent = `${count}쪽 · ${size.label} · 표지 포함`;
      onPages?.(count);
      extra?.(count);
      place();
    });
    place(); // the new scale is set now; place the old view at once so no frame shows a mis-framed page (T-062 #2)
  }

  // ---------- input ----------
  const KEYS = { ArrowRight: 1, PageDown: 1, ArrowLeft: -1, PageUp: -1 };
  const onKey = (e) => {
    if (!el.isConnected || e.target.closest?.('select, input, textarea, [contenteditable], .rd-toc-list') || e.altKey || e.ctrlKey || e.metaKey) return;
    if (e.key in KEYS) { e.preventDefault(); turn(KEYS[e.key]); } else if (e.key === 'Home') { e.preventDefault(); go(0, -1, true); } else if (e.key === 'End') { e.preventDefault(); go(views.length - 1, 1, true); }
  };
  // swipe (touch only): one finger, mostly sideways, quick, no text selected; pinch, a pinch-zoomed page and zoomed
  // panning are left to the browser
  let touch = null;
  let fingers = 0;
  view.addEventListener('pointerdown', (e) => { if (e.pointerType !== 'touch') return; fingers += 1; touch = fingers === 1 && !view.classList.contains('pan') ? { x: e.clientX, y: e.clientY, t: e.timeStamp } : null; });
  const lift = (e) => {
    if (e.pointerType !== 'touch') return;
    fingers = Math.max(0, fingers - 1);
    const s = touch; touch = null;
    if (!s || e.type === 'pointercancel' || (window.visualViewport?.scale || 1) > 1.01) return;
    const dx = e.clientX - s.x; const dy = e.clientY - s.y;
    if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy) * 1.5 || e.timeStamp - s.t > 700 || String(getSelection()).trim()) return;
    turn(dx < 0 ? 1 : -1);
  };
  view.addEventListener('pointerup', lift);
  view.addEventListener('pointercancel', lift);
  // focus moving to a link on another page (Tab) turns to that page; the window itself never scrolls unless zoomed
  view.addEventListener('focusin', (e) => {
    if (!book.el.contains(e.target)) return;
    win.scrollLeft = 0; win.scrollTop = 0;
    const page = book.pageOf(e.target) + 1;
    if (viewOf(page) !== vi) goPage(page);
  });
  view.addEventListener('scroll', () => { if (!view.classList.contains('pan') && (view.scrollLeft || view.scrollTop)) view.scrollTo(0, 0); });

  let last = '';
  // editor: the view's height is set by render itself, so only the width is watched (else the observer would loop)
  const ro = new ResizeObserver(() => { const k = editor ? String(view.clientWidth) : `${view.clientWidth}x${view.clientHeight}`; if (k !== last) { last = k; render(); } });
  ro.observe(view); // also the first render, once the view has a size

  const setZoom = (v) => { zoom = v; zoomSel.value = v; };
  return {
    el, view, nav, tools, info, zoomNote, onKey, render, goPage, goNode, setZoom, panHint, pageOf: book.pageOf, flow: book.flow, front: book.front, get zoom() { return zoom; },
    get count() { return book.st.count; }, get views() { return views; }, get vi() { return vi; }, get reading() { return reading; },
    destroy: () => ro.disconnect(),
  };
}
