-- Aggregate only the selected page, retaining the portfolio filters.
SELECT source, delivery_month, hedge_type,
       SUM(peak_wd_mwh + peak_we_mwh + off_peak_mwh)
FROM crr_monthly_holdings
WHERE report_id = :report_id
  AND account_holder = :account_holder
  AND (:settlement_point IS NULL OR source = :settlement_point OR sink = :settlement_point)
  AND source IN (SELECT value FROM json_each(:sources))
GROUP BY source, delivery_month, hedge_type
