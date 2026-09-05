const test = require('node:test');
const assert = require('node:assert/strict');
const { renderCode, displayValue } = require('../src/template.js');
const scenario = require('../src/scenarios/01-edit-calls-out.js');

test('renderCode replaces each slot with a control and escapes the rest', () => {
  const html = renderCode(scenario.files[1], scenario, {}, new Set(['bulkhead']));
  assert.ok(html.includes('data-slot="bulkhead"'));
  assert.ok(html.includes('class="tg changed"'), 'changed slot is marked');
  assert.ok(html.includes('<span class="kw">public</span>'));
  assert.ok(!html.includes('{{'), 'no raw slot markers');
  assert.ok(!/<(?!\/?span|\/?code)/.test(html.replace(/<span[^>]*>|<\/span>/g, '')), 'only spans emitted');
});

test('displayValue renders annotations, invocations and bulkheads as code', () => {
  assert.equal(displayValue({ kind: 'annotation' }, null), '// no annotation');
  assert.equal(displayValue({ kind: 'annotation' }, '@Transactional'), '@Transactional');
  assert.equal(displayValue({ kind: 'annotation' }, 'NOT_SUPPORTED'), '@Transactional(propagation = NOT_SUPPORTED)');
  assert.equal(displayValue({ kind: 'invocation', labels: { this: 'this', injected: 'fraudCheck', self: 'self' } }, 'injected'), 'fraudCheck');
  assert.equal(displayValue({ kind: 'bulkhead' }, { name: 'fraud-check', permits: 4, wait: '0' }), '@Bulkhead(name = "fraud-check", maxConcurrentCalls = 4, maxWaitDuration = 0)');
  assert.equal(displayValue({ kind: 'bulkhead' }, null), '// no bulkhead');
  assert.equal(displayValue({ kind: 'external' }, { takes: '45s', answers: 'late' }), 'takes 45s, answers late');
});
