-- Holder choices depend on the report, independently of portfolio filters.
SELECT DISTINCT h.account_holder, a.legal_name
FROM crr_monthly_holdings h
JOIN account_holders a ON a.account_holder = h.account_holder
WHERE h.report_id = :report_id
ORDER BY h.account_holder
