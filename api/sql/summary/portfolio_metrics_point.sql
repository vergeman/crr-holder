-- Materialize filtered inventory for totals and distinct path counts.
WITH holdings AS MATERIALIZED (
    SELECT account_holder, source, sink, hedge_type, mwh
    FROM crr_summary_holdings
    WHERE report_id = :report_id
      AND (:account_holder IS NULL OR account_holder = :account_holder)
      AND source = :settlement_point
    UNION ALL
    -- Exclude self paths already included by their source.
    SELECT account_holder, source, sink, hedge_type, mwh
    FROM crr_summary_holdings
    WHERE report_id = :report_id
      AND (:account_holder IS NULL OR account_holder = :account_holder)
      AND sink = :settlement_point AND source != :settlement_point
), source_sink AS (
    -- Count A-to-B and B-to-A as distinct ordered source-sink pairs.
    SELECT DISTINCT source, sink FROM holdings
)
SELECT COALESCE(SUM(mwh), 0), COUNT(DISTINCT account_holder),
       (SELECT COUNT(*) FROM source_sink),
       COALESCE(SUM(CASE WHEN hedge_type = 'OPT' THEN mwh ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN hedge_type = 'OBL' THEN mwh ELSE 0 END), 0)
FROM holdings
