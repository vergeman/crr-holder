"""Shared report selection for service queries."""

import sqlite3

from sql import load_sql


def resolve_report(db: sqlite3.Connection, report_id: int | None) -> int:
    """Use the requested report, or select the latest for service entry points."""
    if report_id is not None:
        return report_id

    return db.execute(load_sql("resolve_report.sql")).fetchone()[0]
