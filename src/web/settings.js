// SPDX-License-Identifier: MIT
(() => {
  const guide = document.querySelector('.nas-mapping-guide');
  if (!guide) return;
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
