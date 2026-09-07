#!/usr/bin/env python3
"""Export a stable validated A2UI response for frontend fallback and inspection."""

from __future__ import annotations

import json
from pathlib import Path

from backend.a2ui_payload import build_response
from backend.analysis import ProcessAnalyzer

ROOT = Path(__file__).resolve().parents[1]
QUESTION = "What is happening in the process right now?"


def main() -> None:
    payload = build_response(QUESTION, ProcessAnalyzer())
    original_id = payload["surfaceId"]
    stable_id = "process-insight-demo"
    payload["surfaceId"] = stable_id
    for message in payload["messages"]:
        for envelope in ("createSurface", "updateComponents", "updateDataModel", "deleteSurface"):
            if envelope in message and message[envelope].get("surfaceId") == original_id:
                message[envelope]["surfaceId"] = stable_id
    for path in [ROOT / "public" / "data" / "fallback_response.json", ROOT / "data" / "generated" / "example_a2ui_response.json"]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n")
    print("Exported validated A2UI fallback response.")


if __name__ == "__main__":
    main()
