(function () {
  "use strict";

  // Guarda el último elemento de entrada con foco
  let lastFocused = null;

  function isTextInput(el) {
    return el && ((el.tagName === 'INPUT' && /text|search|tel|url|email/.test(el.type)) || el.tagName === 'TEXTAREA');
  }

  function setLastFocused(e) {
    const t = e.target;
    if (isTextInput(t) || (t && t.isContentEditable)) {
      lastFocused = t;
    }
  }

  // Convierte entidades HTML a texto si es necesario
  function decodeHtmlEntities(str) {
    if (!str) return str;
    const txt = document.createElement('textarea');
    txt.innerHTML = str;
    return txt.value;
  }

  function insertAtCursor(el, text) {
    if (!el) return;
    text = decodeHtmlEntities(text);

    // input / textarea
    if (isTextInput(el)) {
      try {
        const start = el.selectionStart ?? el.value.length;
        const end = el.selectionEnd ?? start;
        const v = el.value || "";
        el.value = v.slice(0, start) + text + v.slice(end);
        const pos = start + text.length;
        el.setSelectionRange(pos, pos);
        el.focus();
        el.dispatchEvent(new Event('input', { bubbles: true }));
      } catch (err) {
        el.value = (el.value || '') + text;
        el.focus();
        el.dispatchEvent(new Event('input', { bubbles: true }));
      }
      return;
    }

    // contenteditable
    if (el && el.isContentEditable) {
      const sel = window.getSelection();
      if (!sel) {
        el.textContent = (el.textContent || '') + text;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        return;
      }
      if (sel.rangeCount === 0) {
        el.focus();
        sel.selectAllChildren(el);
        sel.collapseToEnd();
      }
      const range = sel.getRangeAt(0);
      range.deleteContents();
      const node = document.createTextNode(text);
      range.insertNode(node);
      range.setStartAfter(node);
      range.collapse(true);
      sel.removeAllRanges();
      sel.addRange(range);
      el.focus();
      el.dispatchEvent(new Event('input', { bubbles: true }));
      return;
    }

    // fallback: selector por data-default-target
    const fallbackSelector = document.querySelector('[data-default-target]');
    if (fallbackSelector) {
      insertAtCursor(fallbackSelector, text);
    }
  }

  // Maneja click en botones (delegación)
  function onDocumentClick(e) {
    const btn = e.target.closest && e.target.closest('.symbol-button, [data-symbol]');
    if (!btn) return;
    e.preventDefault();

    // Priorizar data-symbol; si no existe, tomar texto interno
    let symbol = btn.getAttribute('data-symbol') || btn.dataset.symbol || btn.textContent || '';
    symbol = (symbol || '').trim();
    if (!symbol) return;

    // Si el boton indica un target específico
    const targetSelector = btn.getAttribute('data-target');
    let targetEl = null;
    if (targetSelector) {
      try { targetEl = document.querySelector(targetSelector); } catch { targetEl = null; }
    }

    if (!targetEl) targetEl = lastFocused;

    if (!targetEl) {
      const container = btn.closest('.symbol-container') || document;
      targetEl = container.querySelector('input[type="text"], textarea, [contenteditable="true"]');
    }

    insertAtCursor(targetEl, symbol);
  }

  // permitir activar con Enter/Space para accesibilidad
  function onDocumentKeydown(e) {
    const btn = e.target.closest && e.target.closest('.symbol-button, [data-symbol]');
    if (!btn) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      btn.click();
    }
  }

  function initSymbolInserter() {
    document.addEventListener('focusin', setLastFocused, true);
    document.addEventListener('click', onDocumentClick, true);
    document.addEventListener('keydown', onDocumentKeydown, true);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSymbolInserter);
  } else {
    initSymbolInserter();
  }
})();