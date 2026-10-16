def delivery_months(db, report_id):
    # Both drill-downs share a continuous report timeline.
    # Returns list[str] of month-start dates, e.g. ["2026-10-01", "2026-11-01"].
    return [row[0] for row in db.execute("""
        -- WITH RECURSIVE expands the report span one month at a time.
        -- Example: October and January holdings yield Oct, Nov, Dec, Jan.
        WITH RECURSIVE months(month, last) AS (
            -- Separate lookups seek each endpoint of the report's month index.
            SELECT (SELECT MIN(delivery_month) FROM crr_monthly_holdings WHERE report_id = ?),
                   (SELECT MAX(delivery_month) FROM crr_monthly_holdings WHERE report_id = ?)
            UNION ALL
            SELECT date(month, '+1 month'), last FROM months WHERE month < last
        )
        SELECT month FROM months WHERE month IS NOT NULL ORDER BY month
    """, (report_id, report_id))]
