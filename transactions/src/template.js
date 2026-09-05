(function (root) {
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

  function displayValue(slot, v) {
    switch (slot.kind) {
      case 'annotation':
        if (!v) return '// no annotation';
        if (typeof v === 'object') return v.rollbackFor && v.rollbackFor.length
          ? `@Transactional(propagation = ${v.propagation}, rollbackFor = ${v.rollbackFor.join('.class, ')}.class)`
          : `@Transactional(propagation = ${v.propagation})`;
        return v === '@Transactional' ? v : `@Transactional(propagation = ${v})`;
      case 'invocation': return (slot.labels && slot.labels[v]) || v;
      case 'visibility': return v === 'package' ? '/* package-private */' : v;
      case 'bulkhead': return v ? `@Bulkhead(name = "${v.name}", maxConcurrentCalls = ${v.permits}, maxWaitDuration = ${v.wait})` : '// no bulkhead';
      case 'external': return v ? `takes ${v.takes}, answers ${v.answers}${v.reason ? ' (' + v.reason + ')' : ''}` : '';
      case 'exception': return v ? `throw new ${v.name}()  // ${v.kind}` : '// throws nothing';
      case 'flag': return String(v);
      default: return String(v);
    }
  }

  const TOKEN = /(\/\/[^\n]*|#[^\n]*)|(@\w+(?:\([^)\n]*\))?)|\b(public|private|protected|class|return|new|final|void|int|throw|throws|static)\b|\b([A-Z][A-Za-z]+)\b/g;
  function highlight(text) {
    return esc(text).replace(TOKEN, (m, cm, ann, kw, ty) => {
      const cls = cm ? 'cm' : ann ? 'ann' : kw ? 'kw' : 'ty';
      return `<span class="${cls}">${m}</span>`;
    });
  }

  function controlHtml(name, slot, value, changed) {
    const cls = 'tg' + (changed ? ' changed' : '') + ((slot.kind === 'annotation' || slot.kind === 'bulkhead') && !value ? ' off' : '');
    return `<span class="${cls}" data-slot="${esc(name)}" data-kind="${slot.kind}" tabindex="0" title="${esc(slot.help || 'click to change')}">${esc(displayValue(slot, value))}</span>`;
  }

  function renderCode(file, scenario, values, changed) {
    changed = changed || new Set();
    const parts = file.code.split(/(\{\{\w+\}\})/);
    return parts.map(p => {
      const m = p.match(/^\{\{(\w+)\}\}$/);
      if (!m) return highlight(p);
      const slot = scenario.slots[m[1]];
      if (!slot) throw new Error('unknown slot ' + m[1]);
      const v = Object.prototype.hasOwnProperty.call(values, m[1]) ? values[m[1]] : slot.default;
      return controlHtml(m[1], slot, v, changed.has(m[1]));
    }).join('');
  }

  const api = { renderCode, controlHtml, displayValue, highlight, esc };
  root.TxPlay = Object.assign(root.TxPlay || {}, api);
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
