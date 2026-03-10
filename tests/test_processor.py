from __future__ import annotations

import json
import unittest

from core.models import parse_session_input
from core.processor import process_session


class ProcessorTests(unittest.TestCase):
    def test_hard_delete_and_cluster_time_range(self) -> None:
        with open("examples/session_example.json", "r", encoding="utf-8") as f:
            payload = json.load(f)

        session = parse_session_input(payload)
        result = process_session(session)

        self.assertEqual(result.session_id, "sess_001")
        self.assertEqual(sorted(result.retained_stroke_ids), ["s_001", "s_002"])
        self.assertEqual(len(result.clusters), 1)
        self.assertEqual(result.clusters[0].member_stroke_ids, ["s_001", "s_002"])

        self.assertEqual(len(result.cluster_time_ranges), 1)
        tr = result.cluster_time_ranges[0]
        self.assertEqual(tr.time_start_offset_ms, 2500)
        self.assertEqual(tr.time_end_offset_ms, 5000)


if __name__ == "__main__":
    unittest.main()
