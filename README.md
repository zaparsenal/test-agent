# FieldGuide Process Insights

FieldGuide is a local demo of an industrial operations assistant. It reads a process diagram (PFD or P&ID) and DCS readings, checks data quality, ranks possible issues, and lets you ask questions about the results. Its answers can include charts and other visual evidence. The included scenarios use synthetic data; the app does not connect to or control a real plant.

## Run it

Install **Node.js 22.13 or newer** and **Python 3.11–3.14**. Then open a terminal in this project folder and run:

```bash
npm run setup
```

This same command works on Windows, macOS, and Linux. It installs what the project needs, starts the app, and opens [http://localhost:3000](http://localhost:3000). Keep the terminal open while using it; press `Ctrl+C` to stop. Use the same command next time you want to run it.

## Try the demo

On the **Inputs** page, choose **Healthy baseline** or **Critical incident**. You can also upload your own compatible files; ready-to-use files are in [`data/sample-inputs`](data/sample-inputs). Continue to **Data review** for the quality score and ranked findings, then open **Analysis** to ask questions and see the supporting visuals.

No API key is needed for the default demo.
