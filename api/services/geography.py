from services.helpers import summary_holdings_query


def get_settlement_point_summary(db, report_id, account_holder=None, settlement_point=None):
    # Filter inventory before expanding its two endpoint roles.
    holdings_sql, parameters = summary_holdings_query(
        report_id, account_holder, settlement_point
    )

    rows = db.execute(f"""
        -- One publication and the shared portfolio predicates.
        WITH holdings AS MATERIALIZED (
            SELECT source, sink, mwh FROM ({holdings_sql})
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
    """, parameters).fetchall()

    # Missing coordinates do not remove inventory from reconciliation.
    geography = [dict(zip(('settlementPoint', 'longitude', 'latitude', 'sourceMwh', 'sinkMwh'), row))
                 for row in rows]

    # Rank the same points by MWh, then identifier to resolve ties.
    ranked_rows = sorted(rows, key=lambda row: (-row[5], row[0]))[:100]
    rankings = [{"settlementPoint": row[0], "totalMwh": row[5]} for row in ranked_rows]
    return geography, rankings
