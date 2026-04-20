"""Metric comparison across snapshots: diff two snapshots and report changes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics import MetricStatus
from pipewatch.snapshot import Snapshot


@dataclass
class MetricDiff:
    name: str
    old_status: Optional[MetricStatus]
    new_status: Optional[MetricStatus]
    old_value: Optional[float]
    new_value: Optional[float]

    @property
    def changed(self) -> bool:
        return self.old_status != self.new_status

    @property
    def direction(self) -> str:
        """Return 'improved', 'degraded', 'unchanged', or 'new'/'removed'."""
        if self.old_status is None:
            return "new"
        if self.new_status is None:
            return "removed"
        order = [MetricStatus.OK, MetricStatus.WARNING, MetricStatus.CRITICAL]
        try:
            old_idx = order.index(self.old_status)
            new_idx = order.index(self.new_status)
        except ValueError:
            return "unchanged"
        if new_idx > old_idx:
            return "degraded"
        if new_idx < old_idx:
            return "improved"
        return "unchanged"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "old_status": self.old_status.value if self.old_status else None,
            "new_status": self.new_status.value if self.new_status else None,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed": self.changed,
            "direction": self.direction,
        }


@dataclass
class SnapshotComparison:
    old_timestamp: str
    new_timestamp: str
    diffs: List[MetricDiff] = field(default_factory=list)

    @property
    def changed_metrics(self) -> List[MetricDiff]:
        return [d for d in self.diffs if d.changed]

    def to_dict(self) -> dict:
        return {
            "old_timestamp": self.old_timestamp,
            "new_timestamp": self.new_timestamp,
            "total": len(self.diffs),
            "changed": len(self.changed_metrics),
            "diffs": [d.to_dict() for d in self.diffs],
        }


def compare_snapshots(old: Snapshot, new: Snapshot) -> SnapshotComparison:
    """Diff two snapshots and return a SnapshotComparison."""
    old_map: Dict[str, dict] = {e["name"]: e for e in old.entries}
    new_map: Dict[str, dict] = {e["name"]: e for e in new.entries}
    all_names = sorted(set(old_map) | set(new_map))

    diffs: List[MetricDiff] = []
    for name in all_names:
        old_entry = old_map.get(name)
        new_entry = new_map.get(name)
        diffs.append(
            MetricDiff(
                name=name,
                old_status=MetricStatus(old_entry["status"]) if old_entry else None,
                new_status=MetricStatus(new_entry["status"]) if new_entry else None,
                old_value=old_entry.get("value") if old_entry else None,
                new_value=new_entry.get("value") if new_entry else None,
            )
        )
    return SnapshotComparison(
        old_timestamp=old.timestamp,
        new_timestamp=new.timestamp,
        diffs=diffs,
    )
