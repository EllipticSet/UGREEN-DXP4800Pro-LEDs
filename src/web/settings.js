// SPDX-License-Identifier: MIT
(() => {
  document.querySelectorAll('.nas-front-settings').forEach(panel => {
    if (panel.dataset.initialized) return;
    panel.dataset.initialized = 'true';
    // Unraid owns the inline_help click binding and animation. Its native
    // initialization replaces help IDs; keep accessibility references in sync.
    panel.querySelectorAll('blockquote.inline_help').forEach(help => {
      const row = help.previousElementSibling;
      const button = row.querySelector('.nas-help-toggle');
      const input = row.querySelector('input, select');
      const sync = () => {
        button.setAttribute('aria-controls', help.id);
        button.setAttribute('aria-expanded', String(help.style.display !== 'none'));
        input.setAttribute('aria-describedby', help.id);
      };
      new MutationObserver(sync).observe(help, { attributes: true, attributeFilter: ['id', 'style'] });
      sync();
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
