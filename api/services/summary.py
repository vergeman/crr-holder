import sqlite3

from services.helpers import holdings_filter, resolve_report
from services.geography import get_geographic_footprint
from services.rankings import get_top_account_holders, get_top_settlement_points


def get_summary(db: sqlite3.Connection, report_id=None, account_holder=None,
                settlement_point=None) -> dict:
    report_id = resolve_report(db, report_id)

    where, parameters = holdings_filter(report_id, account_holder, settlement_point)

    # Filter holdings for the Portfolio Summary panel's totals,
    # holder/point/source-sink counts, and OPT/OBL mix.
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
        ), source_sink AS (
            -- Count A-to-B and B-to-A as distinct ordered source-sink pairs.
            SELECT DISTINCT source, sink FROM holdings
        )
        SELECT COALESCE(SUM(mwh), 0), COUNT(DISTINCT account_holder),
               (SELECT COUNT(*) FROM points), (SELECT COUNT(*) FROM source_sink),
               COALESCE(SUM(CASE WHEN hedge_type = 'OPT' THEN mwh ELSE 0 END), 0),
               COALESCE(SUM(CASE WHEN hedge_type = 'OBL' THEN mwh ELSE 0 END), 0)
        FROM holdings
        """,
        parameters,
    ).fetchone()

    return {
        "reportId": report_id,
        "totalMwh": row[0],
        "geographicFootprint": get_geographic_footprint(
            db, report_id, account_holder, settlement_point),
        "accountHolderCount": row[1],
        "settlementPointCount": row[2],
        "directedPathCount": row[3],
        "hedgeTypeMwh": {"OPT": row[4], "OBL": row[5]},
        "topAccountHolders": get_top_account_holders(
            db, report_id, account_holder, settlement_point),
        "topSettlementPoints": get_top_settlement_points(
            db, report_id, account_holder, settlement_point),
    }
