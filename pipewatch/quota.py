"""Metric quota enforcement — limits how many critical/warning events
are allowed within a rolling time window before a quota breach is raised."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

DEFAULT_QUOTA_PATH = ".pipewatch/quota_state.json"


@dataclass
class QuotaRule:
    metric_name: str
    max_violations: int  # max allowed violations in the window
    window_seconds: int  # rolling window size
    status_filter: List[str] = field(default_factory=lambda: ["warning", "critical"])


@dataclass
class QuotaState:
    metric_name: str
    violation_timestamps: List[str] = field(default_factory=list)

    def prune(self, window_seconds: int) -> None:
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        self.violation_timestamps = [
            ts for ts in self.violation_timestamps
            if datetime.fromisoformat(ts) >= cutoff
        ]

    def record(self, ts: Optional[str] = None) -> None:
        self.violation_timestamps.append(ts or datetime.utcnow().isoformat())

    def count(self) -> int:
        return len(self.violation_timestamps)

    def to_dict(self) -> dict:
        return {"metric_name": self.metric_name, "violation_timestamps": self.violation_timestamps}

    @classmethod
    def from_dict(cls, d: dict) -> "QuotaState":
        return cls(metric_name=d["metric_name"], violation_timestamps=d.get("violation_timestamps", []))


def load_quota_state(path: str = DEFAULT_QUOTA_PATH) -> dict[str, QuotaState]:
    p = Path(path)
    if not p.exists():
        return {}
    data = json.loads(p.read_text())
    return {k: QuotaState.from_dict(v) for k, v in data.items()}


def save_quota_state(state: dict[str, QuotaState], path: str = DEFAULT_QUOTA_PATH) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({k: v.to_dict() for k, v in state.items()}, indent=2))


@dataclass
class QuotaResult:
    metric_name: str
    breached: bool
    violations_in_window: int
    max_violations: int
    window_seconds: int

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "breached": self.breached,
            "violations_in_window": self.violations_in_window,
            "max_violations": self.max_violations,
            "window_seconds": self.window_seconds,
        }


def check_quota(
    rule: QuotaRule,
    metric_status: str,
    state: dict[str, QuotaState],
) -> QuotaResult:
    """Record a violation if status matches filter, then evaluate the quota."""
    entry = state.setdefault(rule.metric_name, QuotaState(metric_name=rule.metric_name))
    entry.prune(rule.window_seconds)
    if metric_status in rule.status_filter:
        entry.record()
    count = entry.count()
    return QuotaResult(
        metric_name=rule.metric_name,
        breached=count > rule.max_violations,
        violations_in_window=count,
        max_violations=rule.max_violations,
        window_seconds=rule.window_seconds,
    )
