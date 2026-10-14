# Imports
import unittest

from fixtures import create_fixture_db
from queries import get_summary


class RankingTests(unittest.TestCase):
    def setUp(self):
        # Setup
        self.db = create_fixture_db()
        self.addCleanup(self.db.close)

    def test_rankings_follow_summary_filters(self):
        cases = [
            ({}, [("Y", None, 110), ("X", "Holder X", 100)],
             [("A", 160), ("C", 110), ("B", 60), ("D", 50)]),
            ({"account_holder": "X"}, [("X", "Holder X", 100)],
             [("A", 100), ("B", 60)]),
            ({"settlement_point": "A"},
             [("X", "Holder X", 100), ("Y", None, 60)],
             [("A", 160), ("B", 60), ("C", 60)]),
            ({"account_holder": "X", "settlement_point": "A"},
             [("X", "Holder X", 100)], [("A", 100), ("B", 60)]),
            ({"account_holder": "X", "settlement_point": "C"}, [], []),
            ({"report_id": 1}, [("Z", "Holder Z", 20), ("X", "Holder X", 10)],
             [("A", 30), ("D", 20), ("B", 10)]),
        ]
        for filters, holders, points in cases:
            with self.subTest(filters=filters):
                # Execution: exercise the summary response, not isolated queries.
                summary = get_summary(self.db, **filters)

                # Assertions: independent totals include self paths and ties.
                self.assertEqual(summary["topAccountHolders"], [
                    {"accountHolder": holder, "legalName": name, "totalMwh": mwh}
                    for holder, name, mwh in holders
                ])
                self.assertEqual(summary["topSettlementPoints"], [
                    {"settlementPoint": point, "totalMwh": mwh}
                    for point, mwh in points
                ])

    def test_ties_and_limit_after_grouping(self):
        # Setup: local twelve-way ties do not change the shared fixture.
        self.db.execute("INSERT INTO reports VALUES (3, '2026-11-01')")
        identifiers = [f"T{index:02}" for index in range(12)]
        self.db.executemany(
            "INSERT INTO account_holders (account_holder) VALUES (?)",
            [(identifier,) for identifier in reversed(identifiers)],
        )
        self.db.executemany(
            "INSERT INTO settlement_points (settlement_point) VALUES (?)",
            [(identifier,) for identifier in reversed(identifiers)],
        )
        self.db.executemany(
            "INSERT INTO crr_monthly_holdings VALUES "
            "(3, ?, ?, ?, '2026-11-01', 'OPT', 0, 0, 0, 1, 0, 0)",
            [(identifier, identifier, identifier) for identifier in reversed(identifiers)],
        )

        # Execution
        summary = get_summary(self.db)

        # Assertions: full rows verify alphabetical ties, limit, and self counting.
        self.assertEqual(summary["topAccountHolders"], [
            {"accountHolder": identifier, "legalName": None, "totalMwh": 1}
            for identifier in identifiers[:10]
        ])
        self.assertEqual(summary["topSettlementPoints"], [
            {"settlementPoint": identifier, "totalMwh": 1}
            for identifier in identifiers[:10]
        ])


if __name__ == "__main__":
    unittest.main()
