import './styles/main.css';
import './styles/journey.css';
import './styles/book.css';
import './styles/deck.css';
import './styles/print.css';
import { h, $, toast, modal, download } from './dom.js';
import { getProject, replaceProject, subscribe, validateProject } from './state.js';
import { loadProject, autosaver, parkRecovery } from './storage.js';
import { mountJourney } from './pages/journey.js';
import { mountStudio, prepareBookPrint } from './pages/studio.js';
import { mountAdminProcess, mountAdminPrompts, prepareDeckPrint } from './pages/admin.js'; // private entry; stubbed in the public build

// Public build (VITE_PUBLIC=1, GitHub Pages): the admin presentation screens are left out — pages/admin.js is replaced
// by a stub module at build time (vite.config.js) and the admin routes show a notice (W-046).
const PUBLIC = Boolean(import.meta.env.VITE_PUBLIC);
// Mode lives in memory only: every fresh open starts in student mode (NAV requirement).
let mode = 'student';
let unmount = null;
let lastStudentRoute = '#/studio';

const STUDENT = [['#/journey', '책은 어떻게 만들어질까'], ['#/studio', '나만의 책 만들기']];
const ADMIN = [['#/admin/process', '발표 1 · 개발 과정'], ['#/admin/prompts', '발표 2 · 사용한 프롬프트 기법']];
const ROUTES = { '/journey': mountJourney, '/studio': mountStudio, '/admin/process': mountAdminProcess, '/admin/prompts': mountAdminPrompts };
const TITLES = { '/journey': '책은 어떻게 만들어질까', '/studio': '나만의 책 만들기', '/admin/process': '개발 과정(관리자)', '/admin/prompts': '사용한 프롬프트 기법(관리자)' };
const toStudent = () => { setMode('student'); location.hash = lastStudentRoute; };

const saveState = h('span', { class: 'save-state', role: 'status', 'aria-live': 'polite' }, '');
const nav = h('nav', { class: 'topnav', 'aria-label': '주 메뉴' });
const modeBadge = h('span', { class: 'mode-badge' });
const headBack = h('button', { class: 'btn sm ghost head-back', type: 'button', onclick: toStudent }, '학생 화면으로 돌아가기');
const main = h('main', { id: 'main', tabindex: '-1' });
const footer = h('footer', { class: 'site-foot' });

export function setMode(next) {
  mode = next;
  document.body.dataset.mode = mode;
  renderChrome();
}
export const getMode = () => mode;

function renderChrome() {
  const items = mode === 'admin' ? ADMIN : STUDENT;
  const path = location.hash || '#/journey';
  nav.replaceChildren(...items.map(([href, label]) =>
    h('a', { href, 'aria-current': path.startsWith(href) ? 'page' : null }, label)));
  modeBadge.textContent = mode === 'admin' ? '관리자 모드 · 발표 화면' : '';
  headBack.hidden = mode !== 'admin';
  footer.replaceChildren(
    h('p', {}, '책공방 · 출판 과정을 배우는 교육용 웹앱 · 만든 책은 서버 전송 없이 이 브라우저에만 저장'),
    mode === 'admin'
      ? h('button', { class: 'btn ghost', type: 'button', onclick: toStudent }, '학생 화면으로 돌아가기')
      : PUBLIC ? null : h('button', { class: 'btn ghost', type: 'button', onclick: () => { setMode('admin'); location.hash = '#/admin/process'; } }, '관리자 모드'));
}

function publicNotice() {
  return (root) => {
    root.append(h('section', { class: 'gate paper' },
      h('h1', {}, '이 공개 배포본에는 관리자(발표) 화면이 없어요'),
      h('p', {}, '개발 과정과 프롬프트 기록은 만든 사람의 발표 자료라서 공개 사이트에서는 뺐어요. 학생 화면은 모두 그대로 쓸 수 있어요.'),
      h('div', { class: 'row' }, h('button', { class: 'btn primary', type: 'button', onclick: toStudent }, '학생 화면으로'))));
    root.querySelector('.btn.primary').focus();
  };
}

function adminGate(path) {
  return (root) => {
    root.append(h('section', { class: 'gate paper' },
      h('h1', {}, '관리자 모드에서 볼 수 있는 화면이에요'),
      h('p', {}, '이 화면은 발표용 개발 기록이에요. 관리자 모드는 화면을 나누는 기능이고, 비밀번호로 보호하는 기능은 아니에요.'),
      h('div', { class: 'row' },
        h('button', { class: 'btn primary', type: 'button', onclick: () => { setMode('admin'); route(); } }, '관리자 모드로 전환'),
        h('button', { class: 'btn', type: 'button', onclick: toStudent }, '학생 화면으로'))));
    root.querySelector('.btn.primary').focus();
    void path;
  };
}

function route() {
  const path = (location.hash || '#/journey').slice(1);
  if (!ROUTES[path]) { location.replace('#/journey'); return; }
  unmount?.();
  main.replaceChildren();
  document.body.dataset.page = path.split('/').pop();
  const mount = path.startsWith('/admin') ? (PUBLIC ? publicNotice() : mode !== 'admin' ? adminGate(path) : ROUTES[path]) : ROUTES[path];
  unmount = mount(main) || null;
  if (!path.startsWith('/admin')) lastStudentRoute = `#${path}`;
  document.title = `${TITLES[path]} · 책공방`;
  renderChrome();
  window.scrollTo(0, 0);
  // Move focus to the new page's heading so keyboard and screen-reader users land on the content.
  const heading = main.querySelector('h1');
  if (heading && !main.contains(document.activeElement)) { heading.tabIndex = -1; heading.focus({ preventScroll: true }); }
}

async function boot() {
  document.body.dataset.mode = mode;
  $('#app').append(
    h('header', { class: 'site-head' },
      h('a', { class: 'brand', href: '#/journey' }, h('span', { class: 'brand-mark', 'aria-hidden': 'true' }), '책공방'),
      h('span', { class: 'build-date' }, `업데이트 ${__BUILD_DATE__}`),
      nav, modeBadge, headBack, saveState),
    main, footer);

  const saver = autosaver(getProject, (status, msg) => {
    saveState.dataset.status = status;
    saveState.textContent = status === 'saving' ? '저장 중…'
      : status === 'saved' ? `자동 저장됨 ${new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`
        : '저장 실패';
    if (status === 'error') toast(msg, 'error');
  });

  let saved;
  try {
    saved = await loadProject();
    if (saved) replaceProject(validateProject(saved));
  } catch (e) {
    // Never let autosave overwrite a record we could not read: park it first, then offer it as a file.
    if (saved) {
      await parkRecovery(saved).catch(() => {});
      modal({
        title: '저장된 책을 열지 못했어요',
        body: [h('p', {}, `${e.message}`), h('p', {}, '원래 데이터는 지우지 않고 따로 보관했어요. 파일로 내려받아 두세요. 글이 너무 길어서 열리지 않는 경우라면, 선생님과 함께 파일에서 글을 조금 줄인 뒤 「JSON 불러오기」로 다시 열 수 있어요. 지금은 새 책으로 시작해요.')],
        actions: [{ label: '원래 데이터 내려받기', value: 'dl', primary: true }, { label: '닫기', value: 'close' }],
      }).then((r) => { if (r === 'dl') download('책공방_복구용.json', JSON.stringify(saved)); });
    } else {
      toast(`저장소를 열지 못했어요: ${e.message}`, 'error');
    }
  }
  subscribe((kind) => { if (kind !== 'focus') saver.schedule(); });
  // Save as early as possible when the page may go away; warn if a save is still pending or failed.
  addEventListener('pagehide', () => saver.flush());
  document.addEventListener('visibilitychange', () => { if (document.hidden) saver.flush(); });
  document.addEventListener('change', () => saver.flush());
  addEventListener('beforeunload', (e) => { if (saver.pending() || saveState.dataset.status === 'error') e.preventDefault(); });
  addEventListener('hashchange', route);
  // Ctrl+P etc.: print only the book (student) or the slides (admin), never the app chrome.
  addEventListener('beforeprint', () => {
    if (document.body.dataset.print) return;
    if (mode === 'admin' && location.hash.startsWith('#/admin')) prepareDeckPrint();
    else prepareBookPrint();
  });
  addEventListener('afterprint', () => { delete document.body.dataset.print; $('#print-root').replaceChildren(); });
  route();
}

boot();
