import unittest

from fixtures import HOLDINGS, POINTS, create_fixture_db
from services.summary import get_summary


class GeographyTests(unittest.TestCase):
    def test_roles_filters_and_reports(self):
        # Coordinates are local to geographic tests; C is partially mapped.
        self.db = create_fixture_db()
        self.addCleanup(self.db.close)
        self.db.executemany(
            'UPDATE settlement_points SET longitude=?, latitude=? WHERE settlement_point=?',
            [(-100, 32, 'A'), (-99, 31, 'B'), (-98, None, 'C')])

        # Each case is (selected_filters, aggregate_results), where results are
        # [(settlement_point, sourceMWh, sinkMWh), ...] for the filtered holdings.
        # Example: {'settlement_point': 'A'} selects holdings starting or ending
        # at A; ('A', 70, 130) means 70 source MWh and 130 sink MWh at A.
        cases = [
            ({}, [('A', 70, 130), ('B', 30, 30), ('C', 110, 0), ('D', 0, 50)]),
            ({'account_holder': 'X'}, [('A', 70, 70), ('B', 30, 30)]),
            ({'settlement_point': 'A'}, [('A', 70, 130), ('B', 30, 30), ('C', 60, 0)]),
            ({'account_holder': 'Y', 'settlement_point': 'A'}, [('A', 0, 60), ('C', 60, 0)]),
            ({'report_id': 1}, [('A', 10, 20), ('B', 0, 10), ('D', 20, 0)]),
            ({'account_holder': 'X', 'settlement_point': 'C'}, []),
        ]
        for filters, expected in cases:
            with self.subTest(filters=filters):
                summary = get_summary(self.db, **filters)
                points = summary['geographicFootprint']

                # Independent expected role totals include self paths.
                self.assertEqual([(p['settlementPoint'], p['sourceMwh'], p['sinkMwh'])
                                  for p in points], expected)
                for role in ('sourceMwh', 'sinkMwh'):
                    self.assertEqual(sum(p[role] for p in points), summary['totalMwh'])
                for p in points:
                    if p['settlementPoint'] == 'A':
                        self.assertEqual((p['longitude'], p['latitude']), (-100, 32))
                    if p['settlementPoint'] == 'C':
                        self.assertEqual((p['longitude'], p['latitude']), (-98, None))
                    if p['settlementPoint'] == 'D':
                        self.assertEqual((p['longitude'], p['latitude']), (None, None))

    def test_complete_output_includes_zero_inventory(self):
        # Add 8 points to the fixture's 4. The last added point has zero
        # MWh and must appear in geography.
        # range(1, 9) produces 1 through 8; the upper bound is excluded.
        added_points = [(f'Z{i:02}',) for i in range(1, 9)]
        added_holdings = [
            (2, 'X', point, 'A', '2026-10-01', 'OPT', i if i < 8 else 0, 0, 0)
            for i, (point,) in enumerate(added_points, 1)
        ]
        self.db = create_fixture_db(points=POINTS + added_points,
                                    holdings=HOLDINGS + added_holdings)
        self.addCleanup(self.db.close)

        summary = get_summary(self.db)
        # geographicFootprint returns all participating points, not a ranking.
        points = summary['geographicFootprint']

        self.assertEqual(len(points), 12)
        # The shared fixture supplies A, B, C, D; this test adds Z01 through Z08.
        # E has no holdings, so it is absent: 4 existing + 8 added = 12 points.
        # Identifier sorting puts Z08 last; it is the added zero-MWh point.
        self.assertEqual(points[-1]['settlementPoint'], 'Z08')
        self.assertEqual(points[-1]['sourceMwh'], 0)
        # All 12 points also fit within the ranking limit.
        self.assertEqual(len(summary['topSettlementPoints']), 12)


if __name__ == '__main__':
    unittest.main()
