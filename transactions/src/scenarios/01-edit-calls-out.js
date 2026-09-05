(function (root) {
  const scenario = {
    id: 'edit-calls-out',
    short: 'Edit that calls out',
    entryLabel: 'PUT /claims/{id}',
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
        remote: { takes: { slot: 'remote', field: 'takes' }, answers: { slot: 'remote', field: 'answers' }, reason: { slot: 'remote', field: 'reason' },
          label: 'POST /fraud/check', onFailure: 'FraudCheckUnavailableException', onRefusal: 'FraudCheckRefusedException' } },
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

  root.TxPlay = root.TxPlay || {};
  (root.TxPlay.scenarios = root.TxPlay.scenarios || []).push(scenario);
  if (typeof module !== 'undefined') module.exports = scenario;
})(typeof window !== 'undefined' ? window : globalThis);
