"""GET /api/holdings/sources supplies the CRR Holdings panel's initial load
and subsequent source pages: ranked OPT/OBL totals, monthly MWh, the report
timeline, and the filtered portfolio's nonzero month bounds.
"""

from services.helpers import holdings_filter, resolve_report, summary_holdings_query
from timing import timed

from services.crr_holdings.helpers import delivery_months


def _query_portfolio_bounds(db, report_id, account_holder, settlement_point):
    """Return (first_month, last_month) for nonzero portfolio inventory."""
    bounds_point = None if account_holder else settlement_point
    where, parameters = holdings_filter(report_id, account_holder, bounds_point)
    if account_holder:
        # Keep the NULL guard for faster combined-filter bounds in browser SQLite.
        where += (
            " AND (:settlement_point IS NULL"
            " OR source = :settlement_point OR sink = :settlement_point)"
        )
        parameters['settlement_point'] = settlement_point or None

    # Return the portfolio's first and last months with nonzero MWh.
    # Use date-ordered indexes to search from opposite ends, stopping at the
    # first match in each direction instead of scanning every matching row.
    bounds_sql = f"""
        -- Stop at the first nonzero exposure from each end of the timeline.
        SELECT (
            SELECT delivery_month FROM crr_monthly_holdings WHERE {where}
              AND peak_wd_mwh + peak_we_mwh + off_peak_mwh != 0
            ORDER BY delivery_month ASC LIMIT 1
        ), (
            SELECT delivery_month FROM crr_monthly_holdings WHERE {where}
              AND peak_wd_mwh + peak_we_mwh + off_peak_mwh != 0
            ORDER BY delivery_month DESC LIMIT 1
        )
    """
    if settlement_point and not account_holder:
        # Point lookups do not order months; aggregate their matches once.
        bounds_sql = f"""
            SELECT MIN(delivery_month), MAX(delivery_month)
            FROM crr_monthly_holdings WHERE {where}
              AND peak_wd_mwh + peak_we_mwh + off_peak_mwh != 0
        """
    return db.execute(bounds_sql, parameters).fetchone()


def _query_ranked_sources(db, report_id, account_holder, settlement_point, limit, offset):
    """Return (source, total_opt_mwh, total_obl_mwh), ordered for paging."""
    ranking_sql, parameters = summary_holdings_query(
        report_id, account_holder, settlement_point
    )
    parameters.update(limit=limit, offset=offset)
    return db.execute(f"""
        -- Full-horizon totals are already summed across months.
        WITH holdings AS ({ranking_sql})
        SELECT source,
               SUM(CASE WHEN hedge_type = 'OPT' THEN mwh ELSE 0 END) AS total_opt_mwh,
               SUM(CASE WHEN hedge_type = 'OBL' THEN mwh ELSE 0 END) AS total_obl_mwh
        FROM holdings
        GROUP BY source
        -- Compare combined totals first; source identifiers resolve ties.
        ORDER BY total_opt_mwh + total_obl_mwh DESC, source ASC
        LIMIT :limit OFFSET :offset
    """, parameters).fetchall()


def _query_source_month_cells(db, report_id, account_holder, settlement_point, sources):
    """Return (source, delivery_month, hedge_type, mwh) for selected sources."""
    where, parameters = holdings_filter(report_id, account_holder, settlement_point)
    # Materialize enumeration for Transcrypt dictionary comprehensions.
    source_parameters = {f"source_{i}": source for i, source in list(enumerate(sources))}
    placeholders = ', '.join(f":{key}" for key in source_parameters)

    parameters.update(source_parameters)
    return db.execute(f"""
        -- Aggregate only the selected page, retaining the shared filters.
        SELECT source, delivery_month, hedge_type,
               SUM(peak_wd_mwh + peak_we_mwh + off_peak_mwh)
        FROM crr_monthly_holdings WHERE {where} AND source IN ({placeholders})
        GROUP BY source, delivery_month, hedge_type
    """, parameters).fetchall()


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
