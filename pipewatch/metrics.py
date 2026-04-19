"""Core metric definitions and collection for pipeline health monitoring."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MetricStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class Metric:
    name: str
    value: float
    unit: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: MetricStatus = MetricStatus.UNKNOWN
    labels: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "labels": self.labels,
        }


@dataclass
class ThresholdConfig:
    warning: Optional[float] = None
    critical: Optional[float] = None
    compare: str = "gt"  # gt, lt, gte, lte

    def evaluate(self, value: float) -> MetricStatus:
        def exceeds(threshold: float) -> bool:
            if self.compare == "gt":
                return value > threshold
            elif self.compare == "lt":
                return value < threshold
            elif self.compare == "gte":
                return value >= threshold
            elif self.compare == "lte":
                return value <= threshold
            return False

        if self.critical is not None and exceeds(self.critical):
            return MetricStatus.CRITICAL
        if self.warning is not None and exceeds(self.warning):
            return MetricStatus.WARNING
        return MetricStatus.OK
