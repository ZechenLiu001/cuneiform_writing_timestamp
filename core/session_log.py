from __future__ import annotations

from dataclasses import asdict

from core.models import ProcessResult


class InMemorySessionLog:
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def save(self, result: ProcessResult) -> None:
        self._store[result.session_id] = asdict(result)

    def get(self, session_id: str) -> dict | None:
        return self._store.get(session_id)
