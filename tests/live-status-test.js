// Live state refresh sets text labels on every tab from one request and keeps old text on errors.
const assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm');
const fields = ['monitor', 'lan', 'bay1'].map(live => ({ dataset: { live }, textContent: 'old' }));
let tick, response = { ok: true, json: async () => ({ monitor: 'LED monitor running', lan: '<b>Internet</b>', bay1: 'sda · standby' }) };
const requests = [];
const context = {
  window: {},
  setInterval: (fn, ms) => { assert.equal(ms, 5000); tick = fn; },
  fetch: async (url, options) => { requests.push([url, options.cache]); return response; },
  document: { hidden: false, querySelectorAll: selector => selector === '[data-live]' ? fields : [], querySelector: () => null },
};
vm.runInNewContext(fs.readFileSync('src/web/settings.js', 'utf8'), context);
(async () => {
  await tick();
  assert.deepEqual(requests, [['/plugins/UGREEN-DXP4800Pro-LEDs/status.php', 'no-store']]);
  assert.deepEqual(fields.map(field => field.textContent), ['LED monitor running', '<b>Internet</b>', 'sda · standby']);
  response = { ok: true, json: async () => { throw new SyntaxError('login page'); } };
  await tick();
  assert.equal(fields[0].textContent, 'LED monitor running');
  context.document.hidden = true;
  await tick();
  assert.equal(requests.length, 2);
  console.log('Live state refreshes text labels on all tabs, ignores unexpected responses and pauses while hidden.');
})();
