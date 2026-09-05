(function (root) {
  const api = {};
  root.TxPlay = Object.assign(root.TxPlay || {}, api);
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
