// BookProject state: one object, explicit update functions, subscribers.
export const SCHEMA_VERSION = 1;

export const LIMITS = {
  chars: 20000, blocks: 100, images: 8, tables: 5, rows: 10, cols: 6,
  imageBytes: 5 * 1024 * 1024, imageEdge: 1600, backupBytes: 20 * 1024 * 1024,
  // Stored images together stay under this so a JSON backup (base64) always fits the 20 MB import cap.
  totalImageChars: 12 * 1024 * 1024,
  title: 80, short: 200, long: 2000,
};

export const HEADING_NAMES = { 1: '장', 2: '절', 3: '중제목', 4: '소제목' };
export const PAGE_SIZES = { A5: { w: 148, h: 210, label: 'A5 (148×210mm)' }, B6: { w: 128, h: 182, label: 'B6 (128×182mm)' } };
export const THEMES = {
  classic: { label: '문학·에세이', desc: '차분한 명조 본문과 넉넉한 여백. 장마다 새 쪽에서 시작해요.' },
  modern: { label: '정보·학습', desc: '고딕 본문, 문단 사이 여백, 표지 색 제목 띠로 정보가 잘 나뉘어요.' },
  warm: { label: '사진·기록', desc: '그림을 크게, 캡션은 선 아래에. 좁은 여백으로 그림이 주인공이에요.' },
};
export const FONTS = { myeongjo: '명조 (책공방 명조)', gothic: '고딕 (책공방 고딕)' }; // both embedded (src/fonts)
export const MARGINS = { 12: '좁게 12mm', 18: '보통 18mm', 24: '넓게 24mm' };
export const FONT_SIZES = [9, 10, 11, 12];
export const GENRES = ['소설', '수필', '정보서', '시집', '그림책', '기타'];

export const uid = (p = 'b') => `${p}${Date.now().toString(36)}${Math.random().toString(36).slice(2, 7)}`;

export function blankProject() {
  const now = new Date().toISOString();
  return {
    schemaVersion: SCHEMA_VERSION, id: uid('p'), createdAt: now, updatedAt: now,
    meta: { title: '', authorAlias: '', genre: '', topic: '', targetReader: '' },
    blocks: [],
    layout: { pageSize: 'A5', theme: '', fontFamily: 'myeongjo', fontSize: 10, lineHeight: 1.7, margin: 18 },
    assets: [],
    imagePrompt: '',
    frontMatter: { titlePage: '', copyrightText: '', preface: '' },
    // W-034: layout '' = automatic (panel with a picture, typographic without); focus = crop point (%); textY/textAlign/ink = title place on a full-bleed picture
    // W-035: copy = a short line on the front (not the subtitle); backHeadline = the emphasised sentence on the back
    cover: { backgroundColor: '#1d4fb8', imageId: '', backText: '', layout: '', focusX: 50, focusY: 50, textY: 0.08, textAlign: 'left', ink: '', accentColor: '', copy: '', backHeadline: '' },
    reflection: { designReason: '' },
    progress: { currentStep: 1, tocReviewed: false },
  };
}

// ---- store ----
let project = blankProject();
const listeners = new Set();
export const getProject = () => project;
export function subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); }
function emit(kind) { project.updatedAt = new Date().toISOString(); listeners.forEach((fn) => fn(kind)); }

export function replaceProject(next) { project = next; emit('replace'); }
export function setField(path, value) {
  const keys = path.split('.');
  let o = project;
  for (const k of keys.slice(0, -1)) o = o[k];
  o[keys.at(-1)] = value;
  emit(path.startsWith('progress.currentStep') ? 'step' : 'field');
}

// ---- blocks ----
export const totalChars = (p = project) =>
  p.blocks.reduce((n, b) => n + (b.text?.length || 0) + (b.caption?.length || 0)
    + (b.rows ? b.rows.flat().join('').length : 0), 0);

export function canAdd(type, p = project, chars = 0) {
  if (p.blocks.length >= LIMITS.blocks) return `블록은 최대 ${LIMITS.blocks}개까지 만들 수 있어요.`;
  if (totalChars(p) + chars > LIMITS.chars) return `원고가 ${LIMITS.chars.toLocaleString()}자에 가까워서 더 넣을 수 없어요. 다른 글을 줄여 주세요.`;
  if (type === 'table' && p.blocks.filter((b) => b.type === 'table').length >= LIMITS.tables)
    return `표는 최대 ${LIMITS.tables}개까지 넣을 수 있어요.`;
  return '';
}

export function addBlock(block, afterId) {
  const b = { id: uid(), ...block };
  const i = afterId ? project.blocks.findIndex((x) => x.id === afterId) : -1;
  project.blocks.splice(i < 0 ? project.blocks.length : i + 1, 0, b);
  emit('blocks');
  return b;
}
export const lastEdit = { id: '', at: 0 };
// Clicking into a block also moves the preview there (no data change, so nothing is saved).
export function touchBlock(id) { lastEdit.id = id; lastEdit.at = Date.now(); listeners.forEach((fn) => fn('focus')); }
export function updateBlock(id, patch, structural = false) {
  const b = project.blocks.find((x) => x.id === id);
  if (!b) return;
  Object.assign(b, patch);
  lastEdit.id = id;
  lastEdit.at = Date.now();
  emit(structural ? 'blocks' : 'field');
}
export function removeBlock(id) { project.blocks = project.blocks.filter((b) => b.id !== id); emit('blocks'); }
export function moveBlock(id, dir) {
  const i = project.blocks.findIndex((b) => b.id === id);
  const j = i + dir;
  if (i < 0 || j < 0 || j >= project.blocks.length) return;
  [project.blocks[i], project.blocks[j]] = [project.blocks[j], project.blocks[i]];
  emit('blocks');
}

// ---- assets ----
export function addAsset(asset) { const a = { id: uid('a'), ...asset }; project.assets.push(a); emit('assets'); return a; }
export function updateAsset(id, patch) { Object.assign(project.assets.find((a) => a.id === id) || {}, patch); emit('field'); }
export function removeAsset(id) {
  project.assets = project.assets.filter((a) => a.id !== id);
  project.blocks = project.blocks.filter((b) => !(b.type === 'image' && b.assetId === id));
  if (project.cover.imageId === id) project.cover.imageId = '';
  emit('assets');
}

// ---- derived ----
export const headings = (p = project) => p.blocks.filter((b) => b.type === 'heading' && b.text?.trim());

export function stepDone(n, p = project) {
  const filled = (s) => !!String(s || '').trim();
  const imgs = p.blocks.filter((b) => b.type === 'image');
  switch (n) {
    case 1: return ['title', 'genre', 'topic', 'targetReader'].every((k) => filled(p.meta[k]));
    case 2: return headings(p).length > 0 && p.blocks.some((b) => b.type === 'paragraph' && filled(b.text));
    case 3: return !!THEMES[p.layout.theme];
    case 4: return p.assets.length > 0 && p.assets.every((a) => filled(a.sourceNote));
    case 5: return (imgs.length > 0 || p.blocks.some((b) => b.type === 'table'))
      && imgs.every((b) => filled(b.caption) && filled(b.alt));
    case 6: return filled(p.frontMatter.copyrightText) && filled(p.frontMatter.preface);
    case 7: return headings(p).length > 0 && p.progress.tocReviewed;
    case 8: return filled(p.cover.backText) && filled(p.reflection.designReason);
    default: return false;
  }
}
export const progressCount = (p = project) => [1, 2, 3, 4, 5, 6, 7, 8].filter((n) => stepDone(n, p)).length;
export const hasWork = (p = project) =>
  p.blocks.length > 0 || p.assets.length > 0
  || [...Object.values(p.meta), ...Object.values(p.frontMatter), p.cover.backText, p.reflection.designReason, p.imagePrompt]
    .some((v) => String(v || '').trim());
export const imageChars = (p = project) => p.assets.reduce((n, a) => n + (a.data?.length || 0), 0);

// ---- validation for imported JSON (runs on a temporary object; never touches the live project) ----
const isStr = (v, max) => typeof v === 'string' && v.length <= max;
const DATA_URL = /^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/;
const BUILTIN = /^builtin:(alley|tree|night|books|chart|photo-alley|photo-pots|photo-tree|photo-window|photo-sea|cover-walk|cover-window|cover-horizon|cover-tree)$/; // keep in sync with images.js BUILTINS + BODY_PHOTOS + COVER_IMAGES
const COLOR = /^#[0-9a-fA-F]{6}$/;
const num = (v, lo, hi, d) => (typeof v === 'number' && v >= lo && v <= hi ? v : d);

export function validateProject(p) {
  const err = (m) => { throw new Error(m); };
  if (!p || typeof p !== 'object') err('JSON 파일 안에 책 정보가 없어요.');
  if (p.schemaVersion !== SCHEMA_VERSION) err(`지원하지 않는 버전이에요(파일 버전: ${p.schemaVersion ?? '없음'}, 앱 버전: ${SCHEMA_VERSION}).`);
  const base = blankProject();
  const out = { ...base, id: isStr(p.id, 60) ? p.id : base.id, createdAt: isStr(p.createdAt, 40) ? p.createdAt : base.createdAt };

  for (const k of Object.keys(base.meta)) {
    const v = p.meta?.[k] ?? '';
    if (!isStr(v, k === 'title' ? LIMITS.title : LIMITS.short)) err(`기획 정보(${k})의 형식이나 길이가 맞지 않아요.`);
    out.meta[k] = v;
  }
  if (!Array.isArray(p.blocks) || p.blocks.length > LIMITS.blocks) err(`블록 목록이 없거나 ${LIMITS.blocks}개를 넘어요.`);
  if (!Array.isArray(p.assets) || p.assets.length > LIMITS.images) err(`이미지가 ${LIMITS.images}개를 넘어요.`);

  out.assets = p.assets.map((a, i) => {
    if (!isStr(a?.id, 60)) err(`${i + 1}번째 이미지의 id가 올바르지 않아요.`);
    const builtin = BUILTIN.test(a.builtin || '');
    if (!builtin && !(typeof a.data === 'string' && DATA_URL.test(a.data))) err(`${i + 1}번째 이미지는 PNG/JPEG/WebP 형식이 아니에요.`);
    if (!builtin && a.data.length > LIMITS.backupBytes) err(`${i + 1}번째 이미지가 너무 커요.`);
    return {
      id: a.id, ...(builtin ? { builtin: a.builtin } : { data: a.data }),
      mimeType: isStr(a.mimeType, 20) ? a.mimeType : '', width: +a.width || 0, height: +a.height || 0,
      name: isStr(a.name, LIMITS.short) ? a.name : '', sourceNote: isStr(a.sourceNote, LIMITS.short) ? a.sourceNote : '',
    };
  });
  const assetIds = new Set(out.assets.map((a) => a.id));
  if (assetIds.size !== out.assets.length) err('이미지 id가 겹쳐요. 책공방에서 내보낸 파일인지 확인해 주세요.');
  const seen = new Set();

  out.blocks = p.blocks.map((b, i) => {
    const at = `${i + 1}번째 블록`;
    if (!isStr(b?.id, 60)) err(`${at}의 id가 올바르지 않아요.`);
    if (b.type === 'heading') {
      if (![1, 2, 3, 4].includes(b.level) || !isStr(b.text, LIMITS.title * 2)) err(`${at}(제목)의 단계나 길이가 맞지 않아요.`);
      return { id: b.id, type: 'heading', level: b.level, text: b.text };
    }
    if (b.type === 'paragraph') {
      if (!isStr(b.text, LIMITS.chars)) err(`${at}(문단)의 길이가 맞지 않아요.`);
      return { id: b.id, type: 'paragraph', text: b.text, ...(b.style === 'quote' ? { style: 'quote' } : {}) };
    }
    if (b.type === 'image') {
      if (!assetIds.has(b.assetId)) err(`${at}(그림)이 없는 이미지를 가리켜요.`);
      return { id: b.id, type: 'image', assetId: b.assetId, caption: isStr(b.caption, LIMITS.short) ? b.caption : '', alt: isStr(b.alt, LIMITS.short) ? b.alt : '' };
    }
    if (b.type === 'table') {
      const ok = Array.isArray(b.rows) && b.rows.length >= 1 && b.rows.length <= LIMITS.rows
        && b.rows.every((r) => Array.isArray(r) && r.length === b.rows[0].length && r.length <= LIMITS.cols && r.every((c) => isStr(c, LIMITS.short)));
      if (!ok) err(`${at}(표)의 크기는 최대 ${LIMITS.rows}행 ${LIMITS.cols}열이고, 각 행의 칸 수가 같아야 해요.`);
      return { id: b.id, type: 'table', rows: b.rows.map((r) => [...r]), caption: isStr(b.caption, LIMITS.short) ? b.caption : '' };
    }
    return err(`${at}의 종류(${String(b.type).slice(0, 20)})를 알 수 없어요.`);
  });
  // A repeated block id would make later edits land in the wrong block: give repeats a fresh id.
  for (const b of out.blocks) { if (seen.has(b.id)) b.id = uid(); seen.add(b.id); }
  if (out.blocks.filter((b) => b.type === 'table').length > LIMITS.tables) err(`표가 ${LIMITS.tables}개를 넘어요.`);
  if (totalChars(out) > LIMITS.chars) err(`원고가 ${LIMITS.chars.toLocaleString()}자를 넘어요.`);

  const L = p.layout || {};
  out.layout = {
    pageSize: PAGE_SIZES[L.pageSize] ? L.pageSize : 'A5',
    theme: THEMES[L.theme] ? L.theme : '',
    fontFamily: FONTS[L.fontFamily] ? L.fontFamily : 'myeongjo',
    fontSize: FONT_SIZES.includes(L.fontSize) ? L.fontSize : 10,
    lineHeight: typeof L.lineHeight === 'number' && L.lineHeight >= 1.2 && L.lineHeight <= 2.2 ? L.lineHeight : 1.7,
    margin: MARGINS[L.margin] ? +L.margin : 18,
  };
  out.imagePrompt = isStr(p.imagePrompt ?? '', LIMITS.long) ? p.imagePrompt ?? '' : '';
  for (const k of Object.keys(base.frontMatter)) {
    const v = p.frontMatter?.[k] ?? '';
    if (!isStr(v, LIMITS.long)) err(`앞부속(${k})의 형식이나 길이가 맞지 않아요.`);
    out.frontMatter[k] = v;
  }
  const C = p.cover || {};
  out.cover = {
    backgroundColor: COLOR.test(C.backgroundColor || '') ? C.backgroundColor : base.cover.backgroundColor,
    imageId: assetIds.has(C.imageId) ? C.imageId : '',
    backText: isStr(C.backText ?? '', LIMITS.long) ? C.backText ?? '' : '',
    // W-034 fields; files saved before them get the defaults (their picture and colour are kept)
    layout: ['full', 'band', 'panel', 'type'].includes(C.layout) ? C.layout : '',
    focusX: num(C.focusX, 0, 100, 50), focusY: num(C.focusY, 0, 100, 50),
    textY: num(C.textY, 0, 0.9, 0.08),
    textAlign: ['left', 'center', 'right'].includes(C.textAlign) ? C.textAlign : 'left',
    ink: COLOR.test(C.ink || '') ? C.ink : '',
    accentColor: COLOR.test(C.accentColor || '') ? C.accentColor : '',
    copy: isStr(C.copy ?? '', LIMITS.short) ? C.copy ?? '' : '',
    backHeadline: isStr(C.backHeadline ?? '', LIMITS.short) ? C.backHeadline ?? '' : '',
  };
  out.reflection = { designReason: isStr(p.reflection?.designReason ?? '', LIMITS.long) ? p.reflection?.designReason ?? '' : '' };
  const step = p.progress?.currentStep;
  out.progress = { currentStep: Number.isInteger(step) && step >= 1 && step <= 8 ? step : 1, tocReviewed: !!p.progress?.tocReviewed };
  out.updatedAt = new Date().toISOString();
  return out;
}
