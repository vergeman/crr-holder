-- Filter originals before enriching holders to keep predicates unambiguous.
WITH contracts AS (
    SELECT * FROM crr_holdings
    WHERE report_id = :report_id
      AND (:account_holder IS NULL OR account_holder = :account_holder)
      AND (:settlement_point IS NULL OR source = :settlement_point OR sink = :settlement_point)
      AND source = :source AND sink = :sink AND hedge_type = :hedge_type
)
SELECT h.account_holder, a.legal_name, h.time_of_use,
       h.crr_id, h.segment_id, h.crr_type, h.start_date, h.end_date,
       h.mw, t.hours, h.mw * t.hours AS month_mwh
FROM contracts h
JOIN tou_hours t ON t.time_of_use = h.time_of_use
                 AND t.delivery_month = :month
                 -- Use the same inclusive month bounds as preparation.
                 AND t.delivery_month BETWEEN h.start_date AND h.end_date
JOIN account_holders a ON a.account_holder = h.account_holder
-- Compare monthly MWh first, then contract and segment identifiers.
ORDER BY month_mwh DESC, h.crr_id ASC, h.segment_id ASC
