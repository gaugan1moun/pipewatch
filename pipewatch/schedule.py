"""Scheduled pipeline check runner for pipewatch."""

import time
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class ScheduleConfig:
    def __init__(self, interval_seconds: int = 60, max_runs: Optional[int] = None):
        self.interval_seconds = interval_seconds
        self.max_runs = max_runs


class ScheduledRunner:
    """Runs a check function on a fixed interval."""

    def __init__(self, check_fn: Callable, config: ScheduleConfig):
        self.check_fn = check_fn
        self.config = config
        self._run_count = 0
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        logger.info(
            "Starting scheduled runner (interval=%ds, max_runs=%s)",
            self.config.interval_seconds,
            self.config.max_runs,
        )
        while not self._stop:
            try:
                self.check_fn()
            except Exception as exc:  # noqa: BLE001
                logger.error("Scheduled check failed: %s", exc)

            self._run_count += 1
            if self.config.max_runs is not None and self._run_count >= self.config.max_runs:
                logger.info("Reached max_runs=%d, stopping.", self.config.max_runs)
                break

            time.sleep(self.config.interval_seconds)

        logger.info("Scheduled runner stopped after %d run(s).", self._run_count)

    @property
    def run_count(self) -> int:
        return self._run_count
