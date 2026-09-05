(function (root) {
  const scenario = {
    id: 'proxy-bypass',
    short: 'Proxy bypass',
    entryLabel: 'PUT /claims/{id}',
    title: 'The proxy bypass: this.call() versus a self-injected proxy',
    intro: 'Every Spring annotation is applied by a proxy that wraps the bean. A call that stays inside the class never meets the proxy, so the annotation on call() below is ignored unless the call goes out through the proxy and comes back in. Change how call() is reached and whether it is private, and watch the same annotation do nothing, something, or throw.',
    files: [
      { name: 'ClaimService.java', role: 'frame 1: the entry point', code:
`@Service
@Transactional
public class ClaimService {

    private final ClaimRepository claims;
    private final FraudCheckService fraudCheck;

    public Claim updateClaim(int id, ClaimEdit edit) {
        Claim claim = claims.findById(id);          // inside the transaction that began at the call
        claims.save(claim.apply(edit));
        fraudCheck.runFraudCheck(claim);
        return claim;
    }
}` },
      { name: 'FraudCheckService.java', role: 'frames 2 and 3: where the bypass lives', code:
`@Service
@Transactional
public class FraudCheckService {

    private final FraudGateway gateway;
    private final FraudCheckService self;            // a self-injected proxy of this very bean

    public Verdict runFraudCheck(Claim claim) {
        return {{invoke3}}.call(prepare(claim));
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
      invoke3: { kind: 'invocation', default: 'this', choices: ['this', 'self'], labels: { this: 'this', self: 'self' },
        help: 'this: a plain self-invocation, no proxy. self: the self-injected proxy, so annotations on call() apply.' },
      methodTx3: { kind: 'annotation', target: 'method', default: 'NOT_SUPPORTED', choices: [null, 'NOT_SUPPORTED', 'REQUIRES_NEW', 'NEVER', 'MANDATORY'] },
      visibility3: { kind: 'visibility', default: 'package', choices: ['private', 'package', 'public'],
        help: 'A class-based proxy can advise package-private and public methods, never a private one.' },
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
      'self-injected': { invoke3: 'self', visibility3: 'public' },
      'private': { invoke3: 'self', visibility3: 'private' },
      'NEVER through the proxy': { invoke3: 'self', visibility3: 'public', methodTx3: 'NEVER' },
    },
    config: { poolSize: { slot: 'poolSize' }, connectionTimeout: { slot: 'connectionTimeout' },
      connectTimeout: { slot: 'connectTimeout' }, readTimeout: { slot: 'readTimeout' }, osiv: false },
    entries: [{ root: 'f1', users: { slot: 'users' }, startAt: 0 }],
    frames: [
      { id: 'f1', actor: 'ClaimService', method: 'updateClaim', classTx: '@Transactional', methodTx: null, visibility: 'public', invoke: 'injected',
        dbTouch: true, calls: ['f2'], phase: 'the save arrives' },
      { id: 'f2', actor: 'FraudCheckService', method: 'runFraudCheck', classTx: '@Transactional', methodTx: null, visibility: 'public', invoke: 'injected',
        calls: ['f3'], phase: 'how is call() reached?' },
      { id: 'f3', actor: 'FraudCheckService', method: 'call', classTx: '@Transactional', methodTx: { slot: 'methodTx3' }, visibility: { slot: 'visibility3' },
        invoke: { slot: 'invoke3' },
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
    discoveries: ['self-invocation', 'suspension-not-release', 'tx-owns-connection'],
  };

  root.TxPlay = root.TxPlay || {};
  (root.TxPlay.scenarios = root.TxPlay.scenarios || []).push(scenario);
  if (typeof module !== 'undefined') module.exports = scenario;
})(typeof window !== 'undefined' ? window : globalThis);
