"""Tests for alert dispatch and channels."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from pipewatch.alerts import AlertDispatcher, EmailChannel, LogChannel
from pipewatch.metrics import Metric, MetricStatus


def _metric(status: MetricStatus, name: str = "test.metric", value: float = 1.0) -> Metric:
    return Metric(name=name, value=value, status=status, message="test")


def test_log_channel_ok_no_log(caplog):
    ch = LogChannel()
    m = _metric(MetricStatus.OK)
    result = ch.send(m)
    assert result is True


def test_log_channel_warning(caplog):
    ch = LogChannel()
    with caplog.at_level(logging.WARNING):
        ch.send(_metric(MetricStatus.WARNING))
    assert any("WARNING" in r.message or "warning" in r.message.lower() for r in caplog.records)


def test_log_channel_critical(caplog):
    ch = LogChannel()
    with caplog.at_level(logging.CRITICAL):
        ch.send(_metric(MetricStatus.CRITICAL))
    assert any(r.levelno == logging.CRITICAL for r in caplog.records)


def test_dispatcher_skips_ok():
    ch = MagicMock()
    d = AlertDispatcher(channels=[ch])
    d.dispatch(_metric(MetricStatus.OK))
    ch.send.assert_not_called()


def test_dispatcher_sends_warning():
    ch = MagicMock()
    ch.send.return_value = True
    d = AlertDispatcher(channels=[ch])
    count = d.dispatch(_metric(MetricStatus.WARNING))
    ch.send.assert_called_once()
    assert count == 1


def test_dispatcher_sends_critical():
    ch = MagicMock()
    ch.send.return_value = True
    d = AlertDispatcher(channels=[ch])
    count = d.dispatch(_metric(MetricStatus.CRITICAL))
    assert count == 1


def test_dispatcher_dispatch_all():
    ch = MagicMock()
    ch.send.return_value = True
    d = AlertDispatcher(channels=[ch])
    metrics = [
        _metric(MetricStatus.OK),
        _metric(MetricStatus.WARNING),
        _metric(MetricStatus.CRITICAL),
    ]
    total = d.dispatch_all(metrics)
    assert total == 2
    assert ch.send.call_count == 2


def test_dispatcher_multiple_channels():
    ch1, ch2 = MagicMock(return_value=True), MagicMock(return_value=True)
    ch1.send.return_value = True
    ch2.send.return_value = True
    d = AlertDispatcher(channels=[ch1, ch2])
    d.dispatch(_metric(MetricStatus.CRITICAL))
    ch1.send.assert_called_once()
    ch2.send.assert_called_once()
