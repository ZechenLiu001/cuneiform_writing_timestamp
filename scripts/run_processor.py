#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.models import parse_session_input
from core.processor import process_session
from core.session_log import InMemorySessionLog


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/run_processor.py <session_json>")
        return 1

    session_json = sys.argv[1]
    with open(session_json, "r", encoding="utf-8") as f:
        payload = json.load(f)

    session = parse_session_input(payload)
    result = process_session(session)

    log = InMemorySessionLog()
    log.save(result)

    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
