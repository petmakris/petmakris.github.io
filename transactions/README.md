# Transaction playground

A single page at <https://petmakris.github.io/transactions/>. Six scenarios
of a small Spring application shown as code; every annotation, invocation and
number on the code is a control. Run replays the scenario for every concurrent
user with a discrete-event engine and draws the chosen user's timeline as a
sequence diagram, with an explanation and a set of discoveries to unlock.

    make build     # bake src/ + index.template.html -> index.html
    make test      # node --test tests/*.test.js
    make serve     # http://localhost:8090/

```
index.template.html     markup + CSS; __SCRIPTS__ and __BUILD__ placeholders
build.py                concatenates src/ in order, checks JS syntax, writes index.html
src/seqrender.js        the sequence renderer (verbatim from the annotate skill's JS port)
src/rules.js            proxy reach, effective @Transactional, propagation, rollback rule
src/engine.js           discrete-event engine: simulate(scenario, values) -> timeline
src/diagram.js          timeline -> renderer spec
src/explain.js          timeline -> templated explanation, chips, "try next"
src/discoveries.js      the nine mechanisms and their predicates
src/template.js         code templates with {{slot}} controls
src/claude.js           key in localStorage, prompt, Messages API, answer cache
src/ui.js               page wiring
src/scenarios/*.js      one scenario per file
tests/*.test.js         node --test
```

Design: `docs/superpowers/specs/2026-09-05-transaction-playground-design.md`.
Plan: `docs/superpowers/plans/2026-09-05-transaction-playground.md`.
