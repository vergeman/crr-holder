-- Full-horizon totals are already summed across months.
WITH holdings AS (
    SELECT source, hedge_type, mwh
    FROM crr_summary_holdings
    WHERE report_id = :report_id
      AND (:account_holder IS NULL OR account_holder = :account_holder)
)
SELECT source,
       SUM(CASE WHEN hedge_type = 'OPT' THEN mwh ELSE 0 END) AS total_opt_mwh,
       SUM(CASE WHEN hedge_type = 'OBL' THEN mwh ELSE 0 END) AS total_obl_mwh
FROM holdings
GROUP BY source
-- Compare combined totals first; source identifiers resolve ties.
ORDER BY total_opt_mwh + total_obl_mwh DESC, source ASC
LIMIT :limit OFFSET :offset
