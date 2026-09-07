from backend.analysis import ProcessAnalyzer


def test_upstream_and_downstream_topology_queries():
    analyzer = ProcessAnalyzer()
    assert analyzer.connected_equipment("P-101", "downstream") == ["FT-101", "FV-101", "T-102"]
    assert analyzer.connected_equipment("FV-101", "upstream") == ["FT-101", "P-101", "T-101"]
    assert "FV-101" in analyzer.connected_equipment("PT-101", "downstream")


def test_restriction_rates_and_thresholds_are_detected():
    analyzer = ProcessAnalyzer()
    start, end = "2026-08-18T10:15:00", "2026-08-18T11:00:00"
    assert analyzer.statistics("FT-101", start, end)["rate_per_hour"] < -15
    assert analyzer.statistics("PT-101", start, end)["rate_per_hour"] > 2
    assert analyzer.statistics("LT-101", start, end)["rate_per_hour"] > 15
    violated_tags = {item["tag"] for item in analyzer.threshold_violations(["FT-101", "PT-101", "LT-101"])}
    assert violated_tags == {"FT-101", "PT-101", "LT-101"}


def test_quality_problems_and_missing_values_are_reported():
    problems = {item["tag"]: item for item in ProcessAnalyzer().quality_problems()}
    assert "BAD" in problems["PT-101"]["qualities"]
    assert "MISSING" in problems["FT-101"]["qualities"]


def test_timeline_is_ordered():
    events = ProcessAnalyzer().incident_timeline()
    timestamps = [event["timestamp"] for event in events]
    assert len(events) >= 3
    assert timestamps == sorted(timestamps)


def test_detected_incident_types_cover_the_scenario():
    detected = {item["type"] for item in ProcessAnalyzer().detect_basic_anomalies()}
    assert {"startup", "downstream_restriction", "sensor_drift", "bad_quality", "recovery"} <= detected
