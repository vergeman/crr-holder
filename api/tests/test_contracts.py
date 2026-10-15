# Imports
import asyncio
import unittest
from pathlib import Path
from urllib.parse import urlencode
from unittest.mock import patch

from fixtures import create_fixture_db
from services.holdings import get_contract_holdings, get_sink_holdings
from main import app


class ContractHoldingsTests(unittest.TestCase):
    def setUp(self):
        # Setup: build consistent originals and monthly cells in this fixture only.
        self.db = create_fixture_db()
        self.addCleanup(self.db.close)
        self.db.execute('DELETE FROM crr_monthly_holdings')
        self.db.executemany('INSERT INTO tou_hours VALUES (?, ?, ?)', [
            ('2026-10-01', 'PeakWD', 10), ('2026-10-01', 'PeakWE', 5),
            ('2026-10-01', 'Off-peak', 20), ('2026-11-01', 'PeakWD', 12),
        ])
        self.db.executemany('INSERT INTO crr_holdings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [
            (2, 100, 2, 'X', 'OPT', 'STANDARD', 'A', 'B', '2026-10-01', '2026-11-30', 'PeakWD', 1.25),
            (2, 100, 1, 'X', 'OPT', 'STANDARD', 'A', 'B', '2026-10-01', '2026-10-31', 'PeakWD', 1.25),
            (2, 99, 1, 'X', 'OPT', 'STANDARD', 'A', 'B', '2026-10-01', '2026-10-31', 'PeakWD', 2),
            (2, 101, 1, 'X', 'OPT', 'REFUND', 'A', 'B', '2026-10-01', '2026-10-31', 'PeakWE', 2),
            (2, 102, 1, 'X', 'OPT', 'STANDARD', 'A', 'B', '2026-10-01', '2026-10-31', 'Off-peak', 0),
            (2, 103, 1, 'Y', 'OPT', 'STANDARD', 'A', 'B', '2026-10-01', '2026-10-31', 'PeakWD', 5.5),
            (2, 104, 1, 'Z', 'OPT', 'STANDARD', 'A', 'B', '2026-10-01', '2026-10-31', 'PeakWD', 1),
            (2, 105, 1, 'X', 'OBL', 'STANDARD', 'A', 'B', '2026-10-01', '2026-10-31', 'PeakWD', 3),
            (2, 106, 1, 'X', 'OPT', 'STANDARD', 'B', 'A', '2026-10-01', '2026-10-31', 'PeakWD', 4),
            (2, 107, 1, 'X', 'OPT', 'STANDARD', 'A', 'A', '2026-10-01', '2026-10-31', 'PeakWD', 6),
            (1, 100, 1, 'X', 'OPT', 'STANDARD', 'A', 'B', '2026-10-01', '2026-10-31', 'PeakWD', 9),
        ])
        sql = Path(__file__).resolve().parents[2] / 'db/crr/sql/monthly_holdings.sql'
        if not sql.exists():
            sql = Path('/data/sql/monthly_holdings.sql')
        self.db.executescript(sql.read_text())

    def details(self, **filters):
        return get_contract_holdings(self.db, 'A', 'B', '2026-10-01', 'OPT', **filters)

    def test_original_fields_grouping_and_order(self):
        # Execution
        result = self.details()
        holders = result['accountHolders']
        groups = holders[0]['timeOfUseGroups']

        # Assertions: equal holder totals and segment contributions have stable ties.
        self.assertEqual(result['reportId'], 2)
        self.assertEqual(result['totalMwh'], 120)
        self.assertEqual([h['accountHolder'] for h in holders], ['X', 'Y', 'Z'])
        self.assertIsNone(holders[1]['legalName'])
        self.assertEqual([g['timeOfUse'] for g in groups], ['PeakWD', 'PeakWE', 'Off-peak'])
        self.assertEqual([g['totalMwh'] for g in groups], [45, 10, 0])
        self.assertEqual([g['hours'] for g in groups], [10, 5, 20])
        self.assertEqual([(c['crrId'], c['segmentId']) for c in groups[0]['contracts']],
                         [(99, 1), (100, 1), (100, 2)])
        self.assertEqual(groups[0]['contracts'][2], {
            'crrId': 100, 'segmentId': 2, 'crrType': 'STANDARD',
            'startDate': '2026-10-01', 'endDate': '2026-11-30',
            'mw': 1.25, 'monthMwh': 12.5,
        })
        self.assertEqual(groups[1]['contracts'][0]['crrType'], 'REFUND')
        self.assertEqual(len(groups[2]['contracts']), 1)

    def test_filters_and_sink_reconciliation(self):
        # Execution: compare all contribution levels with prepared cells.
        for filters in ({}, {'report_id': 1}, {'account_holder': 'X'},
                        {'settlement_point': 'A'}, {'settlement_point': 'B'},
                        {'account_holder': 'X', 'settlement_point': 'B'},
                        {'settlement_point': 'C'}, {'account_holder': 'missing'}):
            with self.subTest(filters=filters):
                result = self.details(**filters)
                parent = get_sink_holdings(self.db, 'A', **filters)
                cell = next((r['months'][0]['OPT'] for r in parent['sinks']
                             if r['sink'] == 'B'), 0)

                # Assertions
                self.assertEqual(result['totalMwh'], cell)
                self.assertEqual(result['totalMwh'], sum(h['totalMwh']
                                                        for h in result['accountHolders']))
                for holder in result['accountHolders']:
                    self.assertEqual(holder['totalMwh'], sum(g['totalMwh']
                                                            for g in holder['timeOfUseGroups']))
                    for group in holder['timeOfUseGroups']:
                        self.assertEqual(group['totalMwh'], sum(c['monthMwh']
                                                               for c in group['contracts']))
                        for contract in group['contracts']:
                            self.assertEqual(contract['monthMwh'],
                                             contract['mw'] * group['hours'])
        self.assertEqual(self.details(settlement_point='C')['accountHolders'], [])

    def test_pair_month_and_instrument_selection(self):
        # Execution
        same = get_contract_holdings(self.db, 'A', 'A', '2026-10-01', 'OPT',
                                     settlement_point='A')
        reverse = get_contract_holdings(self.db, 'B', 'A', '2026-10-01', 'OPT')
        obl = get_contract_holdings(self.db, 'A', 'B', '2026-10-01', 'OBL')
        later = get_contract_holdings(self.db, 'A', 'B', '2026-11-01', 'OPT')
        empty = get_contract_holdings(self.db, 'A', 'B', '2026-12-01', 'OPT')

        # Assertions
        self.assertEqual(same['totalMwh'], 60)
        self.assertEqual(reverse['totalMwh'], 40)
        self.assertEqual(obl['totalMwh'], 30)
        self.assertEqual(later['totalMwh'], 15)
        self.assertEqual(later['accountHolders'][0]['timeOfUseGroups'][0]['contracts'][0]['segmentId'], 2)
        self.assertEqual(empty['totalMwh'], 0)
        self.assertEqual(empty['accountHolders'], [])

    def test_route_validation(self):
        async def request(parameters):
            # Execution: exercise FastAPI directly without another test dependency.
            messages = []

            async def receive():
                return {'type': 'http.request', 'body': b'', 'more_body': False}

            async def send(message):
                messages.append(message)

            await app({'type': 'http', 'http_version': '1.1', 'method': 'GET',
                       'scheme': 'http', 'path': '/api/holdings/contracts',
                       'query_string': urlencode(parameters).encode(),
                       'headers': [], 'server': ('test', 80), 'client': ('test', 1),
                       'root_path': ''}, receive, send)
            return messages[0]['status']

        # Assertions: invalid dates and unsupported instruments never reach SQLite.
        valid = dict(source='A', sink='B', month='2026-10-01', hedge_type='OPT')
        with patch('database.sqlite3.connect') as connect:
            for field, value in [('month', '2026-10'), ('month', '2026-10-02'),
                                 ('month', '2026-13-01'), ('month', '2026-1-01'),
                                 ('hedge_type', 'BOTH')]:
                with self.subTest(field=field, value=value):
                    self.assertEqual(asyncio.run(request(valid | {field: value})), 422)
            connect.assert_not_called()


if __name__ == '__main__':
    unittest.main()
