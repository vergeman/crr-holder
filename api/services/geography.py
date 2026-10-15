from services.helpers import summary_holdings_query


def get_geographic_footprint(db, report_id, account_holder=None, settlement_point=None):
    # Filter inventory before expanding its two endpoint roles.
    holdings_sql, parameters = summary_holdings_query(
        report_id, account_holder, settlement_point
    )

    # A self path participates once in each independent role.
    rows = db.execute(f"""
        -- One publication and the shared portfolio predicates.
        WITH holdings AS MATERIALIZED (
            {holdings_sql}
        ), roles AS (
            SELECT source AS point, mwh AS source_mwh, 0 AS sink_mwh FROM holdings
            UNION ALL
            SELECT sink AS point, 0 AS source_mwh, mwh AS sink_mwh FROM holdings
        ), totals AS (
            SELECT point, SUM(source_mwh) AS source_mwh, SUM(sink_mwh) AS sink_mwh
            FROM roles GROUP BY point
        )
        SELECT t.point, s.longitude, s.latitude, t.source_mwh, t.sink_mwh
        FROM totals t
        LEFT JOIN settlement_points s ON s.settlement_point = t.point
        -- Compare identifiers for stable, complete output.
        ORDER BY t.point
    """, parameters).fetchall()

    # Missing coordinates do not remove inventory from reconciliation.
    return [dict(zip(('settlementPoint', 'longitude', 'latitude', 'sourceMwh', 'sinkMwh'), row))
            for row in rows]
