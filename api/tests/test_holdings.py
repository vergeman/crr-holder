# Imports
import unittest

from fixtures import create_fixture_db
from holdings import get_source_holdings
from queries import get_summary


class HoldingsTests(unittest.TestCase):
    def setUp(self):
        # Setup
        self.db = create_fixture_db()
        self.addCleanup(self.db.close)

    def test_reports_filters_and_reconciliation(self):
        # Execution: compare summary and source pages under identical filters.
        for report in (None, 1, 2):
            for holder, point in ((None, None), ('X', None), (None, 'A'),
                                  ('X', 'A'), ('Z', 'E')):
                with self.subTest(report=report, holder=holder, point=point):
                    # Summary: obtain portfolio totals for reconciliation.
                    summary = get_summary(self.db, report, holder, point)

                    # Sources: collect every page for the same portfolio.
                    sources = []
                    offset = 0
                    while True:
                        page = get_source_holdings(self.db, report, holder, point, 1, offset)

                        # Assertions: each source has complete months and totals.
                        self.assertEqual(page['reportId'], summary['reportId'])
                        sources.extend(page['sources'])
                        for source in page['sources']:
                            self.assertEqual([cell['deliveryMonth'] for cell in source['months']],
                                             page['deliveryMonths'])
                            self.assertEqual(source['totalOptMwh'] + source['totalOblMwh'], sum(
                                cell['OPT'] + cell['OBL'] for cell in source['months']))

                            for hedge, field in (('OPT', 'totalOptMwh'), ('OBL', 'totalOblMwh')):
                                self.assertEqual(source[field],
                                                 sum(cell[hedge] for cell in source['months']))

                        if page['nextOffset'] is None:
                            break
                        offset = page['nextOffset']

                    # Reconciliation: all pages match summary totals without duplicates.
                    self.assertEqual(len(sources), len({row['source'] for row in sources}))
                    self.assertEqual(sum(row['totalOptMwh'] + row['totalOblMwh'] for row in sources), summary['totalMwh'])

                    for hedge, field in (('OPT', 'totalOptMwh'), ('OBL', 'totalOblMwh')):
                        self.assertEqual(sum(row[field] for row in sources),
                                         summary['hedgeTypeMwh'][hedge])
                        self.assertEqual(sum(cell[hedge] for row in sources for cell in row['months']),
                                         summary['hedgeTypeMwh'][hedge])

                    # Empty portfolios retain the report timeline.
                    if not sources:
                        self.assertIsNone(page['holdingsRange'])
                        self.assertTrue(page['deliveryMonths'])

    def test_month_cells_and_portfolio_bounds(self):
        # Setup: add a January CRR for source D, leaving December empty.
        # D ranks below the first source page; its month must still set the bounds.
        self.db.execute("""INSERT INTO crr_monthly_holdings
            VALUES (2, 'Y', 'D', 'A', '2027-01-01', 'OBL', 0, 0, 0, 1, 0, 0)""")

        # Execution
        page = get_source_holdings(self.db, account_holder='X')
        market = get_source_holdings(self.db, limit=1)
        empty = get_source_holdings(self.db, account_holder='Z')

        # Assertions
        self.assertEqual(page['deliveryMonths'], ['2026-10-01', '2026-11-01',
                                                  '2026-12-01', '2027-01-01'])
        self.assertEqual(page['holdingsRange'], {'firstMonth': '2026-10-01',
                                                'lastMonth': '2026-11-01'})
        self.assertEqual(market['holdingsRange']['lastMonth'], '2027-01-01')
        self.assertEqual([row['source'] for row in page['sources']], ['A', 'B'])
        self.assertEqual(page['sources'][0]['months'][0],
                         {'deliveryMonth': '2026-10-01', 'OPT': 50, 'OBL': 0})
        self.assertEqual(page['sources'][0]['months'][2]['OPT'], 0)
        self.assertEqual(empty['deliveryMonths'], page['deliveryMonths'])
        self.assertEqual(empty['sources'], [])
        self.assertIsNone(empty['nextOffset'])

    def test_zero_contributions_have_no_holdings_range(self):
        # Setup
        self.db.execute("UPDATE crr_monthly_holdings SET peak_wd_mwh=0, "
                        "peak_we_mwh=0, off_peak_mwh=0 WHERE account_holder='X'")

        # Execution
        page = get_source_holdings(self.db, account_holder='X')

        # Assertions
        self.assertIsNone(page['holdingsRange'])
        self.assertEqual([row['source'] for row in page['sources']], ['A', 'B'])
        self.assertTrue(all(row['totalOptMwh'] + row['totalOblMwh'] == 0 for row in page['sources']))

    def test_ties_and_complete_source_pages(self):
        # Setup: local pagination rows exceed the default page size.
        self.db.executemany("INSERT INTO settlement_points (settlement_point) VALUES (?)",
                            [(f'S{i:02}',) for i in range(23)])
        self.db.executemany("""INSERT INTO crr_monthly_holdings
            VALUES (2, 'Y', ?, 'A', '2026-10-01', 'OPT', 0, 0, 0, 2, 0, 0)""",
            [(f'S{i:02}',) for i in range(23)])

        # Execution
        first = get_source_holdings(self.db)
        second = get_source_holdings(self.db, offset=first['nextOffset'])
        rows = first['sources'] + second['sources']
        exhausted = get_source_holdings(self.db, offset=100)

        # Assertions
        self.assertEqual(len(first['sources']), 20)
        self.assertEqual(first['nextOffset'], 20)
        self.assertIsNone(second['nextOffset'])
        self.assertEqual([row['source'] for row in rows],
                         ['C', 'A', 'B'] + [f'S{i:02}' for i in range(23)])
        self.assertEqual(exhausted['sources'], [])
        self.assertIsNone(exhausted['nextOffset'])
        self.assertIsNotNone(exhausted['holdingsRange'])


if __name__ == '__main__':
    unittest.main()
