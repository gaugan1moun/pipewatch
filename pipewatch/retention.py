"""History retention policy: prune old entries from history."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List

from pipewatch.history import HistoryEntry, load_history, save_history


@dataclass
class RetentionPolicy:
    max_age_days: int = 30
    max_entries_per_metric: int = 500

    def is_expired(self, entry: HistoryEntry) -> bool:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=self.max_age_days)
        try:
            ts = datetime.fromisoformat(entry.timestamp)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return ts < cutoff
        except (ValueError, AttributeError):
            return False


def prune_history(
    path: str,
    policy: RetentionPolicy | None = None,
) -> int:
    """Remove expired / excess entries. Returns number of entries removed."""
    if policy is None:
        policy = RetentionPolicy()

    entries: List[HistoryEntry] = load_history(path)
    original_count = len(entries)

    # Remove expired
    entries = [e for e in entries if not policy.is_expired(e)]

    # Per-metric cap (keep most recent)
    from collections import defaultdict
    buckets: dict = defaultdict(list)
    for e in entries:
        buckets[e.metric_name].append(e)

    pruned: List[HistoryEntry] = []
    for name, group in buckets.items():
        group.sort(key=lambda e: e.timestamp)
        pruned.extend(group[-policy.max_entries_per_metric:])

    pruned.sort(key=lambda e: e.timestamp)
    save_history(path, pruned)
    return original_count - len(pruned)


def retention_summary(path: str, policy: RetentionPolicy | None = None) -> dict:
    if policy is None:
        policy = RetentionPolicy()
    entries = load_history(path)
    expired = sum(1 for e in entries if policy.is_expired(e))
    return {
        "total_entries": len(entries),
        "expired_entries": expired,
        "max_age_days": policy.max_age_days,
        "max_entries_per_metric": policy.max_entries_per_metric,
    }
