"""Throttle: limit how frequently alerts fire for a given metric."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

DEFAULT_THROTTLE_PATH = ".pipewatch/throttle_state.json"


@dataclass
class ThrottleEntry:
    metric_name: str
    last_fired: float  # unix timestamp
    cooldown_seconds: int

    def is_throttled(self, now: Optional[float] = None) -> bool:
        """Return True if the metric is still within its cooldown window."""
        now = now if now is not None else time.time()
        return (now - self.last_fired) < self.cooldown_seconds

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "last_fired": self.last_fired,
            "cooldown_seconds": self.cooldown_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ThrottleEntry":
        return cls(
            metric_name=data["metric_name"],
            last_fired=float(data["last_fired"]),
            cooldown_seconds=int(data["cooldown_seconds"]),
        )


def load_throttle_state(path: str = DEFAULT_THROTTLE_PATH) -> Dict[str, ThrottleEntry]:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open() as f:
        raw = json.load(f)
    return {k: ThrottleEntry.from_dict(v) for k, v in raw.items()}


def save_throttle_state(
    state: Dict[str, ThrottleEntry], path: str = DEFAULT_THROTTLE_PATH
) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        json.dump({k: v.to_dict() for k, v in state.items()}, f, indent=2)


def check_throttle(
    metric_name: str,
    cooldown_seconds: int,
    state: Dict[str, ThrottleEntry],
    now: Optional[float] = None,
) -> bool:
    """Return True if the alert should be suppressed (throttled).

    Side-effect: updates *state* in-place when the alert is allowed through.
    """
    now = now if now is not None else time.time()
    entry = state.get(metric_name)
    if entry is not None and entry.is_throttled(now):
        return True  # suppress
    # Allow and record firing time
    state[metric_name] = ThrottleEntry(
        metric_name=metric_name,
        last_fired=now,
        cooldown_seconds=cooldown_seconds,
    )
    return False
