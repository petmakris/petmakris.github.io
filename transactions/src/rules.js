(function (root) {
  const PROPAGATIONS = ['REQUIRED', 'REQUIRES_NEW', 'NOT_SUPPORTED', 'SUPPORTS', 'NEVER', 'MANDATORY'];

  function seconds(v) {
    if (v == null || v === '') return 0;
    if (typeof v === 'number') return v;
    const m = String(v).trim().match(/^([\d.]+)\s*(ms|s|m)?$/);
    if (!m) throw new Error('bad duration: ' + v);
    const n = parseFloat(m[1]);
    return m[2] === 'ms' ? n / 1000 : m[2] === 'm' ? n * 60 : n;
  }

  function normalizeTx(v) {
    if (!v) return null;
    if (typeof v === 'string') {
      const m = v.match(/(REQUIRES_NEW|NOT_SUPPORTED|REQUIRED|SUPPORTS|NEVER|MANDATORY)/);
      return { propagation: m ? m[1] : 'REQUIRED', rollbackFor: [] };
    }
    return { propagation: v.propagation || 'REQUIRED', rollbackFor: v.rollbackFor || [] };
  }

  function reachesProxy(frame) {
    return frame.invoke !== 'this' && frame.visibility !== 'private';
  }

  function effectiveTx(frame) {
    if (!reachesProxy(frame)) return null;
    return normalizeTx(frame.methodTx) || normalizeTx(frame.classTx);
  }

  function enter(propagation, active) {
    switch (propagation) {
      case 'REQUIRED': return { action: active ? 'join' : 'start' };
      case 'REQUIRES_NEW': return { action: active ? 'suspendStart' : 'start' };
      case 'NOT_SUPPORTED': return { action: active ? 'suspend' : 'none' };
      case 'SUPPORTS': return { action: active ? 'join' : 'none' };
      case 'NEVER': return active ? { action: 'throw', reason: 'NEVER but a transaction is active' } : { action: 'none' };
      case 'MANDATORY': return active ? { action: 'join' } : { action: 'throw', reason: 'MANDATORY but no transaction is active' };
      default: throw new Error('unknown propagation ' + propagation);
    }
  }

  function rollsBack(error, attr) {
    if (error.exceptionKind !== 'checked') return true;
    return (attr.rollbackFor || []).includes(error.kind);
  }

  const api = { PROPAGATIONS, seconds, normalizeTx, reachesProxy, effectiveTx, enter, rollsBack };
  root.TxPlay = Object.assign(root.TxPlay || {}, api);
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
