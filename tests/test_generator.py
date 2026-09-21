from scripts.generate_dcs import generate


def test_generator_is_deterministic():
    assert generate(seed=101) == generate(seed=101)
    assert generate(seed=101) != generate(seed=202)


def test_generator_covers_six_hours_and_all_signals():
    records = generate(seed=101)
    assert records[0]["timestamp"] == "2026-08-18T08:00:00"
    assert records[-1]["timestamp"] == "2026-08-18T14:00:00"
    assert {record["tag"] for record in records} == {"LT-101", "LT-102", "PT-101", "FT-101", "P-101_STATUS", "FV-101_POS"}


def test_healthy_comparison_scenario_is_stable_and_keeps_all_source_quality_flags_good():
    records = generate(seed=202, scenario="healthy")
    assert all(record["quality"] == "GOOD" and record["value"] is not None for record in records)
    by_tag = {tag: [float(record["value"]) for record in records if record["tag"] == tag] for tag in {record["tag"] for record in records}}
    assert min(by_tag["FT-101"]) > 42
    assert max(by_tag["PT-101"]) < 4.2
