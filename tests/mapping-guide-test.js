// Exercise navigation and browser-history restoration without a WebGUI server.
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const script = fs.readFileSync('src/web/settings.js', 'utf8');
function visit() {
  const events = {};
  const attributes = {};
  const content = { visible: true };
  const toggle = { setAttribute: (key, value) => attributes[key] = value,
    addEventListener: (key, fn) => events[key] = fn };
  const guide = { dataset: {}, querySelector: selector => selector === '#nas-mapping-content' ? content : toggle };
  const window = { addEventListener: (key, fn) => events[key] = fn };
  const context = { document: { querySelectorAll: () => [], querySelector: () => guide }, window,
    $: () => ({ stop() { return this; }, hide() { content.visible = false; }, toggle() { content.visible = !content.visible; } }) };
  vm.runInNewContext(script, context);
  const checkClosed = () => { assert.equal(content.visible, false); assert.equal(attributes['aria-expanded'], 'false'); assert.equal(toggle.textContent, 'Show guide'); };
  checkClosed();
  events.click();
  assert.equal(content.visible, true);
  assert.equal(attributes['aria-expanded'], 'true');
  events.pageshow();
  checkClosed();
  events.click();
  assert.equal(content.visible, true);
}
visit();
visit(); // A new page visit must discard the previous open state.
console.log('Guide starts closed on each visit and resets after browser-history restoration.');
