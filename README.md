# FieldGuide Process Insights

FieldGuide is a **local demo** of an assistant for reviewing industrial process data. Give it a process diagram and DCS readings; it checks data quality, ranks possible issues, and answers questions with supporting visuals. The included scenarios use synthetic data. FieldGuide does not connect to or control a plant.

## Try it

Install Node.js 22.13+ and Python 3.11–3.14, then run this in the project folder:

```sh
npm run setup
```

The setup command installs dependencies, starts the app, and opens [http://localhost:3000](http://localhost:3000). Keep the terminal open while using the demo; press `Ctrl+C` to stop. Run the same command next time.

On **Inputs**, choose **Healthy baseline** or **Critical incident**. Continue to **Data review** to see quality checks and ranked findings, then open **Analysis** to ask questions and inspect the evidence. You can also upload compatible files; examples are in [`data/sample-inputs`](data/sample-inputs).

The default demo needs no API key. To use the optional Google ADK agent through an LLM runtime, see [`.env.example`](.env.example).
