(function (root) {
  const scenario = {
    id: 'create-compensation',
    short: 'Create with compensation',
    entryLabel: 'POST /claims',
    title: 'A create that commits first and compensates by deleting on failure',
    intro: 'A new claim needs an identifier from an external registry, and the registry wants our own id in the request. Our id only exists once the row is inserted, so the create commits the row first, then calls the registry in a second transaction. If that call fails, the row is deleted by hand: a compensation, not a rollback.',
    files: [
      { name: 'ClaimCreator.java', role: 'frames 1 to 3: two transactions, deliberately', code:
`@Service
{{classTx1}}
public class ClaimCreator {

    private final ClaimRepository claims;
    private final RegistryClient registry;
    private final ClaimCreator self;                     // self-injected proxy, so the annotations below apply

    public Claim create(ClaimDraft draft) {
        Claim claim = self.persist(draft);               // transaction 1: the row exists, the id is known
        try {
            return self.startWorkflow(claim);            // transaction 2: calls out, then updates the row
        } catch (RuntimeException e) {
            claims.delete(claim);                        // compensation: the row from transaction 1 is removed
            throw e;
        }
    }

    @Transactional(propagation = REQUIRES_NEW)
    public Claim persist(ClaimDraft draft) { return claims.save(Claim.from(draft)); }

    @Transactional
    public Claim startWorkflow(Claim claim) {
        claim.setExternalId(registry.register(claim.getId()));   // {{remote}}
        return claims.save(claim);
    }
}` },
      { name: 'application.yml', role: 'the numbers the timeline is computed from', code:
`datasource:
  hikari:
    maximum-pool-size: {{poolSize}}
    connection-timeout: {{connectionTimeout}}
spring:
  cloud.openfeign.client.config.registry:
    connect-timeout: {{connectTimeout}}
    read-timeout: {{readTimeout}}
load:
  concurrent-users-creating: {{users}}
  show-user: {{showUser}}` },
    ],
    slots: {
      classTx1: { kind: 'annotation', target: 'class', default: null, choices: [null, '@Transactional'],
        help: 'With a class-level @Transactional, create() itself starts a transaction and both inner calls join it: one transaction over both.' },
      remote: { kind: 'external', default: { takes: '3s', answers: 'ok' } },
      poolSize: { kind: 'number', default: 10 },
      connectionTimeout: { kind: 'number', default: '30s' },
      connectTimeout: { kind: 'number', default: '10s' },
      readTimeout: { kind: 'number', default: '60s' },
      users: { kind: 'number', default: 1 },
      showUser: { kind: 'number', default: 1 },
    },
    presets: {
      'as designed': {},
      'the registry is down': { remote: { takes: '3s', answers: '5xx' } },
      'one transaction over both': { classTx1: '@Transactional' },
      'twelve at once, registry slow': { users: 12, remote: { takes: '45s', answers: 'late' }, showUser: 11 },
    },
    config: { poolSize: { slot: 'poolSize' }, connectionTimeout: { slot: 'connectionTimeout' },
      connectTimeout: { slot: 'connectTimeout' }, readTimeout: { slot: 'readTimeout' }, osiv: false },
    entries: [{ root: 'f1', users: { slot: 'users' }, startAt: 0 }],
    frames: [
      { id: 'f1', actor: 'ClaimCreator', method: 'create', classTx: { slot: 'classTx1' }, methodTx: null, visibility: 'public', invoke: 'injected',
        calls: ['f2', 'f3'], phase: 'the create arrives' },
      { id: 'f2', actor: 'ClaimCreator', method: 'persist', classTx: { slot: 'classTx1' }, methodTx: 'REQUIRES_NEW', visibility: 'public', invoke: 'self',
        dbTouch: true, phase: 'transaction 1: the row exists' },
      { id: 'f3', actor: 'ClaimCreator', method: 'startWorkflow', classTx: { slot: 'classTx1' }, methodTx: 'REQUIRED', visibility: 'public', invoke: 'self',
        dbTouch: true, calls: ['f4'], compensation: 'delete the row transaction 1 wrote', phase: 'transaction 2: and it calls out' },
      { id: 'f4', actor: 'RegistryClient', method: 'register', classTx: null, methodTx: null, visibility: 'public', invoke: 'injected',
        remote: { takes: { slot: 'remote', field: 'takes' }, answers: { slot: 'remote', field: 'answers' }, reason: { slot: 'remote', field: 'reason' },
          label: 'POST /registry/claims', onFailure: 'RegistryUnavailableException', onRefusal: 'RegistryRefusedException' } },
    ],
    actors: [
      { id: 'user', label: 'User\n(browser)', tone: 'edge' },
      { id: 'ClaimCreator', label: 'ClaimCreator\n(proxy)', tone: 'plain' },
      { id: 'RegistryClient', label: 'RegistryClient', tone: 'internal' },
      { id: 'remote', label: 'Registry\n(external)', tone: 'service' },
      { id: 'pool', label: 'Hikari pool', tone: 'hot' },
    ],
    discoveries: ['tx-owns-connection', 'rollback-on-exception', 'timeout-order', 'pool-starvation'],
  };

  root.TxPlay = root.TxPlay || {};
  (root.TxPlay.scenarios = root.TxPlay.scenarios || []).push(scenario);
  if (typeof module !== 'undefined') module.exports = scenario;
})(typeof window !== 'undefined' ? window : globalThis);
