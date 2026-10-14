# Imports
import unittest

from fixtures import create_fixture_db
from holdings import get_sink_holdings, get_source_holdings


class SinkHoldingsTests(unittest.TestCase):
    def setUp(self):
        # Setup
        self.db = create_fixture_db()
        self.addCleanup(self.db.close)

    def test_reports_filters_and_parent_reconciliation(self):
        # Execution: reconcile each expanded source under the same portfolio.
        for report in (None, 1, 2):
            for holder, point in ((None, None), ('X', None), (None, 'A'),
                                  ('X', 'A'), ('X', 'B')):
                with self.subTest(report=report, holder=holder, point=point):
                    parents = get_source_holdings(self.db, report, holder, point)
                    for parent in parents['sources']:
                        result = get_sink_holdings(self.db, parent['source'],
                                                  report, holder, point)

                        # Assertions: full months and hedge totals partition the parent.
                        self.assertEqual(result['reportId'], parents['reportId'])
                        self.assertEqual(result['source'], parent['source'])
                        self.assertEqual(result['deliveryMonths'], parents['deliveryMonths'])
                        for hedge, field in (('OPT', 'totalOptMwh'), ('OBL', 'totalOblMwh')):
                            self.assertEqual(sum(row[field] for row in result['sinks']),
                                             parent[field])
                            for index, cell in enumerate(parent['months']):
                                self.assertEqual(sum(row['months'][index][hedge]
                                                     for row in result['sinks']), cell[hedge])
                            for row in result['sinks']:
                                self.assertEqual(row[field], sum(cell[hedge] for cell in row['months']))
                                self.assertEqual([cell['deliveryMonth'] for cell in row['months']],
                                                 result['deliveryMonths'])

        # Assertions: settlement point matching source keeps all sinks; matching sink narrows them.
        all_sinks = get_sink_holdings(self.db, 'A', settlement_point='A')
        narrowed = get_sink_holdings(self.db, 'A', settlement_point='B')
        self.assertEqual([row['sink'] for row in all_sinks['sinks']], ['A', 'B'])
        self.assertEqual(all_sinks['sinks'][0]['totalOptMwh'], 40)
        self.assertEqual([row['sink'] for row in narrowed['sinks']], ['B'])
        self.assertEqual(narrowed['sinks'][0]['totalOptMwh'], 30)
        self.assertEqual(get_sink_holdings(self.db, 'B')['sinks'][0]['totalOblMwh'], 30)

    def test_complete_timeline_and_empty_sources(self):
        # Setup: a later holding extends the report with an intervening empty month.
        self.db.execute("""INSERT INTO crr_monthly_holdings
            VALUES (2, 'Y', 'D', 'A', '2027-01-01', 'OBL', 0, 0, 0, 1, 0, 0)""")

        # Execution
        result = get_sink_holdings(self.db, 'A', account_holder='X')
        empty = get_sink_holdings(self.db, 'A', account_holder='Z')
        missing = get_sink_holdings(self.db, 'unknown')

        # Assertions
        self.assertEqual(result['deliveryMonths'], ['2026-10-01', '2026-11-01',
                                                    '2026-12-01', '2027-01-01'])
        self.assertTrue(all(row['months'][2]['OPT'] == row['months'][2]['OBL'] == 0
                            for row in result['sinks']))
        for response in (empty, missing):
            self.assertEqual(response['sinks'], [])
            self.assertEqual(response['deliveryMonths'], result['deliveryMonths'])

    def test_all_sinks_and_deterministic_ordering(self):
        # Setup: more sinks than the source page size, with equal combined totals.
        self.db.executemany("INSERT INTO settlement_points (settlement_point) VALUES (?)",
                            [(f'S{i:02}',) for i in range(23)])
        self.db.executemany("""INSERT INTO crr_monthly_holdings
            VALUES (2, 'Y', 'A', ?, '2026-10-01', 'OBL', 0, 0, 0, 2, 0, 0)""",
            [(f'S{i:02}',) for i in range(23)])

        # Execution
        result = get_sink_holdings(self.db, 'A')

        # Assertions
        self.assertEqual([row['sink'] for row in result['sinks']],
                         ['A', 'B'] + [f'S{i:02}' for i in range(23)])
        self.assertEqual(len(result['sinks']), 25)


if __name__ == '__main__':
    unittest.main()
