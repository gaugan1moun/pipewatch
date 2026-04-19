"""Silence-aware alert dispatcher wrapper."""
from __future__ import annotations
from typing import List

from pipewatch.alerts import AlertDispatcher
from pipewatch.metrics import Metric, MetricStatus
from pipewatch.silencer import is_silenced


class SilencedDispatcher:
    """Wraps AlertDispatcher and skips metrics that are currently silenced."""

    def __init__(self, dispatcher: AlertDispatcher, silence_path: str) -> None:
        self.dispatcher = dispatcher
        self.silence_path = silence_path

    def dispatch(self, metrics: List[Metric]) -> None:
        filtered = [
            m for m in metrics
            if not is_silenced(self.silence_path, m.name)
        ]
        skipped = len(metrics) - len(filtered)
        if skipped:
            import logging
            logging.getLogger(__name__).info(
                "Suppressed alerts for %d silenced metric(s).", skipped
            )
        if filtered:
            self.dispatcher.dispatch(filtered)

    def dispatch_one(self, metric: Metric) -> None:
        if is_silenced(self.silence_path, metric.name):
            import logging
            logging.getLogger(__name__).info(
                "Alert suppressed for silenced metric '%s'.", metric.name
            )
            return
        self.dispatcher.dispatch([metric])
