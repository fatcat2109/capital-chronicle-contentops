# ContentOps Four-Trigger Data Resolution and Editorial Operating Model V1

Status: owner-approved additive operating plan, implementation-ready design  
Authority: CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md; CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md; CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md  
Shared dependency: Capital Chronicle Four-Trigger Analysis and Data Operating Model V1  
Non-authority: this document does not own Core numeric truth, broker execution, mutable Main App status, routine V1 publication authority or V2 public-write authority.

## 1. Purpose

ContentOps uses the same evidence-resolution method as Capital Chronicle when it plans or researches content:

1. identify the editorial question and audience need;
2. create a versioned DataNeedPlan;
3. query the governed Capital Chronicle database first;
4. use Codex Desktop with bounded BrowserOS read-only recovery only for named gaps;
5. preserve source identity, timestamps, rights, freshness, hashes and epistemic state;
6. produce an editorial packet that keeps report truth, event truth, Capital Chronicle analysis and scenario/uncertainty separate.

This adds a shared planning seam. It does not rebuild the V1 publisher, durable store, Simple scheduler, canonical Substack route, eight-derivative compiler or readback/reconciliation owner.

## 2. Four entry channels for ContentOps

| Channel | ContentOps use | Current owner and boundary |
| --- | --- | --- |
| Foundation coverage and serving | Declare needed official events, macro fields, market context, headline evidence and SEC/fundamental fields; expose public-safe coverage/readiness projection | Shared with Main App; ContentOps is not numeric authority |
| Scheduled latest intelligence | Use newest reconciled headline/event interval to choose an editorial research question and request supporting facts | Simple Gemini remains V1 owner; input contract, not a fifth routine window |
| Scheduled daily portfolio context | Request only owner-approved public-safe market context when it helps editorial planning; never expose Jim private positions | Portfolio control plane remains Main App-owned |
| Jim manual request | Jim asks Codex Desktop for a source-backed briefing, market context or content plan; scope is fixed before BrowserOS recovery | Owner-operated research surface; no automatic publication or account action |

X/high-volume headline ingestion remains the existing CDP ingestion seam. BrowserOS is for bounded source recovery and approved browser-rendered data acquisition, not high-volume ingestion replacement.

## 3. Shared request and evidence contracts

ContentOps sends consumer_route=CONTENTOPS_EDITORIAL and uses the Main App contracts:

- CapitalChronicleTriggerRequestV1;
- CapitalChronicleDataNeedPlanV1;
- CapitalChronicleDataResolutionReceiptV1;
- CapitalChronicleAnalysisRunReceiptV1 when analytical context is returned;
- CapitalChronicleServingCoverageProjectionV1 for public-safe capability/readiness views.

The adapter adds editorial mode, audience, language, requested format, claim sensitivity/harm class, sourceability threshold, maximum source expansion, publication target, research-only/draft-only/publishable intent and required epistemic state. Successful resolution does not make a claim publishable; the existing deterministic claim/source/epistemic validator decides qualification.

## 4. Database-first resolution

For each request, search:

1. canonical retained headline/event sidecars and published memory;
2. official event history, filings and provider records admitted to the database;
3. existing market/asset/portfolio-safe read models;
4. approved BrowserOS read-only recovery for a specific missing need;
5. explicit unavailable or DATA_BLOCKED state.

The receipt states why each lower layer was used. A stale row, unverified social post or presentation widget is not silently upgraded into numeric or event authority. Current and historical evidence remain separate, and revised official values retain vintage/known-at semantics.

## 5. BrowserOS recovery boundary

Codex Desktop may invoke BrowserOS for a named source question when the database cannot provide a fresh/admissible answer and the source is permitted. The recovery packet records visible source identity, retrieval time, source timestamp, exact fields needed for the claim, durable hash/capture reference, rights class, epistemic state, contradictions, why DB was insufficient and remaining missing/stale fields.

BrowserOS must not read credentials, cookies or session tokens, select accounts, publish, comment, send messages or access private portfolio state. Later public writes continue through existing Edge CDP 9223 owner and UNKNOWN_WRITE reconciliation. BrowserOS is read-only in this plan.

## 6. Editorial lifecycle

    headline/event or Jim request
      -> editorial TriggerRequest
      -> DataNeedPlan
      -> database-first queries
      -> bounded BrowserOS recovery for named gaps
      -> immutable DataResolutionReceipt
      -> existing selector/writer/validator
      -> qualified article or explicit abstention
      -> canonical Substack publication/readback
      -> eight derivative packages and reconciliation

Packets distinguish OBSERVED_FACT, ATTRIBUTED_REPORT_OR_INTERPRETATION, CAPITAL_CHRONICLE_ANALYSIS and SCENARIO_OR_UNCERTAINTY. A market direction, GEX signal, macro proxy or Core output is context, not an observed fact without matching evidence.

## 7. Compatibility with current V1 and V2

- Routine V1 remains SIMPLE_GEMINI_RUNTIME with windows 17:00, 21:00, 23:00 and 01:00 Asia/Bangkok.
- Do not add a fifth routine task, revive native Desktop Automations as routine owner, rebuild transports or create a second publication store.
- V1 retains existing candidate/selector/source GET/writer/revision ceilings and eight-derivative contract.
- V2 remains isolated with separate authority and no-public-write assumption.
- Public-safe web projections may expose coverage/freshness/rights/exact-proxy state; private portfolio facts remain outside ContentOps.
- Investing.com calendar and TradingView remain presentation surfaces; retained database and official records remain authority.

## 8. Implementation sequence

1. Add adapter and schema validation for shared request, need-plan and resolution receipts.
2. Bind adapter to existing sidecars, published memory and admitted database views without changing source ownership.
3. Add bounded BrowserOS read-only recovery with source/rights/epistemic receipts and explicit unavailable states.
4. Shadow one scheduled latest-intelligence research packet through existing Simple path.
5. Shadow one Jim manual research request through Codex Desktop.
6. Add public-safe coverage/freshness/rights/exact-proxy fields to existing read model.
7. Validate replay, contradiction, stale-source, rights and no-write behavior; publish one durable handoff.

Each step leaves changed paths, contract hashes, tests, current owner, unresolved gaps and an exact next command. Quota exhaustion or paused runtime is a checkpoint event, not a reason to create a duplicate scheduler or repeat completed evidence work.

## 9. Acceptance

The adapter is ready for the next bounded Builder goal when:

- a request is created, deduplicated and resumed from a durable checkpoint;
- DB-first resolution returns source identity, clocks, freshness, rights and missingness;
- BrowserOS recovery is read-only and produces an immutable receipt;
- the existing selector/writer receives only a scoped editorial packet;
- epistemic state survives the article and all eight derivatives;
- no private portfolio data or broker authority crosses into ContentOps;
- no V1 scheduler, publisher, store or publication owner is duplicated;
- replay and contradiction tests cover fact, attributed report, analysis, scenario and abstention paths.
