# wiki_context.py — UBS LatAm TMT analyst domain knowledge for Claude triage
# Source: Obsidian wiki vault (NEWS_WRITER_CONTEXT.md, latam-tmt-coverage-universe.md, — auto-updated 2026-05-11
#         editorial conversations Apr 2026)
# Embedded as a constant — no runtime file I/O required.

ANALYST_CONTEXT = """## UBS LatAm TMT — Analyst Triage Context

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

### Earnings / Results: covered vs. peers (CRITICAL FILTER)

This rule applies STRICTLY to results coverage of covered names. It does NOT
filter general corporate news about covered names — those stay important.

Rafael tracks earnings directly for every covered company. The clipping should
not duplicate that channel by recapping what he already follows.

**OMIT routine RESULTS COVERAGE of covered names (this is the only filter):**
- "AMX Q1 results", "TOTVS reports Q1 EBITDA", "VTEX earnings preview",
  "TIM 4Q recap", "GLOB beats consensus", "Vivo Q1 net income up X%",
  earnings call recaps, post-earnings price-action, analyst recap notes
  without rating/TP action.

**KEEP all NON-results news about covered names — this is NOT what we filter:**
- M&A / strategic deals (e.g., AMX/Desktop, TIGO/Coltel, BRISANET tower deal)
- Regulatory rulings, court decisions, spectrum auction outcomes
- Product launches, partnership announcements, new market entries
- Executive appointments OUTSIDE earnings (board changes, hires)
- Capital raises, refinancings with strategic intent
- New disclosure of segment reporting / KPIs / capital-return policy
- Any operational or competitive milestone

**KEEP earnings exceptions even for covered names:**
- Surprise material miss/beat that re-prices the thesis
- Guidance update or material outlook revision (margin guide, capex, growth)
- M&A or strategic announcement made AT the earnings call (Telefónica MX exit-class)
- CFO / CEO transition announced at results
- Earnings-tied broker rating change → Sell-side section

**ALWAYS KEEP peer earnings — read-across signal we don't get elsewhere:**
- SAP / ACN / COG / INFY / TCS / CAP / WIPRO / EPAM results → IT services & software
- OPENAI / ANTHROPIC / ORACLE / SALESFORCE / SERVICENOW launches & results → TOTVS multiples
- SHOPIFY / MELI / AMZN ecommerce results → VTEX / LWSA read-across
- TEF-MX / AT&T MX / Megacable / Liberty LatAm results → AMX / TIGO competitive context
- Apple / Samsung / Xiaomi shipment data → INTB / POSI / MLAS

**Decision test:** "Is this story PRIMARILY a results recap of a covered name?"
- YES → OMIT
- NO (any other angle, even involving the same company, or any peer) → evaluate
  normally on materiality. The default for non-routine-results stories about
  covered names is KEEP.
- Generic IT-services "AI is changing consulting" think-pieces with no named peer print,
  headcount cut, or pricing data point → at most Other News under GLOB/CINT. Past corpus
  shows GLOB/CINT joint tag accumulates the most curated items but never gets promoted
  to a note — most joint items are sector color, not investable. Reserve full notes for
  single-name prints (GLOB, CINT individually), ACN/TCS/Cognizant/Infosys/EPAM concrete
  events (earnings, guidance, layoffs, large M&A), or named pricing/headcount disclosures.

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
  announcement reads NEUTRAL — market flags management bandwidth risk. TIGO is the most
  crowded LatAm telco (Crowding +5.00 latest, up from prior month) — incremental positive
  news has higher hurdle to move the stock; negative surprises asymmetrically painful.
- TEO (Telecom Argentina): Personal mobile + Fibertel fixed. Triggers: Argentina FX/tariff
  reform, TIGO as potential acquirer, Telecom–Telefónica MX/AR merger review at competition
  authority (30-day pronouncement window).
- TV (Grupo Televisa/TelevisaUnivision): Sky + Izzi cable MX, ViX streaming.
  Triggers: pay-TV churn, F1 partnership through 2028, ViX subscriber growth.
- LILA (Liberty Latin America): coverage in initiation. Triggers: Caribbean/Panama/Chile
  ops, preferred-stock plan, quarterly results, FCF trajectory. Track as primary covered
  name in Telecom LatAm clipping section.

**TELECOM Brazil:**
- VIVT3 (Vivo/TEF-BZ): Mobile market leader, FTTH expansion, dividend yield story.
  CFO David Melcon departing to Virgin Media O2 (Apr-26). Capital Markets Day reaffirmed
  Brazil as core market (eases stake-sale risk to fund EU M&A).
  Triggers: Anatel monthly data (postpaid net adds, portability vs AMX), price increase
  execution (postpaid/hybrid hikes Mar-26), B2B revenue growth (R$5.2bn +30% YoY,
  only 15% cross-sell penetration → large upside), AMX/Desktop FTTH competitive threat
  (key driver of TEF-BZ crowding decline in latest month).
- TIMS3 (TIM Brasil): EBITDA margin 53.1%, div yield ~8%, guidance ~5% MSR growth 2026
  with 35% YoY shareholder payments increase. I-Systems acquisition (CADE approved).
  Triggers: Anatel monthly data — TIM postpaid remains weak (prepaid showed a rebound
  in Mar-26 +85k after consistent losses, watch whether it sustains); possible read-across
  from ISPs entering mobile (no convergent fixed offer = structural disadvantage);
  B2B at R$1bn (nascent); EU Digital Networks Act + potential Poste Italiane / new
  controller scenarios at parent TIM (Italy) → Brazil asset sale OR defended-and-expanded
  paths both plausible, V.tal stake sale opens negotiation space.
- BRISANET (BRIT3): Regional fiber ISP. Triggers: ISP consolidation, Anatel formalization
  policy, FTTH net adds pace vs Unifique, 700 MHz auction participation.
- DESK (Desktop): AMX acquiring 73% for R$2.4bn (~45% premium). Triggers: Anatel approval
  timeline, deal closing, adds >40% to AMX FTTH homes passed in SP. Note: DESK still
  trades and announces standalone events (dividends, results) — tag DESK by itself for
  Desktop-specific corporate actions; tag AMX/DESK only when the story affects the
  combined deal narrative.
- UNIFIQUE: coverage in initiation. Triggers: FTTH net adds vs Brisanet, 56.4% stake in
  Amazônia 5G consortium (R$15mn, 3.5 GHz licenses SP/North), Anatel approval, mobile
  expansion via 5G consortium.
- GGPS3 (Rumo GPS): coverage in initiation. Triggers: results, contracts, sector data;
  treat as standalone covered name pending full triage rules.

**IT Services:**
- GLOB (Globant): AI Pods $20mn ARR → target $60–100mn YE, margin 45–60% vs 30–40%
  traditional. FY26 guidance 0.2–2.2% FXN growth. Headcount –2.5k in 2025.
  Read-across triggers:
  • ACN large M&A (scale play) → raises GLOB/CINT as acquisition targets
  • AI startups disrupting consulting/strategy work upstream (e.g., AI doing McKinsey-style
    reports at fraction of cost) → directly threatens GLOB/CINT premium pricing
  • ACN/TCS/Cognizant/Infosys/EPAM headcount cuts, AI displacement announcements, or
    guidance cuts → demand signal (e.g., Cognizant 4,000 layoffs, weak quarterly guide)
  • Anthropic/OpenAI PE/distribution plays (forward-deployed engineers model) → could
    compete with or complement IT services firms
  • Partnership ecosystem expansions (e.g., Autodesk) → support 2H26 reacceleration
    narrative; pair with relative valuation context (P/E vs L3Y vs peers)
  NOT material: routine peer acquisitions, minor partnership announcements, ESG reports,
  generic "AI eats consulting" think-pieces without a named pricing or headcount data point.
- CINT (CI&T): FLOW AI platform ~90% internal adoption, FY26 ~15% FXN growth guidance.
  FinSvcs ~38% of revenues. Read-across: same as GLOB above. Also: Brazil AI talent pool
  deepening (universities → GPU investment, 3rd largest AI adopter country) = supports
  CI&T nearshore value proposition.

**Software & AI:**
- TOTVS (TOTS3): Dominant Brazil ERP/SMB. LYNN AI model launched Feb-26. R$300mn AI
  capex. P/E ~19x vs 22.5x 3Y avg. Techfin JV with Itaú (R$2.49bn credit book, R$13.2bn
  origination 2025) targeting 30x larger TAM via new digital account / credit lines —
  but high BZ interest rates cap near-term contribution. Key risks:
  • SAP cloud/pricing shifts (seat→token model) DIRECTLY pressure TOTVS multiples —
    include even without direct revenue impact yet
  • Anthropic/OpenAI major new model launches → software sector selloffs (perception
    effect on multiples, even before confirmed competition). Anthropic Claude Enterprise
    moving from flat-fee to usage-based ($20 base + compute) frames the seat→token
    migration narrative across the industry
  • OpenAI Frontier / agent-orchestration platforms → directly compete with TOTVS
    Task-as-a-Service ambitions → negative read
  • Brazil AI-native startups targeting regulated verticals (HR, legal, tax, regulated
    sectors = core TOTVS TAM) — Brazil is 3rd largest AI adopter globally; AI lowers
    cost to build; founders increasingly targeting complexity = structural long-term
    competitive pressure → tag as "slightly negative" even if near-term impact uncertain
- LWSA (Locaweb/Wake): Wake AI shopping agents 2H26. Locaweb Cloud (50–70% cheaper than
  AWS/Azure, BRL billing). Revenue ~R$1.1bn. Read-across: Shopify, MELI, AI agent
  commerce launches, same AI-native startup risk as TOTVS.
- VTEX: E-commerce SaaS. FY26 Adj. EBIT margin low-20%s (vs 16% FY25 — major inflection).
  Most crowded LatAm software (UBS quant score +7.60 Mar-26). Read-across: Brazil
  e-commerce GMV data, Shopify/MELI peers (MELI earnings/GMV prints frame VTEX/LWSA
  marketplace narrative), AI checkout disruption, agentic-commerce (Visa agentic
  payments BR pilot, Anthropic agent-on-agent marketplace).

**Hardware:**
- INTB (Intelbras): Security cameras, networking, solar. Q1 print: Rev/EBITDA +5%/+14%
  vs St, EBITDA mg 14% (highest in ~2y on restructuring); cautious mgmt tone on growth
  + margin sustainability. Triggers: antidumping tariffs on Chinese fiber optic cables
  (direct benefit), security market demand, PPB/IPI consultations on radio base station
  manufacturing (positioning opportunity), Manaus land acquisition / R$200mn capex 18m.
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
- **Anthropic/OpenAI major model launch or pricing model change** → software sector
  sentiment risk; markets sell TOTVS/VTEX/LWSA/GLOB/CINT on AI disruption concerns even
  before product impact. Anthropic Claude Enterprise usage-based pricing (Apr-26) is a
  template event: shifts the industry conversation toward seat→token economics
- **OpenAI Frontier / enterprise agent platforms** → captures share of TOTVS
  Task-as-a-Service TAM → negative read for TOTVS even before adoption data
- **CFE government free internet (Mexico)** → competes with AMX Telcel in prepaid
  segment; fits the Mexico regulatory pressure narrative → include
- **PPB consultation for radio base stations** → manufacturing requirement changes affect
  INTB/POSI competitive positioning → include even if outcome uncertain
- **ACN $5bn M&A at pace** → signals IT services consolidation dynamic; raises question
  of GLOB/CINT as acquisition targets → include with that angle
- **V.tal ownership events** (creditor suits, regulatory moves, BTG stake-sale approvals)
  → TIM/TEF-BZ/AMX fiber infrastructure access story → always material while ownership
  is unresolved
- **STF ICMS surcharge rulings on additional states** (Sergipe ruling extends the
  RJ/Paraíba precedent; Alagoas and Mato Grosso cases remain pending) → each new
  favorable ruling strengthens precedent → positive for AMX/TEF-BZ/TIM
- **Crowding-score context** — when a covered name is at the top of the crowding
  distribution (e.g., TIGO most recent), incremental positive news has a higher hurdle
  to move the stock and negative surprises are asymmetrically painful. Frame takes
  accordingly: a crowded name needs a bigger surprise to remain a "positive read."

---

### Anatel Monthly Data (Brazil) — Standard Materiality

Anatel mobile/broadband data always triggers a full note for AMX/TEF-BZ/TIM. Frame
the headline around the 1–2 most investable data points (not a recap of all figures):
- AMX postpaid leadership / prepaid reversal → positive
- TIM prepaid widening losses / structural fixed-mobile gap → negative; flag if a
  monthly print shows a reversal (e.g., Mar-26 +85k prepaid net adds after consistent
  losses) — call out whether this looks sustainable or one-off
- TEF-BZ price increase timing impact / strong broadband → slightly positive/neutral
- Portability data: AMX running surplus; TIM deepening deficit → ongoing theme
- ISP broadband (Desktop flat = profitability pivot confirmed; Brisanet/Unifique pace)

---

### Active Running Stories
When a headline clearly connects to one of these monitored themes, note it:
1. "AI disruption on software" — SAP/Anthropic/OpenAI launches affecting TOTVS/VTEX/LWSA/GLOB/CINT multiples; Anthropic Claude Enterprise pricing shift to usage-based; OpenAI Frontier agent platform vs TOTVS Task-as-a-Service
2. "ISP consolidation Brazil" — AMX/Desktop R$2.4bn deal (Anatel approval pending), Ligga/Brasil TecPar, Anatel formalization, Unifique acquiring Amazônia 5G consortium control
3. "Brazil telecom regulatory" — Anatel monthly portability data, ICMS STF cases (Sergipe ruling done extending RJ/Paraíba precedent; Alagoas and Mato Grosso pending), 700 MHz spectrum auction (Anatel proposals Mon-4; TRF-3 liberated auction; Brisanet/Unifique pushing back on Telcomp liminar)
4. "Mexico regulatory" — AMX preponderance review 2027, Telefónica MX exit ($450mn sale), BAIT MVNO expansion, CFE internet programs, CRT mobile coverage / padrón biometric registration disconnects
5. "LatAm telco FCF yield" — ~4ppts LTM compression; AMX compressed least → supports AMX as top pick
6. "Satellite/D2D threat" — Starlink V2 D2D 2027, AST SpaceMobile, Amazon/Globalstar (~US$12bn) vs LatAm operators; satellite M&A targeting spectrum + local regulatory teams a key risk to monitor
7. "TIGO M&A pipeline" — Coltel done; Peru (TEF-Integratel) and Venezuela aspirations; US$3 dividend trigger; integration bandwidth a key investor concern
8. "AI disruption IT services" — AI startups moving upstream into consulting/strategy, headcount cuts at IT majors (Cognizant 4,000 announced; AT&T/Verizon combined ~17,700 in 2025), Uber CTO flagging AI tool cost overruns, demand signal for GLOB/CINT
9. "V.tal ownership" — creditor suits, Anatel/regulatory moves, RJ 7th Business Court rejecting UMB/SC Lowy/Pimco appeals on BTG fund sale (24-month IPO restriction only); implications for TIM/TEF-BZ/AMX fiber access and parent-level optionality
10. "Brazil B2B telco" — Vivo R$5.2bn B2B (+30% YoY, 15% cross-sell); TIM R$1bn (nascent); Singtel entering Brazil; 18.5% IT market growth vs 9.5% expected
11. "TIM Italy parent control" — EU Digital Networks Act + potential Poste Italiane control scenarios at parent → Brazil asset sale OR defended-and-expanded paths; V.tal sale resolution opens negotiation space

### Ticker Cross-Reference (editorial short forms used in the clipping)
TEF-BZ  = Vivo / Telefonica Brasil (VIVT3)  — ALWAYS use TEF-BZ, never VIVT3/VIVO
TIM     = TIM Brasil (TIMS3)                — ALWAYS use TIM, never TIMS3
AMX     = América Móvil (Claro/Telcel/Telmex/Claro Brasil)
TIGO    = Millicom
TEO     = Telecom Argentina / Personal
TV      = Grupo Televisa / TelevisaUnivision
LILA    = Liberty Latin America (coverage in initiation)
DESK    = Desktop Telecom (AMX acquisition target — Anatel approval pending; still tag
          alone for Desktop-specific corporate actions e.g., standalone dividend)
UNIFIQUE = Unifique (Brazil ISP, coverage in initiation)
GGPS3   = Rumo GPS (coverage in initiation)
ACN     = Accenture (peer)
COG     = Cognizant (peer)
INFY    = Infosys (peer)
TCS     = Tata Consultancy Services (peer)
EPAM    = EPAM Systems (peer — frequently surfaces in IT services flow: PT cuts,
          guidance, 52-wk lows; useful demand barometer for GLOB/CINT)
MELI    = MercadoLibre (peer — ecommerce read-across for VTEX/LWSA; GMV prints and
          earnings frame marketplace/checkout narrative)
AMZN    = Amazon (peer)
MSFT    = Microsoft (peer)
SAP     = SAP (peer — directly anchors TOTVS multiple debate; high theme frequency in
          curated flow; only escalate to full note when there is a concrete pricing,
          AI-feature, or guidance event)
TEF-MX  = Telefónica Mexico / Movistar MX (non-covered peer, relevant for AMX)
MX      = Mexico-country tag for Mexico-wide regulatory/sector items without a single
          operator focus (e.g., national connectivity plans, spectrum-flexibility moves)
V.tal   = V.tal (Brazil fiber infra — tag with own name, not a ticker)

In the **Sell-side** section of the clipping (broker rating/PT changes), brokers
typically use their own conventions — preserve those as written, e.g.:
  "TIMB: Tim SA downgraded to Neutral from Outperform at Bradesco BBI"
  "VIV: Telefonica Brasil downgraded to Neutral from Outperform at Bradesco BBI"
Editorial short forms (TIM, TEF-BZ) apply everywhere else.

### Multi-Ticker Format
When a single story directly affects 2–3 covered names, join tickers with "/":
  "AMX/TEF-BZ/TIM" — story hitting all Brazil telcos (e.g. spectrum auction, court ruling)
  "AMX/TEF-BZ/TIM/TIGO" — broader LatAm telco read-across (e.g. D2D satellite events)
  "GLOB/CINT"       — IT services read-across hitting both
  "VTEX/LWSA"       — ecommerce platform story hitting both
  "AMX/DESK"        — story affecting the acquisition or the combined entity
  "TOTVS/Sage"      — when both covered and peer are explicitly named with same angle
  "TOTVS/GLOB/CINT" — AI-pricing/agent-platform stories that simultaneously frame the
                     software-multiple and IT-services-demand narratives
Max 3 tickers in most cases (4 acceptable for LatAm-wide telco events). Only use when
BOTH/ALL names have a named investment angle in the headline. NOTE: joint-tag stories
(esp. GLOB/CINT, VTEX/LWSA) tend to be sector color and rarely warrant full notes —
default to "Other News" or the clipping headline unless there's a named, attributable
data point tying the headline to each ticker.

### Read-Across Tag Style
For peer headlines with a clear covered-stock investment angle, lead with covered ticker:
  "TOTVS: MSFT: Microsoft Pushes Usage-Based Pricing as AI Eats into Cloud Margins"
  means TOTVS is the investment angle; MSFT is the subject of the news.
  Use this style only when the read-across is explicit and direct."""
