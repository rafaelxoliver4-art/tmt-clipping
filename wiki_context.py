# wiki_context.py — UBS LatAm TMT analyst domain knowledge for Claude triage
# Source: Obsidian wiki vault (NEWS_WRITER_CONTEXT.md, latam-tmt-coverage-universe.md, — auto-updated 2026-05-11 — auto-updated 2026-05-14 — auto-updated 2026-05-19 — auto-updated 2026-05-21 — auto-updated 2026-05-22 — auto-updated 2026-05-25 — auto-updated 2026-05-28 — auto-updated 2026-06-02 — auto-updated 2026-06-08 — auto-updated 2026-06-16 — auto-updated 2026-06-19 — auto-updated 2026-06-23 — auto-updated 2026-07-01
#         editorial conversations Apr 2026)
# Embedded as a constant — no runtime file I/O required.

ANALYST_CONTEXT = """## UBS LatAm TMT — News Curator & Note Writer Analyst Context

**Owner:** Rafael Rodrigues (UBS LatAm TMT research, with Leonardo Olmos, CFA as lead analyst; support from Andre Salles and Gustavo Farias).
**Purpose:** Guide two tasks every cycle: (1) curate the daily TMT news clipping into sector buckets and tag covered tickers; (2) draft short analytical notes (📍 Headline + What happened + 🔎 UBS's take) for items that clear the materiality bar.

---

### 1. Coverage universe and correct ticker aliases

Use the alias on the LEFT in all curation and note titles. Do NOT use the local ticker symbol (VIVT3, TIMS3, TOTS3, VTEX3) inside the note headline — those are reserved for filings/disclosures.

| Alias used in clipping | Company | Sector bucket |
|---|---|---|
| AMX | América Móvil (Claro, Telcel, Telmex, Sites LatAm) | Telecom LatAm / Telecom Brazil |
| TEF-BZ | Telefônica Brasil (Vivo) | Telecom Brazil |
| TIM | TIM Brasil | Telecom Brazil |
| TIGO | Millicom International | Telecom LatAm |
| TEO | Telecom Argentina (Personal) | Telecom LatAm |
| TV | Grupo Televisa / TelevisaUnivision | Telecom LatAm / Streaming |
| TEF-MX | Telefónica México (now OXIO/Newfoundland transition) | Telecom LatAm |
| BRISANET / BRIT3 | Brisanet | Telecom Brazil (ISP) |
| DESK | Desktop (AMX acquisition target in BZ fiber) | Telecom Brazil (ISP) |
| TOTVS | TOTVS | Software and AI |
| LWSA | Locaweb / Wake | Ecommerce |
| VTEX | VTEX | Ecommerce |
| GLOB | Globant | IT Services |
| CINT | CI&T | IT Services |
| INTB | Intelbras | Hardware |
| POSI | Positivo Tecnologia | Hardware |
| MLAS | Multilaser | Hardware |
| LILA | Liberty Latin America (DCF pilot — partial coverage) | Telecom LatAm |
| GGPS3 | Ruoo GPS (initiation candidate) | Hardware / mobility |
| Unifique / FIQE3 | Unifique (regional ISP — initiation candidate; active UBS-style coverage model build in progress per D) | Telecom Brazil |

**US / global peers tagged for read-across (never lead the clipping, only support):** ACN (Accenture), COG (Cognizant), INFY (Infosys), TCS (Tata Consultancy), EPAM, IBM, Capgemini (CAP — observed in B as a recurring European IT-services peer in the GLOB/CINT cluster; tag `GLOB/CINT:` for read-across), Wipro/HCL, MSFT, AMZN, SAP, Oracle, ServiceNow, Sage, Salesforce (CRM), Shopify, MELI (MercadoLibre), OpenAI, Anthropic, Nvidia, Google Cloud.

**Standalone peer-ticker lines in the clipping (observed in E, 27–30 Apr clippings):** Peer tickers may lead their own line inside the relevant sector bucket when the headline is peer-only and the read-across is implicit (e.g., `AMZN:` under Software and AI, `MSFT:` and `COG:` under IT Services, `SAP:` and `OpenAI:` and `Anthropic:` under Software and AI). This is NOT promotion to a note — it is a clipping-level peer mention. The covered-ticker read-across is implied by the bucket; only escalate to `TOTVS: MSFT:` or `GLOB/CINT:` formatting when the read-across is the actual hook.

**Multi-ticker tag conventions (use these exact strings):**
- `AMX/TEF-BZ/TIM:` — anything affecting all three BZ mobile operators (Anatel, ICMS, portability, V.tal, spectrum auctions)
- `AMX/TEF-BZ/TIM/ISPs:` — same as above, but when the angle explicitly includes regional ISPs (Brisanet, Unifique, Desktop) — e.g., 700 MHz auction participation rules, court rulings on outorga transfers (Ligga → Amazônia 5G/Unifique), pole-access rules that name ISPs as third-party managers
- `AMX/TEF-BZ/TIM/TIGO:` — add TIGO for region-wide telco angles (D2D satellite, Brussels-style consolidation)
- `GLOB/CINT:` — any US IT Services peer or AI-disruption-of-services story
- `GLOB/CINT/Sector:` — when read-across is for the broader IT Services group
- `VTEX/LWSA:` — Brazilian e-commerce / digital commerce
- `INTB/POSI/MLAS:` — Brazilian hardware sector items affecting all three (smartphone import tariffs, BZ electronics tax changes, Foxconn/EV-on-Brazil press) — observed in F as a recurring grouping; promote to a name-specific note only when the angle names INTB, POSI, or MLAS directly
- `TOTVS:` for TOTVS-only; `TOTVS: SAP:`, `TOTVS: MSFT:`, `TOTVS/Sage:`, `TOTVS: Oracle:`, `TOTVS: Salesforce:` when the headline is a peer event with TOTVS read-across (covered ticker first, peer second; slash for full read-across pieces, colon for peer-mention items)
- `TOTVS/GLOB/CINT:` — observed in C (Anthropic Enterprise pricing piece) when a single peer event has opposite-direction reads across covered names. Use sparingly; the take must spell out the directional split (e.g., "Slightly positive for TOTVS, slightly negative for GLOB/CINT"). Per B, a more recent variant ("Microsoft and Uber reportedly hit by unexpected coding-agent cost surge in 2026") confirms this is the right tag for industry-wide agent-cost pieces where TOTVS gets the governance read and GLOB/CINT gets the input-cost read.
- `TOTS3:` (B3 ticker) used only when sourcing a Brazil filing or local press teaser. Note that during note-writing iteration C, Rafael repeatedly drafts headline shortlists with the `TOTS3:` prefix even when the published version uses `TOTVS:` — accept `TOTS3:` in draft headlines for B3-filings/teasers and switch to `TOTVS:` for the final published note.
- `DESK:` can lead its own line when it's a Desktop-specific event (dividends, capex, integration milestones with AMX). DESK has 5 published Observer notes per H — treat as a tradable standalone within Telecom Brazil.

---

### 2. Clipping format — sector buckets and ordering

Every clipping uses this fixed order; omit a bucket only if it has zero relevant items:

```
Telecom LatAm and World:
Telecom Brazil:
IT Services:
Software and AI:
Ecommerce:
Streaming:
Hardware:
Sell-side:
Next Results/Events:
```

**Rules:**
- Headlines in original language (PT/ES/EN). Do not translate.
- 3–15 items per bucket. If a bucket has 0 items, skip the section header entirely (do not write `[empty]` — the 28-Apr clipping that showed `[empty]` under IT Services is a known formatting bug to avoid).
- Lead with the covered ticker tag; use `Sector:` for peer/industry items inside a sector bucket.
- **Country-prefix lines (`MX:`, `CO:`, `BR:`)** function like `Sector:` for broad country-market items that have no single covered-operator hook (e.g., "MX: Neutralidad y competencia: la estrategia de Altán para potenciar el mercado mayorista y los OMV", "MX: Desconexión regulatoria de más de 100 millones de líneas móviles" — observed in E 27/30-Apr). They are acceptable in the clipping as country-level color. Re-map to the covered alias (`AMX:`, `TIGO:`, `TEO:`) the moment the item is operator-specific or quantifies per-operator impact, and never anchor a note on a bare country-prefix line.
- Each line: `[TICKER]: [Headline] — [Source]` (URL in the published version).
- Do NOT repeat in the clipping a headline that already appears as a full analytical note on the same day.
- **Sell-side section** is for broker rating/PT changes on covered names (e.g., "TIMB: Tim SA downgraded to Neutral from Outperform at Bradesco BBI"). When sourcing Brazil sell-side, the local B3 tickers (`TIMB:`, `VIV:`) may appear in this section only — the rest of the clipping continues to use the alias. Include UBS reports under "UBS Reports:" at the very top of the clipping when present.
- **Macro line** observed in E (8-Apr clipping): a `Macro:` block may sit just under `UBS Reports:` and above `Telecom LatAm and World:` when there are 1–3 macro items with direct LatAm TMT transmission (e.g., "MX: Comisiones del Senado aprueban reforma a LFT sobre jornada laboral", "US: Higher Tax Refunds Positive for Consumer Spending"). Keep to ≤3 lines and only include items with a covered-name transmission channel.
- **Next Results/Events** lists earnings, investor days, AGMs, regulatory auctions in the next ~30 days. Use precise timing markers observed in E: `[Company] reports TODAY`, `[Company] to report on [Date] (before market open / post-market)`, `[Event] [Date]`. Group by date implicitly; do not bullet sub-headers. Recurring events to keep on the radar (per E): Televisa, TelevisaUnivision, Walmex (BAIT), Cognizant, Grid Dynamics, Shopify, EPAM, TEF-MC, AMX Investor Day.
- **Earnings-preview-style aggregator lines** (e.g., "Earnings Preview: CI&T Inc. to Report Financial Results Post-market on May 11", "MELI MercadoLibre Earnings Preview May 6, 2026") observed in B/F appear regularly from TipRanks/AOL/Moomoo aggregators. These belong in Next Results/Events as a date entry, NOT as a curated ticker line in the sector bucket — drop the aggregator framing and keep only the date+ticker.

---

### 3. Materiality bar — full note vs. Other News vs. omit

**Promote to a full analytical note (📍 + What happened + UBS's take) only when ALL of:**
1. The story has a directional read on a covered name's revenue, margin, capex, capital allocation, regulation, competitive position, or valuation multiple — i.e., it changes the marginal investment view.
2. The fact is sourced from a primary/credible outlet (Bloomberg, Reuters, FT, WSJ, Valor, DPL News, TELETIME, TeleSíntese, El Economista, RCR Wireless, Bloomberg Línea, El Economista, Estadão, official filings, Anatel/CRT/ANE/Enacom publications, conference call transcripts, UBS sell-side reports). Avoid making a full note off TipRanks, GuruFocus, AOL.com, Moomoo, marketscreener.com aggregators — these can feed the clipping but are not strong enough to anchor a take.
3. There is enough material for a 1–4 bullet "What happened" plus a 3–6 sentence take that says something analytical and not just a restatement.

**Send to "Other News" / single-bullet item when:**
- The fact is material but is one of several minor items the same day (V.tal court rulings, spectrum auction procedural updates, MVNO licensing on Altán, regional ISP M&A under R$200m, individual TEF-BZ/TIM marketing launches).
- A peer event (SAP, Sage, ServiceNow, Anthropic) deserves mention but the read-across is thin.

**Omit entirely:**
- Pure stock-price tickers, generic "stock up/down" headlines, paid-syndication content with no original reporting, repetitive Mercado Libre "X analyst raises PT" notes (track once a quarter as a calibration point only).
- Generic AI/macro pieces with no LatAm TMT covered-name angle.
- Globant securities class-action / investigation press releases (e.g., "Securities Fraud Investigation Into Globant S.A. (GLOB) Announced") — appear repeatedly in B/E. Surface ONCE in the clipping per litigation cycle as a Sector: line; do NOT promote to a note unless a court ruling, settlement, or material disclosure event occurs.

**Specifically material story types — these should ALWAYS reach the clipping (sector tag at minimum, multi-ticker tag when the angle is named):**

*Brazil telecom regulatory + fiscal (AMX/TEF-BZ/TIM):*
- **FISTEL** changes / disputes — the regulatory fee is THE recurring cost-line for BR mobile operators. Any MCom/Anatel/Congress fight over FISTEL allocation is material (tag AMX/TEF-BZ/TIM). PRIORITY WATCH: the STF virtual session scheduled for May 15–22, 2026 on the FISTEL ADI, plus the parallel TRF-1 case from 2003 — TEF-BZ CEO Christian Gebara discussed both on the 1Q26 call and called the STF thesis "very strong and solid". A favorable STF ruling triggers a Positive read for AMX/TEF-BZ/TIM; unfavorable ruling is Negative — write the note same-day.
- **Reforma tributária** clauses affecting telecom (incremento de arrecadação, ICMS, ISS, special regimes) — frame as cost/margin transmission. Per G call commentary, TIM CEO Alberto Griselli's framing that "tax reform could initially increase tax collection from the telecom sector, although the long-term effect should likely be neutral, with compensation coming later through tax credits" is the canonical take template; use Griselli's wording when the trigger is reforma tributária.
- **Rede neutra regulation** (Telebrasil position, Anatel proceedings, V.tal/Open Fiber/Newco governance) — affects all 3 BR telcos' wholesale economics.
- **Anatel commentary on consolidation / spectrum / portability** — when an Anatel official speaks, it's a tradable signal.

*LatAm regulator-driven country signals:*
- **Mexico spectrum plans** (IFT/SCT, Programa Nacional de Espectro, 2026-2030 plan, prepondancia review, AT&T MX status, CRT 5G industrial auction consultation opening May-26, CRT public consultation on a dynamic spectrum auction platform) — AMX-direct.
- **Colombia CRC** rankings, spectrum auctions, MVNO licensing, Coltel privatization — AMX/TIGO.
- **Argentina ENACOM** rule changes, internet/data growth data — TEO read-across.
- **Chile / Peru / Venezuela** spectrum or consolidation events — TIGO/AMX context.
- **Mexico CRT Padrón de Telefonía / line registry** — observed in E (27–28 Apr) as a recurring AMX-tagged item; over 100mn lines pending registration with Telcel and AT&T MX leading disconnections. Material to AMX subscriber base; tag `AMX:` (not `MX:`) when the disconnection figures are quantified per operator. Altán biometric simplification press also belongs under `AMX:` when it touches the same registry mechanic.

*IT services pricing/economics (GLOB/CINT):*
- **AI token / consumption pricing frameworks** at IT-services peers (Cognizant tokenised pricing, TCS "pay-to-play AI token landscape", Accenture managed AI) — these reframe how the entire industry charges → direct margin read for GLOB/CINT.
- Any Indian-IT peer (TCS/Infosys/Wipro/HCL) commentary on AI delivery economics.
- **Coding-agent cost-surge stories at hyperscalers / mega-enterprises** (Microsoft, Uber, Anthropic-customer disclosures of unexpected token bills) — these are the trigger for the `TOTVS/GLOB/CINT:` split-direction note (per B). Frame as TOTVS slightly positive (governance edge), GLOB/CINT slightly negative (rising input cost on AI-augmented delivery).

Reject only if the story has ZERO named transmission. The above categories
all have explicit transmission to covered names — don't drop them as "sector
color" or "regulatory noise".

**Curator self-discipline based on F (corpus analysis) and H (Observer published-notes):**
- `GLOB/CINT` was curated 320× and never promoted to a full note as the multi-ticker tag. The promotion happens via the `GLOB`-only (40 published notes per H) or `CINT`-only (33 published notes) tag. Curator should keep tagging peer/sector items as `GLOB/CINT` (Other News candidates) and only promote when a peer event (TCS, ACN, INFY, COG, EPAM, IBM, Capgemini, Cognizant) is large enough to drag the sub-sector or when it speaks directly to AI disruption of services delivery.
- `AMX/TEF-BZ/TIM` was curated 124× as a multi-ticker without promotion — that pattern is correct for regulatory/V.tal/auction items that are color, not theses. EXCEPTION: monthly Anatel data, ICMS/FISTEL rulings, and 700 MHz auction milestones are the recurring multi-ticker triggers that DO warrant a full note (see §4).
- `VTEX/LWSA` and `MELI` are curated repeatedly but rarely noted — keep them in Ecommerce bucket and only promote on (i) earnings, (ii) Amazon/Mercado Libre capex or pricing actions with read-across, (iii) cross-border tariff changes. H confirms LWSA (9 notes) and VTEX (9 notes) are real but earnings-clustered. Recent LWSA promotion examples in B (Locaweb AI ecosystem for SMBs / Wake AI agent stack) confirm a name-specific AI product launch is a valid promotion trigger.
- `ANTHROPIC`, `EPAM`, `COG`, `MX`, `BR`, `CO`, `Regulatory`, `AI` are appearing as themes — these should never be ticker tags. Re-map to the appropriate covered ticker tag (TOTVS for Anthropic enterprise pricing, GLOB/CINT for EPAM/COG, AMX/TEF-BZ/TIM for MX/BR regulatory, TIGO/AMX for CO regulatory, TOTVS or GLOB/CINT for AI depending on angle). (Exception: `MX:`/`CO:`/`BR:` country prefixes are allowed as country-level clipping lines per §2, but never as note tags.)
- `INTB/POSI/MLAS` and `TEO` appear repeatedly in F without promotion — for INTB/POSI/MLAS this is correct (sector item unless name-specific capex/dividend/tariff hits a single ticker; H shows only 2 published INTB notes). For TEO, the antitrust-review window (30-day pronouncement) and any conditional remedies should escalate to a full note when concrete — H shows TEO has 7 published notes, so the bar is real but the trigger must be specific.
- **H tier-1 names — never let these get curated as "Sector:" or as a theme.** AMX (57 notes), GLOB (40), CINT (33), TOTVS (29), TIM (29), TEF-BZ (25), TIGO (16). Any headline that touches one of these names directly must be tagged with the covered alias, not buried under `Sector:`. If a story is genuinely sector-level and only indirectly touches a tier-1 name, the `Sector:` line still belongs in the relevant sector bucket and should NOT be substituted for the covered tag.
- **Aggregator pattern: TipRanks (48), AD HOC NEWS (47), Investing.com (46), TELETIME News (45 — note this duplicates with Teletime 50, dedupe), marketscreener.com (41), Moomoo (35), Globant Newsroom (35).** Per F, these are the top-volume sources but generate clipping-level noise. Treat aggregator-only items as auto-greylist: include in clipping if no primary source is available, but never anchor a note. Globant Newsroom is acceptable for GLOB filings/press but is corporate PR — independent confirmation required before promotion.

---

### 4. Active running stories — keep watching these every cycle

Each story below has a covered-ticker read; surface ANY headline that advances it.

**Telecom LatAm:**
- **AMX Investor Day (27-May-26) — flattish-capex / FCF-expansion thesis** — Per G (TMT Online Observer Data, 27-May), management laid out a three-year outlook: ~US$7bn annual capex through 2028E (flattish, major 5G/fiber investment cycles largely behind), 4–5% service revenue and 4.5–6% EBITDA growth at constant FX, and clearer capital-allocation priorities (footprint M&A, deleveraging, shareholder returns). Targets imply a 12.2% 2028E FCF yield vs. UBSe 11%; BZ/COL margin aspirations imply ~3.5% higher EBITDA vs. UBSe. UBS take: Positive read for AMX. This FCF-expansion-from-flattish-capex narrative is now the core AMX thesis to track — surface post-Investor-Day follow-through (capex confirmation, footprint M&A like Desktop/TEF-Chile, buyback/dividend actions) as `AMX:` items.
- **Millicom (TIGO) consolidation push** — Coltel Phase 2 government stake auction (overdue vs. management's "around April" guidance; watch Superfinanciera/MinHacienda; track the published timeline — Decreto 1481 (Dec-30-25), Phase 1 aviso Jan-16, Phase 2 precalification Mar-9 → Mar-31 close, Phase 1 adjudication Mar-26 (3,000 shares at COP 772.38), Phase 1 settlement Apr-8, $75M 2032 notes tap Apr-2/closing Apr-14, USD 214.4M Feb-6 OPA closing for 67.5% from Telefónica, ~USD 220M targeted for La Nación stake). CEO Marcelo Benítez signalled Peru and Venezuela as next adjacencies but priorities are turnarounds in Uruguay/Ecuador/Chile/Colombia (post-M&A EBITDA margins already >40% in Uruguay and Ecuador). Two-to-three-player endgame thesis for LatAm; Chile fragmentation with four operators flagged by Benítez as unsustainable. Per E (26-Apr), watch the "Millicom consolida control de Movistar Colombia tras compra de acciones del Estado" headline cluster — when Phase 2 actually clears, write the note same day. **UPDATE (per B run log "Millicom assumes control of Coltel as Colombia exits stake" + G Crowding doc noting Colombia's antitrust regulator approved the Coltel acquisition): Phase 2 / state-stake consolidation has now effectively cleared — the same-day note trigger is spent for the auction milestone itself. The watch now pivots to (i) integration execution across Uruguay/Ecuador/Chile/Colombia, which G ties to TIGO's sharp crowding-score decline (profit-taking + integration-execution risk), and (ii) the next adjacency moves (Peru/Venezuela). Promote on concrete integration milestones, margin prints, or a new-market deal — not on residual consolidation chatter.** Also surface portability-fine items on Movistar Colombia (e.g., "Movistar Colombia recibe multa por fallas en portabilidad numérica") as `TIGO:` Other News.
- **Movistar México sale (TEF-MX → OXIO/Newfoundland for ~US$450m)** — OXIO timeline, MVNO platform implications, competitive pressure on AMX/Telcel via either branded MVNO route (heavier execution risk, higher AMX downside) or Altán wholesale route (more contained — 187+ MVNOs already on Altán). Note also OXIO's "Telecom-as-a-Service" framing in PR — flag as a category-defining narrative, not as standalone jargon to repeat in notes without definition. Background context to surface: Movistar México revenue grew 7.1% H1-24 vs. H1-23, back to its best 2017 level — fits the "underinvested asset with optionality" angle that justifies the OXIO bid. Per E (29-Apr), the "Telefónica supera 1.3 millones de conexiones IoT en medio de su transición hacia Oxio" headline is a transition-progress data point worth keeping as `TEF-MX:` Other News.
- **TEO/Telefónica Argentina antitrust review** — 30-day pronouncement window (track Enacom/Competencia statements); conditional remedies possible; affects post-deal MSR and 5G capex. Promote to a full note when the regulator pronounces or when concrete remedies leak. H shows 7 published TEO notes — the recurring triggers are FY/quarter results, fast takes on subscriber/ARPU/margin signals, and antitrust milestones. The 30-Apr headline "30 días para el pronunciamiento de la autoridad de Competencia de Argentina sobre Telecom-Telefónica" is exactly the kind of item that should escalate to a full note when the pronouncement actually drops.
- **Spectrum / regulator agendas** — MX CRT 5G industrial auction consultation (May-26 opening flagged in E) and the CRT's public consultation on a dynamic spectrum auction platform (recent `AMX:` note in B); Colombia ANE 2026–2030 plan, BZ 700 MHz auction (TRF-3 / Telcomp liminar reversal, regional ISP exclusion, leilão dates — per E 30-Apr, "Anatel confirma abertura das propostas do 700 MHz para dia 4" is the imminent trigger; promote to full note on auction day).
- **LatAm telco dividend / FCF-yield relative-value theme (standing view)** — per D (06-29 session drafting a cross-sector dividend-yield relative-value piece, grounded against Selic, peer-sector yields, and telecom payout sustainability), UBS runs a standing yield-compression thesis on LatAm telcos: sector FCF yield down ~4ppt LTM and >6ppt over 3Y, with AMX having compressed the least → AMX is the top pick on relative FCF-yield; Vivo (TEF-BZ) framed as the defensive high-dividend name; TIM guiding ~8% dividend yield and ~+35% YoY shareholder remuneration for 2026 (highest payout growth). Surface any headline touching telco payout/dividend policy, Selic moves that reprice the relative yield gap, or cross-sector (utilities/banks) dividend-yield comparisons as a read on this theme. Tag by the named operator (`AMX:` / `TEF-BZ:` / `TIM:`); use `AMX/TEF-BZ/TIM:` for a sector-wide payout/yield readout. Promote to a note when a covered telco updates payout policy or when the relative-yield case shifts materially.
- **TelevisaUnivision capital structure** — tender offer for 8.000% Senior Secured Notes due 2028 (E, 8-Apr). TV has 8 Observer notes per H; treat capital-structure events (refis, tender offers, debt covenants) as promotion triggers, not just earnings. Also watch Televisa M&A interest in Mexico telecom (per B "Televisa eyes M&A in Mexico telecom") — F shows TV curated 104× with a very low promotion rate, so reserve full notes for concrete capital-structure or M&A events, not market chatter.

**Telecom Brazil:**
- **V.tal stake sale to BTG Pactual funds** — RJ 7th Business Court approvals, creditor appeals (UMB Bank, SC Lowy, Pimco); 24-month IPO restriction does not block asset sales/mergers/spin-offs. Watch TIM Brasil parent (Poste Italiane) angle on whether a new controller divests BZ or doubles down via inorganic fiber. Wording note: use "appeals" (not "embargos") in English-language notes; preserve the Portuguese "embargos" only when quoting source verbatim.
- **AMX–Desktop integration in BZ fiber.** DESK is a tradable standalone (5 Observer notes per H) — surface dividend declarations, capex, regulatory milestones as DESK-tagged items. E (29-Apr "DESK: R$5mn dividend announced") confirms the dividend-declaration pattern as a stand-alone `DESK:` line within Telecom Brazil.
- **Brisanet (BRISANET/BRIT3) as a tradable regional-ISP standalone** — F shows BRISANET curated 32× with no codified promotion rule, and the Observer archive includes a dedicated Brisanet Q4-results note (mobile growth + capex-intensity angle). Treat Brisanet as a name-specific promotion candidate on (i) quarterly results (mobile subscriber adds, 5G expansion, ARPU, capex intensity / capex-to-sales trajectory), (ii) corporate/strategic shifts (e.g., "Brisanet encerra Brisaplay e migra clientes ao SKY+" — content/partnership pivots), and (iii) M&A or 700 MHz / outorga participation. Otherwise keep as `BRISANET:` Other News, or roll into the `AMX/TEF-BZ/TIM/ISPs:` tag when the angle is regulatory and names ISPs as a group. Brisanet is also a called-out "smaller player" line in the monthly Anatel net-adds note (see below).
- **ICMS surcharge STF cases** — RJ and PB already ruled; Sergipe added; Alagoas and Mato Grosso pending. Each new ruling strengthens precedent → positive read for AMX/TEF-BZ/TIM. Take template observed in C: "Positive read for AMX/TEF-BZ/TIM. The ruling follows the STF's earlier decisions against similar surcharges in [States]. We note that ICMS surcharge cases in [pending States] remain ongoing at the STF, and we believe this decision strengthens the precedent for their removal as well."
- **FISTEL STF virtual session (May 15–22, 2026)** — TEF-BZ CEO flagged on 1Q26 call; parallel TRF-1 case from 2003 also in appeals. Favorable ruling = Positive AMX/TEF-BZ/TIM; unfavorable = Negative. Write same-day; cross-reference Gebara's "very strong and solid thesis" framing.
- **NuCel (Nubank MVNO on Claro's network)** — 4× QoQ active subs in 4Q25 (~232k est.). Positive AMX driver, drags TIM prepaid more than TEF-BZ. TIM CEO on Q4 call: "Nucel is not material at this stage"; back-book price increases communicated Dec-25 expected to drive Q1 churn. AMX CEO clarified Claro is ALSO attracting higher-ARPU subs independently of NuCel — frame NuCel as a tailwind, not the whole story. Cross-reference: "Assessing Nucel's risk: uneven exposure across Brazilian carriers".
- **Brazil MVNO landscape (NuCel, SKY Móvel, Vero, Correios, iFood, Motu; Surf Telecom as enabler)** — per D (06-25 Brazil-MVNO factual report + 06-29 corpus), Rafael maintains a Brazil-MVNO map worth tracking as a competitive-intensity theme: NuCel (Nubank on Claro, ~232k YE25) is the standout, SKY Móvel runs via Surf Telecom, with Correios, iFood, Motu and Vero (convergence) among branded MVNOs; Surf Telecom is the recurring enabler/host. Anatel's Sept-2025 MVNO disclosure cut — a contested Claro confidentiality dispute — was restored Jun-2026, so per-network MVNO share data is visible again. Read-across: MVNOs hosted on Claro's network are an AMX wholesale tailwind (NuCel drives this most), while rising overall MVNO share is a competitive-intensity read for all three BR mobile operators (heavier on prepaid-exposed TIM). Data caveats to carry into any note: Uber's ~140mn is cumulative reach (not active subs) and the Nio figure has conflicting sources. Keep as `AMX/TEF-BZ/TIM:` Other News / sector color; promote when an MVNO discloses subs/GMV, an enabler deal names a covered network, or Anatel data reveals a material share shift.
- **AMX-Claro April pure-postpaid price increase (+14%)** — per G (Crowding Score Data), AMX raised pure-postpaid prices ~14% in April, which surprised investors given AMX's prior commentary and helped ease competitive-pricing fears for the sector (a key driver of TEF-BZ's crowding-score improvement). Frame as a rational-pricing / ARPU-supportive signal for the BZ mobile complex (constructive for AMX/TEF-BZ/TIM pricing discipline); watch for TEF-BZ and TIM front-book follow-through and any churn read in subsequent Anatel data.
- **Telco-fintech expansion (TEF-BZ Vivo Pay, TIM-PicPay)** — Vivo Pay use of crediário to grow the financial-services book; TIM/PicPay credit partnership. Track as part of the TEF-BZ "telecom-vira-fintech" thesis (top curated example in B). Promote when (i) management discloses GMV/loan book, (ii) bundling drives ARPU or churn data, (iii) a fintech-only competitor reacts.
- **Monthly Anatel data (portability + net adds + broadband)** — full note every cycle: title `📍 AMX/TEF-BZ/TIM: [Operator readout]; Anatel [Mon-YY] data`. Lead with hook line ≤160 chars; "What happened" = 2 bullets (total trend + bilateral flows); "UBS's take" = one paragraph per operator (AMX/TEF-BZ/TIM in that order). For TIM, paragraph must stay ≤3 sentences (rewrite feedback from C: "make tims part more concise"). Calibration baseline (Mar-26 per G/Anatel Reports doc): Human Mobile total +850k (vs. +530k Feb-26); AMX-Claro +492k total, TIM +171k, TEF-BZ +70k. Human Postpaid +854k total: AMX +391k, TEF-BZ +280k, TIM +85k. Prepaid −4k total: AMX +101k, TIM +85k (rebound), TEF-BZ −210k. Portability: AMX +98k, TEF-BZ +4k, TIM −145k. Smaller players: Brisanet +40k, Unifique +15k. Recent trajectory: AMX holding ~+90–100k portability since Oct-25; TIM stuck in net loss; TEF-BZ oscillating around zero. Take vocabulary observed in C: "despite reversing the negative trend seen in last month, the net portability net adds are still immaterial given TEF-BZ size"; "human postpaid has remained soft this year". Use the Anatel Reports doc (G) as the canonical structure — postpaid/prepaid/broadband three-segment format with Brisanet and Unifique called out among smaller players. Per G, the published Mar-26 title was "AMX keeps the lead in Mobile, TEF-BZ stable trends, TIM prepaid rebound" — mirror this "lead / stable / rebound or pressure" one-word-per-operator title cadence. Latest reading (G/Anatel Reports doc, Apr-26): AMX-Claro portability +84k (slight decel vs. +98k Mar-26), TEF-BZ +9k (stable), TIM −138k (still soft, marginally narrower); published title "AMX slight decel, TEF-BZ stable, TIM still soft; Anatel Apr-26 portability data" — confirms AMX's slowdown from the ~90–100k pace (level still well above early-2025) and TIM's persistent net loss.
- **Pole-access / FIIS bill** — Aneel cap (Executive sets maximum price only until Aneel defines permanent regulated price — amendment narrowed scope from 5 years), Anatel parameters, third-party infrastructure manager role, prohibition on discriminatory treatment and cross-subsidies between telecom and energy. Approval was terminative → bill proceeds to House of Representatives. AMX/TEF-BZ/TIM/ISPs tag. Per B (recent note "AGU e Anatel encerram impasse jurídico do compartilhamento de postes" / "AGU clears pole-sharing legal impasse; Anatel awaits Aneel to resume rulemaking"), AGU/Anatel jurisdictional rulings on pole-sharing belong on the same watch line — promote when AGU/Anatel issue joint instruments.
- **D2D satellite** — Amazon-Globalstar (~US$12bn), Sky Móvel + Amazon Leo. UBS US Telecom analyst John Hodulik view: limited near-term risk to terrestrial carriers from satellite but rising space-economy investment warrants monitoring. M&A targeting companies with spectrum/infrastructure (and local regulatory teams) is the monitoring item, not satellite capacity itself. Per E (29-Apr) "Sky acelera triple play com Sky Móvel e internet satelital via Amazon Leo" is the canonical AMX/TEF-BZ/TIM tag for satellite-via-Amazon-Leo items.
- **Brazil data centers / sovereign cloud / Redata tax regime** — recurring `BR:` country-level theme in B/F (e.g., "expansão dos Data Centers brasileiros", "Investimento de R$50 milhões... data centers — Ministério das Comunicações"). Covered-name transmission is evidenced in E (27-Apr "AMX/TEF-BZ/TIM: Oracle vê telcos como base da nuvem soberana no Brasil") — telcos positioned as the infrastructure/sovereign-cloud base, and the Redata special tax regime (approved 4Q25, surfaced in the ESG recap) shapes data-center build economics. Tag `AMX/TEF-BZ/TIM:` when telcos are named as the data-center/sovereign-cloud base; tag `BR:` (country-level color, per §2) when the item is broad market/policy with no single-operator hook. Generally Other News / sector color — promote only when a covered telco discloses a concrete data-center capex/partnership or a Redata change quantifies a covered-name impact.
- **TIM as #1 single-name fast-take pattern (H: 29 notes, joint-second behind AMX/GLOB).** Per G/Conference Call Transcripts and the TIM 4Q25 "margem recorde" fast take, TIM is a recurring single-ticker promotion via (i) quarterly margin/EBITDA-aL prints, (ii) FY guidance updates (35% YoY shareholder payments, ~8% dividend yield, ~5% MSR growth, 6–8% EBITDA), (iii) capex/leasing trajectory commentary. The `TIM:` (not `AMX/TEF-BZ/TIM:`) tag is correct when the news is operator-specific (margin record, network rollout, partnership). Do not bury these under the multi-ticker tag.

**IT Services (GLOB/CINT):**
- **AI disruption of services delivery** — outcome/fixed-price pricing vs. T&M, productivity gain-sharing in RFPs, talent retention risk if enterprises can't embed AI as fast as employees do personally. CI&T managed-squad model (sharing productivity, charging higher avg ticket — fixed-throughput teams instead of hours per FTE) vs. Globant's more conservative walk-away stance on unclear-scope fixed-price deals.
- **US peer reads** — TCS quarterly (AI revenue acceleration, FY27 confidence, 26% long-term margin target, Q1 wage-hike 150–200bps drag); ACN Microsoft Copilot rollout to ~743k employees; COG guidance (revenue below estimates, 4,000 job cuts); INFY/EPAM/IBM/Capgemini. UBS's reaction view: AI revenue acceleration in TCS hasn't moved GLOB/CINT in recent quarters → flag as neutral unless the read is specifically pricing-model or demand-environment color. Per G (Duke CFO survey / UBS Evidence Lab), CFO-survey "little-to-no AI impact so far" and "59% cite unclear ROI" data points anchor a Negative read for GLOB/CINT — use when survey/adoption-ROI evidence is the trigger.
- **Globant Q1 2026 — "100 Squared" strategy + capital return** — Q1 print beat with deeper AI-transformation engagements, first positive Q1 FCF since 2019 (~$36.1mn, >55% conversion), new $125mn buyback authorization bringing aggregate repurchase capacity close to ~15% of market cap. Frame as supportive of the 2H26 reacceleration narrative. Modeling note from G: 2026 revenue/EBIT-margin estimates aligned with mid-point guidance (unchanged); EPS revised +2% on higher buybacks; lower headcount growth offset by higher revenue/headcount as AI-delivery scales.
- **Globant Autodesk partnership / ecosystem expansion** — 2H26 reacceleration narrative. GLOB currently trades at ~12m fwd P/E discount vs. L3Y and vs. peers — note valuation framing.
- **Globant securities class action / investor lawsuits** — track but don't over-amplify; flag as monitoring item. Recurring headline phrasing: "Globant Investors File Securities Suit Citing Alleged Misstatements About Latin American Expansion" and "Securities Fraud Investigation Into Globant S.A. (GLOB) Announced". Per E and B, surface once per litigation cycle as a Sector: line; do NOT make this the lead `GLOB:` item.

**Software and AI (TOTVS):**
- **SaaS-incumbent multiple compression on AI-disruption fears** — a SaaS peer's stock move or forecast disappointment (Salesforce/CRM, Workday, SAP) is a multiple-compression read-through to TOTVS and the BZ software complex, NOT an earnings-line read. Recent note in B: "📍 TOTVS: Salesforce forecast disappoints on AI-disruption fears — read-through to ERP/SaaS multiples." Tag `TOTVS: Salesforce:` (peer-mention) and write the take around valuation/sentiment, consistent with the "multiple-compression risk, not earnings-line risk" framing already used for the Brazil-AI-adopter piece.
- **Oracle earnings / capex guide (peer read-across)** — per G (TMT Online Observer Data, 11-Jun, UBS analyst Karl Keirstead), Oracle's −10% after-market reaction was driven by an FY27 capex guide of $90–95bn (above ~$85bn buy-side consensus) despite in-line/better 4Q/May numbers, above-consensus 1Q/Aug cloud guidance, and a reaffirmed FY27 revs/EPS guide; UBS remains Buy-rated. Tag `TOTVS: Oracle:` as peer read-across only — relevant as cloud-infra/SaaS-capex sentiment color and a calibration point for how the market is pricing AI capex, not a TOTVS earnings-line read.
- **Anthropic enterprise pricing shift (flat → usage-based, $20/seat base + compute)** — Slightly positive for TOTVS (system-of-record incumbents can govern token costs via conversation limits / token caps / smaller task-specific models, with native workflow understanding for cost analytics); slightly negative for GLOB/CINT (rising tool cost as input). Industry context: OpenAI moved Codex to token metering early April, GitHub tightened Copilot limits Apr-10, Windsurf replaced credits with daily/weekly quotas in March — the flat-fee era for agentic AI workloads is ending across the industry. Anchor sources: The Information (original), Gizmodo (independent confirmation with spokesperson quote), PYMNTS (procurement angle). WSJ quoted Retool's David Hsu on Anthropic API uptime of 98.95% (90 days ending Apr-8) — flag as separate reliability angle if it comes up.
- **Agentic AI cost-governance angle** — Deloitte flagged customer support as highest-impact agentic AI use case; off-purpose / complex queries can consume 25%+ of inference spend even at 5–8% of traffic share; per-query token cost ~10× for complex vs. simple. Slightly positive for TOTVS via system-of-record cost-governance edge.
- **Microsoft Copilot / Microsoft usage-based pricing for AI / agent rollouts** — same direction as Anthropic shift. Tag `TOTVS: MSFT:` when Microsoft's pricing or agent commentary is the trigger; treat as Slightly positive for TOTVS (governance/cost control via ERP) absent a name-specific Microsoft-vs-TOTVS competitive event. Per E (30-Apr) "Microsoft Pushes Usage-Based Pricing as AI Eats into Cloud Margins" is the canonical `TOTVS: MSFT:` framing.
- **Sage, Oracle NetSuite, ServiceNow, Salesforce, Microsoft Copilot agent rollouts** — peer read-across only. Per E (30-Apr) "Sage expands AI agents across finance, HR and operations to automate workflows" and "Oracle NetSuite announces AI coding skills for SuiteCloud developers" appeared back-to-back; the `TOTVS/Sage:` and `TOTVS: Oracle:` tags belong on these as peer-read-across in Software and AI.
- **Brazil as 3rd-largest AI adopter / GPU buyer pattern (universities-first)** — slightly negative for TOTVS via low-entry barriers for AI-native ERP-adjacent challengers. Per Nvidia's Wei Xiao: universities lead GPU investment in Brazil (unusual vs. other markets where enterprises lead), funding talent pipeline → applied research → enterprise follow-on. Frame as multiple-compression risk, not earnings-line risk.

**Ecommerce (VTEX/LWSA):**
- **Amazon cross-border fuel/logistics surcharge** — 3.5% temporary surcharge on third-party sellers using fulfillment in US/Canada, effective Apr-17, including remote fulfillment to Canada/Mexico/Brazil. Read-across: LWSA via marketplace economics, VTEX via D2C migration (if marketplaces raise rates, GMV may migrate to D2C platforms → VTEX positive); LWSA tends to benefit from marketplace commerce → net neutral framing for LWSA, slightly positive for VTEX. Follows UPS/FedEx fuel surcharges and USPS 8% temporary increase (Apr-26).
- **MELI as benchmark** — capex, GMV, financial-services expansion, autos vertical. Curate as Ecommerce sector context, promote to note only on earnings.
- **Cross-border tariff (taxa das blusinhas) and EU duty-free expansion** — 5,000+ Brazilian products with EU zero tariff from May; "taxa das blusinhas" revocation discussion in BZ government.
- **Agentic AI / Visa agentic payments pilots / AI-driven traffic to e-commerce** — AI traffic to US e-commerce up 393% with above-traditional conversion; Visa BZ agentic-payments pilot. Frame as TAM expansion catalyst for VTEX/LWSA platforms. Per E (30-Apr) "Buscas via IA cortam mais de 95% do tráfego para sites" is the bearish counter-read — when both directions are surfaced same week, frame as Mixed read for VTEX/LWSA.
- **LWSA AI ecosystem / Wake AI agent stack** — recent promotion in B ("LWSA: Locaweb launches AI ecosystem for SMBs, deepening the Wake AI agent stack"). Name-specific AI product launches by LWSA are valid promotion triggers — write as `LWSA:` single-ticker note, slightly positive read on platform stickiness.

**Streaming / Media (TV):**
- TelevisaUnivision capital structure (tender offer 8.000% 2028 notes).
- Netflix / WBD bid dynamics.
- Televisa M&A interest in Mexico telecom (per B); promote only on a concrete deal/structure event, not market speculation.

**Hardware (INTB, POSI, MLAS):**
- INTB capex announcements (e.g., Manaus land + R$200m / 18 months), dividends, Brazil import-tariff exposure on smartphones.
- Brazil smartphone/electronics import-tariff debates can be tagged `INTB/POSI/MLAS:` when the angle hits all three; surface as Hardware sector items unless one name is explicitly affected. Per F, MELI is "not material" framing applies analogously here — only one Hardware bucket entry per cycle unless multiple names are concretely affected. Zona Franca de Manaus / Suframa items and foreign-OEM expansion press (Oppo, Realme, Foxconn) recur in F as Hardware-sector color — tag `Sector:` (or `INTB/POSI/MLAS:` when the policy hits all three), and only escalate to `INTB:` when the Manaus/Suframa angle touches Intelbras's own footprint directly.

---

### 5. Read-across logic Rafael uses repeatedly

When you see a story, run this lookup table BEFORE deciding the tag:

| Story type | Covered-name reads |
|---|---|
| Anatel / 5G / 700 MHz / pole access / FIIS / AGU pole-sharing rulings | AMX/TEF-BZ/TIM (+ BRISANET, Unifique when ISP-specific → use `AMX/TEF-BZ/TIM/ISPs:`) |
| STF tax ruling (ICMS, FUST, FUNTTEL, FISTEL) | AMX/TEF-BZ/TIM |
| V.tal, Oi creditors, BTG | AMX/TEF-BZ/TIM (TIM most directly via parent dynamics) |
| Mexico CRT / Altán / OMV licensing / Padrón de Telefonía / Altán biometric simplification / dynamic spectrum auction platform | AMX (always); TIGO if OXIO-related |
| Colombia ANE / Coltel / Movistar Colombia / Movistar Colombia portability fines | TIGO (primary), AMX (secondary) |
| Argentina Enacom / TEO–TMA merger / Argentina antitrust pronouncement | TEO, AMX (secondary) |
| Chile fragmentation, four-operator dynamics | TIGO |
| D2D satellite, Amazon Leo, Globalstar, Sky Móvel/Amazon Leo | AMX/TEF-BZ/TIM/TIGO |
| Brazil data centers / sovereign cloud / Redata tax regime | AMX/TEF-BZ/TIM (telco-as-infra / sovereign-cloud base, per E 27-Apr Oracle item); `BR:` country line otherwise — sector color unless a covered telco's capex/partnership is named |
| SAP / Oracle NetSuite / Sage / ServiceNow / Salesforce / Microsoft ERP / Microsoft Copilot pricing | TOTVS (`TOTVS: peer ticker:` or `TOTVS/Sage:` format) |
| SaaS-incumbent stock move / forecast disappointment on AI-disruption fears (Salesforce/CRM, Workday) | TOTVS (multiple-compression / SaaS-multiple read-through — sentiment/valuation, not earnings) |
| Oracle / US-software earnings + capex guide (Keirstead) | TOTVS (`TOTVS: Oracle:` peer read — cloud-capex / SaaS-multiple sentiment color, not earnings) |
| Anthropic / OpenAI enterprise pricing | TOTVS (positive — governance), GLOB/CINT (negative — cost input) — use `TOTVS/GLOB/CINT:` only when split-direction read is the actual hook |
| Hyperscaler / enterprise coding-agent cost surge (Microsoft, Uber, Anthropic-customer disclosures) | `TOTVS/GLOB/CINT:` split-direction (governance vs. input cost) |
| ACN / COG / INFY / TCS / EPAM / IBM / Capgemini (CAP) | GLOB/CINT |
| Mercado Libre / Amazon BZ / Shopify | VTEX/LWSA |
| Amazon AWS / agentic productivity launches | TOTVS (governance angle) and VTEX/LWSA (commerce angle) — choose based on whether the news is enterprise-AI or marketplace-economics |
| Netflix / WBD / streaming consolidation | TV |
| TelevisaUnivision capital structure / tender offers / debt refis / Televisa MX telecom M&A | TV |
| Nubank / NuCel / fintech-telco / PicPay-telco | AMX (primary), TIM (negative — direct partner with PicPay but prepaid drag dominates), TEF-BZ (Vivo Pay angle) |
| Brazil MVNO landscape / Surf Telecom enabler / branded-MVNO launches (SKY Móvel, Correios, iFood, Motu, Vero) | AMX (wholesale-host tailwind, esp. via NuCel on Claro); AMX/TEF-BZ/TIM (rising MVNO share = competitive-intensity read, heavier on prepaid-exposed TIM) |
| LatAm telco dividend / payout-policy / FCF-yield relative value / Selic-driven yield reprice | AMX (top pick, compressed least), TEF-BZ (Vivo defensive high-dividend), TIM (~8% yield / +35% payout growth); `AMX/TEF-BZ/TIM:` for a sector-wide payout/yield readout |
| BZ smartphone/electronics import-tariff / Zona Franca de Manaus / Suframa | INTB/POSI/MLAS (sector); promote to name-specific only when tax exposure or capex is quantified per ticker (INTB on Manaus footprint) |
| HFS Research / panel commentary on IT services AI delivery | GLOB/CINT |
| CFO/IT-exec survey evidence on AI ROI / productivity impact (Duke CFO survey, UBS Evidence Lab) | GLOB/CINT (Negative when "no impact / unclear ROI" is the signal) |
| AI cost-per-task / token budgets / domain-specific agents | TOTVS (system-of-record governance angle) |
| LWSA/Wake AI product launches | LWSA (single-ticker promotion when name-specific) |
| Reforma tributária / telecom tax-credit transmission | AMX/TEF-BZ/TIM (use Griselli's "neutral long-term via credits" framing) |
| BZ mobile front-book / back-book price increases (e.g., AMX-Claro +14% Apr pure-postpaid) | AMX/TEF-BZ/TIM (rational-pricing / ARPU-support read; watch churn follow-through in Anatel data) |
| Brisanet quarterly results / strategic pivots (Brisaplay→SKY+) / regional-ISP M&A | BRISANET single-ticker (promote on quarterly prints / capex / 5G; otherwise Other News, or `AMX/TEF-BZ/TIM/ISPs:` if regulatory and group-wide) |

---

### 6. Note-writing style and editorial conventions

**Mandatory format:**

```
📍 [TICKERS]: [Headline that frames investment relevance]

What happened:

- [Opening bullet — context: "According to [source]…", "We met with…", "At [event]…", "In a note by [Analyst]…"]
- **[Bold sub-header, 4–8 words, sentence case]:** [2–4 sentences. Factual only. Attributed.]
- **[Bold sub-header]:** [2–4 sentences. Factual only.]
(1–4 content bullets total)

🔎 UBS's take:

[Signal] read for [TICKER]. [3–6 sentences. Analytical only. Never restate facts. Close with forward-looking or monitoring flag.]
```

**Fast Take format (per G/wiki — short-form variant for single-metric/earnings moments):**
- Max 100-character title, max 250-character body.
- Format: `📍 [TICKER]: [Message headline]` + body paragraph.
- Use for quarterly margin records (e.g., TIM 4Q25 "Margem recorde…"), high-conviction single-metric reads, earnings flash takes. Recurring case in H: TIM (29 notes) and TEO (7 notes) leverage Fast Take format around quarterly prints.

**Directional signal vocabulary (calibrated from H — 151 published notes):**
- Positive (used ~36×) — clear directional benefit
- Neutral (~28×) — color without changing the view
- Slightly positive (~22×) — directional but second-order
- Mixed read / Mixed but skewed [positive/negative] (~17×) — competing forces
- Slightly negative (~12×)
- Negative (~8×)
- "Doesn't move the needle" (~2×) — use sparingly when impact is real but immaterial at the stock level

The Mixed/Slightly-positive/Slightly-negative bucket is ~33% of all takes — when in doubt, prefer the calibrated middle. Pure "Positive/Negative" only when the directional read is unambiguous. Use "Mixed read" specifically when the same event has opposite-direction reads across covered names (e.g., Anthropic pricing shift = TOTVS slightly positive AND GLOB/CINT slightly negative, or coding-agent cost surge = same split) — and spell out both directions in the take.

**Hedging language is mandatory in the take.** Use: may, might, could, suggest, indicate, in our view, we believe, we expect, warrants monitoring, opens the door for, raises the question of, could be perceived. Never assert future certainty.

**Recurring writing-style feedback observed in C (apply preemptively):**
- "Make it more concise" — default to fewer words. Two passes: write, then cut 20%.
- "Don't restate the factual section in the take" — the take must add analysis, not summarize.
- "Follow the one before that was good" — keep prior-note tone consistent; if the user shifts tone, mirror the new direction immediately. If the user says "now its too concise, follow the one before that was good," restore the prior level of detail without re-padding.
- "Be more direct on the take" — open with the signal; subject + verb; no warm-up sentence.
- "Mention launches or product launches planned" — when management discusses pipeline, name the launches explicitly in the title.
- "Make TIM's part more concise" — for multi-operator takes, the third paragraph is the one most often cut. Keep it under 3 sentences.
- For headline drafting, offer 3–5 short alternatives when the user is choosing — not 1 long version. Recurring shortlist style observed in C: numbered list, each ≤90 chars, ticker prefix included. Use `TOTS3:` prefix in draft shortlists when the ultimate clipping/note ticker is `TOTVS:` — this matches Rafael's draft style.
- Use `mn` not `m` for millions; spell out `bn` for billions; use `R$`, `US$`, `MXN`, `COP`, `ARS` as appropriate.
- Currency framing: "~US$220m for La Nación stake", "USD 214.4M for the 67.5% OPA" — match the source's convention.
- Avoid jargon ("systems of record", "D2C", "T-as-a-Service") unless defined in-line.
- Single emoji per section: 📍 for title, 🔎 for take. No others in body.
- When Rafael flags an unclear or awkward word ("emarbgos? strange wording"), rewrite the entire sentence cleanly in plain English rather than just substituting the word; preserve attribution and dates exactly. Specifically: use "appeals" or "creditor challenges" in English notes, never carry "embargos" through untranslated; clarify "the sale decision" with "the approval of the sale of [asset]" so the antecedent is explicit.
- When Rafael writes a directional sketch in Portuguese or broken English, reconstruct in clean analytical English without losing the directional anchor he gave (e.g., "techfin is suffering because of high interest rates in BZ" → "Techfin's near-term EBIT impact is capped by high BZ rates, in our view"). Preserve every concrete number he supplied.
- When Rafael provides a take-template sentence ("This decision comes following the STF's earlier rulings…"), use his structure verbatim and only modulate the opening clause.
- When Rafael provides only a brief directional cue in Portuguese for ecommerce ("se outros marketplaces aumentarem as taxas pode migrar gmv para plataformas d2c, beneficiando a vtex"), reconstruct as a clean two-direction take with the LWSA-neutral / VTEX-positive split spelled out — do not flatten to a single ticker.
- When Rafael asks "which report we published that?" / "send me the wqritting for me to search", reply with the exact verbatim quote from the source doc (TMT Online Observer Data, Anatel Reports, Crowding Score Data) so he can grep — do not paraphrase or summarize the cited passage.

**Attribution rules:**
- "According to [outlet]…" for press articles.
- "Management noted/stated…" for earnings calls or interviews.
- "In a note by [Analyst Name], [team] reviewed…" for sell-side reports (Hodulik for US Telecom, Olmos for LatAm, Chandrasekar for SAP, Karl Keirstead for US software/Oracle, Weston for EMEA Pharma when H&E pipeline is cross-referenced).
- "At [event], [person] highlighted/stated that…" for conferences (HFS Research webinar, CFO event, NDR, site visit).
- Reference past UBS notes with placeholders: "We note that in our recent [report/marketing/NDR]…", "Assessing Nucel's risk: uneven exposure across Brazilian carriers".

**Source whitelist (use as primary anchor):**
- Bloomberg, Reuters, FT, WSJ, Bloomberg Línea, The Information, Gizmodo (corroboration), PYMNTS (procurement angle), El Economista, RCR Wireless, El País
- DPL News, TELETIME, TeleSíntese, Valor Econômico, Estadão, Ecommerce Brasil
- Anatel, CRT (Mexico), ANE (Colombia), Enacom (Argentina), STF, CADE, Superfinanciera/MinHacienda (Colombia) filings
- Conference call transcripts (TEF-BZ Vivo, TIM Brasil, AMX, TIGO/Millicom, TOTVS, GLOB, CINT, TEO, VTEX, LWSA, BRISANET)
- UBS reports (Hodulik, Olmos, Salles, Farias, Chandrasekar on SAP, Keirstead on US software/Oracle, EMEA Pharma's Weston cited only for H&E pipeline)

**Source greylist (acceptable in clipping, never anchor a note):**
- TipRanks, GuruFocus, Investing.com, marketscreener.com, AD HOC NEWS, AOL.com, Moomoo. These are aggregators; if they are the only source, find the primary outlet first. F shows AD HOC NEWS (47), Investing.com (46), TipRanks (48), marketscreener.com (41), Moomoo (35), AOL.com among the top-volume sources — most of their contribution is clipping-level noise, not note material.
- DPL News (top source in F at 171 uses) is whitelist — it is a primary LatAm telecom outlet (e.g., ANE Colombia spectrum plan was DPL-anchored). Globant Newsroom (35) is acceptable for GLOB filings/press but never anchor a take that requires independent confirmation. TELETIME News (45) duplicates with Teletime (50); dedupe in source counts.

---

### 7. Monthly cadence pieces (always reserve space)

- **Anatel monthly data note** — first week of the month; format and structure fixed (see §4 Telecom Brazil).
- **Monthly portability note** — same release, can be standalone or merged with net adds depending on the read.
- **Monthly crowding score note** — Communication Services + Information Technology sectors; one paragraph per name (TIGO, TIM, TEF-BZ, AMX; VTEX, TOTVS, GLOB, CINT). Tie each move to a stock-specific or sector-specific catalyst observed that month in the TMT Online Observer Data. Calibration baseline from G (Crowding Score Data, prior reading): Communication Services sector +0.28 (+0.21ppts MoM); TIGO standout at +5.00 (+1.63ppts MoM, post-Q4 beat + US$3/share dividend + post-M&A margin visibility); TIM +3.29 (+0.77ppts MoM, on 2026 guidance — 35% YoY shareholder payments, ~8% dividend yield, ~5% MSR growth, 6–8% EBITDA); AMX broadly flat at -0.99 (+0.02ppts MoM, conservative shareholder-remuneration expectations amid Desktop / TEF-Chile M&A signals); TEF-BZ the exception at +0.21 (-0.26ppts MoM). IT sector: VTEX most crowded in Software on profitability pivot (FY26 EBIT margin guided low-20%s); TOTVS crowding around stock declines + discount-to-peers framing (~19× 12m fwd P/E vs. ~22.5× 3Y avg, ~9% discount to global software peers vs. ~20% historically). Most recent reading (G, Crowding Score Data 2026-06-03): Communication Services +0.45 (+0.17ppts MoM); TIGO declined sharply to +2.20 (−2.80ppts, profit-taking after ~10% April outperformance, now ~12.4% 12m fwd FCF yield vs. ~9% LatAm peers); TEF-BZ rose to +1.79 (+1.58ppts, partly on AMX-Claro's +14% April pure-postpaid price increase easing competitive fears); TIM broadly flat at +3.11 (−0.18ppts); AMX edged up to −0.74 (+0.25ppts). IT: VTEX still most crowded at +6.09 (+0.82ppts, profitability pivot); TOTVS fell to +1.98 (−0.57ppts, on the global software de-rating ~30% peers / ~13% TOTVS since Dec-25); Intelbras −2.50 (−0.19ppts, mixed Q4). Tie each move to a stock-specific or sector-specific catalyst observed that month.
- **Quarterly ESG TMT recap** — co-authored with Andre Salles. Telecom + Technology split, two themes per sector, COP / CDP / S&P CSA scores, data-center and renewable-energy deployments. Recurring data points to surface (4Q25 calibration from C): TEF-BZ at CDP A List for 6th consecutive year, Amazon biodiversity initiative (800 ha / 30 years / 900k trees), R$3.2bn LTM revenues from energy/climate-efficiency solutions, Vivo S&P Global CSA 89 points (5th globally), TIM Brasil CDP A List 3rd time + Axia Energia partnership, GLOB 2025 Integrated Report (14.6% YoY GHG reduction, A− CDP Supplier Engagement Assessment score, 2,787 volunteers / 34,073 hours / 135k+ beneficiaries). The "technology" half of the recap routinely names data-center and Redata-approval moves (4Q25) — keep this tied to the §4 Brazil data-center / Redata watch line. Structure template: "In [Quarter], telcos kept the ESG narrative grounded in two fronts: (i) [theme 1]; and (ii) [theme 2]. Across technology, ESG-related moves in the period were concentrated in [data centers / renewable energy / specific Redata/AI infra approval]."

---

### 8. Things to systematically NOT do

- Do not produce a note off aggregator-only sourcing (TipRanks, GuruFocus, Moomoo, AD HOC NEWS, Investing.com, marketscreener.com, AOL.com). Search for the primary outlet first.
- Do not assert future outcomes ("will", "is going to"). Hedge.
- Do not restate facts in the take section.
- Do not use the local B3 ticker (VIVT3, TIMS3, TOTS3) in headlines; use the alias (TEF-BZ, TIM, TOTVS). Exception: the Sell-side section of the clipping may use `TIMB:` / `VIV:` for broker rating changes; draft note-headline shortlists may use `TOTS3:` per Rafael's recurring draft style.
- Do not write notes off "spectrum plan" or "spectrum agenda" high-level institutional documents unless they contain specific band allocations, auction timelines, pricing mechanisms, or operator-specific implications. Wait for concrete items. (E.g., the ANE Colombia 2026–2030 plan is too high-level on its own — wait for D2D licensing frameworks, shared-spectrum rules, or specific band auctions.)
- Do not mix Ecommerce and Software and AI buckets — VTEX/LWSA stay in Ecommerce; TOTVS stays in Software and AI even when its news is fintech (Techfin).
- Do not promote `MELI` to its own note unless it's earnings, capital allocation, or a direct LatAm e-commerce TAM shift. Sector context only otherwise.
- Do not let "AI", "Regulatory", "ANTHROPIC", "EPAM", "ACN" become *note* ticker tags — they are themes/peers; re-tag to the covered name that actually wears the read. Country prefixes ("MX", "BR", "CO") are allowed ONLY as country-level *clipping* lines (like `Sector:`) for broad market color with no single-operator hook (per E 27/30-Apr); the moment a covered name is directly affected, use its alias (AMX/TIGO/TEF-BZ/TIM/TEO) and never anchor a note on a bare country prefix.
- Do not let `INTB/POSI/MLAS` become a backdoor for generic BZ electronics-tariff or smartphone-pricing pieces (incl. Oppo/Realme/Foxconn/Suframa expansion press). Promote to note only when a single covered name (INTB capex/dividend, POSI tender, MLAS receivable) is the actual hook.
- Do not let tier-1 H names (AMX, GLOB, CINT, TOTVS, TIM, TEF-BZ, TIGO) get curated as `Sector:` when the headline is name-specific — the covered alias must lead.
- Do not carry untranslated Portuguese legal vocabulary ("embargos", "outorga", "liminar") in English notes without inline translation — rewrite cleanly and preserve the attribution.
- Do not write `[empty]` under a sector header when there are zero items; skip the header entirely (known formatting bug from the 28-Apr clipping).
- Do not promote Globant securities-litigation/investigation press releases to a full note — surface once per litigation cycle as a `Sector:` line. Promote only on a court ruling, settlement, or material disclosure event.
- Do not paste aggregator-style "Earnings Preview" headlines into the sector bucket — move them to Next Results/Events as a date entry with ticker only."""
