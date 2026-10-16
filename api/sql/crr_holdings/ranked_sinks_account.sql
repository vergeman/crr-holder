-- Rank full-horizon sinks by combined MWh, then identifier for ties.
SELECT sink,
       SUM(CASE WHEN hedge_type = 'OPT'
           THEN peak_wd_mwh + peak_we_mwh + off_peak_mwh ELSE 0 END) AS total_opt_mwh,
       SUM(CASE WHEN hedge_type = 'OBL'
           THEN peak_wd_mwh + peak_we_mwh + off_peak_mwh ELSE 0 END) AS total_obl_mwh
FROM crr_monthly_holdings WHERE report_id = :report_id
  AND account_holder = :account_holder
  AND (:settlement_point IS NULL OR source = :settlement_point OR sink = :settlement_point)
  AND source = :source
GROUP BY sink
ORDER BY total_opt_mwh + total_obl_mwh DESC, sink ASC
