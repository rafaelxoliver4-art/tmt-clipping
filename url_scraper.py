# url_scraper.py — direct source scraper with RSS-first strategy
#
# Strategy per source:
#   1. If the source has an "rss" URL → parse as RSS/Atom (fast, reliable)
#   2. Otherwise → fetch HTML and extract headline links (fragile fallback)
#
# RSS is dramatically more reliable than HTML scraping for JS-heavy sites.

from urllib.request import urlopen, Request
from urllib.parse import urlparse
from html.parser import HTMLParser
from datetime import datetime, timezone, timedelta
from time import sleep
import ssl, socket, os, sys, re
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import DIRECT_SOURCES, LOCAL_TZ, MAX_AGE_HOURS, current_max_age_hours

INSECURE_ENV_FLAG = os.environ.get("GNEWS_INSECURE", "0") == "1"
MAX_PER_SOURCE    = 30   # was 10. Bumped 2026-05-22 — analyst flagged that
                         # material direct-source stories (e.g. Telesíntese
                         # 850 MHz debate) were beyond the top-10 cutoff and
                         # never made it into the curator's input.
MAX_WORKERS       = 12   # parallel site fetches

# ── SSL context ───────────────────────────────────────────────────────────────
def _ssl_context():
    ctx = ssl.create_default_context()
    if INSECURE_ENV_FLAG:
        ctx.check_hostname = False
        ctx.verify_mode    = ssl.CERT_NONE
    return ctx

_SSL = _ssl_context()

HEADERS_HTML = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,es;q=0.7",
}
HEADERS_RSS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/rss+xml,application/xml,application/atom+xml,*/*;q=0.8",
}


def _fetch(url: str, timeout: int = 18,
           headers: Dict = None) -> Optional[bytes]:
    req = Request(url, headers=headers or HEADERS_HTML)
    for attempt in range(2):
        try:
            with urlopen(req, timeout=timeout, context=_SSL) as r:
                return r.read()
        except Exception as e:
            if attempt == 1:
                return None
            sleep(0.4)
    return None


# ── RSS / Atom parser ─────────────────────────────────────────────────────────
_ATOM_NS = "http://www.w3.org/2005/Atom"

def _parse_rss(xml_bytes: bytes, source_name: str, sector: str,
               base_url: str, max_age_hours: int = None) -> List[Dict]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []

    # Resolve at call time so Monday's 72h window always wins
    if max_age_hours is None:
        max_age_hours = current_max_age_hours()
    now    = datetime.now(LOCAL_TZ)
    cutoff = now - timedelta(hours=max_age_hours)
    results = []
    seen    = set()

    def _make_row(title, link, pub_date_str):
        title = title.strip()
        if not title or title in seen:
            return
        if len(title) < 20 or len(title) > 250:
            return
        seen.add(title)
        results.append({
            "title":           title,
            "link":            link.strip() if link else "",
            "source":          source_name,
            "published_local": pub_date_str,
            "keyword":         sector,
            "edition_lang":    "mixed",
            "edition_country": "mixed",
            "source_type":     "direct",
        })

    def _parse_pubdate(raw: str):
        """Return one of:
          - formatted "YYYY-MM-DD HH:MM" — date parsed and within window
          - "TOO_OLD"  — date parsed but older than cutoff (reject)
          - ""         — no parseable date (KEEP with empty date marker)
        Iteration 2026-05-22: undated items used to be dropped, then we noticed
        that loses important news with weak date markup. Now we KEEP undated
        items with an empty date string; downstream renders them as
        "(date unknown)" and the curator decides materiality by title.
        """
        if not raw:
            return ""  # missing pubDate — keep with unknown date
        # Try RFC 2822 (RSS)
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(raw.strip())
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            local = dt.astimezone(LOCAL_TZ)
            if local >= cutoff:
                return local.strftime("%Y-%m-%d %H:%M")
            return "TOO_OLD"   # parseable but stale — reject
        except Exception:
            pass
        # Try ISO 8601 (Atom)
        try:
            raw_clean = raw.strip().rstrip("Z")
            if "+" in raw_clean[10:]:
                raw_clean = raw_clean[:raw_clean.rindex("+")]
            dt = datetime.fromisoformat(raw_clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            local = dt.astimezone(LOCAL_TZ)
            if local >= cutoff:
                return local.strftime("%Y-%m-%d %H:%M")
            return "TOO_OLD"
        except Exception:
            pass
        # Unparseable date — keep with unknown date (was: drop; lost news)
        return ""

    # ── RSS 2.0 ───────────────────────────────────────────────────────────────
    channel = root.find("channel")
    if channel is not None:
        for item in channel.findall("item"):
            if len(results) >= MAX_PER_SOURCE:
                break
            title   = item.findtext("title") or ""
            link    = item.findtext("link") or ""
            pub_raw = item.findtext("pubDate") or ""
            pub_str = _parse_pubdate(pub_raw)
            if pub_str == "TOO_OLD":
                continue   # date parsed and old — drop
            # pub_str is either "" (date unknown) or "YYYY-MM-DD HH:MM"
            _make_row(title, link, pub_str)
        return results

    # ── Atom ──────────────────────────────────────────────────────────────────
    ns = {"a": _ATOM_NS}
    for entry in root.findall("a:entry", ns):
        if len(results) >= MAX_PER_SOURCE:
            break
        title   = (entry.findtext("a:title", namespaces=ns) or "").strip()
        # Atom link is an element with href attribute
        link_el = entry.find("a:link", ns)
        link    = (link_el.get("href", "") if link_el is not None else "")
        pub_raw = (entry.findtext("a:published", namespaces=ns)
                   or entry.findtext("a:updated", namespaces=ns) or "")
        pub_str = _parse_pubdate(pub_raw)
        if pub_str == "TOO_OLD":
            continue
        _make_row(title, link, pub_str)

    return results


def _fetch_rss(source: Dict) -> List[Dict]:
    rss_url = source.get("rss", "").strip()
    if not rss_url:
        return []
    data = _fetch(rss_url, headers=HEADERS_RSS)
    if not data:
        return []
    rows = _parse_rss(data, source["name"], source["sector"], source["url"])

    # ── Shallow-feed pagination (2026-07-14) ─────────────────────────────────
    # Some WordPress feeds expose only ~10 items (DPL News ≈ 2h of news!), so
    # stories published between runs — and the whole weekend — scroll off
    # before we ever fetch. For sources with "rss_pages": N in DIRECT_SOURCES,
    # also fetch ?paged=2..N (WP returns progressively older posts). On 72h
    # (Monday) windows the page count is tripled (capped at 15) to reach the
    # weekend. Stops early once a whole page falls outside the lookback window.
    pages = int(source.get("rss_pages", 1) or 1)
    if pages > 1:
        if current_max_age_hours() == 72:
            pages = min(15, pages * 3)
        sep = "&" if "?" in rss_url else "?"
        seen_links  = {r.get("link", "") for r in rows}
        seen_titles = {r.get("title", "") for r in rows}
        for p in range(2, pages + 1):
            data_p = _fetch(f"{rss_url}{sep}paged={p}", headers=HEADERS_RSS)
            if not data_p:
                break
            page_rows = _parse_rss(data_p, source["name"], source["sector"],
                                   source["url"])
            fresh = [r for r in page_rows
                     if r.get("link", "") not in seen_links
                     and r.get("title", "") not in seen_titles]
            if not page_rows:
                # every item on this page is outside the window (or feed ended)
                break
            for r in fresh:
                seen_links.add(r.get("link", ""))
                seen_titles.add(r.get("title", ""))
                rows.append(r)
    return rows


# ── Headline text cleaner ─────────────────────────────────────────────────────
_BY_AUTHOR = re.compile(
    r"\s*By\s+[A-Z][a-z]+\s+[A-Z][a-z]+.*$",   # "By Maxwell Cooter Apr 17..."
    re.DOTALL,
)
_DATE_PREFIX = re.compile(
    r"^\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s+",
    re.IGNORECASE,
)
_PRESS_RELEASE_PREFIX = re.compile(
    r"^(?:\d{1,2}\s+\w+\s+\d{4}\s+)?Press release\s+",
    re.IGNORECASE,
)
_TIMEREAD_SUFFIX = re.compile(r"\s*\d+\s+min(?:ute)?\s*read$", re.IGNORECASE)
_MONTH_DATE = re.compile(
    r"\s*[|]\s*(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}",
    re.IGNORECASE,
)

def _clean_title(text: str) -> str:
    text = _BY_AUTHOR.sub("", text)
    text = _PRESS_RELEASE_PREFIX.sub("", text)
    text = _DATE_PREFIX.sub("", text)
    text = _TIMEREAD_SUFFIX.sub("", text)
    text = _MONTH_DATE.sub("", text)
    return text.strip()


# URL patterns that suggest OLD pinned/archived content (reject these)
_OLD_YEAR_IN_URL = re.compile(r"/20(1[0-9]|2[0-2])/")   # 2010–2022 in URL path

# URLs that are clearly navigation/taxonomy pages, not articles
_NAV_URL = re.compile(
    r"/(category|categories|tag|tags|author|autores|autor|topic|seccion"
    r"|section|label|search|buscar|pagina|page|arquivo|archive)/",
    re.IGNORECASE,
)


# ── HTML fallback ─────────────────────────────────────────────────────────────
# URL patterns that strongly suggest an article link
_ARTICLE_PATTERNS = re.compile(
    r"(/\d{4}/\d{2}/|/article/|/news/|/noticias?/|/novedades/"
    r"|/post/|/story/|/noticia/|/reportagem/|/conteudo/|/telecomunicaciones/"
    r"|-\d{4,}|/\d{6,}/)",
    re.IGNORECASE,
)
# Classes / ids to skip (nav, footer, etc.)
_SKIP_CLASSES = frozenset({
    "nav", "menu", "footer", "header", "sidebar", "breadcrumb",
    "pagination", "tag", "category", "cookie", "subscribe",
    "newsletter", "social", "share", "related", "author", "byline",
    "comment", "advertisement", "promo", "banner", "widget",
})


class _HeadlineParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self._parsed  = urlparse(base_url)
        self.headlines: List[Dict] = []
        self._in_a     = False
        self._href     = ""
        self._cls      = ""
        self._text     = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        d = dict(attrs)
        self._href  = d.get("href", "") or ""
        self._cls   = (d.get("class", "") or "").lower()
        self._text  = []
        self._in_a  = True

    def handle_endtag(self, tag):
        if tag != "a" or not self._in_a:
            return
        self._in_a = False
        text = " ".join("".join(self._text).split())
        href = self._href

        # Skip navigation-like links
        if any(skip in self._cls for skip in _SKIP_CLASSES):
            return
        # Text quality checks
        if len(text) < 30 or len(text) > 250:
            return
        if not re.search(r"[a-zA-ZÀ-ú]", text):
            return
        if text == text.upper() and len(text) > 20:
            return
        # Reject if text looks like a URL (Accenture newsroom pattern)
        if text.startswith("http") or text.startswith("/"):
            return
        # Reject if it's mostly digits / date strings (Fusões e Aquisições pattern)
        digit_ratio = sum(c.isdigit() for c in text) / len(text)
        if digit_ratio > 0.25:
            return
        # Reject concatenated date strings like "31 de dezembro de 202519 de janeiro"
        if re.search(r"\d{4}\d{2}\s+de\s", text):
            return
        # Reject pure category/tag labels (short single-word or label patterns)
        word_count = len(text.split())
        if word_count < 5:
            return

        # Clean metadata from text (author bylines, date prefixes, etc.)
        text = _clean_title(text)
        if len(text) < 25:
            return

        # Resolve relative URLs
        if href.startswith("/"):
            href = f"{self._parsed.scheme}://{self._parsed.netloc}{href}"
        elif not href.startswith("http"):
            href = ""

        # Reject URLs with old years (pinned/archived historical posts)
        if href and _OLD_YEAR_IN_URL.search(href):
            return
        # Reject taxonomy/navigation URLs (categories, tags, authors, etc.)
        if href and _NAV_URL.search(href):
            return

        # Prefer URLs that look like articles
        score = 1 if (href and _ARTICLE_PATTERNS.search(href)) else 0
        self.headlines.append({"title": text, "link": href, "score": score})

    def handle_data(self, data):
        if self._in_a:
            self._text.append(data)


def _fetch_html(source: Dict) -> List[Dict]:
    data = _fetch(source["url"])
    if not data:
        return []

    # Detect charset
    charset = "utf-8"
    try:
        import re as _re
        ct_match = _re.search(rb'charset=["\']?([a-zA-Z0-9_\-]+)', data[:2000])
        if ct_match:
            charset = ct_match.group(1).decode("ascii", errors="replace")
    except Exception:
        pass

    try:
        html = data.decode(charset, errors="replace")
    except (LookupError, UnicodeDecodeError):
        html = data.decode("utf-8", errors="replace")

    parser = _HeadlineParser(source["url"])
    try:
        parser.feed(html)
    except Exception:
        pass

    # Sort: article-patterned URLs first, then by order of appearance
    candidates = sorted(parser.headlines, key=lambda h: (-h["score"],))
    today_str  = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
    now_local  = datetime.now(LOCAL_TZ)
    max_age_h  = current_max_age_hours()
    cutoff     = now_local - timedelta(hours=max_age_h)
    seen       = set()
    results    = []

    # 2026-05-22 fix: extract dates from URLs when possible to filter old items.
    import re as _re
    DATE_PATTERNS = [
        (_re.compile(r"/(\d{4})/(\d{1,2})/(\d{1,2})(?:/|-)"), lambda y,m,d: (int(y), int(m), int(d))),
        (_re.compile(r"[-/](\d{4})-(\d{1,2})-(\d{1,2})[-/]"), lambda y,m,d: (int(y), int(m), int(d))),
        (_re.compile(r"/(\d{1,2})/(\d{1,2})/(\d{4})/"), lambda d,m,y: (int(y), int(m), int(d))),
    ]

    # 2026-05-22 fix #2: extract dates from listing HTML context near each link.
    # Most sites include dates inline that the SAX parser misses. Examples:
    #   CIO:      <span itemprop="datePublished" content="2026-05-15T...">
    #   Globant:  <p class="date">18 May 2026</p>
    #   Generic:  <time datetime="2026-05-22">...</time>
    # Patterns in priority order (most reliable first).
    MONTH_MAP = {
        'jan': 1, 'january': 1, 'janeiro': 1, 'enero': 1,
        'feb': 2, 'february': 2, 'fevereiro': 2, 'febrero': 2,
        'mar': 3, 'march': 3, 'março': 3, 'marzo': 3, 'marco': 3,
        'apr': 4, 'april': 4, 'abril': 4,
        'may': 5, 'maio': 5, 'mayo': 5,
        'jun': 6, 'june': 6, 'junho': 6, 'junio': 6,
        'jul': 7, 'july': 7, 'julho': 7, 'julio': 7,
        'aug': 8, 'august': 8, 'agosto': 8,
        'sep': 9, 'sept': 9, 'september': 9, 'setembro': 9, 'septiembre': 9,
        'oct': 10, 'october': 10, 'outubro': 10, 'octubre': 10,
        'nov': 11, 'november': 11, 'novembro': 11, 'noviembre': 11,
        'dec': 12, 'december': 12, 'dezembro': 12, 'diciembre': 12,
    }
    CTX_PATTERNS = [
        # schema.org itemprop=datePublished content="ISO date"
        (_re.compile(r'itemprop=["\']datePublished["\']\s+content=["\'](\d{4})-(\d{1,2})-(\d{1,2})', _re.I),
         lambda y,m,d: (int(y), int(m), int(d))),
        # HTML5 <time datetime="ISO date">
        (_re.compile(r'<time[^>]+datetime=["\'](\d{4})-(\d{1,2})-(\d{1,2})', _re.I),
         lambda y,m,d: (int(y), int(m), int(d))),
        # ISO date in any attribute: data-date="2026-05-15", content="2026-05-15"
        (_re.compile(r'(?:datetime|data-date|date|content|published)=["\'](\d{4})-(\d{1,2})-(\d{1,2})', _re.I),
         lambda y,m,d: (int(y), int(m), int(d))),
    ]

    def _date_from_url(url: str):
        for pat, builder in DATE_PATTERNS:
            m = pat.search(url)
            if not m:
                continue
            try:
                y, mo, d = builder(*m.groups())
                if 2020 <= y <= 2030 and 1 <= mo <= 12 and 1 <= d <= 31:
                    from datetime import date as _date
                    return _date(y, mo, d)
            except Exception:
                continue
        return None

    def _date_from_ctx(ctx: str):
        """Extract a date from a ~1500-char chunk of HTML surrounding a link."""
        # Try ISO-style patterns first (most reliable)
        for pat, builder in CTX_PATTERNS:
            m = pat.search(ctx)
            if m:
                try:
                    y, mo, d = builder(*m.groups())
                    if 2020 <= y <= 2030 and 1 <= mo <= 12 and 1 <= d <= 31:
                        from datetime import date as _date
                        return _date(y, mo, d)
                except Exception:
                    pass
        # Written-out month: "18 May 2026" or "May 18, 2026" or "18 de mayo de 2026"
        # English/Portuguese/Spanish month names supported via MONTH_MAP.
        # Pattern A: DD Month YYYY (incl. "de" connector)
        for m in _re.finditer(r'\b(\d{1,2})\s*(?:de\s+)?([A-Za-zçãéíóúÁÉÍÓÚÇÃ]+)\s*(?:de\s+)?(\d{4})\b', ctx):
            d, mo_name, y = m.groups()
            mo_num = MONTH_MAP.get(mo_name.lower())
            if mo_num and 2020 <= int(y) <= 2030 and 1 <= int(d) <= 31:
                from datetime import date as _date
                return _date(int(y), mo_num, int(d))
        # Pattern B: Month DD, YYYY
        for m in _re.finditer(r'\b([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})\b', ctx):
            mo_name, d, y = m.groups()
            mo_num = MONTH_MAP.get(mo_name.lower())
            if mo_num and 2020 <= int(y) <= 2030 and 1 <= int(d) <= 31:
                from datetime import date as _date
                return _date(int(y), mo_num, int(d))
        # Pattern C: numeric DD/MM/YYYY (Brazilian / Latin-American convention).
        # Used by gov.br portals (Anatel, CADE, Anvisa) and many BR/MX news sites.
        # Always parsed as DD/MM/YYYY here — accept some US date ambiguity in
        # exchange for catching the bulk of LatAm sites correctly.
        for m in _re.finditer(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', ctx):
            d, mo, y = m.groups()
            d_i, mo_i, y_i = int(d), int(mo), int(y)
            if 2020 <= y_i <= 2030 and 1 <= mo_i <= 12 and 1 <= d_i <= 31:
                from datetime import date as _date
                return _date(y_i, mo_i, d_i)
        return None

    for h in candidates:
        if len(results) >= MAX_PER_SOURCE:
            break
        title = h["title"]
        if title in seen:
            continue

        from datetime import datetime as _dt, time as _time, date as _date

        # 1. Try URL date pattern (most reliable when present)
        pub_date = _date_from_url(h["link"])
        # 2. If no URL date, look in surrounding HTML context AFTER the link.
        # Window AFTER the link only — listings usually put dates inside the
        # same <a> element as the link, after the href attribute. Going
        # backward risks picking up the date of the PREVIOUS article.
        # Window is generous (5000 chars) to handle CIO-style "featured"
        # cards with rich image/summary markup that pushes the date span
        # 3000+ chars after the link. The </a> early-termination scopes
        # us to the current anchor element so we don't bleed into the next.
        if pub_date is None and h.get("link"):
            link = h["link"]
            idx = html.find(link)
            # 2026-05-22 fix: some sites (Ecommerce Brasil etc.) use RELATIVE
            # URLs (/noticias/foo) in HTML but SAX parser stores them
            # absolute. Try the relative version too.
            if idx < 0:
                try:
                    from urllib.parse import urlparse
                    p = urlparse(link)
                    if p.path:
                        rel = p.path + (("?" + p.query) if p.query else "")
                        idx = html.find('"' + rel + '"')
                        if idx >= 0:
                            idx += 1   # skip the opening quote
                            link = rel
                except Exception:
                    pass
            if idx >= 0:
                # Simple fixed 5000-char window starting at idx. Since we
                # start AT the current link's href, the FIRST date pattern
                # in the window is always this article's date. No need for
                # smart boundaries — the page is rendered top-down and the
                # date follows the title closely on every layout we've seen.
                # This is more robust than </a> or path-prefix boundaries
                # (which broke for sites with author links or absolute URLs).
                ctx = html[idx:idx + 5000]
                pub_date = _date_from_ctx(ctx)
        # 3. Apply date filter
        if pub_date is not None:
            pub_dt = _dt.combine(pub_date, _time(12, 0)).replace(tzinfo=LOCAL_TZ)
            if pub_dt < cutoff:
                continue  # parseable + stale — drop
            pub_str = pub_date.strftime("%Y-%m-%d")
        else:
            # No date in URL or listing context — keep with empty date.
            # Downstream renders as "(date unknown)"; curator decides materiality.
            # (Iteration: was today_str — but that disguised old items as fresh.)
            pub_str = ""

        seen.add(title)
        results.append({
            "title":           title,
            "link":            h["link"],
            "source":          source["name"],
            "published_local": pub_str,
            "keyword":         source["sector"],
            "edition_lang":    "mixed",
            "edition_country": "mixed",
            "source_type":     "direct",
        })
    return results


# ── Per-source orchestrator ───────────────────────────────────────────────────
def scrape_site(source: Dict) -> List[Dict]:
    # Try RSS first — much more reliable
    if source.get("rss"):
        rows = _fetch_rss(source)
        if rows:
            return rows

    # HTML fallback
    return _fetch_html(source)


# ── Main ──────────────────────────────────────────────────────────────────────
def run(existing_headlines: List[Dict] = None) -> List[Dict]:
    if existing_headlines is None:
        existing_headlines = []
    existing_titles = {x["title"].lower() for x in existing_headlines}

    total    = len(DIRECT_SOURCES)
    all_rows = []
    done     = 0

    print(f"  Direct scrape: {total} sources, {MAX_WORKERS} threads", flush=True)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(scrape_site, src): src for src in DIRECT_SOURCES}
        for future in as_completed(futures):
            done += 1
            pct = int(done / total * 100)
            src = futures[future]
            print(
                f"\r  Direct [{pct:3d}%]  {done}/{total}  {src['name'][:35]:<35}",
                end="", flush=True,
            )
            try:
                all_rows.extend(future.result())
            except Exception as e:
                print(f"\n  [WARN] {src['name']} -> {e}", file=sys.stderr)

    print()

    # Dedup against gnews + internally
    seen: set = set()
    final: List[Dict] = []
    for x in all_rows:
        key = x["title"].lower()
        if key not in existing_titles and key not in seen:
            seen.add(key)
            final.append(x)
    return final


if __name__ == "__main__":
    rows = run()
    print(f"\nDirect scrape: {len(rows)} headlines")
    for r in rows[:10]:
        method = "RSS" if r.get("source_type") == "direct" else "HTML"
        print(f"  [{r['source']}] {r['title'][:80]}")
