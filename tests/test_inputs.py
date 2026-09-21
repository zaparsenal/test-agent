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
    assert payload["qualityReview"]["score"] == 85
    assert [item["id"] for item in payload["qualityReview"]["issues"]] == [
        "restriction-pattern",
        "historian-quality",
        "sensor-drift",
    ]
    assert payload["qualityReview"]["issueCounts"] == {
        "critical": 1,
        "high": 1,
        "medium": 1,
        "low": 0,
    }


def test_healthy_sample_is_available_as_a_second_demo_option():
    client = TestClient(app)
    client.delete("/api/inputs")
    payload = client.post("/api/inputs/demo?scenario=healthy").json()

    assert payload["analysisReady"] is True
    assert payload["dcs"]["name"] == "dcs_readings_clean.csv"
    assert payload["qualityReview"]["score"] == 100
    assert payload["qualityReview"]["weakSampleCount"] == 0
    assert payload["qualityReview"]["issues"] == []

    response = client.post("/api/query", json={"question": "Which sensor readings are unreliable?"})
    assert response.status_code == 200
    assert response.json()["answer"]["severity"] == "normal"
    assert "complete, stable" in response.json()["answer"]["title"]

    diagnosis = client.post("/api/query", json={"question": "Why did T-101's level increase?"})
    assert diagnosis.status_code == 200
    assert diagnosis.json()["answer"]["severity"] == "normal"
    assert "No abnormal" in diagnosis.json()["answer"]["title"]


def test_uploaded_historian_is_used_by_analysis():
    client = TestClient(app)
    client.delete("/api/inputs")
    diagram = ROOT / "data" / "sample-inputs" / "process-diagram" / "tank_transfer_pid.svg"
    dcs = ROOT / "data" / "sample-inputs" / "dcs" / "dcs_readings.csv"

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
