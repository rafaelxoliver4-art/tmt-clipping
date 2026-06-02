# generate_report.py — Build the daily TMT News Clipping PDF

import os
from datetime import datetime
from typing import Dict, List

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from config import LOCAL_TZ, OUTPUT_DIR

# ── Sector display order ──────────────────────────────────────────────────────
SECTOR_ORDER = [
    "Telecom LatAm",
    "Telecom Brazil",
    "IT Services",
    "Software & AI",
    "Ecommerce",
    "Hardware",
    "Streaming",
    "General",
]

# ── Colour palette ────────────────────────────────────────────────────────────
COLOR_ACCENT    = colors.HexColor("#1A2B4A")   # dark navy — title / footer rule
COLOR_SUBACCENT = colors.HexColor("#2E5F9E")   # medium blue — sector titles
COLOR_DIVIDER   = colors.HexColor("#C8D4E3")   # light blue — inter-sector rules
COLOR_TEXT      = colors.HexColor("#1C1C1C")   # body text

HEX_TICKER    = "2E5F9E"   # covered ticker labels
HEX_SECTOR    = "6B7E99"   # "Sector" tag (peers)
HEX_SOURCE    = "9AAAB8"   # muted source attribution
HEX_TEXT      = "1C1C1C"   # headline body
HEX_FULLNOTE  = "1B7340"   # Full Note badge (dark green)
HEX_WHY       = "5A7A5A"   # why-it-matters annotation (muted green)

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm


def _styles():
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            fontName="Helvetica-Bold", fontSize=16,
            textColor=COLOR_ACCENT, leading=20, alignment=TA_LEFT,
        ),
        "date": ParagraphStyle(
            "DateLine",
            fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#6B7E99"), leading=12, alignment=TA_LEFT,
        ),
        "sector_header": ParagraphStyle(
            "SectorHeader",
            fontName="Helvetica-Bold", fontSize=11,
            textColor=COLOR_SUBACCENT, leading=16, spaceBefore=4,
        ),
        "news_item": ParagraphStyle(
            "NewsItem",
            fontName="Helvetica", fontSize=9,
            textColor=COLOR_TEXT, leading=13, leftIndent=12, spaceAfter=3,
        ),
        "events_header": ParagraphStyle(
            "EventsHeader",
            fontName="Helvetica-Bold", fontSize=11,
            textColor=COLOR_ACCENT, leading=16, spaceBefore=4,
        ),
        "event_item": ParagraphStyle(
            "EventItem",
            fontName="Helvetica", fontSize=9,
            textColor=COLOR_TEXT, leading=13, leftIndent=12, spaceAfter=3,
        ),
        "footer": ParagraphStyle(
            "Footer",
            fontName="Helvetica", fontSize=7.5,
            textColor=colors.HexColor("#9AAAB8"), leading=10, alignment=TA_CENTER,
        ),
        "raw": ParagraphStyle(
            "Raw",
            fontName="Courier", fontSize=7,
            textColor=COLOR_TEXT, leading=10,
        ),
        "why_text": ParagraphStyle(
            "WhyText",
            fontName="Helvetica-Oblique", fontSize=8,
            textColor=colors.HexColor(f"#{HEX_WHY}"), leading=11,
            leftIndent=24, spaceAfter=4,
        ),
    }

S = _styles()


def _ticker_tag(ticker: str) -> str:
    if not ticker or ticker == "Sector":
        return f'<font color="#{HEX_SECTOR}" size="9"><b>Sector</b></font>'
    return f'<font color="#{HEX_TICKER}" size="9"><b>{ticker}</b></font>'


def _news_line(item: Dict) -> List[Paragraph]:
    """Return 1 or 2 Paragraphs: headline (+ optional why line for Full Note)."""
    ticker        = item.get("ticker", "Sector")
    headline      = item.get("headline", "")
    source        = item.get("source", "")
    link          = item.get("link", "")
    triage        = item.get("triage", "Other News")
    why           = item.get("why", "")
    running_story = item.get("running_story", "")

    if len(headline) > 180:
        headline = headline[:177] + "..."

    headline = (headline
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))

    ticker_html = _ticker_tag(ticker)
    source_html = f' <font color="#{HEX_SOURCE}" size="8">— {source}</font>' if source else ""

    if link and link.startswith("http"):
        headline_html = f'<a href="{link}" color="#{HEX_TEXT}">{headline}</a>'
    else:
        headline_html = f'<font color="#{HEX_TEXT}">{headline}</font>'

    if triage == "Full Note":
        badge = f'<font color="#{HEX_FULLNOTE}" size="8"><b>[FULL NOTE]</b></font> '
        bullet = f"• {badge}{ticker_html}: {headline_html}{source_html}"
    else:
        bullet = f"• {ticker_html}: {headline_html}{source_html}"

    paras: List[Paragraph] = [Paragraph(bullet, S["news_item"])]

    if triage == "Full Note" and why:
        why_clean = why.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        story_tag = ""
        if running_story:
            story_tag = (f' <font color="#{HEX_SOURCE}" size="7.5">'
                         f'[{running_story}]</font>')
        paras.append(Paragraph(
            f'<font color="#{HEX_WHY}">{why_clean}{story_tag}</font>',
            S["why_text"],
        ))

    return paras


def _add_footer(canvas, doc):
    canvas.saveState()
    now_str = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M %Z")
    p = Paragraph(
        f"TMT News Clipping — auto-generated {now_str} | For internal use only",
        S["footer"],
    )
    w, h = A4
    p.wrapOn(canvas, w - 2 * MARGIN, 20)
    p.drawOn(canvas, MARGIN, 10 * mm)
    canvas.restoreState()


def build_pdf(report: Dict, events: List[Dict], output_path: str) -> str:
    os.makedirs(
        os.path.dirname(output_path) if os.path.dirname(output_path) else ".",
        exist_ok=True,
    )

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=22 * mm,
    )

    today    = datetime.now(LOCAL_TZ)
    # Cross-platform: use today.day (int) instead of %-d / %#d
    date_str = f"{today.day}/{today.strftime('%b').upper()}"  # e.g. "2/MAR"

    story = []

    # ── Title block ───────────────────────────────────────────────────────────
    story.append(Paragraph(f"TMT News Clipping — {date_str}", S["title"]))
    story.append(Paragraph(today.strftime("%A, %B %d, %Y"), S["date"]))
    story.append(Spacer(1, 3 * mm))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=COLOR_ACCENT, spaceAfter=4 * mm))

    # ── Sectors ───────────────────────────────────────────────────────────────
    sectors_printed = 0
    for sector in SECTOR_ORDER:
        items = report.get(sector, [])
        if not items:
            continue

        if sectors_printed > 0:
            story.append(HRFlowable(
                width="100%", thickness=0.5,
                color=COLOR_DIVIDER, spaceBefore=3 * mm, spaceAfter=3 * mm,
            ))

        story.append(Paragraph(sector, S["sector_header"]))
        story.append(Spacer(1, 1 * mm))

        for item in items:
            story.extend(_news_line(item))

        sectors_printed += 1

    # Fallback if Claude returned raw text instead of JSON
    if "_raw" in report:
        story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_DIVIDER,
                                spaceBefore=3 * mm, spaceAfter=3 * mm))
        story.append(Paragraph("Raw Output (JSON parse error)", S["sector_header"]))
        story.append(Paragraph(report["_raw"][:3000], S["raw"]))

    # ── Next Results / Events ─────────────────────────────────────────────────
    if events:
        story.append(HRFlowable(
            width="100%", thickness=1.5,
            color=COLOR_ACCENT, spaceBefore=5 * mm, spaceAfter=3 * mm,
        ))
        story.append(Paragraph("Next Results / Events", S["events_header"]))
        story.append(Spacer(1, 1 * mm))

        for ev in events:
            date_tag = ev.get("date", "TBD")
            try:
                d = datetime.strptime(date_tag, "%Y-%m-%d")
                date_tag = d.strftime("%b-%d")
            except Exception:
                pass

            ticker = ev.get("ticker_or_name", "Sector") or "Sector"
            event  = ev.get("event", "")
            color  = HEX_TICKER if ticker not in ("Sector", "") else HEX_SECTOR
            text   = (
                f'• <font color="#{color}" size="9"><b>{ticker}</b></font>: '
                f'{event} <font color="#{HEX_SOURCE}" size="8">— {date_tag}</font>'
            )
            story.append(Paragraph(text, S["event_item"]))

    doc.build(story, onFirstPage=_add_footer, onLaterPages=_add_footer)
    return output_path


def run(report: Dict, events: List[Dict]) -> str:
    today_str   = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
    filename    = f"TMT_News_Clipping_{today_str}.pdf"
    output_path = os.path.join(OUTPUT_DIR, filename)
    return build_pdf(report, events, output_path)


if __name__ == "__main__":
    sample_report = {
        "Telecom LatAm": [
            {"ticker": "AMX",    "headline": "América Móvil reporta caída de ingresos en México", "source": "El Economista", "link": ""},
            {"ticker": "Sector", "headline": "SpaceX could seek IPO valuation of over $1.75 trillion", "source": "Bloomberg", "link": ""},
        ],
        "Software & AI": [
            {"ticker": "TOTVS",  "headline": "Totvs conclui aquisição da Linx por R$7 bilhões", "source": "Valor Econômico", "link": ""},
            {"ticker": "Sector", "headline": "OpenAI raises $110B in one of the largest private rounds", "source": "Reuters", "link": ""},
        ],
        "IT Services": [
            {"ticker": "Sector", "headline": "TCS is asking staff to use AI even if it hits revenues", "source": "Economic Times", "link": ""},
        ],
    }
    sample_events = [
        {"date": "2025-05-07", "ticker_or_name": "VTEX",         "event": "Q1 2025 Earnings"},
        {"date": "2025-05-12", "ticker_or_name": "VIVT3",        "event": "Q1 2025 Earnings Call"},
        {"date": "2025-06-03", "ticker_or_name": "Sector",       "event": "MWC Americas 2025"},
    ]
    path = run(sample_report, sample_events)
    print(f"PDF saved: {path}")
