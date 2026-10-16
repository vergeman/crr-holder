from contextlib import asynccontextmanager, contextmanager
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from fixtures import create_fixture_db
from main import app
import test_contracts


RESPONSES = Path(__file__).parent / 'fixtures/service_responses'


@asynccontextmanager
async def connected_client():
    async with app.router.lifespan_context(app):
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), base_url='http://localhost:8000'
        ) as http:
            async with streamable_http_client(
                'http://localhost:8000/mcp/', http_client=http
            ) as streams:
                async with ClientSession(*streams) as client:
                    await client.initialize()
                    yield client, http


class McpTests(unittest.IsolatedAsyncioTestCase):
    async def test_mounted_protocol(self):
        event_loop_thread = threading.get_ident()
        database_threads = []
        contracts = False

        @contextmanager
        def fixture_database():
            # Create, query, and close SQLite in the SDK's invocation thread.
            database_threads.append(threading.get_ident())
            if contracts:
                fixture = test_contracts.ContractHoldingsTests()
                fixture.setUp()
                try:
                    yield fixture.db
                finally:
                    fixture.doCleanups()
            else:
                db = create_fixture_db()
                db.executemany(
                    'UPDATE settlement_points SET longitude=?, latitude=? WHERE settlement_point=?',
                    [(-100, 32, 'A'), (-99, 31, 'B'), (-98, None, 'C')],
                )
                try:
                    yield db
                finally:
                    db.close()

        with patch('mcp_server.open_database', fixture_database):
            async with connected_client() as (client, http):
                discovery = await client.list_tools()
                names = {'get_metadata', 'get_summary', 'get_source_holdings',
                         'get_sink_holdings', 'get_contract_holdings'}
                self.assertEqual({tool.name for tool in discovery.tools}, names)
                for tool in discovery.tools:
                    self.assertTrue(tool.annotations.read_only_hint)
                    self.assertIsNotNone(tool.output_schema)

                # Reuse complete committed responses, including empty selections.
                scenarios = {
                    'market': {}, 'previous_report': {'report_id': 1},
                    'account': {'account_holder': 'X'},
                    'point': {'settlement_point': 'A'},
                    'combined': {'account_holder': 'X', 'settlement_point': 'A'},
                    'empty': {'account_holder': 'Z'},
                }
                for tool, baseline, required in [
                    ('get_metadata', 'metadata', {}),
                    ('get_summary', 'summary', {}),
                    ('get_source_holdings', 'sources', {}),
                    ('get_sink_holdings', 'sinks', {'source': 'A'}),
                    ('get_contract_holdings', 'contracts', {
                        'source': 'A', 'sink': 'B', 'month': '2026-10-01',
                        'hedge_type': 'OPT',
                    }),
                ]:
                    contracts = baseline == 'contracts'
                    expected = json.loads((RESPONSES / f'{baseline}.json').read_text())
                    for scenario, filters in scenarios.items():
                        if baseline == 'metadata':
                            filters = {k: v for k, v in filters.items()
                                       if k != 'settlement_point'}
                        with self.subTest(tool=tool, scenario=scenario):
                            result = await client.call_tool(tool, required | filters)
                            self.assertFalse(result.is_error)
                            self.assertEqual(result.structured_content, expected[scenario])

                contracts = False
                expected = json.loads((RESPONSES / 'sources.json').read_text())
                for offset in range(4):
                    result = await client.call_tool('get_source_holdings',
                                                    {'limit': 1, 'offset': offset})
                    self.assertEqual(result.structured_content, expected[f'page_{offset}'])
                self.assertTrue(database_threads)
                self.assertNotIn(event_loop_thread, database_threads)

                await self.check_validation(client, http)

                # HTTP contracts remain accessible alongside the MCP mount.
                with patch('routes.open_database', fixture_database):
                    response = await http.get('/api/metadata')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), json.loads(
                    (RESPONSES / 'metadata.json').read_text())['market'])
                schema = (await http.get('/openapi.json')).json()
                self.assertEqual(schema['paths']['/api/metadata']['get']['operationId'],
                                 'getMetadata')
                self.assertEqual(len(schema['paths']), 5)

    async def check_validation(self, client, http):
        valid = {'source': 'A', 'sink': 'B', 'month': '2026-10-01', 'hedge_type': 'OPT'}
        invalid = [
            ('get_source_holdings', '/api/holdings/sources', {'limit': 0}),
            ('get_source_holdings', '/api/holdings/sources', {'limit': 101}),
            ('get_source_holdings', '/api/holdings/sources', {'offset': -1}),
        ]
        for field, value in [('month', '2026-10'), ('month', '2026-10-02'),
                             ('month', '2026-13-01'), ('month', '2026-1-01'),
                             ('hedge_type', 'BOTH')]:
            invalid.append(('get_contract_holdings', '/api/holdings/contracts',
                            valid | {field: value}))

        with patch('mcp_server.open_database') as database, \
                patch('routes.open_database') as http_database:
            for tool, route, parameters in invalid:
                with self.subTest(tool=tool, parameters=parameters):
                    result = await client.call_tool(tool, parameters)
                    self.assertTrue(result.is_error)
                    self.assertEqual((await http.get(route, params=parameters)).status_code, 422)
            database.assert_not_called()
            http_database.assert_not_called()
