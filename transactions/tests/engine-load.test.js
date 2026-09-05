const test = require('node:test');
const assert = require('node:assert/strict');
const { simulate } = require('../src/engine.js');
const { scenario } = require('./engine.test.js');

const byUser = (run, u) => run.timeline.filter(e => e.user === u);
const ev = (run, u) => byUser(run, u).map(e => e.event);

test('with a bulkhead of 4, users 5 to 12 are refused at once and release their connection', () => {
  const run = simulate(scenario(), { users: 12, bulkhead: { name: 'fraud-check', permits: 4, wait: '0' } });
  assert.equal(run.summary.refused, 8);
  assert.equal(run.summary.peakConnections, 4 + 1, 'four held across the remote plus the fifth for an instant');
  const u5 = byUser(run, 5);
  assert.equal(u5.find(e => e.event === 'refused').detail.after, 0);
  assert.equal(u5.find(e => e.event === 'response').t, 0);
  assert.equal(u5.find(e => e.event === 'response').detail.status, 503);
  assert.ok(!ev(run, 5).includes('httpStart'), 'the remote is never called for a refused user');
  assert.equal(byUser(run, 1).find(e => e.event === 'response').t, 45);
  assert.equal(run.summary.poolTimeouts, 0);
});

test('without a bulkhead, ten users hold the pool and the last two time out after 30 s', () => {
  const run = simulate(scenario(), { users: 12 });
  assert.equal(run.summary.peakConnections, 10);
  assert.equal(run.summary.poolTimeouts, 2);
  const u11 = byUser(run, 11);
  assert.equal(u11.find(e => e.event === 'poolTimeout').t, 30);
  assert.equal(u11.find(e => e.event === 'response').detail.status, 500);
  assert.equal(byUser(run, 10).find(e => e.event === 'response').t, 45);
});

test('a bulkhead with a wait queues the fifth user, who holds its connection while it waits', () => {
  const run = simulate(scenario(), { users: 5, bulkhead: { name: 'fraud-check', permits: 4, wait: '60s' } });
  const u5 = byUser(run, 5);
  assert.equal(u5.find(e => e.event === 'permit').t, 45, 'granted when user 1 finishes');
  assert.equal(u5.find(e => e.event === 'connAcquired').t, 0, 'held from t = 0');
  assert.equal(u5.find(e => e.event === 'response').t, 90);
  assert.equal(run.summary.longestHold, 90);
});

test('a second entry that arrives later starves on the exhausted pool', () => {
  const s = scenario({ slots: { browsers: { kind: 'number', default: 2 } } });
  s.frames.push({ id: 'g1', actor: 'DashboardService', method: 'list', classTx: '@Transactional', methodTx: null,
    visibility: 'public', invoke: 'injected', dbTouch: true });
  s.entries.push({ root: 'g1', users: { slot: 'browsers' }, startAt: '1s' });
  const run = simulate(s, { users: 10 });
  const browser = byUser(run, 11);
  assert.equal(browser[0].t, 1);
  assert.equal(browser.find(e => e.event === 'poolTimeout').t, 31);
  assert.equal(run.summary.poolTimeouts, 2);
});
