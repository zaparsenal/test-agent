# FieldGuide Process Insights

FieldGuide is a proof-of-concept industrial operations assistant. It lets a user add a process diagram and DCS historian export, checks what was provided, and then turns the data into a conversational operating review with visual evidence.

The demonstration follows a simple tank-transfer process:

`T-101 → P-101 → FT-101 → FV-101 → T-102`

## How the project started

The project began with a practical demo question: can an agent combine the process context in a PFD or P&ID with time-series DCS data, explain what may be happening, and show the evidence in a way that an operations team can understand?

We built a small, safe scenario around that question:

1. Create a synthetic tank-transfer process and six hours of DCS readings.
2. Add open DEXPI files as real-world PFD/P&ID reference material.
3. Let the user upload and inspect both inputs before analysis begins.
4. Present the analysis as a conversation instead of a crowded dashboard.
5. Use A2UI to attach the most useful visual evidence to each answer.

The application was created specifically for this proof of concept. It was not forked from, copied from, or bootstrapped with another GitHub project.

## What inspired the design

The interaction design was informed by three established product patterns:

- **Power BI Copilot:** conversational answers with supporting visuals and references.
- **Databricks Genie:** natural-language questions over trusted data.
- **AVEVA Industrial AI Assistant:** a chat-style experience for industrial operations.

The implementation also follows the official **Google Agent Development Kit** and **A2UI** documentation. The open engineering reference files come from the DEXPI Training Test Cases on GitLab. Exact links and licensing details are recorded in [`docs/sources.md`](docs/sources.md).

## The final prototype

The finished demo has two clear parts:

- **Inputs:** upload a process diagram and DCS export, inspect the parsed equipment, tags, time range, data quality, and example readings, then approve them for analysis.
- **Analysis:** receive an initial operating review, ask follow-up questions in a chat, and expand the evidence attached to each answer.

Depending on the question, the evidence can include current values, trends, event timing, affected process paths, data-quality warnings, and suggested field checks.

The default demo does not need an API key. It uses repeatable local analysis so the same evidence appears reliably during a presentation. A Google ADK agent is included for future Gemini-powered conversation, but that optional path requires a Google API key and should still be treated as experimental.

## Try the demo

You need Node.js 22.13 or newer and Python 3.12.

```bash
git clone https://github.com/zaparsenal/test-agent.git
cd test-agent
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm install
npm run demo
```

Open [http://localhost:3000](http://localhost:3000).

For a quick walkthrough:

1. Select **Load sample inputs** on the Inputs page.
2. Inspect the process diagram and historian data.
3. Select **Analyze these inputs**.
4. Ask: `Why did T-101's level increase?`
5. Expand **Supporting evidence** to show the A2UI-generated visuals.
6. Follow with: `Which sensor readings are unreliable?`

The sample data contains a planned restriction-like event between 10:15 and 11:00, followed by sensor drift, bad or missing readings, recovery, and stable operation.

## Project map

| Folder | What it contains |
|---|---|
| `src/` | The web interface, chat experience, and A2UI visual components |
| `backend/` | File inspection, process analysis, response generation, and the Google ADK agent |
| `data/` | All sample inputs, open reference files, and expected demo results |
| `docs/` | Architecture, design rationale, sources, and the PDF demo guide |
| `scripts/` | Utilities for regenerating data, evaluation results, and the demo guide |
| `tests/` | Automated checks for the analysis, inputs, sources, and A2UI messages |

The [`data/README.md`](data/README.md) file explains exactly which files to upload during the demo.

## Check that everything works

```bash
npm run test
.venv/bin/python -m scripts.evaluate
npm run build
```

The evaluation checks this intentionally designed synthetic scenario. It is not a performance claim for real plant data.

## Important boundaries

- The working process diagram and all DCS readings are synthetic. No live plant or customer data is included.
- The public DEXPI files are unchanged reference material and are clearly separated from the working sample inputs.
- FieldGuide is advisory only. It cannot control equipment or replace alarms, procedures, safety systems, or operator judgment.
- Suggested causes are evidence-based hypotheses, not confirmed mechanical diagnoses.

For more detail, see [`docs/architecture.md`](docs/architecture.md), [`docs/ui-rationale.md`](docs/ui-rationale.md), and the presenter-ready [`docs/demo/fieldguide-demo-guide.pdf`](docs/demo/fieldguide-demo-guide.pdf).
