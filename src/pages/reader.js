// The completed book as an e-book reader (W-038, W-039): the shared book view in reader mode plus reading chrome —
// a contents menu with page numbers, 처음으로, keys anywhere in the (modal) dialog, and the page remembered per project
// for reopening in this session.
import { h } from '../dom.js';
import { getProject } from '../state.js';
import { bookView } from './bookView.js';

const memory = new Map(); // project id -> { page, single, zoom }

export function bookReader() {
  const p0 = getProject();
  let tocItems = [];
  const tocList = h('ol', { class: 'rd-toc-list' });
  const tocSum = h('summary', { class: 'btn sm' }, '차례');
  const toc = h('details', { class: 'rd-toc' }, tocSum, tocList);
  const firstBtn = h('button', { class: 'btn sm', type: 'button', onclick: () => bv.goPage(1, true) }, '처음으로');

  const bv = bookView({
    mode: 'reader', prefix: 'fb', initial: memory.get(p0.id), onPages: (count) => fillToc(count),
    onPlace: ({ page, single, zoom, view: v }) => {
      memory.set(p0.id, { page, single, zoom });
      firstBtn.disabled = v.a === 0;
      const lastShown = v.a + v.len; // contents: mark the last entry that starts on or before the pages on screen
      const cur = tocItems.filter((t) => t.page <= lastShown).at(-1);
      tocItems.forEach((t) => (t === cur ? t.btn.setAttribute('aria-current', 'location') : t.btn.removeAttribute('aria-current')));
    },
  });
  toc.addEventListener('keydown', (e) => { // Esc closes the menu, not the whole book
    if (e.key === 'Escape' && toc.open) { e.preventDefault(); e.stopPropagation(); toc.open = false; tocSum.focus(); }
  });

  function fillToc(count) {
    const items = [{ text: '앞표지', page: 1 }];
    const tp = bv.flow.querySelector('.bk-tocpage');
    if (tp) items.push({ text: '차례', page: bv.pageOf(tp) + 1 });
    for (const a of bv.flow.querySelectorAll('.bk-toc a')) {
      const target = bv.flow.querySelector(`#${CSS.escape(a.getAttribute('href').slice(1))}`);
      const text = [...a.childNodes].map((n) => n.textContent.trim()).filter(Boolean).join(' '); // 「1장」 and the title are separate spans
      const level = Number((a.closest('li').className.match(/toc-l(\d)/) || [0, 1])[1]);
      if (target) items.push({ text, page: bv.pageOf(target) + 1, level });
    }
    if (count > 1) items.push({ text: '뒤표지', page: count });
    tocItems = items.map((t) => ({ ...t, btn: h('button', { type: 'button', onclick: () => { bv.goPage(t.page, true); toc.open = false; bv.view.focus({ preventScroll: true }); } },
      h('span', {}, t.text), h('span', { class: 'rd-toc-pg' }, `${t.page}쪽`)) }));
    tocList.replaceChildren(...tocItems.map((t) => h('li', { class: t.level > 1 ? `sub l${t.level}` : '' }, t.btn)));
  }

  const el = h('section', { class: 'reader full-book', 'aria-label': '완성본' },
    h('div', { class: 'rd-bar' }, h('div', { class: 'rd-tools' }, toc, firstBtn), bv.tools),
    bv.el, bv.nav);
  document.addEventListener('keydown', bv.onKey); // the dialog is modal, so keys anywhere in it turn the pages
  const render = () => bv.render();
  return { el, render, destroy: () => { bv.destroy(); document.removeEventListener('keydown', bv.onKey); } };
}
