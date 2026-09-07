"""Create the FieldGuide workflow and A2UI demonstration guide."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "fieldguide-demo-guide.pdf"
PAGE_W, PAGE_H = landscape(letter)

NAVY = colors.HexColor("#0D2736")
NAVY_2 = colors.HexColor("#173B4D")
BLUE = colors.HexColor("#19728C")
BLUE_DARK = colors.HexColor("#15596D")
TEAL = colors.HexColor("#26816F")
TEAL_PALE = colors.HexColor("#DFF1EC")
AMBER = colors.HexColor("#CB7C15")
AMBER_PALE = colors.HexColor("#FFF2D9")
RED = colors.HexColor("#B44740")
RED_PALE = colors.HexColor("#FAE6E3")
INK = colors.HexColor("#152833")
MUTED = colors.HexColor("#61747F")
BORDER = colors.HexColor("#C3D0D8")
CANVAS = colors.HexColor("#E9EEF2")
PANEL = colors.white
LIGHT_BLUE = colors.HexColor("#E6F0F4")


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("Arial", "/System/Library/Fonts/Supplemental/Arial.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Bold", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"))
    pdfmetrics.registerFont(TTFont("Arial-Italic", "/System/Library/Fonts/Supplemental/Arial Italic.ttf"))
    pdfmetrics.registerFont(TTFont("Mono", "/System/Library/Fonts/SFNSMono.ttf"))


register_fonts()


def para(
    c: canvas.Canvas,
    text: str,
    x: float,
    y_top: float,
    width: float,
    font_size: float = 11,
    leading: float | None = None,
    color: colors.Color = INK,
    bold: bool = False,
    align: int = TA_LEFT,
    max_height: float = 500,
) -> float:
    style = ParagraphStyle(
        "body",
        fontName="Arial-Bold" if bold else "Arial",
        fontSize=font_size,
        leading=leading or font_size * 1.35,
        textColor=color,
        alignment=align,
        spaceAfter=0,
        spaceBefore=0,
    )
    item = Paragraph(text, style)
    _, height = item.wrap(width, max_height)
    item.drawOn(c, x, y_top - height)
    return height


def rounded(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill: colors.Color, stroke: colors.Color = BORDER, radius: float = 10, line: float = 1) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(line)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def label(c: canvas.Canvas, text: str, x: float, y: float, color: colors.Color = BLUE_DARK, size: float = 8.5) -> None:
    c.setFillColor(color)
    c.setFont("Mono", size)
    c.drawString(x, y, text.upper())


def page_header(c: canvas.Canvas, section: str, page: int, title: str, subtitle: str = "") -> None:
    c.setFillColor(CANVAS)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 48, PAGE_W, 48, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Arial-Bold", 12)
    c.drawString(34, PAGE_H - 30, "FieldGuide")
    c.setFillColor(colors.HexColor("#9FB7C1"))
    c.setFont("Arial", 8.5)
    c.drawString(96, PAGE_H - 30, "PROCESS INSIGHTS")
    c.setFillColor(colors.HexColor("#B9CBD2"))
    c.setFont("Arial-Bold", 8.5)
    c.drawRightString(PAGE_W - 34, PAGE_H - 30, section.upper())
    label(c, f"{page:02d}  {section}", 36, PAGE_H - 75)
    c.setFillColor(INK)
    c.setFont("Arial-Bold", 25)
    c.drawString(36, PAGE_H - 105, title)
    if subtitle:
        para(c, subtitle, 36, PAGE_H - 118, PAGE_W - 72, 10.5, 14, MUTED)


def footer(c: canvas.Canvas, page: int, source: str = "FieldGuide local prototype") -> None:
    c.setStrokeColor(BORDER)
    c.setLineWidth(.6)
    c.line(36, 28, PAGE_W - 36, 28)
    c.setFillColor(MUTED)
    c.setFont("Arial", 7.5)
    c.drawString(36, 16, source)
    c.drawRightString(PAGE_W - 36, 16, f"DEMO GUIDE  /  {page}")


def speaker_note(c: canvas.Canvas, text: str, x: float, y: float, w: float) -> None:
    rounded(c, x, y, w, 38, NAVY_2, NAVY_2, 8)
    c.setFillColor(colors.HexColor("#65C3AF"))
    c.setFont("Arial-Bold", 8)
    c.drawString(x + 12, y + 23, "SAY")
    para(c, text, x + 46, y + 29, w - 58, 9, 11, colors.white)


def arrow(c: canvas.Canvas, x1: float, y1: float, x2: float, y2: float, color: colors.Color = BLUE) -> None:
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(2)
    c.line(x1, y1, x2, y2)
    if x2 >= x1:
        c.line(x2, y2, x2 - 6, y2 + 4)
        c.line(x2, y2, x2 - 6, y2 - 4)
    else:
        c.line(x2, y2, x2 + 6, y2 + 4)
        c.line(x2, y2, x2 + 6, y2 - 4)


def metric(c: canvas.Canvas, x: float, y: float, w: float, value: str, caption: str, accent: colors.Color = TEAL) -> None:
    rounded(c, x, y, w, 56, PANEL, BORDER, 8)
    c.setFillColor(accent)
    c.rect(x, y, 4, 56, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("Arial-Bold", 18)
    c.drawString(x + 14, y + 29, value)
    c.setFillColor(MUTED)
    c.setFont("Arial", 8.5)
    c.drawString(x + 14, y + 14, caption)


def process_route(c: canvas.Canvas, x: float, y: float, scale: float = 1.0, warning: bool = False, dark_background: bool = False) -> None:
    pipe = AMBER if warning else BLUE
    c.setStrokeColor(pipe)
    c.setLineWidth(4 * scale)
    c.line(x + 45 * scale, y, x + 430 * scale, y)
    c.setFillColor(pipe)
    c.line(x + 430 * scale, y, x + 421 * scale, y + 5 * scale)
    c.line(x + 430 * scale, y, x + 421 * scale, y - 5 * scale)

    # Tank 101
    c.setFillColor(colors.white)
    c.setStrokeColor(NAVY_2)
    c.setLineWidth(2)
    c.roundRect(x, y - 34 * scale, 58 * scale, 68 * scale, 8 * scale, fill=1, stroke=1)
    c.setFillColor(LIGHT_BLUE)
    c.rect(x + 4 * scale, y - 28 * scale, 50 * scale, 31 * scale, fill=1, stroke=0)
    # Pump
    c.setFillColor(colors.white)
    c.setStrokeColor(NAVY_2)
    c.circle(x + 130 * scale, y, 25 * scale, fill=1, stroke=1)
    c.setFillColor(BLUE_DARK)
    p = c.beginPath()
    p.moveTo(x + 120 * scale, y - 13 * scale)
    p.lineTo(x + 143 * scale, y)
    p.lineTo(x + 120 * scale, y + 13 * scale)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    # Flow instrument
    c.setFillColor(colors.white)
    c.setStrokeColor(NAVY_2)
    c.circle(x + 225 * scale, y, 21 * scale, fill=1, stroke=1)
    # Valve
    c.setFillColor(AMBER_PALE if warning else colors.white)
    c.setStrokeColor(AMBER if warning else NAVY_2)
    p = c.beginPath()
    p.moveTo(x + 295 * scale, y - 17 * scale)
    p.lineTo(x + 320 * scale, y)
    p.lineTo(x + 295 * scale, y + 17 * scale)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    p = c.beginPath()
    p.moveTo(x + 345 * scale, y - 17 * scale)
    p.lineTo(x + 320 * scale, y)
    p.lineTo(x + 345 * scale, y + 17 * scale)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Tank 102
    c.setFillColor(colors.white)
    c.setStrokeColor(NAVY_2)
    c.roundRect(x + 415 * scale, y - 34 * scale, 58 * scale, 68 * scale, 8 * scale, fill=1, stroke=1)

    c.setFillColor(colors.HexColor("#C7D7DD") if dark_background else INK)
    c.setFont("Mono", 8 * scale)
    tags = [(3, "T-101"), (108, "P-101"), (204, "FT-101"), (297, "FV-101"), (418, "T-102")]
    for dx, tag in tags:
        c.drawString(x + dx * scale, y - 49 * scale, tag)
    c.setFont("Arial-Bold", 8.5 * scale)
    c.drawCentredString(x + 225 * scale, y - 3 * scale, "FT")


def cover(c: canvas.Canvas) -> None:
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(NAVY_2)
    c.circle(710, 530, 190, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#19475B"))
    c.circle(735, 545, 120, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#65C3AF"))
    c.circle(706, 518, 10, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Arial-Bold", 17)
    c.drawString(42, PAGE_H - 54, "FieldGuide")
    c.setFillColor(colors.HexColor("#9FB7C1"))
    c.setFont("Arial", 10)
    c.drawString(125, PAGE_H - 54, "PROCESS INSIGHTS")

    label(c, "DEMO ENABLEMENT", 43, 447, colors.HexColor("#65C3AF"), 10)
    c.setFillColor(colors.white)
    c.setFont("Arial-Bold", 38)
    c.drawString(42, 396, "Industrial operations assistant")
    c.drawString(42, 350, "Workflow + A2UI guide")
    para(c, "A presenter-ready explanation of how process diagrams and synthetic DCS data become conversational, evidence-backed insights - and why A2UI is the key interface layer.", 43, 321, 610, 14, 20, colors.HexColor("#C2D2D8"))

    rounded(c, 42, 186, 706, 98, colors.HexColor("#123242"), colors.HexColor("#315365"), 12)
    process_route(c, 76, 237, 1.25, warning=True, dark_background=True)

    metric(c, 42, 91, 158, "2 inputs", "P&ID + historian export", TEAL)
    metric(c, 212, 91, 158, "2,166", "synthetic DCS readings", BLUE)
    metric(c, 382, 91, 158, "10", "approved A2UI components", AMBER)
    metric(c, 552, 91, 196, "0 API keys", "required for the default demo", TEAL)
    c.setFillColor(colors.HexColor("#91AAB5"))
    c.setFont("Arial", 8)
    c.drawString(43, 43, "Local proof of concept  |  Advisory only  |  Prepared 2026-09-07")
    c.showPage()


def workflow_overview(c: canvas.Canvas) -> None:
    page_header(c, "Section 1 - Workflow", 2, "From source files to an explainable conversation", "The demo has a visible beginning, middle, and end: evidence enters, the system validates it, and the assistant turns it into a discussion with attached visual proof.")
    steps = [
        ("01", "Load process context", "Add a tagged SVG, normalized topology JSON, or conservative DEXPI / Proteus XML."),
        ("02", "Load operating data", "Add a CSV or JSON historian export with timestamps, tags, values, units, and quality."),
        ("03", "Inspect + validate", "Review parsed tags, coverage, quality counts, and sample rows before analysis unlocks."),
        ("04", "Run the analysis", "Apply topology, limits, statistics, correlations, quality checks, and event sequencing."),
        ("05", "Continue the conversation", "Receive a written answer, expand supporting visuals, then ask follow-up questions."),
    ]
    x0, y, gap, w, h = 36, 276, 10, 136, 170
    for index, (number, title, body) in enumerate(steps):
        x = x0 + index * (w + gap)
        rounded(c, x, y, w, h, PANEL, BORDER, 10)
        c.setFillColor(TEAL if index in {0, 1, 2, 4} else AMBER)
        c.circle(x + 24, y + h - 26, 14, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Mono", 8)
        c.drawCentredString(x + 24, y + h - 29, number)
        para(c, title, x + 13, y + h - 50, w - 26, 11.5, 14, INK, True)
        para(c, body, x + 13, y + h - 84, w - 26, 9.2, 12.5, MUTED)
        if index < len(steps) - 1:
            arrow(c, x + w + 2, y + 84, x + w + gap - 2, y + 84, BLUE)

    rounded(c, 36, 167, 720, 84, LIGHT_BLUE, colors.HexColor("#B7CCD5"), 10)
    label(c, "DEMO DATA AT A GLANCE", 51, 229)
    metrics = [
        ("Process path", "T-101  >  P-101  >  FT-101  >  FV-101  >  T-102"),
        ("Historian", "6 tags  |  1-minute cadence  |  08:00-14:00"),
        ("Quality", "2,140 GOOD  |  20 BAD  |  6 MISSING"),
    ]
    for i, (key, value) in enumerate(metrics):
        x = 51 + i * 233
        c.setFillColor(INK)
        c.setFont("Arial-Bold", 9)
        c.drawString(x, 205, key)
        para(c, value, x, 197, 216, 8.5, 11, MUTED)
    c.setFillColor(MUTED)
    c.setFont("Arial", 7.7)
    c.drawString(51, 179, "Provenance: open DEXPI reference specimen retained under CC BY 4.0; the working T-101 topology and DCS readings are synthetic.")
    speaker_note(c, "The prototype does not jump straight to an answer. It lets the user see exactly what went in, what was parsed, and when the system is ready.", 36, 78, 720)
    footer(c, 2)
    c.showPage()


def workflow_architecture(c: canvas.Canvas) -> None:
    page_header(c, "Section 1 - Workflow", 3, "What the prototype is actually doing", "A local, repeatable evidence path keeps the demonstration reliable while preserving the same boundaries needed for a future agent runtime.")

    columns = [
        (36, 126, "INPUT SESSION", "Files remain in memory", ["Parse diagram tags", "Parse historian rows", "Check time coverage", "Confirm required tags"]),
        (194, 154, "ANALYSIS TOOLS", "Deterministic calculations", ["Topology queries", "Normal-range checks", "Trend + correlation", "Event + quality detection"]),
        (380, 154, "RESPONSE COMPOSER", "Question selects an intent", ["Narrative answer", "Confidence + window", "Intent-specific layout", "A2UI message payload"]),
        (566, 190, "CLIENT EXPERIENCE", "One continuous thread", ["Native React renderer", "Trusted component catalog", "Expandable evidence", "Follow-up questions"]),
    ]
    y, h = 258, 188
    for i, (x, w, heading, subtitle, items) in enumerate(columns):
        rounded(c, x, y, w, h, PANEL, BORDER, 10)
        c.setFillColor([TEAL, BLUE, AMBER, NAVY_2][i])
        c.rect(x, y + h - 5, w, 5, fill=1, stroke=0)
        label(c, heading, x + 12, y + h - 27, [TEAL, BLUE, AMBER, BLUE_DARK][i], 7.5)
        para(c, subtitle, x + 12, y + h - 38, w - 24, 9.5, 12, INK, True)
        for j, item in enumerate(items):
            yy = y + h - 76 - j * 27
            c.setFillColor(TEAL if i != 2 else AMBER)
            c.circle(x + 16, yy + 2, 3, fill=1, stroke=0)
            c.setFillColor(MUTED)
            c.setFont("Arial", 8.5)
            c.drawString(x + 25, yy - 1, item)
        if i < len(columns) - 1:
            arrow(c, x + w + 4, y + h / 2, columns[i + 1][0] - 4, y + h / 2, BLUE)

    rounded(c, 36, 176, 720, 58, AMBER_PALE, colors.HexColor("#D7BC82"), 9)
    label(c, "DESIGNED INCIDENT", 50, 213, AMBER)
    para(c, "10:15-11:00: flow falls to <b>28.7 m3/h</b>, pressure rises to <b>5.93 bar</b>, and LT-101 climbs at <b>31.4%/h</b>. The flow-pressure correlation is <b>-0.985</b>, which is consistent with a downstream restriction signature.", 50, 203, 690, 9.5, 13, INK)

    rounded(c, 36, 93, 352, 62, TEAL_PALE, colors.HexColor("#A2CABD"), 9)
    label(c, "WHAT IS PROVEN", 50, 133, TEAL)
    para(c, "The readings, time window, limits, topology, and calculated relationships are traceable to the supplied demo inputs.", 50, 123, 324, 9, 12, INK)
    rounded(c, 404, 93, 352, 62, RED_PALE, colors.HexColor("#D7AAA5"), 9)
    label(c, "WHAT IS NOT CLAIMED", 418, 133, RED)
    para(c, "Correlation does not prove a mechanical cause. The UI says 'consistent with' and requires field confirmation.", 418, 123, 324, 9, 12, INK)
    footer(c, 3, "Project sources: backend/input_session.py, backend/analysis.py, data/plant/topology.json")
    c.showPage()


def demo_runbook(c: canvas.Canvas) -> None:
    page_header(c, "Section 1 - Workflow", 4, "A six-minute live demo runbook", "Use the sample path for reliability, then slow down at the input inspection and A2UI evidence moments.")
    rows = [
        ("0:00", "Inputs", "Choose Load sample inputs", "Both sources become visible and analysis unlocks."),
        ("0:45", "Inspection", "Open Inspect on each file", "Show diagram tags, 2,166 rows, time coverage, and quality."),
        ("1:30", "General review", "Choose Analyze these inputs", "The assistant explains the recovered state at 14:00."),
        ("2:30", "Root cause", "Ask: Why did T-101's level increase?", "Narrative + KPIs + trends + timeline + highlighted path."),
        ("4:15", "Data quality", "Ask: Which sensor readings are unreliable?", "The layout changes to a quality warning and tag table."),
        ("5:15", "Close", "Expand Supporting evidence", "Call out A2UI, the trusted catalog, and advisory boundaries."),
    ]
    x, y, w = 36, 180, 720
    col = [58, 92, 258, 312]
    c.setFillColor(NAVY_2)
    c.roundRect(x, y + 264, w, 31, 8, fill=1, stroke=0)
    headings = ["TIME", "MOMENT", "WHAT TO DO", "WHAT THE TEAM SEES"]
    xpos = [x + 10, x + col[0] + 10, x + col[0] + col[1] + 10, x + col[0] + col[1] + col[2] + 10]
    for xx, heading in zip(xpos, headings):
        c.setFillColor(colors.white)
        c.setFont("Arial-Bold", 8)
        c.drawString(xx, y + 275, heading)
    row_h = 44
    for i, row in enumerate(rows):
        yy = y + 264 - (i + 1) * row_h
        c.setFillColor(colors.white if i % 2 == 0 else colors.HexColor("#F3F7F8"))
        c.rect(x, yy, w, row_h, fill=1, stroke=0)
        c.setStrokeColor(BORDER)
        c.line(x, yy, x + w, yy)
        c.setFillColor(BLUE_DARK)
        c.setFont("Mono", 8.5)
        c.drawString(xpos[0], yy + 17, row[0])
        para(c, row[1], xpos[1], yy + 30, col[1] - 18, 9, 11, INK, True)
        para(c, row[2], xpos[2], yy + 32, col[2] - 18, 8.5, 10.5, INK)
        para(c, row[3], xpos[3], yy + 32, col[3] - 18, 8.5, 10.5, MUTED)

    speaker_note(c, "Watch how the interface changes with the question. The assistant is not merely describing a chart - it is choosing an evidence layout appropriate to the operator's intent.", 36, 86, 720)
    footer(c, 4)
    c.showPage()


def a2ui_concept(c: canvas.Canvas) -> None:
    page_header(c, "Section 2 - A2UI", 5, "A2UI in one sentence", "A2UI is a JSON-based protocol that lets an agent describe a user interface while the client retains control of the components, design system, and rendering behavior.")

    rounded(c, 36, 324, 210, 126, PANEL, BORDER, 11)
    label(c, "1  AGENT / SERVER", 52, 424, BLUE)
    para(c, "Produces declarative messages describing <b>what the surface contains</b>.", 52, 405, 178, 11, 15, INK)
    rounded(c, 291, 324, 210, 126, LIGHT_BLUE, colors.HexColor("#AFC7D1"), 11)
    label(c, "2  MESSAGE PROCESSOR", 307, 424, TEAL)
    para(c, "Validates the message stream, stores component state, and reconstructs the UI tree.", 307, 405, 178, 11, 15, INK)
    rounded(c, 546, 324, 210, 126, PANEL, BORDER, 11)
    label(c, "3  NATIVE RENDERER", 562, 424, AMBER)
    para(c, "Renders only client-approved React components from the industrial catalog.", 562, 405, 178, 11, 15, INK)
    arrow(c, 251, 387, 284, 387, BLUE)
    arrow(c, 506, 387, 539, 387, BLUE)

    rounded(c, 36, 209, 720, 86, NAVY_2, NAVY_2, 11)
    label(c, "THE THREE MESSAGES USED IN FIELDGUIDE", 52, 272, colors.HexColor("#65C3AF"))
    messages = [
        ("createSurface", "Open a named rendering surface and identify the approved catalog."),
        ("updateComponents", "Send the component list: summary, KPIs, chart, timeline, diagram, and more."),
        ("updateDataModel", "Attach question, intent, and provenance data to the surface state."),
    ]
    for i, (name, body) in enumerate(messages):
        xx = 52 + i * 232
        c.setFillColor(colors.white)
        c.setFont("Mono", 9)
        c.drawString(xx, 245, name)
        para(c, body, xx, 236, 206, 8.3, 10.5, colors.HexColor("#C7D5DA"))

    rounded(c, 36, 112, 346, 70, TEAL_PALE, colors.HexColor("#9CC7B9"), 9)
    label(c, "THE IMPORTANT SAFETY PROPERTY", 50, 159, TEAL)
    para(c, "The server sends data and component descriptions - <b>not arbitrary JavaScript or executable UI code</b>.", 50, 147, 318, 9.5, 13, INK)
    rounded(c, 398, 112, 358, 70, AMBER_PALE, colors.HexColor("#D9C08B"), 9)
    label(c, "PROTOTYPE-SPECIFIC NOTE", 412, 159, AMBER)
    para(c, "A2UI supports streaming. This demo returns the three-message bundle in one local HTTP response for repeatability.", 412, 147, 330, 9.5, 13, INK)
    footer(c, 5, "A2UI Protocol v0.9: https://a2ui.org/specification/v0.9-a2ui/")
    c.showPage()


def a2ui_anatomy(c: canvas.Canvas) -> None:
    page_header(c, "Section 2 - A2UI", 6, "One question, one adaptive response surface", "The narrative remains conversational. The A2UI surface underneath it carries the visual evidence selected for that intent.")

    # Left: compact message stream
    rounded(c, 36, 124, 314, 326, NAVY, NAVY, 11)
    label(c, "SERVER RESPONSE  /  SIMPLIFIED", 52, 426, colors.HexColor("#65C3AF"))
    code = [
        '{ "version": "v0.9",',
        '  "createSurface": {',
        '    "surfaceId": "process-insight-...",',
        '    "catalogId": ".../industrial/v1"',
        '  }}',
        '',
        '{ "updateComponents": {',
        '  "components": [',
        '    { "id": "root",',
        '      "component": "ResponseLayout",',
        '      "children": ["kpis", "trend",',
        '        "timeline", "diagram", "inspection"] },',
        '    { "id": "trend",',
        '      "component": "TrendChart", ... }',
        '  ]}}',
        '',
        '{ "updateDataModel": {',
        '  "value": { "intent": "root_cause" }',
        '}}',
    ]
    c.setFillColor(colors.HexColor("#D7E5EA"))
    c.setFont("Mono", 7.4)
    yy = 402
    for line in code:
        c.drawString(52, yy, line)
        yy -= 13.2

    # Right: rendered response anatomy
    rounded(c, 378, 124, 378, 326, colors.HexColor("#F7FAFB"), BORDER, 11)
    label(c, "CLIENT-RENDERED EVIDENCE", 394, 426, BLUE)
    rounded(c, 394, 340, 346, 67, AMBER_PALE, colors.HexColor("#D9C08B"), 8)
    c.setFillColor(AMBER)
    c.rect(394, 340, 4, 67, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("Arial-Bold", 12)
    c.drawString(410, 383, "A downstream restriction is most likely")
    para(c, "Written answer + confidence + incident window", 410, 373, 310, 8.5, 11, MUTED)

    card_w = 79
    for i, (tag, value, state) in enumerate([("LT-101", "78.7 %", AMBER), ("PT-101", "5.93 bar", RED), ("FT-101", "28.7", AMBER), ("FV-101", "82 %", TEAL)]):
        xx = 394 + i * 87
        rounded(c, xx, 278, card_w, 49, colors.white, BORDER, 6)
        c.setFillColor(state)
        c.rect(xx, 278, 3, 49, fill=1, stroke=0)
        c.setFillColor(MUTED)
        c.setFont("Mono", 6.5)
        c.drawString(xx + 9, 313, tag)
        c.setFillColor(INK)
        c.setFont("Arial-Bold", 10)
        c.drawString(xx + 9, 293, value)

    # Mini trend
    rounded(c, 394, 198, 214, 65, colors.white, BORDER, 7)
    c.setStrokeColor(colors.HexColor("#D8E2E6"))
    for j in range(1, 4):
        c.line(405, 204 + j * 13, 595, 204 + j * 13)
    c.setStrokeColor(BLUE)
    c.setLineWidth(2)
    points = [(405, 247), (445, 243), (480, 229), (520, 215), (555, 221), (595, 244)]
    for p1, p2 in zip(points, points[1:]): c.line(p1[0], p1[1], p2[0], p2[1])
    c.setStrokeColor(RED)
    points = [(405, 214), (445, 219), (480, 230), (520, 248), (555, 241), (595, 217)]
    for p1, p2 in zip(points, points[1:]): c.line(p1[0], p1[1], p2[0], p2[1])

    rounded(c, 620, 198, 120, 65, colors.white, BORDER, 7)
    label(c, "TIMELINE", 631, 247, BLUE, 6.5)
    for i, text in enumerate(["Flow low", "Pressure high", "Level rising"]):
        c.setFillColor(AMBER if i < 2 else RED)
        c.circle(633, 232 - i * 13, 2.5, fill=1, stroke=0)
        c.setFillColor(MUTED)
        c.setFont("Arial", 6.8)
        c.drawString(642, 230 - i * 13, text)

    rounded(c, 394, 140, 346, 43, LIGHT_BLUE, colors.HexColor("#B7CCD5"), 7)
    process_route(c, 410, 162, .58, warning=True)

    # Numbered annotations
    annotations = [
        ("1", "Surface + catalog establish the contract."),
        ("2", "Root child IDs define the response composition."),
        ("3", "The renderer turns approved types into native UI."),
    ]
    for i, (number, body) in enumerate(annotations):
        xx = 36 + i * 242
        c.setFillColor([TEAL, BLUE, AMBER][i])
        c.circle(xx + 12, 91, 11, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Arial-Bold", 8)
        c.drawCentredString(xx + 12, 88, number)
        para(c, body, xx + 31, 100, 194, 8.2, 10.5, INK)
    footer(c, 6, "Prototype: backend/a2ui_payload.py + client A2UI renderer")
    c.showPage()


def catalog_and_trust(c: canvas.Canvas) -> None:
    page_header(c, "Section 2 - A2UI", 7, "The restricted catalog is the control point", "FieldGuide does not let the server invent arbitrary widgets. The client and server share one industrial catalog with ten approved component types.")

    components = [
        ("ResponseLayout", "Root composition"),
        ("OperationalSummary", "Narrative status"),
        ("KpiGrid", "Measured values"),
        ("TrendChart", "Correlated signals"),
        ("IncidentTimeline", "Event sequence"),
        ("ProcessDiagram", "Affected topology"),
        ("InspectionPanel", "Field checks"),
        ("EquipmentTable", "Tag inventory"),
        ("SensorQualityWarning", "Data limitations"),
        ("StatusState", "Loading / errors"),
    ]
    for i, (name, purpose) in enumerate(components):
        row, col = divmod(i, 5)
        x = 36 + col * 146
        y = 336 - row * 81
        rounded(c, x, y, 134, 66, PANEL, BORDER, 8)
        c.setFillColor([TEAL, BLUE, AMBER, BLUE_DARK, TEAL][col])
        c.rect(x, y, 4, 66, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont("Arial-Bold", 8.7)
        c.drawString(x + 12, y + 42, name)
        c.setFillColor(MUTED)
        c.setFont("Arial", 8)
        c.drawString(x + 12, y + 22, purpose)

    gates = [
        ("Catalog gate", "Every component type must be in the approved industrial catalog."),
        ("Schema gate", "Required properties, confidence ranges, severities, and child references are checked."),
        ("Tree gate", "A root is required; IDs must be unique; all referenced children must exist."),
        ("Renderer gate", "The browser renders application-owned React code through the official message processor."),
    ]
    label(c, "VALIDATION BEFORE RENDER", 36, 240)
    for i, (heading, body) in enumerate(gates):
        x = 36 + i * 180
        rounded(c, x, 139, 168, 84, LIGHT_BLUE if i % 2 == 0 else TEAL_PALE, colors.HexColor("#B4C9D2"), 8)
        c.setFillColor(TEAL if i % 2 == 0 else BLUE_DARK)
        c.circle(x + 18, 197, 8, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Arial-Bold", 7)
        c.drawCentredString(x + 18, 194.5, str(i + 1))
        para(c, heading, x + 32, 205, 122, 9, 11, INK, True)
        para(c, body, x + 12, 180, 144, 8, 10.2, MUTED)

    speaker_note(c, "A2UI moves the flexibility boundary: the server can choose the composition, but the client still owns which components exist and how they behave.", 36, 78, 720)
    footer(c, 7, "A2UI catalogs: https://a2ui.org/concepts/catalogs/")
    c.showPage()


def benefits(c: canvas.Canvas) -> None:
    page_header(c, "Section 2 - A2UI", 8, "Why this matters beyond the proof of concept", "A2UI gives the team a path from a reliable demo to richer agent experiences without surrendering interface governance.")

    # Comparison
    rounded(c, 36, 297, 226, 148, PANEL, BORDER, 10)
    label(c, "TEXT-ONLY ASSISTANT", 52, 420, MUTED)
    para(c, "The user must interpret prose, find the relevant trend, connect the tags, and decide what to inspect.", 52, 396, 194, 11, 15, INK)
    c.setFillColor(MUTED)
    c.setFont("Arial-Bold", 9)
    c.drawString(52, 321, "One answer shape for every question")

    rounded(c, 282, 297, 474, 148, TEAL_PALE, colors.HexColor("#97C6B7"), 10)
    label(c, "A2UI EVIDENCE ASSISTANT", 298, 420, TEAL)
    para(c, "The response combines plain language with the right native visual surface: KPIs for status, trends for correlation, a timeline for sequence, a P&ID for topology, or a quality warning for unreliable data.", 298, 396, 442, 11, 15, INK)
    c.setFillColor(TEAL)
    c.setFont("Arial-Bold", 9)
    c.drawString(298, 321, "The layout adapts while design and safety controls remain stable")

    benefits = [
        ("Adaptive", "Question intent changes the evidence layout."),
        ("Governed", "Only approved component schemas can render."),
        ("Explainable", "Narrative, values, time windows, and visuals stay attached."),
        ("Consistent", "The client's design system controls the final experience."),
        ("Portable", "The protocol can target web, mobile, and desktop renderers."),
        ("Extensible", "Add approved components without rewriting the whole agent."),
    ]
    label(c, "BUSINESS + PRODUCT BENEFITS", 36, 271)
    for i, (heading, body) in enumerate(benefits):
        row, col = divmod(i, 3)
        x = 36 + col * 240
        y = 188 - row * 74
        rounded(c, x, y, 228, 61, colors.white, BORDER, 8)
        c.setFillColor([TEAL, BLUE, AMBER][col])
        c.circle(x + 19, y + 31, 9, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Arial-Bold", 7.5)
        c.drawCentredString(x + 19, y + 28.5, str(i + 1))
        para(c, heading, x + 36, y + 47, 178, 9.5, 11, INK, True)
        para(c, body, x + 36, y + 32, 178, 8.1, 10, MUTED)

    rounded(c, 36, 47, 720, 44, NAVY_2, NAVY_2, 8)
    c.setFillColor(colors.white)
    c.setFont("Arial-Bold", 10.5)
    c.drawString(50, 70, "Closing message")
    para(c, "FieldGuide is not just a chatbot on top of historian data. It is a controlled method for turning engineering context and operating evidence into an interface the user can inspect, question, and trust.", 145, 79, 594, 9, 11.5, colors.HexColor("#D8E4E8"))
    footer(c, 8, "Sources: a2ui.org and the A2UI client setup guide")
    c.showPage()


def build() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle("FieldGuide Process Insights - Workflow and A2UI Demo Guide")
    c.setAuthor("FieldGuide Process Insights")
    c.setSubject("Demo workflow and A2UI architecture")
    cover(c)
    workflow_overview(c)
    workflow_architecture(c)
    demo_runbook(c)
    a2ui_concept(c)
    a2ui_anatomy(c)
    catalog_and_trust(c)
    benefits(c)
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    build()
