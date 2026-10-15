# Imports
import sqlite3


from filters import summary_holdings_query


def get_top_account_holders(db: sqlite3.Connection, report_id, account_holder=None,
                            settlement_point=None) -> list[dict]:
    # Preparation
    holdings_sql, parameters = summary_holdings_query(
        report_id, account_holder, settlement_point)

    # Transformation: aggregate inventory before joining directory names.
    rows = db.execute(
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

    # Output
    return [{"accountHolder": row[0], "legalName": row[1], "totalMwh": row[2]}
            for row in rows]
