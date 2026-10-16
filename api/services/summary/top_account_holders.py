import sqlite3

from sql import load_sql


def _query_top_account_holders(db, report_id, account_holder, settlement_point):
    """Return (account_holder, legal_name, total_mwh), highest totals first."""
    parameters = {
        "report_id": report_id,
        "account_holder": account_holder or None,
        "settlement_point": settlement_point or None,
    }
    statement = "summary/top_account_holders.sql"
    if settlement_point:
        statement = "summary/top_account_holders_point.sql"
    if account_holder:
        statement = statement.removesuffix(".sql") + "_account.sql"
    return db.execute(load_sql(statement), parameters).fetchall()


def get_top_account_holders(db: sqlite3.Connection, report_id, account_holder=None,
                            settlement_point=None) -> list[dict]:
    holder_totals = _query_top_account_holders(
        db, report_id, account_holder, settlement_point)

    return [{"accountHolder": holder, "legalName": legal_name, "totalMwh": total_mwh}
            for holder, legal_name, total_mwh in holder_totals]
