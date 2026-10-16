from sql import load_sql


def delivery_months(db, report_id):
    # Both drill-downs share a continuous report timeline.
    return [row[0] for row in db.execute(
        load_sql("crr_holdings/delivery_months.sql"), {"report_id": report_id}
    )]
