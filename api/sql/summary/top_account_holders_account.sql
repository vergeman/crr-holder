-- Match inventory from one publication snapshot.
WITH holdings AS (
    SELECT account_holder, source, sink, hedge_type, mwh
    FROM crr_summary_holdings
    WHERE report_id = :report_id
      AND account_holder = :account_holder
), totals AS (
    -- Aggregate inventory before joining directory names.
    SELECT account_holder, SUM(mwh) AS total_mwh
    FROM holdings GROUP BY account_holder
)
SELECT t.account_holder, a.legal_name, t.total_mwh
FROM totals t
LEFT JOIN account_holders a ON a.account_holder = t.account_holder
-- Compare unrounded totals first; identifiers resolve ties.
ORDER BY t.total_mwh DESC, t.account_holder ASC LIMIT 100
