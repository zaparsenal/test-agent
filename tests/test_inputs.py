from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import app


ROOT = Path(__file__).resolve().parents[1]


def test_analysis_requires_inspected_inputs():
    client = TestClient(app)
    cleared = client.delete("/api/inputs")
    assert cleared.status_code == 200
    assert cleared.json()["analysisReady"] is False

    response = client.post("/api/query", json={"question": "What is happening?"})
    assert response.status_code == 409
    assert "inputs" in response.json()["detail"].lower()


def test_sample_inputs_are_parsed_and_visible():
    client = TestClient(app)
    client.delete("/api/inputs")
    payload = client.post("/api/inputs/demo").json()

    assert payload["analysisReady"] is True
    assert payload["diagram"]["tagCount"] >= 5
    assert payload["dcs"]["rowCount"] == 2166
    assert payload["dcs"]["timeRange"] == {
        "start": "2026-08-18T08:00:00",
        "end": "2026-08-18T14:00:00",
    }
    assert payload["dcs"]["sampleRows"]


def test_uploaded_historian_is_used_by_analysis():
    client = TestClient(app)
    client.delete("/api/inputs")
    diagram = ROOT / "data" / "plant" / "tank_transfer_pid.svg"
    dcs = ROOT / "data" / "generated" / "dcs_readings.csv"

    diagram_result = client.post(
        "/api/inputs/inspect",
        json={"kind": "diagram", "name": diagram.name, "content": diagram.read_text(), "sizeBytes": diagram.stat().st_size},
    )
    assert diagram_result.status_code == 200
    dcs_result = client.post(
        "/api/inputs/inspect",
        json={"kind": "dcs", "name": dcs.name, "content": dcs.read_text(), "sizeBytes": dcs.stat().st_size},
    )
    assert dcs_result.status_code == 200
    assert dcs_result.json()["analysisReady"] is True

    response = client.post("/api/query", json={"question": "Show pressure and flow during the event."})
    assert response.status_code == 200
    assert response.json()["intent"] == "trend"
