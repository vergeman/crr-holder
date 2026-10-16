"""GET /api/holdings/sinks supplies the CRR Holdings panel's source expansion.
Show sinks ranked by total MWh across all months, with OPT/OBL totals and
monthly MWh for the expanded source and selected portfolio filters.
All matching sinks are returned without pagination.
_query_ranked_sinks retrieves OPT/OBL totals across all months for ranking;
_query_sink_month_cells retrieves individual-month OPT/OBL totals for each sink.
"""

from services.helpers import holdings_filter, resolve_report
from timing import timed

from .helpers import delivery_months


def _query_ranked_sinks(db, report_id, account_holder, settlement_point, source):
    """Rank sinks for the expanded source by OPT + OBL MWh across all months.

    Return (sink, total_opt_mwh, total_obl_mwh), highest combined totals first.
    """
    where, parameters = holdings_filter(report_id, account_holder, settlement_point)
    where += " AND source = :source"
    parameters['source'] = source

    return db.execute(f"""
        -- Rank full-horizon sinks by combined MWh, then identifier for ties.
        SELECT sink,
               SUM(CASE WHEN hedge_type = 'OPT'
                   THEN peak_wd_mwh + peak_we_mwh + off_peak_mwh ELSE 0 END) AS total_opt_mwh,
               SUM(CASE WHEN hedge_type = 'OBL'
                   THEN peak_wd_mwh + peak_we_mwh + off_peak_mwh ELSE 0 END) AS total_obl_mwh
        FROM crr_monthly_holdings WHERE {where}
        GROUP BY sink
        ORDER BY total_opt_mwh + total_obl_mwh DESC, sink ASC
    """, parameters).fetchall()


def _query_sink_month_cells(db, report_id, account_holder, settlement_point, source):
    """Fetch individual-month OPT/OBL totals for sinks of the expanded source.

    Return (sink, delivery_month, hedge_type, mwh) for monthly table cells.
    """
    where, parameters = holdings_filter(report_id, account_holder, settlement_point)
    where += " AND source = :source"
    parameters['source'] = source

    return db.execute(f"""
        -- Keep the same predicates for monthly cells and full-horizon totals.
        SELECT sink, delivery_month, hedge_type,
               SUM(peak_wd_mwh + peak_we_mwh + off_peak_mwh)
        FROM crr_monthly_holdings WHERE {where}
        GROUP BY sink, delivery_month, hedge_type
    """, parameters).fetchall()


def _build_sink_holdings(ranked_sinks, months, monthly_totals):
    """Build sink rows in ranking order with zero-filled monthly MWh.

    Each sink gets the report's delivery months (the panel's month columns),
    e.g. ["2026-10-01", "2026-11-01", "2026-12-01"], initialized to zero MWh.
    With no ranked sinks, return []; no rows or zero-filled cells are created.
    """
    sinks = [
        {
            "sink": sink,
            "totalOptMwh": opt,
            "totalOblMwh": obl,
            "months": [
                {"deliveryMonth": month, "OPT": 0, "OBL": 0} for month in months
            ],
        }
        for sink, opt, obl in ranked_sinks
    ]
    cells = {
        (row["sink"], cell["deliveryMonth"]): cell
        for row in sinks
        for cell in row["months"]
    }

    # Use the same portfolio and source restriction as the full-horizon totals.
    for sink, month, hedge_type, mwh in monthly_totals:
        cells[sink, month][hedge_type] = mwh

    return sinks


@timed
def get_sink_holdings(
    db, source, report_id=None, account_holder=None, settlement_point=None
):
    """Build the sink rows displayed when a source is expanded.

    Return all matching sinks ordered by combined OPT/OBL MWh descending,
    then sink identifier for ties. Each row includes OPT/OBL totals and
    monthly MWh on a zero-filled report timeline.
    """
    report_id = resolve_report(db, report_id)
    months = delivery_months(db, report_id)
    ranked_sinks = _query_ranked_sinks(
        db, report_id, account_holder, settlement_point, source
    )
    monthly_totals = _query_sink_month_cells(
        db, report_id, account_holder, settlement_point, source
    )

    sinks = _build_sink_holdings(ranked_sinks, months, monthly_totals)

    return {
        "reportId": report_id,
        "source": source,
        "deliveryMonths": months,
        "sinks": sinks,
    }
