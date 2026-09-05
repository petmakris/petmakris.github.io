(function (root) {
  const has = (run, ev, pred) => run.timeline.some(e => e.event === ev && (!pred || pred(e)));
  const DISCOVERIES = [
    { id: 'tx-owns-connection', title: 'A transaction owns its connection until it ends', hint: 'taken at BEGIN, returned at commit or rollback, whatever happens in between',
      test: run => run.timeline.some(e => e.event === 'connAcquired' && !e.detail.autoCommit && run.timeline.some(r => r.event === 'connReleased' && r.detail.conn === e.detail.conn && r.t > e.t)) },
    { id: 'self-invocation', title: 'Self-invocation never reaches the proxy', hint: 'this.call() ignores every annotation on call',
      test: run => has(run, 'call', e => !e.detail.viaProxy && e.detail.ignoredAnnotation) },
    { id: 'refuse-not-queue', title: 'Refuse rather than queue', hint: 'a caller waiting for a permit holds its connection while it waits',
      test: run => has(run, 'refused', e => e.detail.after === 0) },
    { id: 'rollback-on-exception', title: 'A failure inside the transaction rolls the edit back', hint: 'the exception reaches the outer @Transactional',
      test: run => has(run, 'rollback', e => !!e.detail.cause) },
    { id: 'suspension-not-release', title: 'Suspension is not release', hint: 'NOT_SUPPORTED through the proxy keeps the connection',
      test: run => has(run, 'suspend', e => e.detail.keepsConnection) && has(run, 'httpStart', e => e.detail.suspendedHolding > 0) },
    { id: 'pool-starvation', title: 'Pool exhaustion starves unrelated requests', hint: 'connection-timeout fires on a thread that never called out',
      test: run => has(run, 'poolTimeout') },
    { id: 'two-connections', title: 'Two connections on one thread', hint: 'a repository read inside a suspended section',
      test: run => has(run, 'connAcquired', e => e.detail.alsoHolding > 0) },
    { id: 'checked-no-rollback', title: 'Checked exceptions do not roll back', hint: 'unless rollbackFor names them',
      test: run => run.timeline.some(e => e.event === 'exception' && e.detail.exceptionKind === 'checked' && run.timeline.some(c => c.event === 'commit' && c.user === e.user && c.t >= e.t)) },
    { id: 'timeout-order', title: 'Which timeout fires first', hint: 'read-timeout, connection-timeout and the bulkhead wait race each other',
      test: run => has(run, 'httpTimeout') },
  ];
  function detect(run) { return DISCOVERIES.filter(d => d.test(run)).map(d => d.id); }
  const api = { DISCOVERIES, detect };
  root.TxPlay = Object.assign(root.TxPlay || {}, api);
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
