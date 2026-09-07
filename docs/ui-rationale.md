# Interface rationale

The redesigned experience is a conversational analysis workspace rather than a dashboard with a detached question box.

## Pattern research

Three current product patterns informed the design:

- Power BI Copilot appends new answers to conversation history, embeds visuals alongside narrative answers, and emphasizes references that let users validate an insight. Source: https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-pane-summarize-content
- Databricks Genie uses a natural-language conversational workspace, common starter questions, adaptable visualizations, and trusted data assets. Source: https://docs.databricks.com/aws/en/ai-bi/concepts
- AVEVA Industrial AI Assistant is positioned as a chat interface for natural-language questions about site and plant operations. Source: https://www.aveva.com/en/connect-experience/about-connect/industrial-ai-assistant/

## Applied decisions

1. Give **inputs** a full workspace instead of a narrow status rail. Both source types have large drop zones, sample downloads, replacement controls, and clear readiness state.
2. Let users inspect the parsed equipment, tags, timestamps, quality counts, and historian rows before analysis. This makes the source-to-answer transition demonstrable rather than implied.
3. Lock analysis until compatible diagram and historian inputs exist, so the product has an understandable beginning and avoids showing unrelated canned outputs.
4. Make **discussion** the primary analysis workspace, with conventional user and assistant message alignment and a readable narrative answer for every turn.
5. Attach **outputs** to the answer in an expandable Supporting evidence region. Charts, readings, timelines, process context, and inspection guidance remain available without overwhelming the conversation.
6. Use a dark navy product frame, a cool-gray canvas, high-contrast white working surfaces, and teal/amber state accents. Body text stays at 16px, with metadata no smaller than 12px.
7. Preserve the thread so follow-up questions have an understandable sequence, and keep common follow-ups near the latest result.

The result intentionally borrows the strong information hierarchy of analyst copilots while retaining industrial cues, evidence language, signal quality, and the advisory-only boundary. The separation is now explicit: **Inputs** is where evidence enters and can be inspected; **Analysis** is where discussion and generated outputs accumulate.
