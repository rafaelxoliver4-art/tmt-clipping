# config.py — TMT News Clipping: Universe, Sectors, Sources

from zoneinfo import ZoneInfo

# ── Timezone & schedule ───────────────────────────────────────────────────────
LOCAL_TZ   = ZoneInfo("America/Sao_Paulo")
GNEWS_WHEN = "1d"  # Google News-side hint; real cutoff enforced client-side
MAX_AGE_HOURS = 24  # strict rolling window for published-at filter
SLEEP_S    = 0.5


# ── Lookback window — single source of truth ──────────────────────────────────
# Normally 24h rolling from execution time. The Monday-morning 07:00 BRT run
# extends to 72h to catch Friday afternoon + Saturday + Sunday news the team
# missed over the weekend. Monday 16:30 / 18:00 BRT runs use the normal 24h
# window because the morning run already handled the weekend gap.
# These functions are evaluated EVERY TIME — never frozen as a constant.
def current_max_age_hours() -> int:
    """Return 72 only on Monday morning (before noon BRT). 24h otherwise."""
    from datetime import datetime
    now = datetime.now(LOCAL_TZ)
    return 72 if (now.weekday() == 0 and now.hour < 12) else MAX_AGE_HOURS


def current_gnews_when() -> str:
    """Google News `when:` hint — 3d on Monday morning, 1d otherwise."""
    from datetime import datetime
    now = datetime.now(LOCAL_TZ)
    return "3d" if (now.weekday() == 0 and now.hour < 12) else GNEWS_WHEN

OUTPUT_DIR = "output"

# ── Covered-name aliases (used by enforce_covered_inclusion safety net) ─────
# Maps ticker → list of company-name strings that mean the same thing in
# news headlines. Any DIRECT-source headline containing one of these names
# is FORCE-INCLUDED in the digest (curator cannot drop it).
# Added 2026-05-25.
COVERED_NAME_ALIASES = {
    # Telecom LatAm — controlling shareholders + subsidiaries
    "AMX":     ["America Movil", "América Móvil", "AMX", "Claro Brasil",
                "Claro Mexico", "Claro México", "Claro Colombia", "Claro Chile",
                "Claro Peru", "Claro Argentina", "Telcel", "Telmex", "Sites LatAm",
                "Telesites", "Sitios LatAm", "A1", "Carlos Slim"],
    "TIGO":    ["Millicom", "Tigo", "TIGO", "Tigo Colombia", "Tigo Bolivia",
                "Tigo Guatemala", "Tigo Paraguay", "Tigo Honduras", "Tigo El Salvador",
                "Xavier Niel", "Iliad Millicom", "Atlas Investissement"],
    "TEO":     ["Telecom Argentina", "Personal Argentina", "TEO", "Cablevisión",
                "Cablevision Flow"],
    "Televisa":["Televisa", "Grupo Televisa", "TelevisaUnivision", "Univision",
                "Sky México"],
    # Telecom Brazil
    # "Vivo" alone collides with Portuguese verb (alive). Require longer forms.
    "VIVT3":   ["Vivo Telefônica", "Vivo Telefonica", "Telefonica Brasil",
                "Telefônica Brasil", "VIVT3", "Vivo 5G", "TEF Brasil",
                "Telefonica Vivo"],
    "TIMS3":   ["TIM Brasil", "TIM Participações", "TIM Part", "TIMS3",
                "TIM Inova", "Sparkle"],
    "BRISANET":["Brisanet", "BRIT3", "BRISANET", "BR Digital", "Brisa Digital"],
    "DESK":    ["Desktop telecom", "Desktop", "DESK3", "Desktop FTTH"],
    # IT Services — covered names + global peers tracked
    "GLOB":    ["Globant", "GLOB"],
    "CINT":    ["CI&T", "CINT", "CI&T Brasil"],
    "EPAM":    ["EPAM", "EPAM Systems"],
    "ENDV":    ["Endava"],
    "COG":     ["Cognizant", "COG"],
    "ACN":     ["Accenture", "ACN"],
    "INFY":    ["Infosys", "INFY"],
    "TCS":     ["Tata Consultancy", "TCS"],
    "CAP":     ["Capgemini", "CAP"],
    "WIT":     ["Wipro"],
    # Software / SaaS
    "TOTVS":   ["TOTVS", "TOTS3", "RD Station", "RDStation"],
    "LWSA":    ["Locaweb", "LWSA", "LWSA3", "Bling", "Tray", "KingHost"],
    "VTEX":    ["VTEX"],
    # Ecommerce
    "MELI":    ["Mercado Libre", "MercadoLibre", "Mercado Livre", "MELI",
                "Mercado Pago", "Mercado Envios", "Mercado Envíos", "Mercado Ads"],
    # Hardware
    "POSI":    ["Positivo Tecnologia", "POSI", "POSI3", "Positivo Casa Inteligente",
                "Quantum smartphones"],
    "INTB":    ["Intelbras", "INTB", "INTB3"],
    "MLAS":    ["Magazine Luiza", "Magalu", "MGLU", "MGLU3", "MLAS", "KaBuM",
                "Estante Virtual"],
}


# ── Coverage Universe — Sectors ───────────────────────────────────────────────
SECTORS = {
    "Telecom LatAm and World": {
        "covered": ["AMX", "TIGO", "TEO", "Televisa", "Millicom", "Telecom Argentina"],
        "peers": [
            "Claro", "Telcel", "Telmex", "Sites LatAm", "Telesites",
            "Claro Mexico", "Claro Colombia", "Claro Chile", "Claro Peru",
            "Claro Argentina", "Claro Brasil",
            "Tigo Colombia", "Tigo Chile", "Tigo Bolivia", "Tigo Paraguay",
            "Tigo Guatemala", "Tigo Honduras", "Tigo El Salvador",
            "Entel Chile", "Entel Peru", "Entel",
            "Movistar Mexico", "Movistar Colombia", "Movistar Chile", "Movistar Peru",
            "Telefonica Venezuela", "TEF Venezuela", "TEF Integratel", "Integratel",
            "Personal Argentina", "Liberty Latin America", "Cable & Wireless",
            "AT&T Mexico", "BAIT", "Megacable",
            "IFT", "CRT Colombia", "Subtel Chile", "Osiptel Peru", "Anatel",
            "Starlink LatAm", "SpaceX Starlink", "Ericsson", "Nokia",
        ],
        "keywords": [
            # Covered — company names
            "America Movil", "AMX", "Millicom", "Tigo", "Telecom Argentina",
            "Televisa", "TEO telecom",
            # Claro family
            "Claro", "Telcel", "Telmex", "Sites LatAm", "Telesites",
            # Other LatAm operators
            "Megacable", "AT&T Mexico", "BAIT operador",
            "Entel Chile", "Entel Peru",
            "Liberty Latin America",
            "Starlink Latin America", "Starlink Mexico",
            # Regulatory & sector
            "IFT espectro", "IFT regulacion",
            "telecomunicaciones Colombia", "telecom Chile", "telecom Peru",
            "telecom Argentina", "telecom Venezuela",
            "Telefonica Venezuela", "TEF Venezuela",
            # M&A / consolidation
            "consolidacion telecom Colombia", "consolidacion telecom LatAm",
            "Tigo Movistar Colombia",
            # Sector-level (important: no company name needed)
            "5G rollout Mexico", "5G Colombia licitacion",
            "espectro 5G Colombia", "espectro 5G Chile", "espectro 5G Peru",
            "cable submarino LatAm", "fibra Colombia", "despliegue fibra Mexico",
            "MVNO Mexico", "MVNO Colombia",
            "regulacion telecom LatAm",
            # Country-specific spectrum/operator data signals (regulator-driven)
            "Programa Nacional Espectro Mexico", "Plan Espectro Mexico",
            "espectro radioelectrico Mexico", "espectro Mexico 2026 2030",
            "CRC Colombia ranking", "CRC Colombia velocidad",
            "ranking velocidad movil Colombia", "Claro Colombia velocidad",
            "WOM Colombia", "Tigo Colombia velocidad",
            "ENACOM Argentina datos", "Argentina trafico internet",
            "Argentina datos moviles crecimiento", "IA trafico Argentina",
            # Key person — Xavier Niel (controls Millicom via Iliad/Atlas Investissement).
            # 2026-05-22: added so any deal, share buy/sell, board move, or
            # corporate action he takes lands in the TMT clipping.
            "Xavier Niel", "Niel Iliad", "Iliad Millicom", "Atlas Investissement",
            "Atlas Investissement Millicom", "Niel TIGO", "Niel Tigo",
        ],
    },

    "Telecom Brazil": {
        "covered": ["VIVT3", "TIMS3", "BRISANET", "DESK", "Desktop"],
        "peers": [
            "TIM Brasil", "Claro Brasil", "V.tal", "Anatel", "Oi",
            "Vero Telecom", "Unifique", "Desktop Telecom", "Brisanet",
            "Desk3", "Ponto ISP", "Winity", "Algar Telecom",
        ],
        "keywords": [
            # Covered
            "Vivo", "Vivo 5G", "Telefonica Brasil",
            "TIM Brasil telecom",
            "Claro Brasil",
            "Brisanet", "BRISANET",
            # Peers
            "V.tal", "Anatel",
            "Unifique", "Vero telecom", "Desktop telecom", "Desktop FTTH", "Desk3",
            "Algar Telecom", "Winity", "Oi fibra", "Oi recuperacao judicial",
            # Sector-level
            "espectro 5G Brasil", "licitacao espectro Brasil",
            "fibra optica Brasil", "FTTH Brasil",
            "ISP Brasil", "ISP consolidacao Brasil", "MVNO Brasil",
            "Anatel regulacao fibra", "5G cobertura Brasil",
            "cabos submarinos Brasil",
            # ── Fiber costs / infrastructure economics (added 2026-06-02) ──
            "custo da fibra óptica", "custo da fibra ótica", "custo de fibra óptica",
            "custo de implantação de fibra", "custo de rede de fibra",
            "investimento em fibra óptica", "custo de expansão de rede de fibra",
            # Pole access — the core fiber-cost / regulatory driver in Brazil
            # (the Aneel/Anatel/AGU pole-sharing fight drives ISP/telco fiber capex)
            "compartilhamento de postes", "Aneel postes provedores",
            "aluguel de postes telecom", "ocupação de postes fibra",
        ],
    },

    "IT Services": {
        "covered": ["CINT", "Globant", "INTB", "CI&T"],
        "peers": [
            "Accenture", "Cognizant", "TCS", "Tata Consultancy", "Infosys",
            "Wipro", "Capgemini", "EPAM", "Grid Dynamics", "Endava",
            "Atos", "IBM Services", "DXC Technology", "HCL Technologies",
            "Thoughtworks", "Stefanini",
        ],
        "keywords": [
            # Covered
            "Globant", "CI&T", "CINT",
            # Peers
            "Accenture", "Cognizant", "TCS Tata", "Infosys", "Wipro",
            "Capgemini", "EPAM", "Grid Dynamics", "Endava", "Thoughtworks",
            # Sector-level (key theme: AI disruption)
            "AI disruption IT services", "AI replacing developers",
            "AI coding tools enterprise", "generative AI outsourcing",
            "IT services headcount AI", "IT services demand AI",
            "offshore IT AI", "nearshore IT",
            "IT outsourcing AI impact",
            "AI adoption enterprise", "digital transformation LatAm",
            # Industry research (Gartner direct-scrape blocked by anti-bot;
            # this catches their published reports via Google News indexing)
            "Gartner research", "Gartner IT spending", "Gartner forecast",
            "Gartner CIO survey", "Gartner Magic Quadrant",
            # AI token-pricing / pay-to-play / consumption pricing — the
            # 2026 IT-services pricing shift that affects GLOB/CINT margins
            "AI token pricing", "tokenised pricing IT services",
            "pay-to-play AI", "AI per-token pricing",
            "Cognizant tokenised pricing", "Cognizant token framework",
            "IT services consumption pricing",
            "AI pricing model IT services", "AI billing IT services",
        ],
    },

    "Software and AI": {
        "covered": ["TOTVS", "LWSA", "VTEX"],
        "peers": [
            "SAP", "Sage", "Salesforce", "Workday", "ServiceNow",
            "Oracle", "Microsoft Copilot", "OpenAI", "Anthropic",
            "Google AI", "Gemini", "Mistral", "xAI", "Grok",
            "Cursor", "GitHub Copilot", "Omie", "Senior Sistemas",
            "Sankhya", "Linx",
        ],
        "keywords": [
            # Covered
            "TOTVS", "LWSA", "Locaweb",
            # Peers
            "SAP", "Sage software", "Salesforce", "Workday", "ServiceNow",
            "OpenAI", "Anthropic", "Claude AI",
            "GPT-5", "ChatGPT enterprise", "Gemini Google",
            "xAI Grok", "Mistral AI", "AI model launch",
            "GitHub Copilot", "Cursor AI",
            # Sector-level
            "AI agent enterprise", "agentic AI enterprise",
            "LLM enterprise", "foundation model release",
            "AI software disruption", "AI replacing software engineers",
            "vibe coding", "AI ERP",
            "ERP cloud", "ERP Brasil", "Omie", "Senior Sistemas", "Sankhya",
            "software Brasil", "SaaS Latin America",
        ],
    },

    "Ecommerce": {
        "covered": ["VTEX", "LWSA", "MLAS"],
        "peers": [
            "Mercado Libre", "Shopify", "eBay", "TikTok Shop",
            "Amazon Brasil", "Magalu", "Via Varejo", "B2W",
        ],
        "keywords": [
            "VTEX", "Mercado Libre", "MELI", "Shopify",
            "TikTok Shop", "e-commerce Brasil", "ecommerce Latin America",
            "marketplace Brasil", "Amazon Brasil", "D2C Brazil",
            "logistica ecommerce", "Magalu", "LWSA ecommerce",
        ],
    },

    "Hardware": {
        "covered": ["POSI", "INTB", "MLAS"],
        "peers": ["Apple", "Samsung", "Xiaomi", "Motorola", "IDC",
                  "Positivo Tecnologia", "Intelbras",
                  # Intelbras segment competitors (read-across)
                  "Hikvision", "Dahua", "TP-Link", "Growatt"],
        "keywords": [
            "Positivo Tecnologia", "POSI", "Intelbras", "INTB", "MLAS",
            "Apple Brasil", "Samsung Brasil", "smartphones Brasil",
            "imposto smartphones", "tarifacao eletronicos",
            "IDC smartphones", "mercado hardware Brasil",
            "Xiaomi Brasil",
            # ── Intelbras (INTB) by business segment — added 2026-06-01 ──
            # Intelbras was only matched by name; its actual segments (security,
            # networking, solar, comms) had no keywords, so segment-level and
            # read-across news never surfaced. Hardware sits at 48/80 (room).
            # Company / results
            "Intelbras resultados", "Intelbras receita", "Intelbras aquisição",
            "Intelbras guidance", "INTB3",
            # Segurança eletrônica (largest segment: CFTV, alarmes, acesso)
            "Intelbras segurança", "Intelbras câmeras",
            "segurança eletrônica Brasil", "mercado de CFTV Brasil",
            "controle de acesso Brasil",
            # Redes / conectividade (gear sold to ISPs/provedores)
            "Intelbras redes", "Intelbras roteador",
            "equipamentos para provedores de internet", "Wi-Fi 7 Brasil",
            "ONU fibra óptica Brasil",
            # Energia solar (key growth driver)
            "Intelbras energia solar", "Intelbras energia",
            "geração distribuída energia solar", "energia solar distribuída Brasil",
            "marco legal geração distribuída",
            # Comunicação
            "Intelbras PABX",
        ],
    },

    "Streaming": {
        "covered": [],
        "peers": ["Netflix", "Disney+", "Spotify", "Warner Bros Discovery",
                  "Paramount", "HBO", "YouTube Premium", "Globoplay"],
        "keywords": [
            "Netflix", "Disney Plus", "Spotify", "Warner Bros Discovery",
            "streaming Latin America", "streaming Brasil", "HBO Max",
            "Globoplay", "Paramount Plus", "streaming consolidation",
        ],
    },
}

# ── Flat keyword list (auto-derived) ──────────────────────────────────────────
def get_all_keywords():
    seen = set()
    out  = []
    for sector_data in SECTORS.values():
        for kw in sector_data["keywords"]:
            if kw not in seen:
                seen.add(kw)
                out.append(kw)
    return out

ALL_KEYWORDS = get_all_keywords()

# ── Google News editions ──────────────────────────────────────────────────────
EDITIONS = [
    {"lang": "pt-BR", "country": "BR"},
    {"lang": "es-MX", "country": "MX"},
    {"lang": "en",    "country": "US"},
]

ED_BR  = EDITIONS[0]
ED_MX  = EDITIONS[1]
ED_US  = EDITIONS[2]

# Keyword→edition routing. Most keywords only make sense in one market's edition
# (e.g. "tarifacao eletronicos" is pt-BR; "IFT espectro" is es-MX; "OpenAI" is en).
# Firing every keyword across all 3 editions = 492 queries and ~15 min runtime.
# Tightly routed = ~200 queries and ~2 min.

_PT_MARKERS = (
    "brasil", "brasileir", "anatel", " vivo", "^vivo", "brisanet", "locaweb",
    "oi fibra", "oi recuperacao", "unifique", "vero telecom", "desktop telecom",
    "algar", "winity", "desk3", "v.tal", "ftth brasil", "isp brasil",
    "isp consolidacao", "mvno brasil", "licitacao", "tarifacao",
    "imposto smartphones", "magalu", "intelbras", "positivo tecnologia",
    "xiaomi brasil", "apple brasil", "samsung brasil", "globoplay",
    "recuperacao judicial", "fibra optica brasil", "cobertura brasil",
    "cabos submarinos brasil", "regulacao", "mercado hardware brasil",
    "e-commerce brasil", "marketplace brasil", "amazon brasil", "erp brasil",
    "omie", "senior sistemas", "sankhya", "software brasil", "streaming brasil",
    "telefonica brasil", "tim brasil", "claro brasil", "fibra optica",
    "5g cobertura", "5g brasil",
)

_ES_MARKERS = (
    "america movil", "telcel", "telmex", "televisa", "mexico", "colombia",
    "chile", "peru ", "argentina", "venezuela", "entel", "movistar",
    "megacable", "bait", "at&t mexico", "ift ", "ift espectro", "ift regulacion",
    "telefonica venezuela", "tef venezuela", "consolidacion",
    "tigo movistar", "espectro 5g", "cable submarino", "fibra colombia",
    "despliegue fibra", "mvno mexico", "mvno colombia", "regulacion telecom",
    "telecomunicaciones", "starlink latin america", "starlink mexico",
    "5g rollout mexico",
)

# Tickers & global names — fire across all 3 editions.
_UNIVERSAL = (
    "amx", "tigo", "teo telecom", "millicom", "vivt3", "tims3", "brisanet",
    "cint", "globant", "ci&t", "totvs", "lwsa", "vtex", "posi", "intb",
    "mlas", "meli", "mercado libre",
)


def _match_any(text_lower: str, markers) -> bool:
    for m in markers:
        if m.startswith("^"):
            if text_lower.startswith(m[1:]):
                return True
        elif m in text_lower:
            return True
    return False


def keyword_editions(kw: str):
    """Return the editions to query for a given keyword."""
    kw_lower = kw.lower()
    if _match_any(kw_lower, _UNIVERSAL):
        return EDITIONS
    if _match_any(kw_lower, _PT_MARKERS):
        return [ED_BR]
    if _match_any(kw_lower, _ES_MARKERS):
        return [ED_MX]
    # Default: English/global tech keywords → US edition only
    return [ED_US]


def get_query_tasks():
    """Build the (keyword, edition) list with per-keyword edition routing."""
    tasks = []
    for kw in ALL_KEYWORDS:
        for ed in keyword_editions(kw):
            tasks.append((kw, ed))
    return tasks

# ── Direct sources ─────────────────────────────────────────────────────────────
# rss: tried first (RSS/Atom are far more reliable than HTML scraping)
# url: HTML fallback if rss is empty or fails
# Entries with rss="" will use HTML scraping only.

DIRECT_SOURCES = [
    # ── Technology / Software / AI ─────────────────────────────────────────────
    {
        "name": "TechCrunch",
        "url":  "https://techcrunch.com/",
        "rss":  "https://techcrunch.com/feed/",
        "sector": "Software and AI",
    },
    {
        "name": "The Verge",
        "url":  "https://www.theverge.com/",
        "rss":  "https://www.theverge.com/rss/index.xml",
        "sector": "Software and AI",
    },
    {
        "name": "The Information",
        "url":  "https://www.theinformation.com/",
        "rss":  "",   # paywall — Google News covers this
        "sector": "Software and AI",
    },
    {
        "name": "Baguete",
        "url":  "https://www.baguete.com.br/noticias",
        "rss":  "https://www.baguete.com.br/noticias/rss",
        "sector": "Software and AI",
    },
    {
        "name": "Fusões e Aquisições",
        "url":  "https://fusoesaquisicoes.com/acontece-no-setor/",
        "rss":  "https://fusoesaquisicoes.com/feed/",
        "sector": "General",
    },
    {
        "name": "Gartner Newsroom",
        "url":  "https://www.gartner.com/en/newsroom",
        "rss":  "",   # JS-rendered — Gartner reports appear in Google News
        "sector": "IT Services",
    },
    {
        "name": "Infor Channel",
        "url":  "https://inforchannel.com.br/blog/",
        "rss":  "https://inforchannel.com.br/feed/",
        "sector": "IT Services",
    },
    {
        "name": "Ecommerce Brasil",
        "url":  "https://www.ecommercebrasil.com.br/noticias",
        "rss":  "https://www.ecommercebrasil.com.br/feed/",
        "sector": "Ecommerce",
    },
    {
        "name": "Data Center Dynamics",
        "url":  "https://www.datacenterdynamics.com/en/news/",
        "rss":  "https://www.datacenterdynamics.com/en/rss/",
        "sector": "Software and AI",
    },
    {
        "name": "CIO",
        "url":  "https://www.cio.com/news/",
        "rss":  "",   # global RSS is multilingual (Korean/Japanese) — use HTML of English /news/ page
        "sector": "IT Services",
    },
    {
        # 2026-06-01: section RSS now 404s + page JS-rendered → was returning
        # 0 items. Repointed to the live canonical Valor feed (Valor Impresso
        # below carries the print tech/telecom deep-dives).
        # 2026-06-03: pointed at Valor's dedicated TECH section feed (pox, 100
        # items) instead of the general feed — de-redundifies vs Geral/Tele.
        "name": "Valor Econômico Tech",
        "url":  "https://valor.globo.com/empresas/tecnologia/",
        "rss":  "https://pox.globo.com/rss/valor/empresas/tecnologia",
        "sector": "Software and AI",
    },
    {
        "name": "TI Inside",
        "url":  "https://tiinside.com.br/top-news/",
        "rss":  "https://tiinside.com.br/feed/",
        "sector": "IT Services",
    },
    {
        "name": "Economic Times India",
        "url":  "https://economictimes.indiatimes.com/tech/information-tech",
        "rss":  "https://economictimes.indiatimes.com/tech/information-tech/rssfeeds/78570550.cms",
        "sector": "IT Services",
    },
    {
        "name": "Mercado & Consumo",
        "url":  "https://mercadoeconsumo.com.br/category/noticias/",
        "rss":  "https://mercadoeconsumo.com.br/feed/",
        "sector": "Ecommerce",
    },
    {
        "name": "Apollo Academy Daily Spark",
        "url":  "https://www.apolloacademy.com/the-daily-spark/",
        "rss":  "",   # JS-rendered; HTML fallback
        "sector": "General",
    },
    {
        "name": "Portal ERP",
        "url":  "https://portalerp.com/noticias",
        "rss":  "https://portalerp.com/feed/",   # WordPress-style guess
        "sector": "Software and AI",
    },
    {
        "name": "Portal Solar",
        "url":  "https://www.portalsolar.com.br/noticias",
        "rss":  "https://www.portalsolar.com.br/feed/",   # WordPress-style guess
        "sector": "Hardware",
    },

    # ── Company Newsrooms ──────────────────────────────────────────────────────
    {
        "name": "Globant Newsroom",
        "url":  "https://www.globant.com/news-room",
        "rss":  "",
        "sector": "IT Services",
    },
    {
        "name": "VTEX Press",
        "url":  "https://vtex.com/gb-en/press-media/",
        "rss":  "",   # JS-rendered; HTML fallback
        "sector": "Ecommerce",
    },
    {
        "name": "Accenture Newsroom",
        "url":  "https://newsroom.accenture.com/",
        "rss":  "",   # JS-rendered; HTML fallback (gnews backstop on keyword "Accenture")
        "sector": "IT Services",
    },
    {
        "name": "Capgemini News",
        "url":  "https://www.capgemini.com/news/",
        "rss":  "https://www.capgemini.com/news/feed/",
        "sector": "IT Services",
    },
    {
        "name": "EPAM Newsroom",
        "url":  "https://www.epam.com/about/newsroom",
        "rss":  "",   # HTML fallback
        "sector": "IT Services",
    },
    {
        "name": "Cognizant News",
        "url":  "https://www.cognizant.com/us/en/news",
        "rss":  "",
        "sector": "IT Services",
    },
    {
        "name": "TCS Newsroom",
        "url":  "https://www.tcs.com/who-we-are/newsroom",
        "rss":  "",   # HTML fallback
        "sector": "IT Services",
    },
    {
        "name": "Infosys Newsroom",
        "url":  "https://www.infosys.com/newsroom/press-releases.html",
        "rss":  "",   # HTML fallback
        "sector": "IT Services",
    },

    # ── Telecom LatAm ──────────────────────────────────────────────────────────
    {
        "name": "El Economista Telecom",
        "url":  "https://www.eleconomista.com.mx/tecnologia/",   # technology section only
        "rss":  "https://www.eleconomista.com.mx/rss/tecnologia.xml",
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "Cinco Días",
        "url":  "https://cincodias.elpais.com/noticias/telefonica/",
        "rss":  "https://cincodias.elpais.com/rss/",
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "El Financiero Tech",
        "url":  "https://www.elfinanciero.com.mx/tech/",   # tech section only
        "rss":  "",
        "sector": "Telecom LatAm and World",
    },
    # NOTE (2026-05-21): Reuters Telecom direct-source removed — all Reuters
    # paths return HTTP 401 (paywall + bot detection), same as WSJ. Reuters
    # stories still surface via Google News; allowlist boosts dedup priority.
    {
        "name": "FT Telecoms",
        "url":  "https://www.ft.com/telecoms",
        "rss":  "",   # FT requires subscription; HTML attempt only
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "El Economista España (Telefonica)",
        "url":  "https://www.eleconomista.es/empresa/TELEFONICA",
        "rss":  "",   # HTML fallback — Telefónica Spain coverage matters for AMX/TIGO read-across
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "Expansión Últimas Noticias",
        "url":  "https://expansion.mx/ultimas-noticias",
        "rss":  "",   # HTML fallback
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "Ookla Research",
        "url":  "https://www.ookla.com/research/reports",
        "rss":  "",   # HTML fallback
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "DPL News",
        "url":  "https://dplnews.com/category/dplnews/",
        "rss":  "https://dplnews.com/feed/",
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "DPL News Redes",
        "url":  "https://dplnews.com/category/redes/",
        "rss":  "",   # main feed already covers this
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "Mobile Time LAT",
        "url":  "https://mobiletime.la/noticias/",
        "rss":  "https://mobiletime.la/feed/",
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "Expansión Tecnología",
        "url":  "https://expansion.mx/tecnologia",
        "rss":  "",   # general feed is off-topic; scrape the /tecnologia section directly
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "El País Telecom",
        "url":  "https://elpais.com/noticias/telecomunicaciones/",
        "rss":  "",   # El País RSS is the general homepage — use HTML of telecom section
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "Ookla",
        "url":  "https://www.ookla.com/articles",
        "rss":  "",
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "BNAmericas Telecom",
        "url":  "https://www.bnamericas.com/en/news/telecommunications",
        "rss":  "",
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "TeleSemana",
        "url":  "https://www.telesemana.com/",
        "rss":  "https://www.telesemana.com/feed/",
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "Mexico Business News Tech",
        "url":  "https://mexicobusiness.news/tech",   # tech/ICT section
        "rss":  "",
        "sector": "Telecom LatAm and World",
    },

    # ── Telecom Brazil ─────────────────────────────────────────────────────────
    {
        "name": "Tele.Síntese",
        "url":  "https://telesintese.com.br/plantao-de-noticias/",
        "rss":  "https://telesintese.com.br/feed/",
        "sector": "Telecom Brazil",
    },
    {
        "name": "Teletime",
        "url":  "https://teletime.com.br/noticias/",
        "rss":  "https://teletime.com.br/feed/",
        "sector": "Telecom Brazil",
    },
    {
        "name": "Mobile Time BR",
        "url":  "https://www.mobiletime.com.br/noticias/",
        "rss":  "https://www.mobiletime.com.br/feed/",
        "sector": "Telecom Brazil",
    },
    {
        "name": "Ponto ISP",
        "url":  "https://www.pontoisp.com.br/category/noticia/",
        "rss":  "https://www.pontoisp.com.br/feed/",
        "sector": "Telecom Brazil",
    },
    {
        # 2026-06-01: section RSS now 404s → was returning 0 items. Repointed
        # to the live canonical Valor feed.
        "name": "Valor Econômico Tele",
        "url":  "https://valor.globo.com/empresas/telecom/",
        "rss":  "https://valor.globo.com/rss/valor",
        "sector": "Telecom Brazil",
    },

    # ── General / M&A ─────────────────────────────────────────────────────────
    {
        "name": "NeoFeed",
        "url":  "https://neofeed.com.br/",
        "rss":  "https://neofeed.com.br/feed/",
        "sector": "General",
    },
    {
        "name": "Brazil Journal",
        "url":  "https://braziljournal.com/",
        "rss":  "https://braziljournal.com/feed/",
        "sector": "General",
    },
    {
        # 2026-05-22: was /arc/outboundfeeds/rss/ which 404s.
        # The working pox.globo.com-style feed lives at /rss/pipelinevalor.
        "name": "Pipeline Valor",
        "url":  "https://pipelinevalor.globo.com/",
        "rss":  "https://pipelinevalor.globo.com/rss/pipelinevalor",
        "sector": "General",
    },
    {
        # 2026-06-01: arc/outboundfeeds RSS now 404s. Switched to the live
        # canonical Valor feed (advertised on the section pages) — 100 items.
        "name": "Valor Econômico Geral",
        "url":  "https://valor.globo.com/ultimas-noticias/",
        "rss":  "https://valor.globo.com/rss/valor",
        "sector": "General",
    },
    {
        # 2026-06-01: Valor PRINT edition feed (pox.globo.com) — carries the
        # high-value print pieces (telecom/tech/M&A deep-dives) that don't
        # appear in the general web feed. Mirrors the H&E pipeline fix.
        "name": "Valor Impresso",
        "url":  "https://valor.globo.com/impresso/",
        "rss":  "https://pox.globo.com/rss/valor/impresso",
        "sector": "General",
    },
    {
        "name": "Estadão",
        "url":  "https://www.estadao.com.br/ultimas/",
        "rss":  "https://www.estadao.com.br/arc/outboundfeeds/rss/",
        "sector": "General",
    },
    # NOTE (2026-05-21): WSJ cannot be added as a direct source.
    # - All public RSS feeds were deprecated Jan 2025 (last build 16+ months stale).
    # - HTML scrape returns HTTP 401 Forbidden (paywall + bot detection).
    # WSJ articles still surface via Google News — see SOURCES_ALLOWLIST below
    # where we boost WSJ-attributed items for dedup priority.

    # ── Brazilian regulators (added 2026-05-21) ───────────────────────────────
    # Official sources for FISTEL, spectrum auctions, telecom M&A approvals,
    # IT-services concentration decisions. Server-rendered HTML — scrape works.
    {
        "name": "Anatel Notícias",
        "url":  "https://www.gov.br/anatel/pt-br/assuntos/noticias",
        "rss":  "",   # gov.br portals are HTML-only (no public RSS)
        "sector": "Telecom Brazil",
    },
    {
        "name": "CADE Notícias",
        "url":  "https://www.gov.br/cade/pt-br/assuntos/noticias",
        "rss":  "",
        "sector": "General",  # antitrust covers M&A across all sectors
    },
    # NOTE: IFT (Mexico telecom regulator, ift.org.mx) is JS-rendered and the
    # HTML scrape returns no article links. IFT stories surface via Google
    # News — see SOURCES_ALLOWLIST for dedup-priority boost.

    # ── Colombian regulators (added 2026-05-21) ───────────────────────────────
    {
        "name": "CRC Colombia",
        "url":  "https://crcom.gov.co/es/noticias",
        "rss":  "",
        "sector": "Telecom LatAm and World",
    },
    {
        "name": "MinTIC Colombia",
        "url":  "https://www.mintic.gov.co/portal/inicio/Sala-de-prensa/Noticias/",
        "rss":  "",
        "sector": "Telecom LatAm and World",
    },

    # ── Bloomberg Línea family (added 2026-05-21) ─────────────────────────────
    # The Arc-CMS RSS endpoints are not advertised on the homepage but they
    # publish full feeds with 100 items each. Bloomberg.com main is paywalled
    # (HTTP 403); Bloomberg Línea is the LatAm-facing arm and is open.
    {
        "name": "Bloomberg Línea Brasil",
        "url":  "https://www.bloomberglinea.com.br/",
        "rss":  "https://www.bloomberglinea.com.br/arc/outboundfeeds/rss.xml",
        "sector": "General",
    },
    {
        "name": "Bloomberg Línea",
        "url":  "https://www.bloomberglinea.com/",
        "rss":  "https://www.bloomberglinea.com/arc/outboundfeeds/rss.xml",
        "sector": "General",
    },
    {
        "name": "Bloomberg Línea México",
        "url":  "https://www.bloomberglinea.com.mx/",
        "rss":  "https://www.bloomberglinea.com/arc/outboundfeeds/rss/latinoamerica/mexico.xml",
        "sector": "Telecom LatAm and World",
    },

    # ── Investor-relations sub-domains for covered IT-services names ──────────
    # Added 2026-05-22 — the corporate /news-room pages we scrape do NOT
    # include 8-K-style press releases (buybacks, earnings releases, board
    # changes), which live on the separate investor-relations sub-domains.
    # Analyst flagged misses: news.cognizant.com $500M ASR; investors.globant
    # CORRECTION release; investors.endava Q3 FY26 results.
    {
        "name": "Cognizant News Center",
        "url":  "https://news.cognizant.com/",
        "rss":  "",   # no public RSS; HTML scrape works
        "sector": "IT Services",
    },
    # NOTE: investors.globant.com is JS-rendered (HTML scrape returns only
    # site nav). Globant IR releases surface via gnews — see allowlist.
    {
        "name": "Endava Investor Relations",
        "url":  "https://investors.endava.com/news-events/press-releases",
        "rss":  "",
        "sector": "IT Services",
    },

    # ── Specialist additions (2026-05-22) — user-approved batch ───────────────
    {
        # GSMA-affiliated global telecom trade. 5G launches, operator strategy,
        # spectrum policy. Catches AMX/TEF international context.
        "name": "Mobile World Live",
        "url":  "https://www.mobileworldlive.com/",
        "rss":  "https://www.mobileworldlive.com/feed/",
        "sector": "Telecom LatAm and World",
    },
    {
        # Brazilian IT/telecom trade — often breaks IT-services contract wins
        # in BR market before generalist outlets.
        "name": "Convergência Digital",
        "url":  "https://www.convergenciadigital.com.br/",
        "rss":  "https://www.convergenciadigital.com.br/feed",
        "sector": "Telecom Brazil",
    },
    {
        # IT services analyst research (competes with Gartner). Covers
        # Globant/CINT/Cognizant/Accenture strategic positioning.
        "name": "Forrester Blogs",
        "url":  "https://www.forrester.com/blogs/",
        "rss":  "",   # HTML scrape — RSS deprecated
        "sector": "IT Services",
    },
    {
        # Brazilian pay-TV / streaming trade. Caught Brisanet→Sky+ early.
        "name": "TELA VIVA News",
        "url":  "https://telaviva.com.br/",
        "rss":  "https://telaviva.com.br/feed/",
        "sector": "Streaming",
    },
    {
        # US telecom industry trade — 5G, carrier strategy, equipment.
        # AMX/TEF/Millicom international context.
        "name": "Light Reading",
        "url":  "https://www.lightreading.com/",
        "rss":  "",   # RSS endpoint 404; HTML scrape (thin, ~4 articles/run)
        "sector": "Telecom LatAm and World",
    },

    # ── Brazilian financial portals (added 2026-05-22) — sell-side coverage ──
    # User flagged on 2026-05-22 that noise was coming from non-reliable
    # outlets; tightened EXT cap to 2 AND adding these mainstream BR
    # financial portals as DIRECT so sell-side coverage (BTG/Itaú BBA/XP
    # views, target-price changes, earnings recaps) flows in without
    # burning EXT slots.
    {
        "name": "InfoMoney",
        "url":  "https://www.infomoney.com.br/",
        "rss":  "https://www.infomoney.com.br/feed/",
        "sector": "Sell-side",
    },
    {
        "name": "Money Times",
        "url":  "https://www.moneytimes.com.br/",
        "rss":  "https://www.moneytimes.com.br/feed/",
        "sector": "Sell-side",
    },
    {
        "name": "Seu Dinheiro",
        "url":  "https://www.seudinheiro.com/",
        "rss":  "https://www.seudinheiro.com/feed/",
        "sector": "Sell-side",
    },
    {
        "name": "Suno",
        "url":  "https://www.suno.com.br/noticias/",
        "rss":  "https://www.suno.com.br/noticias/feed/",
        "sector": "Sell-side",
    },
]

# ── Source allowlist (used only by Google News priority ranking, not as filter) ──
SOURCES_ALLOWLIST = [
    "TechCrunch", "The Verge", "The Information", "Baguete",
    "Portal ERP", "Portal Solar", "Gartner", "Infor Channel", "Ecommerce Brasil",
    "Data Center Dynamics", "CIO", "Valor Econômico", "TI Inside",
    "Mexico Business News", "Economic Times",
    "Apollo Academy",
    "Accenture", "Capgemini", "EPAM", "Cognizant", "TCS", "Infosys", "Globant",
    "VTEX",
    "El Economista", "Cinco Días", "Cinco Dias", "El Financiero", "Reuters",
    "Financial Times", "FT", "DPL News", "Mobile Time", "Expansión", "El País",
    "Ookla", "BNAmericas", "TeleSemana",
    "Tele.Síntese", "Teletime", "TELETIME", "Ponto ISP",
    "NeoFeed", "Brazil Journal", "Pipeline Valor", "Estadão",
    "Fusões e Aquisições", "Mercado & Consumo",
    "Bloomberg", "Reuters", "AFP", "PR Newswire", "Business Wire",
    "WSJ", "Wall Street Journal", "wsj.com",  # surfaced via Google News only
    "Reuters Telecom", "Reuters Tech",  # paywalled — gnews-only
    "Bloomberg Technology", "Bloomberg",  # main Bloomberg.com paywalled — gnews-only
    "IFT", "Instituto Federal de Telecomunicaciones",  # MX regulator (JS-rendered, gnews-only)
    "CRT", "Cofetel",  # alternative Mexican telecom regulator references
    "Anatel", "CADE", "CRC", "MinTIC",  # also in direct sources — allowlist ensures dedup keeps them
    "Bloomberg Línea", "Bloomberg Linea",  # already direct — boost dedup priority
]

# ── Pre-filter caps (input to Claude; Claude does the final 50-item curation) ─
MAX_HEADLINES_PER_SECTOR = 80
MAX_TOTAL_HEADLINES      = 400

# Final Claude-curated digest cap.
# 2026-05-25: set to 60. 50 was too tight; 80 was too loose (60 material
# items in a 24h window across 2-3 daily runs is already very high without
# repetition). 60 is the right ceiling.
MAX_DIGEST_ITEMS = 60

# ── Sector display order (used by email + PDF renderers) ─────────────────────
SECTOR_ORDER = [
    "Telecom LatAm and World",
    "Telecom Brazil",
    "IT Services",
    "Software and AI",
    "Ecommerce",
    "Hardware",
    "Streaming",
    "General",
    "Sell-side",   # broker rating changes — appears last before events
]

# ── Email recipients for the daily digest ─────────────────────────────────────
EMAIL_RECIPIENTS = [
    # 2026-05-22: rafaelxoliver4@gmail.com removed at user request after the
    # switch to Gmail SMTP (sender is now ibotatom@gmail.com).
    "rafael.oliveira@ubs.com",
]
