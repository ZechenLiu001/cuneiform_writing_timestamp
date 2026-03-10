from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ASRError(RuntimeError):
    """Raised when ASR enrichment cannot be completed."""


@dataclass
class ASRConfig:
    provider: str = "mock"
    qwen_endpoint: str | None = None
    timeout_s: float = 8.0

    @classmethod
    def from_env(cls) -> "ASRConfig":
        endpoint = os.getenv("QWEN_ASR_ENDPOINT")
        return cls(
            provider=os.getenv("ASR_PROVIDER", "mock").strip().lower(),
            qwen_endpoint=endpoint,
            timeout_s=float(os.getenv("ASR_TIMEOUT_S", "8.0")),
        )


def ensure_transcript_segments(payload: dict[str, Any], cfg: ASRConfig | None = None) -> dict[str, Any]:
    """Ensure payload has transcript_segments.

    Priority:
    1) Use provided transcript_segments if non-empty.
    2) Build via configured ASR provider using `asr_input`.
    """
    if payload.get("transcript_segments"):
        return payload

    config = cfg or ASRConfig.from_env()
    asr_input = payload.get("asr_input")
    if not asr_input:
        raise ASRError("transcript_segments missing and asr_input not provided")

    if config.provider == "mock":
        segments = _segments_from_mock(asr_input)
    elif config.provider == "qwen":
        segments = _segments_from_qwen(asr_input, config)
    else:
        raise ASRError(f"unsupported ASR provider: {config.provider}")

    payload = dict(payload)
    payload["transcript_segments"] = segments
    return payload


def _segments_from_mock(asr_input: dict[str, Any]) -> list[dict[str, Any]]:
    mock_segments = asr_input.get("mock_segments", [])
    if not mock_segments:
        raise ASRError("mock provider requires asr_input.mock_segments")

    out: list[dict[str, Any]] = []
    for idx, seg in enumerate(mock_segments, start=1):
        out.append(
            {
                "transcript_seg_id": seg.get("transcript_seg_id", f"t_mock_{idx:03d}"),
                "start_ts_ms": int(seg["start_ts_ms"]),
                "end_ts_ms": int(seg["end_ts_ms"]),
                "start_offset_ms": int(seg["start_offset_ms"]),
                "end_offset_ms": int(seg["end_offset_ms"]),
                "text": seg.get("text", ""),
            }
        )
    return out


def _segments_from_qwen(asr_input: dict[str, Any], cfg: ASRConfig) -> list[dict[str, Any]]:
    if not cfg.qwen_endpoint:
        raise ASRError("QWEN_ASR_ENDPOINT is not configured")

    req_payload = {
        "audio_url": asr_input.get("audio_url"),
        "session_id": asr_input.get("session_id"),
    }
    if not req_payload["audio_url"]:
        raise ASRError("qwen provider requires asr_input.audio_url")

    req = Request(
        cfg.qwen_endpoint,
        method="POST",
        data=json.dumps(req_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(req, timeout=cfg.timeout_s) as resp:  # noqa: S310 - endpoint is controlled by env config
            body = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise ASRError(f"qwen asr request failed: {exc}") from exc

    segments = body.get("segments", [])
    if not segments:
        raise ASRError("qwen asr returned empty segments")

    out: list[dict[str, Any]] = []
    for idx, seg in enumerate(segments, start=1):
        out.append(
            {
                "transcript_seg_id": seg.get("transcript_seg_id", f"t_qwen_{idx:03d}"),
                "start_ts_ms": int(seg["start_ts_ms"]),
                "end_ts_ms": int(seg["end_ts_ms"]),
                "start_offset_ms": int(seg["start_offset_ms"]),
                "end_offset_ms": int(seg["end_offset_ms"]),
                "text": seg.get("text", ""),
            }
        )
    return out
