import sqlite3

from services.helpers import summary_holdings_query, resolve_report
from services.geography import get_settlement_point_summary
from services.rankings import get_top_account_holders
from timing import timed


@timed
def get_summary(db: sqlite3.Connection, report_id=None, account_holder=None,
                settlement_point=None) -> dict:
    report_id = resolve_report(db, report_id)

    holdings_sql, parameters = summary_holdings_query(
        report_id, account_holder, settlement_point
    )

    # Filter holdings for the Portfolio Summary panel's totals,
    # holder/source-sink counts, and OPT/OBL mix.
    row = db.execute(
        f"""
        WITH holdings AS MATERIALIZED (
            {holdings_sql}
        ), source_sink AS (
            -- Count A-to-B and B-to-A as distinct ordered source-sink pairs.
            SELECT DISTINCT source, sink FROM holdings
        )
        SELECT COALESCE(SUM(mwh), 0), COUNT(DISTINCT account_holder),
               (SELECT COUNT(*) FROM source_sink),
               COALESCE(SUM(CASE WHEN hedge_type = 'OPT' THEN mwh ELSE 0 END), 0),
               COALESCE(SUM(CASE WHEN hedge_type = 'OBL' THEN mwh ELSE 0 END), 0)
        FROM holdings
        """,
        parameters,
    ).fetchone()

    geographic_footprint, top_settlement_points = get_settlement_point_summary(
        db, report_id, account_holder, settlement_point
    )

    return {
        "reportId": report_id,
        "totalMwh": row[0],
        "geographicFootprint": geographic_footprint,
        "accountHolderCount": row[1],
        "settlementPointCount": len(geographic_footprint),
        "directedPathCount": row[2],
        "hedgeTypeMwh": {"OPT": row[3], "OBL": row[4]},
        "topAccountHolders": get_top_account_holders(
            db, report_id, account_holder, settlement_point),
        "topSettlementPoints": top_settlement_points,
    }
