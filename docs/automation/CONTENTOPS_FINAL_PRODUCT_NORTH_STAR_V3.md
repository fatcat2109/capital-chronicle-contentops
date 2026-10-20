# Capital Chronicle ContentOps — Final Product North Star V3

Authority date: 2026-10-20
Status: `CURRENT_ROOT_PRODUCT_NORTH_STAR / EARLY_ATTRIBUTED_INTELLIGENCE / V1_ACCEPTED`

This document records the current product direction. It supersedes conflicting current-looking wording that requires universal official confirmation, routes routine V1 through historical model fleets, says routine V1 public-write/readback remains ungranted, or says `V1_FINAL_PRODUCT_ACCEPTED` is still pending.

## 1. Product role and North Star

Capital Chronicle/Core Analyzer owns proprietary analytical and numeric truth. ContentOps is the autonomous early-signal financial newsroom, distribution, readback/reconciliation, organic audience-acquisition, and bounded-learning engine.

V1 product promise:

> Tell readers early what credible sources are reporting, exactly label what is confirmed versus unconfirmed, relayed, leaked, disputed, or rumor, explain why it matters now, and update the state when evidence changes.

North Star:

> Build an autonomous early-signal financial newsroom that reliably publishes 5–8 useful articles per production day by surfacing credible market-moving reports before official confirmation when warranted, preserving exact source attribution and visible epistemic state, adding Capital Chronicle's evidence-bounded analysis, criticism, and contrarian framing, then distributing and learning what drives qualified audience growth — without ever converting an unconfirmed report into confirmed fact or engagement into truth authority.

The moat is minimizing **time-to-awareness** while preserving **epistemic honesty**.

## 2. Current owner state

Jim has explicitly granted:

- `V1_FINAL_PRODUCT_ACCEPTED = TRUE`;
- routine V1 public-write/readback authority for the accepted V1 product path.

Repository merge commit `db0befb8ad44f1080c67fcb801e5470ce7852369` records that grant.

This acceptance does not bypass exact destination identity/readiness, canonical Substack identity, strict readback/reconciliation, or `UNKNOWN_WRITE` safeguards. V2 public-write authority remains zero unless separately granted.

## 3. Alpha-speed doctrine

Financial markets often price credible reporting before an issuer, government, regulator, or other primary actor confirms it. Therefore:

- official confirmation is not a universal prerequisite;
- a credible reputable newsroom report may itself be the publishable event;
- the factual proposition may be `Publisher X reports Y` while `Y happened` remains unconfirmed;
- an exact accepted newsroom-owned social post may prove that newsroom's reporting act without proving the underlying event;
- an exact approved trusted relay may support only `Relay R, citing Publisher X, reports Y`;
- an exact approved rumor record may support only a visibly marked rumor proposition;
- confirmation, denial, dispute, or material clarification is a new editorial event, normally a `FOLLOW_UP_UPDATE`.

Do not spend scarce GET/model budget seeking official confirmation merely to make a timely attributed report look more certain. Prove the proposition actually being published.

## 4. Report truth and event truth

Keep separate:

1. **REPORT TRUTH** — did the named source actually report/post/relay the proposition?
2. **EVENT TRUTH** — is the underlying event independently established?

A PASS on report truth never implies a PASS on event truth.

The model never upgrades report truth into event truth by judgment.

## 5. First-class epistemic state

Every current-event article carries machine-readable epistemic state through canonical writing, qualification, derivative packaging, publication/readback, and follow-up reconciliation.

Evidence basis:

- `PRIMARY_EVENT_EVIDENCE`
- `DIRECT_REPUTABLE_REPORT`
- `DIRECT_NEWSROOM_SOCIAL_REPORT`
- `TRUSTED_RELAY_ATTRIBUTED_REPORT`
- `TRUSTED_MARKET_RUMOR`

Underlying-event state:

- `CONFIRMED`
- `UNCONFIRMED`
- `PARTIALLY_CONFIRMED`
- `DISPUTED_OR_DENIED`
- `SUPERSEDED`

Origin characterization, only when source-supported:

- `ON_RECORD`
- `ANONYMOUS_OR_INTERNAL_SOURCES`
- `LEAK`
- `RUMOR`
- `UNSPECIFIED`

Multiplicity:

- `SINGLE_SOURCE`
- `MULTI_SOURCE`

`UNCONFIRMED` is a valid publication state. It is not permission to write the event as confirmed.

## 6. Public labeling contract

Reader-facing uncertainty must remain visible where material. Valid forms include `CONFIRMED`, `UNCONFIRMED REPORT — PUBLISHER`, `SINGLE-SOURCE REPORT — PUBLISHER`, `RELAYED / UNCONFIRMED — citing PUBLISHER`, `MARKET RUMOR — UNCONFIRMED`, and `DISPUTED`/`DENIED` where later evidence requires it.

For unconfirmed/relayed/rumor coverage:

- headline/dek retains material attribution or equally prominent epistemic label;
- opening paragraph makes reporting state clear;
- factual details remain no broader than exact source support;
- consequence analysis is conditional where dependent on the unconfirmed event;
- all eight derivatives preserve epistemic state.

A derivative may compress wording, never certainty.

## 7. Evidence and editorial edge

Evidence burden follows the claim actually made. One exact accepted reputable secondary may support a narrow ordinary attributed claim while the event remains unconfirmed. Primary/official evidence is preferred when directly relevant and cheap, but is not mandatory for every attributed report.

Arbitrary social posts remain discovery/ranking only. Exact canonical-X relay/rumor authority is record-scoped and narrow. High-harm allegations, misconduct/crime, casualty/death, conflict, and similar claims retain enhanced risk handling.

Public prose preserves distinct layers:

- `OBSERVED_FACT`
- `ATTRIBUTED_REPORT_OR_INTERPRETATION`
- `CAPITAL_CHRONICLE_ANALYSIS`
- `SCENARIO_OR_UNCERTAINTY`

Capital Chronicle analysis may be strong, critical, skeptical, or contrarian when premises are supported. Blandness is a product failure; fabricated outrage is also a product failure.

Engagement may improve angle, packaging, timing, and distribution. It may never change truth, epistemic state, source attribution, permissions, or CC numeric authority.

## 8. Current V1 editorial architecture

Routine V1 target ownership is `NATIVE_CODEX_DESKTOP`, with the owner-approved three-stage method:
Luna/Terra MAX filters X headlines; `gpt-6.1-sol / low` (Light) selects content and prepares data;
`gpt-6.1-sol / max` writes the article and SEO/house-style package, including a bounded useful revision.
Read `docs/automation/CONTENTOPS_NATIVE_DESKTOP_EDITORIAL_ROLE_POLICY_V2.md` for exact role,
source/tool, style and checkpoint rules. This target supersedes the earlier Sol-low-only method;
the Goal24 isolated proof remains evidence for its older configuration, not this complete pipeline.
Reuse MainReportFeed/current intake, canonical publication memory, reviewed retained research,
evolving story/revision context, <=32 candidates, <=3 admissions and <=6 source requests.
Existing source/claim/epistemic checks and the native eight-channel compiler remain authoritative.
There is no Gemini/9Router, SDK/App-Server, headless or paid API model fallback.

The existing four App tasks own routine scheduling; existing window/day/slot IDs, bounded
catch-up, store/outbox/lease and sole DurablePublicationCoordinator are reused. Legacy Simple
scheduler/start paths are non-routing in target source. Bulk X CDP ingestion remains unchanged;
Neo is the browser path for research and prepared browser-only destination handoffs. Existing
Telegram/Discord/Meta/Threads/LinkedIn API transports remain channel-specific.

Current engineering/deployed state: **PAUSED_NOT_DEPLOYED**. Host schedules, production pause,
store and deployed bytes were not changed by this migration. Native manual proof is isolated.
No current configuration grants activation or public writes. Historical Simple and old Desktop
proofs establish only their exact epochs; do not rebuild their accepted deterministic components.
See `docs/automation/CONTENTOPS_NATIVE_DESKTOP_EDITORIAL_RUNTIME_V1.md` for the supported operation,
exact paused rollout, truthful telemetry, remaining native browser executor boundary and activation.


## 9. Editorial modes

V1 keeps the eight-mode spectrum:

1. `BREAKING_BRIEF`
2. `FOLLOW_UP_UPDATE`
3. `STANDARD_NEWS_ANALYSIS`
4. `CAPITAL_CHRONICLE_VIEW`
5. `WHAT_THE_MARKET_IS_MISSING`
6. `EVERGREEN_EXPLAINER`
7. `DATA_OR_DOCUMENT_LENS`
8. `WEEK_AHEAD_OR_WATCH`

Quiet day is not silent-day permission. Lower materiality or choose another mode before giving up; never lower truth or attribution standards.

## 10. Output contract

Final live target is **5–8 PUBLISHED ARTICLES** per newsroom production day, each useful and non-filler.

Historical zero-write benchmark: **4 QUALIFIED ZERO-PUBLIC-WRITE ARTICLES / 32 DERIVATIVE INTENTS** per newsroom production day. It remains telemetry/economics evidence, not a launch or acceptance prerequisite.

Candidate-level abstention is valid. Whole-day silent success below the live target without an exact hard external blocker is `DEGRADED_DAILY_OUTPUT_DEFICIT`.

Routine windows remain 17:00, 21:00, 23:00, and following 01:00 Asia/Bangkok under one deterministic production day. No fifth routine task merely to chase quota.

## 11. Publication and update lifecycle

Substack is canonical. The eight V1 derivative destinations are Telegram, Discord, X, LinkedIn, Facebook Page, Instagram Business, Threads, and YouTube Community.

## Four-trigger data-resolution extension (owner direction 2026-10-18)

ContentOps uses the shared Capital Chronicle request/resolution method through consumer_route=CONTENTOPS_EDITORIAL. Foundation coverage, scheduled latest-intelligence context, scheduled portfolio-safe context and Jim manual research are entry channels into the existing editorial path; they are not a new publisher or a fifth routine scheduler.

The adapter queries the governed database first. When a named editorial need is absent or stale, Codex Desktop uses the existing BrowserOS Neo research/startup seam and records source identity, clocks, rights, freshness, hash and epistemic state. X/headline ingestion remains CDP ingestion-only. The input extension retains four windows, canonical Substack, eight derivatives and UNKNOWN_WRITE recovery; native Desktop ownership supersedes its former Simple owner. See CONTENTOPS_FOUR_TRIGGER_DATA_RESOLUTION_AND_EDITORIAL_OPERATING_MODEL_V1.md.

### Latest Capital Chronicle report as editorial input

The four analytical cases now include substantive foundation asset reports, daily headline
thesis updates, daily holdings UNION active-recommendation review and Jim manual analysis.
ContentOps consumes their public-safe latest report envelopes through
CONTENTOPS_CAPITAL_CHRONICLE_LATEST_REPORT_BRIDGE_V1.md. It preserves report/event/analysis/
scenario layers and follows material changes, corrections and invalidations without rebuilding
Core or accessing private portfolio data. A report recommendation is conditional research,
not an executed order or independent observed fact.

Accepted publication lifecycle:

`qualified article -> canonical Substack publish/readback -> exactly eight derivative attempts -> destination-local recovery -> strict reconciliation`

A counted published article requires exact canonical identity/readback. Derivatives use the real reconciled canonical `/p/...` URL, never a pending placeholder.

`UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`

Epistemic lifecycle remains separate:

`UNCONFIRMED/RELAYED -> CONFIRMED | PARTIALLY_CONFIRMED | DISPUTED_OR_DENIED | SUPERSEDED`

## 12. Accepted foundation and current activation route

1. Implement and independently audit the native Desktop migration on PR90, preserving Goal20–23 evidence.
2. Verify one isolated native Sol-low editorial flow, actual reader copy/native previews/media and replay.
3. Preserve the exact paused four-task rollout and per-channel API/Neo setup/readback handoff.
4. After separate audit/deployment authority, apply the one documented activation transition with pause release last.
5. Observe natural runtime separately; 5–8/day reliability is unproven until actual reconciled output establishes it.

No production activation, public write, pause release, self-merge or deployment is part of Goal24.

Historical Simple selection/source/validation/compiler/recovery proofs remain provenance. Reuse their deterministic components.

## 13. Hard boundaries

Never fabricate a report/source/leak/rumor/quote/number/event; present unconfirmed material as confirmed; infer leak/rumor without source support; publish unsupported high-harm allegations; promote external reporting into proprietary CC numeric authority; expose secrets/session material; destructively mutate production state; or blind-retry an ambiguous write.

Chrome `CapitalChronicleBot` CDP 9222 remains ingestion-only. Neo is the target browser publication/readback path; Edge 9223 is historical deployment provenance.

Protected historical `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.

## Evolving Main intelligence, original research and demo privacy (owner update 2026-10-19)

ContentOps serves two complementary inputs: eligible public-safe Main report updates and
independently acquired, rights-checked newsroom evidence. Retain exact source/capture/known-at,
revision, permission and epistemic state. A Main report returning through the context feed is
recirculated analysis, not independent confirmation or a new factual observation.

Consume Main's versioned immutable public manifest and lawful parent chain through the existing
latest-report feed. Missed-history/cold-start/restart, corrections and withdrawals must preserve
lineage without per-report manual Git pointers. A non-editorial ancestor may establish lineage
under the Main-owned contract; it cannot create a writer intent or become publishable content.
A fixture, copied schema or valid hash alone is not real cross-repository admission proof.

Capital Chronicle's designated demo is private portfolio/learning infrastructure. Account IDs,
balances, positions, fills and demo performance stay outside public packets, copy and media.
No demo result establishes public alpha claims or real-money authority. Main's newer policy
requires credible prospective paper/demo alpha evidence and fresh Jim authorization before any
real-account transition; ContentOps cannot grant or perform that transition.

Use the existing Simple writer/validator, source-backed chart/media owners, Daily App and
canonical publication/recovery path. Research, controlled previews, fresh provider output,
validated copy, publication and natural production results remain distinct. Preserve the current
operator LLM pause and runtime state; this update does not restart them or extend V2 authority.
See [the bridge plan](CONTENTOPS_CAPITAL_CHRONICLE_LATEST_REPORT_BRIDGE_V1.md) and
[dated reconciliation](CONTENTOPS_OWNER_UPDATE_RECONCILIATION_20261019.md).
