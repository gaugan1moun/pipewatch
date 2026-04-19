"""Output formatters for metric results."""

from __future__ import annotations

import json
from typing import List

from pipewatch.metrics import Metric, MetricStatus

_STATUS_COLORS = {
    MetricStatus.OK: "\033[32m",       # green
    MetricStatus.WARNING: "\033[33m",  # yellow
    MetricStatus.CRITICAL: "\033[31m", # red
}
_RESET = "\033[0m"


def format_table(metrics: List[Metric], color: bool = True) -> str:
    """Render metrics as a human-readable table."""
    header = f"{'NAME':<30} {'STATUS':<10} {'VALUE':<12} MESSAGE"
    sep = "-" * 70
    rows = [header, sep]
    for m in metrics:
        color_code = _STATUS_COLORS.get(m.status, "") if color else ""
        reset = _RESET if color else ""
        rows.append(
            f"{m.name:<30} "
            f"{color_code}{m.status.value:<10}{reset} "
            f"{str(m.value):<12} "
            f"{m.message or ''}"
        )
    return "\n".join(rows)


def format_json(metrics: List[Metric]) -> str:
    """Render metrics as a JSON array."""
    from pipewatch.metrics import to_dict
    return json.dumps([to_dict(m) for m in metrics], indent=2, default=str)


def format_summary(metrics: List[Metric]) -> str:
    """One-line summary: counts per status."""
    counts: dict = {s: 0 for s in MetricStatus}
    for m in metrics:
        counts[m.status] += 1
    parts = [f"{s.value}={counts[s]}" for s in MetricStatus]
    overall = (
        MetricStatus.CRITICAL if counts[MetricStatus.CRITICAL]
        else MetricStatus.WARNING if counts[MetricStatus.WARNING]
        else MetricStatus.OK
    )
    color = _STATUS_COLORS[overall]
    return f"{color}[{overall.value.upper()}]{_RESET} " + "  ".join(parts)
