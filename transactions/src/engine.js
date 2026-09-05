(function (root) {
  const R = typeof require === 'function' ? require('./rules.js') : root.TxPlay;

  // ---- slot resolution ----------------------------------------------------
  function slotValue(scenario, values, name) {
    const slot = scenario.slots[name];
    if (!slot) throw new Error('unknown slot ' + name);
    return Object.prototype.hasOwnProperty.call(values, name) ? values[name] : slot.default;
  }
  function resolve(node, scenario, values) {
    if (Array.isArray(node)) return node.map(n => resolve(n, scenario, values));
    if (node && typeof node === 'object') {
      if (node.slot) {
        const v = slotValue(scenario, values, node.slot);
        return resolve(node.field ? (v == null ? null : v[node.field]) : v, scenario, values);
      }
      const out = {};
      for (const k of Object.keys(node)) out[k] = resolve(node[k], scenario, values);
      return out;
    }
    return node;
  }
  function resolveFrames(scenario, values) { return resolve(scenario.frames, scenario, values); }
  function resolveConfig(scenario, values) {
    const c = resolve(scenario.config, scenario, values);
    return { poolSize: Number(c.poolSize), connectionTimeout: R.seconds(c.connectionTimeout),
      connectTimeout: R.seconds(c.connectTimeout), readTimeout: R.seconds(c.readTimeout), osiv: !!c.osiv };
  }

  // ---- discrete-event scheduler and resources -----------------------------
  class Scheduler {
    constructor() { this.now = 0; this.queue = []; this.seq = 0; }
    at(t, fn) { this.queue.push({ t, seq: this.seq++, fn }); }
    run() {
      while (this.queue.length) {
        this.queue.sort((a, b) => a.t - b.t || a.seq - b.seq);
        const e = this.queue.shift(); this.now = e.t; e.fn();
      }
    }
  }
  class Resource {
    constructor(name, size) { this.name = name; this.size = size; this.free = size; this.waiters = []; }
  }
  // ops yielded by a user program: (sched, resume) => void
  function acquire(res, timeout) {
    return (sched, resume) => {
      if (res.free > 0) { res.free--; resume('ok'); return; }
      if (timeout <= 0) { resume('refused'); return; }
      const w = { resume, done: false };
      res.waiters.push(w);
      sched.at(sched.now + timeout, () => {
        if (w.done) return;
        w.done = true; res.waiters.splice(res.waiters.indexOf(w), 1); resume('timeout');
      });
    };
  }
  function release(res) {
    return (sched, resume) => {
      const w = res.waiters.shift();
      if (w) { w.done = true; sched.at(sched.now, () => w.resume('ok')); }
      else res.free++;
      resume();
    };
  }
  function sleep(d) { return (sched, resume) => sched.at(sched.now + d, () => resume()); }
  function drive(sched, gen, value) {
    const r = gen.next(value);
    if (r.done) return;
    r.value(sched, v => drive(sched, gen, v));
  }

  function fail(name, status, reason, kind) {
    const e = new Error(name);
    e.kind = name; e.status = status; e.reason = reason; e.exceptionKind = kind || 'runtime';
    return e;
  }

  // ---- one user's request ---------------------------------------------------
  function* userProgram(u, rootFrame, frames, cfg, res, emit) {
    const ctx = { user: u, active: null, suspended: [], txSeq: 0, held: 0 };
    try {
      yield* runFrame(rootFrame, ctx, cfg, res, emit, frames);
      emit(u, rootFrame.actor, 'response', { status: 200 });
    } catch (e) {
      emit(u, rootFrame.actor, 'response', { status: e.status || 500, error: e.kind, reason: e.reason });
    }
  }

  function* runFrame(f, ctx, cfg, res, emit, frames) {
    const u = ctx.user;
    const attr = R.effectiveTx(f);
    const reach = R.reachesProxy(f);
    emit(u, f.actor, 'call', { frame: f.id, method: f.method, viaProxy: reach,
      propagation: attr ? attr.propagation : null,
      ignoredAnnotation: !reach && !!(f.methodTx || f.classTx), phase: f.phase || null });
    const entry = attr ? R.enter(attr.propagation, ctx.active) : { action: 'none' };
    if (entry.action === 'throw') throw fail('IllegalTransactionStateException', 500, entry.reason);

    let started = null, suspendedHere = false, permitHeld = false;
    if (entry.action === 'suspend' || entry.action === 'suspendStart') {
      ctx.suspended.push(ctx.active);
      emit(u, f.actor, 'suspend', { tx: ctx.active.id, keepsConnection: !!ctx.active.conn, propagation: attr.propagation });
      ctx.active = null; suspendedHere = true;
    }
    if (entry.action === 'start' || entry.action === 'suspendStart') {
      started = { id: 't' + (++ctx.txSeq) + '.' + u, conn: null, rollbackOnly: false, attr, frame: f.id };
      ctx.active = started;
      emit(u, f.actor, 'txBegin', { tx: started.id, propagation: attr.propagation });
    } else if (entry.action === 'join') {
      emit(u, f.actor, 'txJoin', { tx: ctx.active.id, propagation: attr.propagation });
    }
    const bulk = f.bulkhead ? res.bulkheads[f.bulkhead.name] : null;

    try {
      if (started) yield* takeConnection(f, ctx, cfg, res, emit, started);
      if (f.dbTouch) yield* dbTouch(f, ctx, cfg, res, emit);
      if (bulk) {
        const got = yield acquire(bulk, R.seconds(f.bulkhead.wait));
        if (got === 'ok') { permitHeld = true; emit(u, f.actor, 'permit', { name: bulk.name, used: bulk.size - bulk.free, size: bulk.size }); }
        else {
          emit(u, f.actor, 'refused', { name: bulk.name, after: got === 'timeout' ? R.seconds(f.bulkhead.wait) : 0, size: bulk.size });
          throw fail(f.bulkhead.fallback || 'BulkheadFullException', 503, 'refused by the ceiling');
        }
      }
      for (const id of f.calls || []) {
        const child = frames.find(x => x.id === id);
        if (!child) throw new Error('unknown frame ' + id);
        yield* runFrame(child, ctx, cfg, res, emit, frames);
      }
      if (f.remote) yield* remoteCall(f, ctx, cfg, emit);
      if (f.throws) throw fail(f.throws.name, f.throws.status || 500, 'thrown by ' + f.method, f.throws.kind);
      if (permitHeld) { permitHeld = false; yield release(bulk); }
      if (started) {
        const s = started; started = null;
        const unexpected = yield* endTx(f, ctx, s, null, res, emit);
        if (suspendedHere) { suspendedHere = false; ctx.active = ctx.suspended.pop(); emit(u, f.actor, 'resume', { tx: ctx.active ? ctx.active.id : null }); }
        if (unexpected) throw fail('UnexpectedRollbackException', 500, 'the transaction was marked rollback-only');
      } else if (suspendedHere) {
        suspendedHere = false; ctx.active = ctx.suspended.pop();
        emit(u, f.actor, 'resume', { tx: ctx.active ? ctx.active.id : null });
      }
    } catch (e) {
      if (permitHeld) { permitHeld = false; yield release(bulk); }
      if (started) { const s = started; started = null; yield* endTx(f, ctx, s, e, res, emit); }
      else if (ctx.active && attr && R.rollsBack(e, attr) && !ctx.active.rollbackOnly) {
        ctx.active.rollbackOnly = true;
        emit(u, f.actor, 'rollbackOnly', { tx: ctx.active.id, exception: e.kind });
      }
      if (suspendedHere) { suspendedHere = false; ctx.active = ctx.suspended.pop(); emit(u, f.actor, 'resume', { tx: ctx.active ? ctx.active.id : null }); }
      if (f.compensation) yield* compensate(f, ctx, cfg, res, emit);
      emit(u, f.actor, 'exception', { frame: f.id, name: e.kind, status: e.status, exceptionKind: e.exceptionKind, reason: e.reason });
      throw e;
    }
  }

  // Hibernate acquires the JDBC connection when a resource-local transaction begins, to switch off
  // auto-commit; measured on the real stack: a transaction with no database work still held one.
  function* takeConnection(f, ctx, cfg, res, emit, tx) {
    const u = ctx.user;
    const got = yield acquire(res.pool, cfg.connectionTimeout);
    if (got !== 'ok') {
      emit(u, f.actor, 'poolTimeout', { waited: cfg.connectionTimeout, alsoHolding: ctx.held });
      throw fail('SQLTransientConnectionException', 500, 'no connection within connection-timeout');
    }
    const conn = 'c' + (++res.connSeq);
    tx.conn = conn; ctx.held++;
    emit(u, f.actor, 'connAcquired', { tx: tx.id, conn, free: res.pool.free, size: res.pool.size, alsoHolding: ctx.held - 1 });
  }

  function* dbTouch(f, ctx, cfg, res, emit) {
    const u = ctx.user, tx = ctx.active;
    if (tx) { emit(u, f.actor, 'dbRead', { tx: tx.id, conn: tx.conn }); return; }
    if (f.lazyRead && !cfg.osiv) {
      emit(u, f.actor, 'detachedRead', { frame: f.id });
      throw fail('LazyInitializationException', 500, 'lazy association touched outside a session');
    }
    const got = yield acquire(res.pool, cfg.connectionTimeout);
    if (got !== 'ok') {
      emit(u, f.actor, 'poolTimeout', { waited: cfg.connectionTimeout, alsoHolding: ctx.held });
      throw fail('SQLTransientConnectionException', 500, 'no connection within connection-timeout');
    }
    const conn = 'c' + (++res.connSeq);
    emit(u, f.actor, 'connAcquired', { tx: null, conn, free: res.pool.free, size: res.pool.size, alsoHolding: ctx.held, autoCommit: true });
    yield release(res.pool);
    emit(u, f.actor, 'connReleased', { conn, tx: null, autoCommit: true });
  }

  function* remoteCall(f, ctx, cfg, emit) {
    const u = ctx.user, r = f.remote;
    const takes = R.seconds(r.takes), read = cfg.readTimeout, connect = cfg.connectTimeout;
    const holding = ctx.active && ctx.active.conn ? ctx.active.conn : null;
    emit(u, f.actor, 'httpStart', { frame: f.id, label: r.label || null, holdingConnection: holding,
      suspendedHolding: ctx.suspended.filter(t => t && t.conn).length, takes });
    if (r.answers === 'unreachable') {
      yield sleep(connect);
      emit(u, f.actor, 'httpTimeout', { after: connect, kind: 'connect' });
      throw fail(r.onFailure || 'RemoteUnavailableException', 503, 'the remote is unreachable');
    }
    const d = Math.min(takes, read);
    yield sleep(d);
    if (takes > read) {
      emit(u, f.actor, 'httpTimeout', { after: read, kind: 'read' });
      throw fail(r.onFailure || 'RemoteUnavailableException', 503, 'no answer within read-timeout');
    }
    if (r.answers === '4xx') {
      emit(u, f.actor, 'httpEnd', { after: d, status: 422, reason: r.reason || 'refused' });
      throw fail(r.onRefusal || 'RemoteRefusedException', 422, r.reason || 'refused');
    }
    if (r.answers === '5xx') {
      emit(u, f.actor, 'httpEnd', { after: d, status: 503 });
      throw fail(r.onFailure || 'RemoteUnavailableException', 503, 'the remote failed');
    }
    emit(u, f.actor, 'httpEnd', { after: d, status: 200 });
  }

  // returns true when a clean exit still has to roll back (rollback-only marker)
  function* endTx(f, ctx, tx, e, res, emit) {
    const u = ctx.user;
    const rollback = e ? (R.rollsBack(e, tx.attr) || tx.rollbackOnly) : tx.rollbackOnly;
    emit(u, f.actor, rollback ? 'rollback' : 'commit', { tx: tx.id, cause: e ? e.kind : (tx.rollbackOnly ? 'rollbackOnly' : null),
      exceptionKind: e ? e.exceptionKind : null });
    if (tx.conn) {
      yield release(res.pool); ctx.held--;
      emit(u, f.actor, 'connReleased', { conn: tx.conn, tx: tx.id });
      tx.conn = null;
    }
    ctx.active = null;
    return !e && tx.rollbackOnly;
  }

  function* compensate(f, ctx, cfg, res, emit) {
    const u = ctx.user;
    const got = yield acquire(res.pool, cfg.connectionTimeout);
    if (got !== 'ok') { emit(u, f.actor, 'poolTimeout', { waited: cfg.connectionTimeout, alsoHolding: ctx.held, during: 'compensation' }); return; }
    const conn = 'c' + (++res.connSeq);
    emit(u, f.actor, 'compensation', { conn, what: f.compensation });
    yield release(res.pool);
    emit(u, f.actor, 'connReleased', { conn, tx: null, compensation: true });
  }

  // ---- the run ------------------------------------------------------------
  function round(t) { return Math.round(t * 1000) / 1000; }

  function summarize(timeline, cfg) {
    const holds = {}; let peak = 0, live = 0, longest = 0;
    for (const e of timeline) {
      if (e.event === 'connAcquired' && !e.detail.autoCommit) { holds[e.detail.conn] = e.t; live++; peak = Math.max(peak, live); }
      if (e.event === 'connReleased' && e.detail.tx) { longest = Math.max(longest, e.t - holds[e.detail.conn]); live--; }
    }
    const count = ev => timeline.filter(e => e.event === ev).length;
    const responses = timeline.filter(e => e.event === 'response');
    return { peakConnections: peak, poolSize: cfg.poolSize, longestHold: round(longest),
      refused: count('refused'), poolTimeouts: count('poolTimeout'), remoteTimeouts: count('httpTimeout'),
      saved: responses.filter(e => e.detail.status === 200).length,
      failed: responses.filter(e => e.detail.status !== 200).length,
      finishedAt: round(timeline.length ? timeline[timeline.length - 1].t : 0) };
  }

  function simulate(scenario, values) {
    values = values || {};
    const frames = resolveFrames(scenario, values);
    const cfg = resolveConfig(scenario, values);
    const res = { pool: new Resource('pool', cfg.poolSize), bulkheads: {}, connSeq: 0 };
    for (const f of frames) if (f.bulkhead) res.bulkheads[f.bulkhead.name] = res.bulkheads[f.bulkhead.name] || new Resource(f.bulkhead.name, Number(f.bulkhead.permits));
    const timeline = []; const sched = new Scheduler();
    const emit = (user, actor, event, detail) => timeline.push({ t: round(sched.now), user, actor, event, detail: detail || {} });
    let u = 0;
    for (const entry of resolve(scenario.entries, scenario, values)) {
      const rootFrame = frames.find(f => f.id === entry.root);
      for (let i = 0; i < Number(entry.users); i++) {
        const user = ++u;
        sched.at(R.seconds(entry.startAt || 0), () => drive(sched, userProgram(user, rootFrame, frames, cfg, res, emit), undefined));
      }
    }
    sched.run();
    return { timeline, cfg, frames, users: u, summary: summarize(timeline, cfg) };
  }

  const api = { simulate, resolveFrames, resolveConfig, slotValue };
  root.TxPlay = Object.assign(root.TxPlay || {}, api);
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
