"""Escalation policy: re-alert after repeated failures over time."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import json
from pathlib import Path
from datetime import datetime, timezone

DEFAULT_PATH = Path(".pipewatch/escalation_state.json")


@dataclass
class EscalationEntry:
    metric_name: str
    consecutive_failures: int = 0
    last_escalated: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "consecutive_failures": self.consecutive_failures,
            "last_escalated": self.last_escalated,
        }

    @staticmethod
    def from_dict(d: dict) -> "EscalationEntry":
        return EscalationEntry(
            metric_name=d["metric_name"],
            consecutive_failures=d.get("consecutive_failures", 0),
            last_escalated=d.get("last_escalated"),
        )


def load_escalation_state(path: Path = DEFAULT_PATH) -> List[EscalationEntry]:
    if not path.exists():
        return []
    with open(path) as f:
        return [EscalationEntry.from_dict(e) for e in json.load(f)]


def save_escalation_state(entries: List[EscalationEntry], path: Path = DEFAULT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump([e.to_dict() for e in entries], f, indent=2)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def evaluate_escalation(
    metric_name: str,
    is_failing: bool,
    entries: List[EscalationEntry],
    threshold: int = 3,
) -> tuple[List[EscalationEntry], bool]:
    """Update state and return (updated_entries, should_escalate)."""
    entry = next((e for e in entries if e.metric_name == metric_name), None)
    if entry is None:
        entry = EscalationEntry(metric_name=metric_name)
        entries = list(entries) + [entry]

    if not is_failing:
        entry.consecutive_failures = 0
        return entries, False

    entry.consecutive_failures += 1
    if entry.consecutive_failures >= threshold:
        entry.last_escalated = _now()
        return entries, True
    return entries, False
