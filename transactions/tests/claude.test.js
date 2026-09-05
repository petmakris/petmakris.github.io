const test = require('node:test');
const assert = require('node:assert/strict');
const scenario = require('../src/scenarios/01-edit-calls-out.js');
const { simulate } = require('../src/engine.js');
const { explain } = require('../src/explain.js');
const { buildPrompt } = require('../src/claude.js');

test('the prompt carries the code, the values, the timeline and the ground-truth instruction', () => {
  const run = simulate(scenario, {});
  const p = buildPrompt(scenario, run, {}, explain(scenario, run, {}, []));
  assert.match(p, /ClaimService/);
  assert.match(p, /"event": ?"refused"/);
  assert.match(p, /ground truth/i);
  assert.match(p, /do not assert any mechanism the timeline does not show/i);
  assert.ok(p.length < 60000);
});
