"""Circuit breaker for pipeline metric checks — trips after repeated failures."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_STATE_PATH = ".pipewatch/circuit_breaker.json"


@dataclass
class CircuitState:
    metric_name: str
    failure_count: int = 0
    tripped: bool = False
    tripped_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "failure_count": self.failure_count,
            "tripped": self.tripped,
            "tripped_at": self.tripped_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CircuitState":
        return cls(
            metric_name=d["metric_name"],
            failure_count=d.get("failure_count", 0),
            tripped=d.get("tripped", False),
            tripped_at=d.get("tripped_at"),
        )


def load_circuit_state(path: str = DEFAULT_STATE_PATH) -> Dict[str, CircuitState]:
    p = Path(path)
    if not p.exists():
        return {}
    data = json.loads(p.read_text())
    return {k: CircuitState.from_dict(v) for k, v in data.items()}


def save_circuit_state(
    state: Dict[str, CircuitState], path: str = DEFAULT_STATE_PATH
) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({k: v.to_dict() for k, v in state.items()}, indent=2))


def record_failure(
    metric_name: str,
    state: Dict[str, CircuitState],
    threshold: int,
    now: Optional[str] = None,
) -> CircuitState:
    from datetime import datetime, timezone

    entry = state.get(metric_name, CircuitState(metric_name=metric_name))
    if not entry.tripped:
        entry.failure_count += 1
        if entry.failure_count >= threshold:
            entry.tripped = True
            entry.tripped_at = now or datetime.now(timezone.utc).isoformat()
    state[metric_name] = entry
    return entry


def reset_circuit(
    metric_name: str, state: Dict[str, CircuitState]
) -> CircuitState:
    entry = CircuitState(metric_name=metric_name)
    state[metric_name] = entry
    return entry


def is_tripped(metric_name: str, state: Dict[str, CircuitState]) -> bool:
    return state.get(metric_name, CircuitState(metric_name=metric_name)).tripped
