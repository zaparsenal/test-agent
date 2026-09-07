from scripts.generate_dcs import generate


def test_generator_is_deterministic():
    assert generate(seed=101) == generate(seed=101)
    assert generate(seed=101) != generate(seed=202)


def test_generator_covers_six_hours_and_all_signals():
    records = generate(seed=101)
    assert records[0]["timestamp"] == "2026-08-18T08:00:00"
    assert records[-1]["timestamp"] == "2026-08-18T14:00:00"
    assert {record["tag"] for record in records} == {"LT-101", "LT-102", "PT-101", "FT-101", "P-101_STATUS", "FV-101_POS"}

