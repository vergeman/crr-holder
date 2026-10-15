# Imports
import unittest

from fixtures import create_fixture_db
from queries import get_metadata, get_summary
from services.helpers import resolve_report


class SummaryTests(unittest.TestCase):
    def setUp(self):
        # Setup: each test owns its fresh in-memory connection.
        self.db = create_fixture_db()
        self.addCleanup(self.db.close)

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
                expected_metrics = {
                    "reportId": 2, "totalMwh": expected[0],
                    "accountHolderCount": expected[1], "settlementPointCount": expected[2],
                    "directedPathCount": expected[3],
                    "hedgeTypeMwh": {"OPT": expected[4], "OBL": expected[5]},
                }
                self.assertEqual(
                    {key: summary[key] for key in expected_metrics}, expected_metrics)

    def test_report_isolation_and_default(self):
        # Execution
        latest = resolve_report(self.db, None)
        previous = get_summary(self.db, report_id=1)

        # Assertions
        self.assertEqual(latest, 2)
        expected_metrics = {
            "reportId": 1, "totalMwh": 30, "accountHolderCount": 2,
            "settlementPointCount": 3, "directedPathCount": 2,
            "hedgeTypeMwh": {"OPT": 10, "OBL": 20},
        }
        self.assertEqual(
            {key: previous[key] for key in expected_metrics}, expected_metrics)

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
