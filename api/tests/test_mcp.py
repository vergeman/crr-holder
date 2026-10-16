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
                await self.check_usage(client)

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
                patch('routes.open_database') as http_database, \
                patch('mcp_usage.logger.info') as usage:
            for tool, route, parameters in invalid:
                with self.subTest(tool=tool, parameters=parameters):
                    result = await client.call_tool(tool, parameters)
                    self.assertTrue(result.is_error)
                    self.assertEqual((await http.get(route, params=parameters)).status_code, 422)
            database.assert_not_called()
            http_database.assert_not_called()
            usage.assert_not_called()

    async def check_usage(self, client):
        with patch('mcp_usage.logger.info') as log:
            success = await client.call_tool('get_metadata')
            with patch('mcp_server.metadata.get_metadata', side_effect=RuntimeError('private')):
                failure = await client.call_tool('get_metadata', {'account_holder': 'X'})

        self.assertFalse(success.is_error)
        self.assertTrue(failure.is_error)
        records = [json.loads(call.args[0]) for call in log.call_args_list
                   if call.args[0].startswith('{')]
        self.assertEqual(len(records), 2)
        for record, status in zip(records, ['success', 'error']):
            self.assertEqual(set(record), {
                'tool', 'parameters', 'status', 'elapsed_ms', 'cpu_ms',
                'rss_before_bytes', 'rss_after_bytes',
                'input_payload_bytes', 'output_payload_bytes',
            } | ({'error_type'} if status == 'error' else set()))
            self.assertEqual(record['tool'], 'get_metadata')
            self.assertEqual(record['status'], status)
            self.assertEqual(record['parameters'], {
                'report_id': None, 'account_holder': 'X' if status == 'error' else None,
            })
            for field in ('elapsed_ms', 'cpu_ms'):
                self.assertIsInstance(record[field], float)
                self.assertGreaterEqual(record[field], 0)
            for field in ('rss_before_bytes', 'rss_after_bytes'):
                self.assertIsInstance(record[field], int)
                self.assertGreater(record[field], 0)
        self.assertEqual(records[1]['error_type'], 'RuntimeError')
        self.assertEqual(records[0]['input_payload_bytes'],
                         len(b'{"report_id":null,"account_holder":null}'))
        self.assertEqual(records[1]['input_payload_bytes'],
                         len(b'{"report_id":null,"account_holder":"X"}'))
        expected = json.loads((RESPONSES / 'metadata.json').read_text())['market']
        self.assertEqual(records[0]['output_payload_bytes'], len(json.dumps(
            expected, ensure_ascii=False, separators=(',', ':')).encode('utf-8')))
        self.assertIsNone(records[1]['output_payload_bytes'])
        self.assertNotIn('private', json.dumps(records))
