from pathlib import PureWindowsPath

from fastapi.testclient import TestClient

from backend.a2ui_payload import ALLOWED_COMPONENTS, _catalog_config_for_path, validate_payload
from backend.app import app


def demo_client() -> TestClient:
    client = TestClient(app)
    client.delete("/api/inputs")
    loaded = client.post("/api/inputs/demo")
    assert loaded.status_code == 200
    assert loaded.json()["analysisReady"] is True
    return client


def test_windows_catalog_path_is_treated_as_a_file_path():
    windows_path = PureWindowsPath(
        r"D:\BKP\Projects\A2UI\FieldGuide\test-agent\backend\industrial_catalog.json"
    )
    config = _catalog_config_for_path(windows_path)
    assert config.provider.path == str(windows_path)


def test_agent_to_a2ui_workflow():
    response = demo_client().post("/api/query", json={"question": "Why is T-101's level increasing?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "root_cause"
    validate_payload(payload["messages"])
    components = payload["messages"][1]["updateComponents"]["components"]
    types = {component["component"] for component in components}
    assert types <= ALLOWED_COMPONENTS
    assert {"OperationalSummary", "KpiGrid", "TrendChart", "IncidentTimeline", "ProcessDiagram", "InspectionPanel"} <= types
    summary = next(component for component in components if component["component"] == "OperationalSummary")
    assert "FT-101" in summary["explanation"]
    assert "PT-101" in summary["explanation"]
    assert "restriction" in summary["title"].lower()
    assert payload["answer"]["text"] == summary["explanation"]


def test_layout_changes_for_quality_question():
    payload = demo_client().post("/api/query", json={"question": "Are any sensors unreliable?"}).json()
    types = {item["component"] for item in payload["messages"][1]["updateComponents"]["components"]}
    assert payload["intent"] == "sensor_quality"
    assert {"SensorQualityWarning", "EquipmentTable"} <= types
    assert "TrendChart" not in types


def test_each_demo_intent_returns_a_valid_specialized_surface():
    cases = [
        ("What is happening in the process right now?", "status", "KpiGrid"),
        ("Show me pressure and flow around the incident.", "trend", "TrendChart"),
        ("Which equipment should be inspected?", "inspection", "InspectionPanel"),
        ("Show the P&ID process path.", "process_path", "ProcessDiagram"),
    ]
    client = demo_client()
    for question, intent, required_component in cases:
        response = client.post("/api/query", json={"question": question})
        assert response.status_code == 200
        payload = response.json()
        validate_payload(payload["messages"])
        types = {item["component"] for item in payload["messages"][1]["updateComponents"]["components"]}
        assert payload["intent"] == intent
        assert required_component in types
