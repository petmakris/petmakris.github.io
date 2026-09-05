# Transaction Playground Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A single-page web game at `petmakris.github.io/transactions/` that shows a small Spring application as code with the annotations and configuration as inline controls, simulates what every thread and database connection does, and draws it as a sequence diagram with an explanation.

**Architecture:** Plain JavaScript modules under `src/`, each exporting both to a `TxPlay` browser global and to CommonJS for Node tests, baked by `build.py` into one `index.html` the way Fréquence is. A discrete-event engine interprets a scenario's call frames per concurrent user against a shared connection pool and shared bulkheads; the diagram, the explanation and the discoveries are derived from the engine's timeline, never from the code text. The diagram uses the annotate skill's sequence renderer, copied verbatim.

**Tech Stack:** JavaScript (no framework, no bundler), Node 24 `node --test` for tests, Python 3 for the build, GitHub Pages for hosting, Anthropic Messages API from the browser for the optional explanation.

**Spec:** `transactions/docs/superpowers/specs/2026-09-05-transaction-playground-design.md`

## Global Constraints

- Everything lives in `~/projects/blog/transactions/`; commit and push straight to `main` (the blog repo's rule). No AI attribution footers in commits.
- One self-contained `index.html`, produced only by `build.py`; never hand-edit it.
- No server. The engine, renderer, templated explanation and discoveries work with no key. Only "Ask Claude" uses a key, stored in `localStorage` under `txplay-apikey`.
- No proposal, orders, bank or montblanc name appears in any scenario. The invented domain is insurance claims and an external fraud check.
- Light theme only, high contrast, Roboto for the page, IBM Plex Mono and IBM Plex Sans inside the diagram. The sequence renderer and its stylesheet are copied verbatim from `~/projects/tx-explorer/.superpowers/brainstorm/82347-1788596978/content/code-playground.html`.
- Every `src/*.js` file ends with the same export shim so Node tests `require()` it and the browser reads it from `TxPlay`.
- Tests: `node --test tests/` from `transactions/`. Golden timelines are asserted exactly.

## File map

```
transactions/
  build.py                      concatenates src/ into index.html, stamps BUILD hash, runs node --check
  Makefile                      build · test · serve
  index.template.html           markup + CSS; placeholders __SCRIPTS__ __BUILD__
  index.html                    generated, committed (GitHub Pages serves it)
  src/seqrender.js              renderSequence(spec) → SVG string (verbatim renderer)
  src/rules.js                  proxy reach, effective @Transactional, propagation entry, rollback rule, durations
  src/engine.js                 simulate(scenario, values) → run {timeline, cfg, frames, summary}
  src/diagram.js                toDiagramSpec(scenario, run, values) → renderer spec
  src/explain.js                explain(scenario, run, values) → {paragraphs, chips, tryNext}
  src/discoveries.js            DISCOVERIES, detect(run) → ids
  src/template.js               renderCode(file, scenario, values) → HTML; control HTML per slot kind
  src/claude.js                 key storage, prompt, Messages API call, answer cache
  src/ui.js                     page wiring: tabs, controls, run, discoveries, key form
  src/scenarios/01-edit-calls-out.js … 06-suspension.js
  tests/*.test.js               node --test
  docs/superpowers/specs/…      the spec
  docs/superpowers/plans/…      this plan
```

Export shim used by every `src/*.js` file:

```js
(function (root) {
  // ... file body defines `api` ...
  root.TxPlay = Object.assign(root.TxPlay || {}, api);
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
```

Cross-file dependency inside a file (works in Node and in the baked page, where files are concatenated in order):

```js
const R = typeof require === 'function' ? require('./rules.js') : root.TxPlay;
```

---

### Task 1: Scaffold, build script and test runner

**Files:**
- Create: `transactions/Makefile`
- Create: `transactions/build.py`
- Create: `transactions/index.template.html` (skeleton; the real markup arrives in Task 9)
- Create: `transactions/src/seqrender.js` (placeholder shim only; real code in Task 3)
- Test: `transactions/tests/build.test.js`

**Interfaces:**
- Produces: `python3 build.py` writing `index.html` with `__SCRIPTS__` and `__BUILD__` replaced; `SRC_ORDER` list in `build.py` that later tasks append to.

- [ ] **Step 1: Write the failing test**

```js
// tests/build.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.join(__dirname, '..');

test('build.py bakes src into index.html with a build hash', () => {
  execFileSync('python3', ['build.py'], { cwd: ROOT });
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  assert.ok(!html.includes('__SCRIPTS__'), 'scripts placeholder replaced');
  assert.ok(!html.includes('__BUILD__'), 'build placeholder replaced');
  assert.match(html, /<meta name="build" content="[0-9a-f]{12}">/);
  assert.ok(html.includes('root.TxPlay = Object.assign'), 'src files inlined');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/projects/blog/transactions && node --test tests/build.test.js`
Expected: FAIL, `build.py` not found.

- [ ] **Step 3: Write the build script, the Makefile and the skeleton template**

```python
#!/usr/bin/env python3
"""Bake the transaction playground into one self-contained index.html.

Concatenates src/ in SRC_ORDER into the template's __SCRIPTS__ slot, stamps a
content hash into __BUILD__, and refuses to write if node reports a JS syntax
error. Same shape as frequence/build_game.py.
"""
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "index.html"
TEMPLATE = ROOT / "index.template.html"

SRC_ORDER = [
    "src/seqrender.js",
    "src/rules.js",
    "src/engine.js",
    "src/diagram.js",
    "src/explain.js",
    "src/discoveries.js",
    "src/template.js",
    "src/claude.js",
    "src/scenarios/01-edit-calls-out.js",
    "src/scenarios/02-nightly-sweep.js",
    "src/scenarios/03-create-compensation.js",
    "src/scenarios/04-pool-exhaustion.js",
    "src/scenarios/05-proxy-bypass.js",
    "src/scenarios/06-suspension.js",
    "src/ui.js",
]


def check_js(script: str) -> None:
    node = shutil.which("node")
    if not node:
        print("note: node not found, skipping JS syntax check")
        return
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(script)
    r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
    Path(f.name).unlink(missing_ok=True)
    if r.returncode != 0:
        sys.exit("JS syntax error:\n" + r.stderr)


def main() -> None:
    parts = []
    for rel in SRC_ORDER:
        p = ROOT / rel
        if p.exists():
            parts.append(f"// ---- {rel} ----\n" + p.read_text(encoding="utf-8"))
    script = "\n".join(parts)
    check_js(script)
    template = TEMPLATE.read_text(encoding="utf-8")
    build = hashlib.sha256((template + script).encode("utf-8")).hexdigest()[:12]
    html = template.replace("__SCRIPTS__", script).replace("__BUILD__", build)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(html):,} bytes, build {build})")


if __name__ == "__main__":
    main()
```

```makefile
# Transaction playground — build helpers.
.DEFAULT_GOAL := help
.PHONY: build test serve help

build:   ## bake src/ + index.template.html -> index.html
	python3 build.py

test:    ## run the engine, renderer and scenario tests
	node --test tests/

serve:   ## serve this folder locally on :8090
	python3 -m http.server 8090

help:    ## list targets
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed -E 's/:[^#]*## / - /'
```

`index.template.html` skeleton (Task 9 replaces it):

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="build" content="__BUILD__">
<title>Transaction playground</title>
</head>
<body>
<main id="app"></main>
<script>
__SCRIPTS__
</script>
</body>
</html>
```

`src/seqrender.js` placeholder so the build has one source file:

```js
(function (root) {
  const api = {};
  root.TxPlay = Object.assign(root.TxPlay || {}, api);
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/projects/blog/transactions && node --test tests/build.test.js`
Expected: PASS, and `index.html` exists.

- [ ] **Step 5: Commit**

```bash
cd ~/projects/blog && git add transactions/Makefile transactions/build.py transactions/index.template.html transactions/index.html transactions/src/seqrender.js transactions/tests/build.test.js && git commit -m "transactions: scaffold build and test runner"
```

---

### Task 2: Rules

**Files:**
- Create: `transactions/src/rules.js`
- Test: `transactions/tests/rules.test.js`

**Interfaces:**
- Produces:
  - `seconds(v)`: `"45s" | "500ms" | "2m" | 30 | null → number` of seconds
  - `normalizeTx(v)`: `null | string | {propagation, rollbackFor} → null | {propagation, rollbackFor: string[]}`
  - `reachesProxy(frame)`: `frame.invoke !== 'this' && frame.visibility !== 'private'`
  - `effectiveTx(frame)`: the tx attribute that applies, or `null`
  - `enter(propagation, activeTx)`: `{action: 'join'|'start'|'suspendStart'|'suspend'|'none'|'throw', reason?}`
  - `rollsBack(error, attr)`: boolean

- [ ] **Step 1: Write the failing tests**

```js
// tests/rules.test.js
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test tests/rules.test.js`
Expected: FAIL, cannot find `../src/rules.js`.

- [ ] **Step 3: Implement rules.js**

```js
// src/rules.js
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test tests/rules.test.js`
Expected: PASS, 6 tests.

- [ ] **Step 5: Commit**

```bash
cd ~/projects/blog && git add transactions/src/rules.js transactions/tests/rules.test.js && git commit -m "transactions: propagation, proxy and rollback rules"
```

---

### Task 3: The sequence renderer

**Files:**
- Modify: `transactions/src/seqrender.js` (replace the placeholder)
- Test: `transactions/tests/seqrender.test.js`

**Interfaces:**
- Produces: `renderSequence(spec) → string` (an `<svg class="seq">`). Spec shape: `{alt, actors:[{id,label,tone}], steps:[{from,to,arrow:'request'|'event'|'self'|'band', tone, label, sub, note, phase, span, dashed}], rails:[{actor,from,to,tone,label}], legend:[{tone,label}]}`. `rails[].from/to` are step indexes.

- [ ] **Step 1: Write the failing test**

```js
// tests/seqrender.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const { renderSequence } = require('../src/seqrender.js');

const spec = {
  alt: 'two actors',
  actors: [{ id: 'a', label: 'Alpha\nOne', tone: 'edge' }, { id: 'pool', label: 'Pool', tone: 'hot' }],
  rails: [{ actor: 'pool', from: 0, to: 1, tone: 'hot', label: 'held' }],
  steps: [
    { from: 'a', to: 'pool', arrow: 'request', label: 'BEGIN', sub: 'first touch', tone: 'hot', note: 'taken', phase: 'start' },
    { from: 'a', to: 'pool', arrow: 'request', label: 'COMMIT', tone: 'good', note: 'released' },
    { from: 'a', to: 'a', arrow: 'self', label: 'done' },
    { from: 'a', to: 'pool', arrow: 'band', label: 'a band' },
  ],
  legend: [{ tone: 'hot', label: 'holds' }],
};

test('renderSequence draws actors, rows, a rail, a phase and a legend', () => {
  const svg = renderSequence(spec);
  assert.ok(svg.startsWith('<svg class="seq"'));
  assert.ok(svg.endsWith('</svg>'));
  assert.ok(svg.includes('Alpha') && svg.includes('One'), 'two-line actor label');
  assert.ok(svg.includes('class="rail t-hot"'), 'rail on the pool');
  assert.ok(svg.includes('class="phase-label"') && svg.includes('start'));
  assert.ok(svg.includes('class="row-note t-hot"') && svg.includes('taken'));
  assert.ok(svg.includes('class="legend-text"') && svg.includes('holds'));
  assert.equal((svg.match(/class="row-num"/g) || []).length, 3, 'bands are not numbered');
});

test('renderSequence escapes labels', () => {
  const svg = renderSequence({ actors: [{ id: 'a', label: 'A' }, { id: 'b', label: 'B' }],
    steps: [{ from: 'a', to: 'b', arrow: 'request', label: '<script>' }] });
  assert.ok(!svg.includes('<script>'));
  assert.ok(svg.includes('&lt;script&gt;'));
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/seqrender.test.js`
Expected: FAIL, `renderSequence is not a function`.

- [ ] **Step 3: Copy the renderer verbatim**

Take the `render` function and its constants from `~/projects/tx-explorer/.superpowers/brainstorm/82347-1788596978/content/code-playground.html` (the `<script>` at the bottom, everything before `document.getElementById('d1')`), rename `render` to `renderSequence`, and wrap it in the shim. Do not change any constant or drawing code.

```js
// src/seqrender.js
(function (root) {
  const ROW_H=34, ACTOR_W=124, ACTOR_GAP=12, PAD_L=54, ROWNUM_X=42, PAD_R=18,
        GUTTER_GAP=26, ACTOR_H=46, TOP=14, INSET=6, HEAD=7, BAND_H=22, SELF_W=24,
        LEGEND_H=30, RAIL_W=11;
  const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const tc=t=>t&&t!=='plain'?' t-'+t:'';

  function renderSequence(spec){
    /* body of render(spec) from the mockup, unchanged */
  }

  const api = { renderSequence };
  root.TxPlay = Object.assign(root.TxPlay || {}, api);
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/seqrender.test.js`
Expected: PASS, 2 tests.

- [ ] **Step 5: Commit**

```bash
cd ~/projects/blog && git add transactions/src/seqrender.js transactions/tests/seqrender.test.js && git commit -m "transactions: sequence renderer from the annotate skill"
```

---

### Task 4: The engine, single user

**Files:**
- Create: `transactions/src/engine.js`
- Test: `transactions/tests/engine.test.js`

**Interfaces:**
- Consumes: `rules.js`.
- Produces: `simulate(scenario, values) → run`, where
  - `scenario.frames[]`: `{id, actor, method, classTx, methodTx, visibility, invoke, dbTouch, lazyRead, bulkhead:{name,permits,wait,fallback}, remote:{takes,answers:'ok'|'late'|'4xx'|'5xx'|'unreachable',label,onFailure,onRefusal,reason}, throws:{name,kind}, compensation, calls:[ids], phase}`. Any field may be `{slot:'name'}` and is replaced by `values[name]` (or the slot's default).
  - `scenario.config`: `{poolSize, connectionTimeout, connectTimeout, readTimeout, osiv}` with the same slot references.
  - `scenario.entries[]`: `{root:'f1', users:{slot:'users'}, startAt: 0}`; user numbers are global across entries.
  - `run = {timeline:[{t,user,actor,event,detail}], cfg, frames, summary}`; events: `call, txBegin, txJoin, suspend, resume, dbRead, connAcquired, connReleased, poolTimeout, permit, refused, httpStart, httpEnd, httpTimeout, rollbackOnly, rollback, commit, exception, compensation, detachedRead, response`.
  - `resolveFrames(scenario, values)`, `resolveConfig(scenario, values)`, `slotValue(scenario, values, name)`.

- [ ] **Step 1: Write the failing tests**

```js
// tests/engine.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const { simulate } = require('../src/engine.js');

function scenario(overrides = {}) {
  return {
    slots: {
      classTx1: { kind: 'annotation', default: '@Transactional' },
      classTx2: { kind: 'annotation', default: '@Transactional' },
      methodTx3: { kind: 'annotation', default: null },
      invoke2: { kind: 'invocation', default: 'injected' },
      invoke3: { kind: 'invocation', default: 'this' },
      visibility3: { kind: 'visibility', default: 'private' },
      bulkhead: { kind: 'bulkhead', default: null },
      remote: { kind: 'external', default: { takes: '45s', answers: 'late' } },
      throws: { kind: 'exception', default: null },
      poolSize: { kind: 'number', default: 10 },
      connectionTimeout: { kind: 'number', default: '30s' },
      connectTimeout: { kind: 'number', default: '10s' },
      readTimeout: { kind: 'number', default: '60s' },
      users: { kind: 'number', default: 1 },
      showUser: { kind: 'number', default: 1 },
      ...overrides.slots,
    },
    config: { poolSize: { slot: 'poolSize' }, connectionTimeout: { slot: 'connectionTimeout' },
      connectTimeout: { slot: 'connectTimeout' }, readTimeout: { slot: 'readTimeout' }, osiv: false },
    entries: [{ root: 'f1', users: { slot: 'users' }, startAt: 0 }],
    frames: [
      { id: 'f1', actor: 'ClaimService', method: 'updateClaim', classTx: { slot: 'classTx1' }, methodTx: null,
        visibility: 'public', invoke: 'injected', dbTouch: true, calls: ['f2'] },
      { id: 'f2', actor: 'FraudCheckService', method: 'runFraudCheck', classTx: { slot: 'classTx2' }, methodTx: null,
        visibility: 'public', invoke: { slot: 'invoke2' }, bulkhead: { slot: 'bulkhead' }, calls: ['f3'], throws: { slot: 'throws' } },
      { id: 'f3', actor: 'FraudCheckService', method: 'call', classTx: { slot: 'classTx2' }, methodTx: { slot: 'methodTx3' },
        visibility: { slot: 'visibility3' }, invoke: { slot: 'invoke3' }, remote: { slot: 'remote' } },
    ],
  };
}

const events = (run, user) => run.timeline.filter(e => e.user === user).map(e => e.event);
const find = (run, ev, user = 1) => run.timeline.find(e => e.user === user && e.event === ev);

test('the remote call runs inside the transaction and holds its connection for 45 s', () => {
  const run = simulate(scenario(), {});
  assert.deepEqual(events(run, 1), ['call', 'txBegin', 'connAcquired', 'call', 'txJoin', 'call', 'httpStart', 'httpEnd', 'commit', 'connReleased', 'response']);
  assert.equal(find(run, 'httpStart').detail.holdingConnection, 'c1');
  assert.equal(find(run, 'connReleased').t, 45);
  assert.equal(find(run, 'response').detail.status, 200);
});

test('a self-invoked call ignores its own NOT_SUPPORTED annotation', () => {
  const run = simulate(scenario(), { methodTx3: 'NOT_SUPPORTED' });
  assert.ok(!events(run, 1).includes('suspend'));
  const call3 = run.timeline.filter(e => e.event === 'call')[2];
  assert.equal(call3.detail.viaProxy, false);
  assert.equal(call3.detail.ignoredAnnotation, true);
});

test('NOT_SUPPORTED through the proxy suspends but keeps the connection', () => {
  const run = simulate(scenario(), { methodTx3: 'NOT_SUPPORTED', invoke3: 'self', visibility3: 'public' });
  assert.deepEqual(events(run, 1), ['call', 'txBegin', 'connAcquired', 'call', 'txJoin', 'call', 'suspend', 'httpStart', 'httpEnd', 'resume', 'commit', 'connReleased', 'response']);
  assert.equal(find(run, 'suspend').detail.keepsConnection, true);
  assert.equal(find(run, 'httpStart').detail.holdingConnection, null);
  assert.equal(find(run, 'httpStart').detail.suspendedHolding, 1);
  assert.equal(find(run, 'connReleased').t, 45);
});

test('a refusal from the remote rolls the edit back and releases the connection', () => {
  const run = simulate(scenario(), { remote: { takes: '2s', answers: '4xx', reason: 'no policy' } });
  assert.deepEqual(events(run, 1), ['call', 'txBegin', 'connAcquired', 'call', 'txJoin', 'call', 'httpStart', 'httpEnd', 'exception', 'exception', 'rollback', 'connReleased', 'exception', 'response']);
  assert.equal(find(run, 'response').detail.status, 422);
  assert.equal(find(run, 'connReleased').t, 2);
});

test('a read timeout on the remote is an unavailability, not a refusal', () => {
  const run = simulate(scenario(), { remote: { takes: '90s', answers: 'late' } });
  assert.equal(find(run, 'httpTimeout').detail.after, 60);
  assert.equal(find(run, 'response').detail.status, 503);
  assert.equal(find(run, 'connReleased').t, 60);
});

test('a checked exception does not roll back unless rollbackFor names it', () => {
  const checked = simulate(scenario(), { throws: { name: 'AuditFailure', kind: 'checked' } });
  assert.ok(events(checked, 1).includes('commit'));
  assert.equal(find(checked, 'response').detail.status, 500);
  const named = simulate(scenario(), { throws: { name: 'AuditFailure', kind: 'checked' }, classTx1: { propagation: 'REQUIRED', rollbackFor: ['AuditFailure'] } });
  assert.ok(events(named, 1).includes('rollback'));
});

test('a repository read inside a suspended section takes a second connection', () => {
  const s = scenario();
  s.frames[2].dbTouch = true;
  const run = simulate(s, { methodTx3: 'NOT_SUPPORTED', invoke3: 'self', visibility3: 'public' });
  const second = run.timeline.filter(e => e.event === 'connAcquired')[1];
  assert.equal(second.detail.autoCommit, true);
  assert.equal(second.detail.alsoHolding, 1);
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test tests/engine.test.js`
Expected: FAIL, cannot find `../src/engine.js`.

- [ ] **Step 3: Implement engine.js**

```js
// src/engine.js
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
      if (node.slot) return resolve(slotValue(scenario, values, node.slot), scenario, values);
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

  function* dbTouch(f, ctx, cfg, res, emit) {
    const u = ctx.user, tx = ctx.active;
    if (tx && tx.conn) { emit(u, f.actor, 'dbRead', { tx: tx.id, conn: tx.conn }); return; }
    if (!tx && f.lazyRead && !cfg.osiv) {
      emit(u, f.actor, 'detachedRead', { frame: f.id });
      throw fail('LazyInitializationException', 500, 'lazy association touched outside a session');
    }
    const got = yield acquire(res.pool, cfg.connectionTimeout);
    if (got !== 'ok') {
      emit(u, f.actor, 'poolTimeout', { waited: cfg.connectionTimeout, alsoHolding: ctx.held });
      throw fail('SQLTransientConnectionException', 500, 'no connection within connection-timeout');
    }
    const conn = 'c' + (++res.connSeq);
    if (tx) {
      tx.conn = conn; ctx.held++;
      emit(u, f.actor, 'connAcquired', { tx: tx.id, conn, free: res.pool.free, size: res.pool.size, alsoHolding: ctx.held - 1 });
    } else {
      emit(u, f.actor, 'connAcquired', { tx: null, conn, free: res.pool.free, size: res.pool.size, alsoHolding: ctx.held, autoCommit: true });
      yield release(res.pool);
      emit(u, f.actor, 'connReleased', { conn, tx: null, autoCommit: true });
    }
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test tests/engine.test.js`
Expected: PASS, 7 tests. If an event sequence differs, print `run.timeline` and fix the engine, not the expectation, unless the expectation contradicts the spec's rules.

- [ ] **Step 5: Commit**

```bash
cd ~/projects/blog && git add transactions/src/engine.js transactions/tests/engine.test.js && git commit -m "transactions: discrete-event engine for one user"
```

---

### Task 5: The engine under load

**Files:**
- Modify: `transactions/src/engine.js` only if a test exposes a defect
- Test: `transactions/tests/engine-load.test.js`

**Interfaces:**
- Consumes: `simulate` from Task 4 and the `scenario()` helper from `tests/engine.test.js` (export it: add `module.exports = { scenario }` at the end of that file, guarded by `if (require.main !== module)` is not needed; `node --test` ignores exports).

- [ ] **Step 1: Write the failing tests**

```js
// tests/engine-load.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const { simulate } = require('../src/engine.js');
const { scenario } = require('./engine.test.js');

const byUser = (run, u) => run.timeline.filter(e => e.user === u);
const ev = (run, u) => byUser(run, u).map(e => e.event);

test('with a bulkhead of 4, users 5 to 12 are refused at once and release their connection', () => {
  const run = simulate(scenario(), { users: 12, bulkhead: { name: 'fraud-check', permits: 4, wait: '0' } });
  assert.equal(run.summary.refused, 8);
  assert.equal(run.summary.peakConnections, 4 + 1, 'four held across the remote plus the fifth for an instant');
  const u5 = byUser(run, 5);
  assert.equal(u5.find(e => e.event === 'refused').detail.after, 0);
  assert.equal(u5.find(e => e.event === 'response').t, 0);
  assert.equal(u5.find(e => e.event === 'response').detail.status, 503);
  assert.ok(!ev(run, 5).includes('httpStart'), 'the remote is never called for a refused user');
  assert.equal(byUser(run, 1).find(e => e.event === 'response').t, 45);
  assert.equal(run.summary.poolTimeouts, 0);
});

test('without a bulkhead, ten users hold the pool and the last two time out after 30 s', () => {
  const run = simulate(scenario(), { users: 12 });
  assert.equal(run.summary.peakConnections, 10);
  assert.equal(run.summary.poolTimeouts, 2);
  const u11 = byUser(run, 11);
  assert.equal(u11.find(e => e.event === 'poolTimeout').t, 30);
  assert.equal(u11.find(e => e.event === 'response').detail.status, 500);
  assert.equal(byUser(run, 10).find(e => e.event === 'response').t, 45);
});

test('a bulkhead with a wait queues the fifth user, who holds its connection while it waits', () => {
  const run = simulate(scenario(), { users: 5, bulkhead: { name: 'fraud-check', permits: 4, wait: '60s' } });
  const u5 = byUser(run, 5);
  assert.equal(u5.find(e => e.event === 'permit').t, 45, 'granted when user 1 finishes');
  assert.equal(u5.find(e => e.event === 'connAcquired').t, 0, 'held from t = 0');
  assert.equal(u5.find(e => e.event === 'response').t, 90);
  assert.equal(run.summary.longestHold, 90);
});

test('a second entry that arrives later starves on the exhausted pool', () => {
  const s = scenario({ slots: { browsers: { kind: 'number', default: 2 } } });
  s.frames.push({ id: 'g1', actor: 'DashboardService', method: 'list', classTx: '@Transactional', methodTx: null,
    visibility: 'public', invoke: 'injected', dbTouch: true });
  s.entries.push({ root: 'g1', users: { slot: 'browsers' }, startAt: '1s' });
  const run = simulate(s, { users: 10 });
  const browser = byUser(run, 11);
  assert.equal(browser[0].t, 1);
  assert.equal(browser.find(e => e.event === 'poolTimeout').t, 31);
  assert.equal(run.summary.poolTimeouts, 2);
});
```

- [ ] **Step 2: Run tests to verify they fail or pass**

Run: `node --test tests/engine-load.test.js`
Expected: the four tests run against Task 4's engine. Any FAIL is a defect in the engine's resource handling; fix it in `engine.js` until all pass. The likely defect: `acquire` granting to a waiter must happen through `sched.at(sched.now, ...)` so the releasing user finishes its own step first; check the third test's `permit` time is exactly 45.

- [ ] **Step 3: Run the whole suite**

Run: `node --test tests/`
Expected: PASS, all tests.

- [ ] **Step 4: Commit**

```bash
cd ~/projects/blog && git add transactions/src/engine.js transactions/tests/engine-load.test.js transactions/tests/engine.test.js && git commit -m "transactions: engine under concurrent load"
```

---

### Task 6: Scenario format, scenario 1, and the code template renderer

**Files:**
- Create: `transactions/src/scenarios/01-edit-calls-out.js`
- Create: `transactions/src/template.js`
- Test: `transactions/tests/scenario1.test.js`, `transactions/tests/template.test.js`

**Interfaces:**
- Produces:
  - scenario module shape: `{id, title, intro, files:[{name, role, code}], slots, presets, frames, config, entries, actors:[{id,label,tone}], actorOf:{frameActor: actorId}, remoteActor, poolActor, discoveries:[ids]}`. Registered as `TxPlay.scenarios.push(scenario)` in the browser and `module.exports = scenario` in Node.
  - `renderCode(file, scenario, values, changed) → html`: highlighted code with one `<span class="tg" data-slot="name">…</span>` per `{{slot}}`; `changed` is a Set of slot names to mark.
  - `controlHtml(name, slot, value) → html` and `displayValue(slot, value) → string`.

- [ ] **Step 1: Write the failing tests**

```js
// tests/scenario1.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const scenario = require('../src/scenarios/01-edit-calls-out.js');
const { simulate } = require('../src/engine.js');

test('scenario 1 declares every slot its code and frames reference', () => {
  const refs = new Set();
  for (const f of scenario.files) for (const m of f.code.matchAll(/\{\{(\w+)\}\}/g)) refs.add(m[1]);
  JSON.stringify(scenario.frames, (k, v) => { if (v && v.slot) refs.add(v.slot); return v; });
  JSON.stringify(scenario.config, (k, v) => { if (v && v.slot) refs.add(v.slot); return v; });
  for (const r of refs) assert.ok(scenario.slots[r], 'slot declared: ' + r);
  for (const p of Object.values(scenario.presets)) for (const k of Object.keys(p)) assert.ok(scenario.slots[k], 'preset slot: ' + k);
});

test('scenario 1 as designed: user 5 of 12 is refused, users 1 to 4 hold for 45 s', () => {
  const run = simulate(scenario, {});
  assert.equal(run.users, 12);
  assert.equal(run.summary.refused, 8);
  assert.equal(run.summary.longestHold, 45);
  assert.equal(run.summary.saved, 4);
});

test('scenario 1 preset "no ceiling": pool exhaustion', () => {
  const run = simulate(scenario, scenario.presets['no ceiling']);
  assert.equal(run.summary.poolTimeouts, 2);
  assert.equal(run.summary.peakConnections, 10);
});

test('scenario 1 preset "self-injected": the suspended transaction keeps its connection', () => {
  const run = simulate(scenario, { ...scenario.presets['self-injected'], users: 1 });
  const http = run.timeline.find(e => e.event === 'httpStart');
  assert.equal(http.detail.holdingConnection, null);
  assert.equal(http.detail.suspendedHolding, 1);
});
```

```js
// tests/template.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const { renderCode, displayValue } = require('../src/template.js');
const scenario = require('../src/scenarios/01-edit-calls-out.js');

test('renderCode replaces each slot with a control and escapes the rest', () => {
  const html = renderCode(scenario.files[1], scenario, {}, new Set(['bulkhead']));
  assert.ok(html.includes('data-slot="bulkhead"'));
  assert.ok(html.includes('class="tg changed"'), 'changed slot is marked');
  assert.ok(html.includes('<span class="kw">public</span>'));
  assert.ok(!html.includes('{{'), 'no raw slot markers');
  assert.ok(!/<(?!\/?span|\/?code)/.test(html.replace(/<span[^>]*>|<\/span>/g, '')), 'only spans emitted');
});

test('displayValue renders annotations, invocations and bulkheads as code', () => {
  assert.equal(displayValue({ kind: 'annotation' }, null), '// no annotation');
  assert.equal(displayValue({ kind: 'annotation' }, '@Transactional'), '@Transactional');
  assert.equal(displayValue({ kind: 'annotation' }, 'NOT_SUPPORTED'), '@Transactional(propagation = NOT_SUPPORTED)');
  assert.equal(displayValue({ kind: 'invocation', labels: { this: 'this', injected: 'fraudCheck', self: 'self' } }, 'injected'), 'fraudCheck');
  assert.equal(displayValue({ kind: 'bulkhead' }, { name: 'fraud-check', permits: 4, wait: '0' }), '@Bulkhead(name = "fraud-check", maxConcurrentCalls = 4, maxWaitDuration = 0)');
  assert.equal(displayValue({ kind: 'bulkhead' }, null), '// no bulkhead');
  assert.equal(displayValue({ kind: 'external' }, { takes: '45s', answers: 'late' }), 'takes 45s, answers late');
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test tests/scenario1.test.js tests/template.test.js`
Expected: FAIL, modules not found.

- [ ] **Step 3: Write scenario 1**

```js
// src/scenarios/01-edit-calls-out.js
(function (root) {
  const scenario = {
    id: 'edit-calls-out',
    title: 'An edit that asks an external system before it commits',
    intro: 'A user edits a claim. Before the edit is committed, the application asks an external fraud check for a verdict and stores it with the edit. If the check refuses or cannot answer, nothing must be saved.',
    files: [
      { name: 'ClaimService.java', role: 'frame 1: the entry point the save reaches', code:
`@Service
{{classTx1}}
public class ClaimService {

    private final ClaimRepository claims;
    private final FraudCheckService fraudCheck;

    {{methodTx1}}
    public Claim updateClaim(int id, ClaimEdit edit) {
        Claim claim = claims.findById(id);          // first database touch: a connection is taken here
        claim.apply(edit);
        claims.save(claim);                          // written, not committed
        {{invoke2}}.runFraudCheck(claim);
        return claim;                                // the transaction commits when this method returns
    }
}` },
      { name: 'FraudCheckService.java', role: 'frames 2 and 3: the bean that owns the external call', code:
`@Service
{{classTx2}}
public class FraudCheckService {

    private final FraudGateway gateway;              // HTTP client to the insurer
    private final VerdictWriter verdicts;

    {{bulkhead}}
    public Verdict runFraudCheck(Claim claim) {
        Payload payload = prepare(claim);
        Verdict verdict = {{invoke3}}.call(payload);
        verdicts.apply(claim, verdict);
        return verdict;
    }

    {{methodTx3}}
    {{visibility3}} Verdict call(Payload payload) {
        return gateway.check(payload);               // {{remote}}
    }
}` },
      { name: 'application.yml', role: 'the numbers the timeline is computed from', code:
`datasource:
  hikari:
    maximum-pool-size: {{poolSize}}
    connection-timeout: {{connectionTimeout}}        # how long a thread waits for a free connection
spring:
  jpa:
    open-in-view: {{osiv}}
  cloud.openfeign.client.config.fraud-gateway:
    connect-timeout: {{connectTimeout}}
    read-timeout: {{readTimeout}}                    # the insurer may take up to this long
load:                                                # the simulation's inputs, not real configuration
  concurrent-users-saving: {{users}}
  show-user: {{showUser}}` },
    ],
    slots: {
      classTx1: { kind: 'annotation', target: 'class', default: '@Transactional', choices: [null, '@Transactional'] },
      methodTx1: { kind: 'annotation', target: 'method', default: null, choices: [null, 'REQUIRED', 'REQUIRES_NEW'] },
      invoke2: { kind: 'invocation', default: 'injected', choices: ['injected'], labels: { injected: 'fraudCheck' } },
      classTx2: { kind: 'annotation', target: 'class', default: '@Transactional', choices: [null, '@Transactional'] },
      bulkhead: { kind: 'bulkhead', default: { name: 'fraud-check', permits: 4, wait: '0' } },
      invoke3: { kind: 'invocation', default: 'this', choices: ['this', 'self'], labels: { this: 'this', self: 'self' },
        help: 'this: a plain self-invocation. self: a self-injected proxy of this bean.' },
      methodTx3: { kind: 'annotation', target: 'method', default: null, choices: [null, 'NOT_SUPPORTED', 'SUPPORTS', 'REQUIRES_NEW'] },
      visibility3: { kind: 'visibility', default: 'private', choices: ['private', 'package', 'public'] },
      remote: { kind: 'external', default: { takes: '45s', answers: 'late' }, label: 'POST /fraud/check' },
      poolSize: { kind: 'number', default: 10 },
      connectionTimeout: { kind: 'number', default: '30s' },
      osiv: { kind: 'flag', default: false, choices: [false, true] },
      connectTimeout: { kind: 'number', default: '10s' },
      readTimeout: { kind: 'number', default: '60s' },
      users: { kind: 'number', default: 12 },
      showUser: { kind: 'number', default: 5 },
    },
    presets: {
      'as designed': {},
      'no ceiling': { bulkhead: null },
      'self-injected': { invoke3: 'self', visibility3: 'public', methodTx3: 'NOT_SUPPORTED' },
      'the insurer refuses': { remote: { takes: '2s', answers: '4xx', reason: 'no active policy' }, showUser: 1 },
    },
    config: { poolSize: { slot: 'poolSize' }, connectionTimeout: { slot: 'connectionTimeout' },
      connectTimeout: { slot: 'connectTimeout' }, readTimeout: { slot: 'readTimeout' }, osiv: { slot: 'osiv' } },
    entries: [{ root: 'f1', users: { slot: 'users' }, startAt: 0 }],
    frames: [
      { id: 'f1', actor: 'ClaimService', method: 'updateClaim', classTx: { slot: 'classTx1' }, methodTx: { slot: 'methodTx1' },
        visibility: 'public', invoke: 'injected', dbTouch: true, calls: ['f2'], phase: 'the save arrives' },
      { id: 'f2', actor: 'FraudCheckService', method: 'runFraudCheck', classTx: { slot: 'classTx2' }, methodTx: null,
        visibility: 'public', invoke: { slot: 'invoke2' }, bulkhead: { slot: 'bulkhead' }, calls: ['f3'], phase: 'the check is reached' },
      { id: 'f3', actor: 'FraudCheckService', method: 'call', classTx: { slot: 'classTx2' }, methodTx: { slot: 'methodTx3' },
        visibility: { slot: 'visibility3' }, invoke: { slot: 'invoke3' },
        remote: { takes: { slot: 'remote' }, answers: { slot: 'remote' }, label: 'POST /fraud/check', onFailure: 'FraudCheckUnavailableException', onRefusal: 'FraudCheckRefusedException' } },
    ],
    actors: [
      { id: 'user', label: 'User\n(browser)', tone: 'edge' },
      { id: 'ClaimService', label: 'ClaimService\n(proxy)', tone: 'plain' },
      { id: 'FraudCheckService', label: 'FraudCheck\nService (proxy)', tone: 'internal' },
      { id: 'bulkhead', label: 'Bulkhead\nfraud-check', tone: 'internal' },
      { id: 'remote', label: 'FraudGateway\n→ insurer', tone: 'service' },
      { id: 'pool', label: 'Hikari pool', tone: 'hot' },
    ],
    discoveries: ['tx-owns-connection', 'self-invocation', 'refuse-not-queue', 'rollback-on-exception',
      'suspension-not-release', 'pool-starvation', 'two-connections', 'checked-no-rollback', 'timeout-order'],
  };
  // the external slot is one object; the frame reads two of its fields
  scenario.frames[2].remote.takes = { slot: 'remote', field: 'takes' };
  scenario.frames[2].remote.answers = { slot: 'remote', field: 'answers' };
  scenario.frames[2].remote.reason = { slot: 'remote', field: 'reason' };

  root.TxPlay = root.TxPlay || {};
  (root.TxPlay.scenarios = root.TxPlay.scenarios || []).push(scenario);
  if (typeof module !== 'undefined') module.exports = scenario;
})(typeof window !== 'undefined' ? window : globalThis);
```

Add `field` support to `resolve` in `engine.js` (one line):

```js
if (node.slot) { const v = slotValue(scenario, values, node.slot); return resolve(node.field ? (v == null ? null : v[node.field]) : v, scenario, values); }
```

- [ ] **Step 4: Write template.js**

```js
// src/template.js
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

  const KW = /\b(public|private|protected|class|return|new|final|void|int|throw|throws|static)\b/g;
  function highlight(text) {
    return esc(text)
      .replace(/(\/\/[^\n]*|#[^\n]*)/g, '<span class="cm">$1</span>')
      .replace(/(^|\n)(\s*)(@\w+(?:\([^)]*\))?)/g, '$1$2<span class="ann">$3</span>')
      .replace(KW, '<span class="kw">$1</span>')
      .replace(/\b([A-Z][A-Za-z]+)\b(?![^<]*>)/g, '<span class="ty">$1</span>');
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `node --test tests/`
Expected: PASS. If `scenario1` "as designed" reports `refused !== 8`, check the `field` resolution in `engine.js`.

- [ ] **Step 6: Commit**

```bash
cd ~/projects/blog && git add transactions/src/scenarios/01-edit-calls-out.js transactions/src/template.js transactions/src/engine.js transactions/tests/scenario1.test.js transactions/tests/template.test.js && git commit -m "transactions: scenario 1 and the code template renderer"
```

---

### Task 7: The timeline becomes a diagram spec

**Files:**
- Create: `transactions/src/diagram.js`
- Test: `transactions/tests/diagram.test.js`

**Interfaces:**
- Consumes: `run` from `simulate`, `scenario.actors`, `scenario.frames`.
- Produces: `toDiagramSpec(scenario, run, values) → spec` for `renderSequence`, showing `values.showUser` (default slot value).

- [ ] **Step 1: Write the failing tests**

```js
// tests/diagram.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const scenario = require('../src/scenarios/01-edit-calls-out.js');
const { simulate } = require('../src/engine.js');
const { toDiagramSpec } = require('../src/diagram.js');
const { renderSequence } = require('../src/seqrender.js');

test('user 5 refused: a short green rail, a refused step, a dropped remote step, a 503', () => {
  const run = simulate(scenario, {});
  const spec = toDiagramSpec(scenario, run, {});
  const labels = spec.steps.map(s => s.label);
  assert.ok(labels.includes('PUT /claims/{id}'));
  assert.ok(labels.some(l => /BulkheadFullException/.test(l)));
  assert.ok(labels.includes('ROLLBACK'));
  const dropped = spec.steps.find(s => s.tone === 'dropped');
  assert.equal(dropped.to, 'remote');
  assert.deepEqual(spec.rails.map(r => r.tone), ['good']);
  assert.match(spec.steps[spec.steps.length - 1].label, /^503/);
  assert.ok(spec.legend.some(l => l.tone === 'dropped'));
  assert.ok(renderSequence(spec).startsWith('<svg'));
});

test('user 1 saved: a red rail spanning the remote call, a 200 after 45 s', () => {
  const run = simulate(scenario, { showUser: 1 });
  const spec = toDiagramSpec(scenario, run, { showUser: 1 });
  const http = spec.steps.find(s => s.to === 'remote' && s.arrow === 'request');
  assert.equal(http.tone, 'hot');
  assert.match(http.note, /holding c1/);
  assert.deepEqual(spec.rails.map(r => r.tone), ['hot']);
  assert.match(spec.rails[0].label, /45 s/);
  assert.match(spec.steps[spec.steps.length - 1].note, /t = 45/);
  assert.ok(spec.steps.some(s => s.phase === 'the save arrives'));
});

test('a self-invocation is drawn as a self arrow that says the proxy is not consulted', () => {
  const run = simulate(scenario, { showUser: 1, methodTx3: 'NOT_SUPPORTED' });
  const spec = toDiagramSpec(scenario, run, { showUser: 1, methodTx3: 'NOT_SUPPORTED' });
  const self = spec.steps.find(s => s.arrow === 'self' && /call\(/.test(s.label));
  assert.match(self.sub, /proxy is not consulted/);
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test tests/diagram.test.js`
Expected: FAIL, module not found.

- [ ] **Step 3: Implement diagram.js**

```js
// src/diagram.js
(function (root) {
  const E = typeof require === 'function' ? require('./engine.js') : root.TxPlay;

  function fmt(t) { return t >= 1 ? (Math.round(t * 10) / 10) + ' s' : Math.round(t * 1000) + ' ms'; }

  function toDiagramSpec(scenario, run, values) {
    values = values || {};
    const showUser = Number(E.slotValue(scenario, values, 'showUser') || 1);
    const events = run.timeline.filter(e => e.user === showUser);
    const actorId = a => (scenario.actorOf && scenario.actorOf[a]) || a;
    const frameOf = id => run.frames.find(f => f.id === id);
    const steps = [], rails = [], stack = ['user'], open = {};
    const usedTones = new Set();
    const push = s => { if (s.tone) usedTones.add(s.tone); steps.push(s); return steps.length - 1; };
    const remoteReached = events.some(e => e.event === 'httpStart');
    let pendingPhase = null;

    for (const e of events) {
      const a = actorId(e.actor), d = e.detail, top = stack[stack.length - 1];
      const phase = () => { const p = pendingPhase; pendingPhase = null; return p || undefined; };
      switch (e.event) {
        case 'call': {
          pendingPhase = d.phase || pendingPhase;
          const f = frameOf(d.frame);
          if (!d.viaProxy) {
            push({ from: a, to: a, arrow: 'self', label: `${d.method}()`, phase: phase(),
              sub: d.ignoredAnnotation ? 'self-invocation: the proxy is not consulted, its annotation is ignored' : 'self-invocation: the proxy is not consulted', tone: 'internal' });
          } else {
            const label = stack.length === 1 ? (scenario.entryLabel || 'PUT /claims/{id}') : `${d.method}(…)`;
            push({ from: top, to: a, arrow: 'request', label, phase: phase(), tone: stack.length === 1 ? 'edge' : undefined,
              sub: d.propagation ? `through the proxy: @Transactional ${d.propagation}` : 'through the proxy, no transaction attribute' });
          }
          stack.push(a);
          break;
        }
        case 'txBegin': { const last = steps[steps.length - 1]; last.sub = (last.sub ? last.sub + ', ' : '') + 'starts a transaction'; break; }
        case 'txJoin': { const last = steps[steps.length - 1]; last.sub = (last.sub ? last.sub + ', ' : '') + 'joins the open transaction'; break; }
        case 'connAcquired': {
          if (d.autoCommit) {
            push({ from: a, to: 'pool', arrow: 'request', label: 'read outside a transaction', sub: 'takes and returns a connection of its own', tone: 'internal',
              note: d.alsoHolding > 0 ? `a second connection on this thread` : undefined });
          } else {
            const i = push({ from: a, to: 'pool', arrow: 'request', label: 'BEGIN', sub: 'first database touch', tone: 'hot', phase: phase(),
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
          if (!remoteReached && scenario.actors.some(x => x.id === 'remote'))
            push({ from: actorId(run.frames.find(f => f.remote).actor), to: 'remote', arrow: 'request', label: 'never reached', tone: 'dropped', sub: `the remote is not called for user ${showUser}` });
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test tests/diagram.test.js`
Expected: PASS, 3 tests.

- [ ] **Step 5: Commit**

```bash
cd ~/projects/blog && git add transactions/src/diagram.js transactions/tests/diagram.test.js && git commit -m "transactions: derive the sequence diagram from the timeline"
```

---

### Task 8: Explanation and discoveries

**Files:**
- Create: `transactions/src/explain.js`
- Create: `transactions/src/discoveries.js`
- Test: `transactions/tests/explain.test.js`, `transactions/tests/discoveries.test.js`

**Interfaces:**
- Produces:
  - `DISCOVERIES: [{id, title, hint, test(run) → boolean}]`, `detect(run) → string[]`.
  - `explain(scenario, run, values, foundIds) → {paragraphs: string[], chips: [{text, tone}], tryNext: string|null}`.

- [ ] **Step 1: Write the failing tests**

```js
// tests/discoveries.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const scenario = require('../src/scenarios/01-edit-calls-out.js');
const { simulate } = require('../src/engine.js');
const { detect, DISCOVERIES } = require('../src/discoveries.js');

test('nine discoveries exist with unique ids', () => {
  assert.equal(DISCOVERIES.length, 9);
  assert.equal(new Set(DISCOVERIES.map(d => d.id)).size, 9);
});

test('as designed unlocks the four the mockup shows found', () => {
  const ids = detect(simulate(scenario, {}));
  for (const id of ['tx-owns-connection', 'self-invocation', 'refuse-not-queue', 'rollback-on-exception']) assert.ok(ids.includes(id), id);
  assert.ok(!ids.includes('suspension-not-release'));
  assert.ok(!ids.includes('pool-starvation'));
});

test('no ceiling unlocks pool starvation; self-injected unlocks suspension is not release', () => {
  assert.ok(detect(simulate(scenario, scenario.presets['no ceiling'])).includes('pool-starvation'));
  assert.ok(detect(simulate(scenario, scenario.presets['self-injected'])).includes('suspension-not-release'));
});

test('a checked exception that commits unlocks checked-no-rollback', () => {
  const s = JSON.parse(JSON.stringify(scenario));
  s.frames[1].throws = { name: 'AuditFailure', kind: 'checked' };
  assert.ok(detect(simulate(s, { users: 1 })).includes('checked-no-rollback'));
});
```

```js
// tests/explain.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const scenario = require('../src/scenarios/01-edit-calls-out.js');
const { simulate } = require('../src/engine.js');
const { explain } = require('../src/explain.js');

test('the explanation names the hold, the refusal and the rollback with this run\'s numbers', () => {
  const run = simulate(scenario, {});
  const x = explain(scenario, run, {}, []);
  const text = x.paragraphs.join(' ');
  assert.match(text, /4 users? .*hold/i);
  assert.match(text, /45 s/);
  assert.match(text, /refuse/i);
  assert.match(text, /roll(s|ed)? back/i);
  assert.ok(x.chips.some(c => /refused/.test(c.text)));
  assert.ok(x.tryNext && x.tryNext.length > 20);
});

test('tryNext points at a discovery not yet found', () => {
  const run = simulate(scenario, {});
  const all = ['tx-owns-connection', 'self-invocation', 'refuse-not-queue', 'rollback-on-exception', 'suspension-not-release', 'pool-starvation', 'two-connections', 'checked-no-rollback', 'timeout-order'];
  assert.equal(explain(scenario, run, {}, all).tryNext, null);
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test tests/discoveries.test.js tests/explain.test.js`
Expected: FAIL, modules not found.

- [ ] **Step 3: Implement discoveries.js**

```js
// src/discoveries.js
(function (root) {
  const has = (run, ev, pred) => run.timeline.some(e => e.event === ev && (!pred || pred(e)));
  const DISCOVERIES = [
    { id: 'tx-owns-connection', title: 'A transaction owns its connection until it ends', hint: 'first database touch to commit or rollback, whatever happens in between',
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
```

- [ ] **Step 4: Implement explain.js**

```js
// src/explain.js
(function (root) {
  const T = typeof require === 'function' ? Object.assign({}, require('./engine.js'), require('./discoveries.js'), require('./diagram.js')) : root.TxPlay;

  function explain(scenario, run, values, foundIds) {
    values = values || {}; foundIds = foundIds || [];
    const showUser = Number(T.slotValue(scenario, values, 'showUser') || 1);
    const s = run.summary, tl = run.timeline, me = tl.filter(e => e.user === showUser);
    const paragraphs = [];
    const holders = new Set(tl.filter(e => e.event === 'httpStart' && e.detail.holdingConnection).map(e => e.user));
    const remote = run.frames.find(f => f.remote);
    const takes = remote ? T.fmt(tl.find(e => e.event === 'httpStart')?.detail.takes || 0) : null;

    if (holders.size) {
      const started = tl.find(e => e.event === 'txBegin');
      paragraphs.push(`${holders.size} user${holders.size > 1 ? 's' : ''} hold one connection each for the whole ${takes} the remote takes. ` +
        `The remote call runs inside the transaction ${started ? 'started by ' + run.frames.find(f => f.id === started.detail.tx && false)?.method || 'started at the entry point' : ''}, ` +
        `and a resource-local transaction keeps its connection from its first database touch until it commits or rolls back, so nothing releases it while the remote thinks.`);
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
```

Replace the awkward `started by …` fragment in the first paragraph with this exact sentence before running the tests: `The remote call runs inside the transaction started at the entry point,`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `node --test tests/`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd ~/projects/blog && git add transactions/src/explain.js transactions/src/discoveries.js transactions/tests/explain.test.js transactions/tests/discoveries.test.js && git commit -m "transactions: templated explanation and discoveries"
```

---

### Task 9: The page

**Files:**
- Modify: `transactions/index.template.html` (full markup and CSS)
- Create: `transactions/src/ui.js`
- Test: manual in the browser plus `node --test tests/build.test.js`

**Interfaces:**
- Consumes: every `TxPlay.*` function above and `TxPlay.scenarios`.
- Produces: the working page; `localStorage` keys `txplay-found` (JSON array of discovery ids), `txplay-values-<scenarioId>` (JSON slot values).

- [ ] **Step 1: Write the template**

Take the CSS from the mockup `code-playground.html` (`:root` through the end of the `.seq` rules) and its body structure, and make these changes: the app bar tabs, the preset strip, the three left cards, the three right cards and the option strip are generated by `ui.js`, so the body is:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="build" content="__BUILD__">
<meta name="theme-color" content="#1565c0">
<title>Transaction playground</title>
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Roboto+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
/* paste the mockup's CSS here, unchanged, then add: */
.tg select, .tg input { font: inherit; border: 0; background: transparent; color: inherit; padding: 0; }
.tg input[type=text] { width: 5em; }
.key-form { display: flex; gap: 8px; margin-top: 10px; }
.key-form input { flex: 1; border: 1px solid #8a8f98; border-radius: 4px; padding: 6px 10px; font: inherit; }
.muted { color: var(--text2); font-size: 13.5px; }
.err { color: var(--err); }
</style>
</head>
<body>
<div class="appbar"><h1>Transaction playground</h1><div class="tabs" id="tabs"></div></div>
<main>
  <div class="scenario-bar"><h2 id="title"></h2></div>
  <p class="muted" id="intro"></p>
  <div class="scenario-bar" id="presets"></div>
  <div class="grid">
    <div id="left"></div>
    <div id="right">
      <div class="card"><div class="card-head"><span class="file">Timeline</span><span id="timeline-sub"></span></div><div class="section"><div class="canvas" id="diagram"></div></div></div>
      <div class="card"><div class="card-head"><span class="file">What happened, and why</span><span class="muted">templated from the timeline</span></div><div class="section explain" id="explain"></div></div>
      <div class="card"><div class="card-head"><span class="file">Discoveries</span><span id="disc-count" class="role"></span></div><div class="section discover" id="discoveries"></div></div>
    </div>
  </div>
</main>
<script>
__SCRIPTS__
</script>
</body>
</html>
```

- [ ] **Step 2: Write ui.js**

```js
// src/ui.js
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
      state.values = next; renderLeft();
    });
  }

  function renderLeft() {
    const s = state.scenario;
    $('left').innerHTML = s.files.map(f => `<div class="card"><div class="card-head"><span class="file">${esc(f.name)}</span><span>${esc(f.role || '')}</span></div><pre class="code">${P.renderCode(f, s, state.values, state.changed)}</pre></div>`).join('') +
      `<div class="card"><div class="actions"><span class="btn" id="run">Run</span><span class="btn outline" id="ask">Ask Claude to explain this run</span>` +
      (state.changed.size ? `<span class="diffchip">${state.changed.size} change${state.changed.size > 1 ? 's' : ''} since last run</span>` : '') + `</div><div id="ask-out"></div></div>`;
    $('left').querySelectorAll('.tg').forEach(el => el.onclick = () => edit(el));
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
    }
    state.values[name] = next; state.changed.add(name);
    save('txplay-values-' + state.scenario.id, state.values);
    renderLeft();
  }

  function run() {
    const s = state.scenario;
    const run = P.simulate(s, state.values);
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
```

The `prompt()` dialogs are the version-one control: they keep the task small and every slot editable today. A dropdown rendered inside the token is a later task.

- [ ] **Step 3: Build and open**

Run: `cd ~/projects/blog/transactions && make build && make serve`
Open http://localhost:8090/ and check: the tab shows scenario 1, the three code cards render with underlined tokens, Run draws the diagram for user 5, the explanation has paragraphs and chips, four discoveries read FOUND. Click the `@Bulkhead` token, enter an empty value, Run: the diagram shows user 5 saving and the explanation mentions pool timeouts; "Pool exhaustion" flips to FOUND. Reload: found discoveries persist.

- [ ] **Step 4: Run the suite**

Run: `make test`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/projects/blog && git add transactions/index.template.html transactions/index.html transactions/src/ui.js && git commit -m "transactions: the playground page"
```

---

### Task 10: Ask Claude

**Files:**
- Create: `transactions/src/claude.js`
- Test: `transactions/tests/claude.test.js` (prompt construction only; the network call is exercised by hand)

**Interfaces:**
- Produces: `buildPrompt(scenario, run, values, explanation) → string`, `getKey()/setKey(k)/clearKey()`, `askClaude(key, prompt) → Promise<string>`, `askForThisRun(state, outEl)` (used by `ui.js`). Constants `MODEL = 'claude-sonnet-5'`, `KEY_LS = 'txplay-apikey'`, `CACHE_LS = 'txplay-answers'`, cache cap 60.

- [ ] **Step 1: Write the failing test**

```js
// tests/claude.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const scenario = require('../src/scenarios/01-edit-calls-out.js');
const { simulate } = require('../src/engine.js');
const { explain } = require('../src/explain.js');
const { buildPrompt } = require('../src/claude.js');

test('the prompt carries the code, the values, the timeline and the ground-truth instruction', () => {
  const run = simulate(scenario, {});
  const p = buildPrompt(scenario, run, {}, explain(scenario, run, {}, []));
  assert.match(p, /ClaimService/);
  assert.match(p, /"event": ?"refused"/);
  assert.match(p, /ground truth/i);
  assert.match(p, /do not assert any mechanism the timeline does not show/i);
  assert.ok(p.length < 60000);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/claude.test.js`
Expected: FAIL, module not found.

- [ ] **Step 3: Implement claude.js**

```js
// src/claude.js
(function (root) {
  const T = typeof require === 'function' ? Object.assign({}, require('./engine.js'), require('./template.js')) : root.TxPlay;
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
      '', `# Summary`, JSON.stringify(run.summary),
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
```

- [ ] **Step 4: Run tests, build, try by hand**

Run: `node --test tests/ && make build && make serve`. In the browser press "Ask Claude to explain this run": the key form appears; paste a key; the answer renders and a second press is instant (cached). Change a token, Run, ask again: a new answer.

- [ ] **Step 5: Commit**

```bash
cd ~/projects/blog && git add transactions/src/claude.js transactions/tests/claude.test.js transactions/index.html && git commit -m "transactions: ask Claude with the timeline as ground truth"
```

---

### Task 11: Scenarios 2 to 6

**Files:**
- Create: `transactions/src/scenarios/02-nightly-sweep.js`, `03-create-compensation.js`, `04-pool-exhaustion.js`, `05-proxy-bypass.js`, `06-suspension.js`
- Test: `transactions/tests/scenarios.test.js`

**Interfaces:**
- Consumes: the scenario shape from Task 6. Each file follows scenario 1's layout exactly: `files`, `slots`, `presets`, `config`, `entries`, `frames`, `actors`, `discoveries`, plus `short` for the tab label and `entryLabel` for the first arrow.

- [ ] **Step 1: Write the failing tests**

```js
// tests/scenarios.test.js
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test tests/scenarios.test.js`
Expected: FAIL, modules not found.

- [ ] **Step 3: Write the five scenarios**

Each follows scenario 1's file. The domain, frames and presets per scenario:

**02-nightly-sweep** (`short: 'Nightly sweep'`, `entryLabel: 'sweep worker starts'`). Files `ReviewSweep.java` (frame f1 `refresh(claimId)`, no annotation, invoked from the batch; calls f2 then f3 then f4), `FraudCheckService.java` (frames f3 `check` with `{{classTx}}` class annotation, `{{methodTx}}` method annotation, `{{invoke}}` injected or this, remote 45s), and the yaml. Frames: f2 `ReviewSweep.loadAndPrepare` `methodTx: 'REQUIRED'` (stands for `TransactionTemplate.execute`), `dbTouch: true`; f3 as above; f4 `ReviewSweep.store` `methodTx: 'REQUIRED'`, `dbTouch: true`. Slots: `classTx` default `null` choices `[null,'@Transactional']`; `methodTx` default `null` choices `[null,'NOT_SUPPORTED','SUPPORTS']`; `invoke` default `'injected'`; `remote`; pool 10; `users` default 8 (`entryLabel` names workers); `showUser` 1. Presets: `'as designed': {}`, `'transactional check service': { classTx: '@Transactional' }`, `'NOT_SUPPORTED on the call': { classTx: '@Transactional', methodTx: 'NOT_SUPPORTED' }`. Actors: worker (edge), ReviewSweep (plain), FraudCheckService (internal), remote (service), pool (hot). Discoveries: tx-owns-connection, suspension-not-release, timeout-order, two-connections.

**03-create-compensation** (`short: 'Create with compensation'`, `entryLabel: 'POST /claims'`). Files `ClaimCreator.java`: f1 `create` no annotation (`{{classTx1}}` default null, choices `[null,'@Transactional']`), calls f2 `persist` `methodTx: 'REQUIRES_NEW'`, `dbTouch: true`, then f3 `startWorkflow` `methodTx: 'REQUIRED'`, `dbTouch: true`, `compensation: 'delete the claim row persisted by transaction 1'`, calls f4 `RegistryClient.fetchExternalId` remote `{{remote}}` (default takes 3s ok). Presets: `'as designed': {}`, `'the registry is down': { remote: { takes: '3s', answers: '5xx' } }`, `'one transaction over both': { classTx1: '@Transactional' }`. Users default 1. Discoveries: tx-owns-connection, rollback-on-exception, timeout-order.

**04-pool-exhaustion** (`short: 'Pool exhaustion'`, `entryLabel: 'PUT /claims/{id}'`). Scenario 1's frames without a bulkhead slot (bulkhead absent), plus frame g1 `DashboardService.list` `classTx: '@Transactional'`, `dbTouch: true`, no remote, and a second entry `{ root: 'g1', users: { slot: 'browsers' }, startAt: '1s' }`. Slots: `users` default 10, `browsers` default 3, `showUser` default 11, pool 10, remote 45s. Presets: `'as designed': {}`, `'a bigger pool': { poolSize: 20 }`, `'a ceiling of 4': {}` is not possible without a bulkhead slot, so instead `'a shorter remote': { remote: { takes: '2s', answers: 'ok' } }`. Actors add `DashboardService` (plain). Discoveries: pool-starvation, tx-owns-connection.

**05-proxy-bypass** (`short: 'Proxy bypass'`, `entryLabel: 'PUT /claims/{id}'`). Scenario 1's files and frames with `users` default 1, `showUser` 1, `invoke3` default `'this'`, `methodTx3` default `'NOT_SUPPORTED'`, `visibility3` default `'package'`, `bulkhead` default null. Presets: `'as designed': {}`, `'self-injected': { invoke3: 'self', visibility3: 'public' }`, `'private': { invoke3: 'self', visibility3: 'private' }`. Discoveries: self-invocation, suspension-not-release.

**06-suspension** (`short: 'Suspension is not release'`, `entryLabel: 'PUT /claims/{id}'`). Scenario 5 with `invoke3` default `'self'`, `visibility3` default `'public'`, `methodTx3` default `'NOT_SUPPORTED'`, and frame f3 `dbTouch: true` (a repository read of the claim's history inside `call`). Presets: `'as designed': {}`, `'REQUIRES_NEW instead': { methodTx3: 'REQUIRES_NEW' }`, `'no annotation': { methodTx3: null }`. Discoveries: suspension-not-release, two-connections, tx-owns-connection.

Write each file completely, copying scenario 1 and editing; do not share code between scenario files.

- [ ] **Step 4: Register them in the build and run everything**

`SRC_ORDER` in `build.py` already lists the five files. Run: `node --test tests/ && make build`.
Expected: PASS, and the page shows six tabs.

- [ ] **Step 5: Commit**

```bash
cd ~/projects/blog && git add transactions/src/scenarios transactions/tests/scenarios.test.js transactions/index.html && git commit -m "transactions: scenarios 2 to 6"
```

---

### Task 12: Hub card, README, deploy

**Files:**
- Modify: `~/projects/blog/index.html` (add a card)
- Modify: `~/projects/blog/README.md` (add a row)
- Create: `transactions/README.md`

- [ ] **Step 1: Add the hub card**

In `index.html`, after the last `<a class="item">` in the group that fits best (add a group `<div class="group">Engineering</div>` before it if none fits):

```html
  <a class="item" href="transactions/">
    <h2>Transaction playground</h2>
    <div class="sub">Spring, connections and proxies as a game</div>
    <p>A small application shown as code. Change an annotation or a timeout
       directly on the code, run it, and read what every thread and every
       database connection did, drawn as a sequence diagram.</p>
    <span class="tag">6 scenarios · 9 discoveries</span>
  </a>
```

- [ ] **Step 2: Add the README row and the folder README**

Row in `README.md`: `| /transactions/ | Transaction playground — Spring transactions, proxies and connection pools as a game with sequence diagrams. | `transactions/` |`

`transactions/README.md`:

```markdown
# Transaction playground

A single page at <https://petmakris.github.io/transactions/>. Six scenarios
of a small Spring application shown as code; every annotation, invocation and
number on the code is a control. Run replays the scenario for every concurrent
user with a discrete-event engine and draws the chosen user's timeline as a
sequence diagram, with an explanation and a set of discoveries to unlock.

    make build     # bake src/ + index.template.html -> index.html
    make test      # node --test tests/
    make serve     # http://localhost:8090/

Design: docs/superpowers/specs/2026-09-05-transaction-playground-design.md
```

- [ ] **Step 3: Build, test, commit, push**

```bash
cd ~/projects/blog/transactions && make test && make build && cd ~/projects/blog && git add index.html README.md transactions && git commit -m "transactions: publish the transaction playground" && git push origin main
```

Open https://petmakris.github.io/transactions/ after Pages deploys and run scenario 1 once.

---

## Self-review

- Spec coverage: folder and build (Task 1, 12), key handling (Task 10), layout (Task 9), scenario format and slot kinds (Task 6), six scenarios (Tasks 6, 11), engine rules (Tasks 2, 4, 5), derived diagram and explanation (Tasks 7, 8), discoveries (Task 8), testing (every task), out of scope (untouched). The `flag` slot kind is declared in scenario 1 as `osiv` and consumed by `resolveConfig`; the `exception` kind is consumed through `frames[].throws`.
- Placeholders: none; every code step is complete. The renderer body in Task 3 is a verbatim copy from a named file, which is the instruction.
- Type consistency: `simulate/resolveFrames/resolveConfig/slotValue` (engine), `toDiagramSpec/fmt` (diagram), `explain` (explain), `DISCOVERIES/detect` (discoveries), `renderCode/controlHtml/displayValue/highlight/esc` (template), `renderSequence` (seqrender), `buildPrompt/askClaude/askForThisRun/getKey/setKey/clearKey` (claude); `ui.js` calls only those names. Event names in `diagram.js`, `discoveries.js` and `explain.js` match the engine's `emit` calls.
