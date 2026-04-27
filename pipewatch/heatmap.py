"""Heatmap: summarise metric status frequency across time buckets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.history import HistoryEntry
from pipewatch.metrics import MetricStatus


@dataclass
class HeatmapCell:
    bucket: str
    metric_name: str
    ok: int = 0
    warning: int = 0
    critical: int = 0

    @property
    def dominant(self) -> str:
        """Return the status with the highest count."""
        counts = {
            "ok": self.ok,
            "warning": self.warning,
            "critical": self.critical,
        }
        return max(counts, key=lambda k: counts[k])

    def to_dict(self) -> dict:
        return {
            "bucket": self.bucket,
            "metric": self.metric_name,
            "ok": self.ok,
            "warning": self.warning,
            "critical": self.critical,
            "dominant": self.dominant,
        }


def _bucket_label(ts: str, granularity: str) -> str:
    """Truncate an ISO timestamp to the requested granularity."""
    if granularity == "hour":
        return ts[:13]  # YYYY-MM-DDTHH
    return ts[:10]      # YYYY-MM-DD  (default: day)


def build_heatmap(
    entries: List[HistoryEntry],
    granularity: str = "day",
    metric_name: Optional[str] = None,
) -> List[HeatmapCell]:
    """Aggregate history entries into heatmap cells."""
    cells: Dict[tuple, HeatmapCell] = {}

    for entry in entries:
        if metric_name and entry.metric_name != metric_name:
            continue
        bucket = _bucket_label(entry.timestamp, granularity)
        key = (bucket, entry.metric_name)
        if key not in cells:
            cells[key] = HeatmapCell(bucket=bucket, metric_name=entry.metric_name)
        cell = cells[key]
        status = entry.status.lower() if isinstance(entry.status, str) else entry.status.value.lower()
        if status == MetricStatus.OK.value.lower():
            cell.ok += 1
        elif status == MetricStatus.WARNING.value.lower():
            cell.warning += 1
        elif status == MetricStatus.CRITICAL.value.lower():
            cell.critical += 1

    return sorted(cells.values(), key=lambda c: (c.bucket, c.metric_name))


def heatmap_summary(cells: List[HeatmapCell]) -> str:
    """Return a plain-text heatmap table."""
    if not cells:
        return "No heatmap data available."
    lines = [f"{'Bucket':<20} {'Metric':<25} {'OK':>5} {'WARN':>6} {'CRIT':>6} {'Dominant':<10}"]
    lines.append("-" * 80)
    for c in cells:
        lines.append(
            f"{c.bucket:<20} {c.metric_name:<25} {c.ok:>5} {c.warning:>6} {c.critical:>6} {c.dominant:<10}"
        )
    return "\n".join(lines)
