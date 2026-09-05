(function (root) {
  const T = typeof require === 'function' ? Object.assign({}, require('./engine.js'), require('./discoveries.js'), require('./diagram.js')) : root.TxPlay;

  function explain(scenario, run, values, foundIds) {
    values = values || {}; foundIds = foundIds || [];
    const showUser = Number(T.slotValue(scenario, values, 'showUser') || 1);
    const s = run.summary, tl = run.timeline, me = tl.filter(e => e.user === showUser);
    const paragraphs = [];
    const holders = new Set(tl.filter(e => e.event === 'httpStart' && e.detail.holdingConnection).map(e => e.user));
    const firstHttp = tl.find(e => e.event === 'httpStart');
    const takes = firstHttp ? T.fmt(firstHttp.detail.takes) : null;

    if (holders.size) {
      paragraphs.push(`${holders.size} user${holders.size > 1 ? 's' : ''} hold one connection each for the whole ${takes} the remote takes. ` +
        `The remote call runs inside the transaction started at the entry point, and a resource-local transaction keeps its connection from its first database touch until it commits or rolls back, so nothing releases it while the remote thinks.`);
    }
    const susp = tl.find(e => e.event === 'suspend' && e.detail.keepsConnection);
    if (susp) paragraphs.push(`${susp.detail.propagation} suspends the transaction around the remote call, but suspension is not release: the suspended transaction still owns its connection, so the pool sees no difference.`);
    const refused = me.find(e => e.event === 'refused');
    if (refused) paragraphs.push(`User ${showUser} arrives while all ${refused.detail.size} permits of the bulkhead are taken. ` +
      (refused.detail.after ? `It waits ${T.fmt(refused.detail.after)} holding its connection, then is refused.` : `The bulkhead refuses at once, because its wait is zero: a caller queuing for a permit would hold its connection while it waits.`) +
      ` The fallback throws, the transaction rolls back and the connection returns to the pool. Nothing is saved, and the remote is never called for this user.`);
    const pt = me.find(e => e.event === 'poolTimeout');
    if (pt) paragraphs.push(`User ${showUser} waits ${T.fmt(pt.detail.waited)} for a free connection and fails: all ${s.poolSize} connections are held by users still waiting on the remote. This request never called the remote itself.`);
    const rb = me.find(e => e.event === 'rollback' && e.detail.cause && e.detail.cause !== 'rollbackOnly');
    if (rb && !refused) paragraphs.push(`${rb.detail.cause} reaches the transaction that started the request, which rolls back; the edit and the verdict go together, and the connection is released after ${T.fmt(rb.t)}.`);
    const checkedCommit = me.find(e => e.event === 'exception' && e.detail.exceptionKind === 'checked') && me.find(e => e.event === 'commit');
    if (checkedCommit) paragraphs.push(`The failure is a checked exception and rollbackFor does not name it, so Spring commits the transaction anyway: the edit is saved despite the error the user is shown.`);
    const two = me.find(e => e.event === 'connAcquired' && e.detail.alsoHolding > 0);
    if (two) paragraphs.push(`A repository read inside the suspended section opens a connection of its own while the suspended transaction still holds one: two connections on one thread.`);
    const ok = me.find(e => e.event === 'response' && e.detail.status === 200);
    if (ok && !paragraphs.length) paragraphs.push(`User ${showUser} saves after ${T.fmt(ok.t)}: the remote answered and the transaction committed with the verdict.`);

    const chips = [];
    if (holders.size) chips.push({ text: `${holders.size} connection${holders.size > 1 ? 's' : ''} held ${T.fmt(s.longestHold)}`, tone: 'hot' });
    chips.push({ text: `${Math.max(0, s.poolSize - s.peakConnections)} of ${s.poolSize} free at peak`, tone: s.peakConnections >= s.poolSize ? 'hot' : 'ok' });
    if (s.refused) chips.push({ text: `${s.refused} users refused`, tone: 'warn' });
    if (s.poolTimeouts) chips.push({ text: `${s.poolTimeouts} pool timeouts`, tone: 'hot' });
    if (s.remoteTimeouts) chips.push({ text: `${s.remoteTimeouts} remote timeouts`, tone: 'hot' });
    chips.push({ text: `${s.saved} saved, ${s.failed} failed`, tone: s.failed ? 'warn' : 'ok' });

    const NUDGE = {
      'suspension-not-release': 'Try next: set the preset "self-injected" and watch NOT_SUPPORTED suspend the transaction without giving the connection back.',
      'pool-starvation': 'Try next: remove the @Bulkhead line. Users 11 and 12 then wait on the pool and fail after connection-timeout.',
      'two-connections': 'Try next: with the self-injected preset, add a repository read inside call(). The suspended section opens a second connection.',
      'checked-no-rollback': 'Try next: make runFraudCheck throw a checked exception and watch the transaction commit anyway.',
      'timeout-order': 'Try next: make the insurer take 90 s. The read-timeout of 60 s fires first, and the connection was held for all of it.',
      'refuse-not-queue': 'Try next: give the bulkhead a wait of 5s and watch refused users become waiting users that hold a connection.',
      'rollback-on-exception': 'Try next: the preset "the insurer refuses" shows a 422 rolling the edit back.',
      'self-invocation': 'Try next: put NOT_SUPPORTED on call() while it is still reached as this.call(), and see that nothing changes.',
      'tx-owns-connection': 'Try next: run as designed and follow connection 1 from BEGIN to COMMIT.',
    };
    const locked = (scenario.discoveries || []).filter(id => !foundIds.includes(id));
    const tryNext = locked.length ? NUDGE[locked[0]] : null;
    return { paragraphs, chips, tryNext };
  }

  const api = { explain };
  root.TxPlay = Object.assign(root.TxPlay || {}, api);
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
