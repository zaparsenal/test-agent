#!/usr/bin/env python3
"""Generate a deterministic six-hour synthetic DCS historian export."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_START = datetime.fromisoformat("2026-08-18T08:00:00")

UNITS = {
    "LT-101": "%",
    "LT-102": "%",
    "PT-101": "bar",
    "FT-101": "m3/h",
    "P-101_STATUS": "state",
    "FV-101_POS": "%",
}

LIMITS = {
    "LT-101": {"normal_low": 35.0, "normal_high": 75.0, "alarm_low": 20.0, "alarm_high": 82.0},
    "LT-102": {"normal_low": 20.0, "normal_high": 80.0, "alarm_low": 12.0, "alarm_high": 88.0},
    "PT-101": {"normal_low": 2.6, "normal_high": 4.2, "alarm_low": 1.8, "alarm_high": 5.5},
    "FT-101": {"normal_low": 42.0, "normal_high": 54.0, "alarm_low": 30.0, "alarm_high": 60.0},
    "P-101_STATUS": {"normal_low": 1.0, "normal_high": 1.0, "alarm_low": 0.0, "alarm_high": 1.0},
    "FV-101_POS": {"normal_low": 65.0, "normal_high": 88.0, "alarm_low": 20.0, "alarm_high": 98.0},
}


def lerp(start: float, end: float, progress: float) -> float:
    return start + (end - start) * max(0.0, min(1.0, progress))


def period_for(minute: int) -> str:
    if minute < 30:
        return "normal_baseline"
    if minute < 60:
        return "startup"
    if minute < 135:
        return "normal_operation"
    if minute < 180:
        return "downstream_restriction"
    if minute < 225:
        return "sensor_drift"
    if minute < 255:
        return "bad_quality"
    if minute < 300:
        return "recovery"
    return "normal_recovered"


def alarm_for(tag: str, value: float | None, quality: str) -> str:
    if quality != "GOOD" or value is None:
        return "UNAVAILABLE"
    limits = LIMITS[tag]
    if value > limits["alarm_high"]:
        return "HIHI"
    if value < limits["alarm_low"]:
        return "LOLO"
    if value > limits["normal_high"]:
        return "HI"
    if value < limits["normal_low"]:
        return "LO"
    return "NORMAL"


def values_for(minute: int, rng: random.Random) -> dict[str, float]:
    period = period_for(minute)
    wave = math.sin(minute / 9.0)
    noise = lambda scale: rng.gauss(0.0, scale)

    if period == "startup":
        p = (minute - 30) / 30
        status = 1.0 if minute >= 35 else 0.0
        valve = lerp(18, 76, p) + noise(0.5)
        flow = lerp(0, 48, max(0, (minute - 35) / 25)) + noise(0.8)
        pressure = lerp(0.4, 3.25, max(0, (minute - 35) / 25)) + noise(0.05)
        lt101 = lerp(60, 55, p) + noise(0.15)
        lt102 = lerp(36, 42, p) + noise(0.13)
    elif period == "downstream_restriction":
        p = (minute - 135) / 45
        status = 1.0
        valve = lerp(76, 83, p) + noise(0.4)
        flow = lerp(48, 28.2, p) + noise(0.65)
        pressure = lerp(3.25, 5.95, p) + noise(0.06)
        lt101 = lerp(55, 79.0, p) + noise(0.16)
        lt102 = lerp(42, 47.5, p) + noise(0.14)
    elif period == "sensor_drift":
        p = (minute - 180) / 45
        status = 1.0
        valve = 82 + noise(0.4)
        flow = lerp(29.0, 39.0, p) + noise(1.5)
        pressure = lerp(5.8, 4.2, p) + noise(0.08)
        lt101 = lerp(79, 71, p) + noise(0.18)
        lt102 = lerp(47.5, 56, p) + noise(1.15) + 1.5 * math.sin(minute * 1.8)
    elif period == "bad_quality":
        p = (minute - 225) / 30
        status = 1.0
        valve = lerp(82, 78, p) + noise(0.45)
        flow = lerp(39, 44, p) + noise(0.65)
        pressure = lerp(4.2, 3.6, p) + noise(0.07)
        lt101 = lerp(71, 66, p) + noise(0.2)
        lt102 = 55 + wave * 0.25 + noise(0.16)
    elif period == "recovery":
        p = (minute - 255) / 45
        status = 1.0
        valve = lerp(78, 75, p) + noise(0.35)
        flow = lerp(44, 48, p) + noise(0.45)
        pressure = lerp(3.6, 3.25, p) + noise(0.05)
        lt101 = lerp(66, 56, p) + noise(0.16)
        lt102 = lerp(55, 50, p) + noise(0.14)
    else:
        status = 1.0
        valve = 75.5 + wave * 0.5 + noise(0.28)
        flow = 48.0 + wave * 0.65 + noise(0.38)
        pressure = 3.22 + wave * 0.05 + noise(0.035)
        if period == "normal_baseline":
            lt101 = 56.5 + wave * 0.25 + noise(0.12)
            lt102 = 35.5 + wave * 0.2 + noise(0.12)
        elif period == "normal_operation":
            lt101 = 55.0 + wave * 0.24 + noise(0.12)
            lt102 = 42.0 + wave * 0.2 + noise(0.12)
        else:
            lt101 = 56.0 + wave * 0.2 + noise(0.12)
            lt102 = 50.0 + wave * 0.2 + noise(0.12)

    return {
        "LT-101": lt101,
        "LT-102": lt102,
        "PT-101": pressure,
        "FT-101": max(0.0, flow),
        "P-101_STATUS": status,
        "FV-101_POS": valve,
    }


def generate(
    seed: int = 101,
    start: datetime = DEFAULT_START,
    quality_mode: str = "standard",
) -> list[dict[str, object]]:
    if quality_mode not in {"standard", "clean"}:
        raise ValueError("quality_mode must be 'standard' or 'clean'")
    rng = random.Random(seed)
    records: list[dict[str, object]] = []
    for minute in range(361):
        timestamp = start + timedelta(minutes=minute)
        period = period_for(minute)
        values = values_for(minute, rng)
        for tag, raw_value in values.items():
            quality = "GOOD"
            value: float | None = round(raw_value, 3)
            if quality_mode == "standard" and period == "bad_quality" and tag == "PT-101" and minute % 3 != 0:
                quality = "BAD"
            if quality_mode == "standard" and period == "bad_quality" and tag == "FT-101" and minute % 5 == 0:
                quality = "MISSING"
                value = None
            records.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "tag": tag,
                    "value": value,
                    "unit": UNITS[tag],
                    "quality": quality,
                    "alarm_state": alarm_for(tag, value, quality),
                }
            )
    return records


def write_dataset(
    records: list[dict[str, object]],
    seed: int,
    output_dir: Path,
    stem: str,
    quality_mode: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stem}.json"
    csv_path = output_dir / f"{stem}.csv"
    json_path.write_text(
        json.dumps({"seed": seed, "qualityMode": quality_mode, "records": records}, indent=2) + "\n"
    )
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "tag", "value", "unit", "quality", "alarm_state"])
        writer.writeheader()
        writer.writerows(records)


def write_outputs(records: list[dict[str, object]], seed: int, output_dir: Path) -> None:
    write_dataset(records, seed, output_dir, "dcs_readings", "standard")

    ground_truth = {
        "dataset_seed": seed,
        "note": "Held separately from analysis inputs; used only by tests and evaluation.",
        "incidents": [
            {"id": "restart", "label": "startup", "start": "2026-08-18T08:30:00", "end": "2026-08-18T09:00:00", "tags": ["P-101_STATUS", "FT-101", "PT-101", "FV-101_POS"]},
            {"id": "restriction", "label": "downstream_restriction", "start": "2026-08-18T10:15:00", "end": "2026-08-18T11:00:00", "tags": ["FT-101", "PT-101", "LT-101", "LT-102", "FV-101_POS"]},
            {"id": "drift", "label": "sensor_drift", "start": "2026-08-18T11:00:00", "end": "2026-08-18T11:45:00", "tags": ["LT-102"]},
            {"id": "quality", "label": "bad_quality", "start": "2026-08-18T11:45:00", "end": "2026-08-18T12:15:00", "tags": ["PT-101", "FT-101"]},
            {"id": "recovery", "label": "recovery", "start": "2026-08-18T12:15:00", "end": "2026-08-18T13:00:00", "tags": ["FT-101", "PT-101", "LT-101", "FV-101_POS"]}
        ]
    }
    ground_truth_path = ROOT / "data" / "expected-results" / "incidents.json"
    ground_truth_path.parent.mkdir(parents=True, exist_ok=True)
    ground_truth_path.write_text(json.dumps(ground_truth, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "sample-inputs" / "dcs")
    args = parser.parse_args()
    records = generate(seed=args.seed)
    write_outputs(records, args.seed, args.output_dir)
    clean_records = generate(seed=202, quality_mode="clean")
    write_dataset(clean_records, 202, args.output_dir, "dcs_readings_clean", "clean")
    print(
        f"Generated standard and clean six-hour scenarios "
        f"({len(records):,} readings each; seeds {args.seed} and 202)."
    )


if __name__ == "__main__":
    main()
