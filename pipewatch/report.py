"""Generate pipeline health reports combining current metrics and history trends."""

from typing import List, Optional
from dataclasses import dataclass

from pipewatch.metrics import Metric
from pipewatch.history import trend, get_metric_history, DEFAULT_HISTORY_PATH


@dataclass
class MetricReport:
    name: str
    value: float
    status: str
    trend: Optional[str]
    history_count: int


def build_report(
    metrics: List[Metric],
    history_path: str = DEFAULT_HISTORY_PATH,
    trend_window: int = 5,
) -> List[MetricReport]:
    reports = []
    for m in metrics:
        t = trend(m.name, last_n=trend_window, path=history_path)
        history = get_metric_history(m.name, path=history_path)
        reports.append(MetricReport(
            name=m.name,
            value=m.value,
            status=m.status.value,
            trend=t,
            history_count=len(history),
        ))
    return reports


def format_report(reports: List[MetricReport]) -> str:
    lines = [f"{'Metric':<25} {'Value':>10} {'Status':<10} {'Trend':<8} {'History':>8}"]
    lines.append("-" * 65)
    trend_icons = {"up": "↑", "down": "↓", "stable": "→", None: "N/A"}
    for r in reports:
        icon = trend_icons.get(r.trend, "N/A")
        lines.append(
            f"{r.name:<25} {r.value:>10.4f} {r.status:<10} {icon:<8} {r.history_count:>8}"
        )
    return "\n".join(lines)
