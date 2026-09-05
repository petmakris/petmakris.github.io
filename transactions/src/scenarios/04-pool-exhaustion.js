(function (root) {
  const scenario = {
    id: 'pool-exhaustion',
    short: 'Pool exhaustion',
    entryLabel: 'PUT /claims/{id}',
    title: 'Pool exhaustion: the pages that never called out are the ones that fail',
    intro: 'Ten users save claims at the same moment and each save waits on the insurer with its connection held. One second later, three other users open the dashboard, a page that only reads the database. Watch who gets the connection-timeout.',
    files: [
      { name: 'ClaimService.java', role: 'frame 1: the save, holding a connection across the remote call', code:
`@Service
@Transactional
public class ClaimService {

    private final ClaimRepository claims;
    private final FraudCheckService fraudCheck;

    public Claim updateClaim(int id, ClaimEdit edit) {
        Claim claim = claims.findById(id);          // inside the transaction that began at the call
        claim.apply(edit);
        claims.save(claim);
        fraudCheck.runFraudCheck(claim);             // {{remote}}
        return claim;
    }
}` },
      { name: 'DashboardService.java', role: 'frame g1: a page that only reads', code:
`@Service
@Transactional(readOnly = true)
public class DashboardService {

    private final ClaimRepository claims;

    public List<ClaimRow> list(int advisorId) {
        return claims.findOpenBy(advisorId);         // needs one connection for a few milliseconds
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
  users-opening-the-dashboard-one-second-later: {{browsers}}
  show-user: {{showUser}}` },
    ],
    slots: {
      remote: { kind: 'external', default: { takes: '45s', answers: 'late' } },
      poolSize: { kind: 'number', default: 10 },
      connectionTimeout: { kind: 'number', default: '30s' },
      connectTimeout: { kind: 'number', default: '10s' },
      readTimeout: { kind: 'number', default: '60s' },
      users: { kind: 'number', default: 10 },
      browsers: { kind: 'number', default: 3 },
      showUser: { kind: 'number', default: 11 },
    },
    presets: {
      'as designed': {},
      'a bigger pool': { poolSize: 20 },
      'a shorter connection-timeout': { connectionTimeout: '5s' },
      'a faster insurer': { remote: { takes: '2s', answers: 'ok' } },
    },
    config: { poolSize: { slot: 'poolSize' }, connectionTimeout: { slot: 'connectionTimeout' },
      connectTimeout: { slot: 'connectTimeout' }, readTimeout: { slot: 'readTimeout' }, osiv: false },
    entries: [
      { root: 'f1', users: { slot: 'users' }, startAt: 0 },
      { root: 'g1', users: { slot: 'browsers' }, startAt: '1s' },
    ],
    frames: [
      { id: 'f1', actor: 'ClaimService', method: 'updateClaim', classTx: '@Transactional', methodTx: null, visibility: 'public', invoke: 'injected',
        dbTouch: true, calls: ['f2'], phase: 'a save arrives' },
      { id: 'f2', actor: 'FraudCheckService', method: 'runFraudCheck', classTx: '@Transactional', methodTx: null, visibility: 'public', invoke: 'injected',
        remote: { takes: { slot: 'remote', field: 'takes' }, answers: { slot: 'remote', field: 'answers' }, reason: { slot: 'remote', field: 'reason' },
          label: 'POST /fraud/check', onFailure: 'FraudCheckUnavailableException', onRefusal: 'FraudCheckRefusedException' } },
      { id: 'g1', actor: 'DashboardService', method: 'list', classTx: '@Transactional', methodTx: null, visibility: 'public', invoke: 'injected',
        dbTouch: true, phase: 'a dashboard opens, one second later' },
    ],
    actors: [
      { id: 'user', label: 'User\n(browser)', tone: 'edge' },
      { id: 'ClaimService', label: 'ClaimService\n(proxy)', tone: 'plain' },
      { id: 'DashboardService', label: 'Dashboard\nService (proxy)', tone: 'plain' },
      { id: 'FraudCheckService', label: 'FraudCheck\nService (proxy)', tone: 'internal' },
      { id: 'remote', label: 'FraudGateway\n→ insurer', tone: 'service' },
      { id: 'pool', label: 'Hikari pool', tone: 'hot' },
    ],
    discoveries: ['pool-starvation', 'tx-owns-connection', 'timeout-order'],
  };

  root.TxPlay = root.TxPlay || {};
  (root.TxPlay.scenarios = root.TxPlay.scenarios || []).push(scenario);
  if (typeof module !== 'undefined') module.exports = scenario;
})(typeof window !== 'undefined' ? window : globalThis);
