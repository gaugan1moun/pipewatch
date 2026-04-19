"""Metric history storage and trend analysis."""

import json
import os
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, asdict

from pipewatch.metrics import Metric

DEFAULT_HISTORY_PATH = ".pipewatch_history.json"


@dataclass
class HistoryEntry:
    name: str
    value: float
    status: str
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


def _now() -> str:
    return datetime.utcnow().isoformat()


def load_history(path: str = DEFAULT_HISTORY_PATH) -> List[HistoryEntry]:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        raw = json.load(f)
    return [HistoryEntry(**entry) for entry in raw]


def save_history(entries: List[HistoryEntry], path: str = DEFAULT_HISTORY_PATH) -> None:
    with open(path, "w") as f:
        json.dump([e.to_dict() for e in entries], f, indent=2)


def record_metrics(metrics: List[Metric], path: str = DEFAULT_HISTORY_PATH) -> None:
    entries = load_history(path)
    ts = _now()
    for m in metrics:
        entries.append(HistoryEntry(
            name=m.name,
            value=m.value,
            status=m.status.value,
            timestamp=ts,
        ))
    save_history(entries, path)


def get_metric_history(name: str, path: str = DEFAULT_HISTORY_PATH) -> List[HistoryEntry]:
    return [e for e in load_history(path) if e.name == name]


def trend(name: str, last_n: int = 5, path: str = DEFAULT_HISTORY_PATH) -> Optional[str]:
    """Return 'up', 'down', 'stable', or None if insufficient data."""
    entries = get_metric_history(name, path)[-last_n:]
    if len(entries) < 2:
        return None
    values = [e.value for e in entries]
    if values[-1] > values[0]:
        return "up"
    elif values[-1] < values[0]:
        return "down"
    return "stable"
