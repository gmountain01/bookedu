import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';

// VITE_PUBLIC=1 (GitHub Pages build): the admin presentation entry (src/pages/admin.js, private) is replaced by the
// stub src/pages/admin.public.js, so no presentation code or data is bundled. The local build uses the real entry.
const PUBLIC = Boolean(process.env.VITE_PUBLIC);
const here = (p) => fileURLToPath(new URL(p, import.meta.url)).split('\\').join('/');

// One JS chunk + one CSS file, so scripts/inline.mjs can fold them into dist/index.html.
export default defineConfig({
  base: './',
  // W-052: the header shows when this build was made (Korean date, fixed at build time).
  define: { __BUILD_DATE__: JSON.stringify(new Date().toLocaleDateString('sv-SE', { timeZone: 'Asia/Seoul' })) },
  resolve: {
    // the whole specifier is replaced (a partial match would leave '..' in front of the absolute path)
    alias: PUBLIC ? [{ find: /^.*\/pages\/admin\.js$/, replacement: here('./src/pages/admin.public.js') }] : [],
  },
  build: {
    assetsInlineLimit: 100_000_000,
    cssCodeSplit: false,
    modulePreload: false,
  },
});
