-- Expand the report span one month at a time, including timeline gaps.
WITH RECURSIVE months(month, last) AS (
    -- Separate lookups seek each endpoint of the report's month index.
    SELECT (SELECT MIN(delivery_month) FROM crr_monthly_holdings WHERE report_id = :report_id),
           (SELECT MAX(delivery_month) FROM crr_monthly_holdings WHERE report_id = :report_id)
    UNION ALL
    SELECT date(month, '+1 month'), last FROM months WHERE month < last
)
SELECT month FROM months WHERE month IS NOT NULL ORDER BY month
