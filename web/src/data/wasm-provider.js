// Preparation: create the worker only when the WASM provider is used.
let worker;
let nextId = 0;
const pending = new Map();

function query(label, sql, params, signal) {
  if (signal?.aborted) return Promise.reject(signal.reason);
  if (!worker) {
    worker = new Worker(new URL('./sqlite.worker.js', import.meta.url), { type: 'module' });
    worker.onmessage = ({ data: { id, rows, error } }) => {
      const request = pending.get(id);
      if (!request) return;
      request.finish();
      if (error) request.reject(new Error(error));
      else request.resolve(rows);
    };
    worker.onerror = (event) => {
      for (const request of pending.values()) {
        request.finish();
        request.reject(new Error(event.message));
      }
      worker.terminate();
      worker = undefined;
    };
  }

  return new Promise((resolve, reject) => {
    const id = ++nextId;
    const finish = () => {
      pending.delete(id);
      signal?.removeEventListener('abort', abort);
    };
    const abort = () => {
      finish();
      reject(signal.reason);
    };
    pending.set(id, { resolve, reject, finish });
    signal?.addEventListener('abort', abort, { once: true });
    worker.postMessage({ id, label, sql, params });
  });
}

// Transformation: match the API's publication ordering and filter semantics.
async function resolveReport(reportId, signal) {
  if (reportId != null) return reportId;
  const [report] = await query('latest report',
    'SELECT report_id FROM reports ORDER BY publication_date DESC, report_id DESC LIMIT 1',
    [], signal);
  return report.report_id;
}

export const wasmProvider = {
  async getMetadata({ reportId, accountHolder }, signal) {
    reportId = await resolveReport(reportId, signal);
    const reports = await query('reports',
      'SELECT report_id AS reportId, publication_date AS publicationDate FROM reports ' +
      'ORDER BY publication_date DESC, report_id DESC', [], signal);

    // Holder choices depend on report; point choices also depend on holder.
    const accountHolders = await query('account holders', `
      SELECT DISTINCT h.account_holder AS accountHolder, a.legal_name AS legalName
      FROM crr_monthly_holdings h
      JOIN account_holders a ON a.account_holder = h.account_holder
      WHERE h.report_id = ? ORDER BY h.account_holder
    `, [reportId], signal);
    const params = [reportId];
    let where = 'report_id = ?';
    if (accountHolder) {
      where += ' AND account_holder = ?';
      params.push(accountHolder);
    }
    const points = await query('settlement points', `
      -- Relevant holdings and their distinct source-or-sink endpoints.
      WITH holdings AS (
        SELECT source, sink FROM crr_monthly_holdings WHERE ${where}
      ), points AS (
        SELECT source AS point FROM holdings UNION SELECT sink FROM holdings
      )
      SELECT s.settlement_point FROM points p
      JOIN settlement_points s ON s.settlement_point = p.point
      ORDER BY s.settlement_point
    `, params, signal);

    // Output: preserve the HTTP provider's response shape.
    return { reportId, reports, accountHolders,
      settlementPoints: points.map((row) => row.settlement_point) };
  },

  async getSummary({ reportId, accountHolder, settlementPoint }, signal) {
    reportId = await resolveReport(reportId, signal);
    const filters = ['report_id = ?'];
    const params = [reportId];
    if (accountHolder) {
      filters.push('account_holder = ?');
      params.push(accountHolder);
    }
    if (settlementPoint) {
      filters.push('(source = ? OR sink = ?)');
      params.push(settlementPoint, settlementPoint);
    }

    // Each monthly row contributes once; reversed paths stay distinct.
    const [row] = await query('summary', `
      WITH holdings AS (
        SELECT account_holder, source, sink, hedge_type,
               peak_wd_mwh + peak_we_mwh + off_peak_mwh AS mwh
        FROM crr_monthly_holdings WHERE ${filters.join(' AND ')}
      ), points AS (
        -- Unique endpoints across months and instruments.
        SELECT source AS point FROM holdings UNION SELECT sink FROM holdings
      ), paths AS (
        -- Unique directed source-sink pairs.
        SELECT DISTINCT source, sink FROM holdings
      )
      SELECT COALESCE(SUM(mwh), 0) AS totalMwh,
             COUNT(DISTINCT account_holder) AS accountHolderCount,
             (SELECT COUNT(*) FROM points) AS settlementPointCount,
             (SELECT COUNT(*) FROM paths) AS directedPathCount,
             COALESCE(SUM(CASE WHEN hedge_type = 'OPT' THEN mwh ELSE 0 END), 0) AS opt,
             COALESCE(SUM(CASE WHEN hedge_type = 'OBL' THEN mwh ELSE 0 END), 0) AS obl
      FROM holdings
    `, params, signal);

    // Output
    const { opt, obl, ...metrics } = row;
    return { reportId, ...metrics, hedgeTypeMwh: { OPT: opt, OBL: obl } };
  },
};
