# FieldGuide demonstration data

This folder separates files that work immediately in the prototype from public engineering references retained for provenance and future adapter work.

## Use these files in the live demo

### 1. PFD or P&ID input

Upload one of these files in the **PFD or P&ID** input card:

- `demo-inputs/pid/tank_transfer_pid.svg` - recommended visual input for the demonstration.
- `demo-inputs/pid/topology.json` - equivalent normalized machine-readable topology.

Both describe the synthetic transfer route:

`T-101 -> P-101 -> FT-101 -> FV-101 -> T-102`

### 2. DCS input

Upload one of these files in the **DCS historian export** input card:

- `demo-inputs/dcs/dcs_readings.csv` - recommended because it resembles a typical historian export.
- `demo-inputs/dcs/dcs_readings.json` - the same readings in JSON format.

The historian dataset contains:

- 2,166 readings across six tags.
- One-minute data from 2026-08-18 08:00 through 14:00.
- `LT-101`, `LT-102`, `FT-101`, `PT-101`, `P-101_STATUS`, and `FV-101_POS`.
- 2,140 GOOD, 20 BAD, and 6 MISSING samples.
- A designed restriction-like event from 10:15 through 11:00, followed by recovery.

## Fast demonstration sequence

1. Open the prototype's **Inputs** section.
2. Upload `tank_transfer_pid.svg` into the process-diagram card.
3. Upload `dcs_readings.csv` into the historian card.
4. Choose **Inspect** on each file to show the parsed tags, time coverage, quality counts, and sample rows.
5. Choose **Analyze these inputs**.
6. Ask: `Why did T-101's level increase?`
7. Expand **Supporting evidence** to show the A2UI-generated KPIs, trends, event timeline, process path, and inspection suggestions.

## Open-source references

The `open-source-references` folder contains unchanged public DEXPI material:

- `dexpi-pid/C01V04-VER.EX01.xml` - machine-readable DEXPI / Proteus XML.
- `dexpi-pid/C01V04-VER.EX01.svg` - visual rendering of the same public example P&ID.
- `dexpi-pid/LICENSE-CC-BY-4.0.txt` - the retained Creative Commons Attribution 4.0 license.
- `dexpi-process/DEXPI-Process-1.0-Manual.pdf` - the DEXPI Process specification and PFD/process-engineering reference.
- `SOURCES.json` - exact URLs, repository revision, retrieval date, licenses, and SHA-256 digests.

The public DEXPI example is valuable for provenance and parser development, but it is **not the upload file for the T-101 demonstration**. Its equipment and tag names belong to a different process, so it will not satisfy the prototype's T-101 readiness check. Use the synthetic tagged SVG or topology JSON for the working demo.

## Data boundaries

- The P&ID used by the working T-101 scenario and all DCS readings are synthetic.
- No live plant or customer information is present.
- The open DEXPI artifacts are retained unchanged and are clearly separated from the synthetic working inputs.
- The prototype is advisory only and cannot control equipment.

See `manifest.json` for a machine-readable inventory of every file in this package.
