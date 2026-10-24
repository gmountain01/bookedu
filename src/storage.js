// IndexedDB persistence for the one BookProject. Success is reported only after the transaction completes.
const DB = 'publishing-lab';
const STORE = 'projects';
const KEY = 'current';

function open() {
  return new Promise((resolve, reject) => {
    if (!('indexedDB' in window)) return reject(new Error('이 브라우저는 저장소(IndexedDB)를 지원하지 않아요.'));
    const req = indexedDB.open(DB, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

let dbPromise;
const db = () => (dbPromise ??= open());

function tx(mode, fn) {
  return db().then((d) => new Promise((resolve, reject) => {
    const t = d.transaction(STORE, mode);
    const result = fn(t.objectStore(STORE));
    t.oncomplete = () => resolve(result.result);
    t.onerror = t.onabort = () => reject(t.error || new Error('저장 작업이 취소됐어요.'));
  }));
}

export const loadProject = () => tx('readonly', (s) => s.get(KEY));
export const saveProject = (p) => tx('readwrite', (s) => s.put(structuredClone(p), KEY));
// A saved record that fails validation is parked here before anything can overwrite it.
export const parkRecovery = (raw) => tx('readwrite', (s) => s.put(raw, 'recovery'));

// Debounced autosave with a status callback: 'saving' | 'saved' | 'error'.
export function autosaver(getProject, onStatus, delay = 700) {
  let timer;
  let pending = false;
  const run = async () => {
    pending = false;
    onStatus('saving');
    try {
      await saveProject(getProject());
      onStatus('saved');
    } catch (e) {
      onStatus('error', friendly(e));
    }
  };
  return {
    schedule() { pending = true; clearTimeout(timer); timer = setTimeout(run, delay); },
    pending: () => pending,
    flush() { if (pending) { clearTimeout(timer); return run(); } return Promise.resolve(); },
  };
}

function friendly(e) {
  if (e?.name === 'QuotaExceededError') return '브라우저 저장 공간이 부족해요. 큰 이미지를 지우거나 JSON으로 백업하세요.';
  if (e?.name === 'SecurityError' || e?.name === 'InvalidStateError') return '이 브라우저 설정(시크릿 창 등)에서는 저장할 수 없어요. JSON으로 백업하세요.';
  return `저장하지 못했어요(${e?.message || e}). JSON으로 백업하세요.`;
}
