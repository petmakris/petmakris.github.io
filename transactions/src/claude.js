(function (root) {
  const T = typeof require === 'function' ? Object.assign({}, require('./engine.js'), require('./template.js'), require('./explain.js')) : root.TxPlay;
  const MODEL = 'claude-sonnet-5', KEY_LS = 'txplay-apikey', CACHE_LS = 'txplay-answers', CACHE_CAP = 60;
  const ls = () => (typeof localStorage !== 'undefined' ? localStorage : null);
  function getKey() { return ls() ? ls().getItem(KEY_LS) : null; }
  function setKey(k) { if (ls()) ls().setItem(KEY_LS, k.trim()); }
  function clearKey() { if (ls()) ls().removeItem(KEY_LS); }

  function buildPrompt(scenario, run, values, explanation) {
    const showUser = T.slotValue(scenario, values, 'showUser');
    const code = scenario.files.map(f => `--- ${f.name} ---\n` + f.code.replace(/\{\{(\w+)\}\}/g, (m, n) => T.displayValue(scenario.slots[n], Object.prototype.hasOwnProperty.call(values, n) ? values[n] : scenario.slots[n].default))).join('\n\n');
    const timeline = run.timeline.filter(e => e.user === showUser || ['refused', 'poolTimeout', 'httpTimeout'].includes(e.event)).slice(0, 400);
    return [
      'You explain how a Spring Boot application behaves under one exact configuration, for a developer who does not yet hold the mechanism.',
      'The code below is a simulation of a real shape. The timeline is the ground truth of what happened: it was computed by a rule engine that models Spring proxies, @Transactional propagation, a resource-local JPA transaction manager holding one connection from first use to commit, a Hikari pool with a connection-timeout, Feign timeouts and a resilience4j bulkhead.',
      'Rewrite the templated explanation as three or four short paragraphs of cause and effect. Do not assert any mechanism the timeline does not show. Do not list events; explain why they happened in this order. End with one concrete change to try and what it would change.',
      '', '# Code', code,
      '', '# Configuration values', JSON.stringify(values),
      '', '# Summary', JSON.stringify(run.summary),
      '', `# Timeline (user ${showUser} plus every refusal and timeout)`, JSON.stringify(timeline, null, 1),
      '', '# Templated explanation', explanation.paragraphs.join('\n'),
    ].join('\n');
  }

  async function askClaude(key, prompt) {
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01', 'anthropic-dangerous-direct-browser-access': 'true' },
      body: JSON.stringify({ model: MODEL, max_tokens: 1200, messages: [{ role: 'user', content: prompt }] }),
    });
    if (!res.ok) throw new Error(`Anthropic API ${res.status}: ${(await res.text()).slice(0, 200)}`);
    const data = await res.json();
    const text = (data.content || []).map(c => c.text || '').join('').trim();
    if (!text) throw new Error('Empty response from the model.');
    return text;
  }

  function cacheGet(k) { try { return (JSON.parse(ls().getItem(CACHE_LS)) || {})[k]; } catch (e) { return undefined; } }
  function cachePut(k, v) { try { const c = JSON.parse(ls().getItem(CACHE_LS)) || {}; c[k] = v; const keys = Object.keys(c); if (keys.length > CACHE_CAP) delete c[keys[0]]; ls().setItem(CACHE_LS, JSON.stringify(c)); } catch (e) {} }

  async function askForThisRun(state, out) {
    const esc = T.esc;
    if (!state.lastRun) { out.innerHTML = '<p class="muted">Run first.</p>'; return; }
    const key = getKey();
    if (!key) {
      out.innerHTML = '<p class="muted">To ask Claude, add an Anthropic API key. This page has no server, so your key is stored only in this browser and sent straight to Anthropic. <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noopener">Get a key →</a></p>' +
        '<div class="key-form"><input id="key-input" type="password" placeholder="Paste your API key" autocomplete="off"><span class="btn" id="key-save">Save &amp; continue</span></div>';
      const go = () => { const v = out.querySelector('#key-input').value; if (v.trim()) { setKey(v); askForThisRun(state, out); } };
      out.querySelector('#key-save').onclick = go;
      out.querySelector('#key-input').addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
      out.querySelector('#key-input').focus();
      return;
    }
    const x = T.explain(state.scenario, state.lastRun, state.values, [...state.found]);
    const prompt = buildPrompt(state.scenario, state.lastRun, state.values, x);
    const ck = state.scenario.id + ':' + JSON.stringify(state.values);
    const cached = cacheGet(ck);
    if (cached) { out.innerHTML = cached.split(/\n{2,}/).map(p => `<p>${esc(p)}</p>`).join(''); return; }
    out.innerHTML = '<p class="muted">Asking Claude…</p>';
    try {
      const text = await askClaude(key, prompt);
      cachePut(ck, text);
      out.innerHTML = text.split(/\n{2,}/).map(p => `<p>${esc(p)}</p>`).join('');
    } catch (e) {
      out.innerHTML = `<p class="err">${esc(e.message)}</p><div class="key-form"><span class="btn outline" id="ask-retry">Retry</span><span class="btn outline" id="ask-chkey">Change API key</span></div>`;
      out.querySelector('#ask-retry').onclick = () => askForThisRun(state, out);
      out.querySelector('#ask-chkey').onclick = () => { clearKey(); askForThisRun(state, out); };
    }
  }

  const api = { MODEL, KEY_LS, buildPrompt, askClaude, askForThisRun, getKey, setKey, clearKey };
  root.TxPlay = Object.assign(root.TxPlay || {}, api);
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
