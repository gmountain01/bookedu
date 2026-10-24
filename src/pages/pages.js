// The page engine every book screen shares (W-033, W-039; docs/DESIGN.md Plan B1 and W-039). Covers are full-bleed
// pages beside the text flow; CSS multi-column cuts the interior into pages of the print text block (same width, same
// height, same embedded fonts), so page n here is page n of the printed PDF. Laid out at print size (1mm = 96/25.4 px)
// and only scaled for the screen with a transform: a window width never changes the pages.
// ponytail: column layout reproduces the print breaks for this app's block types; tests/book_audit.py and
// tests/book_cases.py compare them page by page. Running heads or contents page numbers would need a paged-media
// layout engine.
import { h } from '../dom.js';
import { bookSequence, bookVars, applyVars, geometry } from '../book.js';

export const PX_PER_MM = 96 / 25.4; // CSS reference = print: 「실제 크기」

/**
 * Right-hand starts (class rt): Chromium ignores break-before: right, so a blank page is inserted before any rt
 * element that would land on an even page (front cover = page 1). Synchronous: reads layout after each insert.
 * Used for the preview and, on an off-screen copy, for print, so both get the same blank pages.
 * @param {HTMLElement} flow the column container, laid out at print size
 * @param {number} U one page width in px (unscaled)
 */
export function paginate(flow, U) {
  flow.style.width = `${U}px`; // one page wide: columns get exactly the print text width
  const box = flow.getBoundingClientRect();
  const u = box.width; // one page as measured on screen (the preview strip is scaled by a transform; print is not)
  const col = (x) => Math.floor((x - box.left + 1) / u);
  // Figures that do not fit go to the next page whole (with their caption). If that leaves more than about a sixth of the
  // page empty, the paragraph after the figure is set before it, as a typesetter would; one paragraph at most,
  // never a heading; the manuscript itself is unchanged.
  const pad = parseFloat(getComputedStyle(flow).paddingBottom) * (u / U);
  const colBottom = box.bottom - pad;
  const colH = colBottom - box.top - parseFloat(getComputedStyle(flow).paddingTop) * (u / U);
  for (const fig of flow.querySelectorAll('.bk-body > .bk-fig, .bk-body > .bk-tablefig')) {   // tables too (W-035): they cannot shrink, so only the paragraph move applies
    const prev = fig.previousElementSibling;
    const next = fig.nextElementSibling;
    if (!prev) continue;
    const last = [...prev.getClientRects()].at(-1);
    if (!last || col(fig.getBoundingClientRect().left) !== col(last.left) + 1) continue;
    const gap = colBottom - last.bottom;
    if (gap <= colH * 0.15) continue;   // MT-19: a 31mm gap (just under a fifth) still read as a hole
    // first choice: a slightly smaller picture that fits the space left (not below 70% of its size, MT-16)
    const img = fig.querySelector('img');
    const fr = fig.getBoundingClientRect();
    const margin = parseFloat(getComputedStyle(fig).marginTop) * (u / U) * 2;
    const ratio = img ? (gap - margin - (fr.height - img.getBoundingClientRect().height) - 2) / img.getBoundingClientRect().height : 0;
    if (ratio >= 0.7 && ratio < 1) { fig.style.setProperty('--imgw', `${img.offsetWidth * ratio}px`); fig.dataset.fit = 'shrunk'; continue; }
    // otherwise the next paragraph (never a heading) is set before the picture
    if (next?.classList.contains('bk-p')) { fig.before(next); fig.dataset.moved = 'after-text'; }
  }
  for (const el of flow.querySelectorAll('.rt')) {
    const page = col(el.getBoundingClientRect().left) + 2;
    if (page % 2) continue;
    const sec = el.classList.contains('bk-sec');
    const at = !sec && !el.previousElementSibling ? el.parentElement : el; // first in its section: blank before the section
    const asSec = at.classList.contains('bk-sec');
    at.before(h(asSec ? 'section' : 'div', { class: asSec ? 'bk-blank bk-sec' : 'bk-blank', 'data-page': 'plain', 'aria-hidden': 'true' }));
  }
  const n = Math.max(1, Math.ceil(flow.scrollWidth / U - 0.02));
  flow.style.width = `${n * U}px`;
  return n;
}

/**
 * Pages of one book: [blank lead (spreads only)] [front cover] [interior columns] [back cover].
 * The pages are laid out at print size (1mm = 96/25.4 CSS px, as in print) and only scaled for the screen with a
 * transform, so line and page breaks are the print's own: at small screen sizes glyph widths round to pixels and
 * a layout at screen size broke lines differently (W-033, case long-titles: 8 preview pages vs 7 printed).
 */
export function pagedBook({ prefix, onJump }) {
  const lead = h('div', { class: 'pg pg-blank', 'aria-hidden': 'true' });
  const front = h('div', { class: 'pg pg-cover' });
  const back = h('div', { class: 'pg pg-cover pg-back' });
  const flow = h('div', { class: 'pv-flow' });
  const folios = h('div', { class: 'pv-folios', 'aria-hidden': 'true' });
  const strip = h('div', { class: 'book pv-strip' }, lead, front, h('div', { class: 'pv-flowwrap' }, flow, folios), back);
  const box = h('div', { class: 'pv-scale' }, strip);
  const st = { pagePx: 0, count: 0, single: true, scale: 1 };

  function render(p, mm, single, done) {
    st.single = single;
    st.scale = mm / PX_PER_MM;
    const g = geometry(p.layout);
    const U = g.w * PX_PER_MM; // one page, unscaled
    applyVars(strip, bookVars(p));
    strip.style.setProperty('--mm', `${PX_PER_MM}px`);
    strip.style.transform = `scale(${st.scale})`;
    strip.dataset.theme = p.layout.theme || 'classic';
    const seq = bookSequence(p, prefix, onJump);
    front.replaceChildren(seq.front);
    back.replaceChildren(seq.back);
    flow.replaceChildren(...seq.flow);
    lead.hidden = single;
    st.pagePx = U * st.scale; // on screen
    requestAnimationFrame(() => {
      if (!flow.isConnected) return;
      const n = paginate(flow, U);
      box.style.width = `${(n + 2 + (single ? 0 : 1)) * st.pagePx}px`;
      box.style.height = `${g.h * mm}px`;
      // folios: the PDF's page numbers (front cover = 1); none on title page, copyright, blank pages
      const x0 = flow.getBoundingClientRect().left;
      const plain = new Set([...flow.querySelectorAll('[data-page="plain"]')].map((el) => Math.floor((el.getBoundingClientRect().left - x0 + 1) / st.pagePx)));
      folios.replaceChildren(...Array.from({ length: n }, (_, k) => (plain.has(k) ? null
        : h('span', { class: `pv-folio ${(k + 2) % 2 ? 'odd' : 'even'}`, style: { left: `${k * U}px`, width: `${U}px` } }, String(k + 2)))).filter(Boolean));
      st.count = n + 2;
      done?.(st.count);
    });
  }
  /** index of the strip page that holds node (lead counts when shown) */
  const pageOf = (node) => Math.floor((node.getBoundingClientRect().left - strip.getBoundingClientRect().left + 1) / st.pagePx);
  return { el: box, flow, front, render, pageOf, st };
}
