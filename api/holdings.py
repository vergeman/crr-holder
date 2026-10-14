# Imports
from filters import holdings_filter
from queries import resolve_report


def get_source_holdings(db, report_id=None, account_holder=None,
                        settlement_point=None, limit=20, offset=0):
    # Preparation: the report timeline remains independent of portfolio filters.
    report_id = resolve_report(db, report_id)
    months = [row[0] for row in db.execute("""
        -- WITH RECURSIVE expands the report span one month at a time.
        -- Example: October and January holdings yield Oct, Nov, Dec, Jan.
        WITH RECURSIVE months(month, last) AS (
            SELECT MIN(delivery_month), MAX(delivery_month)
            FROM crr_monthly_holdings WHERE report_id = ?
            UNION ALL
            SELECT date(month, '+1 month'), last FROM months WHERE month < last
        )
        SELECT month FROM months WHERE month IS NOT NULL ORDER BY month
    """, (report_id,))]
    where, parameters = holdings_filter(report_id, account_holder, settlement_point)
    bounds = db.execute(f"""
        SELECT MIN(delivery_month), MAX(delivery_month)
        FROM crr_monthly_holdings WHERE {where}
          AND peak_wd_mwh + peak_we_mwh + off_peak_mwh != 0
    """, parameters).fetchone()

    # Transformation: rank complete sources before loading their monthly cells.
    parameters.update(limit=limit + 1, offset=offset)
    ranked = db.execute(f"""
        SELECT source, SUM(peak_wd_mwh + peak_we_mwh + off_peak_mwh) AS total
        FROM crr_monthly_holdings WHERE {where}
        GROUP BY source ORDER BY total DESC, source ASC LIMIT :limit OFFSET :offset
    """, parameters).fetchall()
    sources = [{"source": source, "totalMwh": total,
                "months": [{"deliveryMonth": month, "OPT": 0, "OBL": 0}
                           for month in months]} for source, total in ranked[:limit]]
    cells = {(source['source'], cell['deliveryMonth']): cell
             for source in sources for cell in source['months']}
    if sources:
        source_parameters = {f"source_{i}": row['source'] for i, row in enumerate(sources)}
        placeholders = ', '.join(f":{key}" for key in source_parameters)
        rows = db.execute(f"""
            -- Aggregate only the selected page, retaining the shared filters.
            SELECT source, delivery_month, hedge_type,
                   SUM(peak_wd_mwh + peak_we_mwh + off_peak_mwh)
            FROM crr_monthly_holdings WHERE {where} AND source IN ({placeholders})
            GROUP BY source, delivery_month, hedge_type
        """, parameters | source_parameters)
        for source, month, hedge_type, mwh in rows:
            cells[source, month][hedge_type] = mwh

    # Output: bounds cover the portfolio, while offsets count complete source rows.
    return {"reportId": report_id, "deliveryMonths": months,
            "holdingsRange": {"firstMonth": bounds[0], "lastMonth": bounds[1]}
                             if bounds[0] else None,
            "sources": sources,
            "nextOffset": offset + limit if len(ranked) > limit else None}
