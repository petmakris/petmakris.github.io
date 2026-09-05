const test = require('node:test');
const assert = require('node:assert/strict');
const { simulate } = require('../src/engine.js');
const { detect } = require('../src/discoveries.js');
const { toDiagramSpec } = require('../src/diagram.js');
const { renderSequence } = require('../src/seqrender.js');
const S = ['01-edit-calls-out', '02-nightly-sweep', '03-create-compensation', '04-pool-exhaustion', '05-proxy-bypass', '06-suspension']
  .map(n => require(`../src/scenarios/${n}.js`));

test('every scenario declares its slots, renders and simulates every preset', () => {
  for (const s of S) {
    const refs = new Set();
    for (const f of s.files) for (const m of f.code.matchAll(/\{\{(\w+)\}\}/g)) refs.add(m[1]);
    for (const r of refs) assert.ok(s.slots[r], `${s.id}: slot ${r}`);
    for (const [name, p] of Object.entries(s.presets)) {
      const run = simulate(s, p);
      assert.ok(run.timeline.length > 0, `${s.id} ${name}`);
      assert.ok(renderSequence(toDiagramSpec(s, run, p)).startsWith('<svg'), `${s.id} ${name} renders`);
    }
    assert.ok(s.short && s.entryLabel, `${s.id} has short and entryLabel`);
  }
});

test('02 nightly sweep as designed holds nothing during the remote call; the class-level bug holds one', () => {
  const s = S[1];
  const ok = simulate(s, {});
  assert.ok(ok.timeline.every(e => e.event !== 'httpStart' || (!e.detail.holdingConnection && e.detail.suspendedHolding === 0)));
  assert.equal(ok.summary.longestHold < 1, true);
  const bug = simulate(s, s.presets['transactional check service']);
  assert.ok(bug.timeline.some(e => e.event === 'httpStart' && e.detail.holdingConnection));
});

test('03 create: a failing remote compensates by deleting the row committed first', () => {
  const s = S[2];
  const run = simulate(s, s.presets['the registry is down']);
  const ev = run.timeline.filter(e => e.user === 1).map(e => e.event);
  assert.ok(ev.indexOf('commit') < ev.indexOf('httpStart'), 'the row is committed before the remote is called');
  assert.ok(ev.includes('compensation'));
  assert.equal(run.timeline.find(e => e.event === 'response').detail.status, 503);
});

test('04 pool exhaustion: browsing users that never call out time out on the pool', () => {
  const run = simulate(S[3], {});
  assert.ok(run.summary.poolTimeouts >= 2);
  assert.ok(detect(run).includes('pool-starvation'));
});

test('05 proxy bypass: this.call ignores NOT_SUPPORTED, a self-injected call honours it', () => {
  const s = S[4];
  assert.ok(detect(simulate(s, {})).includes('self-invocation'));
  assert.ok(detect(simulate(s, s.presets['self-injected'])).includes('suspension-not-release'));
});

test('06 suspension: a read inside the suspended section takes a second connection', () => {
  const ids = detect(simulate(S[5], {}));
  assert.ok(ids.includes('suspension-not-release') && ids.includes('two-connections'));
});
