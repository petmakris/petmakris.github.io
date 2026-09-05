const test = require('node:test');
const assert = require('node:assert/strict');
const scenario = require('../src/scenarios/01-edit-calls-out.js');
const { simulate } = require('../src/engine.js');

test('scenario 1 declares every slot its code and frames reference', () => {
  const refs = new Set();
  for (const f of scenario.files) for (const m of f.code.matchAll(/\{\{(\w+)\}\}/g)) refs.add(m[1]);
  JSON.stringify(scenario.frames, (k, v) => { if (v && v.slot) refs.add(v.slot); return v; });
  JSON.stringify(scenario.config, (k, v) => { if (v && v.slot) refs.add(v.slot); return v; });
  for (const r of refs) assert.ok(scenario.slots[r], 'slot declared: ' + r);
  for (const p of Object.values(scenario.presets)) for (const k of Object.keys(p)) assert.ok(scenario.slots[k], 'preset slot: ' + k);
});

test('scenario 1 as designed: user 5 of 12 is refused, users 1 to 4 hold for 45 s', () => {
  const run = simulate(scenario, {});
  assert.equal(run.users, 12);
  assert.equal(run.summary.refused, 8);
  assert.equal(run.summary.longestHold, 45);
  assert.equal(run.summary.saved, 4);
});

test('scenario 1 preset "no ceiling": pool exhaustion', () => {
  const run = simulate(scenario, scenario.presets['no ceiling']);
  assert.equal(run.summary.poolTimeouts, 2);
  assert.equal(run.summary.peakConnections, 10);
});

test('scenario 1 preset "self-injected": the suspended transaction keeps its connection', () => {
  const run = simulate(scenario, { ...scenario.presets['self-injected'], users: 1 });
  const http = run.timeline.find(e => e.event === 'httpStart');
  assert.equal(http.detail.holdingConnection, null);
  assert.equal(http.detail.suspendedHolding, 1);
});
