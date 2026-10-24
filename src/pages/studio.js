import { h, toast, modal, download, $ } from '../dom.js';
import edu from '../data/education.json';
import {
  getProject, setField, subscribe, replaceProject, validateProject, stepDone, progressCount, headings,
  addAsset, updateAsset, removeAsset, updateBlock,
  GENRES, PAGE_SIZES, THEMES, FONTS, MARGINS, FONT_SIZES, HEADING_NAMES, LIMITS,
} from '../state.js';
import { BODY_PHOTOS, COVER_IMAGES, readImageFile, assetSrc } from '../images.js';
import { blockEditor, guard } from './blocks.js';
import { preview } from './preview.js';
import { paginate, PX_PER_MM } from './pages.js';
import { bookReader } from './reader.js';
import { bookSequence, bodyNodes, coverNodes, coverLayout, titleTooLong, bookVars, applyVars, geometry, FONT_STACKS, DESIGN_DEFAULTS } from '../book.js';
import { startSample, startBlank, confirmReplace } from './journey.js';
import { artImg } from '../art.js';

const STEP_NAMES = ['기획', '원고', '조판', '이미지 준비', '본문 배치', '앞부속', '목차', '표지와 완성'];

// "편집장의 미션": the required items mirror stepDone(); '도전' items are optional extras.
const filled = (v) => !!String(v || '').trim();
const MISSIONS = {
  1: [['책 제목 정하기', (p) => filled(p.meta.title)], ['장르 고르기', (p) => filled(p.meta.genre)], ['전하고 싶은 주제 쓰기', (p) => filled(p.meta.topic)], ['읽을 사람(독자) 정하기', (p) => filled(p.meta.targetReader)]],
  2: [['장·절 같은 제목 1개 이상 쓰기', (p) => headings(p).length > 0], ['문단 1개 이상 쓰기', (p) => p.blocks.some((b) => b.type === 'paragraph' && filled(b.text))],
    ['도전: 장 아래에 절을 넣어 단계 나누기', (p) => headings(p).some((b) => b.level >= 2), true]],
  3: [['책 디자인 고르기', (p) => !!THEMES[p.layout.theme]], ['도전: 판형을 바꿔 미리보기 쪽수가 어떻게 바뀌는지 보기', (p) => p.layout.pageSize !== 'A5', true]],
  4: [['그림 1개 이상 준비하기', (p) => p.assets.length > 0], ['모든 그림에 출처와 이용 조건 적기', (p) => p.assets.length > 0 && p.assets.every((a) => filled(a.sourceNote))],
    ['도전: AI 그림 프롬프트 써 보기', (p) => filled(p.imagePrompt), true]],
  5: [['본문에 그림이나 표 넣기', (p) => p.blocks.some((b) => b.type === 'image' || b.type === 'table')],
    ['그림마다 캡션 달기', (p) => p.blocks.filter((b) => b.type === 'image').every((b) => filled(b.caption))],
    ['그림마다 대체 텍스트 쓰기', (p) => p.blocks.filter((b) => b.type === 'image').every((b) => filled(b.alt))]],
  6: [['판권지 쓰기', (p) => filled(p.frontMatter.copyrightText)], ['머리말 쓰기', (p) => filled(p.frontMatter.preface)], ['도전: 표제지 부제 붙이기', (p) => filled(p.frontMatter.titlePage), true]],
  7: [['제목이 1개 이상 있기 (2단계)', (p) => headings(p).length > 0], ['목차를 읽고 확인했다고 체크하기', (p) => p.progress.tocReviewed]],
  8: [['뒤표지 소개 글 쓰기', (p) => filled(p.cover.backText)], ['디자인을 고른 이유 한 문장 쓰기', (p) => filled(p.reflection.designReason)], ['도전: 표지 그림과 배치 고르기', (p) => filled(p.cover.imageId) && !!p.cover.layout, true]],
};
function missionList(n) {
  const p = getProject();
  return MISSIONS[n].map(([label, ok, extra]) => {
    const done = ok(p);
    return h('li', { 'data-done': String(done), class: extra ? 'extra' : '' }, h('span', { class: 'm-box', 'aria-hidden': 'true' }, done ? '✓' : ''), h('span', {}, label), h('span', { class: 'sr' }, done ? ' (완료)' : ' (아직)'));
  });
}

// ---------- backup ----------
export function exportJson() {
  const p = getProject();
  const name = (p.meta.title || '내 책').replace(/[\\/:*?"<>|]/g, '').slice(0, 40);
  const text = JSON.stringify(p);
  download(`${name}_책공방.json`, text);
  if (text.length > LIMITS.backupBytes) toast('백업 파일이 20MB를 넘어서 다시 불러올 수 없어요. 큰 그림을 빼고 다시 백업하세요.', 'error');
  else toast('JSON 백업 파일을 내려받았어요.');
}

async function importJson(file) {
  if (!file) return;
  if (file.size > LIMITS.backupBytes) return toast(`백업 파일이 ${(file.size / 1048576).toFixed(1)}MB예요. 20MB 이하만 불러올 수 있어요.`, 'error');
  let next;
  try {
    const parsed = JSON.parse(await file.text());
    next = validateProject(parsed); // temporary object; the live project is untouched on failure
  } catch (e) {
    const msg = e instanceof SyntaxError ? 'JSON 형식이 깨져 있어요. 책공방에서 내보낸 파일인지 확인해 주세요.' : e.message;
    return modal({ title: '불러오지 못했어요', body: h('p', {}, `${msg} 지금 작업은 그대로 남아 있어요.`), actions: [{ label: '확인', value: 'ok', primary: true }] });
  }
  if (!(await confirmReplace('불러온 책'))) return;
  replaceProject(next);
  toast(`「${next.meta.title || '제목 없음'}」을(를) 불러왔어요.`);
}

// ---------- form helpers ----------
const fmGroup = (id, label, ...buttons) => h('div', { role: 'group', 'aria-labelledby': id }, h('p', { class: 'fm-label', id }, label), ...buttons);
const field = (label, control, hint) => h('label', { class: 'field' }, h('span', {}, label), control, hint ? h('small', { class: 'hint' }, hint) : null);
const text = (path, value, props = {}) => h('input', { type: 'text', value: value ?? '', oninput: (e) => setField(path, e.target.value), ...props });
const area = (path, value, props = {}) => h('textarea', { rows: 4, oninput: (e) => setField(path, e.target.value), ...props }, value ?? '');
function radios(name, legend, options, current, onPick) {
  return h('fieldset', { class: 'choices' }, h('legend', {}, legend),
    Object.entries(options).map(([v, label]) => h('label', { class: 'choice' },
      h('input', { type: 'radio', name, value: v, checked: String(current) === v, onchange: () => onPick(v) }),
      typeof label === 'string' ? h('span', {}, label) : h('span', {}, h('b', {}, label.label), h('small', {}, label.desc)))));
}

// ---------- steps ----------
function step1(p) {
  return [
    field('책 제목', text('meta.title', p.meta.title, { maxlength: String(LIMITS.title), placeholder: '예: 골목에서 찾은 이야기' })),
    field('지은이 이름(필명 가능)', text('meta.authorAlias', p.meta.authorAlias, { maxlength: '40', placeholder: '실명 대신 필명을 써도 좋아요' }), '개인정보를 지키기 위해 실명 대신 필명을 권해요.'),
    field('장르', h('select', { onchange: (e) => setField('meta.genre', e.target.value) },
      h('option', { value: '' }, '장르를 고르세요'), GENRES.map((g) => h('option', { value: g, selected: g === p.meta.genre }, g)))),
    field('주제 (무엇을 전하고 싶나요?)', area('meta.topic', p.meta.topic, { rows: 3, maxlength: String(LIMITS.short) })),
    field('독자 (누구에게 전하고 싶나요?)', text('meta.targetReader', p.meta.targetReader, { maxlength: String(LIMITS.short), placeholder: '예: 등굣길이 지루한 중학생' })),
  ];
}

// Step 3 (W-033): pick one of three coherent book designs from small samples of the student's own first page,
// then adjust details. Picking a design sets its defaults; if the student had changed them, say so and offer undo.
const DETAIL_KEYS = { fontFamily: '본문 서체', fontSize: '글자 크기', lineHeight: '줄 간격', margin: '여백' };
const detailText = (k, v) => (k === 'fontFamily' ? FONTS[v] : k === 'fontSize' ? `${v}pt` : k === 'lineHeight' ? `${v}배` : `${v}mm`);
let designSwap = null; // { before: {...} } the student's own settings before the first of a run of design swaps

function designSample(p, theme) {
  const layout = { ...p.layout, ...DESIGN_DEFAULTS[theme], theme };
  const first = p.blocks.find((b) => b.type === 'heading' && b.level === 1) || { id: 'x', type: 'heading', level: 1, text: '1장 첫 장의 제목' };
  const text = p.blocks.find((b) => b.type === 'paragraph' && (b.text || '').trim()) || { id: 'y', type: 'paragraph', text: '여기에 내 원고의 첫 문단이 이 디자인으로 보여요. 글꼴, 줄 간격, 여백이 함께 바뀌어요.' };
  const sample = { ...p, layout, blocks: [first, text, ...p.blocks.filter((b) => b.type === 'image').slice(0, 1)] };
  const page = h('div', { class: 'book dz-page', 'data-theme': theme, 'aria-hidden': 'true' }, h('div', { class: 'bk-body' }, bodyNodes(sample, `dz-${theme}`)));
  applyVars(page, bookVars(sample));
  return page;
}

function step3(p, rerender) {
  const L = p.layout;
  const pick = (theme) => {
    const cur = getProject().layout;
    const prev = DESIGN_DEFAULTS[cur.theme];
    // keep the first snapshot across successive swaps (arrow keys move through all three designs, MT-15)
    if (!designSwap && prev) {
      const own = Object.keys(DETAIL_KEYS).filter((k) => cur[k] !== prev[k]);
      if (own.length) designSwap = { before: Object.fromEntries(own.map((k) => [k, cur[k]])) };
    }
    for (const [k, v] of Object.entries(DESIGN_DEFAULTS[theme])) setField(`layout.${k}`, v);
    setField('layout.theme', theme);
    rerender();
    document.querySelector(`.dz-choice input[value="${theme}"]`)?.focus({ preventScroll: true });
    (document.querySelector('.dz-notice') || document.querySelector(`.dz-choice input[value="${theme}"]`))?.closest('.dz-notice, .dz-choice')?.scrollIntoView({ block: 'nearest' });
  };
  const swap = designSwap;
  const changed = swap ? Object.keys(swap.before).filter((k) => swap.before[k] !== L[k]) : [];
  const notice = changed.length ? h('div', { class: 'dz-notice', role: 'status' },
    h('p', {}, `「${THEMES[L.theme].label}」 디자인의 기본값으로 바뀌었어요: `,
      changed.map((k, i) => [i ? ', ' : '', `${DETAIL_KEYS[k]} ${detailText(k, swap.before[k])} → ${detailText(k, L[k])}`]), '.'),
    h('button', { class: 'btn sm', type: 'button', onclick: () => { for (const k of changed) setField(`layout.${k}`, swap.before[k]); designSwap = null; rerender(); document.querySelector('.dz-choice input:checked')?.focus(); } }, '직접 고친 설정 되살리기'),
    h('button', { class: 'btn sm', type: 'button', onclick: () => { designSwap = null; rerender(); document.querySelector('.dz-choice input:checked')?.focus(); } }, '이대로 두기')) : null;
  return [
    h('fieldset', { class: 'choices dz' }, h('legend', {}, '책 디자인'),
      h('p', { class: 'hint' }, '서체, 글자 크기, 줄 간격, 여백, 제목 모양, 강조색(표지 색)이 함께 정해져요. 견본은 내 원고의 첫 쪽이에요. 원고 내용과 제목 구조는 바뀌지 않아요.'),
      notice,
      h('div', { class: 'dz-grid' }, Object.entries(THEMES).map(([v, t]) => h('label', { class: 'choice dz-choice' },
        h('input', { type: 'radio', name: 'theme', value: v, checked: L.theme === v, onchange: () => pick(v) }),
        designSample(p, v),
        h('span', { class: 'dz-txt' }, h('b', {}, t.label), h('small', {}, t.desc)))))),
    h('section', { class: 'dz-detail', 'aria-labelledby': 'dz-detail-h' },
      h('h3', { id: 'dz-detail-h' }, '세부 설정'),
      h('p', { class: 'hint' }, '디자인을 고른 뒤 필요할 때만 바꿔요. 다른 디자인을 고르면 서체·글자 크기·줄 간격·여백이 그 디자인의 기본값으로 바뀌어요.'),
      radios('pageSize', '판형 (책의 크기)', Object.fromEntries(Object.entries(PAGE_SIZES).map(([k, v]) => [k, v.label])), L.pageSize, (v) => setField('layout.pageSize', v)),
      radios('font', '본문 서체', FONTS, L.fontFamily, (v) => { designSwap = null; setField('layout.fontFamily', v); }),
      field('글자 크기 (인쇄했을 때의 크기)', h('select', { onchange: (e) => { designSwap = null; setField('layout.fontSize', +e.target.value); } },
        FONT_SIZES.map((sz) => h('option', { value: String(sz), selected: sz === L.fontSize }, `${sz}pt`))), '미리보기의 「화면 배율」은 화면에서 보는 크기만 바꿔요. 책의 글자 크기는 여기서 정해요.'),
      radios('margin', '여백', MARGINS, L.margin, (v) => { designSwap = null; setField('layout.margin', +v); }),
      field('줄 간격', h('input', { type: 'range', min: '1.4', max: '2', step: '0.05', value: String(L.lineHeight), 'aria-valuetext': `${L.lineHeight}배`, oninput: (e) => { e.target.setAttribute('aria-valuetext', `${e.target.value}배`); e.target.nextElementSibling.textContent = `${e.target.value}배`; designSwap = null; setField('layout.lineHeight', +e.target.value); } }),
        `${L.lineHeight}배`)),
  ];
}

function step4(p, rerender) {
  const lib = h('ul', { class: 'library' }, p.assets.map((a) => h('li', { class: 'asset' },
    h('img', { src: assetSrc(a), alt: '', width: 96, height: 64 }),
    h('div', { class: 'asset-f' },
      h('strong', {}, a.name || '그림'),
      field('출처와 이용 조건', h('input', { type: 'text', value: a.sourceNote || '', maxlength: String(LIMITS.short), placeholder: '예: 내가 직접 찍은 사진 / 공공누리 제1유형', oninput: (e) => updateAsset(a.id, { sourceNote: e.target.value }) })),
      h('button', { class: 'btn sm danger', type: 'button', onclick: async () => {
        const used = getProject().blocks.filter((b) => b.type === 'image' && b.assetId === a.id).length
          + (getProject().cover.imageId === a.id ? 1 : 0);
        if (used) {
          const ok = await modal({
            title: '이 그림을 빼면 함께 사라져요',
            body: h('p', {}, `본문과 표지에서 이 그림을 쓰는 곳 ${used}곳도 캡션·대체 텍스트와 함께 지워져요.`),
            actions: [{ label: '그림과 사용한 곳 모두 빼기', value: 'yes', danger: true }, { label: '취소', value: 'no', primary: true }],
          });
          if (ok !== 'yes') return;
        }
        removeAsset(a.id);
        rerender();
        document.getElementById('library-h')?.focus();
      } }, '목록에서 빼기')))));
  const full = p.assets.length >= LIMITS.images;
  const upload = h('input', {
    type: 'file', accept: 'image/png,image/jpeg,image/webp', multiple: true, disabled: full,
    onchange: async (e) => {
      for (const f of [...e.target.files]) {
        if (getProject().assets.length >= LIMITS.images) { toast(`그림은 최대 ${LIMITS.images}개까지예요.`, 'error'); break; }
        try { addAsset({ ...(await readImageFile(f)), sourceNote: '' }); } catch (err) { toast(err.message, 'error'); }
      }
      rerender();
      document.getElementById('library-h')?.focus();
    },
  });
  const promptBox = area('imagePrompt', p.imagePrompt, { rows: 3, maxlength: String(LIMITS.long), placeholder: '예: 해 질 무렵 좁은 골목길, 노란 불빛 창문, 색연필 그림체' });
  return [
    h('h3', {}, '기본 사진에서 고르기'),
    h('p', { class: 'hint' }, '본문에 넣을 수 있는 사진이에요. 출처와 이용 조건은 자동으로 적혀요. 표지 사진은 8단계에서 따로 골라요.'),
    h('div', { class: 'builtins' }, Object.entries(BODY_PHOTOS).map(([key, b]) => h('button', {
      type: 'button', class: 'builtin', disabled: full, 'data-key': key, title: `${b.name} — ${b.desc}`,
      onclick: () => {
        addAsset({ builtin: key, name: b.name, sourceNote: b.credit, mimeType: 'image/jpeg', width: b.width, height: b.height });
        rerender();
        (document.querySelector(`.builtin[data-key="${key}"]:not(:disabled)`) || document.getElementById('library-h'))?.focus();
      },
    }, // the thumbnail box has a fixed shape; the photo inside keeps its own ratio (width/height = the photo's real size)
    h('span', { class: 'bi-thumb' }, h('img', { src: b.src, alt: '', width: b.width, height: b.height }),
      h('span', { class: 'bi-orient' }, b.width > b.height * 1.15 ? '가로' : b.height > b.width * 1.15 ? '세로' : '정사각')),
    h('b', { class: 'bi-name' }, `+ ${b.name}`),
    h('small', { class: 'bi-desc' }, b.desc.replace(/\s*\((세로|가로|거의 정사각)\)/, ''))))),
    h('h3', {}, '내 그림 올리기'),
    field('PNG · JPEG · WebP, 한 장에 5MB 이하', upload, '큰 그림은 긴 변 1,600px로 줄여서 저장해요. 그림은 이 브라우저에만 저장돼요.'),
    h('h3', { id: 'library-h', tabindex: '-1' }, `준비한 그림 (${p.assets.length}/${LIMITS.images})`),
    p.assets.length ? lib : h('p', { class: 'empty' }, '아직 준비한 그림이 없어요.'),
    h('h3', {}, 'AI 그림 프롬프트 써 보기'),
    field('그림 프롬프트', promptBox, '이 앱은 그림을 직접 만들지 않아요. 프롬프트를 써서 복사해 두었다가, 학교에서 허락한 도구에서 사용해 보세요.'),
    h('button', { class: 'btn sm', type: 'button', onclick: async () => {
      try { await navigator.clipboard.writeText(promptBox.value); toast('프롬프트를 복사했어요.'); } catch { promptBox.select(); toast('자동 복사가 막혀 있어요. 선택된 글자를 Ctrl+C로 복사하세요.', 'error'); }
    } }, '프롬프트 복사'),
  ];
}

function step6(p) {
  const fm = p.frontMatter;
  const cr = area('frontMatter.copyrightText', fm.copyrightText, { rows: 6, maxlength: String(LIMITS.long) });
  return [
    field('표제지 부제 (표제지에 제목과 함께 들어가요)', text('frontMatter.titlePage', fm.titlePage, { maxlength: String(LIMITS.short) })),
    field('판권지(판권면)', cr, '책 이름, 지은이, 펴낸 곳 같은 책의 정보를 적어요. ISBN은 출판사가 발급받는 번호라서 여기서는 비워 두거나 "발급받지 않음"이라고 써요.'),
    h('button', { class: 'btn sm', type: 'button', onclick: () => {
      cr.value = `${p.meta.title || '책 제목'}\n지은이 ${p.meta.authorAlias || '필명'}\n펴낸 곳 ○○중학교 책공방(교육용)\n\n이 책은 수업에서 만든 교육용 책입니다.\nISBN은 발급받지 않았습니다.`;
      setField('frontMatter.copyrightText', cr.value);
    } }, '판권지 예시 채우기'),
    field('머리말 (책을 펴내며)', area('frontMatter.preface', fm.preface, { rows: 5, maxlength: String(LIMITS.long) })),
  ];
}

function step7(p, rerender) {
  const hs = headings(p);
  return [
    h('p', {}, '목차는 2단계에서 쓴 장·절 제목으로 자동으로 만들어져요. 여기서 제목을 고치면 목차도 바로 바뀌어요.'),
    h('p', { class: 'muted' }, '이 앱의 목차에는 쪽 번호를 넣지 않아요. 실제 책에서는 조판이 끝나 쪽수가 정해진 뒤에 쪽 번호를 확정해요.'),
    hs.length ? h('ol', { class: 'toc-edit' }, hs.map((b) => h('li', { class: `lv${b.level}` },
      h('select', { 'aria-label': `「${b.text}」 제목 단계`, 'data-id': b.id, onchange: (e) => { updateBlock(b.id, { level: +e.target.value }, true); rerender(); document.querySelector(`.toc-edit select[data-id="${b.id}"]`)?.focus(); } },
        [1, 2, 3, 4].map((l) => h('option', { value: String(l), selected: l === b.level }, HEADING_NAMES[l]))),
      h('input', { type: 'text', value: b.text, 'aria-label': '제목', maxlength: String(LIMITS.title * 2), oninput: (e) => updateBlock(b.id, { text: guard(e.target, (b.text || '').length) }) }))))
      : h('p', { class: 'empty' }, '제목이 없어서 목차가 비어 있어요. 2단계에서 장 제목을 추가해 보세요.'),
    h('label', { class: 'check' },
      h('input', { type: 'checkbox', checked: p.progress.tocReviewed, onchange: (e) => setField('progress.tocReviewed', e.target.checked) }),
      h('span', {}, '목차를 읽어 보고, 제목 순서와 단계가 맞는지 확인했어요')),
  ];
}

const SWATCHES = [['#1d4fb8', '파랑'], ['#b3261e', '빨강'], ['#2f6b4f', '초록'], ['#1b2230', '먹색'], ['#e0a400', '노랑'], ['#7a4bb3', '보라'], ['#e6dccf', '모래'], ['#eceee2', '종이']];
const syncSwatches = (row, c) => row.querySelectorAll('.swatch').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.color === c)));

// ---------- step 8: the cover (W-034) ----------
const LAYOUTS = {
  full: { label: '사진 전면형', desc: '그림이 표지 전체를 채우고, 그림이 비워 둔 자리에 제목을 놓아요.' },
  band: { label: '사진·띠 분리형', desc: '위는 그림, 아래는 표지 색 띠에 제목과 지은이를 놓아요. 그림이 복잡해도 글자가 잘 읽혀요.' },
  panel: { label: '제목·그림 나눔형', desc: '위쪽은 표지 색 위의 제목, 아래쪽은 그림 판이에요. 어떤 그림에도 글자가 잘 읽혀요.' },
  type: { label: '글자 중심형', desc: '그림 없이 제목의 크기와 여백으로 만드는 표지예요.' },
};
const TEXT_Y = { top: [0.07, '위'], middle: [0.4, '가운데'], bottom: [0.64, '아래'] };
const COVER_KEYS = ['layout', 'imageId', 'backgroundColor', 'accentColor', 'focusX', 'focusY', 'textY', 'textAlign', 'ink'];
let coverUndo = null; // the cover fields before a built-in photograph re-set them (one step back)
let inkMsg = ''; // result of 「글자색 맞추기」, shown once

const relLum = (r, g, b) => { const f = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
const ratio = (a, b) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
const hexLum = (hex) => relLum(...[1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)));
/**
 * Luminance of the picture where the title block sits on a full-bleed cover (same crop as object-fit: cover with the
 * crop point), as [10th, 90th percentile]. Used to pick a readable ink and to warn about a weak place.
 */
async function zoneLum(asset, cover, size) {
  const img = new Image();
  img.src = assetSrc(asset);
  await img.decode().catch(() => {});
  if (!img.naturalWidth) return null;
  const W = 160; const H = Math.round(W * size.h / size.w);
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d', { willReadFrequently: true });
  const s = Math.max(W / img.naturalWidth, H / img.naturalHeight);
  const dw = img.naturalWidth * s; const dh = img.naturalHeight * s;
  g.drawImage(img, (W - dw) * cover.focusX / 100, (H - dh) * cover.focusY / 100, dw, dh);
  const x0 = cover.textAlign === 'right' ? 0.415 : cover.textAlign === 'center' ? 0.12 : 0.085; // matches .lay-full .cv-head (50% wide, inset 8.5%)
  const box = g.getImageData(Math.round(W * x0), Math.round(H * cover.textY), Math.round(W * (cover.textAlign === 'center' ? 0.76 : 0.5)), Math.round(H * 0.2)).data;
  const L = [];
  for (let i = 0; i < box.length; i += 4) L.push(relLum(box[i], box[i + 1], box[i + 2]));
  L.sort((a, b) => a - b);
  return [L[Math.floor(L.length * 0.1)], L[Math.floor(L.length * 0.9)]];
}

/** How much the back-cover text overflows its space at print size (0 = fits), measured on an off-screen copy. */
function backOverflow(p) {
  const box = h('div', { class: 'book', 'data-theme': p.layout.theme || 'classic', style: 'position:fixed;left:-100000px;top:0;visibility:hidden' }, coverNodes(p).back);
  applyVars(box, bookVars(p));
  box.style.setProperty('--mm', `${96 / 25.4}px`);
  document.body.append(box);
  const body = box.querySelector('.cv-back-body');
  const over = body ? Math.max(0, body.scrollHeight - body.clientHeight) / Math.max(1, body.scrollHeight) : 0;
  box.remove();
  return over;
}

function coverSample(p, layout) {
  const sample = { ...p, cover: { ...p.cover, layout } };
  const box = h('div', { class: 'book cvs-page', 'data-theme': p.layout.theme || 'classic', 'aria-hidden': 'true' }, coverNodes(sample).front);
  applyVars(box, bookVars(sample));
  return box;
}

function step8(p, rerender) {
  const C = p.cover;
  const img = p.assets.find((a) => a.id === C.imageId);
  const layout = coverLayout(p);
  const size = PAGE_SIZES[p.layout.pageSize] || PAGE_SIZES.A5;
  const set = (k, v) => setField(`cover.${k}`, v);
  const refocus = (sel) => document.querySelector(sel)?.focus({ preventScroll: true });

  const pickBuiltin = (key) => {
    const meta = COVER_IMAGES[key];
    if (img?.builtin === key) return; // already the cover photo (MT-18)
    let asset = getProject().assets.find((a) => a.builtin === key);
    let added = null;
    if (!asset) {
      if (getProject().assets.length >= LIMITS.images) return toast(`그림은 ${LIMITS.images}개까지 넣을 수 있어요. 4단계에서 쓰지 않는 그림을 빼 주세요.`, 'error');
      asset = addAsset({ builtin: key, name: meta.name, sourceNote: meta.credit.replace(/^표지 사진: /, ''), mimeType: 'image/jpeg', width: meta.width, height: meta.height });
      added = asset.id;
    }
    const cur = getProject().cover;
    coverUndo = { ...Object.fromEntries(COVER_KEYS.map((k) => [k, cur[k]])), _added: added };
    set('imageId', asset.id); set('layout', meta.layout); set('backgroundColor', meta.paper); set('accentColor', meta.accent);
    set('ink', meta.ink); set('textY', meta.textY ?? 0.07); set('textAlign', meta.textAlign || 'left');
    set('focusX', meta.focusX ?? 50); set('focusY', meta.focusY ?? 50);
    rerender(); refocus(`.cvp-builtin[data-key="${key}"]`);
  };
  const pickOwn = (id) => {
    coverUndo = null;
    set('imageId', id);
    if (id) { set('focusX', 50); set('focusY', 50); if (!getProject().cover.layout || getProject().cover.layout === 'type') set('layout', 'panel'); }
    rerender(); refocus('.cvp-own select');
  };
  const autoInk = async () => {
    const q = await zoneLum(img, getProject().cover, size);
    if (!q) return;
    const dark = '#1b1d22'; const light = '#ffffff';
    const best = ratio(q[0], hexLum(dark)) >= ratio(q[1], hexLum(light)) ? dark : light;
    inkMsg = `${best === getProject().cover.ink ? '지금 글자색이 이 자리에서 가장 잘 보여요' : '이 자리에 더 잘 보이는 글자색으로 바꿨어요'} (어두운 곳·밝은 곳 대비 약 ${Math.min(ratio(q[0], hexLum(best)), ratio(q[1], hexLum(best))).toFixed(1)}:1).`;
    set('ink', best); rerender(); refocus('.cvp-ink');
  };

  const notice = coverUndo ? h('div', { class: 'dz-notice', role: 'status' },
    h('p', {}, '표지 색, 강조색, 배치, 제목 자리를 이 사진에 맞췄어요. 원고와 내가 올린 그림은 그대로예요.'),
    h('button', { class: 'btn sm', type: 'button', onclick: () => {
      const { _added, ...back } = coverUndo;
      for (const [k, v] of Object.entries(back)) set(k, v);
      if (_added && !getProject().blocks.some((b) => b.assetId === _added)) removeAsset(_added);
      coverUndo = null; rerender(); refocus('.cvl-choice input:checked');
    } }, '이전 표지로 되돌리기'),
    h('button', { class: 'btn sm', type: 'button', onclick: () => { coverUndo = null; rerender(); } }, '이대로 두기')) : null;

  const warn = h('p', { class: 'cvp-warn', role: 'status', hidden: true });
  const msg = inkMsg; inkMsg = '';
  const ppi = img && img.width ? Math.round(img.width / (size.w / 25.4)) : 0;
  const notes = [
    img && layout !== 'type' && ppi && ppi < 200 ? `이 그림은 표지 폭에 비해 작아서 인쇄하면 흐릴 수 있어요(약 ${ppi}ppi, 200ppi 이상 권장). 더 큰 그림을 쓰면 선명해요.` : null,
    img && !COVER_IMAGES[img.builtin] && !String(img.sourceNote || '').trim() ? '4단계에서 이 그림의 출처를 적으면 뒤표지에 자동으로 적혀요.' : null,
    C.layout === 'full' && titleTooLong(p) ? '제목이 길어서 이 사진의 빈자리에 다 들어가지 않아요. 그래서 「제목·그림 나눔형」으로 보여 줘요.' : null,
  ].filter(Boolean);
  if (img && layout === 'full') {
    zoneLum(img, C, size).then((q) => {
      if (!q) return;
      const ink = C.ink || '#ffffff';
      const worst = Math.min(ratio(q[0], hexLum(ink)), ratio(q[1], hexLum(ink)));
      if (worst < 3) { warn.hidden = false; warn.textContent = `이 자리에서는 제목이 잘 안 보일 수 있어요(어두운 곳·밝은 곳 대비 약 ${worst.toFixed(1)}:1). 제목 자리나 사진 위치를 바꾸거나 「글자색 맞추기」를 눌러 보세요. 「제목·그림 나눔형」은 어떤 그림에서도 잘 읽혀요.`; }
    });
  }

  const color = h('input', { type: 'color', value: C.backgroundColor, 'aria-label': '표지 색 직접 고르기', oninput: (e) => { set('backgroundColor', e.target.value); syncSwatches(e.target.parentElement, e.target.value); } });
  const own = p.assets.filter((a) => !COVER_IMAGES[a.builtin]);
  const over = backOverflow(p);
  const backChars = [...String(C.backText || '')].length + [...String(C.backHeadline || '')].length;
  const textField = (path, value, label, hint, ph) => field(label, text(path, value, { maxlength: String(LIMITS.short), placeholder: ph }), hint);
  const coverText = h('section', { class: 'cvt', 'aria-labelledby': 'cvt-h' },
    h('h3', { id: 'cvt-h' }, '앞표지 글'),
    h('p', { class: 'hint' }, `제목(1단계: 「${p.meta.title || '제목 없음'}」)과 지은이(「${p.meta.authorAlias || '없음'}」)는 그대로 쓰여요. 아래 두 칸은 비워 두면 표지에서 빠지고, 나머지가 자리를 다시 잡아요.`),
    textField('frontMatter.titlePage', p.frontMatter.titlePage, '부제 (무엇을 다룬 책인지 구체적으로)', '표제지 부제와 같은 칸이에요.', '예: 등굣길 칠 분의 기록'),
    textField('cover.copy', C.copy, '카피 (관심을 끄는 짧은 한 줄, 25자 안팎)', '부제와 달리 책의 분위기나 마음을 전해요. 추천사나 수상 이력은 실제로 있을 때만 써요.', '예: 같은 길도 천천히 걸으면 다른 이야기가 보인다'));
  const backFields = h('section', { class: 'cvt', 'aria-labelledby': 'cvb-h' },
    h('h3', { id: 'cvb-h' }, '뒤표지'),
    textField('cover.backHeadline', C.backHeadline, '강조 문장 (책의 핵심을 한 문장으로)', '뒤표지 맨 위에 크게 놓여요.', '예: 땅만 보고 걷던 칠 분이, 어느 날 조금 느려졌다.'),
    field('소개 글 (무슨 내용인지 두세 문장, 문단은 줄을 바꿔요)', area('cover.backText', C.backText, { rows: 5, maxlength: String(LIMITS.long) }), '서점에서 책을 뒤집어 본 독자가 읽을 내용 소개예요.'),
    h('p', { class: 'hint' }, p.meta.targetReader ? `「이런 독자에게」에는 1단계에서 정한 독자(「${p.meta.targetReader}」)가 들어가요.` : '1단계에서 독자를 정하면 뒤표지 「이런 독자에게」에 들어가요.'),
    over > 0 ? h('p', { class: 'cvp-warn', role: 'status' }, `뒤표지 글이 공간보다 길어서 끝부분이 가려져요. 소개 글을 약 ${Math.max(10, Math.ceil(backChars * over / 10) * 10)}자 줄이거나 강조 문장을 짧게 해 주세요.`) : null);
  return [
    coverText,
    h('fieldset', { class: 'choices cvl' }, h('legend', {}, '표지 배치'),
      h('p', { class: 'hint' }, '견본은 지금 내 책의 제목·부제·지은이로 만든 표지예요. 배치마다 그림과 글자의 자리가 달라요.'),
      notice,
      h('div', { class: 'cvl-grid' }, Object.entries(LAYOUTS).map(([v, t]) => {
        const off = v !== 'type' && !img;   // full, band and panel need a picture
        return h('label', { class: `choice cvl-choice${off ? ' off' : ''}` },
          h('input', { type: 'radio', name: 'cover-layout', value: v, checked: layout === v, disabled: off, onchange: () => { coverUndo = null; set('layout', v); rerender(); refocus(`.cvl-choice input[value="${v}"]`); } }),
          coverSample(p, off ? 'type' : v),
          h('span', { class: 'dz-txt' }, h('b', {}, t.label), h('small', {}, off ? '아래에서 표지 그림을 고르면 쓸 수 있어요.' : t.desc)));
      }))),
    h('section', { class: 'cvp', 'aria-labelledby': 'cvp-h' },
      h('h3', { id: 'cvp-h' }, '표지 그림'),
      h('p', { class: 'hint' }, '표지 전용 사진은 책 내용과 분위기를 보고 골라요. 사진마다 제목이 놓일 자리와 어울리는 색이 정해져 있어요. 출처는 뒤표지에 자동으로 적혀요.'),
      h('div', { class: 'cvp-grid' }, Object.entries(COVER_IMAGES).map(([key, m]) => h('button', {
        type: 'button', class: 'cvp-builtin', 'data-key': key, 'aria-pressed': String(img?.builtin === key), onclick: () => pickBuiltin(key),
      }, h('img', { src: m.src, alt: '', width: 120, height: 170 }), h('span', {}, m.name)))),
      h('div', { class: 'row cvp-own' },
        field('내가 준비한 그림 (4단계)', h('select', { onchange: (e) => pickOwn(e.target.value) },
          h('option', { value: '' }, '그림 없음'),
          own.map((a) => h('option', { value: a.id, selected: a.id === C.imageId }, a.name || '그림')),
          img && COVER_IMAGES[img.builtin] ? h('option', { value: img.id, selected: true }, `${img.name} (표지 사진)`) : null))),
      img && layout !== 'type' ? h('div', { class: 'cvp-adjust' },
        h('p', { class: 'fm-label' }, '사진 위치 조정 (사진은 늘어나지 않고, 보이는 부분만 옮겨요)'),
        field('가로', h('input', { type: 'range', min: '0', max: '100', step: '5', value: String(C.focusX), 'aria-valuetext': `${C.focusX}%`, oninput: (e) => set('focusX', +e.target.value) })),
        field('세로', h('input', { type: 'range', min: '0', max: '100', step: '5', value: String(C.focusY), 'aria-valuetext': `${C.focusY}%`, oninput: (e) => set('focusY', +e.target.value) })),
        layout === 'full' ? [
          radios('cover-ty', '제목 자리', Object.fromEntries(Object.entries(TEXT_Y).map(([k, [, l]]) => [k, l])),
            Object.entries(TEXT_Y).reduce((best, [k, [y]]) => (Math.abs(y - C.textY) < Math.abs(TEXT_Y[best][0] - C.textY) ? k : best), 'top'),
            (k) => { coverUndo = null; set('textY', TEXT_Y[k][0]); rerender(); refocus(`input[name="cover-ty"][value="${k}"]`); }),
          radios('cover-ta', '제목 정렬', { left: '왼쪽', center: '가운데', right: '오른쪽' }, C.textAlign, (v) => { coverUndo = null; set('textAlign', v); rerender(); refocus(`input[name="cover-ta"][value="${v}"]`); }),
          h('div', { class: 'row' },
            h('button', { class: 'btn sm cvp-ink', type: 'button', onclick: autoInk }, '글자색 맞추기 (사진의 밝기를 재서 고름)'),
            h('span', { class: 'muted' }, `지금 글자색: ${C.ink || '#ffffff'}`)),
          h('p', { class: 'hint' }, '「아래」를 고르면 지은이 이름은 표지 위쪽으로 옮겨요.'),
          msg ? h('p', { class: 'cvp-ok', role: 'status' }, msg) : null,
          warn] : null) : null,
      notes.map((t) => h('p', { class: 'cvp-warn' }, t))),
    h('fieldset', { class: 'choices' }, h('legend', {}, layout === 'full' ? '표지 색 (책등·뒤표지)' : '표지 색 (제목 영역·책등·뒤표지)'),
      h('div', { class: 'row' }, SWATCHES.map(([c, name]) => h('button', { type: 'button', class: 'swatch', 'data-color': c, style: { background: c }, 'aria-label': `표지 색 ${name}`, title: name, 'aria-pressed': String(c === C.backgroundColor), onclick: (e) => { color.value = c; set('backgroundColor', c); syncSwatches(e.target.parentElement, c); } })), color)),
    backFields,
    field('되돌아보기: 내가 고른 디자인의 이유를 한 문장으로', area('reflection.designReason', p.reflection.designReason, { rows: 2, maxlength: String(LIMITS.short), placeholder: '예: 중학생 독자가 편하게 읽도록 고딕 서체와 넓은 줄 간격을 골랐다.' })),
    h('div', { class: 'row finish-row', role: 'group', 'aria-label': '완성하기' },
      h('button', { class: 'btn primary', type: 'button', onclick: openBook }, '완성본 보기'),
      h('button', { class: 'btn', type: 'button', onclick: printBook }, '인쇄 / PDF로 저장'),
      h('button', { class: 'btn', type: 'button', onclick: exportJson }, 'JSON 백업')),
  ];
}

// ---------- completed book ----------
// The same pages as the live preview, read page by page like an e-book (src/pages/reader.js, W-038).
function openBook() {
  const opener = document.activeElement;
  const view = bookReader();
  const dlg = h('dialog', { class: 'book-dialog', 'aria-label': '완성본 보기' },
    h('div', { class: 'bd-bar' },
      h('strong', {}, `완성본 · ${getProject().meta.title || '제목 없는 책'}`),
      h('div', { class: 'row small' },
        h('button', { class: 'btn sm primary', type: 'button', onclick: printBook }, '인쇄 / PDF로 저장'),
        h('button', { class: 'btn sm', type: 'button', autofocus: true, onclick: () => dlg.close() }, '닫기'))),
    h('div', { class: 'bd-read' }, view.el));
  dlg.addEventListener('close', () => { view.destroy(); dlg.remove(); opener?.focus?.(); });
  document.body.append(dlg);
  dlg.showModal(); // the reader renders when it gets its size (ResizeObserver)
}

// Print: the same sequence and styles, one CSS page per book page. Folios come from the print engine
// (@page margin boxes, counter(page) = the PDF's page number); covers are full-bleed named pages.
export function prepareBookPrint() {
  const p = getProject();
  const g = geometry(p.layout);
  const mm = (v) => `${v.toFixed(2)}mm`;
  const folio = (side) => `@bottom-${side} { content: counter(page); font: 7.5pt ${FONT_STACKS.gothic}; color: var(--folio, #555); vertical-align: middle; }`;
  const css = `@page { size: ${g.w}mm ${g.h}mm; margin: ${mm(g.top)} ${mm(g.side)} ${mm(g.bottom)}; }
@page :right { margin-left: ${mm(g.inner)}; margin-right: ${mm(g.outer)}; ${folio('right')} }
@page :left { margin-left: ${mm(g.outer)}; margin-right: ${mm(g.inner)}; ${folio('left')} }
@page plain { @bottom-left { content: none; } @bottom-right { content: none; } }
@page cover { margin: 0; @bottom-left { content: none; } @bottom-right { content: none; } }`;
  const seq = bookSequence(p, 'pr');
  // lay the interior out once off screen at print size to place the same blank pages as the preview (paginate)
  const probeFlow = h('div', { class: 'pv-flow' }, ...seq.flow);
  const probe = h('div', { class: 'book pv-strip', 'data-theme': p.layout.theme || 'classic', style: 'position:fixed;left:-100000px;top:0;visibility:hidden' }, probeFlow);
  applyVars(probe, bookVars(p));
  probe.style.setProperty('--mm', `${PX_PER_MM}px`);
  document.body.append(probe);
  paginate(probeFlow, g.w * PX_PER_MM);
  const interior = [...probeFlow.children];
  probe.remove();
  const book = h('div', { class: 'book book-print', 'data-theme': p.layout.theme || 'classic' },
    h('div', { class: 'pg pg-cover' }, seq.front), ...interior, h('div', { class: 'pg pg-cover pg-back' }, seq.back));
  applyVars(book, bookVars(p));
  $('#print-root').replaceChildren(h('style', {}, css), book);
  document.body.dataset.print = 'book';
}

export function printBook() {
  prepareBookPrint();
  window.print();
}

// ---------- page ----------
export function mountStudio(root) {
  const stepper = h('ol', { class: 'stepper', 'aria-label': '8단계' });
  const editor = h('section', { class: 'editor paper', 'aria-labelledby': 'step-title' });
  const pv = preview();
  const progress = h('span', { class: 'progress-n' });
  const meter = h('span', { class: 'progress-meter', 'aria-hidden': 'true' }, h('span', {}));
  const importInput = h('input', { type: 'file', accept: 'application/json,.json', hidden: true, onchange: (e) => { importJson(e.target.files[0]); e.target.value = ''; } });
  const viewTabs = h('div', { class: 'view-tabs', role: 'group', 'aria-label': '화면 전환' },
    h('button', { type: 'button', 'aria-pressed': 'true', onclick: () => setView('edit') }, '편집'),
    h('button', { type: 'button', 'aria-pressed': 'false', onclick: () => setView('preview') }, '미리보기'));
  const work = h('div', { class: 'workbench', 'data-view': 'edit' }, editor, pv.el);
  const sampleNote = h('p', { class: 'sample-note', role: 'note' },
    h('strong', {}, '예시 책이에요. '), '1~6단계는 예시로 미리 채워져 있어요(✓). 각 단계를 둘러보며 내용을 내 생각대로 바꿔 보고, 7·8단계는 직접 마무리해 보세요.');
  const blankNote = h('p', { class: 'sample-note blank-note', role: 'note' },
    h('span', {}, h('strong', {}, '처음이라면 '), '완성된 예시 책을 먼저 둘러보고 시작해도 좋아요.'),
    h('button', { class: 'btn sm', type: 'button', onclick: startSample }, '예시 책 불러오기'));
  const syncSampleNote = () => {
    sampleNote.hidden = !getProject().id.startsWith('sample');
    blankNote.hidden = !sampleNote.hidden || progressCount() > 0;
  };

  const paneY = {};
  function setView(v) {
    paneY[work.dataset.view] = scrollY;
    work.dataset.view = v;
    viewTabs.querySelectorAll('button').forEach((b, i) => b.setAttribute('aria-pressed', String((i === 0) === (v === 'edit'))));
    if (v === 'preview') pv.render();
    if (paneY[v] != null) scrollTo(0, paneY[v]);
  }

  function renderStepper() {
    const p = getProject();
    progress.textContent = `${progressCount()} / 8 단계 완료`;
    meter.firstChild.style.width = `${(progressCount() / 8) * 100}%`;
    syncSampleNote();
    stepper.replaceChildren(...STEP_NAMES.map((name, i) => {
      const n = i + 1;
      const done = stepDone(n);
      return h('li', {}, h('button', {
        type: 'button', class: 'step', 'aria-current': n === p.progress.currentStep ? 'step' : null, 'data-done': String(done),
        onclick: () => setField('progress.currentStep', n),
      }, h('span', { class: 'step-n' }, done ? '✓' : String(n)), h('span', { class: 'step-name' }, name), h('span', { class: 'sr' }, done ? ' (완료)' : ' (진행 전)')));
    }));
    // Phone: the stepper is one scrolling row; keep the current step in view (horizontal only, never the page).
    const cur = stepper.querySelector('[aria-current]');
    if (cur && stepper.scrollWidth > stepper.clientWidth) {
      stepper.scrollLeft += cur.getBoundingClientRect().left - stepper.getBoundingClientRect().left - (stepper.clientWidth - cur.offsetWidth) / 2;
    }
  }

  let blocks = null;
  function renderEditor() {
    const p = getProject();
    const n = p.progress.currentStep;
    const info = edu.steps.find((s) => s.n === n) || { title: STEP_NAMES[n - 1], intro: '', tips: [], check: '' };
    blocks = null;
    let body;
    if (n === 1) body = step1(p);
    else if (n === 2 || n === 5) { blocks = blockEditor({ mode: n === 2 ? 'manuscript' : 'layout' }); body = [blocks.el]; }
    else if (n === 3) body = step3(p, renderEditor);
    else if (n === 4) body = step4(p, renderEditor);
    else if (n === 6) body = step6(p);
    else if (n === 7) body = step7(p, renderEditor);
    else body = step8(p, renderEditor);
    // Step 8: the finish actions come last, after the self-check and the status line.
    const finish = n === 8 ? body.pop() : null;
    editor.replaceChildren(
      h('div', { class: 'step-head' },
        artImg(`step-${n}`, 'step-ic', 'step'),
        h('p', { class: 'step-kicker' }, `${n}단계 / 8`),
        h('h2', { id: 'step-title', tabindex: '-1' }, info.title || STEP_NAMES[n - 1]),
        h('p', { class: 'lead' }, info.intro)),
      h('section', { class: 'missions', 'aria-label': '편집장의 미션' }, h('h3', {}, '편집장의 미션'), h('ul', {}, missionList(n))),
      h('div', { class: 'step-body' }, body),
      info.tips?.length || info.check ? h('div', { class: 'step-help' },
        info.tips?.length ? h('details', { class: 'tips' }, h('summary', {}, `편집자의 팁 ${info.tips.length}개`), h('ul', {}, info.tips.map((t) => h('li', {}, t)))) : null,
        info.check ? h('div', { class: 'self-check' }, h('strong', {}, '스스로 확인하기 '), info.check) : null) : null,
      h('p', { class: 'step-status', 'data-done': String(stepDone(n)) }, stepDone(n) ? '✓ 이 단계를 마쳤어요.' : `아직 마치지 않았어요: ${missing(n)}`),
      ...(finish ? [finish] : []),
      h('div', { class: 'row step-nav' },
        h('button', { class: 'btn', type: 'button', disabled: n === 1, onclick: () => go(n - 1) }, '이전 단계'),
        n < 8 ? h('button', { class: 'btn primary next-step', type: 'button', onclick: () => go(n + 1) }, `다음 단계: ${STEP_NAMES[n]}`) : null));
    wasDone = stepDone(n);
  }
  let wasDone = false;

  function go(n) { setField('progress.currentStep', n); editor.querySelector('#step-title')?.focus(); }

  let raf = 0;
  const unsub = subscribe((kind) => {
    if (kind === 'focus') { cancelAnimationFrame(raf); raf = requestAnimationFrame(pv.render); return; }
    if (kind === 'replace') syncSampleNote();
    if (kind === 'step' || kind === 'replace') { renderEditor(); renderStepper(); editor.querySelector('#step-title')?.focus({ preventScroll: true }); }
    else { renderStepper(); const s = editor.querySelector('.step-status'); if (s) updateStatus(s); }
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(pv.render);
  });

  function updateStatus(s) {
    const n = getProject().progress.currentStep;
    const done = stepDone(n);
    s.dataset.done = String(done);
    s.textContent = done ? '✓ 이 단계를 마쳤어요.' : `아직 마치지 않았어요: ${missing(n)}`;
    editor.querySelector('.missions ul')?.replaceChildren(...missionList(n));
    if (done && !wasDone) celebrate(n);
    wasDone = done;
  }
  // Step just finished: proofreader's stamp + the next button pulses once.
  function celebrate(n) {
    const st = h('span', { class: 'stamp stamp-fixed', 'aria-hidden': 'true' }, `${n}단계 완료`);
    document.body.append(st);
    setTimeout(() => st.remove(), 1600);
    const next = editor.querySelector('.next-step');
    next?.classList.add('pulse');
    next?.addEventListener('animationend', () => next.classList.remove('pulse'), { once: true });
    toast(n < 8 ? `${n}단계 완료! 다음은 ${STEP_NAMES[n]} 단계예요.` : '8단계까지 모두 마쳤어요. 「완성본 보기」로 내 책을 펼쳐 보세요.');
  }

  const closeMenu = (e) => {
    const menu = root.querySelector('.file-menu[open]');
    if (!menu) return;
    if (e.type === 'keydown' && e.key === 'Escape') { menu.open = false; menu.querySelector('summary').focus(); }
    else if ((e.type === 'click' || e.type === 'focusin') && !menu.contains(e.target)) menu.open = false;
  };
  document.addEventListener('keydown', closeMenu);
  document.addEventListener('click', closeMenu);
  document.addEventListener('focusin', closeMenu);
  root.append(
    h('div', { class: 'studio-head' },
      h('div', { class: 'studio-title' }, h('h1', {}, '나만의 책 만들기'), h('p', { class: 'progress-line' }, meter, progress)),
      h('div', { class: 'studio-tools', role: 'group', 'aria-label': '내 책' },
        h('button', { class: 'btn', type: 'button', onclick: openBook }, '완성본 보기'),
        h('details', { class: 'file-menu' }, h('summary', { class: 'btn' }, '책 파일', h('span', { class: 'caret', 'aria-hidden': 'true' }, '▾')),
          h('div', { class: 'file-menu-list', onclick: (e) => { if (e.target.closest('button')) e.currentTarget.parentElement.open = false; } },
            fmGroup('fm-save', '내 책을 파일로 저장', h('button', { class: 'btn sm', type: 'button', onclick: exportJson }, 'JSON 백업')),
            fmGroup('fm-open', '저장한 파일 열기', h('button', { class: 'btn sm', type: 'button', onclick: () => importInput.click() }, 'JSON 불러오기')),
            fmGroup('fm-new', '새로 시작',
              h('button', { class: 'btn sm', type: 'button', onclick: startSample }, '예시 책 불러오기'),
              h('button', { class: 'btn sm', type: 'button', onclick: startBlank }, '새 책 시작')), importInput)))),
    sampleNote, blankNote,
    h('nav', { class: 'stepper-wrap', 'aria-label': '단계 이동' }, stepper),
    viewTabs, work);
  renderStepper();
  renderEditor();
  syncSampleNote();
  return () => { unsub(); pv.destroy(); document.removeEventListener('keydown', closeMenu); document.removeEventListener('click', closeMenu); document.removeEventListener('focusin', closeMenu); };
}

function missing(n) {
  const p = getProject();
  const empty = (pairs) => pairs.filter(([v]) => !String(v || '').trim()).map(([, label]) => label).join(', ');
  const m = {
    1: () => `${empty([[p.meta.title, '제목'], [p.meta.genre, '장르'], [p.meta.topic, '주제'], [p.meta.targetReader, '독자']])}을(를) 채워 주세요.`,
    2: () => '장·절 같은 제목 1개와 문단 1개 이상을 써 주세요.',
    3: () => '스타일을 하나 골라 주세요.',
    4: () => (p.assets.length ? '모든 그림에 출처와 이용 조건을 적어 주세요.' : '그림을 1개 이상 준비해 주세요.'),
    5: () => '본문에 그림이나 표를 1개 이상 넣고, 그림마다 캡션과 대체 텍스트를 적어 주세요.',
    6: () => `${empty([[p.frontMatter.copyrightText, '판권지'], [p.frontMatter.preface, '머리말']])}을(를) 써 주세요.`,
    7: () => (headings(p).length ? '목차를 확인했다고 체크해 주세요.' : '2단계에서 제목을 먼저 써 주세요.'),
    8: () => `${empty([[p.cover.backText, '뒤표지 소개 글'], [p.reflection.designReason, '디자인 이유']])}을(를) 써 주세요.`,
  };
  return m[n]();
}
