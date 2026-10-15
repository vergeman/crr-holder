import sqlite3

from services.helpers import resolve_report


def get_metadata(db: sqlite3.Connection, report_id=None, account_holder=None) -> dict:
    # Resolve one publication snapshot.
    report_id = resolve_report(db, report_id)
    reports = db.execute(
        "SELECT report_id, publication_date FROM reports "
        "ORDER BY publication_date DESC, report_id DESC"
    ).fetchall()

    # Holder choices stay independent of portfolio filters.
    holders = db.execute(
        """
        SELECT DISTINCT h.account_holder, a.legal_name
        FROM crr_monthly_holdings h
        JOIN account_holders a ON a.account_holder = h.account_holder
        WHERE h.report_id = ?
        ORDER BY h.account_holder
        """,
        (report_id,),
    ).fetchall()
    point_filter = "report_id = :report_id"
    if account_holder:
        point_filter += " AND account_holder = :account_holder"
    points = db.execute(
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

    return {
        "reportId": report_id,
        "reports": [{"reportId": row[0], "publicationDate": row[1]} for row in reports],
        "accountHolders": [
            {"accountHolder": row[0], "legalName": row[1]} for row in holders
        ],
        "settlementPoints": [row[0] for row in points],
    }
