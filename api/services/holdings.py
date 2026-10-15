# Imports
from services.helpers import holdings_filter, resolve_report, summary_holdings_query
from timing import timed


def delivery_months(db, report_id):
    # Preparation: share the continuous report timeline across both drill-downs.
    return [row[0] for row in db.execute("""
        -- WITH RECURSIVE expands the report span one month at a time.
        -- Example: October and January holdings yield Oct, Nov, Dec, Jan.
        WITH RECURSIVE months(month, last) AS (
            -- Separate lookups seek each endpoint of the report's month index.
            SELECT (SELECT MIN(delivery_month) FROM crr_monthly_holdings WHERE report_id = ?),
                   (SELECT MAX(delivery_month) FROM crr_monthly_holdings WHERE report_id = ?)
            UNION ALL
            SELECT date(month, '+1 month'), last FROM months WHERE month < last
        )
        SELECT month FROM months WHERE month IS NOT NULL ORDER BY month
    """, (report_id, report_id))]


@timed
def get_source_holdings(db, report_id=None, account_holder=None,
                        settlement_point=None, limit=20, offset=0):
    # Preparation: the report timeline remains independent of portfolio filters.
    report_id = resolve_report(db, report_id)
    months = delivery_months(db, report_id)
    where, parameters = holdings_filter(report_id, account_holder, settlement_point)
    bounds = db.execute(f"""
        SELECT MIN(delivery_month), MAX(delivery_month)
        FROM crr_monthly_holdings WHERE {where}
          AND peak_wd_mwh + peak_we_mwh + off_peak_mwh != 0
    """, parameters).fetchone()

    # Transformation: rank complete sources before loading their monthly cells.
    ranking_sql, _ = summary_holdings_query(
        report_id, account_holder, settlement_point
    )
    parameters.update(limit=limit + 1, offset=offset)
    ranked = db.execute(f"""
        -- Full-horizon totals are already summed across months.
        WITH holdings AS ({ranking_sql})
        SELECT source,
               SUM(CASE WHEN hedge_type = 'OPT' THEN mwh ELSE 0 END) AS total_opt_mwh,
               SUM(CASE WHEN hedge_type = 'OBL' THEN mwh ELSE 0 END) AS total_obl_mwh
        FROM holdings
        GROUP BY source
        ORDER BY total_opt_mwh + total_obl_mwh DESC, source ASC
        LIMIT :limit OFFSET :offset
    """, parameters).fetchall()
    sources = [{"source": source,
                "totalOptMwh": opt, "totalOblMwh": obl,
                "months": [{"deliveryMonth": month, "OPT": 0, "OBL": 0}
                           for month in months]} for source, opt, obl in ranked[:limit]]
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


@timed
def get_sink_holdings(db, source, report_id=None, account_holder=None,
                      settlement_point=None):
    # Preparation: source restriction complements the inclusive portfolio filter.
    report_id = resolve_report(db, report_id)
    months = delivery_months(db, report_id)
    where, parameters = holdings_filter(report_id, account_holder, settlement_point)
    where += " AND source = :source"
    parameters['source'] = source

    # Transformation: aggregate every matching sink, without pagination.
    ranked = db.execute(f"""
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
    sinks = [{"sink": sink, "totalOptMwh": opt, "totalOblMwh": obl,
              "months": [{"deliveryMonth": month, "OPT": 0, "OBL": 0}
                         for month in months]} for sink, opt, obl in ranked]
    cells = {(row['sink'], cell['deliveryMonth']): cell
             for row in sinks for cell in row['months']}
    rows = db.execute(f"""
        -- Keep the same predicates for monthly cells and full-horizon totals.
        SELECT sink, delivery_month, hedge_type,
               SUM(peak_wd_mwh + peak_we_mwh + off_peak_mwh)
        FROM crr_monthly_holdings WHERE {where}
        GROUP BY sink, delivery_month, hedge_type
    """, parameters)
    for sink, month, hedge_type, mwh in rows:
        cells[sink, month][hedge_type] = mwh

    # Output: empty sources retain the selected report's timeline.
    return {"reportId": report_id, "source": source,
            "deliveryMonths": months, "sinks": sinks}


@timed
def get_contract_holdings(db, source, sink, month, hedge_type, report_id=None,
                         account_holder=None, settlement_point=None):
    # Preparation: select original segments with the shared portfolio predicates.
    report_id = resolve_report(db, report_id)
    where, parameters = holdings_filter(report_id, account_holder, settlement_point)
    parameters.update(source=source, sink=sink, month=month, hedge_type=hedge_type)

    # Transformation: match the prepared monthly calculation without proration.
    rows = db.execute(f"""
        -- Filter originals before enriching holders to keep predicates unambiguous.
        WITH contracts AS (
            SELECT * FROM crr_holdings WHERE {where}
              AND source = :source AND sink = :sink AND hedge_type = :hedge_type
        )
        SELECT h.account_holder, a.legal_name, h.time_of_use,
               h.crr_id, h.segment_id, h.crr_type, h.start_date, h.end_date,
               h.mw, t.hours, h.mw * t.hours AS month_mwh
        FROM contracts h
        JOIN tou_hours t ON t.time_of_use = h.time_of_use
                         AND t.delivery_month = :month
                         -- Use the same inclusive month bounds as preparation.
                         AND t.delivery_month BETWEEN h.start_date AND h.end_date
        JOIN account_holders a ON a.account_holder = h.account_holder
        ORDER BY month_mwh DESC, h.crr_id ASC, h.segment_id ASC
    """, parameters)

    holders = {}
    for holder, name, tou, crr_id, segment_id, crr_type, start, end, mw, hours, mwh in rows:
        group = holders.setdefault(holder, {
            "accountHolder": holder, "legalName": name, "totalMwh": 0,
            "timeOfUseGroups": {},
        })
        tou_group = group['timeOfUseGroups'].setdefault(tou, {
            "timeOfUse": tou, "hours": hours, "totalMwh": 0, "contracts": [],
        })
        tou_group['contracts'].append({
            "crrId": crr_id, "segmentId": segment_id, "crrType": crr_type,
            "startDate": start, "endDate": end, "mw": mw, "monthMwh": mwh,
        })
        tou_group['totalMwh'] += mwh
        group['totalMwh'] += mwh

    for group in holders.values():
        groups = group['timeOfUseGroups']
        group['timeOfUseGroups'] = [groups[tou] for tou in
                                    ('PeakWD', 'PeakWE', 'Off-peak') if tou in groups]
    ordered = sorted(holders.values(), key=lambda group:
                     (-group['totalMwh'], group['accountHolder']))

    # Output: totals reflect every returned segment, independent of UI expansion.
    return {"reportId": report_id, "source": source, "sink": sink,
            "deliveryMonth": month, "hedgeType": hedge_type,
            "totalMwh": sum(group['totalMwh'] for group in ordered),
            "accountHolders": ordered}
