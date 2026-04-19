"""Baseline management: store and compare metric values against a known-good baseline."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Optional

DEFAULT_BASELINE_PATH = ".pipewatch_baseline.json"


@dataclass
class BaselineEntry:
    metric_name: str
    value: float
    recorded_at: str

    def to_dict(self) -> dict:
        return asdict(self)


def load_baseline(path: str = DEFAULT_BASELINE_PATH) -> Dict[str, BaselineEntry]:
    """Load baseline entries from a JSON file."""
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        raw = json.load(f)
    return {
        name: BaselineEntry(**entry)
        for name, entry in raw.items()
    }


def save_baseline(
    entries: Dict[str, BaselineEntry],
    path: str = DEFAULT_BASELINE_PATH,
) -> None:
    """Persist baseline entries to a JSON file."""
    with open(path, "w") as f:
        json.dump({name: e.to_dict() for name, e in entries.items()}, f, indent=2)


def record_baseline(
    metrics: list,
    path: str = DEFAULT_BASELINE_PATH,
    recorded_at: Optional[str] = None,
) -> Dict[str, BaselineEntry]:
    """Record current metric values as the new baseline."""
    from datetime import datetime, timezone

    ts = recorded_at or datetime.now(timezone.utc).isoformat()
    entries = {
        m.name: BaselineEntry(metric_name=m.name, value=m.value, recorded_at=ts)
        for m in metrics
    }
    save_baseline(entries, path)
    return entries


def compare_to_baseline(
    metrics: list,
    path: str = DEFAULT_BASELINE_PATH,
) -> Dict[str, dict]:
    """Compare current metric values against the stored baseline.

    Returns a dict mapping metric name to a comparison result with keys:
      baseline, current, delta, pct_change.
    """
    baseline = load_baseline(path)
    results = {}
    for m in metrics:
        if m.name not in baseline:
            continue
        base_val = baseline[m.name].value
        delta = m.value - base_val
        pct = (delta / base_val * 100) if base_val != 0 else None
        results[m.name] = {
            "baseline": base_val,
            "current": m.value,
            "delta": delta,
            "pct_change": round(pct, 2) if pct is not None else None,
        }
    return results
