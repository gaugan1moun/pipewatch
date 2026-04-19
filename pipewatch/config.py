"""Configuration loader for pipewatch metric thresholds."""

import json
from pathlib import Path
from typing import Dict

from pipewatch.metrics import ThresholdConfig

DEFAULT_CONFIG_PATH = Path("pipewatch.json")


def load_thresholds(config_path: Path = DEFAULT_CONFIG_PATH) -> Dict[str, ThresholdConfig]:
    """Load threshold configurations from a JSON file."""
    if not config_path.exists():
        return {}

    with config_path.open() as f:
        raw = json.load(f)

    thresholds = {}
    for metric_name, cfg in raw.get("metrics", {}).items():
        thresholds[metric_name] = ThresholdConfig(
            warning=cfg.get("warning"),
            critical=cfg.get("critical"),
            compare=cfg.get("compare", "gt"),
        )
    return thresholds


def default_config_template() -> dict:
    """Return a minimal example configuration dictionary."""
    return {
        "metrics": {
            "row_count": {"warning": 1000, "critical": 5000, "compare": "gt"},
            "lag_seconds": {"warning": 60, "critical": 300, "compare": "gt"},
            "error_rate": {"warning": 0.05, "critical": 0.1, "compare": "gt"},
        }
    }
