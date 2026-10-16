"""GET /api/metadata bootstraps the selected report ID and populates the
report, account-holder, and settlement-point dropdowns.
"""

import sqlite3

from services.helpers import resolve_report
from timing import timed


def _query_reports(db):
    """Return (report_id, publication_date), newest publication first."""
    return db.execute(
        "SELECT report_id, publication_date FROM reports "
        "ORDER BY publication_date DESC, report_id DESC"
    ).fetchall()


def _query_report_account_holders(db, report_id):
    """Return (account_holder, legal_name), ordered by holder identifier."""
    return db.execute(
        """
        SELECT DISTINCT h.account_holder, a.legal_name
        FROM crr_monthly_holdings h
        JOIN account_holders a ON a.account_holder = h.account_holder
        WHERE h.report_id = ?
        ORDER BY h.account_holder
        """,
        (report_id,),
    ).fetchall()


def _query_settlement_point_choices(db, report_id, account_holder):
    """Return (settlement_point,) rows ordered by identifier for the dropdown."""
    point_filter = "report_id = :report_id"
    if account_holder:
        point_filter += " AND account_holder = :account_holder"
    return db.execute(
        f"""
        -- Holdings relevant to the point dropdown.
        WITH holdings AS (
            SELECT source, sink FROM crr_monthly_holdings
            WHERE {point_filter}
        ), points AS (
            -- Inclusive union removes points appearing at both ends.
            SELECT source AS point FROM holdings
            UNION SELECT sink FROM holdings
        )
        SELECT s.settlement_point FROM points p
        JOIN settlement_points s ON s.settlement_point = p.point
        ORDER BY s.settlement_point
        """,
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
