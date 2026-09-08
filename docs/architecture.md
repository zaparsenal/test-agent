# Prototype architecture

## Runtime flow

```text
PFD / P&ID file + DCS historian file
      │
      ▼
In-memory inspection ── schema, tags, time range, compatibility
      │
      ▼
Evidence-quality scoring ── completeness, flags, stability, tag mapping
      │
      ▼
Ranked findings review
      │
      ▼
Operator question
      │
      ▼
Local FastAPI transport ── intent selection
      │
      ├── normalized P&ID topology
      ├── deterministic DCS query/statistics tools
      ├── quality and anomaly detectors
      └── evidence-only response composer
      │
      ▼
A2UI v0.9.1 messages
  createSurface → updateComponents → updateDataModel
      │
      ▼
Official MessageProcessor + React A2uiSurface
      │
      ▼
Trusted industrial component catalog
```

The default path keeps the demo repeatable and usable without credentials. It uses the same deterministic Python functions that are exposed as tools on the Google ADK agent. The optional ADK runtime can let Gemini select and call those tools, while `SendA2uiToClientToolset` supplies the custom catalog to the agent.

## Trust boundary

The server sends declarative A2UI messages, never executable UI code. Both sides know the same restricted catalog. The server validates message order, surface IDs, component IDs, references, component types, and each component schema with the official A2UI Agent SDK. The client processes those messages with the official A2UI message processor and renders only application-owned React implementations.

## Data layers

| Layer | Purpose | Current implementation |
|---|---|---|
| Source specimens | Preserve open engineering references | DEXPI P&ID XML/SVG and Process/PFD manual |
| Input session | Make demo inputs inspectable and enforce readiness | In-memory JSON, CSV, tagged SVG, and conservative DEXPI XML parsing |
| Adapter boundary | Decouple source format from analysis | JSON, SVG, and conservative DEXPI XML adapters |
| Normalized topology | Stable equipment/instrument graph | Nodes, process-flow edges, measurement edges, operating limits |
| DCS history | Time-series evidence | Two 2,166-reading scenarios, six tags, one-minute cadence |
| Data review | Establish trust and priorities before diagnosis | Quality score, transparent sub-scores, and severity-ranked findings |
| Ground truth | Evaluation only | Five separately stored incident labels |
| Analysis | Reproducible calculations | Windows, descriptive statistics, rates, limits, correlations, quality, event detection |
| Presentation | Intent-specific visual explanation | Restricted A2UI industrial catalog |

## Evidence policy

- Values and timestamps shown in the UI come from deterministic tool results.
- Bad or missing values are not substituted into calculations.
- Diagnoses are hypotheses, not confirmed causes.
- Inspection suggestions require site procedures and field confirmation.
- The software has no process-control write path.

## Extension points

1. Implement full DEXPI line/port connectivity in `DexpiXmlAdapter` and map site-specific classes into the normalized graph.
2. Add a historian adapter (for example, OSIsoft PI Web API or OPC UA) behind the same reading interface.
3. Replace rule thresholds with approved analytics while preserving tool-result provenance.
4. Add authenticated sessions, audit logs, and plant-specific authorization before any non-demo use.
5. Add an operator acknowledgement workflow as an A2UI action; keep control actions out of scope.
