"""GET /api/summary supplies Portfolio Summary, Discover's Top Accounts and
Top Settlement Points, and the map's geographic source/sink MWh totals.
"""

import sqlite3

from services.helpers import summary_holdings_query, resolve_report
from services.summary.top_settlement_points import get_settlement_point_summary
from services.summary.top_account_holders import get_top_account_holders
from timing import timed


def _query_portfolio_metrics(db, report_id, account_holder, settlement_point):
    """Return (total_mwh, holder_count, directed_path_count, opt_mwh, obl_mwh)."""
    holdings_sql, parameters = summary_holdings_query(
        report_id, account_holder, settlement_point
    )

    # Filter holdings for the Portfolio Summary panel's totals,
    # holder/source-sink counts, and OPT/OBL mix.
    return db.execute(
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


@timed
def get_summary(db: sqlite3.Connection, report_id=None, account_holder=None,
                settlement_point=None) -> dict:
    """Combine portfolio metrics, geography, and rankings for the same filters.

    Default to the latest report; omitted filters include all holdings.
    Geography includes every matching point; each ranking returns the top 100.
    """
    report_id = resolve_report(db, report_id)

    total_mwh, holder_count, path_count, opt_mwh, obl_mwh = _query_portfolio_metrics(
        db, report_id, account_holder, settlement_point)

    geographic_footprint, top_settlement_points = get_settlement_point_summary(
        db, report_id, account_holder, settlement_point
    )

    top_account_holders = get_top_account_holders(
        db, report_id, account_holder, settlement_point)

    return {
        "reportId": report_id,
        "totalMwh": total_mwh,
        "geographicFootprint": geographic_footprint,
        "accountHolderCount": holder_count,
        "settlementPointCount": len(geographic_footprint),
        "directedPathCount": path_count,
        "hedgeTypeMwh": {"OPT": opt_mwh, "OBL": obl_mwh},
        "topAccountHolders": top_account_holders,
        "topSettlementPoints": top_settlement_points,
    }
