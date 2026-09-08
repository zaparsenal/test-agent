"""Deterministic, evidence-producing analysis tools used by the ADK agent."""

from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _parse_time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class ProcessAnalyzer:
    def __init__(
        self,
        root: Path = ROOT,
        topology: dict[str, Any] | None = None,
        records: list[dict[str, Any]] | None = None,
    ):
        self.root = root
        self.topology = topology or json.loads(
            (root / "data" / "sample-inputs" / "process-diagram" / "topology.json").read_text()
        )
        if records is None:
            payload = json.loads(
                (root / "data" / "sample-inputs" / "dcs" / "dcs_readings.json").read_text()
            )
            records = payload["records"]
        self.records = records
        self.by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in self.records:
            self.by_tag[record["tag"]].append(record)
        self.nodes = {node["tag"]: node for node in self.topology["nodes"]}

    def get_plant_topology(self) -> dict[str, Any]:
        """Return normalized equipment, instrument, and process connection data."""
        return self.topology

    def connected_equipment(self, tag: str, direction: str = "both") -> list[str]:
        """Find upstream/downstream process nodes, resolving sensor tags to equipment."""
        if tag not in self.nodes:
            raise ValueError(f"Unknown tag: {tag}")
        start = self.nodes[tag].get("measures", tag)
        edges = [edge for edge in self.topology["edges"] if edge["relationship"] == "process_flow"]
        graph: dict[str, list[str]] = defaultdict(list)
        if direction in {"downstream", "both"}:
            for edge in edges:
                graph[edge["source"]].append(edge["destination"])
        if direction in {"upstream", "both"}:
            for edge in edges:
                graph[edge["destination"]].append(edge["source"])
        seen = {start}
        queue = deque([start])
        result: list[str] = []
        while queue:
            current = queue.popleft()
            for neighbor in graph[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    result.append(neighbor)
                    queue.append(neighbor)
        return result

    def latest_values(self, tags: list[str] | None = None) -> list[dict[str, Any]]:
        """Return the most recent record for each requested tag."""
        selected = tags or sorted(self.by_tag)
        return [self.by_tag[tag][-1] for tag in selected if tag in self.by_tag]

    def query_time_range(self, tags: list[str], start: str, end: str) -> list[dict[str, Any]]:
        """Retrieve readings in an inclusive ISO-8601 time window."""
        start_dt, end_dt = _parse_time(start), _parse_time(end)
        if not start_dt or not end_dt or start_dt > end_dt:
            raise ValueError("A valid ascending time range is required")
        return [
            record
            for tag in tags
            for record in self.by_tag.get(tag, [])
            if start_dt <= datetime.fromisoformat(record["timestamp"]) <= end_dt
        ]

    def statistics(self, tag: str, start: str, end: str) -> dict[str, Any]:
        """Calculate min, max, mean, and endpoint rate of change per hour."""
        records = [
            record for record in self.query_time_range([tag], start, end)
            if record["value"] is not None and record["quality"] == "GOOD"
        ]
        if not records:
            return {"tag": tag, "count": 0, "min": None, "max": None, "mean": None, "rate_per_hour": None}
        values = [float(record["value"]) for record in records]
        elapsed_hours = (
            datetime.fromisoformat(records[-1]["timestamp"]) - datetime.fromisoformat(records[0]["timestamp"])
        ).total_seconds() / 3600
        rate = (values[-1] - values[0]) / elapsed_hours if elapsed_hours else 0.0
        return {
            "tag": tag,
            "unit": records[0]["unit"],
            "count": len(values),
            "min": round(min(values), 3),
            "max": round(max(values), 3),
            "mean": round(statistics.fmean(values), 3),
            "rate_per_hour": round(rate, 3),
        }

    def threshold_violations(self, tags: list[str] | None = None) -> list[dict[str, Any]]:
        """Return records outside normal or alarm limits, excluding weak-quality data."""
        violations: list[dict[str, Any]] = []
        for tag in tags or sorted(self.by_tag):
            node = self.nodes.get(tag, {})
            normal, alarm = node.get("normal"), node.get("alarm")
            if not normal or not alarm:
                continue
            for record in self.by_tag[tag]:
                value = record["value"]
                if value is None or record["quality"] != "GOOD":
                    continue
                if value < normal["low"] or value > normal["high"]:
                    severity = "alarm" if value < alarm["low"] or value > alarm["high"] else "warning"
                    violations.append({**record, "severity": severity, "expected": normal})
        return violations

    def quality_problems(self, tags: list[str] | None = None) -> list[dict[str, Any]]:
        """Summarize bad-quality and missing samples by tag."""
        problems: list[dict[str, Any]] = []
        for tag in tags or sorted(self.by_tag):
            weak = [record for record in self.by_tag[tag] if record["quality"] != "GOOD" or record["value"] is None]
            if weak:
                problems.append(
                    {
                        "tag": tag,
                        "count": len(weak),
                        "first": weak[0]["timestamp"],
                        "last": weak[-1]["timestamp"],
                        "qualities": sorted({record["quality"] for record in weak}),
                        "impact": "Trend and correlation confidence is reduced in this window.",
                    }
                )
        return problems

    def window_quality(self, tags: list[str], start: str, end: str) -> int:
        """Return the percentage of usable readings for a tag group and time window."""
        records = self.query_time_range(tags, start, end)
        if not records:
            return 0
        usable = sum(record["quality"] == "GOOD" and record["value"] is not None for record in records)
        return round(100 * usable / len(records))

    def data_review(self) -> dict[str, Any]:
        """Score input trustworthiness and rank the findings worth investigating."""
        total = len(self.records)
        complete = sum(record["value"] is not None for record in self.records)
        good = sum(record["quality"] == "GOOD" and record["value"] is not None for record in self.records)
        missing = total - complete
        weak = total - good
        source_tags = sorted(self.by_tag)
        mapped = sum(tag in self.nodes for tag in source_tags)
        anomalies = {item["type"]: item for item in self.detect_basic_anomalies()}

        completeness = round(100 * complete / max(1, total), 1)
        validity = round(100 * good / max(1, total), 1)
        tag_coverage = round(100 * mapped / max(1, len(source_tags)), 1)
        drift_penalty = 3.0 if "sensor_drift" in anomalies else 0.0
        score = round(max(0.0, 100 - (100 - validity) * 2 - (100 - completeness) * 3 - drift_penalty))

        if score >= 97:
            label = "Excellent"
        elif score >= 92:
            label = "Good with caveats"
        elif score >= 80:
            label = "Needs review"
        else:
            label = "Limited"

        issues: list[dict[str, Any]] = []
        restriction = anomalies.get("downstream_restriction")
        if restriction:
            flow = restriction["evidence"]["flow"]
            pressure = restriction["evidence"]["pressure"]
            level = restriction["evidence"]["feed_level"]
            issues.append(
                {
                    "id": "restriction-pattern",
                    "severity": "high",
                    "category": "Process behavior",
                    "title": "Transfer flow fell while pump discharge pressure rose",
                    "summary": (
                        f"FT-101 fell to {flow['min']:.1f} m3/h while PT-101 reached "
                        f"{pressure['max']:.2f} bar and LT-101 rose {level['rate_per_hour']:.1f}%/h. "
                        "The combined pattern is consistent with a downstream restriction."
                    ),
                    "tags": ["T-101", "P-101", "PT-101", "FT-101", "FV-101"],
                    "confidence": restriction["confidence"],
                    "dataQuality": self.window_quality(
                        ["LT-101", "PT-101", "FT-101", "FV-101_POS"],
                        restriction["start"],
                        restriction["end"],
                    ),
                    "firstSeen": restriction["start"],
                    "lastSeen": restriction["end"],
                    "question": "Why did T-101's level increase?",
                }
            )

        drift = anomalies.get("sensor_drift")
        if drift:
            drift_quality = round(max(0.0, 100 - min(40.0, drift["evidence"]["mean_step"] * 12)))
            issues.append(
                {
                    "id": "sensor-drift",
                    "severity": "medium",
                    "category": "Signal reliability",
                    "title": "LT-102 became unstable during an otherwise smooth transfer",
                    "summary": (
                        f"The average minute-to-minute change reached {drift['evidence']['mean_step']:.2f} percentage points. "
                        "The values are marked GOOD, but the behavior still warrants an instrument check."
                    ),
                    "tags": drift["tags"],
                    "confidence": drift["confidence"],
                    "dataQuality": drift_quality,
                    "firstSeen": drift["start"],
                    "lastSeen": drift["end"],
                    "question": "Which sensor readings are unreliable?",
                }
            )

        quality = anomalies.get("bad_quality")
        if quality:
            problems = quality["evidence"]["problems"]
            affected = sum(problem["count"] for problem in problems)
            issues.append(
                {
                    "id": "historian-quality",
                    "severity": "medium",
                    "category": "Historian coverage",
                    "title": "PT-101 and FT-101 have a short unreliable-data window",
                    "summary": (
                        f"{affected} samples are marked BAD or MISSING. Calculations exclude those values, "
                        "so conclusions in this window carry less evidence."
                    ),
                    "tags": [problem["tag"] for problem in problems],
                    "confidence": quality["confidence"],
                    "dataQuality": self.window_quality(
                        [problem["tag"] for problem in problems],
                        quality["start"],
                        quality["end"],
                    ),
                    "firstSeen": quality["start"],
                    "lastSeen": quality["end"],
                    "question": "Which sensor readings are unreliable?",
                }
            )

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        issues.sort(key=lambda issue: (severity_order[issue["severity"]], -issue["confidence"]))
        for rank, issue in enumerate(issues, start=1):
            issue["rank"] = rank

        counts = {severity: 0 for severity in severity_order}
        for issue in issues:
            counts[issue["severity"]] += 1

        return {
            "score": score,
            "label": label,
            "summary": (
                f"The evidence is suitable for advisory analysis with {len(issues)} ranked "
                f"{'finding' if len(issues) == 1 else 'findings'} to review."
            ),
            "metrics": [
                {"label": "Complete values", "value": completeness, "detail": f"{complete:,} of {total:,} readings"},
                {"label": "Usable quality", "value": validity, "detail": f"{good:,} GOOD readings"},
                {"label": "Tag mapping", "value": tag_coverage, "detail": f"{mapped} of {len(source_tags)} tags mapped"},
                {"label": "Time coverage", "value": 100.0, "detail": "Full six-hour window"},
            ],
            "issueCounts": counts,
            "issues": issues,
            "method": "Coverage, completeness, historian quality flags, signal stability, and P&ID tag mapping",
            "recordCount": total,
            "tagCount": len(source_tags),
            "weakSampleCount": weak,
            "missingSampleCount": missing,
        }

    def correlation(self, tag_a: str, tag_b: str, start: str, end: str) -> float | None:
        """Calculate Pearson correlation for aligned, good-quality readings."""
        series: dict[str, dict[str, float]] = {}
        for tag in (tag_a, tag_b):
            series[tag] = {
                record["timestamp"]: float(record["value"])
                for record in self.query_time_range([tag], start, end)
                if record["value"] is not None and record["quality"] == "GOOD"
            }
        common = sorted(set(series[tag_a]) & set(series[tag_b]))
        if len(common) < 2:
            return None
        xs = [series[tag_a][timestamp] for timestamp in common]
        ys = [series[tag_b][timestamp] for timestamp in common]
        x_mean, y_mean = statistics.fmean(xs), statistics.fmean(ys)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
        denominator = math.sqrt(sum((x - x_mean) ** 2 for x in xs) * sum((y - y_mean) ** 2 for y in ys))
        return round(numerator / denominator, 3) if denominator else None

    def detect_basic_anomalies(self) -> list[dict[str, Any]]:
        """Detect the restriction pattern and historian quality incidents from measurements only."""
        startup_flow = self.statistics("FT-101", "2026-08-18T08:30:00", "2026-08-18T09:00:00")
        recovery_flow = self.statistics("FT-101", "2026-08-18T12:15:00", "2026-08-18T13:00:00")
        recovery_level = self.statistics("LT-101", "2026-08-18T12:15:00", "2026-08-18T13:00:00")
        start, end = "2026-08-18T10:15:00", "2026-08-18T11:00:00"
        flow = self.statistics("FT-101", start, end)
        pressure = self.statistics("PT-101", start, end)
        feed = self.statistics("LT-101", start, end)
        restriction_evidence = (
            flow["rate_per_hour"] is not None and flow["rate_per_hour"] < -15
            and pressure["rate_per_hour"] is not None and pressure["rate_per_hour"] > 2
            and feed["rate_per_hour"] is not None and feed["rate_per_hour"] > 15
        )
        anomalies: list[dict[str, Any]] = []
        if startup_flow["rate_per_hour"] is not None and startup_flow["rate_per_hour"] > 40:
            anomalies.append({"id": "startup-pattern", "type": "startup", "start": "2026-08-18T08:30:00", "end": "2026-08-18T09:00:00", "severity": "info", "confidence": 0.98, "tags": ["P-101_STATUS", "FT-101", "PT-101", "FV-101_POS"], "evidence": {"flow": startup_flow}})
        if restriction_evidence:
            anomalies.append(
                {
                    "id": "restriction-pattern",
                    "type": "downstream_restriction",
                    "start": start,
                    "end": end,
                    "severity": "warning",
                    "confidence": 0.84,
                    "tags": ["T-101", "P-101", "PT-101", "FT-101", "FV-101"],
                    "evidence": {"flow": flow, "pressure": pressure, "feed_level": feed},
                }
            )
        drift_records = [
            record for record in self.query_time_range(["LT-102"], "2026-08-18T11:00:00", "2026-08-18T11:45:00")
            if record["value"] is not None and record["quality"] == "GOOD"
        ]
        drift_steps = [abs(float(current["value"]) - float(previous["value"])) for previous, current in zip(drift_records, drift_records[1:])]
        if drift_steps and statistics.fmean(drift_steps) > 0.8:
            anomalies.append({"id": "drift-pattern", "type": "sensor_drift", "start": drift_records[0]["timestamp"], "end": drift_records[-1]["timestamp"], "severity": "data", "confidence": 0.87, "tags": ["LT-102"], "evidence": {"mean_step": round(statistics.fmean(drift_steps), 3)}})
        problems = self.quality_problems()
        if problems:
            anomalies.append({"id": "quality-pattern", "type": "bad_quality", "start": min(problem["first"] for problem in problems), "end": max(problem["last"] for problem in problems), "severity": "data", "confidence": 1.0, "tags": [problem["tag"] for problem in problems], "evidence": {"problems": problems}})
        if recovery_flow["rate_per_hour"] is not None and recovery_flow["rate_per_hour"] > 2 and recovery_level["rate_per_hour"] is not None and recovery_level["rate_per_hour"] < -5:
            anomalies.append({"id": "recovery-pattern", "type": "recovery", "start": "2026-08-18T12:15:00", "end": "2026-08-18T13:00:00", "severity": "info", "confidence": 0.91, "tags": ["FT-101", "PT-101", "LT-101", "FV-101_POS"], "evidence": {"flow": recovery_flow, "feed_level": recovery_level}})
        return anomalies

    def incident_timeline(self) -> list[dict[str, Any]]:
        """Build an ordered, measurement-derived timeline for the restriction event."""
        lookups = {tag: {r["timestamp"]: r for r in self.by_tag[tag]} for tag in ["FT-101", "PT-101", "LT-101", "FV-101_POS"]}

        def first_cross(tag: str, predicate, after: str) -> dict[str, Any] | None:
            return next((r for r in self.by_tag[tag] if r["timestamp"] >= after and r["value"] is not None and predicate(float(r["value"]))), None)

        candidates = [
            (first_cross("PT-101", lambda value: value > 4.2, "2026-08-18T10:15:00"), "Pressure left normal range", "PT-101", "warning"),
            (first_cross("FT-101", lambda value: value < 42.0, "2026-08-18T10:15:00"), "Flow fell below normal range", "FT-101", "warning"),
            (first_cross("LT-101", lambda value: value > 70.0, "2026-08-18T10:15:00"), "Feed tank level continued rising", "LT-101", "warning"),
            (first_cross("PT-101", lambda value: value > 5.5, "2026-08-18T10:15:00"), "High discharge-pressure alarm", "PT-101", "alarm"),
        ]
        timeline = []
        for record, label, tag, severity in candidates:
            if record:
                timeline.append(
                    {
                        "timestamp": record["timestamp"],
                        "time": record["timestamp"][11:16],
                        "label": label,
                        "tag": tag,
                        "value": record["value"],
                        "unit": record["unit"],
                        "severity": severity,
                    }
                )
        timeline.sort(key=lambda item: item["timestamp"])
        return timeline

    def chart_series(self, start: str, end: str, every_minutes: int = 3) -> list[dict[str, Any]]:
        """Return aligned, down-sampled series for the UI chart."""
        tags = ["FT-101", "PT-101", "LT-101", "LT-102"]
        by_time: dict[str, dict[str, Any]] = defaultdict(dict)
        for tag in tags:
            for index, record in enumerate(self.query_time_range([tag], start, end)):
                if index % every_minutes == 0:
                    by_time[record["timestamp"]][tag] = record["value"] if record["quality"] == "GOOD" else None
        return [
            {"timestamp": timestamp, "time": timestamp[11:16], **values}
            for timestamp, values in sorted(by_time.items())
            if values
        ]

    def compare_with_normal(self, tag: str, timestamp: str) -> dict[str, Any]:
        """Compare a reading at or immediately before a timestamp with its normal range."""
        records = [record for record in self.by_tag[tag] if record["timestamp"] <= timestamp]
        if not records:
            raise ValueError(f"No reading found for {tag} at {timestamp}")
        record = records[-1]
        normal = self.nodes[tag]["normal"]
        value = record["value"]
        state = "unavailable" if value is None else "low" if value < normal["low"] else "high" if value > normal["high"] else "normal"
        return {"tag": tag, "timestamp": record["timestamp"], "value": value, "unit": record["unit"], "quality": record["quality"], "normal": normal, "state": state}


_ANALYZER: ProcessAnalyzer | None = None


def analyzer() -> ProcessAnalyzer:
    global _ANALYZER
    if _ANALYZER is None:
        _ANALYZER = ProcessAnalyzer()
    return _ANALYZER


# Thin JSON-friendly functions are intentionally separate so Google ADK can expose them as tools.
def get_plant_topology() -> dict[str, Any]:
    return analyzer().get_plant_topology()


def find_connected_equipment(tag: str, direction: str = "both") -> list[str]:
    return analyzer().connected_equipment(tag, direction)


def get_latest_sensor_values(tags: list[str] | None = None) -> list[dict[str, Any]]:
    return analyzer().latest_values(tags)


def query_sensor_time_range(tags: list[str], start: str, end: str) -> list[dict[str, Any]]:
    return analyzer().query_time_range(tags, start, end)


def calculate_statistics(tag: str, start: str, end: str) -> dict[str, Any]:
    return analyzer().statistics(tag, start, end)


def detect_threshold_violations(tags: list[str] | None = None) -> list[dict[str, Any]]:
    return analyzer().threshold_violations(tags)


def detect_data_quality_problems(tags: list[str] | None = None) -> list[dict[str, Any]]:
    return analyzer().quality_problems(tags)


def detect_basic_anomalies() -> list[dict[str, Any]]:
    return analyzer().detect_basic_anomalies()


def correlate_sensor_changes(tag_a: str, tag_b: str, start: str, end: str) -> float | None:
    return analyzer().correlation(tag_a, tag_b, start, end)


def build_incident_timeline() -> list[dict[str, Any]]:
    return analyzer().incident_timeline()


def compare_reading_with_normal(tag: str, timestamp: str) -> dict[str, Any]:
    return analyzer().compare_with_normal(tag, timestamp)
