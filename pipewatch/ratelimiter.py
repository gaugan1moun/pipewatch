"""Rate limiting for alert dispatch — prevents alert storms."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

DEFAULT_STATE_PATH = Path(".pipewatch_ratelimit.json")


@dataclass
class RateLimitEntry:
    metric_name: str
    channel: str
    window_seconds: int
    max_alerts: int
    timestamps: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "channel": self.channel,
            "window_seconds": self.window_seconds,
            "max_alerts": self.max_alerts,
            "timestamps": self.timestamps,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RateLimitEntry":
        return cls(
            metric_name=d["metric_name"],
            channel=d["channel"],
            window_seconds=d["window_seconds"],
            max_alerts=d["max_alerts"],
            timestamps=d.get("timestamps", []),
        )

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        self.timestamps = [t for t in self.timestamps if t >= cutoff]

    def is_allowed(self, now: Optional[float] = None) -> bool:
        now = now or time.time()
        self._prune(now)
        return len(self.timestamps) < self.max_alerts

    def record(self, now: Optional[float] = None) -> None:
        now = now or time.time()
        self._prune(now)
        self.timestamps.append(now)


def load_rate_limit_state(path: Path = DEFAULT_STATE_PATH) -> Dict[str, RateLimitEntry]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return {k: RateLimitEntry.from_dict(v) for k, v in data.items()}


def save_rate_limit_state(
    state: Dict[str, RateLimitEntry], path: Path = DEFAULT_STATE_PATH
) -> None:
    path.write_text(json.dumps({k: v.to_dict() for k, v in state.items()}, indent=2))


def _key(metric_name: str, channel: str) -> str:
    return f"{metric_name}::{channel}"


def check_rate_limit(
    state: Dict[str, RateLimitEntry],
    metric_name: str,
    channel: str,
    window_seconds: int = 300,
    max_alerts: int = 3,
    now: Optional[float] = None,
) -> bool:
    """Return True if the alert is allowed (not rate-limited)."""
    k = _key(metric_name, channel)
    if k not in state:
        state[k] = RateLimitEntry(metric_name, channel, window_seconds, max_alerts)
    entry = state[k]
    entry.window_seconds = window_seconds
    entry.max_alerts = max_alerts
    if entry.is_allowed(now):
        entry.record(now)
        return True
    return False
