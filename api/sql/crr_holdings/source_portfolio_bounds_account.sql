-- Stop at the first nonzero exposure from each end of the timeline.
SELECT (
    SELECT delivery_month FROM crr_monthly_holdings
    WHERE report_id = :report_id
      AND account_holder = :account_holder
      AND (:settlement_point IS NULL OR source = :settlement_point OR sink = :settlement_point)
      AND peak_wd_mwh + peak_we_mwh + off_peak_mwh != 0
    ORDER BY delivery_month ASC LIMIT 1
), (
    SELECT delivery_month FROM crr_monthly_holdings
    WHERE report_id = :report_id
      AND account_holder = :account_holder
      AND (:settlement_point IS NULL OR source = :settlement_point OR sink = :settlement_point)
      AND peak_wd_mwh + peak_we_mwh + off_peak_mwh != 0
    ORDER BY delivery_month DESC LIMIT 1
)
