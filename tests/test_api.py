from __future__ import annotations

import json
import threading
import time
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from scripts.run_api import Handler


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.05)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=1)

    def test_health_and_process_and_get_session(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=2)

        conn.request("GET", "/health")
        health = conn.getresponse()
        self.assertEqual(health.status, 200)
        health_data = json.loads(health.read().decode("utf-8"))
        self.assertTrue(health_data["ok"])

        with open("examples/session_example.json", "r", encoding="utf-8") as f:
            payload = f.read()

        conn.request(
            "POST",
            "/process",
            body=payload.encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        process = conn.getresponse()
        self.assertEqual(process.status, 200)
        process_data = json.loads(process.read().decode("utf-8"))
        self.assertEqual(process_data["session_id"], "sess_001")

        conn.request("GET", "/sessions/sess_001")
        stored = conn.getresponse()
        self.assertEqual(stored.status, 200)
        stored_data = json.loads(stored.read().decode("utf-8"))
        self.assertEqual(stored_data["session_id"], "sess_001")

        conn.close()

    def test_process_with_mock_asr_input(self) -> None:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=2)
        payload = {
            "session_id": "sess_mock_asr",
            "submit_ts_ms": 1710000130000,
            "strokes": [
                {
                    "stroke_id": "s_001",
                    "page_id": "page_1",
                    "canvas_id": "canvas_A",
                    "points": [
                        {"point_id": "p_1", "stroke_id": "s_001", "x": 100, "y": 100, "ts_ms": 1710000123000}
                    ],
                    "start_ts_ms": 1710000123000,
                    "end_ts_ms": 1710000124200,
                    "bbox": {"x": 100, "y": 90, "w": 30, "h": 30}
                }
            ],
            "erase_events": [],
            "asr_input": {
                "mock_segments": [
                    {
                        "start_ts_ms": 1710000122500,
                        "end_ts_ms": 1710000125000,
                        "start_offset_ms": 2500,
                        "end_offset_ms": 5000,
                        "text": "mock asr text"
                    }
                ]
            }
        }

        conn.request(
            "POST",
            "/process",
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        process = conn.getresponse()
        self.assertEqual(process.status, 200)
        process_data = json.loads(process.read().decode("utf-8"))
        self.assertEqual(process_data["session_id"], "sess_mock_asr")
        self.assertEqual(len(process_data["cluster_time_ranges"]), 1)
        conn.close()


if __name__ == "__main__":
    unittest.main()
