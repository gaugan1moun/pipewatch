"""Alert channels and notification dispatch for pipewatch."""

from __future__ import annotations

import smtplib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import List

from pipewatch.metrics import Metric, MetricStatus

logger = logging.getLogger(__name__)


class AlertChannel(ABC):
    @abstractmethod
    def send(self, metric: Metric) -> bool:
        """Send an alert for the given metric. Returns True on success."""


@dataclass
class LogChannel(AlertChannel):
    """Writes alerts to the Python logging system."""

    level_map: dict = field(default_factory=lambda: {
        MetricStatus.WARNING: logging.WARNING,
        MetricStatus.CRITICAL: logging.CRITICAL,
    })

    def send(self, metric: Metric) -> bool:
        level = self.level_map.get(metric.status, logging.INFO)
        logger.log(level, "[pipewatch] %s | status=%s value=%s",
                   metric.name, metric.status.value, metric.value)
        return True


@dataclass
class EmailChannel(AlertChannel):
    """Sends alert e-mails via SMTP."""

    smtp_host: str
    smtp_port: int
    sender: str
    recipients: List[str]
    username: str = ""
    password: str = ""

    def send(self, metric: Metric) -> bool:
        msg = EmailMessage()
        msg["Subject"] = f"[pipewatch] {metric.status.value.upper()}: {metric.name}"
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        msg.set_content(
            f"Metric   : {metric.name}\n"
            f"Status   : {metric.status.value}\n"
            f"Value    : {metric.value}\n"
            f"Message  : {metric.message}\n"
        )
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                if self.username:
                    server.login(self.username, self.password)
                server.send_message(msg)
            return True
        except Exception as exc:  # pragma: no cover
            logger.error("EmailChannel failed: %s", exc)
            return False


@dataclass
class AlertDispatcher:
    """Dispatches alerts to registered channels when status is non-OK."""

    channels: List[AlertChannel] = field(default_factory=list)
    notify_on: tuple = (MetricStatus.WARNING, MetricStatus.CRITICAL)

    def add_channel(self, channel: AlertChannel) -> None:
        self.channels.append(channel)

    def dispatch(self, metric: Metric) -> int:
        """Send alert through all channels. Returns number of successful sends."""
        if metric.status not in self.notify_on:
            return 0
        return sum(ch.send(metric) for ch in self.channels)

    def dispatch_all(self, metrics: List[Metric]) -> int:
        return sum(self.dispatch(m) for m in metrics)
