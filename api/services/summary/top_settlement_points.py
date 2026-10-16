from sql import load_sql


def _query_settlement_point_totals(db, report_id, account_holder, settlement_point):
    """Return (point, longitude, latitude, source_mwh, sink_mwh, total_mwh).

    Rows are ordered by point; total_mwh counts a self path once for rankings.
    """
    parameters = {
        "report_id": report_id,
        "account_holder": account_holder or None,
        "settlement_point": settlement_point or None,
    }
    statement = "summary/settlement_point_totals.sql"
    if settlement_point:
        statement = "summary/settlement_point_totals_point.sql"
    if account_holder:
        statement = statement.removesuffix(".sql") + "_account.sql"
    return db.execute(load_sql(statement), parameters).fetchall()


def _build_settlement_point_summary(point_totals):
    """Build complete geography and the top 100 rankings from shared point rows."""
    # Missing coordinates do not remove inventory from reconciliation.
    geography = [
        {"settlementPoint": point, "longitude": longitude, "latitude": latitude,
         "sourceMwh": source_mwh, "sinkMwh": sink_mwh}
        for point, longitude, latitude, source_mwh, sink_mwh, total_mwh in point_totals
    ]

    # Rank the same points by MWh, then identifier to resolve ties.
    ranked_points = sorted(point_totals, key=lambda row: (-row[5], row[0]))[:100]
    rankings = [
        {"settlementPoint": point, "totalMwh": total_mwh}
        for point, longitude, latitude, source_mwh, sink_mwh, total_mwh in ranked_points
    ]
    return geography, rankings


def get_settlement_point_summary(db, report_id, account_holder=None, settlement_point=None):
    point_totals = _query_settlement_point_totals(
        db, report_id, account_holder, settlement_point)

    return _build_settlement_point_summary(point_totals)
