/**
 * app.js
 *
 * Lógica general de la interfaz de usuario para la aplicación.
 * Incluye funcionalidades como los botones para limpiar campos de texto.
 */

document.addEventListener('DOMContentLoaded', function () {
  // Dispara evento input en un elemento (compatible)
  function triggerInputEvent(el) {
    try {
      el.dispatchEvent(new Event('input', { bubbles: true }));
    } catch (e) {
      // fallback para navegadores muy antiguos
      var ev = document.createEvent('Event');
      ev.initEvent('input', true, true);
      el.dispatchEvent(ev);
    }
  }

  // Maneja los botones de limpiar (.btn-limpiar)
  document.querySelectorAll('.btn-limpiar').forEach(function (btn) {
    btn.setAttribute('role', 'button');
    btn.setAttribute('tabindex', btn.getAttribute('tabindex') || '0');

    function doClear() {
      // Prioriza selector explícito data-target
      var targetSelector = btn.getAttribute('data-target');
      var target = null;
      if (targetSelector) {
        try { target = document.querySelector(targetSelector); } catch (err) { target = null; }
      }

      // Si no hay target explícito, buscar en el input-group más cercano
      if (!target) {
        var group = btn.closest('.input-group') || document;
        target = group.querySelector('input.form-control, textarea.form-control, [contenteditable="true"]');
      }

      // Fallback: buscar elemento marcado como data-default-target
      if (!target) {
        target = document.querySelector('[data-default-target]');
      }

      if (!target) return;

      if (target.isContentEditable) {
        target.innerHTML = '';
        target.focus();
        triggerInputEvent(target);
        return;
      }

      if ('value' in target) {
        target.value = '';
        try { target.setSelectionRange(0, 0); } catch (e) {}
        target.focus();
        triggerInputEvent(target);
        return;
      }

      // último recurso: limpiar textContent
      target.textContent = '';
      target.focus();
      triggerInputEvent(target);
    }

    btn.addEventListener('click', function (e) {
      e.preventDefault();
      doClear();
    });

    // Soporte accesible por teclado
    btn.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        doClear();
      }
    });
  });

  // Opcional: mejora para elementos copy-to-clipboard si existen (mantener funcionalidad)
  document.querySelectorAll('.copy-to-clipboard').forEach(function (el) {
    el.setAttribute('role', 'button');
    el.setAttribute('tabindex', el.getAttribute('tabindex') || '0');
    el.addEventListener('click', function () {
      var text = el.textContent.trim();
      if (navigator.clipboard && text) {
        navigator.clipboard.writeText(text).catch(function () {});
      }
    });
    el.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        el.click();
      }
    });
  });
});