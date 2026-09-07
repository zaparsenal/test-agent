"""Plant-structure ingestion adapters for JSON, SVG, and DEXPI/Proteus XML."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class PlantStructureAdapter(ABC):
    """Boundary for converting a diagram source into a normalized plant graph."""

    @abstractmethod
    def load(self, source: Path) -> dict[str, Any]:
        raise NotImplementedError


class JsonTopologyAdapter(PlantStructureAdapter):
    def load(self, source: Path) -> dict[str, Any]:
        graph = json.loads(source.read_text())
        if not {"nodes", "edges", "process_path"}.issubset(graph):
            raise ValueError("Normalized topology JSON is missing graph fields")
        return graph


class SvgPidAdapter(PlantStructureAdapter):
    """Extract tag-bearing SVG nodes; connections remain source-specific metadata."""

    def load(self, source: Path) -> dict[str, Any]:
        root = ET.parse(source).getroot()
        tagged = []
        for element in root.iter():
            tag = element.attrib.get("data-tag")
            if tag:
                tagged.append({"tag": tag, "kind": "diagram_element", "svg_id": element.attrib.get("id")})
        return {"schema_version": "1.0", "source": str(source), "nodes": tagged, "edges": [], "process_path": []}


class DexpiXmlAdapter(PlantStructureAdapter):
    """Conservative DEXPI/Proteus reader that inventories classes and assigned tags.

    Full connectivity mapping is deliberately left behind this interface because DEXPI
    versions and vendor exports differ. The original reference file is never rewritten.
    """

    def load(self, source: Path) -> dict[str, Any]:
        root = ET.parse(source).getroot()
        nodes = []
        for element in root.iter():
            component_class = element.attrib.get("ComponentClass")
            if not component_class:
                continue
            assigned_tag = None
            for child in element.iter():
                name = child.attrib.get("Name", "")
                if name in {"TagNameAssignmentClass", "SubTagNameAssignmentClass"} and child.attrib.get("Value"):
                    assigned_tag = child.attrib["Value"]
                    break
            nodes.append(
                {
                    "tag": assigned_tag or element.attrib.get("ComponentName") or element.attrib.get("ID"),
                    "source_id": element.attrib.get("ID"),
                    "kind": "dexpi_component",
                    "class": component_class,
                }
            )
        return {
            "schema_version": "dexpi-inventory-0.1",
            "source": str(source),
            "nodes": nodes,
            "edges": [],
            "process_path": [],
            "note": "Inventory-only prototype adapter; working connectivity uses the normalized synthetic JSON graph.",
        }


def adapter_for(source: Path) -> PlantStructureAdapter:
    suffix = source.suffix.lower()
    if suffix == ".json":
        return JsonTopologyAdapter()
    if suffix == ".svg":
        return SvgPidAdapter()
    if suffix in {".xml", ".dexpi"}:
        return DexpiXmlAdapter()
    raise ValueError(f"No plant-structure adapter for {suffix or 'unknown file type'}")
