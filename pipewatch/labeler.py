"""Metric labeling: attach structured labels to metrics for richer filtering and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LabelSet:
    """A set of key-value labels attached to a metric."""
    labels: Dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> Optional[str]:
        return self.labels.get(key)

    def set(self, key: str, value: str) -> None:
        self.labels[key] = value

    def matches(self, selector: Dict[str, str]) -> bool:
        """Return True if all selector key-value pairs are present in this label set."""
        return all(self.labels.get(k) == v for k, v in selector.items())

    def to_dict(self) -> Dict[str, str]:
        return dict(self.labels)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "LabelSet":
        return cls(labels=dict(data))


def label_metrics(metrics: list, selector: Dict[str, str]) -> list:
    """Filter metrics whose LabelSet matches all selector key-value pairs.

    Metrics are expected to have a `.labels` attribute of type LabelSet.
    Metrics without a `.labels` attribute are silently excluded.
    """
    result = []
    for m in metrics:
        ls = getattr(m, "labels", None)
        if isinstance(ls, LabelSet) and ls.matches(selector):
            result.append(m)
    return result


def group_by_label(metrics: list, key: str) -> Dict[str, list]:
    """Group metrics by the value of a specific label key.

    Metrics missing the label are grouped under the empty string.
    """
    groups: Dict[str, list] = {}
    for m in metrics:
        ls = getattr(m, "labels", None)
        value = ls.get(key) if isinstance(ls, LabelSet) else None
        bucket = value if value is not None else ""
        groups.setdefault(bucket, []).append(m)
    return groups


def label_summary(metrics: list, key: str) -> List[str]:
    """Return a human-readable summary of metric counts grouped by a label key."""
    groups = group_by_label(metrics, key)
    lines = [f"Label '{key}' distribution:"]
    for value, members in sorted(groups.items()):
        display = value if value else "(unlabeled)"
        lines.append(f"  {display}: {len(members)} metric(s)")
    return lines
