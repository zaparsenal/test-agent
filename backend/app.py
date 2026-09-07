"""Local FastAPI transport for deterministic demo requests."""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.a2ui_payload import build_response
from backend.analysis import ROOT
from backend.input_session import InputSession
from backend.process_insights_agent import root_agent

app = FastAPI(
    title="FieldGuide Process Insights API",
    version="0.1.0",
    description="Advisory-only prototype API for P&ID and synthetic DCS analysis.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

input_session = InputSession()


class QueryRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)


class InputContentRequest(BaseModel):
    kind: Literal["diagram", "dcs"]
    name: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=8_000_000)
    sizeBytes: int = Field(ge=1, le=8_000_000)


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "agent": root_agent.name,
        "model": root_agent.model,
        "mode": "deterministic evidence path",
        "advisoryOnly": True,
        "dataThrough": input_session.analyzer.records[-1]["timestamp"],
    }


@app.get("/api/inputs")
def inputs() -> dict[str, object]:
    return input_session.status()


@app.post("/api/inputs/demo")
def demo_inputs() -> dict[str, object]:
    return input_session.load_demo()


@app.post("/api/inputs/inspect")
def inspect_input(request: InputContentRequest) -> dict[str, object]:
    try:
        return input_session.inspect(request.kind, request.name, request.content, request.sizeBytes)
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.delete("/api/inputs")
def clear_inputs() -> dict[str, object]:
    return input_session.clear()


@app.get("/api/samples/{kind}")
def sample_file(kind: Literal["diagram", "dcs"]):
    if kind == "diagram":
        path = ROOT / "data" / "sample-inputs" / "process-diagram" / "tank_transfer_pid.svg"
        return FileResponse(path, filename="tank_transfer_pid.svg", media_type="image/svg+xml")
    path = ROOT / "data" / "sample-inputs" / "dcs" / "dcs_readings.csv"
    return FileResponse(path, filename="dcs_readings.csv", media_type="text/csv")


@app.get("/api/topology")
def topology() -> dict[str, object]:
    return input_session.analyzer.get_plant_topology()


@app.get("/api/readings")
def readings(
    tags: list[str] = Query(...),
    start: str = Query(...),
    end: str = Query(...),
) -> dict[str, object]:
    try:
        records = input_session.analyzer.query_time_range(tags, start, end)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"records": records, "count": len(records)}


@app.post("/api/query")
def query(request: QueryRequest) -> dict[str, object]:
    """Run deterministic tools and return a validated A2UI v0.9.1 message stream."""
    try:
        if not input_session.status()["analysisReady"]:
            raise HTTPException(status_code=409, detail="Load and inspect both inputs before starting an analysis")
        return build_response(request.question.strip(), input_session.analyzer)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
