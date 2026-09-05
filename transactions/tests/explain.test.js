const test = require('node:test');
const assert = require('node:assert/strict');
const scenario = require('../src/scenarios/01-edit-calls-out.js');
const { simulate } = require('../src/engine.js');
const { explain } = require('../src/explain.js');

test('the explanation names the hold, the refusal and the rollback with this run\'s numbers', () => {
  const run = simulate(scenario, {});
  const x = explain(scenario, run, {}, []);
  const text = x.paragraphs.join(' ');
  assert.match(text, /4 users? .*hold/i);
  assert.match(text, /45 s/);
  assert.match(text, /refuse/i);
  assert.match(text, /roll(s|ed)? back/i);
  assert.ok(x.chips.some(c => /refused/.test(c.text)));
  assert.ok(x.tryNext && x.tryNext.length > 20);
});

test('tryNext points at a discovery not yet found', () => {
  const run = simulate(scenario, {});
  const all = ['tx-owns-connection', 'self-invocation', 'refuse-not-queue', 'rollback-on-exception', 'suspension-not-release', 'pool-starvation', 'two-connections', 'checked-no-rollback', 'timeout-order'];
  assert.equal(explain(scenario, run, {}, all).tryNext, null);
});
