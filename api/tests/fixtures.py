# Imports
import sqlite3
from pathlib import Path


# Preparation: literals mirror the exact eight-row fixture in plan 0004.
REPORTS = [(1, "2026-09-01"), (2, "2026-10-01")]
HOLDERS = [("X", "Holder X"), ("Y", None), ("Z", "Holder Z")]
POINTS = [(point,) for point in "ABCDE"]
HOLDINGS = [
    (1, "X", "A", "B", "2026-10-01", "OPT", 10, 0, 0),
    (1, "Z", "D", "A", "2026-10-01", "OBL", 20, 0, 0),
    (2, "X", "A", "B", "2026-10-01", "OPT", 8, 2, 0),
    (2, "X", "A", "B", "2026-11-01", "OPT", 10, 5, 5),
    (2, "X", "B", "A", "2026-10-01", "OBL", 0, 30, 0),
    (2, "X", "A", "A", "2026-10-01", "OPT", 0, 0, 40),
    (2, "Y", "C", "D", "2026-10-01", "OBL", 50, 0, 0),
    (2, "Y", "C", "A", "2026-10-01", "OPT", 20, 20, 20),
]


def create_fixture_db():
    # Setup: load the existing schema, without persisting a fixture database.
    db = sqlite3.connect(":memory:")
    schema = Path(__file__).resolve().parents[2] / "db/crr/sql/schema.sql"
    if not schema.exists():
        schema = Path("/data/sql/schema.sql")  # Existing read-only Compose mount.
    db.executescript(schema.read_text())
    db.executemany("INSERT INTO reports VALUES (?, ?)", REPORTS)
    db.executemany(
        "INSERT INTO account_holders (account_holder, legal_name) VALUES (?, ?)", HOLDERS
    )
    db.executemany(
        "INSERT INTO settlement_points (settlement_point) VALUES (?)", POINTS
    )
    db.executemany(
        "INSERT INTO crr_monthly_holdings VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?)",
        HOLDINGS,
    )

    refresh_summary_holdings(db)
    return db


def refresh_summary_holdings(db):
    sql = Path(__file__).resolve().parents[2] / "db/crr/sql/summary_holdings.sql"
    if not sql.exists():
        sql = Path("/data/sql/summary_holdings.sql")
    db.execute("DELETE FROM crr_summary_holdings")
    db.executescript(sql.read_text())
