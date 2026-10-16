"""Shared report selection for service queries."""

import sqlite3

from sql import load_sql


def resolve_report(db: sqlite3.Connection, report_id: int | None) -> int:
    """Use the requested report, or select the latest for service entry points."""
    if report_id is not None:
        return report_id

    return db.execute(load_sql("resolve_report.sql")).fetchone()[0]

def holdings_filter(report_id, account_holder=None, settlement_point=None):
    """Build optional portfolio predicates and bound values for holdings queries.

    Used by source, sink, and contract queries, and summary_holdings_query.
    A settlement point matches either endpoint; omitted filters impose no limit.
    """
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
    """Build filtered holdings SQL for summary metrics and rankings.

    Used by summary.py, top_account_holders.py, top_settlement_points.py,
    and source_holdings.py's source ranking query.

    Read preaggregated MWh from crr_summary_holdings, where months and TOU
    are already collapsed. Point filters use separate source and sink lookups
    so each branch can use its index. UNION ALL avoids deduplication work;
    excluding self paths from the sink branch counts each holding once.
    Return SQL and bound parameters for the caller to embed and execute.
    """
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
