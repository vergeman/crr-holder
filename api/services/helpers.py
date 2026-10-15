import sqlite3


def resolve_report(db: sqlite3.Connection, report_id: int | None) -> int:
    if report_id is not None:
        return report_id

    return db.execute(
        "SELECT report_id FROM reports ORDER BY publication_date DESC, report_id DESC LIMIT 1"
    ).fetchone()[0]


# Preparation: shared bound predicates for summary and ranking queries.
def holdings_filter(report_id, account_holder=None, settlement_point=None):
    # Preparation: use identical bound predicates for metrics and both rankings.
    filters = ["report_id = :report_id"]
    if account_holder:
        filters.append("account_holder = :account_holder")
    if settlement_point:
        filters.append("(source = :settlement_point OR sink = :settlement_point)")
    return " AND ".join(filters), {
        "report_id": report_id,
        "account_holder": account_holder or None,
        "settlement_point": settlement_point or None,
    }


def summary_holdings_query(report_id, account_holder=None, settlement_point=None):
    """Return aggregate holdings SQL and bound portfolio parameters."""
    where, parameters = holdings_filter(report_id, account_holder)
    parameters['settlement_point'] = settlement_point or None
    sql = f"""
        SELECT account_holder, source, sink, hedge_type, mwh
        FROM crr_summary_holdings WHERE {where}
    """
    if settlement_point:
        sql = f"""
            -- Source matches include self paths.
            {sql} AND source = :settlement_point
            UNION ALL
            -- Sink matches exclude paths already selected by their source.
            SELECT account_holder, source, sink, hedge_type, mwh
            FROM crr_summary_holdings
            WHERE {where} AND sink = :settlement_point
              AND source != :settlement_point
        """
    return sql, parameters
