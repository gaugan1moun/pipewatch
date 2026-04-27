"""Replay historical metric snapshots for debugging and analysis."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional

from pipewatch.snapshot import Snapshot, from_dict


@dataclass
class ReplayFrame:
    """A single frame in a replay session."""

    index: int
    snapshot: Snapshot

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "snapshot": self.snapshot.to_dict(),
        }


@dataclass
class ReplaySession:
    """Ordered sequence of snapshots for replay."""

    frames: List[ReplayFrame] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.frames)

    def __iter__(self) -> Iterator[ReplayFrame]:
        return iter(self.frames)

    def get_frame(self, index: int) -> Optional[ReplayFrame]:
        for frame in self.frames:
            if frame.index == index:
                return frame
        return None


def load_replay_snapshots(paths: List[Path]) -> ReplaySession:
    """Load multiple snapshot files into a ReplaySession, sorted by timestamp."""
    snapshots: List[Snapshot] = []
    for path in paths:
        if not path.exists():
            continue
        raw = json.loads(path.read_text())
        snapshots.append(from_dict(raw))

    snapshots.sort(key=lambda s: s.timestamp)
    frames = [ReplayFrame(index=i, snapshot=s) for i, s in enumerate(snapshots)]
    return ReplaySession(frames=frames)


def replay_summary(session: ReplaySession) -> List[str]:
    """Return a human-readable summary of each frame in the session."""
    lines: List[str] = []
    for frame in session:
        snap = frame.snapshot
        statuses = ", ".join(
            f"{e.metric_name}={e.status}" for e in snap.entries
        )
        lines.append(f"[{frame.index}] {snap.timestamp}  {statuses or '(no entries)'}")
    return lines
