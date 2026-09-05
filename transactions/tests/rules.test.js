const test = require('node:test');
const assert = require('node:assert/strict');
const R = require('../src/rules.js');

test('seconds parses durations', () => {
  assert.equal(R.seconds('45s'), 45);
  assert.equal(R.seconds('500ms'), 0.5);
  assert.equal(R.seconds('2m'), 120);
  assert.equal(R.seconds(30), 30);
  assert.equal(R.seconds('0'), 0);
  assert.equal(R.seconds(null), 0);
});

test('normalizeTx reads the propagation out of an annotation string', () => {
  assert.equal(R.normalizeTx(null), null);
  assert.deepEqual(R.normalizeTx('@Transactional'), { propagation: 'REQUIRED', rollbackFor: [] });
  assert.deepEqual(R.normalizeTx('@Transactional(propagation = NOT_SUPPORTED)'), { propagation: 'NOT_SUPPORTED', rollbackFor: [] });
  assert.deepEqual(R.normalizeTx({ propagation: 'REQUIRES_NEW', rollbackFor: ['Checked'] }), { propagation: 'REQUIRES_NEW', rollbackFor: ['Checked'] });
});

test('a private method or a this-call never reaches the proxy', () => {
  assert.equal(R.reachesProxy({ invoke: 'injected', visibility: 'public' }), true);
  assert.equal(R.reachesProxy({ invoke: 'injected', visibility: 'package' }), true);
  assert.equal(R.reachesProxy({ invoke: 'injected', visibility: 'private' }), false);
  assert.equal(R.reachesProxy({ invoke: 'this', visibility: 'public' }), false);
});

test('effectiveTx is the method attribute, else the class attribute, else none; nothing without the proxy', () => {
  assert.deepEqual(R.effectiveTx({ invoke: 'injected', visibility: 'public', classTx: '@Transactional', methodTx: null }).propagation, 'REQUIRED');
  assert.equal(R.effectiveTx({ invoke: 'injected', visibility: 'public', classTx: '@Transactional', methodTx: 'NOT_SUPPORTED' }).propagation, 'NOT_SUPPORTED');
  assert.equal(R.effectiveTx({ invoke: 'this', visibility: 'public', classTx: '@Transactional', methodTx: 'NOT_SUPPORTED' }), null);
  assert.equal(R.effectiveTx({ invoke: 'injected', visibility: 'public', classTx: null, methodTx: null }), null);
});

test('enter follows Spring propagation', () => {
  const tx = { id: 't1' };
  assert.equal(R.enter('REQUIRED', null).action, 'start');
  assert.equal(R.enter('REQUIRED', tx).action, 'join');
  assert.equal(R.enter('REQUIRES_NEW', null).action, 'start');
  assert.equal(R.enter('REQUIRES_NEW', tx).action, 'suspendStart');
  assert.equal(R.enter('NOT_SUPPORTED', null).action, 'none');
  assert.equal(R.enter('NOT_SUPPORTED', tx).action, 'suspend');
  assert.equal(R.enter('SUPPORTS', null).action, 'none');
  assert.equal(R.enter('SUPPORTS', tx).action, 'join');
  assert.equal(R.enter('NEVER', tx).action, 'throw');
  assert.equal(R.enter('NEVER', null).action, 'none');
  assert.equal(R.enter('MANDATORY', null).action, 'throw');
  assert.equal(R.enter('MANDATORY', tx).action, 'join');
});

test('runtime exceptions roll back, checked ones only when rollbackFor names them', () => {
  const attr = { propagation: 'REQUIRED', rollbackFor: ['AuditFailure'] };
  assert.equal(R.rollsBack({ kind: 'IllegalStateException', exceptionKind: 'runtime' }, attr), true);
  assert.equal(R.rollsBack({ kind: 'IOException', exceptionKind: 'checked' }, attr), false);
  assert.equal(R.rollsBack({ kind: 'AuditFailure', exceptionKind: 'checked' }, attr), true);
});
