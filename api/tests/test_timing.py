import unittest

from fixtures import create_fixture_db
from services.metadata import get_metadata


class TimingTests(unittest.TestCase):
    def test_metadata_timing(self):
        db = create_fixture_db()
        self.addCleanup(db.close)

        with self.assertLogs("uvicorn.error", level="INFO") as logs:
            metadata = get_metadata(db, account_holder="X")

        self.assertEqual(metadata, {
            "reportId": 2,
            "reports": [
                {"reportId": 2, "publicationDate": "2026-10-01"},
                {"reportId": 1, "publicationDate": "2026-09-01"},
            ],
            "accountHolders": [
                {"accountHolder": "X", "legalName": "Holder X"},
                {"accountHolder": "Y", "legalName": None},
            ],
            "settlementPoints": ["A", "B"],
        })
        self.assertEqual(len(logs.records), 1)
        self.assertRegex(
            logs.records[0].getMessage(),
            r"^get_metadata parameters=\{'report_id': None, 'account_holder': 'X'\} "
            r"elapsed_ms=\d+\.\d{2}$",
        )


if __name__ == "__main__":
    unittest.main()
