# Imports
import sqlite3
import unittest
from pathlib import Path

from queries import get_metadata, get_summary, resolve_report


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


class SummaryTests(unittest.TestCase):
    def setUp(self):
        # Setup: load the existing schema, without persisting a fixture database.
        self.db = sqlite3.connect(":memory:")
        schema = Path(__file__).resolve().parents[2] / "db/crr/sql/schema.sql"
        if not schema.exists():
            schema = Path("/data/sql/schema.sql")  # Existing read-only Compose mount.
        self.db.executescript(schema.read_text())
        self.db.executemany("INSERT INTO reports VALUES (?, ?)", REPORTS)
        self.db.executemany(
            "INSERT INTO account_holders (account_holder, legal_name) VALUES (?, ?)", HOLDERS
        )
        self.db.executemany(
            "INSERT INTO settlement_points (settlement_point) VALUES (?)", POINTS
        )
        self.db.executemany(
            "INSERT INTO crr_monthly_holdings VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?)",
            HOLDINGS,
        )

    def tearDown(self):
        self.db.close()

    def test_summary_filters(self):
        cases = [
            ({}, (210, 2, 4, 5, 130, 80)),
            ({"account_holder": "X"}, (100, 1, 2, 3, 70, 30)),
            ({"settlement_point": "A"}, (160, 2, 3, 4, 130, 30)),
            ({"account_holder": "X", "settlement_point": "A"}, (100, 1, 2, 3, 70, 30)),
            ({"account_holder": "X", "settlement_point": "C"}, (0, 0, 0, 0, 0, 0)),
            ({"account_holder": "", "settlement_point": ""}, (210, 2, 4, 5, 130, 80)),
        ]
        for filters, expected in cases:
            with self.subTest(filters=filters):
                # Execution
                summary = get_summary(self.db, **filters)

                # Assertions: expected values are independent fixture totals.
                self.assertEqual(summary, {
                    "reportId": 2, "totalMwh": expected[0],
                    "accountHolderCount": expected[1], "settlementPointCount": expected[2],
                    "directedPathCount": expected[3],
                    "hedgeTypeMwh": {"OPT": expected[4], "OBL": expected[5]},
                })

    def test_report_isolation_and_default(self):
        # Execution
        latest = resolve_report(self.db, None)
        previous = get_summary(self.db, report_id=1)

        # Assertions
        self.assertEqual(latest, 2)
        self.assertEqual(previous, {
            "reportId": 1, "totalMwh": 30, "accountHolderCount": 2,
            "settlementPointCount": 3, "directedPathCount": 2,
            "hedgeTypeMwh": {"OPT": 10, "OBL": 20},
        })

    def test_metadata_dropdowns(self):
        cases = [(None, None, ["A", "B", "C", "D"]),
                 (2, "X", ["A", "B"]), (2, "Y", ["A", "C", "D"]),
                 (1, None, ["A", "B", "D"])]
        for report_id, holder, points in cases:
            with self.subTest(report_id=report_id, holder=holder):
                # Execution
                metadata = get_metadata(self.db, report_id, holder)

                # Assertions
                self.assertEqual(metadata["settlementPoints"], points)
                self.assertEqual(metadata["reports"], [
                    {"reportId": 2, "publicationDate": "2026-10-01"},
                    {"reportId": 1, "publicationDate": "2026-09-01"},
                ])
                expected_holders = ([{"accountHolder": "X", "legalName": "Holder X"},
                                     {"accountHolder": "Z", "legalName": "Holder Z"}]
                                    if report_id == 1 else
                                    [{"accountHolder": "X", "legalName": "Holder X"},
                                     {"accountHolder": "Y", "legalName": None}])
                self.assertEqual(metadata["accountHolders"], expected_holders)
                self.assertEqual(metadata["reportId"], report_id or 2)


if __name__ == "__main__":
    unittest.main()
