# Source provenance

Downloaded source artifacts are retained unchanged in `data/reference-files/`. The working topology and diagram in `data/sample-inputs/process-diagram/` are explicitly synthetic and are not claimed as transformations of the public examples.

`data/reference-files/SOURCES.json` records the exact source URLs, repository revision, retrieval date, license, and SHA-256 digest for each retained artifact.

## Open P&ID reference

- Project: DEXPI Public Example PIDs, `dexpi/TrainingTestCases`
- Selected specimen: `dexpi 1.3/example pids/C01 DEXPI Reference P&ID/C01V04-VER.EX01`
- Files retained: `C01V04-VER.EX01.xml` and `C01V04-VER.EX01.svg`
- Repository revision used: `a23d61e2e089eb2ca464cd552f9ae580a2785963`
- Source: https://gitlab.com/dexpi/TrainingTestCases
- License retained alongside the files: Creative Commons Attribution 4.0 International

The XML adapter deliberately performs only conservative tag/class inventory extraction in this proof of concept. The demo does not pretend that the reference file is the T-101 transfer process.

## Open PFD/process reference

- Artifact: `DEXPI-Process-1.0-Manual.pdf`
- Publisher: DEXPI e.V.
- Source: https://dexpi.org/wp-content/uploads/2023/12/DEXPI-Process-1.0-Manual.pdf
- Context: the DEXPI Process Specification models process-engineering information and includes reference BFD/PFD material.
- Licensing statement: DEXPI publishes its specifications under a Creative Commons license; see https://dexpi.org/specifications/

The manual is retained as an open reference input. It is not parsed into the working graph in this first prototype.

## Protocol and agent references

- Google Agent Development Kit: https://adk.dev/
- A2UI agent development: https://a2ui.org/guides/agent-development/
- A2UI v0.9.1 protocol: https://a2ui.org/specification/v0.9-a2ui/
- A2UI client setup: https://a2ui.org/guides/client-setup/

Pinned packages in this prototype: `google-adk==2.8.0`, `a2ui-agent-sdk==0.5.0`, `@a2ui/react@0.9.1`, and `@a2ui/web_core@0.9.2`.

## Synthetic assets

The following are original project-generated assets and contain no live plant data:

- `data/sample-inputs/process-diagram/topology.json`
- `data/sample-inputs/process-diagram/tank_transfer_pid.svg`
- `data/sample-inputs/dcs/dcs_readings.json`
- `data/sample-inputs/dcs/dcs_readings.csv`
- `data/expected-results/incidents.json`

The generator seed is `101`. The readings cover 2026-08-18 08:00–14:00 at one-minute cadence for `LT-101`, `LT-102`, `FT-101`, `PT-101`, `P-101_STATUS`, and `FV-101_POS`.
