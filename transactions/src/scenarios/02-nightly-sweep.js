(function (root) {
  const scenario = {
    id: 'nightly-sweep',
    short: 'Nightly sweep',
    entryLabel: 'sweep worker starts',
    title: 'A nightly sweep that splits its work into two transactions around the remote call',
    intro: 'Every night a batch re-checks the claims still open. Nobody is waiting, so the sweep reads a claim in one short transaction, calls the fraud check with no transaction open, and writes the verdict in a second short transaction. Eight workers run in parallel against a pool of ten.',
    files: [
      { name: 'ReviewSweep.java', role: 'frame 1: one worker, one claim', code:
`@Component
public class ReviewSweep {

    private final TransactionTemplate tx;              // programmatic, short transactions
    private final ClaimRepository claims;
    private final FraudCheckService fraudCheck;

    public void refresh(int claimId) {
        Prepared p = tx.execute(s -> loadAndPrepare(claimId));   // transaction 1: read, then commit
        Verdict v = {{invoke}}.check(p.payload);                 // no transaction of our own is open here
        tx.executeWithoutResult(s -> store(claimId, v));         // transaction 2: write, then commit
    }
}` },
      { name: 'FraudCheckService.java', role: 'frame 3: the bean that owns the external call', code:
`@Service
{{classTx}}
public class FraudCheckService {

    private final FraudGateway gateway;

    {{methodTx}}
    public Verdict check(Payload payload) {
        return gateway.check(payload);                 // {{remote}}
    }
}` },
      { name: 'application.yml', role: 'the numbers the timeline is computed from', code:
`datasource:
  hikari:
    maximum-pool-size: {{poolSize}}
    connection-timeout: {{connectionTimeout}}
spring:
  jpa:
    open-in-view: false
  cloud.openfeign.client.config.fraud-gateway:
    connect-timeout: {{connectTimeout}}
    read-timeout: {{readTimeout}}
load:
  sweep-workers: {{users}}
  show-worker: {{showUser}}` },
    ],
    slots: {
      invoke: { kind: 'invocation', default: 'injected', choices: ['injected'], labels: { injected: 'fraudCheck' } },
      classTx: { kind: 'annotation', target: 'class', default: null, choices: [null, '@Transactional'] },
      methodTx: { kind: 'annotation', target: 'method', default: null, choices: [null, 'NOT_SUPPORTED', 'SUPPORTS', 'REQUIRED'] },
      remote: { kind: 'external', default: { takes: '45s', answers: 'late' } },
      poolSize: { kind: 'number', default: 10 },
      connectionTimeout: { kind: 'number', default: '30s' },
      connectTimeout: { kind: 'number', default: '10s' },
      readTimeout: { kind: 'number', default: '60s' },
      users: { kind: 'number', default: 8 },
      showUser: { kind: 'number', default: 1 },
    },
    presets: {
      'as designed': {},
      'transactional check service': { classTx: '@Transactional' },
      'NOT_SUPPORTED on the call': { classTx: '@Transactional', methodTx: 'NOT_SUPPORTED' },
      'the insurer is slow': { remote: { takes: '90s', answers: 'late' } },
    },
    config: { poolSize: { slot: 'poolSize' }, connectionTimeout: { slot: 'connectionTimeout' },
      connectTimeout: { slot: 'connectTimeout' }, readTimeout: { slot: 'readTimeout' }, osiv: false },
    entries: [{ root: 'f1', users: { slot: 'users' }, startAt: 0 }],
    frames: [
      { id: 'f1', actor: 'ReviewSweep', method: 'refresh', classTx: null, methodTx: null, visibility: 'public', invoke: 'injected',
        calls: ['f2', 'f3', 'f4'], phase: 'a worker picks up a claim' },
      { id: 'f2', actor: 'ReviewSweep', method: 'loadAndPrepare', classTx: null, methodTx: 'REQUIRED', visibility: 'public', invoke: 'injected',
        dbTouch: true, phase: 'transaction 1: read' },
      { id: 'f3', actor: 'FraudCheckService', method: 'check', classTx: { slot: 'classTx' }, methodTx: { slot: 'methodTx' }, visibility: 'public',
        invoke: { slot: 'invoke' }, phase: 'the remote is asked',
        remote: { takes: { slot: 'remote', field: 'takes' }, answers: { slot: 'remote', field: 'answers' }, reason: { slot: 'remote', field: 'reason' },
          label: 'POST /fraud/check', onFailure: 'FraudCheckUnavailableException', onRefusal: 'FraudCheckRefusedException' } },
      { id: 'f4', actor: 'ReviewSweep', method: 'store', classTx: null, methodTx: 'REQUIRED', visibility: 'public', invoke: 'injected',
        dbTouch: true, phase: 'transaction 2: write' },
    ],
    actors: [
      { id: 'user', label: 'Sweep\nworker', tone: 'edge' },
      { id: 'ReviewSweep', label: 'ReviewSweep', tone: 'plain' },
      { id: 'FraudCheckService', label: 'FraudCheck\nService (proxy)', tone: 'internal' },
      { id: 'remote', label: 'FraudGateway\n→ insurer', tone: 'service' },
      { id: 'pool', label: 'Hikari pool', tone: 'hot' },
    ],
    discoveries: ['tx-owns-connection', 'suspension-not-release', 'timeout-order', 'two-connections'],
  };

  root.TxPlay = root.TxPlay || {};
  (root.TxPlay.scenarios = root.TxPlay.scenarios || []).push(scenario);
  if (typeof module !== 'undefined') module.exports = scenario;
})(typeof window !== 'undefined' ? window : globalThis);
