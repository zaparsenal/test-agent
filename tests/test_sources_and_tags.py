from pathlib import Path

from backend.adapters import DexpiXmlAdapter, JsonTopologyAdapter, SvgPidAdapter

ROOT = Path(__file__).resolve().parents[1]


def test_working_pid_and_dcs_tags_are_consistent():
    graph = JsonTopologyAdapter().load(ROOT / "data" / "plant" / "topology.json")
    svg = SvgPidAdapter().load(ROOT / "data" / "plant" / "tank_transfer_pid.svg")
    graph_tags = {node["tag"] for node in graph["nodes"]}
    svg_tags = {node["tag"] for node in svg["nodes"]}
    assert {"T-101", "P-101", "FT-101", "FV-101", "T-102", "LT-101", "LT-102", "PT-101"} <= graph_tags & svg_tags


def test_public_dexpi_reference_is_parseable():
    inventory = DexpiXmlAdapter().load(ROOT / "data" / "raw" / "dexpi" / "C01V04-VER.EX01.xml")
    assert inventory["nodes"]
    assert any(node["class"] for node in inventory["nodes"])


def test_open_pfd_reference_and_pid_license_are_retained():
    assert (ROOT / "data" / "raw" / "dexpi" / "DEXPI-Process-1.0-Manual.pdf").exists()
    license_text = (ROOT / "data" / "raw" / "dexpi" / "LICENSE-CC-BY-4.0.txt").read_text()
    assert "Creative Commons Attribution 4.0" in license_text
