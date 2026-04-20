"""Alert deduplication: suppress repeated alerts for the same metric/status."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

DEFAULT_DEDUP_PATH = Path(".pipewatch") / "dedup_state.json"


@dataclass
class DeduplicatorEntry:
    metric_name: str
    last_status: str
    alert_count: int = 0

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "last_status": self.last_status,
            "alert_count": self.alert_count,
        }

    @staticmethod
    def from_dict(d: dict) -> "DeduplicatorEntry":
        return DeduplicatorEntry(
            metric_name=d["metric_name"],
            last_status=d["last_status"],
            alert_count=d.get("alert_count", 0),
        )


def load_dedup_state(path: Path = DEFAULT_DEDUP_PATH) -> Dict[str, DeduplicatorEntry]:
    if not path.exists():
        return {}
    with open(path) as f:
        raw = json.load(f)
    return {k: DeduplicatorEntry.from_dict(v) for k, v in raw.items()}


def save_dedup_state(
    state: Dict[str, DeduplicatorEntry], path: Path = DEFAULT_DEDUP_PATH
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({k: v.to_dict() for k, v in state.items()}, f, indent=2)


def is_duplicate(metric_name: str, current_status: str, state: Dict[str, DeduplicatorEntry]) -> bool:
    """Return True if this metric already fired an alert for the same status."""
    entry = state.get(metric_name)
    if entry is None:
        return False
    return entry.last_status == current_status


def record_alert(
    metric_name: str,
    current_status: str,
    state: Dict[str, DeduplicatorEntry],
) -> DeduplicatorEntry:
    """Update state to reflect a new alert was fired for metric_name."""
    existing = state.get(metric_name)
    count = (existing.alert_count + 1) if existing and existing.last_status == current_status else 1
    entry = DeduplicatorEntry(
        metric_name=metric_name,
        last_status=current_status,
        alert_count=count,
    )
    state[metric_name] = entry
    return entry


def reset_metric(metric_name: str, state: Dict[str, DeduplicatorEntry]) -> None:
    """Remove dedup tracking for a metric (e.g. when status returns to OK)."""
    state.pop(metric_name, None)
