"""Snapshot: capture and compare pipeline metric states over time."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from pipewatch.metrics import Metric, MetricStatus

DEFAULT_SNAPSHOT_PATH = ".pipewatch_snapshots.json"


@dataclass
class Snapshot:
    timestamp: str
    metrics: Dict[str, str]  # name -> status value

    def to_dict(self) -> dict:
        return {"timestamp": self.timestamp, "metrics": self.metrics}

    @staticmethod
    def from_dict(d: dict) -> "Snapshot":
        return Snapshot(timestamp=d["timestamp"], metrics=d["metrics"])


def _now() -> str:
    return datetime.utcnow().isoformat()


def capture_snapshot(metrics: List[Metric]) -> Snapshot:
    """Build a Snapshot from a list of evaluated Metric objects."""
    return Snapshot(
        timestamp=_now(),
        metrics={m.name: m.status.value for m in metrics},
    )


def save_snapshot(snapshot: Snapshot, path: str = DEFAULT_SNAPSHOT_PATH) -> None:
    existing: List[dict] = []
    if os.path.exists(path):
        with open(path, "r") as f:
            existing = json.load(f)
    existing.append(snapshot.to_dict())
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)


def load_snapshots(path: str = DEFAULT_SNAPSHOT_PATH) -> List[Snapshot]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return [Snapshot.from_dict(d) for d in json.load(f)]


def diff_snapshots(previous: Snapshot, current: Snapshot) -> Dict[str, dict]:
    """Return metrics whose status changed between two snapshots."""
    changes: Dict[str, dict] = {}
    all_keys = set(previous.metrics) | set(current.metrics)
    for key in all_keys:
        prev_status = previous.metrics.get(key)
        curr_status = current.metrics.get(key)
        if prev_status != curr_status:
            changes[key] = {"previous": prev_status, "current": curr_status}
    return changes
