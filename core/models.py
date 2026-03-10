from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Point:
    point_id: str
    stroke_id: str
    x: float
    y: float
    ts_ms: int


@dataclass
class Stroke:
    stroke_id: str
    page_id: str
    canvas_id: str
    points: list[Point]
    start_ts_ms: int
    end_ts_ms: int
    bbox: dict[str, float]


@dataclass
class EraseEvent:
    erase_id: str
    page_id: str
    ts_ms: int
    affected_stroke_ids: list[str]


@dataclass
class TranscriptSegment:
    transcript_seg_id: str
    start_ts_ms: int
    end_ts_ms: int
    start_offset_ms: int
    end_offset_ms: int
    text: str = ""


@dataclass
class SessionInput:
    session_id: str
    submit_ts_ms: int
    strokes: list[Stroke] = field(default_factory=list)
    erase_events: list[EraseEvent] = field(default_factory=list)
    transcript_segments: list[TranscriptSegment] = field(default_factory=list)


@dataclass
class ClusterResult:
    cluster_id: str
    page_id: str
    canvas_id: str
    member_stroke_ids: list[str]
    bbox: dict[str, float]
    start_ts_ms: int
    end_ts_ms: int


@dataclass
class ClusterTimeRange:
    cluster_id: str
    time_start_offset_ms: int
    time_end_offset_ms: int
    source_transcript_seg_ids: list[str]


@dataclass
class ProcessResult:
    session_id: str
    retained_stroke_ids: list[str]
    clusters: list[ClusterResult]
    cluster_time_ranges: list[ClusterTimeRange]


def parse_session_input(payload: dict[str, Any]) -> SessionInput:
    strokes: list[Stroke] = []
    for s in payload.get("strokes", []):
        points = [
            Point(
                point_id=p["point_id"],
                stroke_id=p["stroke_id"],
                x=float(p["x"]),
                y=float(p["y"]),
                ts_ms=int(p["ts_ms"]),
            )
            for p in s.get("points", [])
        ]
        strokes.append(
            Stroke(
                stroke_id=s["stroke_id"],
                page_id=s["page_id"],
                canvas_id=s.get("canvas_id", "canvas_A"),
                points=points,
                start_ts_ms=int(s["start_ts_ms"]),
                end_ts_ms=int(s["end_ts_ms"]),
                bbox={k: float(v) for k, v in s["bbox"].items()},
            )
        )

    erase_events = [
        EraseEvent(
            erase_id=e["erase_id"],
            page_id=e["page_id"],
            ts_ms=int(e["ts_ms"]),
            affected_stroke_ids=list(e.get("affected_stroke_ids", [])),
        )
        for e in payload.get("erase_events", [])
    ]

    transcript_segments = [
        TranscriptSegment(
            transcript_seg_id=t["transcript_seg_id"],
            start_ts_ms=int(t["start_ts_ms"]),
            end_ts_ms=int(t["end_ts_ms"]),
            start_offset_ms=int(t.get("start_offset_ms", 0)),
            end_offset_ms=int(t.get("end_offset_ms", 0)),
            text=t.get("text", ""),
        )
        for t in payload.get("transcript_segments", [])
    ]

    return SessionInput(
        session_id=payload["session_id"],
        submit_ts_ms=int(payload["submit_ts_ms"]),
        strokes=strokes,
        erase_events=erase_events,
        transcript_segments=transcript_segments,
    )
