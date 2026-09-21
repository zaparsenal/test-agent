"""In-memory input ingestion and inspection for the local demonstration."""

from __future__ import annotations

import csv
import io
import json
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from backend.analysis import ProcessAnalyzer, ROOT

REQUIRED_PROCESS_TAGS = {"T-101", "P-101", "FT-101", "FV-101", "T-102"}
REQUIRED_DCS_TAGS = {"LT-101", "LT-102", "PT-101", "FT-101", "P-101_STATUS", "FV-101_POS"}
DEMO_WINDOW_START = datetime.fromisoformat("2026-08-18T08:00:00")
DEMO_WINDOW_END = datetime.fromisoformat("2026-08-18T14:00:00")


class InputSession:
    """Hold inspected inputs for one local demo process.

    Files are parsed in memory and are not written to disk. The prototype's
    deterministic event logic expects the documented six-hour demo schema.
    """

    def __init__(self, root: Path = ROOT):
        self.root = root
        self.default_analyzer = ProcessAnalyzer(root)
        self.analyzer = self.default_analyzer
        self.diagram: dict[str, Any] | None = None
        self.dcs: dict[str, Any] | None = None
        self._topology: dict[str, Any] | None = None
        self._records: list[dict[str, Any]] | None = None

    def clear(self) -> dict[str, Any]:
        self.diagram = None
        self.dcs = None
        self._topology = None
        self._records = None
        self.analyzer = self.default_analyzer
        return self.status()

    def load_demo(self, scenario: Literal["critical", "healthy"] = "critical") -> dict[str, Any]:
        diagram_path = self.root / "data" / "sample-inputs" / "process-diagram" / "tank_transfer_pid.svg"
        dcs_name = "dcs_readings_clean.csv" if scenario == "healthy" else "dcs_readings.csv"
        dcs_path = self.root / "data" / "sample-inputs" / "dcs" / dcs_name
        self.inspect("diagram", diagram_path.name, diagram_path.read_text(), diagram_path.stat().st_size, "sample")
        self.inspect("dcs", dcs_path.name, dcs_path.read_text(), dcs_path.stat().st_size, "sample")
        return self.status()

    def inspect(
        self,
        kind: Literal["diagram", "dcs"],
        name: str,
        content: str,
        size_bytes: int,
        origin: str = "upload",
    ) -> dict[str, Any]:
        if not content.strip():
            raise ValueError("The selected file is empty")
        if len(content.encode("utf-8")) > 8_000_000:
            raise ValueError("The prototype accepts text-based files up to 8 MB")
        if kind == "diagram":
            self.diagram, self._topology = self._inspect_diagram(name, content, size_bytes, origin)
        else:
            self.dcs, self._records = self._inspect_dcs(name, content, size_bytes, origin)
        self._rebuild_analyzer()
        return self.status()

    def _inspect_diagram(
        self, name: str, content: str, size_bytes: int, origin: str
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        suffix = Path(name).suffix.lower()
        topology = None
        tags: set[str] = set()
        node_count = 0
        edge_count = 0

        if suffix == ".json":
            candidate = json.loads(content)
            if not {"nodes", "edges", "process_path"}.issubset(candidate):
                raise ValueError("Topology JSON must contain nodes, edges, and process_path")
            topology = candidate
            tags = {str(node.get("tag")) for node in candidate["nodes"] if node.get("tag")}
            node_count = len(candidate["nodes"])
            edge_count = len(candidate["edges"])
            file_type = "Normalized topology JSON"
        elif suffix in {".svg", ".xml", ".dexpi"}:
            root = ET.fromstring(content)
            svg_tags = {element.attrib["data-tag"] for element in root.iter() if element.attrib.get("data-tag")}
            if svg_tags:
                tags = svg_tags
                node_count = len(svg_tags)
                file_type = "Tagged SVG diagram"
            else:
                components = [element for element in root.iter() if element.attrib.get("ComponentClass")]
                for element in components:
                    for child in element.iter():
                        if child.attrib.get("Name") in {"TagNameAssignmentClass", "SubTagNameAssignmentClass"} and child.attrib.get("Value"):
                            tags.add(child.attrib["Value"])
                            break
                node_count = len(components)
                file_type = "DEXPI / Proteus XML"
        else:
            raise ValueError("Use a DEXPI XML, tagged SVG, or normalized topology JSON file")

        compatible = REQUIRED_PROCESS_TAGS <= tags
        metadata = {
            "kind": "diagram",
            "name": Path(name).name,
            "fileType": file_type,
            "sizeBytes": size_bytes,
            "origin": origin,
            "status": "ready" if compatible else "inspected",
            "compatible": compatible,
            "nodeCount": node_count,
            "edgeCount": edge_count,
            "tags": sorted(tags)[:40],
            "tagCount": len(tags),
            "note": (
                "Required transfer equipment was found and mapped to the analysis model."
                if compatible
                else "The file was parsed, but the required T-101 transfer tags were not all found."
            ),
        }
        return metadata, topology

    def _inspect_dcs(
        self, name: str, content: str, size_bytes: int, origin: str
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        suffix = Path(name).suffix.lower()
        if suffix == ".csv":
            raw_records = list(csv.DictReader(io.StringIO(content)))
            file_type = "DCS historian CSV"
        elif suffix == ".json":
            parsed = json.loads(content)
            raw_records = parsed.get("records", []) if isinstance(parsed, dict) else parsed
            file_type = "DCS historian JSON"
        else:
            raise ValueError("Use a CSV or JSON historian export")

        if not isinstance(raw_records, list) or not raw_records:
            raise ValueError("No historian records were found")
        if len(raw_records) > 50_000:
            raise ValueError("The prototype accepts up to 50,000 historian rows")

        records: list[dict[str, Any]] = []
        for index, raw in enumerate(raw_records, start=1):
            if not isinstance(raw, dict) or not raw.get("timestamp") or not raw.get("tag"):
                raise ValueError(f"Historian row {index} is missing timestamp or tag")
            try:
                timestamp = datetime.fromisoformat(str(raw["timestamp"]))
            except ValueError as exc:
                raise ValueError(f"Historian row {index} has an invalid ISO timestamp") from exc
            raw_value = raw.get("value")
            value = None if raw_value in {None, "", "null", "None"} else float(raw_value)
            quality = str(raw.get("quality") or "GOOD").upper()
            records.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "tag": str(raw["tag"]),
                    "value": value,
                    "unit": str(raw.get("unit") or ""),
                    "quality": quality,
                    "alarm_state": str(raw.get("alarm_state") or "NORMAL"),
                }
            )

        records.sort(key=lambda item: (item["timestamp"], item["tag"]))
        tags = sorted({record["tag"] for record in records})
        start = datetime.fromisoformat(records[0]["timestamp"])
        end = datetime.fromisoformat(records[-1]["timestamp"])
        compatible = REQUIRED_DCS_TAGS <= set(tags) and start <= DEMO_WINDOW_START and end >= DEMO_WINDOW_END
        quality_counts = Counter(record["quality"] for record in records)
        metadata = {
            "kind": "dcs",
            "name": Path(name).name,
            "fileType": file_type,
            "sizeBytes": size_bytes,
            "origin": origin,
            "status": "ready" if compatible else "inspected",
            "compatible": compatible,
            "rowCount": len(records),
            "tagCount": len(tags),
            "tags": tags,
            "timeRange": {"start": records[0]["timestamp"], "end": records[-1]["timestamp"]},
            "qualityCounts": dict(sorted(quality_counts.items())),
            "sampleRows": records[:6],
            "note": (
                "Required tags and the six-hour demonstration window are available."
                if compatible
                else "The file was parsed, but it does not match all required demo tags and timestamps."
            ),
        }
        return metadata, records

    def _rebuild_analyzer(self) -> None:
        if not self.diagram or not self.dcs or not self.diagram["compatible"] or not self.dcs["compatible"] or self._records is None:
            self.analyzer = self.default_analyzer
            return
        topology = self._topology or self.default_analyzer.topology
        self.analyzer = ProcessAnalyzer(self.root, topology=topology, records=self._records)

    def status(self) -> dict[str, Any]:
        ready = bool(
            self.diagram
            and self.dcs
            and self.diagram.get("compatible")
            and self.dcs.get("compatible")
        )
        return {
            "diagram": self.diagram,
            "dcs": self.dcs,
            "analysisReady": ready,
            "qualityReview": self.analyzer.data_review() if ready else None,
            "message": (
                "Both inputs are parsed and ready for analysis."
                if ready
                else "Add a compatible process diagram and DCS export to continue."
            ),
        }
