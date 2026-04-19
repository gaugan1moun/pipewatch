"""Trend analysis utilities for pipeline metrics."""
from typing import List, Optional
from enum import Enum
from pipewatch.history import HistoryEntry


class TrendDirection(str, Enum):
    IMPROVING = "improving"
    DEGRADING = "degrading"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


def compute_trend(entries: List[HistoryEntry], window: int = 5) -> TrendDirection:
    """Compute trend direction from the most recent `window` history entries."""
    if len(entries) < 2:
        return TrendDirection.INSUFFICIENT_DATA

    recent = entries[-window:]
    values = [e.value for e in recent]

    if len(values) < 2:
        return TrendDirection.INSUFFICIENT_DATA

    deltas = [values[i + 1] - values[i] for i in range(len(values) - 1)]
    avg_delta = sum(deltas) / len(deltas)

    if abs(avg_delta) < 1e-9:
        return TrendDirection.STABLE

    # Determine if higher values are better by checking status progression
    # Use simple heuristic: degrading means values are rising (e.g. error counts)
    # Users can invert interpretation via caller context
    if avg_delta > 0:
        return TrendDirection.DEGRADING
    return TrendDirection.IMPROVING


def trend_summary(metric_name: str, entries: List[HistoryEntry], window: int = 5) -> str:
    """Return a human-readable trend summary string."""
    direction = compute_trend(entries, window=window)
    if direction == TrendDirection.INSUFFICIENT_DATA:
        return f"{metric_name}: insufficient data for trend analysis"
    recent = entries[-window:]
    first_val = recent[0].value
    last_val = recent[-1].value
    return (
        f"{metric_name}: {direction.value} "
        f"({first_val:.4g} -> {last_val:.4g} over {len(recent)} samples)"
    )
