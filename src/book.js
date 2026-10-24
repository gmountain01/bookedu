// Renders the student's book (W-033, docs/DESIGN.md Plan B1). Preview, completed book and print all use
// bookSequence(), bookVars() and styles/book.css, so the three show the same pages. All text via textContent.
import { h } from './dom.js';
import { headings, PAGE_SIZES } from './state.js';
import { assetSrc, COVER_IMAGES } from './images.js';

// Embedded faces first (src/fonts), so the book never silently falls back to whatever the device has.
export const FONT_STACKS = {
  myeongjo: "'Chaekgongbang Serif', 'Noto Serif KR', 'Batang', serif",
  gothic: "'Chaekgongbang Sans', 'Malgun Gothic', sans-serif",
};

// Load both weights now: printing from another screen (Ctrl+P) must not catch the face half-loaded.
document.fonts?.load("400 1em 'Chaekgongbang Serif'"); document.fonts?.load("700 1em 'Chaekgongbang Serif'");

// Each design sets these together; the student may change them afterwards (step 3).
export const DESIGN_DEFAULTS = {
  classic: { fontFamily: 'myeongjo', fontSize: 10, lineHeight: 1.75, margin: 18 },
  modern: { fontFamily: 'gothic', fontSize: 10, lineHeight: 1.7, margin: 18 },
  warm: { fontFamily: 'myeongjo', fontSize: 10, lineHeight: 1.7, margin: 18 }, // MT-16: 9pt/12mm made 37-syllable lines and tiny labels
};

// ---- colour: the cover colour is the book's one accent ----
const rgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
const lum = (c) => { const [r, g, b] = c.map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4)); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const contrast = (a, b) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
const toHex = (c) => `#${c.map((v) => Math.round(v * 255).toString(16).padStart(2, '0')).join('')}`;
/** The accent darkened just enough to read as text on white paper (4.5:1). */
export function accentInk(hex) {
  let c = rgb(/^#[0-9a-f]{6}$/i.test(hex || '') ? hex : '#1d4fb8');
  for (let i = 0; i < 20 && contrast(lum(c), 1) < 4.5; i++) c = c.map((v) => v * 0.88);
  return toHex(c);
}
/** Text colour on the cover: white on dark covers, ink on light ones. */
export const coverInk = (hex) => (contrast(lum(rgb(hex)), 1) >= 3 ? '#ffffff' : '#1b1d22');

/** Page geometry in mm. Margins scale with the page size; bottom has room for the folio. */
export function geometry(layout) {
  const size = PAGE_SIZES[layout.pageSize] || PAGE_SIZES.A5;
  const k = size.w / 148;
  const m = (layout.margin || 18) * k;
  const g = { w: size.w, h: size.h, top: m * 0.95, bottom: m * 1.25, side: m, inner: m * 1.1, outer: m * 0.9 };
  g.colh = g.h - g.top - g.bottom;
  return g;
}

export function bookVars(p) {
  const L = p.layout;
  const g = geometry(L);
  const color = p.cover?.accentColor || p.cover?.backgroundColor || '#1d4fb8'; // the accent: chosen with a cover photograph, else the cover colour
  return {
    '--pw': g.w, '--ph': g.h, '--mt': g.top, '--mb': g.bottom, '--ms': g.side, '--colh': g.colh,
    '--fs': L.fontSize, '--lh': L.lineHeight,
    '--book-font': FONT_STACKS[L.fontFamily] || FONT_STACKS.myeongjo,
    '--serif': FONT_STACKS.myeongjo, '--sans': FONT_STACKS.gothic,
    '--accent': color, '--accent-ink': accentInk(color), '--cover-ink': coverInk(color),
  };
}
export function applyVars(el, vars) { for (const [k, v] of Object.entries(vars)) el.style.setProperty(k, v); }

const anchor = (prefix, b) => `${prefix}-${b.id}`;
// URLs and long Latin strings may break anywhere, so the line before them does not stretch (MT-16)
const URL_RE = /(https?:\/\/\S+|www\.\S+)/g;
const withUrls = (t) => String(t || '').split(URL_RE).map((part, i) => (i % 2 ? h('span', { class: 'bk-url' }, part) : part));
const paras = (text, cls = 'bk-p') => String(text || '').split(/\n+/).filter((t) => t.trim()).map((t) => h('p', { class: cls }, withUrls(t)));

// 「1장 늘 지나던 길」 → number set apart from the title, both still inside the one heading element.
const CHAPTER_NO = /^((?:제\s?)?\d+\s?[장부편]|[일이삼사오육칠팔구십]+\s?장|chapter\s?\d+|\d+\.)\s+(.+)$/i;
function headingText(b) {
  const text = b.text || ''; // an empty heading keeps its place (chapter break) but prints nothing (MT-16)
  const m = b.level === 1 ? CHAPTER_NO.exec(text) : null;
  return m ? [h('span', { class: 'bk-no' }, m[1]), h('span', { class: 'bk-ht' }, m[2])] : text;
}
// 「그림 1. 오후 네 시의 골목」 → the label in the accent, so the caption is clearly the figure's.
const CAP_NO = /^((?:그림|사진|표|도판|자료)\s?\d+[.:]?)\s*(.*)$/;
const CAP_SRC = /\s*\(((?:자료 )?사진|출처|그림)\s*:\s*([^)]*)\)\s*$/;
function captionText(text) {
  const src = CAP_SRC.exec(text || '');
  const main = src ? text.slice(0, src.index) : text;
  const m = CAP_NO.exec(main || '');
  return [m ? [h('span', { class: 'cap-no' }, m[1]), ' ', m[2]] : main, src ? h('span', { class: 'cap-src' }, `${src[1]}: ${src[2]}`) : null];
}

export function bodyNodes(p, prefix = 'pv') {
  const assets = new Map(p.assets.map((a) => [a.id, a]));
  return p.blocks.map((b) => tagged(b, (() => {
    // chapters open on a right-hand page in the literary design (class rt: see paginate() in preview.js)
    if (b.type === 'heading') return h(`h${b.level + 1}`, { id: anchor(prefix, b), class: `bk-h bk-h${b.level}${b.level === 1 && p.layout.theme !== 'modern' && p.layout.theme !== 'warm' ? ' rt' : ''}` }, headingText(b));
    if (b.type === 'paragraph') return b.style === 'quote' ? h('blockquote', { class: 'bk-quote' }, paras(b.text, 'bk-qp')) : h('p', { class: 'bk-p' }, withUrls(b.text));
    if (b.type === 'image') {
      const a = assets.get(b.assetId);
      const ar = a && a.width && a.height ? a.width / a.height : 1.5;
      // --ar keeps the picture's proportions at any scale (preview px, print mm)
      return h('figure', { class: `bk-fig ${ar >= 1.15 ? 'is-wide' : 'is-tall'}`, style: `--ar:${ar.toFixed(4)}` },
        a ? h('img', { src: assetSrc(a), alt: b.alt || '', width: a.width || null, height: a.height || null }) : h('div', { class: 'bk-missing' }, '그림을 찾을 수 없어요'),
        b.caption ? h('figcaption', {}, captionText(b.caption)) : null);
    }
    if (b.type === 'table') {
      const [head, ...rest] = b.rows || [[]];
      // columns of numbers (years, amounts, percentages) are right-aligned with figures of equal width
      const num = head.map((_, c) => rest.length > 0 && rest.every((r) => NUMERIC.test(r[c] || '')));
      const cls = (c) => (num[c] ? 'num' : null);
      return h('figure', { class: 'bk-tablefig' },
        h('table', { class: 'bk-table' },
          b.caption ? h('caption', {}, captionText(b.caption)) : null,
          h('thead', {}, h('tr', {}, head.map((c, i) => h('th', { scope: 'col', class: cls(i) }, c)))),
          h('tbody', {}, rest.map((r) => h('tr', {}, r.map((c, i) => h('td', { class: cls(i) }, c)))))));
    }
    return null;
  })()));
}
const NUMERIC = /^[\s\d.,%+\-–~:/년월일원개명쪽시분초℃]*\d[\s\d.,%+\-–~:/년월일원개명쪽시분초℃]*$/;
const tagged = (b, node) => { if (node) node.dataset.bid = b.id; return node; };

export function tocNodes(p, prefix = 'pv', onJump) {
  const hs = headings(p);
  if (!hs.length) return h('p', { class: 'bk-empty' }, '아직 제목이 없어서 목차가 비어 있어요. 2단계에서 장·절 제목을 써 보세요.');
  return h('ol', { class: 'bk-toc' }, hs.map((b) => h('li', { class: `toc-l${b.level}` },
    h('a', {
      href: `#${anchor(prefix, b)}`,
      onclick: (e) => { e.preventDefault(); onJump ? onJump(anchor(prefix, b)) : document.getElementById(anchor(prefix, b))?.scrollIntoView({ block: 'start' }); },
    }, headingText({ ...b, text: b.text || '' })))));
}

// Long titles get a smaller size step so they still sit well on the cover and title page.
const titleLen = (t) => { const n = [...(t || '')].length; return n > 26 ? 'xl' : n > 16 ? 'l' : n > 9 ? 'm' : 's'; };

export function frontMatterNodes(p) {
  const { meta, frontMatter: fm } = p;
  return {
    titlePage: h('div', { class: 'bk-titlepage', 'data-len': titleLen(meta.title) },
      h('p', { class: 'bk-tp-title' }, meta.title || '제목 없음'),
      fm.titlePage ? h('p', { class: 'bk-tp-sub' }, fm.titlePage) : null,
      h('span', { class: 'bk-tp-rule', 'aria-hidden': 'true' }),
      h('p', { class: 'bk-tp-author' }, meta.authorAlias || '지은이')),
    // empty parts are left out of the book (no instruction text is printed, MT-16); step 6 asks for them
    copyright: String(fm.copyrightText || '').trim() ? h('div', { class: 'bk-copyright' }, String(fm.copyrightText).split('\n').map((l) => h('p', {}, l || ' '))) : null,
    preface: String(fm.preface || '').trim() ? h('div', { class: 'bk-preface' }, h('h2', { class: 'bk-ft' }, '책을 펴내며'), paras(fm.preface)) : null,
  };
}

/** The cover layout in use: the student's choice, or panel with a picture / typographic without one. */
export function coverLayout(p) {
  const img = p.assets.find((a) => a.id === p.cover.imageId);
  const L = p.cover.layout || (img ? 'panel' : 'type');
  if (!img) return 'type';
  return L === 'full' && titleTooLong(p, img) ? 'panel' : L;
}
const LEN_ORDER = ['s', 'm', 'l', 'xl'];
/** A built-in photograph's open area holds titles up to meta.maxLen; longer titles use the panel layout (MT-18). */
export function titleTooLong(p, img = p.assets.find((a) => a.id === p.cover.imageId)) {
  const meta = img && COVER_IMAGES[img.builtin];
  return !!meta?.maxLen && LEN_ORDER.indexOf(titleLen(p.meta.title)) > LEN_ORDER.indexOf(meta.maxLen);
}
/** Credit printed on the back cover: the built-in photograph's credit, or the student's source note. */
export function coverCredit(p) {
  const img = p.assets.find((a) => a.id === p.cover.imageId);
  if (!img) return '';
  const meta = COVER_IMAGES[img.builtin];
  return meta ? meta.credit : (img.sourceNote ? `표지 그림: ${img.sourceNote}` : '');
}

// W-035: four cover layouts that differ in arrangement, with four front elements in their own places —
//  title (the centre), subtitle (frontMatter.titlePage, a small heading above the title), copy (cover.copy, a short line
//  set apart from the title), author. Empty elements are not drawn and the others close up.
//  full  — the picture fills the cover; the title block sits where the picture leaves room (textY/textAlign); the copy
//          takes a second place (the photo's copyY, else the opposite end); author at the foot (or head when the title is low)
//  band  — the picture above, a band of cover colour below holding subtitle + title (left) and copy + author (right)
//  panel — a title area on the cover colour above a picture panel
//  type  — no picture: author at the head, a bar, a large title anchored low, the copy at the foot
// Back cover: a strip of the front picture (when there is one), the headline, the introduction, the reader it suits.
export function coverNodes(p) {
  const { meta, cover, frontMatter: fm } = p;
  const img = p.assets.find((a) => a.id === cover.imageId);
  const layout = coverLayout(p);
  const paper = cover.backgroundColor;
  const photo = COVER_IMAGES[img?.builtin];
  const ink = cover.ink || (layout === 'full' ? '#ffffff' : coverInk(paper));
  const accent = cover.accentColor || paper;
  const ruleC = contrast(lum(rgb(accent)), lum(rgb(paper))) >= 1.8 ? accent : coverInk(paper);
  const copyY = photo?.copyY ?? (cover.textY > 0.5 ? 0.1 : 0.76);
  const style = `--cv:${paper};--cv-ink:${coverInk(paper)};--ink:${ink};--rule-c:${ruleC};--fx:${cover.focusX}%;--fy:${cover.focusY}%;--ty:${cover.textY};--cy:${copyY};--ta:${cover.textAlign}`;
  const len = titleLen(meta.title);
  const author = String(meta.authorAlias || '').trim();
  const sub = String(fm?.titlePage || '').trim();
  const copy = String(cover.copy || '').trim();
  const credit = coverCredit(p);
  const art = img && layout !== 'type' ? h('div', { class: 'cv-art' }, h('img', { class: 'cv-img', src: assetSrc(img), alt: '', width: img.width || null, height: img.height || null })) : null;
  const subEl = sub ? h('p', { class: 'cv-sub' }, sub) : null;
  const titleEl = h('p', { class: 'cv-title' }, meta.title || '제목 없음');
  const copyEl = copy ? h('p', { class: 'cv-copy' }, copy) : null;
  const authorEl = author ? h('p', { class: `cv-author${[...author].length > 12 ? ' is-long' : ''}` }, author) : null;
  const withTitle = layout === 'full' && !!photo?.authorWithTitle;
  const rule = layout === 'full' || layout === 'band' ? null : h('span', { class: 'cv-rule', 'aria-hidden': 'true' });
  const front = layout === 'band'
    ? h('div', { class: 'cv-front lay-band', style, 'data-len': len },
      art,
      h('div', { class: 'cv-band' },
        h('div', { class: 'cv-head' }, subEl, titleEl),
        h('div', { class: 'cv-side' }, copyEl, authorEl)))
    : h('div', { class: `cv-front lay-${layout}${layout === 'full' && cover.textY > 0.6 ? ' au-top' : ''}`, style, 'data-len': len, 'data-ta': cover.textAlign },
      art,
      h('div', { class: 'cv-head' }, subEl, titleEl, rule, withTitle ? authorEl : null),
      copyEl,
      withTitle ? null : authorEl);
  const reader = String(meta.targetReader || '').trim();
  const headline = String(cover.backHeadline || '').trim();
  return {
    front,
    spine: h('div', { class: 'cv-spine', style }, h('span', { class: 'cv-spine-t' }, meta.title || '제목'), author ? h('span', { class: 'cv-spine-a' }, author) : null),
    back: h('div', { class: `cv-back${img ? ' has-strip' : ''}`, style },
      img ? h('div', { class: 'cv-strip', 'aria-hidden': 'true' }, h('img', { class: 'cv-img', src: assetSrc(img), alt: '' })) : h('span', { class: 'cv-rule', 'aria-hidden': 'true' }),
      h('div', { class: 'cv-back-body' },
        headline ? h('p', { class: 'cv-headline' }, headline) : null,
        h('div', { class: 'cv-blurb' }, paras(cover.backText, 'cv-bp')),
        reader ? h('div', { class: 'cv-reader' }, h('p', { class: 'cv-reader-k' }, '이런 독자에게'), h('p', { class: 'cv-reader-v' }, reader)) : null),
      h('div', { class: 'cv-back-foot' },
        h('p', { class: 'cv-back-id' }, h('span', {}, meta.title || '제목 없음'), author ? h('span', {}, author) : null),
        credit ? h('p', { class: 'cv-credit' }, credit) : null)),
  };
}

/**
 * The whole book in print order. covers: full-bleed pages outside the text flow; flow: the interior sections
 * (title page, copyright, preface, contents, body). data-page="plain" pages carry no folio, in print and preview.
 */
export function bookSequence(p, prefix, onJump) {
  const fm = frontMatterNodes(p);
  const c = coverNodes(p);
  const body = bodyNodes(p, prefix);
  if (!body.length) body.push(h('p', { class: 'bk-empty' }, '원고를 쓰면 여기에 책 모양으로 보여요.'));
  return {
    front: c.front,
    back: c.back,
    flow: [
      // rt = starts on a right-hand (odd) page, as in printed books: title page, preface, contents, body
      h('section', { class: 'bk-sec bk-sec-title rt', 'data-page': 'plain' }, fm.titlePage),
      fm.copyright ? h('section', { class: 'bk-sec bk-sec-copy', 'data-page': 'plain' }, fm.copyright) : null,
      fm.preface ? h('section', { class: 'bk-sec bk-sec-preface rt' }, fm.preface) : null,
      headings(p).length ? h('section', { class: 'bk-sec bk-tocpage' }, h('h2', { class: 'bk-ft' }, '차례'), tocNodes(p, prefix, onJump)) : null,
      h('section', { class: 'bk-sec bk-body rt' }, body),
    ].filter(Boolean),
  };
}
