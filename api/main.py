import sqlite3
from contextlib import closing

from fastapi import FastAPI

app = FastAPI()


@app.get("/api/account-holders")
def account_holders() -> list[str]:
    # Read the prepared dataset without changing it.
    with closing(sqlite3.connect("file:/data/crr.sqlite?mode=ro", uri=True)) as db:
        rows = db.execute(
            "SELECT account_holder FROM account_holders ORDER BY account_holder"
        ).fetchall()

    return [row[0] for row in rows]
