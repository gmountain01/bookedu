// Block editor for the manuscript (step 2) and body layout (step 5).
// Text edits update state without re-rendering, so the cursor never jumps.
import { h, toast, modal } from '../dom.js';
import {
  getProject, addBlock, updateBlock, removeBlock, moveBlock, canAdd, totalChars, touchBlock,
  HEADING_NAMES, LIMITS,
} from '../state.js';
import { assetSrc } from '../images.js';

const TYPE_LABEL = { heading: '제목', paragraph: '문단', image: '그림', table: '표' };

// Keeps the whole manuscript (text, captions, table cells) within LIMITS.chars.
export function guard(el, before) {
  const room = LIMITS.chars - (totalChars() - before);
  if (el.value.length > room) {
    el.value = el.value.slice(0, Math.max(before, room));
    toast(`원고는 표와 캡션을 합쳐 모두 ${LIMITS.chars.toLocaleString()}자까지 쓸 수 있어요.`, 'error');
  }
  return el.value;
}

function blockLabel(b) {
  if (b.type === 'heading') return `${HEADING_NAMES[b.level]}`;
  return TYPE_LABEL[b.type];
}

function textControl(b) {
  if (b.type === 'heading') {
    return h('input', {
      type: 'text', value: b.text || '', maxlength: String(LIMITS.title * 2), 'aria-label': `${HEADING_NAMES[b.level]} 제목`,
      placeholder: `${HEADING_NAMES[b.level]} 제목을 써 보세요`,
      oninput: (e) => updateBlock(b.id, { text: guard(e.target, (b.text || '').length) }),
    });
  }
  return h('textarea', {
    rows: 4, 'aria-label': '문단 내용', placeholder: '문단 내용을 써 보세요. 줄을 바꾸면 새 줄로 이어져요.',
    oninput: (e) => updateBlock(b.id, { text: guard(e.target, (b.text || '').length) }),
  }, b.text || '');
}

function imageControl(b) {
  const a = getProject().assets.find((x) => x.id === b.assetId);
  return h('div', { class: 'blk-media' },
    a ? h('img', { src: assetSrc(a), alt: '' }) : h('span', { class: 'warn' }, '이미지를 찾을 수 없어요'),
    h('div', { class: 'blk-fields' },
      h('label', { class: 'field' }, h('span', {}, '캡션 (그림 아래 설명)'),
        h('input', { type: 'text', value: b.caption || '', maxlength: String(LIMITS.short), placeholder: '예: 그림 1. 오후의 골목', oninput: (e) => updateBlock(b.id, { caption: guard(e.target, (b.caption || '').length) }) })),
      h('label', { class: 'field' }, h('span', {}, '대체 텍스트 (그림을 볼 수 없는 독자를 위한 설명)'),
        h('input', { type: 'text', value: b.alt || '', maxlength: String(LIMITS.short), placeholder: '예: 노란 불빛이 켜진 좁은 골목', oninput: (e) => updateBlock(b.id, { alt: e.target.value }) }))));
}

function tableControl(b, rerender) {
  const rows = b.rows;
  const set = (r, c, el) => { rows[r][c] = guard(el, rows[r][c].length); updateBlock(b.id, { rows }); };
  const resize = (dr, dc) => {
    const nr = rows.length + dr;
    const nc = rows[0].length + dc;
    if (nr < 2 || nc < 1) return toast('표는 머리글 행과 내용 1행, 1열 이상이어야 해요.', 'error');
    if (nr > LIMITS.rows || nc > LIMITS.cols) return toast(`표는 최대 ${LIMITS.rows}행 ${LIMITS.cols}열까지 만들 수 있어요.`, 'error');
    const next = Array.from({ length: nr }, (_, r) => Array.from({ length: nc }, (_, c) => rows[r]?.[c] ?? ''));
    updateBlock(b.id, { rows: next }, true);
    rerender();
  };
  return h('div', { class: 'blk-table' },
    h('label', { class: 'field' }, h('span', {}, '표 제목'),
      h('input', { type: 'text', value: b.caption || '', maxlength: String(LIMITS.short), placeholder: '예: 표 1. 골목 가게 조사', oninput: (e) => updateBlock(b.id, { caption: guard(e.target, (b.caption || '').length) }) })),
    h('div', { class: 'table-scroll' },
      h('table', { class: 'cell-grid' }, h('tbody', {}, rows.map((row, r) => h('tr', {}, row.map((cell, c) =>
        h('td', {}, h('input', {
          type: 'text', value: cell, maxlength: String(LIMITS.short),
          'aria-label': `${r === 0 ? '머리글' : `${r}행`} ${c + 1}열`, class: r === 0 ? 'th' : '',
          oninput: (e) => set(r, c, e.target),
        })))))))),
    h('div', { class: 'row small' },
      h('button', { class: 'btn sm', type: 'button', onclick: () => resize(1, 0) }, '행 추가'),
      h('button', { class: 'btn sm', type: 'button', onclick: () => resize(-1, 0) }, '행 삭제'),
      h('button', { class: 'btn sm', type: 'button', onclick: () => resize(0, 1) }, '열 추가'),
      h('button', { class: 'btn sm', type: 'button', onclick: () => resize(0, -1) }, '열 삭제'),
      h('span', { class: 'muted' }, `${rows.length}행 × ${rows[0].length}열 (첫 행은 머리글)`)));
}

/**
 * @param {{mode:'manuscript'|'layout'}} opts
 * Returns {el, rerender}. The caller re-renders on structural changes only.
 */
export function blockEditor({ mode }) {
  const el = h('div', { class: 'blocks', onfocusin: (e) => { const id = e.target.closest('[data-block]')?.dataset.block; if (id) touchBlock(id); } });
  const rerender = () => {
    const p = getProject();
    const focusId = document.activeElement?.closest?.('[data-block]')?.dataset.block;
    const list = h('ol', { class: 'blk-list' }, p.blocks.map((b, i) => {
      const levelSel = b.type === 'heading' ? h('select', {
        'aria-label': '제목 단계', onchange: (e) => { updateBlock(b.id, { level: +e.target.value }, true); rerender(); el.querySelector(`[data-block="${b.id}"] select`)?.focus(); },
      }, [1, 2, 3, 4].map((l) => h('option', { value: String(l), selected: l === b.level }, `${l}단계 · ${HEADING_NAMES[l]}`))) : null;
      const body = b.type === 'image' ? imageControl(b) : b.type === 'table' ? tableControl(b, rerender) : textControl(b);
      return h('li', { class: `blk blk-${b.type} lv${b.level || 0}`, 'data-block': b.id },
        h('div', { class: 'blk-head' },
          h('span', { class: 'blk-tag' }, blockLabel(b)), levelSel,
          b.type === 'paragraph' ? h('label', { class: 'blk-quote' }, h('input', { type: 'checkbox', checked: b.style === 'quote', onchange: (e) => updateBlock(b.id, { style: e.target.checked ? 'quote' : undefined }, true) }), h('span', {}, '인용문')) : null,
          h('div', { class: 'blk-tools' },
            h('button', { class: 'icon', type: 'button', 'aria-label': `${i + 1}번째 블록 위로`, disabled: i === 0, onclick: () => { moveBlock(b.id, -1); rerender(); el.querySelector(`[data-block="${b.id}"] .icon`)?.focus(); } }, '↑'),
            h('button', { class: 'icon', type: 'button', 'aria-label': `${i + 1}번째 블록 아래로`, disabled: i === p.blocks.length - 1, onclick: () => { moveBlock(b.id, 1); rerender(); el.querySelector(`[data-block="${b.id}"] .icon:nth-child(2)`)?.focus(); } }, '↓'),
            h('button', { class: 'icon danger', type: 'button', 'aria-label': `${i + 1}번째 블록 삭제`, onclick: async () => {
              const hasContent = (b.text || b.caption || '').trim() || b.type === 'image' || b.type === 'table';
              if (hasContent && await modal({ title: '이 블록을 지울까요?', body: h('p', {}, `${blockLabel(b)} 블록과 그 안의 내용이 지워져요.`), actions: [{ label: '지우기', value: 'yes', danger: true }, { label: '취소', value: 'no', primary: true }] }) !== 'yes') return;
              const next = p.blocks[i + 1]?.id || p.blocks[i - 1]?.id;
              removeBlock(b.id);
              rerender();
              (el.querySelector(`[data-block="${next}"] input, [data-block="${next}"] textarea`) || el.querySelector('.adders button'))?.focus();
            } }, '삭제'))),
        body);
    }));
    const empty = p.blocks.length ? null : h('p', { class: 'empty' }, mode === 'manuscript'
      ? '아직 원고가 없어요. 아래에서 「장」 제목부터 추가해 보세요.'
      : '본문이 비어 있어요. 2단계에서 원고를 먼저 써 주세요.');
    el.replaceChildren(empty || list, adders(mode, rerender));
    if (focusId && !el.contains(document.activeElement)) el.querySelector(`[data-block="${focusId}"] input, [data-block="${focusId}"] textarea`)?.focus();
  };
  rerender();
  return { el, rerender };
}

function adders(mode, rerender) {
  const p = getProject();
  const add = (block) => {
    const msg = canAdd(block.type, getProject(), block.rows ? block.rows.flat().join('').length : 0);
    if (msg) return toast(msg, 'error');
    const b = addBlock(block, posSel?.value || null);
    rerender();
    document.querySelector(`[data-block="${b.id}"] input, [data-block="${b.id}"] textarea`)?.focus();
  };
  const count = h('p', { class: 'muted' }, `원고 ${totalChars().toLocaleString()} / ${LIMITS.chars.toLocaleString()}자 · 블록 ${p.blocks.length} / ${LIMITS.blocks}개`);
  let posSel = null;
  if (mode === 'manuscript') {
    return h('div', { class: 'adders' },
      h('p', { class: 'adders-t' }, '맨 아래에 추가'),
      h('div', { class: 'row' },
        [1, 2, 3, 4].map((l) => h('button', { class: 'btn sm', type: 'button', onclick: () => add({ type: 'heading', level: l, text: '' }) }, `+ ${HEADING_NAMES[l]}`)),
        h('button', { class: 'btn sm', type: 'button', onclick: () => add({ type: 'paragraph', text: '' }) }, '+ 문단')),
      count);
  }
  posSel = h('select', { 'aria-label': '넣을 위치' },
    h('option', { value: '' }, '맨 끝에'),
    p.blocks.map((b, i) => h('option', { value: b.id }, `${i + 1}. ${blockLabel(b)} 「${(b.text || b.caption || '').slice(0, 18) || '내용 없음'}」 다음에`)));
  const assetSel = h('select', { 'aria-label': '넣을 그림' },
    p.assets.length ? p.assets.map((a) => h('option', { value: a.id }, a.name || '이름 없는 그림')) : h('option', { value: '' }, '4단계에서 그림을 먼저 준비하세요'));
  return h('div', { class: 'adders' },
    h('label', { class: 'field inline' }, h('span', {}, '넣을 위치'), posSel),
    h('div', { class: 'row' },
      h('label', { class: 'field inline' }, h('span', {}, '그림'), assetSel),
      h('button', {
        class: 'btn sm', type: 'button', disabled: !p.assets.length,
        onclick: () => assetSel.value && add({ type: 'image', assetId: assetSel.value, caption: '', alt: '' }),
      }, '+ 그림 넣기'),
      h('button', { class: 'btn sm', type: 'button', onclick: () => add({ type: 'table', caption: '', rows: [['항목', '내용'], ['', '']] }) }, '+ 표 넣기')),
    count);
}
