// Fold dist/assets/*.js|css into dist/index.html so the app opens by double-click (file://).
import { readFileSync, writeFileSync, rmSync } from 'node:fs';

const dir = new URL('../dist/', import.meta.url);
let html = readFileSync(new URL('index.html', dir), 'utf8');
const read = (p) => readFileSync(new URL(p.replace(/^\.\//, ''), dir), 'utf8');

html = html.replace(/<script type="module" crossorigin src="([^"]+)"><\/script>/g, (_, src) =>
  `<script type="module">${read(src).replace(/<\/script/gi, '<\/script')}</script>`);
html = html.replace(/<link rel="stylesheet" crossorigin href="([^"]+)">/g, (_, href) =>
  `<style>${read(href)}</style>`);

if (/src="\.\/assets|href="\.\/assets/.test(html)) throw new Error('unresolved asset reference left in index.html');
writeFileSync(new URL('index.html', dir), html);
rmSync(new URL('assets/', dir), { recursive: true, force: true });
console.log(`inlined dist/index.html (${(html.length / 1024).toFixed(0)} KB)`);
