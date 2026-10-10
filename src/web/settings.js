// SPDX-License-Identifier: MIT
(() => {
  document.querySelectorAll('.nas-front-settings').forEach(panel => {
    if (panel.dataset.initialized) return;
    panel.dataset.initialized = 'true';
    const validColour = color => /^#[0-9a-f]{6}$/i.test(color || '') && color.toLowerCase() !== '#000000';
    panel.querySelectorAll('input[type="color"]').forEach(input => {
      let previous = input.value;
      function acceptColour() {
        const notice = input.parentElement.querySelector('.nas-color-feedback');
        const valid = validColour(input.value);
        if (valid) previous = input.value;
        else input.value = previous;
        if (notice) notice.hidden = valid;
      }
      // Restore unsupported choices before the bubbled event updates the preview.
      ['input', 'change'].forEach(event => input.addEventListener(event, acceptColour));
    });
    const leds = [...panel.querySelectorAll('.nas-led-marker')];
    const tests = new Map();
    const testTimers = new Map();
    function stopTest(key) {
      clearTimeout(testTimers.get(key));
      testTimers.delete(key);
      tests.delete(key);
    }
    const testButtons = [...panel.querySelectorAll('.nas-led-test')];
    const valueFor = key => panel.querySelector(`[name="${key}"]`)?.value;
    const errorFor = key => key === 'NETWORK_COLOR_ONLINE' ? 'NETWORK_COLOR_OFFLINE' :
      key === 'DISK_COLOR' ? 'DISK_COLOR_FAILED' : null;
    function updatePreview() {
      leds.forEach(led => {
        const errorKey = errorFor(led.dataset.colorKey);
        const testing = tests.has(errorKey);
        const color = testing ? tests.get(errorKey) : valueFor(led.dataset.colorKey);
        if (validColour(color)) led.style.setProperty('--led-color', color);
        led.classList.toggle('is-failure-test', testing && errorKey === 'DISK_COLOR_FAILED');
        const brightness = valueFor(led.dataset.brightnessKey) ?? led.dataset.brightness;
        const level = Number(brightness);
        if (Number.isFinite(level)) led.style.setProperty('--led-brightness', level > 0 ? 1 : 0);
      });
      testButtons.forEach(button => {
        const testing = tests.has(button.dataset.testColor);
        button.textContent = testing ? 'STOP PREVIEW' : 'PREVIEW (5s)';
        button.setAttribute('aria-pressed', String(testing));
      });
    }
    testButtons.forEach(button => button.addEventListener('click', () => {
      const key = button.dataset.testColor;
      if (tests.has(key)) stopTest(key);
      else {
        const color = valueFor(key);
        if (validColour(color)) {
          tests.set(key, color);
          testTimers.set(key, setTimeout(() => {
            stopTest(key);
            updatePreview();
          }, 5000));
        }
      }
      updatePreview();
    }));
    function previewField(event) {
      const key = event.target.name;
      // Editing a colour ends its test; only Test can activate an error preview.
      stopTest(errorFor(key) || key);
      updatePreview();
    }
    ['input', 'change'].forEach(event => panel.addEventListener(event, previewField));
    updatePreview();
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
  let expanded = false;
  function updateButton() {
    toggle.textContent = expanded ? 'Hide guide' : 'Show guide';
    toggle.setAttribute('aria-expanded', String(expanded));
  }
  function collapseGuide() {
    expanded = false;
    $(content).stop(true, true).hide();
    updateButton();
  }
  collapseGuide();
  // Also reset when browser history restores this page from its cache.
  window.addEventListener('pageshow', collapseGuide);
  toggle.addEventListener('click', () => {
    expanded = !expanded;
    updateButton();
    // Use the same jQuery animation as Unraid's native inline help.
    $(content).stop(true, true).toggle('slow');
  });
})();
