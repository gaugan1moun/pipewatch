"""Simple anomaly detection based on historical metric values."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from pipewatch.history import HistoryEntry


@dataclass
class AnomalyResult:
    metric_name: str
    is_anomaly: bool
    current_value: float
    mean: float
    std: float
    z_score: float
    message: str

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "is_anomaly": self.is_anomaly,
            "current_value": self.current_value,
            "mean": round(self.mean, 4),
            "std": round(self.std, 4),
            "z_score": round(self.z_score, 4),
            "message": self.message,
        }


def _mean(values: List[float]) -> float:
    return sum(values) / len(values)


def _std(values: List[float], mean: float) -> float:
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return variance ** 0.5


def detect_anomaly(
    metric_name: str,
    current_value: float,
    history: List[HistoryEntry],
    z_threshold: float = 2.5,
    min_samples: int = 5,
) -> Optional[AnomalyResult]:
    """Detect if current_value is anomalous given historical entries.

    Returns None if there is insufficient history.
    """
    values = [e.value for e in history if e.metric_name == metric_name]
    if len(values) < min_samples:
        return None

    mean = _mean(values)
    std = _std(values, mean)

    if std == 0:
        z_score = 0.0
        is_anomaly = False
        message = "No variance in history; cannot detect anomaly."
    else:
        z_score = abs(current_value - mean) / std
        is_anomaly = z_score > z_threshold
        if is_anomaly:
            message = (
                f"Anomaly detected: value {current_value} deviates "
                f"{z_score:.2f} std devs from mean {mean:.4f}."
            )
        else:
            message = f"Value {current_value} is within normal range (z={z_score:.2f})."

    return AnomalyResult(
        metric_name=metric_name,
        is_anomaly=is_anomaly,
        current_value=current_value,
        mean=mean,
        std=std,
        z_score=z_score,
        message=message,
    )
