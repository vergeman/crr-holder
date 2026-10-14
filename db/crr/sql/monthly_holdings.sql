INSERT INTO crr_monthly_holdings
SELECT h.report_id, h.account_holder, h.source, h.sink, t.delivery_month, h.hedge_type,
       SUM(CASE WHEN h.time_of_use = 'PeakWD' THEN h.mw ELSE 0 END),
       SUM(CASE WHEN h.time_of_use = 'PeakWE' THEN h.mw ELSE 0 END),
       SUM(CASE WHEN h.time_of_use = 'Off-peak' THEN h.mw ELSE 0 END),
       SUM(CASE WHEN h.time_of_use = 'PeakWD' THEN h.mw * t.hours ELSE 0 END),
       SUM(CASE WHEN h.time_of_use = 'PeakWE' THEN h.mw * t.hours ELSE 0 END),
       SUM(CASE WHEN h.time_of_use = 'Off-peak' THEN h.mw * t.hours ELSE 0 END)
FROM crr_holdings h
JOIN tou_hours t ON t.delivery_month BETWEEN h.start_date AND h.end_date
               AND t.time_of_use = h.time_of_use
GROUP BY h.report_id, h.account_holder, h.source, h.sink, t.delivery_month, h.hedge_type;
