# wiki_context.py — UBS LatAm TMT analyst domain knowledge for Claude triage
# Source: Obsidian wiki vault (NEWS_WRITER_CONTEXT.md, latam-tmt-coverage-universe.md,
#         editorial conversations Apr 2026)
# Embedded as a constant — no runtime file I/O required.

ANALYST_CONTEXT = """
## UBS LatAm TMT — Analyst Triage Context

### Triage Decision — Full Note vs. Other News vs. Omit

**Full Note** — ALL must apply:
(1) Fresh, material event: earnings/guidance/M&A, regulatory decision with concrete P&L
    impact, major AI launch reframing sector multiples, macro data with named transmission
    mechanism to a covered stock.
(2) Clear investment read-across to ≥1 covered ticker — thesis, near-term estimate, or
    valuation.
(3) New information — not a duplicate or already-known outcome.

**Other News** — sector-relevant but: no covered-ticker read-across, minor fines, routine
filings, small deals below materiality, preliminary/rumour-stage regulatory items, general
sector color, PR/ESG.

**Omit** — no TMT sector connection, duplicate story, pure PR, irrelevant geography.

---

### Explicit OMIT Examples (do NOT include these as full notes)
- Routine fines: e.g., "TIM/Procon fine R$4mn" → immaterial amount, no thesis impact
- Debt tender offers / liability management: e.g., "TV/TU tender for 8% Senior Notes"
  → routine refinancing, no P&L read-across
- CSR/ESG with no financial mechanism: renewables announcements, community programs,
  Amazon lab partnerships, sustainability pledges
- Legislative committees presenting agenda: "Frente Parlamentar presents regulatory agenda"
  → monitor, but no concrete measure passed → Other News at most
- Routine IT peer acquisitions: "Infosys acquires partner to boost AI" → brief peer color
  only, not a standalone take
- Stale news recycled with new timestamp: check if the event is genuinely fresh
- General capex/investment aggregates without operator-level breakdown: "Teles invest
  R$36bn" → only material if article has per-operator data

---

### Coverage Universe & Read-Across Triggers

**TELECOM LatAm:**
- AMX (América Móvil): brands Claro [BR/CO/CL/PE/AR], Telcel [MX], Telmex [MX fixed].
  Triggers: Mexico competition (BAIT/Walmex MVNO, AT&T MX exit, Telefónica MX exit validates
  AMX dominance), AMX/Desktop FTTH convergence in Brazil, LatAm telco M&A, Mexico
  preponderance review 2027, FCF yield vs peers, CFE government free internet programs
  competing with Telcel prepaid, convergent power post-Desktop acquisition.
- TIGO (Millicom): HN/GT/SV/BO/PA/CO (Coltel), plus Uruguay/Ecuador/Chile (TEF assets).
  Triggers: M&A pipeline execution (Peru, Venezuela), US$3/share dividend release once M&A
  clears, FCF yield, CEO/CFO comments on integration bandwidth. Note: any new market entry
  announcement reads NEUTRAL — market flags management bandwidth risk.
- TEO (Telecom Argentina): Personal mobile + Fibertel fixed. Triggers: Argentina FX/tariff
  reform, TIGO as potential acquirer.
- TV (Grupo Televisa/TelevisaUnivision): Sky + Izzi cable MX, ViX streaming.
  Triggers: pay-TV churn, F1 partnership through 2028, ViX subscriber growth.

**TELECOM Brazil:**
- VIVT3 (Vivo/TEF-BZ): Mobile market leader, FTTH expansion, dividend yield story.
  CFO David Melcon departing to Virgin Media O2 (Apr-26).
  Triggers: Anatel monthly data (postpaid net adds, portability vs AMX), price increase
  execution (postpaid/hybrid hikes Mar-26), B2B revenue growth (R$5.2bn +30% YoY,
  only 15% cross-sell penetration → large upside), AMX/Desktop FTTH competitive threat.
- TIMS3 (TIM Brasil): EBITDA margin 53.1%, div yield ~8%, guidance ~5% MSR growth 2026.
  I-Systems acquisition (CADE approved). Triggers: Anatel monthly data — TIM postpaid
  remains weak AND prepaid losses widening vs peers; possible read-across from ISPs entering
  mobile (no convergent fixed offer = structural disadvantage); B2B at R$1bn (nascent).
- BRISANET (BRIT3): Regional fiber ISP. Triggers: ISP consolidation, Anatel formalization
  policy, FTTH net adds pace vs Unifique.
- DESK (Desktop): AMX acquiring 73% for R$2.4bn (~45% premium). Triggers: Anatel approval
  timeline, deal closing, adds >40% to AMX FTTH homes passed in SP.

**IT Services:**
- GLOB (Globant): AI Pods $20mn ARR → target $60–100mn YE, margin 45–60% vs 30–40%
  traditional. FY26 guidance 0.2–2.2% FXN growth. Headcount –2.5k in 2025.
  Read-across triggers:
  • ACN large M&A (scale play) → raises GLOB/CINT as acquisition targets
  • AI startups disrupting consulting/strategy work upstream (e.g., AI doing McKinsey-style
    reports at fraction of cost) → directly threatens GLOB/CINT premium pricing
  • ACN/TCS/Cognizant headcount cuts or AI displacement announcements → demand signal
  • Anthropic/OpenAI PE/distribution plays (forward-deployed engineers model) → could
    compete with or complement IT services firms
  NOT material: routine peer acquisitions, minor partnership announcements, ESG reports.
- CINT (CI&T): FLOW AI platform ~90% internal adoption, FY26 ~15% FXN growth guidance.
  FinSvcs ~38% of revenues. Read-across: same as GLOB above. Also: Brazil AI talent pool
  deepening (universities → GPU investment, 3rd largest AI adopter country) = supports
  CI&T nearshore value proposition.

**Software & AI:**
- TOTVS (TOTS3): Dominant Brazil ERP/SMB. LYNN AI model launched Feb-26. R$300mn AI
  capex. P/E ~19x vs 22.5x 3Y avg. Key risks:
  • SAP cloud/pricing shifts (seat→token model) DIRECTLY pressure TOTVS multiples —
    include even without direct revenue impact yet
  • Anthropic/OpenAI major new model launches → software sector selloffs (perception
    effect on multiples, even before confirmed competition)
  • Brazil AI-native startups targeting regulated verticals (HR, legal, tax, regulated
    sectors = core TOTVS TAM) — Brazil is 3rd largest AI adopter globally; AI lowers
    cost to build; founders increasingly targeting complexity = structural long-term
    competitive pressure → tag as "slightly negative" even if near-term impact uncertain
- LWSA (Locaweb/Wake): Wake AI shopping agents 2H26. Locaweb Cloud (50–70% cheaper than
  AWS/Azure, BRL billing). Revenue ~R$1.1bn. Read-across: Shopify, MELI, AI agent
  commerce launches, same AI-native startup risk as TOTVS.
- VTEX: E-commerce SaaS. FY26 Adj. EBIT margin low-20%s (vs 16% FY25 — major inflection).
  Most crowded LatAm software (UBS quant score +7.60 Mar-26). Read-across: Brazil
  e-commerce GMV data, Shopify/MELI peers, AI checkout disruption.

**Hardware:**
- INTB (Intelbras): Security cameras, networking, solar. Triggers: antidumping tariffs on
  Chinese fiber optic cables (direct benefit), security market demand, PPB/IPI consultations
  on radio base station manufacturing (positioning opportunity).
- POSI (Positivo): Government procurement contracts, PPB/IPI tariff changes on
  smartphones/electronics. Same PPB consultation read-across as INTB.
- MLAS (Multilaser): Same tariff/manufacturing exposure as INTB/POSI — co-tag on
  hardware news.

---

### Second-Order Read-Across (perception and multiple effects)

A story is material even when direct financial impact is uncertain if it affects the
competitive narrative or valuation multiple for a covered stock. Examples:

- **Brazil as 3rd largest AI adopter globally** → accelerating AI-native startup formation
  targeting regulated verticals = TOTVS/LWSA moat narrative under pressure → include,
  tag "slightly negative" for TOTVS/LWSA/VTEX
- **SAP announcing token-based pricing or AI-native ERP features** → DIRECTLY frames the
  question of whether TOTVS can maintain its multiple premium → always include
- **Anthropic/OpenAI major model launch** → software sector sentiment risk; markets sell
  TOTVS/VTEX/LWSA/GLOB/CINT on AI disruption concerns even before product impact
- **CFE government free internet (Mexico)** → competes with AMX Telcel in prepaid
  segment; fits the Mexico regulatory pressure narrative → include
- **PPB consultation for radio base stations** → manufacturing requirement changes affect
  INTB/POSI competitive positioning → include even if outcome uncertain
- **ACN $5bn M&A at pace** → signals IT services consolidation dynamic; raises question
  of GLOB/CINT as acquisition targets → include with that angle
- **V.tal ownership events** (creditor suits, regulatory moves) → TIM/TEF-BZ/AMX fiber
  infrastructure access story → always material while ownership is unresolved

---

### Anatel Monthly Data (Brazil) — Standard Materiality

Anatel mobile/broadband data always triggers a full note for AMX/TEF-BZ/TIM. Frame
the headline around the 1–2 most investable data points (not a recap of all figures):
- AMX postpaid leadership / prepaid reversal → positive
- TIM prepaid widening losses / structural fixed-mobile gap → negative
- TEF-BZ price increase timing impact / strong broadband → slightly positive/neutral
- Portability data: AMX running surplus; TIM deepening deficit → ongoing theme
- ISP broadband (Desktop flat = profitability pivot confirmed; Brisanet/Unifique pace)

---

### Active Running Stories
When a headline clearly connects to one of these monitored themes, note it:
1. "AI disruption on software" — SAP/Anthropic/OpenAI launches affecting TOTVS/VTEX/LWSA/GLOB/CINT multiples
2. "ISP consolidation Brazil" — AMX/Desktop R$2.4bn deal (Anatel approval pending), Ligga/Brasil TecPar, Anatel formalization
3. "Brazil telecom regulatory" — Anatel monthly portability data, ICMS STF cases (Alagoas/MT pending), 700MHz spectrum
4. "Mexico regulatory" — AMX preponderance review 2027, Telefónica MX exit ($450mn sale), BAIT MVNO expansion, CFE internet programs
5. "LatAm telco FCF yield" — ~4ppts LTM compression; AMX compressed least → supports AMX as top pick
6. "Satellite/D2D threat" — Starlink V2 D2D 2027, AST SpaceMobile, Amazon/Globalstar vs LatAm operators
7. "TIGO M&A pipeline" — Coltel done; Peru (TEF-Integratel) and Venezuela aspirations; US$3 dividend trigger; integration bandwidth a key investor concern
8. "AI disruption IT services" — AI startups moving upstream into consulting/strategy, headcount cuts at IT majors, demand signal for GLOB/CINT
9. "V.tal ownership" — creditor suits, Anatel/regulatory moves; implications for TIM/TEF-BZ/AMX fiber access
10. "Brazil B2B telco" — Vivo R$5.2bn B2B (+30% YoY, 15% cross-sell); TIM R$1bn (nascent); Singtel entering Brazil; 18.5% IT market growth vs 9.5% expected

### Ticker Cross-Reference (editorial short forms used in the clipping)
TEF-BZ  = Vivo / Telefonica Brasil (VIVT3)  — ALWAYS use TEF-BZ, never VIVT3/VIVO
TIM     = TIM Brasil (TIMS3)                — ALWAYS use TIM, never TIMS3
AMX     = América Móvil (Claro/Telcel/Telmex/Claro Brasil)
TIGO    = Millicom
TEO     = Telecom Argentina / Personal
TV      = Grupo Televisa / TelevisaUnivision
DESK    = Desktop Telecom (AMX acquisition target — Anatel approval pending)
ACN     = Accenture (peer)
COG     = Cognizant (peer)
INFY    = Infosys (peer)
AMZN    = Amazon (peer)
MSFT    = Microsoft (peer)
TEF-MX  = Telefónica Mexico / Movistar MX (non-covered peer, relevant for AMX)
V.tal   = V.tal (Brazil fiber infra — tag with own name, not a ticker)

### Multi-Ticker Format
When a single story directly affects 2–3 covered names, join tickers with "/":
  "AMX/TEF-BZ/TIM" — story hitting all Brazil telcos (e.g. spectrum auction, court ruling)
  "GLOB/CINT"       — IT services read-across hitting both
  "VTEX/LWSA"       — ecommerce platform story hitting both
  "AMX/DESK"        — story affecting the acquisition or the combined entity
  "TOTVS/Sage"      — when both covered and peer are explicitly named with same angle
Max 3 tickers. Only use when BOTH names have a named investment angle in the headline.

### Read-Across Tag Style
For peer headlines with a clear covered-stock investment angle, lead with covered ticker:
  "TOTVS: MSFT: Microsoft Pushes Usage-Based Pricing as AI Eats into Cloud Margins"
  means TOTVS is the investment angle; MSFT is the subject of the news.
  Use this style only when the read-across is explicit and direct.
"""
