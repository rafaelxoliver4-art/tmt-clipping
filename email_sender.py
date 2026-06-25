# email_sender.py — Render the daily TMT News Clipping as HTML and email it.
#
# Credentials come from .env (FROM_EMAIL + EMAIL_APP_PASSWORD). Recipients come
# from config.EMAIL_RECIPIENTS. Transport: iCloud SMTP with STARTTLS.

import os
import re
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from typing import Dict, List, Optional

from config import LOCAL_TZ, SECTOR_ORDER, EMAIL_RECIPIENTS

try:
    import link_resolver
    _LINK_RESOLVER_OK = True
except Exception as _e:
    link_resolver = None
    _LINK_RESOLVER_OK = False
    print(f"  [WARN] link_resolver unavailable ({_e}); falling back to "
          f"Google search URLs only.")


def _resolve_report_links(report: Dict) -> None:
    """
    Walk the curated report and resolve every item's `link` field in place.
    Items whose link is a news.google.com redirect are decoded to the real
    publisher URL; failures fall back to a Google search URL.
    """
    if not _LINK_RESOLVER_OK:
        return
    all_items: List[Dict] = []
    for sector, items in report.items():
        if sector == "_raw" or not isinstance(items, list):
            continue
        all_items.extend(items)
    if not all_items:
        return
    counters = link_resolver.resolve_items(all_items)
    total = sum(counters.values())
    print(f"  Link resolver: {counters['resolved']} decoded, "
          f"{counters['cached']} cached, "
          f"{counters['fallback']} fallback to search, "
          f"{counters['passthrough']} pass-through "
          f"(of {total} items)")

# 2026-05-22: switched from iCloud (smtp.mail.me.com) to Gmail. Gmail SMTP
# requires an App Password (not the account password) — generate at
# https://myaccount.google.com/apppasswords and put in .env as EMAIL_APP_PASSWORD.
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


# ── Tiny .env loader — no third-party dependency ──────────────────────────────
def _load_env() -> None:
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            val = val.strip().strip('"').strip("'")
            os.environ.setdefault(key.strip(), val)


# ── Tag rendering ─────────────────────────────────────────────────────────────
# Tags come from Claude in one of four shapes:
#   - covered ticker        → "AMX", "VIVT3"          (uppercase)
#   - peer company name     → "OPENAI", "EVERTEC"     (uppercase)
#   - country code          → "MX", "BR"              (uppercase)
#   - theme / "Sector"      → "Broadband", "Sector"   (title case)
# The user asked for tickers in caps lock. We force uppercase for short alpha-
# numeric tags and leave mixed-case ones (themes, "Sector") alone.
def _format_tag(tag: str) -> str:
    tag = (tag or "Sector").strip() or "Sector"
    if tag.lower() == "sector":
        return "Sector"
    # Mixed-case means Claude sent a theme tag ("Broadband", "Regulatory",
    # "M&A") — trust it and return as-is. All-lower or all-upper means a
    # ticker / peer / country code — force uppercase.
    has_lower = any(c.islower() for c in tag)
    has_upper = any(c.isupper() for c in tag)
    if has_lower and has_upper:
        return tag
    return tag.upper()


# ── HTML rendering ────────────────────────────────────────────────────────────
_STYLE_BODY    = "font-family: Arial, Helvetica, sans-serif; font-size: 11pt; color: #1c1c1c; line-height: 1.45; max-width: 760px;"
_STYLE_TITLE   = "color: #1A2B4A; margin: 0 0 4px 0; font-size: 18pt;"
_STYLE_DATE    = "color: #6B7E99; margin: 0 0 12px 0; font-size: 10pt;"
_STYLE_HR_TOP  = "border: 0; border-top: 1.5px solid #1A2B4A; margin: 0 0 12px 0;"
_STYLE_HR_MID  = "border: 0; border-top: 1px solid #d0d8e4; margin: 24px 0 16px 0;"
_STYLE_SECTOR  = "font-weight: bold; font-size: 12pt; color: #1A2B4A; margin: 18px 0 4px 0;"
_STYLE_EVENTS  = "font-weight: bold; font-size: 12pt; color: #1A2B4A; margin: 24px 0 4px 0;"
_STYLE_UL      = "margin: 0 0 8px 0; padding-left: 22px;"
_STYLE_LI      = "margin: 2px 0;"
_STYLE_LINK    = "color: #1c1c1c; text-decoration: underline;"
_STYLE_SOURCE  = "color: #9AAAB8; font-size: 9pt;"


def _format_published(raw: str) -> str:
    """
    Normalise a published_local string for display next to source name.
      "2026-05-19 14:30"  → "19 May 14:30"
      "2026-05-19"        → "19 May"
      ""                  → "date unknown"   (was: empty; clearer for analyst)
    Falls back to the raw value if parsing fails.
    """
    if not raw or not raw.strip():
        return "date unknown"
    raw = raw.strip()
    from datetime import datetime as _dt
    for fmt, out_fmt in (
        ("%Y-%m-%d %H:%M:%S", "%d %b %H:%M"),
        ("%Y-%m-%d %H:%M",     "%d %b %H:%M"),
        ("%Y-%m-%d",            "%d %b"),
        ("%Y-%m-%dT%H:%M:%S",   "%d %b %H:%M"),
    ):
        try:
            return _dt.strptime(raw, fmt).strftime(out_fmt)
        except ValueError:
            continue
    return raw  # unknown format — pass through
_STYLE_FOOTER  = "color: #9AAAB8; font-size: 8pt; margin-top: 20px;"

# ── Analytical note styles ────────────────────────────────────────────────────
_STYLE_HIGHLIGHTS_HDR = "font-weight: bold; font-size: 13pt; color: #1A2B4A; margin: 16px 0 12px 0;"
_STYLE_NOTE_BOX       = ("background: #f4f7fb; border-left: 4px solid #1A2B4A; "
                         "padding: 12px 16px 12px 16px; margin: 0 0 16px 0; "
                         "border-radius: 0 4px 4px 0;")
_STYLE_NOTE_HEADLINE  = "font-size: 12pt; font-weight: bold; color: #1A2B4A; margin: 0 0 8px 0;"
_STYLE_NOTE_SUBHDR    = "font-weight: bold; font-size: 10.5pt; color: #2c2c2c; margin: 10px 0 3px 0;"
_STYLE_NOTE_TAKE_HDR  = ("font-weight: bold; font-size: 10.5pt; color: #1A2B4A; "
                         "margin: 12px 0 4px 0;")
_STYLE_NOTE_TAKE_BODY = ("font-size: 10.5pt; color: #333; font-style: italic; "
                         "background: #eaf0f8; padding: 8px 10px; margin: 0; "
                         "border-radius: 3px;")
_STYLE_NOTE_UL        = "margin: 4px 0 4px 0; padding-left: 18px;"
_STYLE_NOTE_LI        = "margin: 3px 0; font-size: 10.5pt; line-height: 1.5;"


def _bold_md(text: str) -> str:
    """Convert **text** markdown to <strong>text</strong> in already-escaped HTML."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


def _note_to_html(note_text: str) -> str:
    """Convert a plain-text News Writer note to styled HTML."""
    lines = note_text.strip().splitlines()
    parts = [f'<div style="{_STYLE_NOTE_BOX}">']
    in_bullets = False
    in_take    = False
    take_lines: List[str] = []

    def flush_take():
        nonlocal take_lines
        if take_lines:
            combined = " ".join(take_lines).strip()
            parts.append(f'<p style="{_STYLE_NOTE_TAKE_BODY}">{_bold_md(escape(combined))}</p>')
            take_lines = []

    for line in lines:
        s = line.strip()
        if not s:
            continue

        if s.startswith("📍"):
            # ── Note headline ───────────────────────────────────────────────
            if in_bullets:
                parts.append("</ul>")
                in_bullets = False
            flush_take()
            in_take = False
            parts.append(f'<p style="{_STYLE_NOTE_HEADLINE}">{escape(s)}</p>')

        elif s.lower().startswith("what happened"):
            # ── Section header ──────────────────────────────────────────────
            if in_bullets:
                parts.append("</ul>")
                in_bullets = False
            flush_take()
            in_take = False
            parts.append(f'<p style="{_STYLE_NOTE_SUBHDR}">What happened:</p>')
            parts.append(f'<ul style="{_STYLE_NOTE_UL}">')
            in_bullets = True

        elif s.startswith("🔎"):
            # ── UBS take header ─────────────────────────────────────────────
            if in_bullets:
                parts.append("</ul>")
                in_bullets = False
            flush_take()
            in_take = True
            parts.append(f'<p style="{_STYLE_NOTE_TAKE_HDR}">{escape(s)}</p>')

        elif in_take:
            # ── Take body (accumulate multi-line takes) ─────────────────────
            take_lines.append(s)

        elif (s.startswith("•") or s.startswith("-")) and in_bullets:
            # ── Bullet point ────────────────────────────────────────────────
            content = s.lstrip("•-").strip()
            parts.append(
                f'<li style="{_STYLE_NOTE_LI}">{_bold_md(escape(content))}</li>'
            )

        elif not in_bullets:
            # ── Fallback: sub-headline or note subtitle ─────────────────────
            parts.append(
                f'<p style="font-size: 9.5pt; color: #555; margin: 0 0 6px 0;">'
                f'{escape(s)}</p>'
            )

    if in_bullets:
        parts.append("</ul>")
    flush_take()
    parts.append("</div>")
    return "\n".join(parts)


def _render_notes(notes: List[str]) -> str:
    """Render the analytical notes section (appears below the clipping and events)."""
    if not notes:
        return ""
    parts = [
        f'<hr style="{_STYLE_HR_MID}"/>',
        f'<p style="{_STYLE_HIGHLIGHTS_HDR}">Today\'s Highlights:</p>',
    ]
    for note in notes:
        if note.strip():
            parts.append(_note_to_html(note))
    return "\n".join(parts)


def _render_item(item: Dict) -> str:
    tag      = escape(_format_tag(item.get("ticker", "Sector")))
    headline = escape((item.get("headline") or "").strip())
    link     = (item.get("link") or "").strip()
    source   = escape((item.get("source") or "").strip())
    date_str = _format_published(item.get("date") or "")

    if link.startswith("http"):
        safe_link = escape(link, quote=True)
        title_html = f'<a href="{safe_link}" style="{_STYLE_LINK}">{headline}</a>'
    else:
        title_html = headline

    if source and date_str:
        source_html = f' <span style="{_STYLE_SOURCE}">— {source} · {escape(date_str)}</span>'
    elif source:
        source_html = f' <span style="{_STYLE_SOURCE}">— {source}</span>'
    elif date_str:
        source_html = f' <span style="{_STYLE_SOURCE}">— {escape(date_str)}</span>'
    else:
        source_html = ""
    return f'<li style="{_STYLE_LI}">{tag}: {title_html}{source_html}</li>'


def _render_events(events: List[Dict]) -> str:
    if not events:
        return ""
    parts = [f'<p style="{_STYLE_EVENTS}">Next Results/Events:</p>',
             f'<ul style="{_STYLE_UL}">']
    for ev in events:
        date_tag = (ev.get("date") or "TBD").strip()
        try:
            d = datetime.strptime(date_tag, "%Y-%m-%d")
            date_tag = d.strftime("%b-%d")
        except Exception:
            pass
        tag   = escape(_format_tag(ev.get("ticker_or_name") or "Sector"))
        event = escape((ev.get("event") or "").strip())
        parts.append(
            f'<li style="{_STYLE_LI}">{tag}: {event} '
            f'<span style="{_STYLE_SOURCE}">— {escape(date_tag)}</span></li>'
        )
    parts.append("</ul>")
    return "\n".join(parts)


# ── Markdown rendering (for Obsidian vault write-back) ───────────────────────
def render_markdown(report: Dict, events: List[Dict],
                    notes: Optional[List[str]] = None) -> str:
    """
    Render the same digest as a markdown document for the Obsidian vault.
    The News Writer project consumes this directly — this is the closing of
    the loop between scraper output and report drafting.
    """
    _resolve_report_links(report)
    now      = datetime.now(LOCAL_TZ)
    date_str = now.strftime("%Y-%m-%d")
    long_date = now.strftime("%A, %B %d, %Y")

    out: List[str] = [
        "---",
        f"date: {date_str}",
        f"type: tmt-news-clipping",
        f"generated_by: News Scraper Claude",
        f"timestamp: {now.isoformat()}",
        "---",
        "",
        f"# TMT News Clipping — {now.strftime('%d %b %Y')}",
        "",
        f"*{long_date}*",
        "",
        "---",
        "",
    ]

    def _md_item(item: Dict) -> str:
        tag      = _format_tag(item.get("ticker", "Sector"))
        headline = (item.get("headline") or "").strip()
        link     = (item.get("link") or "").strip()
        source   = (item.get("source") or "").strip()
        date_str = _format_published(item.get("date") or "")
        if link.startswith("http"):
            head = f"[{headline}]({link})"
        else:
            head = headline
        if source and date_str:
            src_tag = f" — *{source} · {date_str}*"
        elif source:
            src_tag = f" — *{source}*"
        elif date_str:
            src_tag = f" — *{date_str}*"
        else:
            src_tag = ""
        return f"- **{tag}:** {head}{src_tag}"

    for sector in SECTOR_ORDER:
        items = report.get(sector, [])
        if not items:
            continue
        out.append(f"## {sector}")
        out.append("")
        for it in items:
            out.append(_md_item(it))
        out.append("")

    extra = [s for s in report.keys() if s not in SECTOR_ORDER and s != "_raw"]
    for sector in extra:
        items = report.get(sector, [])
        if not items:
            continue
        out.append(f"## {sector}")
        out.append("")
        for it in items:
            out.append(_md_item(it))
        out.append("")

    if events:
        out.append("## Next Results/Events")
        out.append("")
        for ev in events:
            date_tag = (ev.get("date") or "TBD").strip()
            try:
                d = datetime.strptime(date_tag, "%Y-%m-%d")
                date_tag = d.strftime("%b-%d")
            except Exception:
                pass
            tag   = _format_tag(ev.get("ticker_or_name") or "Sector")
            event = (ev.get("event") or "").strip()
            out.append(f"- **{tag}:** {event} — *{date_tag}*")
        out.append("")

    if notes:
        out.append("---")
        out.append("")
        out.append("## Today's Highlights")
        out.append("")
        for note in notes:
            note_clean = note.strip()
            if note_clean:
                out.append(note_clean)
                out.append("")
                out.append("---")
                out.append("")

    return "\n".join(out)


def save_to_vault(report: Dict, events: List[Dict],
                  notes: Optional[List[str]] = None,
                  vault_clippings_dir: Optional[str] = None) -> Optional[str]:
    """
    Save the daily clipping as markdown to the Obsidian vault so the News
    Writer project can consume it. Returns the path written, or None on failure.
    Default destination: ~\\Documentos\\Obsidian Vault\\raw\\clippings\\YYYY-MM-DD.md
    """
    if vault_clippings_dir is None:
        vault_clippings_dir = os.path.join(
            os.path.expanduser("~"),
            "OneDrive", "Documentos", "Obsidian Vault",
            "raw", "clippings",
        )
    try:
        os.makedirs(vault_clippings_dir, exist_ok=True)
        date_str = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
        path     = os.path.join(vault_clippings_dir, f"{date_str}.md")
        md       = render_markdown(report, events, notes)
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        return path
    except OSError as e:
        print(f"  [WARN] Could not save to vault: {e}")
        return None


def render_html(report: Dict, events: List[Dict],
                notes: Optional[List[str]] = None) -> str:
    # Resolve news.google.com URLs to real publisher URLs before render.
    # Idempotent — safe to call twice (cache short-circuits).
    _resolve_report_links(report)

    now      = datetime.now(LOCAL_TZ)
    date_str = now.strftime("%d %b %Y")

    parts = [f'<div style="{_STYLE_BODY}">']
    parts.append(f'<h2 style="{_STYLE_TITLE}">TMT News Clipping — {date_str}</h2>')
    parts.append(f'<p style="{_STYLE_DATE}">{now.strftime("%A, %B %d, %Y")}</p>')
    parts.append(f'<hr style="{_STYLE_HR_TOP}"/>')

    for sector in SECTOR_ORDER:
        items = report.get(sector, [])
        if not items:
            continue
        parts.append(f'<p style="{_STYLE_SECTOR}">{escape(sector)}:</p>')
        parts.append(f'<ul style="{_STYLE_UL}">')
        for item in items:
            parts.append(_render_item(item))
        parts.append("</ul>")

    # Catch any sectors Claude invented that aren't in SECTOR_ORDER
    extra = [s for s in report.keys() if s not in SECTOR_ORDER and s != "_raw"]
    for sector in extra:
        items = report.get(sector, [])
        if not items:
            continue
        parts.append(f'<p style="{_STYLE_SECTOR}">{escape(sector)}:</p>')
        parts.append(f'<ul style="{_STYLE_UL}">')
        for item in items:
            parts.append(_render_item(item))
        parts.append("</ul>")

    parts.append(_render_events(events))

    # ── Analytical notes (below clipping + events) ────────────────────────────
    if notes:
        parts.append(_render_notes(notes))

    parts.append(
        f'<p style="{_STYLE_FOOTER}">Auto-generated '
        f'{now.strftime("%Y-%m-%d %H:%M %Z")} · TMT News Scraper</p>'
    )
    parts.append("</div>")
    return "\n".join(p for p in parts if p)


def _count_items(report: Dict) -> int:
    return sum(len(v) for v in report.values() if isinstance(v, list))


# ── SMTP send ─────────────────────────────────────────────────────────────────
def send(report: Dict, events: List[Dict],
         recipients: List[str] = None,
         notes: Optional[List[str]] = None) -> int:
    """Render and send the digest. Returns number of items in the email."""
    _load_env()
    from_email = os.environ.get("FROM_EMAIL", "").strip()
    password   = os.environ.get("EMAIL_APP_PASSWORD", "").strip()
    if not from_email or not password:
        raise RuntimeError(
            "FROM_EMAIL and EMAIL_APP_PASSWORD must be set in .env"
        )

    to_list  = recipients or EMAIL_RECIPIENTS
    date_str = datetime.now(LOCAL_TZ).strftime("%d %b %Y")
    subject  = f"TMT News Clipping — {date_str}"
    html     = render_html(report, events, notes=notes)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_email
    msg["To"]      = ", ".join(to_list)
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(from_email, password)
        server.send_message(msg, from_addr=from_email, to_addrs=to_list)

    return _count_items(report)


def send_alert(subject: str, body: str, to: Optional[List[str]] = None) -> bool:
    """Send a short PLAIN-TEXT operational alert (e.g. curation / Claude-CLI auth
    failure) so a broken run actively notifies the operator, instead of only
    being noticed later as a missing or degraded clipping. Returns True if sent.
    (2026-06-25)"""
    from config import ALERT_EMAIL
    _load_env()
    from_email = os.environ.get("FROM_EMAIL", "").strip()
    password   = os.environ.get("EMAIL_APP_PASSWORD", "").strip()
    to_list    = to or ALERT_EMAIL
    if not from_email or not password or not to_list:
        return False
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"]    = from_email
    msg["To"]      = ", ".join(to_list)
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo(); server.starttls(); server.ehlo()
            server.login(from_email, password)
            server.send_message(msg, from_addr=from_email, to_addrs=to_list)
        return True
    except Exception:
        return False


def run(report: Dict, events: List[Dict],
        recipients: List[str] = None,
        notes: Optional[List[str]] = None) -> int:
    return send(report, events, recipients, notes=notes)


if __name__ == "__main__":
    sample_report = {
        "Telecom LatAm and World": [
            {"ticker": "AMX", "headline": "Claro Brasil apresenta solucoes com 5G e IA",
             "source": "Teletime", "link": "https://example.com/1"},
            {"ticker": "MX",  "headline": "Mexico iniciara registro obligatorio de usuarios",
             "source": "El Economista", "link": "https://example.com/2"},
            {"ticker": "Sector", "headline": "Conatel investiga posible fraude en licitacion 5G",
             "source": "DPL News", "link": "https://example.com/3"},
        ],
        "Software and AI": [
            {"ticker": "TOTVS", "headline": "TOTVS concluira aquisicao da Linx",
             "source": "Valor", "link": "https://example.com/4"},
            {"ticker": "OPENAI", "headline": "OpenAI Sora soars to No. 1 on Apple App Store",
             "source": "TechCrunch", "link": "https://example.com/5"},
        ],
    }
    sample_events = [
        {"date": "2026-05-07", "ticker_or_name": "VTEX", "event": "Q1 2026 Earnings"},
        {"date": "2026-05-12", "ticker_or_name": "VIVT3", "event": "Q1 2026 Earnings Call"},
    ]
    html = render_html(sample_report, sample_events)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_email_preview.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Preview written to: {out}")
