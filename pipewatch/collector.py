"""Metric collector that evaluates pipeline metrics against thresholds."""

from typing import Callable, Dict, List

from pipewatch.metrics import Metric, MetricStatus, ThresholdConfig


class MetricCollector:
    def __init__(self):
        self._sources: Dict[str, Callable[[], float]] = {}
        self._thresholds: Dict[str, ThresholdConfig] = {}

    def register(self, name: str, source: Callable[[], float], threshold: ThresholdConfig = None):
        """Register a metric source function with an optional threshold."""
        self._sources[name] = source
        if threshold:
            self._thresholds[name] = threshold

    def collect(self) -> List[Metric]:
        """Collect all registered metrics and evaluate their statuses."""
        results = []
        for name, source in self._sources.items():
            try:
                value = source()
                metric = Metric(name=name, value=value)
                threshold = self._thresholds.get(name)
                if threshold:
                    metric.status = threshold.evaluate(value)
                else:
                    metric.status = MetricStatus.OK
            except Exception as exc:
                metric = Metric(name=name, value=float("nan"), status=MetricStatus.UNKNOWN)
                metric.labels["error"] = str(exc)
            results.append(metric)
        return results

    def collect_one(self, name: str) -> Metric:
        """Collect a single named metric."""
        if name not in self._sources:
            raise KeyError(f"No metric registered with name '{name}'")
        metrics = {m.name: m for m in self.collect()}
        return metrics[name]
