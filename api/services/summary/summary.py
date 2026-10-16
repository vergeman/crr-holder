"""GET /api/summary supplies Portfolio Summary, Discover's Top Accounts and
Top Settlement Points, and the map's geographic source/sink MWh totals.
"""

import sqlite3

from services.helpers import resolve_report
from sql import load_sql
from timing import timed

from .top_account_holders import get_top_account_holders
from .top_settlement_points import get_settlement_point_summary


def _query_portfolio_metrics(db, report_id, account_holder, settlement_point):
    """Return (total_mwh, holder_count, directed_path_count, opt_mwh, obl_mwh)."""
    parameters = {
        "report_id": report_id,
        "account_holder": account_holder or None,
        "settlement_point": settlement_point or None,
    }
    statement = "summary/portfolio_metrics.sql"
    if settlement_point:
        statement = "summary/portfolio_metrics_point.sql"
    if account_holder:
        statement = statement.removesuffix(".sql") + "_account.sql"
    return db.execute(load_sql(statement), parameters).fetchone()


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
