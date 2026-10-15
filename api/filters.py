# Preparation: shared bound predicates for summary and ranking queries.
def holdings_filter(report_id, account_holder=None, settlement_point=None):
    # Preparation: use identical bound predicates for metrics and both rankings.
    filters = ["report_id = :report_id"]
    if account_holder:
        filters.append("account_holder = :account_holder")
    if settlement_point:
        filters.append("(source = :settlement_point OR sink = :settlement_point)")
    return " AND ".join(filters), {
        "report_id": report_id,
        "account_holder": account_holder or None,
        "settlement_point": settlement_point or None,
    }


def monthly_holdings_query(report_id, account_holder=None, settlement_point=None):
    where, parameters = holdings_filter(report_id, account_holder)
    parameters["settlement_point"] = settlement_point
    sql = f"""
        SELECT account_holder, source, sink, hedge_type,
               peak_wd_mwh + peak_we_mwh + off_peak_mwh AS mwh
        FROM crr_monthly_holdings WHERE {where}
    """
    if settlement_point:
        # Use each endpoint index; self paths enter only through the source branch.
        sql = f"""
            {sql} AND source = :settlement_point
            UNION ALL
            SELECT account_holder, source, sink, hedge_type,
                   peak_wd_mwh + peak_we_mwh + off_peak_mwh AS mwh
            FROM crr_monthly_holdings
            WHERE {where} AND sink = :settlement_point AND source != :settlement_point
        """
    return sql, parameters
