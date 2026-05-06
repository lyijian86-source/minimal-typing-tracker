from __future__ import annotations

from datetime import datetime, timedelta

from type_record.config import AppConfig
from type_record.counter import KeyboardCounter


class FakeStore:
    def __init__(self) -> None:
        self.sessions: list[dict] = []
        self.keys: list[dict] = []

    def record_session(self, **snapshot) -> None:
        self.sessions.append(snapshot)

    def record_key(self, **payload) -> int:
        self.keys.append(payload)
        return 0


def test_expired_session_is_saved_during_live_refresh() -> None:
    store = FakeStore()
    config = AppConfig(session_timeout_seconds=60)
    counter = KeyboardCounter(config=config, store=store)
    now = datetime(2026, 4, 23, 9, 0, 0)
    counter._now = lambda: now

    counter._record_input(delta=1, positive_count=1, pasted_count=0, backspace_count=0, count_for_speed=True)
    now = now + timedelta(seconds=20)
    counter._record_input(delta=1, positive_count=1, pasted_count=0, backspace_count=0, count_for_speed=True)

    now = now + timedelta(seconds=61)
    stats = counter.get_live_stats()
    counter.get_live_stats()

    assert stats["session_is_active"] is False
    assert stats["session_positive_count"] == 0
    assert len(store.sessions) == 1
    assert store.sessions[0]["started_at"] == datetime(2026, 4, 23, 9, 0, 0)
    assert store.sessions[0]["ended_at"] == datetime(2026, 4, 23, 9, 0, 20)
    assert store.sessions[0]["positive_count"] == 2
    assert store.sessions[0]["delta"] == 2
