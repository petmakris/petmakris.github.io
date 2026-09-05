(function (root) {
  if (typeof document === 'undefined') { if (typeof module !== 'undefined') module.exports = {}; return; }
  const P = root.TxPlay;
  const $ = id => document.getElementById(id);
  const esc = P.esc;
  const state = { scenario: null, values: {}, changed: new Set(), lastRun: null, found: new Set() };

  function load(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch (e) { return fallback; } }
  function save(key, v) { try { localStorage.setItem(key, JSON.stringify(v)); } catch (e) {} }

  function select(scenario) {
    state.scenario = scenario;
    state.values = load('txplay-values-' + scenario.id, {});
    state.changed = new Set(); state.lastRun = null;
    renderTabs(); renderHeader(); renderPresets(); renderLeft(); run();
  }

  function renderTabs() {
    $('tabs').innerHTML = P.scenarios.map((s, i) => `<span class="tab${s === state.scenario ? ' on' : ''}" data-i="${i}">${i + 1} · ${esc(s.short || s.title)}</span>`).join('');
    $('tabs').querySelectorAll('.tab').forEach(t => t.onclick = () => select(P.scenarios[+t.dataset.i]));
  }
  function renderHeader() { $('title').textContent = state.scenario.title; $('intro').textContent = state.scenario.intro; }
  function renderPresets() {
    const s = state.scenario;
    $('presets').innerHTML = Object.keys(s.presets).map(p => `<span class="pill" data-p="${esc(p)}">${esc(p)}</span>`).join('') + '<span class="pill" data-p="__reset">Reset</span>';
    $('presets').querySelectorAll('.pill').forEach(el => el.onclick = () => {
      const p = el.dataset.p;
      const next = p === '__reset' ? {} : Object.assign({}, s.presets[p]);
      for (const k of new Set([...Object.keys(state.values), ...Object.keys(next)])) if (JSON.stringify(state.values[k]) !== JSON.stringify(next[k])) state.changed.add(k);
      state.values = next; save('txplay-values-' + s.id, state.values); renderLeft();
    });
  }

  function renderLeft() {
    const s = state.scenario;
    const askOut = $('ask-out') ? $('ask-out').innerHTML : '';
    $('left').innerHTML = s.files.map(f => `<div class="card"><div class="card-head"><span class="file">${esc(f.name)}</span><span>${esc(f.role || '')}</span></div><pre class="code">${P.renderCode(f, s, state.values, state.changed)}</pre></div>`).join('') +
      `<div class="card"><div class="actions"><span class="btn" id="run">Run</span><span class="btn outline" id="ask">Ask Claude to explain this run</span>` +
      (state.changed.size ? `<span class="diffchip">${state.changed.size} change${state.changed.size > 1 ? 's' : ''} since last run</span>` : '') + `</div><div id="ask-out">${askOut}</div></div>`;
    $('left').querySelectorAll('.tg').forEach(el => { el.onclick = () => edit(el); el.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); edit(el); } }; });
    $('run').onclick = run;
    $('ask').onclick = () => P.askForThisRun(state, $('ask-out'));
  }

  function edit(el) {
    const name = el.dataset.slot, slot = state.scenario.slots[name];
    const cur = Object.prototype.hasOwnProperty.call(state.values, name) ? state.values[name] : slot.default;
    let next;
    switch (slot.kind) {
      case 'annotation': case 'invocation': case 'visibility': case 'flag': {
        const choices = slot.choices || [cur];
        const labels = choices.map(c => P.displayValue(slot, c));
        const pick = prompt(`${name}\n` + labels.map((l, i) => `${i + 1}. ${l}`).join('\n'), String(choices.findIndex(c => JSON.stringify(c) === JSON.stringify(cur)) + 1));
        if (pick == null) return; next = choices[Number(pick) - 1]; if (next === undefined) return; break;
      }
      case 'number': { const v = prompt(name, String(cur)); if (v == null) return; next = /^\d+$/.test(v) ? Number(v) : v; break; }
      case 'bulkhead': {
        if (cur) { const v = prompt('permits,wait (empty to remove the bulkhead)', `${cur.permits},${cur.wait}`); if (v == null) return;
          next = v.trim() ? { name: cur.name, permits: Number(v.split(',')[0]), wait: (v.split(',')[1] || '0').trim() } : null; }
        else next = { name: 'fraud-check', permits: 4, wait: '0' };
        break;
      }
      case 'external': { const v = prompt('takes,answers (ok|late|4xx|5xx|unreachable)', `${cur.takes},${cur.answers}`); if (v == null) return;
        const [takes, answers] = v.split(',').map(x => x.trim()); next = { takes, answers, reason: answers === '4xx' ? 'no active policy' : undefined }; break; }
      case 'exception': { const v = prompt('name,runtime|checked (empty for none)', cur ? `${cur.name},${cur.kind}` : ''); if (v == null) return;
        next = v.trim() ? { name: v.split(',')[0].trim(), kind: (v.split(',')[1] || 'runtime').trim() } : null; break; }
      default: return;
    }
    state.values[name] = next; state.changed.add(name);
    save('txplay-values-' + state.scenario.id, state.values);
    renderLeft();
  }

  function run() {
    const s = state.scenario;
    let run;
    try { run = P.simulate(s, state.values); }
    catch (e) { $('explain').innerHTML = `<p class="err">${esc(e.message)}</p>`; return; }
    state.lastRun = run; state.changed = new Set();
    const spec = P.toDiagramSpec(s, run, state.values);
    $('diagram').innerHTML = P.renderSequence(spec);
    $('timeline-sub').textContent = `user ${P.slotValue(s, state.values, 'showUser')} of ${run.users}, computed from the code on the left`;
    const found = P.detect(run); found.forEach(id => state.found.add(id)); save('txplay-found', [...state.found]);
    const x = P.explain(s, run, state.values, [...state.found]);
    $('explain').innerHTML = x.paragraphs.map(p => `<p>${esc(p)}</p>`).join('') +
      `<div class="chips">${x.chips.map(c => `<span class="chip ${c.tone}">${esc(c.text)}</span>`).join('')}</div>` +
      (x.tryNext ? `<p style="margin-top:10px"><strong>${esc(x.tryNext)}</strong></p>` : '');
    renderDiscoveries(found);
    renderLeft();
    if ($('ask-out')) $('ask-out').innerHTML = '';
  }

  function renderDiscoveries(justNow) {
    const all = P.DISCOVERIES, ids = state.scenario.discoveries || all.map(d => d.id);
    $('disc-count').textContent = `${[...state.found].filter(id => ids.includes(id)).length} of ${ids.length}`;
    $('discoveries').innerHTML = all.filter(d => ids.includes(d.id)).map(d => {
      const f = state.found.has(d.id);
      return `<div class="disc ${f ? 'found' : 'locked'}"><span class="badge">${f ? (justNow.includes(d.id) ? 'FOUND NOW' : 'FOUND') : 'LOCKED'}</span><div class="t">${esc(d.title)}</div><div class="h">${esc(d.hint)}</div></div>`;
    }).join('');
  }

  function boot() {
    state.found = new Set(load('txplay-found', []));
    select(P.scenarios[0]);
  }
  document.addEventListener('DOMContentLoaded', boot);
  root.TxPlay = Object.assign(root.TxPlay || {}, { uiState: state });
})(typeof window !== 'undefined' ? window : globalThis);
