# Transaction playground: design

A single-page web game that shows a small Spring application as code, lets the
player change the annotations and the configuration directly on that code, and
draws what happens to every thread and every database connection as a sequence
diagram, with an explanation. It exists because one pull request (montblanc
PMP-272) showed that connection holding, transaction propagation and proxy
semantics are hard to hold in the head and easy to get wrong, and that every
question about them was settled by the same dozen rules.

## Where it lives

- Folder `transactions/` in `~/projects/blog`, served at
  `https://petmakris.github.io/transactions/`, with a card on the hub page.
- One self-contained `index.html`, baked by `build.py` from `index.template.html`
  plus the scenario files, the way Fréquence is built. The build stamps a content
  hash so open tabs reload themselves, and fails on a JavaScript syntax error.
- Deployment is the repo's rule: commit and push to `main`.
- No server. The engine, the renderer, the templated explanation and the
  discoveries work with no key. Only "Ask Claude" needs one.

## The key

Copied from Fréquence. The first press of "Ask Claude" shows a form inside the
explanation card: "This page has no server, so your key is stored only in this
browser and sent straight to Anthropic." The key lives in `localStorage` under
`txplay-apikey`. An error shows "Retry" and "Change API key". Answers are cached
per scenario configuration in `localStorage` with a bounded cache. The provider
is Anthropic's Messages API called directly from the browser with the
direct-browser-access header.

## Layout

App bar with scenario tabs. Under it a preset strip and a reset. Two columns:

- Left: the scenario's files as syntax-highlighted code cards, imports omitted.
  Every slot renders as an underlined token with a dropdown or a number field.
  A token changed since the last run is marked until the next run. Below the
  files: Run, Ask Claude, and a chip counting changes since the last run.
- Right: the timeline card (the diagram), the explanation card, the discoveries
  card.

Light theme, high contrast, Material-like: Roboto, blue app bar, white cards.
The diagram uses the sequence renderer and stylesheet from the annotate skill's
JavaScript port, light palette only.

## A scenario

One authored JavaScript module per scenario, baked in by the build.

```js
export default {
  id, title, intro,
  files: [{ name, role, code }],        // code is a template with {{slot}} markers
  slots: { name: { kind, target?, default, choices? } },
  presets: { "as designed": {}, "no ceiling": { bulkhead: null }, ... },
  frames: [ ... ],                       // the call chain the engine runs, referencing slots
  actors: [ ... ],                       // diagram columns, in order
  discoveries: [ ... ]                   // ids this scenario can unlock
}
```

The page never lets the code and the simulation disagree: the code is the
template rendered with the current slot values, and the engine reads the same
slot values through `frames`.

### Slot kinds, version one

| kind | values | engine input |
|---|---|---|
| annotation | none, or `@Transactional` with a propagation; `readOnly`, `rollbackFor` when offered | effective transaction attribute per frame |
| invocation | `this` (self-invocation) or an injected bean, including a self-injected proxy | whether the proxy is consulted |
| visibility | public, package-private, private | whether a class-based proxy can advise the method |
| bulkhead | absent, or permits and max wait | ceiling per named bulkhead |
| external | how long the remote takes; ok, late, refuses 4xx, fails 5xx, unreachable | remote outcome and duration |
| exception | which frame throws; runtime or checked | rollback semantics |
| number | pool size, connection-timeout, connect-timeout, read-timeout, concurrent users, which user to show | limits and load |
| flag | open-session-in-view; resource-local shown as a locked label | detachment rule |

### The first six scenarios

The six cases PMP-272 lived through, with an invented domain (claims and an
external fraud check) so no proposal or orders name appears:

1. An edit that asks an external system before it commits (the mockup).
2. A nightly sweep that splits its work into two transactions around the call.
3. A create that commits first and compensates by deleting on failure.
4. Pool exhaustion starving pages that never called out.
5. The proxy bypass: `this.call()` versus a self-injected bean.
6. Suspension is not release: `NOT_SUPPORTED` reached through the proxy.

## The engine

A small interpreter over the frames, run once per concurrent user against a
shared pool and shared bulkheads, producing timestamped events. Rules, each a
named function with a golden test:

- A call reaches the proxy only through an injected bean, and only if the
  method is not private.
- Through the proxy the effective annotation is the method's, else the
  class's. REQUIRED joins or starts. REQUIRES_NEW suspends and starts.
  NOT_SUPPORTED suspends. SUPPORTS joins or runs without. NEVER and MANDATORY
  throw.
- A transaction takes a connection when it begins, because Hibernate acquires
  the JDBC connection at BEGIN to switch off auto-commit (measured on the real
  stack: a transaction with no database work still held one), and holds it
  until commit or rollback. Suspension keeps it. A second transaction on the
  same thread takes a second connection.
- A thread with no free connection waits up to connection-timeout, then fails.
- A remote call lasts the smaller of its answer time and read-timeout. An
  unreachable remote fails at connect-timeout.
- A bulkhead with no free permit refuses at once when its wait is zero, and
  otherwise waits, holding whatever the thread already holds.
- A runtime exception marks every joined transaction rollback-only up to the
  outermost boundary. A checked exception does not, unless `rollbackFor` names
  it.
- With open-session-in-view off, an entity read outside a transaction is
  detached; touching a lazy association on it fails.

Output record:

```
timeline[]   t, thread, actor, event, detail
             events: txBegin, connAcquired, poolWait, poolTimeout, suspend, resume,
                     httpStart, httpEnd, httpTimeout, refused, exception,
                     rollbackOnly, rollback, commit, connReleased, detachedRead
summary      connectionsHeld, longestHold, callersRefused, callersTimedOut, dataSaved
diagram      the renderer's spec: actors, steps, rails, phases, legend
explanation  templated sentences, one per rule that fired, with this run's numbers
```

## Diagram and explanation, derived

Each frame is an actor, plus the pool, each bulkhead, and the remote. Each event
is one step: a call is a request arrow; a return or an exception is a dashed
event arrow; a wait is a self arrow with its duration in the note column; commit
and rollback are arrows to the pool. Every interval during which a thread holds
a connection is a rail on the pool's lifeline, red when it spans a remote call,
green when short. Tones are fixed: red for a hold across a remote call and for a
failure, green for a release or a successful end, amber for steps inside the
application, teal for the remote, grey struck through for a step never reached.
The legend lists only the tones used. Phase labels come from the scenario's
frame groups.

The templated explanation is always present. The Claude explanation is optional:
the prompt carries the rendered code, the slot values, the timeline and the
templated explanation, and asks for a rewrite for a developer who does not yet
hold the mechanism, with the instruction that the timeline is ground truth and
no mechanism may be asserted that the timeline does not show. The engine decides
what happened; Claude only says it better.

## Discoveries

Nine mechanisms, each a predicate over a run's timeline, unlocked the first time
any run satisfies it and remembered in `localStorage`:

1. A transaction owns its connection until it ends.
2. Self-invocation never reaches the proxy.
3. Refuse rather than queue.
4. A failure inside the transaction rolls the edit back.
5. Suspension is not release.
6. Pool exhaustion starves unrelated requests.
7. Two connections on one thread.
8. Checked exceptions do not roll back.
9. Which timeout fires first.

Each carries a one-line hint and, once found, the run that found it. The
explanation's "try next" line points at a locked discovery this scenario can
still unlock.

## Testing

- Golden tests per engine rule and per scenario preset, asserting the exact
  timeline. Seeded from the facts PMP-272 measured: one connection still held
  under a suspended transaction; four checks in flight then refusal; the sweep
  holding nothing during the remote call.
- Snapshot test per scenario diagram.
- `build.py` fails on a JavaScript syntax error, as Fréquence's does.
- No Spring runs in version one.

## Out of scope for version one

- Reading montblanc's code to build a scenario (the code-reading shape).
- JTA, reactive stacks, other frameworks.
- A live measurement harness.
- More than one model provider.

Each is a later folder or a later slot kind; none changes the scenario file
format.
