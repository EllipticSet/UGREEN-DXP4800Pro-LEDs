// Exercise the collapsible section toggles and night-mode fields without a WebGUI server.
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const script = fs.readFileSync('src/web/settings.js', 'utf8');
function visit(initiallyOpen) {
  const events = {};
  const attributes = { 'aria-expanded': String(initiallyOpen) };
  const content = { visible: initiallyOpen };
  const toggle = { getAttribute: key => attributes[key], setAttribute: (key, value) => attributes[key] = value,
    addEventListener: (key, fn) => events[key] = fn };
  const section = { dataset: {}, querySelector: selector => selector === '.nas-collapsible-content' ? content : toggle };
  const window = { addEventListener: (key, fn) => events[key] = fn };
  const context = { document: { querySelectorAll: selector => selector === '.nas-collapsible' ? [section, section] : [], querySelector: () => null }, window,
    $: () => ({ stop() { return this; }, hide() { content.visible = false; }, show() { content.visible = true; }, toggle() { content.visible = !content.visible; } }) };
  vm.runInNewContext(script, context);
  const checkState = open => {
    assert.equal(content.visible, open);
    assert.equal(attributes['aria-expanded'], String(open));
    assert.equal(toggle.textContent, open ? 'Hide' : 'Show');
  };
  checkState(initiallyOpen);
  events.click();
  checkState(!initiallyOpen);
  events.pageshow();
  checkState(initiallyOpen);
}
visit(false);
visit(false); // A new page visit must discard the previous open state.
visit(true); // A mapping error opens its section.
console.log('Collapsible sections start closed, open on errors, initialize once and reset after browser-history restoration.');

const help = { hidden: false, matches: selector => selector === 'blockquote.inline_help' };
const fields = [{ hidden: true, nextElementSibling: help }, { hidden: true, nextElementSibling: null }];
let change;
const mode = { value: '0', dataset: {}, addEventListener: (key, fn) => { assert.equal(key, 'change'); change = fn; } };
vm.runInNewContext(script, { window: {}, document: {
  querySelector: selector => selector === 'select[name="NIGHT_MODE"]' ? mode : null,
  querySelectorAll: selector => selector === '[data-night-field]' ? fields : [] } });
assert.ok(fields.every(field => field.hidden) && help.hidden);
mode.value = '1';
change();
assert.ok(fields.every(field => !field.hidden) && !help.hidden);
mode.value = '0';
change();
assert.ok(fields.every(field => field.hidden) && help.hidden);
console.log('Night mode fields and their help are shown only while night mode is enabled.');
