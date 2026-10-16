-- Inventory relevant to the point dropdown.
WITH holdings AS (
    SELECT source, sink FROM crr_monthly_holdings
    WHERE report_id = :report_id
      AND (:account_holder IS NULL OR account_holder = :account_holder)
), points AS (
    -- Inclusive union removes points appearing at both ends.
    SELECT source AS point FROM holdings
    UNION SELECT sink FROM holdings
)
SELECT s.settlement_point FROM points p
JOIN settlement_points s ON s.settlement_point = p.point
ORDER BY s.settlement_point
