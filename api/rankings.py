# Imports
import sqlite3
from time import perf_counter


from filters import monthly_holdings_query


def get_top_account_holders(db: sqlite3.Connection, report_id, account_holder=None,
                            settlement_point=None) -> list[dict]:
    # Preparation
    holdings_sql, parameters = monthly_holdings_query(
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


def get_top_settlement_points(db: sqlite3.Connection, report_id, account_holder=None,
                              settlement_point=None) -> list[dict]:
    # Preparation
    holdings_sql, parameters = monthly_holdings_query(
        report_id, account_holder, settlement_point)

    # Transformation: preserve each monthly contribution without doubling self paths.
    sql = f"""
        -- Matching holdings use the same inclusive point predicate as summary.
        WITH holdings AS (
            {holdings_sql}
        ), contributions AS (
            SELECT source AS point, mwh FROM holdings
            UNION ALL
            -- Compare endpoints: identical source and sink contribute only once.
            SELECT sink AS point, mwh FROM holdings WHERE sink != source
        )
        SELECT point, SUM(mwh) AS total_mwh
        FROM contributions GROUP BY point
        -- Compare unrounded totals first, identifiers resolve ties.
        ORDER BY total_mwh DESC, point ASC LIMIT 100
        """

    print("settlement point rankings query plan:", flush=True)
    for step in db.execute("EXPLAIN QUERY PLAN " + sql, parameters).fetchall():
        print(tuple(step), flush=True)

    started = perf_counter()
    rows = db.execute(sql, parameters).fetchall()
    elapsed_ms = (perf_counter() - started) * 1000
    print(f"settlement point rankings SQL: {elapsed_ms:.2f} ms ({len(rows)} rows)", flush=True)

    # Output: point groups overlap; they are not a portfolio partition.
    started = perf_counter()
    result = [{"settlementPoint": row[0], "totalMwh": row[1]} for row in rows]
    elapsed_ms = (perf_counter() - started) * 1000
    print(f"settlement point rankings Python result building: {elapsed_ms:.2f} ms", flush=True)
    return result
