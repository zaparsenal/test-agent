# FieldGuide Process Insights

An end-to-end, local proof of concept for an evidence-first industrial operations assistant. It joins open DEXPI PFD/P&ID references, a normalized tank-transfer topology, deterministic synthetic DCS history, a Google ADK agent definition, and a real A2UI v0.9.1 client renderer.

The demo investigates this process:

`T-101 → P-101 → FT-101 → FV-101 → T-102`

It can answer current-status, root-cause, trend, process-path, inspection, and sensor-quality questions. The demo starts with a real input workspace: add a PFD/P&ID and DCS historian file, inspect the parsed tags and rows, and start the analysis only after both inputs validate. Questions, narrative answers, and generated evidence then accumulate in one conversation. The evidence surface changes by intent and can include KPI cards, correlated trends, an incident timeline, a clickable P&ID, an inspection panel, or a sensor-quality warning.

## Run the demo

Prerequisites: Node.js 22.13 or newer and Python 3.12.

```bash
cd "/Users/zaydpatel/Desktop/projects/test agent"
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm install
npm run demo
```

Open [http://localhost:3000](http://localhost:3000). No API key is required for the complete default demonstration: the local API executes deterministic analysis tools and returns conversational text plus schema-validated A2UI evidence.

The synthetic dataset is regenerated with the same seed every time `npm run demo` starts. To keep an existing dataset, run the two services separately:

```bash
npm run backend
npm run dev
```

## What is included

- `backend/process_insights_agent/agent.py` — Google ADK `process_insights_agent`, with eleven evidence tools and the A2UI toolset.
- `backend/analysis.py` — topology queries, time-window retrieval, statistics, operating-limit comparisons, data-quality checks, anomaly detection, correlations, and event sequencing.
- `backend/input_session.py` — in-memory upload parsing, compatibility checks, input summaries, and analyzer session assembly.
- `backend/a2ui_payload.py` — intent routing and A2UI v0.9.1 message generation, validated by the official agent SDK against a restricted component catalog.
- `components/agent-surface.tsx` — official A2UI message processor and React surface renderer.
- `components/industrial-catalog.tsx` — the trusted, application-owned industrial component catalog.
- `data/generated/` — six hours of one-minute synthetic readings for six DCS tags, in JSON and CSV.
- `data/ground_truth/` — incident labels kept separate from the readings for evaluation.
- `data/raw/dexpi/` — unchanged open DEXPI PFD/P&ID reference artifacts and license copy.
- `data/plant/` — the normalized working topology and synthetic P&ID used by the demo.

## Demonstration script

1. On **Inputs**, choose **Load sample inputs** for the quick path—or use **Download sample** and upload the two files yourself to demonstrate the file workflow.
2. Choose **Inspect** on either input to show parsed equipment, tags, timestamps, quality counts, and historian rows.
3. Choose **Analyze these inputs**. The assistant opens the conversation with a general operating review.
4. Ask “Why is T-101's level increasing?” to show the narrative diagnosis, correlated evidence, timeline, affected path, and field checks.
5. Ask “Show me pressure and flow around the incident.” or “Are any sensors unreliable?” to demonstrate intent-specific follow-ups.
6. Expand **Supporting evidence**, then use the diagram tags and zoom controls.

The deliberately injected sequence is: startup, stable transfer, a downstream-restriction signature from 10:15–11:00, LT-102 drift, bad/missing historian values, recovery, and stable operation.

## Verify

```bash
npm run test
.venv/bin/python -m scripts.evaluate
npm run build
```

The evaluation is an integrity check for this designed synthetic scenario, not a claim of performance on real plants. The expected result is five matched incident types, precision/recall/F1 of 1.0, and approximately 0.993 mean temporal overlap.

## Optional Google ADK runtime

The browser demo intentionally has a deterministic, keyless execution path so it is repeatable in a team presentation. The same tools are registered on a real Google ADK `Agent`. To experiment with model-driven tool selection, copy `.env.example` to `.env`, add a Google API key, stop the demo API on port 8000, and run:

```bash
.venv/bin/adk web backend
```

Select `process_insights_agent` in the ADK interface. Model output is constrained to the registered tools and the restricted A2UI catalog, but any LLM-generated output should still be treated as experimental.

## Boundaries

- Advisory and demonstrative only; it cannot command equipment or replace operating procedures, alarms, SIS, or human review.
- The working process and DCS history are synthetic. They are not derived from a live plant.
- The DEXPI 1.3 example is retained as an unchanged source specimen. Its adapter currently extracts an equipment/instrument inventory; complete line-connectivity mapping across vendor variants is future work.
- Root-cause text uses “consistent with” language because correlations and topology do not prove a mechanical failure.

See `docs/architecture.md` for the data flow, `docs/ui-rationale.md` for the interaction rationale, and `docs/sources.md` for provenance and licensing.
