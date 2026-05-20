/* Inline form-error decorator.
 *
 * Reads the JSON payload emitted by registar/_form_errors.html
 * (`#form-errors-data` = { field_name: ["error", ...] }), finds the matching
 * input/select/textarea by [name], walks up to its closest .info-row, marks
 * it with .info-row--has-error, and injects a .info-row__error bubble.
 *
 * Auto-scrolls and focuses the first errored field on load. Clears the error
 * state for a field as soon as the user starts editing it (input/change),
 * so the red border + bubble disappear without waiting for a re-submit.
 */
(function () {
  'use strict';

  var dataEl = document.getElementById('form-errors-data');
  if (!dataEl) return;

  var errorsByField;
  try {
    errorsByField = JSON.parse(dataEl.textContent || '{}');
  } catch (e) {
    return;
  }

  function findInput(name) {
    // Prefer an input directly inside an .info-row over any other [name]
    // (e.g. hidden helpers from select2 / formsets).
    var candidates = document.querySelectorAll(
      '[name="' + name.replace(/"/g, '\\"') + '"]'
    );
    for (var i = 0; i < candidates.length; i++) {
      if (candidates[i].closest('.info-row')) return candidates[i];
    }
    return candidates[0] || null;
  }

  function decorateField(name, messages) {
    var input = findInput(name);
    if (!input) return null;
    var row = input.closest('.info-row');
    if (!row) return null;

    row.classList.add('info-row--has-error');
    input.setAttribute('aria-invalid', 'true');

    // Inject the bubble after the input's value-wrapper, only if not present.
    var bubble = row.querySelector('.info-row__error');
    if (!bubble) {
      bubble = document.createElement('div');
      bubble.className = 'info-row__error';
      bubble.setAttribute('role', 'alert');
      // Anchor the bubble inside the row body for layout consistency.
      var anchor = row.querySelector('.info-row__body') || row;
      anchor.appendChild(bubble);
    }
    bubble.textContent = messages.join(' · ');

    // Clear on first edit. `once: true` ensures we don't re-bind.
    var clear = function () {
      row.classList.remove('info-row--has-error');
      input.removeAttribute('aria-invalid');
      if (bubble && bubble.parentNode) bubble.parentNode.removeChild(bubble);
    };
    input.addEventListener('input', clear, { once: true });
    input.addEventListener('change', clear, { once: true });

    return input;
  }

  var firstInput = null;
  Object.keys(errorsByField).forEach(function (name) {
    var messages = errorsByField[name];
    if (!messages || !messages.length) return;
    var input = decorateField(name, messages);
    if (input && !firstInput) firstInput = input;
  });

  if (firstInput) {
    // Wait one frame so layout settles before scrolling.
    requestAnimationFrame(function () {
      firstInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Focusing select2-hidden inputs jumps weirdly — only focus visible ones.
      if (firstInput.offsetParent !== null) firstInput.focus({ preventScroll: true });
    });
  }
})();
