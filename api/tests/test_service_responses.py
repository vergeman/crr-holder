"""Check complete response equality against committed fixtures.

Services run against small in-memory data. Their outputs must equal the JSON in
api/tests/fixtures/service_responses/, including values, fields, and list order.
"""

from contextlib import closing
import json
from pathlib import Path
import unittest

from fixtures import HOLDINGS, create_fixture_db
from services.holdings import get_contract_holdings, get_sink_holdings, get_source_holdings
from services.metadata import get_metadata
from services.summary import get_summary
import test_contracts


# Expected optimized responses, verified against the original baseline in plan 0013.
RESPONSES = Path(__file__).parent / 'fixtures/service_responses'


def fixture_responses():
    db = create_fixture_db()  # Independent reports, holders, points, and holdings.
    try:
        # Include mapped, partially mapped, and unmapped settlement points.
        db.executemany(
            'UPDATE settlement_points SET longitude=?, latitude=? WHERE settlement_point=?',
            [(-100, 32, 'A'), (-99, 31, 'B'), (-98, None, 'C')],
        )
        filters = {  # Scenario name -> service keyword arguments.
            'market': {}, 'previous_report': {'report_id': 1},
            'account': {'account_holder': 'X'}, 'point': {'settlement_point': 'A'},
            'combined': {'account_holder': 'X', 'settlement_point': 'A'},
            'empty': {'account_holder': 'Z'},
        }
        # Service name -> scenario name -> complete returned response.
        results = {name: {} for name in ('metadata', 'summary', 'sources', 'sinks')}
        for name, parameters in filters.items():
            # Metadata: report and account dropdowns, without point filtering.
            results['metadata'][name] = get_metadata(
                db, **{k: v for k, v in parameters.items() if k != 'settlement_point'})

            # Summary: totals, geography, and rankings for the same portfolio.
            results['summary'][name] = get_summary(db, **parameters)

            # Sources: ranked source rows and their monthly cells.
            results['sources'][name] = get_source_holdings(db, **parameters)

            # Sinks: monthly sink rows beneath source A, including its self path.
            results['sinks'][name] = get_sink_holdings(db, 'A', **parameters)

        # Sources: capture each single-row page and the exhausted page.
        for offset in (0, 1, 2, 3):
            results['sources'][f'page_{offset}'] = get_source_holdings(
                db, limit=1, offset=offset)

    finally:
        db.close()

    # Sources: a later holding creates a timeline gap outside X's portfolio.
    gap_holdings = HOLDINGS + [
        (2, 'Y', 'D', 'A', '2027-01-01', 'OBL', 1, 0, 0),
    ]
    with closing(create_fixture_db(holdings=gap_holdings)) as db:
        results['sources']['timeline_gap'] = get_source_holdings(db, account_holder='X')

    # Sources and summary: build a separate, complete zero-exposure portfolio.
    zero_holdings = [row[:6] + (0, 0, 0) if row[1] == 'X' else row
                     for row in gap_holdings]
    with closing(create_fixture_db(holdings=zero_holdings)) as db:
        db.executemany(
            'UPDATE settlement_points SET longitude=?, latitude=? WHERE settlement_point=?',
            [(-100, 32, 'A'), (-99, 31, 'B'), (-98, None, 'C')],
        )
        results['sources']['zero_exposure'] = get_source_holdings(db, account_holder='X')
        results['summary']['zero_exposure'] = get_summary(db, account_holder='X')

    # Contracts: reuse original segments and their matching monthly holdings.
    contracts = test_contracts.ContractHoldingsTests()
    try:
        contracts.setUp()
        results['contracts'] = {
            name: contracts.details(**parameters) for name, parameters in filters.items()
        }

        # Contracts: select a cell whose source and sink are both A.
        results['contracts']['self_path'] = get_contract_holdings(
            contracts.db, 'A', 'A', '2026-10-01', 'OPT')
    finally:
        contracts.doCleanups()
    return results


class ServiceResponseTests(unittest.TestCase):
    def test_complete_responses(self):
        # Execute all service scenarios against fresh fixture databases.
        actual = fixture_responses()  # Service -> scenario -> current response.

        # Compare each service with its committed response, including list ordering.
        for service, response in actual.items():
            with self.subTest(service=service):
                # Expected scenarios for this service; never regenerated here.
                expected = json.loads((RESPONSES / f'{service}.json').read_text())
                self.assertEqual(response, expected)
