"""GET /api/holdings/sources supplies the CRR Holdings panel's initial load
and subsequent source pages: ranked OPT/OBL totals, monthly MWh, the report
timeline, and the filtered portfolio's nonzero month bounds.
"""

import json

from services.helpers import resolve_report
from sql import load_sql
from timing import timed

from .helpers import delivery_months


def _query_portfolio_bounds(db, report_id, account_holder, settlement_point):
    """Return (first_month, last_month) for nonzero portfolio inventory."""
    parameters = {
        "report_id": report_id,
        "account_holder": account_holder or None,
        "settlement_point": settlement_point or None,
    }
    statement = "crr_holdings/source_portfolio_bounds.sql"
    if settlement_point and not account_holder:
        # Point lookups do not order months; aggregate their matches once.
        statement = "crr_holdings/source_portfolio_bounds_point.sql"
    if account_holder:
        statement = statement.removesuffix(".sql") + "_account.sql"
    return db.execute(load_sql(statement), parameters).fetchone()


def _query_ranked_sources(db, report_id, account_holder, settlement_point, limit, offset):
    """Return (source, total_opt_mwh, total_obl_mwh), ordered for paging."""
    parameters = {
        "report_id": report_id,
        "account_holder": account_holder or None,
        "settlement_point": settlement_point or None,
        "limit": limit,
        "offset": offset,
    }
    statement = "crr_holdings/ranked_sources.sql"
    if settlement_point:
        statement = "crr_holdings/ranked_sources_point.sql"
    if account_holder:
        statement = statement.removesuffix(".sql") + "_account.sql"
    return db.execute(load_sql(statement), parameters).fetchall()


def _query_source_month_cells(db, report_id, account_holder, settlement_point, sources):
    """Return (source, delivery_month, hedge_type, mwh) for selected sources."""
    parameters = {
        "report_id": report_id,
        "account_holder": account_holder or None,
        "settlement_point": settlement_point or None,
    }
    parameters["sources"] = json.dumps(sources)
    statement = "crr_holdings/source_month_cells.sql"
    if account_holder:
        statement = "crr_holdings/source_month_cells_account.sql"
    return db.execute(load_sql(statement), parameters).fetchall()


def _build_source_holdings(ranked_sources, months, monthly_totals):
    """Fill the report timeline for each source, preserving ranking order."""
    sources = [
        {"source": source, "totalOptMwh": opt, "totalOblMwh": obl,
         "months": [{"deliveryMonth": month, "OPT": 0, "OBL": 0} for month in months]}
        for source, opt, obl in ranked_sources
    ]
    cells = {(row['source'], cell['deliveryMonth']): cell
             for row in sources for cell in row['months']}

    # Missing monthly contributions retain their initial zero values.
    for source, month, hedge_type, mwh in monthly_totals:
        cells[source, month][hedge_type] = mwh

    return sources


@timed
def get_source_holdings(
    db, report_id=None, account_holder=None, settlement_point=None, limit=20, offset=0
):
    """Build the initial CRR Holdings panel view and subsequent source pages.

    Rank sources by total MWh across all months for the selected filters.
    Return each page's OPT/OBL totals and monthly MWh on a zero-filled report
    timeline, with portfolio-wide nonzero month bounds and the next offset.
    """
    report_id = resolve_report(db, report_id)

    # Report-wide list[str], e.g. ["2026-10-01", "2026-11-01", "2026-12-01"].
    months = delivery_months(db, report_id)

    # Filtered nonzero bounds: two str | None values, e.g. ("2026-11-01", "2026-12-01").
    # Both are None if the portfolio is empty or all zero.
    first_month, last_month = _query_portfolio_bounds(
        db, report_id, account_holder, settlement_point
    )

    # Rank sources by total MWh across all months, fetching one extra for pagination.
    ranked_sources = _query_ranked_sources(
        db, report_id, account_holder, settlement_point, limit + 1, offset
    )
    page_sources = ranked_sources[:limit]
    source_names = [source for source, opt, obl in page_sources]
    monthly_totals = []
    if source_names:
        # Fetch the larger monthly breakdown across all months only for this page's sources.
        monthly_totals = _query_source_month_cells(
            db, report_id, account_holder, settlement_point, source_names
        )

    sources = _build_source_holdings(page_sources, months, monthly_totals)
    holdings_range = (
        {"firstMonth": first_month, "lastMonth": last_month} if first_month else None
    )
    next_offset = offset + limit if len(ranked_sources) > limit else None

    return {
        "reportId": report_id,
        "deliveryMonths": months,
        "holdingsRange": holdings_range,
        "sources": sources,
        "nextOffset": next_offset,
    }
