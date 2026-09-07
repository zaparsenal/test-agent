#!/usr/bin/env python3
"""Compare deterministic incident detections with held-out ground-truth labels."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from backend.analysis import ProcessAnalyzer

ROOT = Path(__file__).resolve().parents[1]


def overlap_ratio(detected: dict, expected: dict) -> float:
    start = max(datetime.fromisoformat(detected["start"]), datetime.fromisoformat(expected["start"]))
    end = min(datetime.fromisoformat(detected["end"]), datetime.fromisoformat(expected["end"]))
    union_start = min(datetime.fromisoformat(detected["start"]), datetime.fromisoformat(expected["start"]))
    union_end = max(datetime.fromisoformat(detected["end"]), datetime.fromisoformat(expected["end"]))
    return max(0.0, (end - start).total_seconds()) / max(1.0, (union_end - union_start).total_seconds())


def evaluate() -> dict[str, float | int]:
    truth = json.loads((ROOT / "data" / "ground_truth" / "incidents.json").read_text())["incidents"]
    detected = ProcessAnalyzer().detect_basic_anomalies()
    truth_by_type = {item["label"]: item for item in truth}
    detected_by_type = {item["type"]: item for item in detected}
    true_positive_types = set(truth_by_type) & set(detected_by_type)
    precision = len(true_positive_types) / max(1, len(detected_by_type))
    recall = len(true_positive_types) / max(1, len(truth_by_type))
    f1 = 2 * precision * recall / max(1e-9, precision + recall)
    overlaps = [overlap_ratio(detected_by_type[label], truth_by_type[label]) for label in true_positive_types]
    return {
        "ground_truth_incidents": len(truth_by_type),
        "detected_incidents": len(detected_by_type),
        "matched_incidents": len(true_positive_types),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "mean_temporal_overlap": round(sum(overlaps) / max(1, len(overlaps)), 3),
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))

