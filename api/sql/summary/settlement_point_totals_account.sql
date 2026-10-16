-- Materialize matching inventory before expanding endpoint roles.
WITH holdings AS MATERIALIZED (
    SELECT source, sink, mwh
    FROM crr_summary_holdings
    WHERE report_id = :report_id
      AND account_holder = :account_holder
), roles AS (
    SELECT source AS point, mwh AS source_mwh, 0 AS sink_mwh,
           mwh AS ranking_mwh FROM holdings
    UNION ALL
    -- Self paths count in both geographic roles, but once in rankings.
    SELECT sink AS point, 0 AS source_mwh, mwh AS sink_mwh,
           CASE WHEN source != sink THEN mwh ELSE 0 END AS ranking_mwh
    FROM holdings
), totals AS (
    SELECT point, SUM(source_mwh) AS source_mwh, SUM(sink_mwh) AS sink_mwh,
           SUM(ranking_mwh) AS total_mwh
    FROM roles GROUP BY point
)
SELECT t.point, s.longitude, s.latitude, t.source_mwh, t.sink_mwh, t.total_mwh
FROM totals t
LEFT JOIN settlement_points s ON s.settlement_point = t.point
-- Compare identifiers for stable, complete output.
ORDER BY t.point
