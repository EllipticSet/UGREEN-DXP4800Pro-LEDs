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
(() => {
  const guide = document.querySelector('.nas-mapping-guide');
  if (!guide || guide.dataset.initialized) return;
  guide.dataset.initialized = 'true';
  const content = guide.querySelector('#nas-mapping-content');
  const toggle = guide.querySelector('.nas-guide-open');
  const key = 'nas-front-leds.mapping-guide.dismissed';
  let expanded = true;
  try { expanded = localStorage.getItem(key) !== 'true'; } catch (_) {}
  function updateButton() {
    toggle.textContent = expanded ? 'Hide guide' : 'Show guide';
    toggle.setAttribute('aria-expanded', String(expanded));
  }
  content.style.display = expanded ? '' : 'none';
  updateButton();
  toggle.addEventListener('click', () => {
    expanded = !expanded;
    updateButton();
    // Use the same jQuery animation as Unraid's native inline help.
    $(content).stop(true, true).toggle('slow');
    try {
      if (expanded) localStorage.removeItem(key);
      else localStorage.setItem(key, 'true');
    } catch (_) {}
  });
})();
