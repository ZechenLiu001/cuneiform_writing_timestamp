from __future__ import annotations

from collections import defaultdict
from math import sqrt

from core.models import ClusterResult, ClusterTimeRange, ProcessResult, SessionInput, Stroke


DEFAULT_CONFIG = {
    "cluster": {
        "d_bbox": 40.0,
        "t_merge_ms": 30000,
    },
    "match": {
        "pre_roll_ms": 3000,
        "post_roll_ms": 3000,
    },
}


def _bbox_distance(a: dict[str, float], b: dict[str, float]) -> float:
    ax1, ay1, ax2, ay2 = a["x"], a["y"], a["x"] + a["w"], a["y"] + a["h"]
    bx1, by1, bx2, by2 = b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]

    dx = max(bx1 - ax2, ax1 - bx2, 0)
    dy = max(by1 - ay2, ay1 - by2, 0)
    return sqrt(dx * dx + dy * dy)


def _merge_bbox(boxes: list[dict[str, float]]) -> dict[str, float]:
    min_x = min(b["x"] for b in boxes)
    min_y = min(b["y"] for b in boxes)
    max_x = max(b["x"] + b["w"] for b in boxes)
    max_y = max(b["y"] + b["h"] for b in boxes)
    return {"x": min_x, "y": min_y, "w": max_x - min_x, "h": max_y - min_y}


def retained_strokes(session: SessionInput) -> list[Stroke]:
    """Hard-delete erase policy: erased strokes are removed entirely."""
    erased: set[str] = set()
    for erase in session.erase_events:
        if erase.ts_ms <= session.submit_ts_ms:
            erased.update(erase.affected_stroke_ids)

    return [
        s
        for s in session.strokes
        if s.end_ts_ms <= session.submit_ts_ms and s.stroke_id not in erased
    ]


def cluster_strokes(strokes: list[Stroke], d_bbox: float, t_merge_ms: int) -> list[ClusterResult]:
    if not strokes:
        return []

    parent = {s.stroke_id: s.stroke_id for s in strokes}
    stroke_map = {s.stroke_id: s for s in strokes}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        pa, pb = find(a), find(b)
        if pa != pb:
            parent[pb] = pa

    for i in range(len(strokes)):
        for j in range(i + 1, len(strokes)):
            s1, s2 = strokes[i], strokes[j]
            if s1.page_id != s2.page_id or s1.canvas_id != s2.canvas_id:
                continue
            spatial_ok = _bbox_distance(s1.bbox, s2.bbox) <= d_bbox
            time_gap = max(s1.start_ts_ms, s2.start_ts_ms) - min(s1.end_ts_ms, s2.end_ts_ms)
            temporal_ok = time_gap <= t_merge_ms
            if spatial_ok and temporal_ok:
                union(s1.stroke_id, s2.stroke_id)

    groups: dict[str, list[Stroke]] = defaultdict(list)
    for s in strokes:
        groups[find(s.stroke_id)].append(s)

    clusters: list[ClusterResult] = []
    for idx, (_, members) in enumerate(groups.items(), start=1):
        members = sorted(members, key=lambda s: s.start_ts_ms)
        clusters.append(
            ClusterResult(
                cluster_id=f"c_{idx:03d}",
                page_id=members[0].page_id,
                canvas_id=members[0].canvas_id,
                member_stroke_ids=[m.stroke_id for m in members],
                bbox=_merge_bbox([m.bbox for m in members]),
                start_ts_ms=members[0].start_ts_ms,
                end_ts_ms=max(m.end_ts_ms for m in members),
            )
        )
    return clusters


def aggregate_cluster_time_ranges(session: SessionInput, clusters: list[ClusterResult], pre_roll_ms: int, post_roll_ms: int) -> list[ClusterTimeRange]:
    results: list[ClusterTimeRange] = []
    for cluster in clusters:
        candidates = [
            t
            for t in session.transcript_segments
            if t.end_ts_ms >= cluster.start_ts_ms - pre_roll_ms
            and t.start_ts_ms <= cluster.end_ts_ms + post_roll_ms
        ]
        if not candidates:
            continue
        results.append(
            ClusterTimeRange(
                cluster_id=cluster.cluster_id,
                time_start_offset_ms=min(t.start_offset_ms for t in candidates),
                time_end_offset_ms=max(t.end_offset_ms for t in candidates),
                source_transcript_seg_ids=[t.transcript_seg_id for t in candidates],
            )
        )
    return results


def process_session(session: SessionInput, config: dict | None = None) -> ProcessResult:
    cfg = config or DEFAULT_CONFIG
    kept = retained_strokes(session)
    clusters = cluster_strokes(
        kept,
        d_bbox=float(cfg["cluster"]["d_bbox"]),
        t_merge_ms=int(cfg["cluster"]["t_merge_ms"]),
    )
    time_ranges = aggregate_cluster_time_ranges(
        session,
        clusters,
        pre_roll_ms=int(cfg["match"]["pre_roll_ms"]),
        post_roll_ms=int(cfg["match"]["post_roll_ms"]),
    )

    return ProcessResult(
        session_id=session.session_id,
        retained_stroke_ids=[s.stroke_id for s in kept],
        clusters=clusters,
        cluster_time_ranges=time_ranges,
    )
