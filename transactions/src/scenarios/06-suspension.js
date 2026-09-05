(function (root) {
  const scenario = {
    id: 'suspension',
    short: 'Suspension is not release',
    entryLabel: 'PUT /claims/{id}',
    title: 'Suspension is not release: NOT_SUPPORTED keeps the connection',
    intro: 'A tempting fix for a connection held across a remote call is to mark the calling method NOT_SUPPORTED so the transaction is suspended around it. It is suspended. It also keeps its connection, because a resource-local transaction owns its connection until it ends, and a suspended transaction has not ended. A repository read inside the suspended section then opens a second one.',
    files: [
      { name: 'ClaimService.java', role: 'frame 1: the entry point', code:
`@Service
@Transactional
public class ClaimService {

    private final ClaimRepository claims;
    private final FraudCheckService fraudCheck;

    public Claim updateClaim(int id, ClaimEdit edit) {
        Claim claim = claims.findById(id);          // the transaction already holds connection 1
        claims.save(claim.apply(edit));
        fraudCheck.runFraudCheck(claim);
        return claim;
    }
}` },
      { name: 'FraudCheckService.java', role: 'frames 2 and 3: the suspended section', code:
`@Service
@Transactional
public class FraudCheckService {

    private final FraudGateway gateway;
    private final ClaimHistoryRepository history;
    private final FraudCheckService self;            // self-injected proxy: the annotation on call() applies

    public Verdict runFraudCheck(Claim claim) {
        return {{invoke3}}.call(prepare(claim));
    }

    {{methodTx3}}
    {{visibility3}} Verdict call(Payload payload) {
        payload.attach(history.recentFor(payload.claimId()));   // a repository read inside the suspended section
        return gateway.check(payload);                           // {{remote}}
    }
}` },
      { name: 'application.yml', role: 'the numbers the timeline is computed from', code:
`datasource:
  hikari:
    maximum-pool-size: {{poolSize}}
    connection-timeout: {{connectionTimeout}}
spring:
  cloud.openfeign.client.config.fraud-gateway:
    connect-timeout: {{connectTimeout}}
    read-timeout: {{readTimeout}}
load:
  concurrent-users-saving: {{users}}
  show-user: {{showUser}}` },
    ],
    slots: {
      invoke3: { kind: 'invocation', default: 'self', choices: ['this', 'self'], labels: { this: 'this', self: 'self' } },
      methodTx3: { kind: 'annotation', target: 'method', default: 'NOT_SUPPORTED', choices: [null, 'NOT_SUPPORTED', 'REQUIRES_NEW', 'SUPPORTS'] },
      visibility3: { kind: 'visibility', default: 'public', choices: ['private', 'package', 'public'] },
      remote: { kind: 'external', default: { takes: '45s', answers: 'late' } },
      poolSize: { kind: 'number', default: 10 },
      connectionTimeout: { kind: 'number', default: '30s' },
      connectTimeout: { kind: 'number', default: '10s' },
      readTimeout: { kind: 'number', default: '60s' },
      users: { kind: 'number', default: 1 },
      showUser: { kind: 'number', default: 1 },
    },
    presets: {
      'as designed': {},
      'REQUIRES_NEW instead': { methodTx3: 'REQUIRES_NEW' },
      'no annotation': { methodTx3: null },
      'six users, pool of ten': { users: 6, showUser: 6 },
    },
    config: { poolSize: { slot: 'poolSize' }, connectionTimeout: { slot: 'connectionTimeout' },
      connectTimeout: { slot: 'connectTimeout' }, readTimeout: { slot: 'readTimeout' }, osiv: false },
    entries: [{ root: 'f1', users: { slot: 'users' }, startAt: 0 }],
    frames: [
      { id: 'f1', actor: 'ClaimService', method: 'updateClaim', classTx: '@Transactional', methodTx: null, visibility: 'public', invoke: 'injected',
        dbTouch: true, calls: ['f2'], phase: 'the save arrives' },
      { id: 'f2', actor: 'FraudCheckService', method: 'runFraudCheck', classTx: '@Transactional', methodTx: null, visibility: 'public', invoke: 'injected',
        calls: ['f3'], phase: 'the suspended section' },
      { id: 'f3', actor: 'FraudCheckService', method: 'call', classTx: '@Transactional', methodTx: { slot: 'methodTx3' }, visibility: { slot: 'visibility3' },
        invoke: { slot: 'invoke3' }, dbTouch: true,
        remote: { takes: { slot: 'remote', field: 'takes' }, answers: { slot: 'remote', field: 'answers' }, reason: { slot: 'remote', field: 'reason' },
          label: 'POST /fraud/check', onFailure: 'FraudCheckUnavailableException', onRefusal: 'FraudCheckRefusedException' } },
    ],
    actors: [
      { id: 'user', label: 'User\n(browser)', tone: 'edge' },
      { id: 'ClaimService', label: 'ClaimService\n(proxy)', tone: 'plain' },
      { id: 'FraudCheckService', label: 'FraudCheck\nService (proxy)', tone: 'internal' },
      { id: 'remote', label: 'FraudGateway\n→ insurer', tone: 'service' },
      { id: 'pool', label: 'Hikari pool', tone: 'hot' },
    ],
    discoveries: ['suspension-not-release', 'two-connections', 'tx-owns-connection'],
  };

  root.TxPlay = root.TxPlay || {};
  (root.TxPlay.scenarios = root.TxPlay.scenarios || []).push(scenario);
  if (typeof module !== 'undefined') module.exports = scenario;
})(typeof window !== 'undefined' ? window : globalThis);
