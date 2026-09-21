"""Build restricted-catalog A2UI v0.9 messages from computed evidence."""

from __future__ import annotations

import json
import re
import uuid
from functools import lru_cache
from pathlib import Path, PurePath
from typing import Any

from a2ui.inference_formats.direct_json.format import DirectJsonFormat
from a2ui.schema.catalog import CatalogConfig
from a2ui.schema.catalog_provider import FileSystemCatalogProvider

from backend.analysis import ProcessAnalyzer

CATALOG_ID = "https://fieldguide.demo/a2ui/catalogs/industrial/v1"
ALLOWED_COMPONENTS = {
    "ResponseLayout",
    "OperationalSummary",
    "KpiGrid",
    "TrendChart",
    "IncidentTimeline",
    "SensorQualityWarning",
    "ProcessDiagram",
    "EquipmentTable",
    "InspectionPanel",
    "StatusState",
}


def _catalog_config_for_path(catalog_path: PurePath) -> CatalogConfig:
    """Load a local catalog without treating a Windows drive letter as a URL scheme."""
    return CatalogConfig(
        name="fieldguide-industrial",
        provider=FileSystemCatalogProvider(str(catalog_path)),
    )


@lru_cache(maxsize=1)
def _official_a2ui_format() -> DirectJsonFormat:
    catalog_path = Path(__file__).with_name("industrial_catalog.json")
    return DirectJsonFormat(
        version="0.9.1",
        catalogs=[_catalog_config_for_path(catalog_path)],
    )


def detect_intent(question: str) -> str:
    text = question.lower()
    if any(word in text for word in ["unreliable", "quality", "bad sensor", "missing", "drift"]):
        return "sensor_quality"
    if any(word in text for word in ["why", "cause", "increasing"]):
        return "root_cause"
    if any(word in text for word in ["inspect", "inspection", "which equipment"]):
        return "inspection"
    if any(word in text for word in ["trend", "pressure and flow", "between 10", "10:00", "11:00"]):
        return "trend"
    if any(word in text for word in ["path", "p&id", "pid", "diagram"]):
        return "process_path"
    return "status"


def _component(component_id: str, component: str, **props: Any) -> dict[str, Any]:
    if component not in ALLOWED_COMPONENTS:
        raise ValueError(f"Component {component!r} is not in the approved industrial catalog")
    return {"id": component_id, "component": component, **props}


def _incident_kpis(analyzer: ProcessAnalyzer, timestamp: str = "2026-08-18T10:52:00") -> list[dict[str, Any]]:
    cards = []
    for tag in ["LT-101", "PT-101", "FT-101", "FV-101_POS"]:
        comparison = analyzer.compare_with_normal(tag, timestamp)
        normal = comparison["normal"]
        cards.append(
            {
                "tag": tag,
                "value": comparison["value"],
                "unit": comparison["unit"],
                "quality": comparison["quality"],
                "state": comparison["state"],
                "normalText": f"Expected {normal['low']:g}–{normal['high']:g} {comparison['unit']}",
                "timestamp": comparison["timestamp"],
            }
        )
    return cards


def _latest_kpis(analyzer: ProcessAnalyzer) -> list[dict[str, Any]]:
    cards = []
    for record in analyzer.latest_values(["LT-101", "PT-101", "FT-101", "FV-101_POS"]):
        node = analyzer.nodes[record["tag"]]
        normal = node["normal"]
        value = record["value"]
        state = "unavailable" if value is None else "low" if value < normal["low"] else "high" if value > normal["high"] else "normal"
        cards.append(
            {
                "tag": record["tag"], "value": value, "unit": record["unit"], "quality": record["quality"],
                "state": state, "normalText": f"Expected {normal['low']:g}–{normal['high']:g} {record['unit']}",
                "timestamp": record["timestamp"],
            }
        )
    return cards


def build_response(question: str, analyzer: ProcessAnalyzer) -> dict[str, Any]:
    intent = detect_intent(question)
    surface_id = f"process-insight-{uuid.uuid4().hex[:10]}"
    root_children: list[str] = ["summary"]
    components: list[dict[str, Any]] = []

    flow_stats = analyzer.statistics("FT-101", "2026-08-18T10:15:00", "2026-08-18T11:00:00")
    pressure_stats = analyzer.statistics("PT-101", "2026-08-18T10:15:00", "2026-08-18T11:00:00")
    level_stats = analyzer.statistics("LT-101", "2026-08-18T10:15:00", "2026-08-18T11:00:00")
    flow_pressure_corr = analyzer.correlation("FT-101", "PT-101", "2026-08-18T10:15:00", "2026-08-18T11:00:00")
    latest = {record["tag"]: record for record in analyzer.latest_values()}
    anomalies = {item["type"]: item for item in analyzer.detect_basic_anomalies()}
    restriction = anomalies.get("downstream_restriction")
    incident_detected = restriction is not None
    critical_incident = bool(restriction and restriction["severity"] == "alarm")
    incident_label = (
        "Critical incident window 10:15–11:00"
        if critical_incident
        else "Incident window 10:15–11:00"
        if incident_detected
        else "No abnormal window detected"
    )

    if intent == "status":
        affected_path = []
        confidence, severity, window = 0.98, "normal", "Current snapshot · 14:00"
        if incident_detected:
            title = "Transfer process has recovered after a critical event" if critical_incident else "Transfer process has recovered to its normal envelope"
            explanation = (
                f"At {latest['FT-101']['timestamp'][11:16]}, FT-101 is {latest['FT-101']['value']:.1f} m3/h and "
                f"PT-101 is {latest['PT-101']['value']:.2f} bar, both inside their expected ranges. "
                f"An {'alarm-level ' if critical_incident else ''}restriction pattern was detected earlier from 10:15–11:00; "
                "no active process alarm remains in the latest readings."
            )
            root_children += ["kpis", "timeline", "diagram"]
            components.extend(
                [
                    _component("kpis", "KpiGrid", title="Current readings", cards=_latest_kpis(analyzer)),
                    _component("timeline", "IncidentTimeline", title="Earlier detected event", events=analyzer.incident_timeline()),
                    _component("diagram", "ProcessDiagram", title="Transfer route", highlightedTags=[], status="normal"),
                ]
            )
        else:
            title = "The transfer process is stable and inside its normal envelope"
            explanation = (
                f"At {latest['FT-101']['timestamp'][11:16]}, FT-101 is {latest['FT-101']['value']:.1f} m3/h and "
                f"PT-101 is {latest['PT-101']['value']:.2f} bar. All monitored values remain inside their expected ranges, "
                "and no abnormal process or signal-quality pattern was detected in the six-hour window."
            )
            root_children += ["kpis", "diagram"]
            components.extend(
                [
                    _component("kpis", "KpiGrid", title="Healthy current readings", cards=_latest_kpis(analyzer)),
                    _component("diagram", "ProcessDiagram", title="Normal transfer route", highlightedTags=[], status="normal"),
                ]
            )
    elif intent == "sensor_quality":
        problems = analyzer.quality_problems()
        if problems:
            affected_samples = sum(problem["count"] for problem in problems)
            first = min(problem["first"] for problem in problems)
            last = max(problem["last"] for problem in problems)
            problem_tags = [problem["tag"] for problem in problems]
            title = f"{len(problems)} historian signals contain unreliable readings"
            explanation = (
                f"{', '.join(problem_tags)} contain {affected_samples} readings marked BAD, SUSPECT, or MISSING between "
                f"{first[11:16]} and {last[11:16]}. Those values are excluded from calculations; conclusions in that window "
                "should be treated with lower confidence."
            )
            confidence, severity, window = 1.0, "data", f"{first[11:16]}–{last[11:16]}"
            affected_path = problem_tags
            root_children += ["quality", "equipment"]
            components.extend(
                [
                    _component("quality", "SensorQualityWarning", title="Data quality limitations", problems=problems),
                    _component("equipment", "EquipmentTable", title="Signals requiring review", rows=[
                        {"tag": problem["tag"], "type": analyzer.nodes[problem["tag"]]["label"], "status": ", ".join(problem["qualities"]), "detail": f"{problem['count']} affected samples"}
                        for problem in problems
                    ]),
                ]
            )
        else:
            drift = anomalies.get("sensor_drift")
            if drift:
                title = "Source quality flags are clean, but LT-102 looks unstable"
                explanation = (
                    "All six signals are complete and marked GOOD, but LT-102 changes more sharply than expected. "
                    "That behavior should be reviewed even though the historian did not flag it."
                )
                confidence, affected_path = 0.87, ["LT-102"]
            else:
                title = "All historian signals are complete, stable, and marked GOOD"
                explanation = (
                    "The six operating signals have full time coverage, no missing values, no weak source-quality flags, "
                    "and no unstable signal pattern in the reviewed window."
                )
                confidence, affected_path = 0.99, []
            severity, window = "normal", "Full window · 08:00–14:00"
            root_children += ["kpis"]
            components.append(_component("kpis", "KpiGrid", title="Latest readings and source quality", cards=_latest_kpis(analyzer)))
    elif intent == "trend":
        window = "09:45–11:15"
        if incident_detected:
            title = "Pressure reached alarm level as transfer flow collapsed" if critical_incident else "Pressure rose as transfer flow fell between 10:15 and 11:00"
            explanation = (
                f"FT-101 dropped to {flow_stats['min']:.1f} m3/h while PT-101 reached "
                f"{pressure_stats['max']:.2f} bar. Their correlation is {flow_pressure_corr:.2f}, showing a strong inverse relationship."
            )
            confidence, severity = restriction["confidence"], "alarm" if critical_incident else "warning"
            affected_path = ["P-101", "PT-101", "FT-101", "FV-101"]
            root_children += ["trend", "timeline"]
            components.extend(
                [
                    _component("trend", "TrendChart", title="Pressure, flow, and tank levels", subtitle="3-minute samples · shaded incident window", series=analyzer.chart_series("2026-08-18T09:45:00", "2026-08-18T11:15:00"), incidentStart="10:15", incidentEnd="11:00", incidentLabel=incident_label),
                    _component("timeline", "IncidentTimeline", title="Signal sequence", events=analyzer.incident_timeline()),
                ]
            )
        else:
            title = "Pressure and transfer flow remained stable"
            explanation = (
                f"FT-101 stayed between {flow_stats['min']:.1f} and {flow_stats['max']:.1f} m3/h while PT-101 remained "
                f"between {pressure_stats['min']:.2f} and {pressure_stats['max']:.2f} bar. No threshold excursion or abnormal trend was detected."
            )
            confidence, severity, affected_path = 0.99, "normal", []
            root_children += ["trend"]
            components.append(_component("trend", "TrendChart", title="Stable pressure, flow, and tank levels", subtitle="3-minute samples · full healthy window", series=analyzer.chart_series("2026-08-18T09:45:00", "2026-08-18T11:15:00"), incidentStart="", incidentEnd="", incidentLabel=incident_label))
    else:
        if not incident_detected:
            title = "No abnormal level increase or restriction pattern was detected"
            explanation = (
                f"Between 10:15 and 11:00, FT-101 stayed near {flow_stats['mean']:.1f} m3/h, PT-101 stayed near "
                f"{pressure_stats['mean']:.2f} bar, and LT-101 changed only {level_stats['rate_per_hour']:.2f}%/h. "
                "The healthy dataset does not contain evidence of a process upset to diagnose."
            )
            confidence, severity, window, affected_path = 0.99, "normal", "Reviewed window · 10:15–11:00", []
            root_children += ["kpis", "trend", "diagram"]
            components.extend(
                [
                    _component("kpis", "KpiGrid", title="Healthy readings at 10:52", cards=_incident_kpis(analyzer)),
                    _component("trend", "TrendChart", title="Stable process response", subtitle="3-minute samples · no incident detected", series=analyzer.chart_series("2026-08-18T09:45:00", "2026-08-18T11:15:00"), incidentStart="", incidentEnd="", incidentLabel=incident_label),
                    _component("diagram", "ProcessDiagram", title="Normal process path", highlightedTags=[], status="normal"),
                ]
            )
        else:
            title = "An alarm-level downstream restriction is the leading explanation" if critical_incident else "A downstream restriction is the most likely explanation"
            explanation = (
                f"From 10:15–11:00, FT-101 fell to {flow_stats['min']:.1f} m3/h (expected 42–54) while "
                f"PT-101 rose to {pressure_stats['max']:.2f} bar (expected 2.6–4.2) and LT-101 climbed at "
                f"{level_stats['rate_per_hour']:.1f}%/h. With P-101 running and FV-101 commanded open, the combined evidence is "
                "consistent with a restriction near or downstream of FV-101. Field inspection is required to confirm; the data does not prove a specific mechanical cause."
            )
            confidence = restriction["confidence"]
            severity = "alarm" if critical_incident else "warning"
            window = "Critical window · 10:15–11:00" if critical_incident else "Incident window · 10:15–11:00"
            affected_path = ["T-101", "P-101", "PT-101", "FT-101", "FV-101"]
            if intent == "process_path":
                root_children += ["diagram", "equipment"]
            elif intent == "inspection":
                root_children += ["diagram", "inspection", "equipment"]
            else:
                root_children += ["kpis", "trend", "timeline", "diagram", "inspection"]

            if "kpis" in root_children:
                components.append(_component("kpis", "KpiGrid", title="Evidence at 10:52", cards=_incident_kpis(analyzer)))
            if "trend" in root_children:
                components.append(_component("trend", "TrendChart", title="Correlated process response", subtitle="3-minute samples · shaded incident window", series=analyzer.chart_series("2026-08-18T09:45:00", "2026-08-18T11:15:00"), incidentStart="10:15", incidentEnd="11:00", incidentLabel=incident_label))
            if "timeline" in root_children:
                components.append(_component("timeline", "IncidentTimeline", title="Incident timeline", events=analyzer.incident_timeline()))
            if "diagram" in root_children:
                components.append(_component("diagram", "ProcessDiagram", title="Affected process path", highlightedTags=affected_path, status="alarm" if critical_incident else "warning"))
            if "inspection" in root_children:
                components.append(
                    _component("inspection", "InspectionPanel", title="Suggested field checks", confidence=confidence, items=[
                        {"priority": "1", "tag": "FV-101", "text": "Verify actual valve travel against FV-101_POS and inspect for fouling or obstruction."},
                        {"priority": "2", "tag": "P-101", "text": "Check discharge-side isolation and listen for abnormal hydraulic noise; do not change operation from this prototype."},
                        {"priority": "3", "tag": "L-101", "text": "Inspect the line segment downstream of FT-101 for a partial blockage or closed manual valve."},
                    ])
                )
            if "equipment" in root_children:
                components.append(
                    _component("equipment", "EquipmentTable", title="Affected tags", rows=[
                        {"tag": "P-101", "type": "Centrifugal pump", "status": "Running", "detail": "Discharge pressure reached alarm level" if critical_incident else "Discharge pressure elevated"},
                        {"tag": "FV-101", "type": "Flow control valve", "status": "Commanded open", "detail": "Inspect valve and downstream line"},
                        {"tag": "FT-101", "type": "Flow transmitter", "status": "Alarm-low flow" if critical_incident else "Low flow", "detail": "Good quality during event"},
                    ])
                )

    incident_quality = analyzer.window_quality(
        ["LT-101", "PT-101", "FT-101", "FV-101_POS"],
        "2026-08-18T10:15:00",
        "2026-08-18T11:00:00",
    )
    components.insert(
        0,
        _component(
            "summary", "OperationalSummary", title=title, explanation=explanation, severity=severity,
            confidence=confidence, window=window, tags=affected_path,
            qualityNote=(
                "No bad-quality samples overlap the 10:15–11:00 incident window."
                if incident_detected and intent not in {"status", "sensor_quality"} and incident_quality == 100
                else f"Incident-window evidence quality is {incident_quality}%."
                if incident_detected and intent not in {"status", "sensor_quality"}
                else ""
            ),
        ),
    )
    components.insert(0, _component("root", "ResponseLayout", children=root_children, intent=intent, question=question))

    messages = [
        {"version": "v0.9", "createSurface": {"surfaceId": surface_id, "catalogId": CATALOG_ID, "sendDataModel": False}},
        {"version": "v0.9", "updateComponents": {"surfaceId": surface_id, "components": components}},
        {"version": "v0.9", "updateDataModel": {"surfaceId": surface_id, "path": "/", "value": {"question": question, "intent": intent, "generatedFrom": "deterministic-analysis-tools"}}},
    ]
    validate_payload(messages)
    return {
        "question": question,
        "intent": intent,
        "surfaceId": surface_id,
        "messages": messages,
        "answer": {
            "title": title,
            "text": explanation,
            "confidence": confidence,
            "severity": severity,
            "window": window,
        },
        "evidence": {
            "flow": flow_stats,
            "pressure": pressure_stats,
            "feedLevel": level_stats,
            "flowPressureCorrelation": flow_pressure_corr,
        },
        "metadata": {"protocol": "A2UI v0.9.1", "catalogId": CATALOG_ID, "advisoryOnly": True, "dataThrough": analyzer.records[-1]["timestamp"]},
    }


def validate_payload(messages: list[dict[str, Any]]) -> None:
    """Validate ordering, envelope shape, catalog restriction, and tree integrity."""
    if len(messages) < 2 or "createSurface" not in messages[0] or "updateComponents" not in messages[1]:
        raise ValueError("A2UI stream must create a surface before updating components")
    if any(message.get("version") != "v0.9" for message in messages):
        raise ValueError("All messages must declare A2UI v0.9")
    surface_id = messages[0]["createSurface"]["surfaceId"]
    if not re.fullmatch(r"[A-Za-z0-9._-]+", surface_id):
        raise ValueError("Unsafe surface id")
    if messages[0]["createSurface"]["catalogId"] != CATALOG_ID:
        raise ValueError("Unapproved A2UI catalog")
    components = messages[1]["updateComponents"]["components"]
    ids = {component.get("id") for component in components}
    if "root" not in ids or None in ids or len(ids) != len(components):
        raise ValueError("Component tree requires unique IDs and a root component")
    if any(component.get("component") not in ALLOWED_COMPONENTS for component in components):
        raise ValueError("Payload contains a component outside the approved catalog")
    root = next(component for component in components if component["id"] == "root")
    missing = set(root.get("children", [])) - ids
    if missing:
        raise ValueError(f"Root references missing components: {sorted(missing)}")
    # The official A2UI Agent SDK validates the v0.9.1 envelope, custom catalog,
    # component schemas, references, and tree topology.
    _official_a2ui_format().parser.compile(json.dumps(messages))
