-- Point lookups do not order months; aggregate their matches once.
SELECT MIN(delivery_month), MAX(delivery_month)
FROM crr_monthly_holdings
WHERE report_id = :report_id
      AND (source = :settlement_point OR sink = :settlement_point)
      AND peak_wd_mwh + peak_we_mwh + off_peak_mwh != 0
