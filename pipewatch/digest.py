"""Periodic digest generation: summarize metric health over a time window."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pipewatch.history import HistoryEntry, load_history
from pipewatch.metrics import MetricStatus


@dataclass
class MetricDigest:
    name: str
    total: int
    ok: int
    warning: int
    critical: int
    worst: MetricStatus

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "total": self.total,
            "ok": self.ok,
            "warning": self.warning,
            "critical": self.critical,
            "worst": self.worst.value,
        }


@dataclass
class DigestReport:
    window_hours: int
    generated_at: str
    metrics: List[MetricDigest]

    def to_dict(self) -> dict:
        return {
            "window_hours": self.window_hours,
            "generated_at": self.generated_at,
            "metrics": [m.to_dict() for m in self.metrics],
        }


_STATUS_RANK = {MetricStatus.OK: 0, MetricStatus.WARNING: 1, MetricStatus.CRITICAL: 2}


def build_digest(history_path: str, window_hours: int = 24) -> DigestReport:
    entries: List[HistoryEntry] = load_history(history_path)
    cutoff = datetime.utcnow() - timedelta(hours=window_hours)

    grouped: Dict[str, List[HistoryEntry]] = {}
    for entry in entries:
        ts = datetime.fromisoformat(entry.timestamp)
        if ts >= cutoff:
            grouped.setdefault(entry.name, []).append(entry)

    digests: List[MetricDigest] = []
    for name, group in sorted(grouped.items()):
        counts = {MetricStatus.OK: 0, MetricStatus.WARNING: 0, MetricStatus.CRITICAL: 0}
        for e in group:
            counts[e.status] = counts.get(e.status, 0) + 1
        worst = max(counts, key=lambda s: _STATUS_RANK.get(s, 0))
        digests.append(
            MetricDigest(
                name=name,
                total=len(group),
                ok=counts[MetricStatus.OK],
                warning=counts[MetricStatus.WARNING],
                critical=counts[MetricStatus.CRITICAL],
                worst=worst,
            )
        )

    return DigestReport(
        window_hours=window_hours,
        generated_at=datetime.utcnow().isoformat(timespec="seconds"),
        metrics=digests,
    )
