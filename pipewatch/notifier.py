"""Rate-limited notification deduplication for pipewatch alerts."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

DEFAULT_COOLDOWN = 300  # seconds


@dataclass
class NotifierState:
    last_notified: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"last_notified": self.last_notified}

    @staticmethod
    def from_dict(data: dict) -> "NotifierState":
        return NotifierState(last_notified=data.get("last_notified", {}))


def load_state(path: Path) -> NotifierState:
    if not path.exists():
        return NotifierState()
    try:
        data = json.loads(path.read_text())
        return NotifierState.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return NotifierState()


def save_state(state: NotifierState, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2))


def should_notify(metric_name: str, state: NotifierState, cooldown: int = DEFAULT_COOLDOWN) -> bool:
    last = state.last_notified.get(metric_name)
    if last is None:
        return True
    return (time.time() - last) >= cooldown


def mark_notified(metric_name: str, state: NotifierState, ts: Optional[float] = None) -> None:
    state.last_notified[metric_name] = ts if ts is not None else time.time()


def purge_expired(state: NotifierState, cooldown: int = DEFAULT_COOLDOWN) -> int:
    now = time.time()
    expired = [k for k, v in state.last_notified.items() if (now - v) >= cooldown]
    for k in expired:
        del state.last_notified[k]
    return len(expired)
