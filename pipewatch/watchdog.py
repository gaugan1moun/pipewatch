"""Watchdog module: detects stale metrics that haven't been updated within a TTL window."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from pipewatch.snapshot import Snapshot


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class StalenessResult:
    metric_name: str
    last_seen: Optional[str]  # ISO timestamp or None
    age_seconds: Optional[float]
    is_stale: bool
    ttl_seconds: float

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "last_seen": self.last_seen,
            "age_seconds": self.age_seconds,
            "is_stale": self.is_stale,
            "ttl_seconds": self.ttl_seconds,
        }


@dataclass
class WatchdogReport:
    checked_at: str
    ttl_seconds: float
    results: List[StalenessResult] = field(default_factory=list)

    @property
    def stale_metrics(self) -> List[StalenessResult]:
        return [r for r in self.results if r.is_stale]

    def to_dict(self) -> dict:
        return {
            "checked_at": self.checked_at,
            "ttl_seconds": self.ttl_seconds,
            "results": [r.to_dict() for r in self.results],
            "stale_count": len(self.stale_metrics),
        }


def check_staleness(snapshot: Snapshot, ttl_seconds: float = 300.0) -> WatchdogReport:
    """Check each metric in a snapshot for staleness against a TTL."""
    now = _now()
    report = WatchdogReport(
        checked_at=now.isoformat(),
        ttl_seconds=ttl_seconds,
    )

    snap_ts: Optional[datetime] = None
    try:
        snap_ts = datetime.fromisoformat(snapshot.timestamp)
        if snap_ts.tzinfo is None:
            snap_ts = snap_ts.replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        snap_ts = None

    for entry in snapshot.metrics:
        if snap_ts is None:
            result = StalenessResult(
                metric_name=entry.get("name", "unknown"),
                last_seen=None,
                age_seconds=None,
                is_stale=True,
                ttl_seconds=ttl_seconds,
            )
        else:
            age = (now - snap_ts).total_seconds()
            result = StalenessResult(
                metric_name=entry.get("name", "unknown"),
                last_seen=snapshot.timestamp,
                age_seconds=round(age, 2),
                is_stale=age > ttl_seconds,
                ttl_seconds=ttl_seconds,
            )
        report.results.append(result)

    return report


def watchdog_summary(report: WatchdogReport) -> str:
    lines = [f"Watchdog checked at {report.checked_at} (TTL={report.ttl_seconds}s)"]
    for r in report.results:
        status = "STALE" if r.is_stale else "OK"
        age_str = f"{r.age_seconds}s" if r.age_seconds is not None else "unknown"
        lines.append(f"  [{status}] {r.metric_name} — age: {age_str}")
    stale = len(report.stale_metrics)
    lines.append(f"Summary: {stale}/{len(report.results)} metrics stale.")
    return "\n".join(lines)
