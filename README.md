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
4. Score the evidence quality and rank the findings worth investigating.
5. Present the deeper analysis as a conversation instead of a crowded dashboard.
6. Use A2UI to attach the most useful visual evidence to each answer.

The application was created specifically for this proof of concept. It was not forked from, copied from, or bootstrapped with another GitHub project.

## What inspired the design

The interaction design was informed by three established product patterns:

- **Power BI Copilot:** conversational answers with supporting visuals and references.
- **Databricks Genie:** natural-language questions over trusted data.
- **AVEVA Industrial AI Assistant:** a chat-style experience for industrial operations.

The implementation also follows the official **Google Agent Development Kit** and **A2UI** documentation. The open engineering reference files come from the DEXPI Training Test Cases on GitLab. Exact links and licensing details are recorded in [`docs/sources.md`](docs/sources.md).

## The final prototype

The finished demo has three clear parts:

- **Inputs:** upload a process diagram and DCS export, inspect the parsed equipment, tags, time range, data quality, and example readings, then approve them for analysis.
- **Data review:** see a calculated evidence-quality score, the checks behind it, and severity-ranked process and signal findings. Each finding can open a focused investigation.
- **Analysis:** receive an initial operating review, ask follow-up questions in a chat, and expand the evidence attached to each answer.

Depending on the question, the evidence can include current values, trends, event timing, affected process paths, data-quality warnings, and suggested field checks.

The default demo does not need an API key. It uses repeatable local analysis so the same evidence appears reliably during a presentation. A Google ADK agent is included for future Gemini-powered conversation, but that optional path requires a Google API key and should still be treated as experimental.

## Start the demo with one command

The same command works in Windows PowerShell, Windows Command Prompt, macOS Terminal, and Linux terminals.

Before the first run, install:

- Python 3.11, 3.12, 3.13, or 3.14.
- Node.js 22.13 or newer.

Download or clone the repository, open a terminal inside the `test-agent` folder, and run:

```bash
npm run setup
```

That one command finds the installed Python version, creates the correct `.venv`, installs the Python and web packages, regenerates the sample data, starts both parts of FieldGuide, and opens [http://localhost:3000](http://localhost:3000).

Use the same command on later runs. Installed packages and the existing environment are reused, so later startups are faster. Keep the terminal open while using FieldGuide and press `Ctrl+C` to stop it.

Windows users may also double-click `setup-and-run-windows.bat`; it runs the same universal setup command.

For a quick walkthrough:

1. Select **Sample A · quality gaps** on the Inputs page. You can use **Sample B · clean data** later to show how the score changes.
2. Inspect the process diagram and historian data.
3. Select **Review data quality** to see the calculated score and ranked findings.
4. Choose **Investigate** on the first finding, or start a general analysis.
5. Expand **Supporting evidence** to show the A2UI-generated visuals.
6. Follow with: `Which sensor readings are unreliable?`

Both sample datasets contain the same planned restriction-like event between 10:15 and 11:00, followed by sensor drift and recovery. Sample A also contains bad or missing historian readings; Sample B keeps the source quality flags clean so the review score and ranked findings visibly change.

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
npm run evaluate
npm run build
```

The evaluation checks this intentionally designed synthetic scenario. It is not a performance claim for real plant data.

## Important boundaries

- The working process diagram and all DCS readings are synthetic. No live plant or customer data is included.
- The public DEXPI files are unchanged reference material and are clearly separated from the working sample inputs.
- FieldGuide is advisory only. It cannot control equipment or replace alarms, procedures, safety systems, or operator judgment.
- Suggested causes are evidence-based hypotheses, not confirmed mechanical diagnoses.

For more detail, see [`docs/architecture.md`](docs/architecture.md), [`docs/ui-rationale.md`](docs/ui-rationale.md), and the presenter-ready [`docs/demo/fieldguide-demo-guide.pdf`](docs/demo/fieldguide-demo-guide.pdf).
