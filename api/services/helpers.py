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

