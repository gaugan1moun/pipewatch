"""Alert silencing/suppression rules for pipewatch."""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class SilenceRule:
    metric_name: str
    reason: str
    expires_at: datetime

    def is_active(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        return now < self.expires_at

    def to_dict(self) -> dict:
        return {
            "metric_name": self.metric_name,
            "reason": self.reason,
            "expires_at": self.expires_at.isoformat(),
        }

    @staticmethod
    def from_dict(d: dict) -> "SilenceRule":
        return SilenceRule(
            metric_name=d["metric_name"],
            reason=d["reason"],
            expires_at=datetime.fromisoformat(d["expires_at"]),
        )


def load_silences(path: str) -> List[SilenceRule]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return [SilenceRule.from_dict(r) for r in data]


def save_silences(path: str, rules: List[SilenceRule]) -> None:
    with open(path, "w") as f:
        json.dump([r.to_dict() for r in rules], f, indent=2)


def add_silence(path: str, metric_name: str, reason: str, duration_minutes: int) -> SilenceRule:
    rules = load_silences(path)
    expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)
    rule = SilenceRule(metric_name=metric_name, reason=reason, expires_at=expires_at)
    rules.append(rule)
    save_silences(path, rules)
    return rule


def is_silenced(path: str, metric_name: str, now: Optional[datetime] = None) -> bool:
    rules = load_silences(path)
    return any(r.metric_name == metric_name and r.is_active(now) for r in rules)


def purge_expired(path: str) -> int:
    rules = load_silences(path)
    active = [r for r in rules if r.is_active()]
    removed = len(rules) - len(active)
    save_silences(path, active)
    return removed
