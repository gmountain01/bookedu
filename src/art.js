// Illustrations drawn for this app (src/illustrations/*.svg), inlined at build time as data URLs.
import { h } from './dom.js';

const files = import.meta.glob('./illustrations/*.svg', { eager: true, query: '?url', import: 'default' });
const SIZE = { scene: [480, 360], step: [96, 96], slide: [640, 360] };

export const art = (name) => files[`./illustrations/${name}.svg`] || '';
export function artImg(name, cls = '', kind = 'scene') {
  const src = art(name);
  if (!src) return null;
  const [w, hgt] = SIZE[kind];
  return h('img', { src, class: `art ${cls}`, alt: '', width: w, height: hgt, 'aria-hidden': 'true', draggable: 'false' });
}
