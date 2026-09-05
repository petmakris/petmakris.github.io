const test = require('node:test');
const assert = require('node:assert/strict');
const { simulate } = require('../src/engine.js');

function scenario(overrides = {}) {
  return {
    slots: {
      classTx1: { kind: 'annotation', default: '@Transactional' },
      classTx2: { kind: 'annotation', default: '@Transactional' },
      methodTx3: { kind: 'annotation', default: null },
      invoke2: { kind: 'invocation', default: 'injected' },
      invoke3: { kind: 'invocation', default: 'this' },
      visibility3: { kind: 'visibility', default: 'private' },
      bulkhead: { kind: 'bulkhead', default: null },
      remote: { kind: 'external', default: { takes: '45s', answers: 'late' } },
      throws: { kind: 'exception', default: null },
      poolSize: { kind: 'number', default: 10 },
      connectionTimeout: { kind: 'number', default: '30s' },
      connectTimeout: { kind: 'number', default: '10s' },
      readTimeout: { kind: 'number', default: '60s' },
      users: { kind: 'number', default: 1 },
      showUser: { kind: 'number', default: 1 },
      ...overrides.slots,
    },
    config: { poolSize: { slot: 'poolSize' }, connectionTimeout: { slot: 'connectionTimeout' },
      connectTimeout: { slot: 'connectTimeout' }, readTimeout: { slot: 'readTimeout' }, osiv: false },
    entries: [{ root: 'f1', users: { slot: 'users' }, startAt: 0 }],
    frames: [
      { id: 'f1', actor: 'ClaimService', method: 'updateClaim', classTx: { slot: 'classTx1' }, methodTx: null,
        visibility: 'public', invoke: 'injected', dbTouch: true, calls: ['f2'] },
      { id: 'f2', actor: 'FraudCheckService', method: 'runFraudCheck', classTx: { slot: 'classTx2' }, methodTx: null,
        visibility: 'public', invoke: { slot: 'invoke2' }, bulkhead: { slot: 'bulkhead' }, calls: ['f3'], throws: { slot: 'throws' } },
      { id: 'f3', actor: 'FraudCheckService', method: 'call', classTx: { slot: 'classTx2' }, methodTx: { slot: 'methodTx3' },
        visibility: { slot: 'visibility3' }, invoke: { slot: 'invoke3' }, remote: { slot: 'remote' } },
    ],
  };
}

const events = (run, user) => run.timeline.filter(e => e.user === user).map(e => e.event);
const find = (run, ev, user = 1) => run.timeline.find(e => e.user === user && e.event === ev);

test('the remote call runs inside the transaction and holds its connection for 45 s', () => {
  const run = simulate(scenario(), {});
  assert.deepEqual(events(run, 1), ['call', 'txBegin', 'connAcquired', 'call', 'txJoin', 'call', 'httpStart', 'httpEnd', 'commit', 'connReleased', 'response']);
  assert.equal(find(run, 'httpStart').detail.holdingConnection, 'c1');
  assert.equal(find(run, 'connReleased').t, 45);
  assert.equal(find(run, 'response').detail.status, 200);
});

test('a self-invoked call ignores its own NOT_SUPPORTED annotation', () => {
  const run = simulate(scenario(), { methodTx3: 'NOT_SUPPORTED' });
  assert.ok(!events(run, 1).includes('suspend'));
  const call3 = run.timeline.filter(e => e.event === 'call')[2];
  assert.equal(call3.detail.viaProxy, false);
  assert.equal(call3.detail.ignoredAnnotation, true);
});

test('NOT_SUPPORTED through the proxy suspends but keeps the connection', () => {
  const run = simulate(scenario(), { methodTx3: 'NOT_SUPPORTED', invoke3: 'self', visibility3: 'public' });
  assert.deepEqual(events(run, 1), ['call', 'txBegin', 'connAcquired', 'call', 'txJoin', 'call', 'suspend', 'httpStart', 'httpEnd', 'resume', 'commit', 'connReleased', 'response']);
  assert.equal(find(run, 'suspend').detail.keepsConnection, true);
  assert.equal(find(run, 'httpStart').detail.holdingConnection, null);
  assert.equal(find(run, 'httpStart').detail.suspendedHolding, 1);
  assert.equal(find(run, 'connReleased').t, 45);
});

test('a refusal from the remote rolls the edit back and releases the connection', () => {
  const run = simulate(scenario(), { remote: { takes: '2s', answers: '4xx', reason: 'no policy' } });
  assert.deepEqual(events(run, 1), ['call', 'txBegin', 'connAcquired', 'call', 'txJoin', 'call', 'httpStart', 'httpEnd', 'exception', 'rollbackOnly', 'exception', 'rollback', 'connReleased', 'exception', 'response']);
  assert.equal(find(run, 'response').detail.status, 422);
  assert.equal(find(run, 'connReleased').t, 2);
});

test('a read timeout on the remote is an unavailability, not a refusal', () => {
  const run = simulate(scenario(), { remote: { takes: '90s', answers: 'late' } });
  assert.equal(find(run, 'httpTimeout').detail.after, 60);
  assert.equal(find(run, 'response').detail.status, 503);
  assert.equal(find(run, 'connReleased').t, 60);
});

test('a checked exception does not roll back unless rollbackFor names it', () => {
  const checked = simulate(scenario(), { throws: { name: 'AuditFailure', kind: 'checked' } });
  assert.ok(events(checked, 1).includes('commit'));
  assert.equal(find(checked, 'response').detail.status, 500);
  const named = simulate(scenario(), { throws: { name: 'AuditFailure', kind: 'checked' }, classTx1: { propagation: 'REQUIRED', rollbackFor: ['AuditFailure'] } });
  assert.ok(events(named, 1).includes('rollback'));
});

test('a repository read inside a suspended section takes a second connection', () => {
  const s = scenario();
  s.frames[2].dbTouch = true;
  const run = simulate(s, { methodTx3: 'NOT_SUPPORTED', invoke3: 'self', visibility3: 'public' });
  const second = run.timeline.filter(e => e.event === 'connAcquired')[1];
  assert.equal(second.detail.autoCommit, true);
  assert.equal(second.detail.alsoHolding, 1);
});

module.exports = { scenario };
