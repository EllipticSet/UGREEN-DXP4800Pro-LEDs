// Live status refresh replaces every panel from one fragment and keeps old content on errors.
const assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm');
const panels = [{ innerHTML: 'old' }, { innerHTML: 'old' }];
let tick, response = { ok: true, text: async () => '<div class="nas-live-status"><strong>Live status</strong></div>' };
const requests = [];
const context = {
  window: {},
  setInterval: (fn, ms) => { assert.equal(ms, 5000); tick = fn; },
  fetch: async (url, options) => { requests.push([url, options.cache]); return response; },
  document: {
    hidden: false,
    querySelectorAll: selector => selector === '.nas-live-status' ? panels : [],
    querySelector: selector => selector === '.nas-live-status' ? panels[0] : null,
    createElement: () => {
      const template = { content: { firstElementChild: null } };
      Object.defineProperty(template, 'innerHTML', { set(html) {
        const match = html.match(/^<div class="([^"]+)">(.*)<\/div>$/s);
        template.content.firstElementChild = match ? { classList: { contains: name => match[1] === name }, innerHTML: match[2] } : null;
      } });
      return template;
    },
  },
};
vm.runInNewContext(fs.readFileSync('src/web/settings.js', 'utf8'), context);
(async () => {
  await tick();
  assert.deepEqual(requests, [['/plugins/UGREEN-DXP4800Pro-LEDs/status.php', 'no-store']]);
  panels.forEach(panel => assert.equal(panel.innerHTML, '<strong>Live status</strong>'));
  response = { ok: true, text: async () => '<p>login page</p>' };
  await tick();
  panels.forEach(panel => assert.equal(panel.innerHTML, '<strong>Live status</strong>'));
  context.document.hidden = true;
  await tick();
  assert.equal(requests.length, 2);
  console.log('Live status refreshes all panels, ignores unexpected responses and pauses while hidden.');
})();
