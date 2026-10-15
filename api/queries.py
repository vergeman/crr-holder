import sqlite3
from time import perf_counter

from filters import monthly_holdings_query
from geography import get_geographic_footprint
from rankings import get_top_account_holders, get_top_settlement_points


def resolve_report(db: sqlite3.Connection, report_id: int | None) -> int:
    if report_id is not None:
        return report_id

    return db.execute(
        "SELECT report_id FROM reports ORDER BY publication_date DESC, report_id DESC LIMIT 1"
    ).fetchone()[0]


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


def get_summary(db: sqlite3.Connection, report_id=None, account_holder=None,
                settlement_point=None) -> dict:
    report_id = resolve_report(db, report_id)

    holdings_sql, parameters = monthly_holdings_query(
        report_id, account_holder, settlement_point)

    # Filter holdings for the Portfolio Summary panel's totals,
    # holder/point/source-sink counts, and OPT/OBL mix.
    sql = f"""
        WITH holdings AS MATERIALIZED (
            {holdings_sql}
        ), points AS (
            -- Unique endpoints across months and instruments.
            SELECT source AS point FROM holdings
            UNION SELECT sink FROM holdings
        ), source_sink AS (
            -- Count A-to-B and B-to-A as distinct ordered source-sink pairs.
            SELECT DISTINCT source, sink FROM holdings
        )
        SELECT COALESCE(SUM(mwh), 0), COUNT(DISTINCT account_holder),
               (SELECT COUNT(*) FROM points), (SELECT COUNT(*) FROM source_sink),
               COALESCE(SUM(CASE WHEN hedge_type = 'OPT' THEN mwh ELSE 0 END), 0),
               COALESCE(SUM(CASE WHEN hedge_type = 'OBL' THEN mwh ELSE 0 END), 0)
        FROM holdings
        """

    print("get_summary totals query plan:", flush=True)
    for step in db.execute("EXPLAIN QUERY PLAN " + sql, parameters).fetchall():
        print(tuple(step), flush=True)

    started = perf_counter()
    row = db.execute(sql, parameters).fetchone()
    elapsed_ms = (perf_counter() - started) * 1000
    print(f"get_summary totals query: {elapsed_ms:.2f} ms", flush=True)

    # Include query execution and result building in each helper's timing.
    started = perf_counter()
    geographic_footprint = get_geographic_footprint(
        db, report_id, account_holder, settlement_point)
    elapsed_ms = (perf_counter() - started) * 1000
    print(f"get_summary geography: {elapsed_ms:.2f} ms", flush=True)

    started = perf_counter()
    top_account_holders = get_top_account_holders(
        db, report_id, account_holder, settlement_point)
    elapsed_ms = (perf_counter() - started) * 1000
    print(f"get_summary account rankings: {elapsed_ms:.2f} ms", flush=True)

    started = perf_counter()
    top_settlement_points = get_top_settlement_points(
        db, report_id, account_holder, settlement_point)
    elapsed_ms = (perf_counter() - started) * 1000
    print(f"get_summary settlement point rankings: {elapsed_ms:.2f} ms", flush=True)

    return {
        "reportId": report_id,
        "totalMwh": row[0],
        "geographicFootprint": geographic_footprint,
        "accountHolderCount": row[1],
        "settlementPointCount": row[2],
        "directedPathCount": row[3],
        "hedgeTypeMwh": {"OPT": row[4], "OBL": row[5]},
        "topAccountHolders": top_account_holders,
        "topSettlementPoints": top_settlement_points,
    }
