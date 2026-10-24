// Tiny DOM builder. User strings always go through textContent, never innerHTML.
export function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v == null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
    else if (k.startsWith('on')) el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k in el && typeof v !== 'string') el[k] = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  // Non-auth text fields: keep password managers / autofill out of the way.
  if (tag === 'input' && ['text', 'search'].includes(el.type) && !el.hasAttribute('autocomplete')) el.autocomplete = 'off';
  append(el, children);
  return el;
}

function append(el, children) {
  for (const c of children.flat(Infinity)) {
    if (c == null || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
}

// replaceChildren() prints null/false as text ("null" on screen, W-027/W-029); fill() skips them like h() does.
export function fill(el, ...children) {
  el.replaceChildren();
  append(el, children);
  return el;
}

export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

let toastTimer;
export function toast(msg, kind = 'info') {
  let el = $('#toast');
  if (!el) {
    el = h('div', { id: 'toast', role: 'status', 'aria-live': 'polite' });
    document.body.append(el);
  }
  el.textContent = msg;
  el.dataset.kind = kind;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 3200);
}

// Modal built on <dialog>: Esc closes, focus returns to the opener.
export function modal({ title, body, actions }) {
  return new Promise((resolve) => {
    const opener = document.activeElement;
    const dlg = h('dialog', { class: 'modal', 'aria-labelledby': 'modal-title' },
      h('h2', { id: 'modal-title' }, title),
      h('div', { class: 'modal-body' }, body),
      h('div', { class: 'modal-actions' },
        actions.map((a) => h('button', {
          class: a.primary ? 'btn primary' : a.danger ? 'btn danger' : 'btn',
          type: 'button',
          onclick: () => { dlg.close(a.value); },
        }, a.label))));
    dlg.addEventListener('close', () => {
      dlg.remove();
      opener?.focus?.();
      resolve(dlg.returnValue || null);
    });
    document.body.append(dlg);
    dlg.showModal();
  });
}

export function download(filename, text, type = 'application/json') {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = h('a', { href: url, download: filename });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
