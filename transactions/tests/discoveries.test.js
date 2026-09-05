const test = require('node:test');
const assert = require('node:assert/strict');
const scenario = require('../src/scenarios/01-edit-calls-out.js');
const { simulate } = require('../src/engine.js');
const { detect, DISCOVERIES } = require('../src/discoveries.js');

test('nine discoveries exist with unique ids', () => {
  assert.equal(DISCOVERIES.length, 9);
  assert.equal(new Set(DISCOVERIES.map(d => d.id)).size, 9);
});

test('as designed unlocks the four the mockup shows found', () => {
  const ids = detect(simulate(scenario, {}));
  for (const id of ['tx-owns-connection', 'self-invocation', 'refuse-not-queue', 'rollback-on-exception']) assert.ok(ids.includes(id), id);
  assert.ok(!ids.includes('suspension-not-release'));
  assert.ok(!ids.includes('pool-starvation'));
});

test('no ceiling unlocks pool starvation; self-injected unlocks suspension is not release', () => {
  assert.ok(detect(simulate(scenario, scenario.presets['no ceiling'])).includes('pool-starvation'));
  assert.ok(detect(simulate(scenario, scenario.presets['self-injected'])).includes('suspension-not-release'));
});

test('a checked exception that commits unlocks checked-no-rollback', () => {
  const s = JSON.parse(JSON.stringify(scenario));
  s.frames[1].throws = { name: 'AuditFailure', kind: 'checked' };
  assert.ok(detect(simulate(s, { users: 1 })).includes('checked-no-rollback'));
});
