"""Tests for pipewatch.schedule."""

import pytest
from unittest.mock import MagicMock, call
from pipewatch.schedule import ScheduleConfig, ScheduledRunner


@pytest.fixture()
def fast_config():
    return ScheduleConfig(interval_seconds=0, max_runs=3)


def test_runs_expected_number_of_times(fast_config):
    fn = MagicMock()
    runner = ScheduledRunner(check_fn=fn, config=fast_config)
    runner.run()
    assert fn.call_count == 3
    assert runner.run_count == 3


def test_stops_after_max_runs(fast_config):
    runner = ScheduledRunner(check_fn=MagicMock(), config=fast_config)
    runner.run()
    assert runner.run_count == fast_config.max_runs


def test_stop_flag_halts_runner():
    call_log = []

    def fn():
        call_log.append(1)
        runner.stop()

    config = ScheduleConfig(interval_seconds=0, max_runs=10)
    runner = ScheduledRunner(check_fn=fn, config=config)
    runner.run()
    assert len(call_log) == 1


def test_exception_in_check_does_not_crash(fast_config):
    fn = MagicMock(side_effect=RuntimeError("boom"))
    runner = ScheduledRunner(check_fn=fn, config=fast_config)
    runner.run()  # should not raise
    assert runner.run_count == 3


def test_unlimited_runs_respects_stop():
    config = ScheduleConfig(interval_seconds=0, max_runs=None)
    counter = {"n": 0}

    def fn():
        counter["n"] += 1
        if counter["n"] >= 5:
            runner.stop()

    runner = ScheduledRunner(check_fn=fn, config=config)
    runner.run()
    assert runner.run_count == 5


def test_run_count_starts_at_zero():
    config = ScheduleConfig(interval_seconds=0, max_runs=0)
    runner = ScheduledRunner(check_fn=MagicMock(), config=config)
    assert runner.run_count == 0
