"""Metric sampler: collect multiple readings and produce statistical summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from pipewatch.metrics import Metric, MetricStatus


@dataclass
class SampleSummary:
    name: str
    samples: List[float]
    mean: float
    minimum: float
    maximum: float
    p50: float
    p95: float
    status: MetricStatus

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "samples": self.samples,
            "mean": self.mean,
            "min": self.minimum,
            "max": self.maximum,
            "p50": self.p50,
            "p95": self.p95,
            "status": self.status.value,
        }


def _percentile(sorted_data: List[float], pct: float) -> float:
    """Return the *pct* percentile (0-100) of a pre-sorted list."""
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * pct / 100.0
    lo, hi = int(k), min(int(k) + 1, len(sorted_data) - 1)
    frac = k - lo
    return sorted_data[lo] + frac * (sorted_data[hi] - sorted_data[lo])


class MetricSampler:
    """Collect *n* readings from a callable and summarise them."""

    def __init__(self, n: int = 5) -> None:
        if n < 1:
            raise ValueError("n must be >= 1")
        self.n = n
        self._collectors: Dict[str, Callable[[], Metric]] = {}

    def register(self, name: str, fn: Callable[[], Metric]) -> None:
        """Register a zero-argument callable that returns a Metric."""
        self._collectors[name] = fn

    def sample(self, name: str) -> SampleSummary:
        """Run the registered collector *n* times and return a summary."""
        if name not in self._collectors:
            raise KeyError(f"No collector registered for '{name}'")
        fn = self._collectors[name]
        readings: List[float] = []
        worst = MetricStatus.OK
        _order = [MetricStatus.OK, MetricStatus.WARNING, MetricStatus.CRITICAL]
        for _ in range(self.n):
            m = fn()
            readings.append(m.value)
            if _order.index(m.status) > _order.index(worst):
                worst = m.status
        sorted_r = sorted(readings)
        mean = sum(readings) / len(readings)
        return SampleSummary(
            name=name,
            samples=readings,
            mean=round(mean, 6),
            minimum=sorted_r[0],
            maximum=sorted_r[-1],
            p50=round(_percentile(sorted_r, 50), 6),
            p95=round(_percentile(sorted_r, 95), 6),
            status=worst,
        )

    def sample_all(self) -> Dict[str, SampleSummary]:
        """Sample every registered collector and return a name→summary map."""
        return {name: self.sample(name) for name in self._collectors}
