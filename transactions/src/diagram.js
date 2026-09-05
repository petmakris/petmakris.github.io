(function (root) {
  const E = typeof require === 'function' ? require('./engine.js') : root.TxPlay;

  function fmt(t) { return t >= 1 ? (Math.round(t * 10) / 10) + ' s' : Math.round(t * 1000) + ' ms'; }

  function toDiagramSpec(scenario, run, values) {
    values = values || {};
    const showUser = Number(E.slotValue(scenario, values, 'showUser') || 1);
    const events = run.timeline.filter(e => e.user === showUser);
    const actorId = a => (scenario.actorOf && scenario.actorOf[a]) || a;
    const steps = [], rails = [], stack = ['user'], open = {};
    const usedTones = new Set();
    const push = s => { if (s.tone) usedTones.add(s.tone); steps.push(s); return steps.length - 1; };
    const remoteReached = events.some(e => e.event === 'httpStart');
    let pendingPhase = null;
    const phase = () => { const p = pendingPhase; pendingPhase = null; return p || undefined; };

    for (const e of events) {
      const a = actorId(e.actor), d = e.detail, top = stack[stack.length - 1];
      switch (e.event) {
        case 'call': {
          pendingPhase = d.phase || pendingPhase;
          if (!d.viaProxy) {
            push({ from: a, to: a, arrow: 'self', label: `${d.method}()`, phase: phase(), tone: 'internal',
              sub: d.ignoredAnnotation ? 'self-invocation: the proxy is not consulted, its annotation is ignored' : 'self-invocation: the proxy is not consulted' });
          } else {
            const label = stack.length === 1 ? (scenario.entryLabel || 'request') : `${d.method}(…)`;
            push({ from: top, to: a, arrow: 'request', label, phase: phase(), tone: stack.length === 1 ? 'edge' : undefined,
              sub: d.propagation ? `proxy: ${d.propagation}` : 'proxy, no attribute' });
          }
          stack.push(a);
          break;
        }
        case 'txBegin': { const last = steps[steps.length - 1]; last.sub = (last.sub ? last.sub + ', ' : '') + 'starts a transaction'; break; }
        case 'txJoin': { const last = steps[steps.length - 1]; last.sub = (last.sub ? last.sub + ', ' : '') + 'joins'; break; }
        case 'connAcquired': {
          if (d.autoCommit) {
            push({ from: a, to: 'pool', arrow: 'request', label: 'read outside a transaction', sub: 'takes and returns a connection of its own', tone: 'internal',
              note: d.alsoHolding > 0 ? 'a second connection on this thread' : undefined });
          } else {
            const i = push({ from: a, to: 'pool', arrow: 'request', label: 'BEGIN', sub: 'the transaction takes a connection as it begins', tone: 'hot', phase: phase(),
              note: `connection ${d.conn.slice(1)} of ${d.size} taken` });
            open[d.conn] = { at: i, t: e.t, spansRemote: false };
          }
          break;
        }
        case 'dbRead': break;
        case 'permit': push({ from: a, to: 'bulkhead', arrow: 'request', label: 'acquire permit', tone: 'internal', note: `permit ${d.used} of ${d.size}` }); break;
        case 'refused': push({ from: 'bulkhead', to: a, arrow: 'event', label: 'BulkheadFullException', tone: 'hot', phase: phase(),
          sub: `${d.size} of ${d.size} permits held, maxWaitDuration ${d.after ? fmt(d.after) : '0'}`, note: d.after ? `refused after ${fmt(d.after)}` : 'refused at once' }); break;
        case 'suspend': push({ from: a, to: a, arrow: 'self', label: `${d.propagation}: transaction suspended`, tone: d.keepsConnection ? 'hot' : 'internal',
          sub: d.keepsConnection ? 'suspension is not release: the connection stays with it' : 'nothing to release' }); break;
        case 'resume': push({ from: a, to: a, arrow: 'self', label: 'transaction resumed', tone: 'internal' }); break;
        case 'httpStart': {
          for (const c of Object.values(open)) c.spansRemote = true;
          push({ from: a, to: 'remote', arrow: 'request', label: d.label || 'remote call', phase: phase(), tone: (d.holdingConnection || d.suspendedHolding) ? 'hot' : 'service',
            note: d.holdingConnection ? `${fmt(d.takes)}, holding ${d.holdingConnection}` : d.suspendedHolding ? `${fmt(d.takes)}, suspended transaction still holds its connection` : `${fmt(d.takes)}, holding nothing` });
          break;
        }
        case 'httpEnd': push({ from: 'remote', to: a, arrow: 'event', tone: d.status === 200 ? 'service' : 'hot',
          label: d.status === 200 ? 'answer' : d.status === 422 ? `refused (4xx): ${d.reason}` : 'failed (5xx)' }); break;
        case 'httpTimeout': push({ from: 'remote', to: a, arrow: 'event', tone: 'hot', label: d.kind === 'read' ? `no answer within read-timeout ${fmt(d.after)}` : `unreachable, connect-timeout ${fmt(d.after)}` }); break;
        case 'poolTimeout': push({ from: 'pool', to: a, arrow: 'event', tone: 'hot', label: `no free connection after ${fmt(d.waited)}`, note: 'connection-timeout' }); break;
        case 'rollbackOnly': push({ from: a, to: a, arrow: 'self', label: 'marked rollback-only', sub: d.exception, tone: 'hot' }); break;
        case 'exception': {
          stack.pop();
          const to = stack[stack.length - 1];
          if (to !== 'user') push({ from: a, to, arrow: 'event', label: d.name, tone: 'hot', sub: d.exceptionKind === 'checked' ? 'a checked exception' : undefined });
          break;
        }
        case 'rollback': case 'commit': {
          push({ from: a, to: 'pool', arrow: 'request', label: e.event.toUpperCase(), tone: 'good', phase: phase(),
            sub: e.event === 'rollback' ? 'the edit is discarded' : 'the edit is written' });
          break;
        }
        case 'connReleased': {
          if (d.tx && open[d.conn]) {
            const o = open[d.conn]; delete open[d.conn];
            steps[steps.length - 1].note = `connection ${d.conn.slice(1)} released`;
            rails.push({ actor: 'pool', from: o.at, to: steps.length - 1, tone: o.spansRemote ? 'hot' : 'good', label: fmt(e.t - o.t) });
          }
          break;
        }
        case 'compensation': push({ from: a, to: 'pool', arrow: 'request', label: 'compensation', sub: d.what, tone: 'internal' }); break;
        case 'detachedRead': push({ from: a, to: a, arrow: 'self', label: 'LazyInitializationException', sub: 'entity read outside a session', tone: 'hot' }); break;
        case 'response': {
          if (!remoteReached && scenario.actors.some(x => x.id === 'remote')) {
            const rf = run.frames.find(f => f.remote);
            if (rf) push({ from: actorId(rf.actor), to: 'remote', arrow: 'request', label: 'never reached', tone: 'dropped', sub: `the remote is not called for user ${showUser}` });
          }
          push({ from: a, to: 'user', arrow: 'event', label: d.status === 200 ? '200, saved' : `${d.status}, ${d.reason || d.error}`, tone: d.status === 200 ? 'good' : 'hot', note: `t = ${fmt(e.t)}` });
          break;
        }
      }
    }
    for (const r of rails) usedTones.add(r.tone);
    const LEGEND = { hot: 'holds a connection across a remote call, or a failure', good: 'released, or nothing lost', internal: 'inside the application',
      service: 'the remote', edge: 'the user', dropped: 'not reached' };
    const actors = scenario.actors.filter(x => x.id !== 'bulkhead' || steps.some(s => s.from === 'bulkhead' || s.to === 'bulkhead'));
    return { alt: `${scenario.title}: user ${showUser} of ${run.users}`, actors, steps, rails,
      legend: ['hot', 'good', 'internal', 'service', 'edge', 'dropped'].filter(t => usedTones.has(t)).map(t => ({ tone: t, label: LEGEND[t] })) };
  }

  const api = { toDiagramSpec, fmt };
  root.TxPlay = Object.assign(root.TxPlay || {}, api);
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
