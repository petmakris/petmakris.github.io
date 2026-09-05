const test = require('node:test');
const assert = require('node:assert/strict');
const scenario = require('../src/scenarios/01-edit-calls-out.js');
const { simulate } = require('../src/engine.js');
const { toDiagramSpec } = require('../src/diagram.js');
const { renderSequence } = require('../src/seqrender.js');

test('user 5 refused: a short green rail, a refused step, a dropped remote step, a 503', () => {
  const run = simulate(scenario, {});
  const spec = toDiagramSpec(scenario, run, {});
  const labels = spec.steps.map(s => s.label);
  assert.ok(labels.includes('PUT /claims/{id}'));
  assert.ok(labels.some(l => /BulkheadFullException/.test(l)));
  assert.ok(labels.includes('ROLLBACK'));
  const dropped = spec.steps.find(s => s.tone === 'dropped');
  assert.equal(dropped.to, 'remote');
  assert.deepEqual(spec.rails.map(r => r.tone), ['good']);
  assert.match(spec.steps[spec.steps.length - 1].label, /^503/);
  assert.ok(spec.legend.some(l => l.tone === 'dropped'));
  assert.ok(renderSequence(spec).startsWith('<svg'));
});

test('user 1 saved: a red rail spanning the remote call, a 200 after 45 s', () => {
  const run = simulate(scenario, { showUser: 1 });
  const spec = toDiagramSpec(scenario, run, { showUser: 1 });
  const http = spec.steps.find(s => s.to === 'remote' && s.arrow === 'request');
  assert.equal(http.tone, 'hot');
  assert.match(http.note, /holding c1/);
  assert.deepEqual(spec.rails.map(r => r.tone), ['hot']);
  assert.match(spec.rails[0].label, /45 s/);
  assert.match(spec.steps[spec.steps.length - 1].note, /t = 45/);
  assert.ok(spec.steps.some(s => s.phase === 'the save arrives'));
});

test('a self-invocation is drawn as a self arrow that says the proxy is not consulted', () => {
  const run = simulate(scenario, { showUser: 1, methodTx3: 'NOT_SUPPORTED' });
  const spec = toDiagramSpec(scenario, run, { showUser: 1, methodTx3: 'NOT_SUPPORTED' });
  const self = spec.steps.find(s => s.arrow === 'self' && /call\(/.test(s.label));
  assert.match(self.sub, /proxy is not consulted/);
});
