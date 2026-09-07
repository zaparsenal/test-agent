"""Google ADK definition for the process insights agent."""

from __future__ import annotations

import os

from a2ui.adk.send_a2ui_to_client_toolset import SendA2uiToClientToolset
from google.adk.agents import Agent

from backend.a2ui_payload import ALLOWED_COMPONENTS, _official_a2ui_format
from backend.analysis import (
    build_incident_timeline,
    calculate_statistics,
    compare_reading_with_normal,
    correlate_sensor_changes,
    detect_basic_anomalies,
    detect_data_quality_problems,
    detect_threshold_violations,
    find_connected_equipment,
    get_latest_sensor_values,
    get_plant_topology,
    query_sensor_time_range,
)

AGENT_INSTRUCTION = """
You are process_insights_agent, an evidence-first industrial operations assistant for a research prototype.

Your job is to understand an operator's question, retrieve the normalized plant topology, select the smallest
set of deterministic analysis tools needed, and explain the computed evidence. Never invent a calculation,
timestamp, tag, value, operating limit, connection, alarm, or diagnosis. Always state uncertainty and any
sensor-quality limitations. Use possible/likely/consistent-with language when causality is not proven.

The process path is T-101 → P-101 → FT-101 → FV-101 → T-102. Return a declarative A2UI response using only
the approved FieldGuide industrial catalog. Choose the response layout by intent: status uses a summary, KPI
cards, events, and overview diagram; trends use a focused chart; root-cause questions use correlated trends,
timeline, affected path, and inspection suggestions; sensor-quality questions use a warning and affected-tag
table. Never emit JavaScript or arbitrary HTML.

This software is advisory only. Never claim to control equipment, issue control commands, bypass safeguards,
or replace operating procedures and safety systems.
""".strip()

_format = _official_a2ui_format()
_catalog = _format._select_catalog()  # The SDK currently exposes catalog selection through this method.

root_agent = Agent(
    name="process_insights_agent",
    model=os.getenv("ADK_MODEL", "gemini-2.5-flash"),
    description="Analyzes P&ID topology and synthetic DCS evidence, then returns restricted A2UI views.",
    instruction=AGENT_INSTRUCTION,
    tools=[
        get_plant_topology,
        find_connected_equipment,
        get_latest_sensor_values,
        query_sensor_time_range,
        calculate_statistics,
        detect_threshold_violations,
        detect_data_quality_problems,
        detect_basic_anomalies,
        correlate_sensor_changes,
        build_incident_timeline,
        compare_reading_with_normal,
        SendA2uiToClientToolset(
            a2ui_enabled=True,
            a2ui_catalog=_catalog,
            a2ui_examples="Use a single root ResponseLayout and only these components: " + ", ".join(sorted(ALLOWED_COMPONENTS)),
        ),
    ],
)
