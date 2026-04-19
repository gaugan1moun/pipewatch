"""Export pipeline metric snapshots to CSV or JSON files."""

from __future__ import annotations

import csv
import json
import os
from typing import List

from pipewatch.snapshot import Snapshot


def export_snapshot_json(snapshot: Snapshot, path: str) -> None:
    """Write a snapshot to a JSON file."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)


def export_snapshot_csv(snapshot: Snapshot, path: str) -> None:
    """Write a snapshot's metrics to a CSV file."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    rows = [
        {
            "timestamp": snapshot.timestamp,
            "name": m["name"],
            "value": m["value"],
            "status": m["status"],
        }
        for m in snapshot.to_dict()["metrics"]
    ]
    fieldnames = ["timestamp", "name", "value", "status"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_snapshot(snapshot: Snapshot, path: str, fmt: str = "json") -> None:
    """Export a snapshot in the given format ('json' or 'csv')."""
    fmt = fmt.lower()
    if fmt == "json":
        export_snapshot_json(snapshot, path)
    elif fmt == "csv":
        export_snapshot_csv(snapshot, path)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'json' or 'csv'.")
