import sqlite3

from services.helpers import summary_holdings_query


def _query_top_account_holders(db, report_id, account_holder, settlement_point):
    """Return (account_holder, legal_name, total_mwh), highest totals first."""
    holdings_sql, parameters = summary_holdings_query(
        report_id, account_holder, settlement_point
    )

    # Aggregate inventory before joining directory names.
    return db.execute(
        f"""
        -- Matching holdings from one publication snapshot.
        WITH holdings AS (
            {holdings_sql}
        ), totals AS (
            SELECT account_holder, SUM(mwh) AS total_mwh
            FROM holdings GROUP BY account_holder
        )
        SELECT t.account_holder, a.legal_name, t.total_mwh
        FROM totals t
        LEFT JOIN account_holders a ON a.account_holder = t.account_holder
        -- Compare unrounded totals first, identifiers resolve ties.
        ORDER BY t.total_mwh DESC, t.account_holder ASC LIMIT 100
        """, parameters,
    ).fetchall()


def get_top_account_holders(db: sqlite3.Connection, report_id, account_holder=None,
                            settlement_point=None) -> list[dict]:
    holder_totals = _query_top_account_holders(
        db, report_id, account_holder, settlement_point)

    return [{"accountHolder": holder, "legalName": legal_name, "totalMwh": total_mwh}
            for holder, legal_name, total_mwh in holder_totals]
