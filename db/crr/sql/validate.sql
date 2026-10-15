-- Called during each build, before replacing the output; the fixture uses it too.

-- Expand raw contracts independently of the materialization query.
WITH RECURSIVE expanded AS (
    SELECT report_id, hedge_type, time_of_use, mw, start_date AS month, end_date
    FROM crr_holdings
    UNION ALL
    SELECT report_id, hedge_type, time_of_use, mw, date(month, '+1 month'), end_date
    FROM expanded WHERE date(month, '+1 month') <= end_date
),

-- Expected MW by report, hedge, month, and TOU.
expected AS (
    SELECT report_id, hedge_type, month, time_of_use, SUM(mw) AS mw
    FROM expanded GROUP BY report_id, hedge_type, month, time_of_use
),

-- Turn monthly TOU columns into rows.
blocks AS (
    SELECT report_id, hedge_type, delivery_month AS month, 'PeakWD' AS time_of_use,
           peak_wd_mw AS mw, peak_wd_mwh AS mwh FROM crr_monthly_holdings
    UNION ALL
    SELECT report_id, hedge_type, delivery_month, 'PeakWE', peak_we_mw, peak_we_mwh
    FROM crr_monthly_holdings
    UNION ALL
    SELECT report_id, hedge_type, delivery_month, 'Off-peak', off_peak_mw, off_peak_mwh
    FROM crr_monthly_holdings
),

-- Actual monthly MW/MWh totals.
actual AS (
    SELECT report_id, hedge_type, month, time_of_use, SUM(mw) AS mw, SUM(mwh) AS mwh
    FROM blocks GROUP BY report_id, hedge_type, month, time_of_use
),

-- Include keys from either side of the comparison.
keys AS (
    SELECT report_id, hedge_type, month, time_of_use FROM expected
    UNION SELECT report_id, hedge_type, month, time_of_use FROM actual
),

-- Expected summary totals retain every observed path, including zero exposure.
summary_expected AS (
    SELECT report_id, account_holder, source, sink, hedge_type,
           SUM(peak_wd_mwh + peak_we_mwh + off_peak_mwh) AS mwh
    FROM crr_monthly_holdings
    GROUP BY report_id, account_holder, source, sink, hedge_type
), summary_keys AS (
    SELECT report_id, account_holder, source, sink, hedge_type FROM summary_expected
    UNION
    SELECT report_id, account_holder, source, sink, hedge_type FROM crr_summary_holdings
)

-- Check 1: imported count matches the CSV.
SELECT 'raw_count_errors', COUNT(*) != :raw_count FROM crr_holdings

UNION ALL
-- Check 2: each contract has all required monthly TOU hours.
SELECT 'tou_coverage_errors', COUNT(*) FROM crr_holdings h
WHERE (SELECT COUNT(*) FROM tou_hours t
       WHERE t.delivery_month BETWEEN h.start_date AND h.end_date AND t.time_of_use = h.time_of_use)
    != (CAST(strftime('%Y', h.end_date) AS INTEGER) - CAST(strftime('%Y', h.start_date) AS INTEGER)) * 12
       + CAST(strftime('%m', h.end_date) AS INTEGER) - CAST(strftime('%m', h.start_date) AS INTEGER) + 1

UNION ALL
-- Check 3: MW/MWh reconcile within the floating-point tolerance.
SELECT 'monthly_total_errors', COUNT(*) FROM keys k
LEFT JOIN expected e USING (report_id, hedge_type, month, time_of_use)
LEFT JOIN actual a USING (report_id, hedge_type, month, time_of_use)
LEFT JOIN tou_hours t ON t.delivery_month = k.month AND t.time_of_use = k.time_of_use
WHERE ABS(COALESCE(e.mw, 0) - COALESCE(a.mw, 0)) > 1e-6 + 1e-10 * ABS(COALESCE(e.mw, 0))
   OR ABS(COALESCE(e.mw * t.hours, 0) - COALESCE(a.mwh, 0)) > 1e-6 + 1e-10 * ABS(COALESCE(e.mw * t.hours, 0))

UNION ALL
-- Check 4: summary paths and MWh match the monthly input.
SELECT 'summary_total_errors', COUNT(*) FROM summary_keys k
LEFT JOIN summary_expected e USING (report_id, account_holder, source, sink, hedge_type)
LEFT JOIN crr_summary_holdings a USING (report_id, account_holder, source, sink, hedge_type)
WHERE e.mwh IS NULL OR a.mwh IS NULL
   OR ABS(e.mwh - a.mwh) > 1e-6 + 1e-10 * ABS(e.mwh)

UNION ALL
-- Report row counts and missing enrichment; these are informational.
SELECT 'raw_rows', COUNT(*) FROM crr_holdings
UNION ALL
SELECT 'monthly_rows', COUNT(*) FROM crr_monthly_holdings
UNION ALL
SELECT 'summary_rows', COUNT(*) FROM crr_summary_holdings
UNION ALL
SELECT 'unmatched_accounts', COUNT(*) FROM account_holders WHERE legal_name IS NULL
UNION ALL
SELECT 'missing_coordinates', COUNT(*) FROM settlement_points WHERE longitude IS NULL OR latitude IS NULL;
