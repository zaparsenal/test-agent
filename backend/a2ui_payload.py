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

    if intent == "status":
        title = "Transfer process has recovered to its normal envelope"
        explanation = (
            f"At {latest['FT-101']['timestamp'][11:16]}, FT-101 is {latest['FT-101']['value']:.1f} m3/h and "
            f"PT-101 is {latest['PT-101']['value']:.2f} bar, both inside their expected ranges. "
            "A restriction-like event was detected earlier from 10:15–11:00; no active process alarm remains."
        )
        confidence, severity, window = 0.93, "normal", "Current snapshot · 14:00"
        affected_path = []
        root_children += ["kpis", "timeline", "diagram"]
        components.extend(
            [
                _component("kpis", "KpiGrid", title="Current readings", cards=_latest_kpis(analyzer)),
                _component("timeline", "IncidentTimeline", title="Earlier detected event", events=analyzer.incident_timeline()),
                _component("diagram", "ProcessDiagram", title="Transfer route", highlightedTags=[], status="normal"),
            ]
        )
    elif intent == "sensor_quality":
        problems = analyzer.quality_problems()
        title = "Two historian signals were unreliable for a limited window"
        explanation = (
            "PT-101 contains bad-quality values and FT-101 contains missing samples between 11:45–12:15. "
            "Those values are excluded from calculations; conclusions in that window should be treated with lower confidence."
        )
        confidence, severity, window = 0.99, "data", "11:45–12:15"
        affected_path = [problem["tag"] for problem in problems]
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
    elif intent == "trend":
        title = "Pressure rose as transfer flow fell between 10:15 and 11:00"
        explanation = (
            f"FT-101 dropped from the normal range toward {flow_stats['min']:.1f} m3/h while PT-101 reached "
            f"{pressure_stats['max']:.2f} bar. Their correlation is {flow_pressure_corr:.2f}, showing a strong inverse relationship."
        )
        confidence, severity, window = 0.91, "warning", "09:45–11:15"
        affected_path = ["P-101", "PT-101", "FT-101", "FV-101"]
        root_children += ["trend", "timeline"]
        components.extend(
            [
                _component("trend", "TrendChart", title="Pressure, flow, and tank levels", subtitle="3-minute samples · shaded incident window", series=analyzer.chart_series("2026-08-18T09:45:00", "2026-08-18T11:15:00"), incidentStart="10:15", incidentEnd="11:00"),
                _component("timeline", "IncidentTimeline", title="Signal sequence", events=analyzer.incident_timeline()),
            ]
        )
    else:
        title = "A downstream restriction is the most likely explanation"
        explanation = (
            f"From 10:15–11:00, FT-101 fell to {flow_stats['min']:.1f} m3/h (expected 42–54) while "
            f"PT-101 rose to {pressure_stats['max']:.2f} bar (expected 2.6–4.2) and LT-101 climbed at "
            f"{level_stats['rate_per_hour']:.1f}%/h. With P-101 running and FV-101 commanded open, the combined evidence is "
            "consistent with a restriction near or downstream of FV-101. Field inspection is required to confirm; the data does not prove a specific mechanical cause."
        )
        confidence, severity, window = 0.84, "warning", "Incident window · 10:15–11:00"
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
            components.append(_component("trend", "TrendChart", title="Correlated process response", subtitle="3-minute samples · shaded incident window", series=analyzer.chart_series("2026-08-18T09:45:00", "2026-08-18T11:15:00"), incidentStart="10:15", incidentEnd="11:00"))
        if "timeline" in root_children:
            components.append(_component("timeline", "IncidentTimeline", title="Incident timeline", events=analyzer.incident_timeline()))
        if "diagram" in root_children:
            components.append(_component("diagram", "ProcessDiagram", title="Affected process path", highlightedTags=affected_path, status="warning"))
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
                    {"tag": "P-101", "type": "Centrifugal pump", "status": "Running", "detail": "Discharge pressure elevated"},
                    {"tag": "FV-101", "type": "Flow control valve", "status": "82% open", "detail": "Inspect valve and downstream line"},
                    {"tag": "FT-101", "type": "Flow transmitter", "status": "Low flow", "detail": "Good quality during event"},
                ])
            )

    components.insert(
        0,
        _component(
            "summary", "OperationalSummary", title=title, explanation=explanation, severity=severity,
            confidence=confidence, window=window, tags=affected_path,
            qualityNote="No bad-quality samples overlap the 10:15–11:00 incident window." if intent not in {"status", "sensor_quality"} else "",
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
        "metadata": {"protocol": "A2UI v0.9.1", "catalogId": CATALOG_ID, "advisoryOnly": True, "dataThrough": "2026-08-18T14:00:00"},
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
