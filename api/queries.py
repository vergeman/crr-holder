# Imports
import sqlite3

from filters import holdings_filter
from rankings import get_top_account_holders, get_top_settlement_points


def resolve_report(db: sqlite3.Connection, report_id: int | None) -> int:
    if report_id is not None:
        return report_id

    return db.execute(
        "SELECT report_id FROM reports ORDER BY publication_date DESC, report_id DESC LIMIT 1"
    ).fetchone()[0]


def get_metadata(db: sqlite3.Connection, report_id=None, account_holder=None) -> dict:
    # Preparation: resolve one publication snapshot.
    report_id = resolve_report(db, report_id)
    reports = db.execute(
        "SELECT report_id, publication_date FROM reports "
        "ORDER BY publication_date DESC, report_id DESC"
    ).fetchall()

    # Transformation: holder choices stay independent of portfolio filters.
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

    # Output
    return {
        "reportId": report_id,
        "reports": [{"reportId": row[0], "publicationDate": row[1]} for row in reports],
        "accountHolders": [
            {"accountHolder": row[0], "legalName": row[1]} for row in holders
        ],
        "settlementPoints": [row[0] for row in points],
    }


def get_summary(db: sqlite3.Connection, report_id=None, account_holder=None,
                settlement_point=None) -> dict:
    # Preparation
    report_id = resolve_report(db, report_id)

    where, parameters = holdings_filter(report_id, account_holder, settlement_point)

    # Transformation: direct predicates allow use of existing filter indexes.
    row = db.execute(
        f"""
        WITH holdings AS (
            SELECT account_holder, source, sink, hedge_type,
                   peak_wd_mwh + peak_we_mwh + off_peak_mwh AS mwh
            FROM crr_monthly_holdings
            WHERE {where}
        ), points AS (
            -- Unique endpoints across months and instruments.
            SELECT source AS point FROM holdings
            UNION SELECT sink FROM holdings
        ), paths AS (
            -- Ordered pairs preserve reversed paths as distinct inventory.
            SELECT DISTINCT source, sink FROM holdings
        )
        SELECT COALESCE(SUM(mwh), 0), COUNT(DISTINCT account_holder),
               (SELECT COUNT(*) FROM points), (SELECT COUNT(*) FROM paths),
               COALESCE(SUM(CASE WHEN hedge_type = 'OPT' THEN mwh ELSE 0 END), 0),
               COALESCE(SUM(CASE WHEN hedge_type = 'OBL' THEN mwh ELSE 0 END), 0)
        FROM holdings
        """,
        parameters,
    ).fetchone()

    # Output
    return {
        "reportId": report_id,
        "totalMwh": row[0],
        "accountHolderCount": row[1],
        "settlementPointCount": row[2],
        "directedPathCount": row[3],
        "hedgeTypeMwh": {"OPT": row[4], "OBL": row[5]},
        "topAccountHolders": get_top_account_holders(
            db, report_id, account_holder, settlement_point),
        "topSettlementPoints": get_top_settlement_points(
            db, report_id, account_holder, settlement_point),
    }
