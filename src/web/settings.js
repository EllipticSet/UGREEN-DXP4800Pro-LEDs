// SPDX-License-Identifier: MIT
(() => {
  document.querySelectorAll('.nas-front-settings').forEach(panel => {
    if (panel.dataset.initialized) return;
    panel.dataset.initialized = 'true';
    panel.querySelectorAll('.nas-help-toggle').forEach(button => {
      button.addEventListener('click', () => {
        const help = document.getElementById(button.getAttribute('aria-controls'));
        const expanded = button.getAttribute('aria-expanded') !== 'true';
        button.setAttribute('aria-expanded', String(expanded));
        if (window.jQuery) {
          // Use the same jQuery animation as Unraid's inline setting help.
          window.jQuery(help).stop(true, true).toggle('slow');
        } else {
          help.style.display = expanded ? 'block' : 'none';
        }
      });
    });
    panel.querySelectorAll('.nas-feedback.success').forEach(notice => {
      setTimeout(() => notice.remove(), 5000);
    });
    panel.querySelectorAll('.nas-feedback-close').forEach(button => {
      button.addEventListener('click', () => button.closest('.nas-feedback').remove());
    });
  });
})();
// SPDX-License-Identifier: MIT
(() => {
  const guide = document.querySelector('.nas-mapping-guide');
  if (!guide || guide.dataset.initialized) return;
  guide.dataset.initialized = 'true';
  const content = guide.querySelector('#nas-mapping-content');
  const reopen = guide.querySelector('.nas-guide-open');
  const done = guide.querySelector('.nas-guide-done');
  const key = 'nas-front-leds.mapping-guide.dismissed';
  function show(expanded, focus) {
    content.hidden = !expanded;
    reopen.hidden = expanded;
    reopen.setAttribute('aria-expanded', String(expanded));
    if (focus) (expanded ? done : reopen).focus();
  }
  try { show(localStorage.getItem(key) !== 'true', false); } catch (_) { show(true, false); }
  done.addEventListener('click', () => {
    show(false, true);
    try { localStorage.setItem(key, 'true'); } catch (_) {}
  });
  reopen.addEventListener('click', () => {
    show(true, true);
    try { localStorage.removeItem(key); } catch (_) {}
  });
})();
