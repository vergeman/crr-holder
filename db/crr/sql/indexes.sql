CREATE INDEX holdings_account_dates ON crr_holdings(report_id, account_holder, start_date, end_date);
CREATE INDEX holdings_path_dates ON crr_holdings(report_id, source, sink, start_date, end_date, hedge_type);
CREATE INDEX holdings_sink ON crr_holdings(report_id, sink);
CREATE INDEX monthly_account ON crr_monthly_holdings(report_id, account_holder, delivery_month);
CREATE INDEX monthly_source ON crr_monthly_holdings(report_id, source, delivery_month);
CREATE INDEX monthly_sink ON crr_monthly_holdings(report_id, sink, delivery_month);
