"""Load alert channel configuration from YAML."""

from __future__ import annotations

from pathlib import Path
from typing import List

import yaml

from pipewatch.alerts import AlertChannel, AlertDispatcher, EmailChannel, LogChannel


def _build_channel(cfg: dict) -> AlertChannel:
    kind = cfg.get("type", "log").lower()
    if kind == "log":
        return LogChannel()
    if kind == "email":
        return EmailChannel(
            smtp_host=cfg["smtp_host"],
            smtp_port=int(cfg.get("smtp_port", 587)),
            sender=cfg["sender"],
            recipients=cfg["recipients"],
            username=cfg.get("username", ""),
            password=cfg.get("password", ""),
        )
    raise ValueError(f"Unknown alert channel type: {kind!r}")


def load_dispatcher(path: str | Path) -> AlertDispatcher:
    """Build an AlertDispatcher from a YAML config file."""
    data = yaml.safe_load(Path(path).read_text())
    dispatcher = AlertDispatcher()
    for entry in data.get("alerts", {}).get("channels", []):
        dispatcher.add_channel(_build_channel(entry))
    return dispatcher


def default_alert_config_template() -> str:
    return """\
alerts:
  channels:
    - type: log
    # - type: email
    #   smtp_host: smtp.example.com
    #   smtp_port: 587
    #   sender: pipewatch@example.com
    #   recipients:
    #     - ops@example.com
    #   username: pipewatch
    #   password: secret
"""
