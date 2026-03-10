from __future__ import annotations

import unittest

from core.asr import ASRError, ASRConfig, ensure_transcript_segments


class ASRTests(unittest.TestCase):
    def test_use_existing_transcript_segments(self) -> None:
        payload = {
            "session_id": "sess_1",
            "submit_ts_ms": 1000,
            "strokes": [],
            "transcript_segments": [
                {
                    "transcript_seg_id": "t1",
                    "start_ts_ms": 100,
                    "end_ts_ms": 200,
                    "start_offset_ms": 100,
                    "end_offset_ms": 200,
                    "text": "ok",
                }
            ],
        }
        out = ensure_transcript_segments(payload, ASRConfig(provider="mock"))
        self.assertEqual(out["transcript_segments"][0]["transcript_seg_id"], "t1")

    def test_mock_asr_enrichment(self) -> None:
        payload = {
            "session_id": "sess_1",
            "submit_ts_ms": 1000,
            "strokes": [],
            "asr_input": {
                "mock_segments": [
                    {
                        "start_ts_ms": 100,
                        "end_ts_ms": 300,
                        "start_offset_ms": 100,
                        "end_offset_ms": 300,
                        "text": "mock text",
                    }
                ]
            },
        }
        out = ensure_transcript_segments(payload, ASRConfig(provider="mock"))
        self.assertEqual(len(out["transcript_segments"]), 1)
        self.assertEqual(out["transcript_segments"][0]["text"], "mock text")

    def test_missing_input_raises(self) -> None:
        payload = {"session_id": "sess_1", "submit_ts_ms": 1000, "strokes": []}
        with self.assertRaises(ASRError):
            ensure_transcript_segments(payload, ASRConfig(provider="mock"))


if __name__ == "__main__":
    unittest.main()
