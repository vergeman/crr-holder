"""GET /api/metadata bootstraps the selected report ID and populates the
report, account-holder, and settlement-point dropdowns.
"""

import sqlite3

from services.helpers import resolve_report
from sql import load_sql
from timing import timed


def _query_reports(db):
    """Return (report_id, publication_date), newest publication first."""
    return db.execute(load_sql("metadata/reports.sql")).fetchall()


def _query_report_account_holders(db, report_id):
    """Return (account_holder, legal_name), ordered by holder identifier."""
    return db.execute(
        load_sql("metadata/report_account_holders.sql"), {"report_id": report_id}
    ).fetchall()


def _query_settlement_point_choices(db, report_id, account_holder):
    """Return (settlement_point,) rows ordered by identifier for the dropdown."""
    statement = "metadata/settlement_point_choices.sql"
    if account_holder:
        statement = "metadata/settlement_point_choices_account.sql"
    return db.execute(
        load_sql(statement),
        {"report_id": report_id, "account_holder": account_holder or None},
    ).fetchall()


@timed
def get_metadata(db: sqlite3.Connection, report_id=None, account_holder=None) -> dict:
    """Build initial dropdown data and refresh it when selections change.

    Default to the latest report. Account-holder choices cover that report;
    settlement-point choices follow the selected account holder, if provided.
    """
    # Resolve one publication snapshot.
    report_id = resolve_report(db, report_id)
    report_rows = _query_reports(db)

    # Holder choices stay independent of portfolio filters.
    holder_rows = _query_report_account_holders(db, report_id)
    point_rows = _query_settlement_point_choices(db, report_id, account_holder)

    return {
        "reportId": report_id,
        "reports": [
            {"reportId": report, "publicationDate": publication_date}
            for report, publication_date in report_rows
        ],
        "accountHolders": [
            {"accountHolder": holder, "legalName": legal_name}
            for holder, legal_name in holder_rows
        ],
        "settlementPoints": [point for point, in point_rows],
    }
