"""Check the database transport needed by SQLite's HTTP VFS."""

import asyncio
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from main import app


class DatabaseDownloadTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.contents = bytes(range(256))
        self.path = Path(directory.name) / "database.sqlite"
        self.path.write_bytes(self.contents)
        environment = patch.dict("os.environ", {"DB_FILE": str(self.path)})
        environment.start()
        self.addCleanup(environment.stop)

    def request(self, method, headers=()):
        async def execute():
            messages = []

            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}

            async def send(message):
                messages.append(message)

            await app({
                "type": "http", "http_version": "1.1", "method": method,
                "asgi": {"spec_version": "2.4"},
                "scheme": "http", "path": "/api/database", "query_string": b"",
                "headers": list(headers), "server": ("test", 80),
                "client": ("test", 1), "root_path": "",
            }, receive, send)
            return (
                messages[0]["status"], dict(messages[0]["headers"]),
                b"".join(message.get("body", b"") for message in messages[1:]),
            )

        return asyncio.run(execute())

    def test_head_reports_file_size_without_body(self):
        status, headers, body = self.request("HEAD")

        self.assertEqual(status, 200)
        self.assertEqual(headers[b"content-length"], b"256")
        self.assertEqual(headers[b"accept-ranges"], b"bytes")
        self.assertEqual(body, b"")

    def test_range_returns_exact_file_bytes(self):
        status, headers, body = self.request("GET", [(b"range", b"bytes=16-31")])

        self.assertEqual(status, 206)
        self.assertEqual(headers[b"content-range"], b"bytes 16-31/256")
        self.assertEqual(headers[b"content-length"], b"16")
        self.assertEqual(body, self.contents[16:32])

    def test_unsatisfiable_range_reports_file_size(self):
        status, headers, body = self.request("GET", [(b"range", b"bytes=256-300")])

        self.assertEqual(status, 416)
        self.assertEqual(headers[b"content-range"], b"bytes */256")
        self.assertEqual(body, b"")
