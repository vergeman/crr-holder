-- Summary filters retain accounts and paths; months and TOU collapse into MWh.
INSERT INTO crr_summary_holdings
SELECT report_id, account_holder, source, sink, hedge_type,
       SUM(peak_wd_mwh + peak_we_mwh + off_peak_mwh)
FROM crr_monthly_holdings
GROUP BY report_id, account_holder, source, sink, hedge_type;
