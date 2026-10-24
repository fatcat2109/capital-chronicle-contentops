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
exact paused rollout, truthful telemetry, bound native Neo request/return/readback loop and separate activation boundary.


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
2. Reuse Goal25's isolated Luna-MAX -> Sol-Light -> Sol-MAX flow and byte-stable restart; retain the exact dated source, eight native previews and readback limits in its owning checkpoint.
3. Preserve the exact paused four-task rollout and per-channel API/Neo setup/readback handoff.
4. After separate audit/deployment authority, apply the one documented activation transition with pause release last.
5. Observe natural runtime separately; 5–8/day reliability is unproven until actual reconciled output establishes it.

No production activation, public write, pause release, self-merge or deployment is part of Goal25.

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

## Public research meaning and uncertainty (owner update 2026-10-21)

Preserve the exact permitted question, target/proxy, horizon/cutoff, probability measure,
method/evaluation and selection/dependence from public research into article and derivatives.
Source facts, Main interpretation, conditional scenarios, subjective challengers, statistical
and risk-neutral probabilities remain distinct. Missing metadata stays unknown and is no
universal block on useful factual/qualitative journalism. No score or option valuation becomes
a trade win rate; Main recirculation/shared-release copies do not independently confirm a claim.
Reuse existing admission, native packets, source-review, compiler and coordinator; Main alone
owns numeric estimation/evaluation. No new engine/status/store, role/pause or publication grant.
See [the consumer projection](../editorial/CONTENTOPS_PUBLIC_RESEARCH_SEMANTICS_V1.md) and the
[Goal30 owning handoff](CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal30/RELEASE_HANDOFF.md).
## Goal33 audience feedback continuation (2026-10-22)

`PARTIAL_CAPABILITY_REUSE_COMPONENTS`: native new opportunities freeze the existing guarded
performance policy, dated eligible feedback and canonical published memory. Compact preferences
reach Sol Light selection and warranted Sol MAX writing/SEO/eight native packages; old frozen
requests and prepared articles remain unchanged. Existing metrics, caps, sample/dependence,
rollback, source/rights/numeric/uncertainty and sole coordinator boundaries remain authoritative.
Two exact historical public objects were observed through read-only Neo; no independent reader
question was found and the policy remained HOLD. Actual native selection reused retained articles
and saved three ranked research briefs rather than creating a duplicate. Current edition remains
3 ready / 24 previews / 0 missing; production and four tasks remain paused. No public write,
activation, account change, merge or deployment is claimed. The CLI, Desk and installed
`contentops-newsroom` continuation are documented in
`docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal33/RELEASE_HANDOFF.md`.
Exact remote/CI evidence follows in that directory's `delivery.json`; Control Tower receiver
synchronization remains pending, with these pointers as the discoverable handoff.

## Signal Clips — adopted product scope, 2026-10-23

Named direction: `CONTENTOPS_V3_SIGNAL_CLIPS_V1`. Jim defined this separate speech-video
product and authorized creative North Star design; L1 selected its compatible direction for
L2 reconciliation. This section is the durable product home, not a new status owner or an
activation/publication grant. V1 newsroom and V2 original analytical video remain intact.

**Viewer promise:** understand who said what, why it matters and what to watch next, while
hearing the authentic original words in context. Serve financially interested viewers with
useful, trustworthy moments from Fed/public officials, CEOs, businesspeople, influencers,
earnings calls and interviews, subject to each recording's actual source and reuse scope.
Selection, comparison and explanation are the editorial value; clip volume is not the moat.

Support five story-selected formats through one workflow:

1. **Moment + Context:** the self-contained original moment plus concise factual context.
2. **What Changed:** comparable explicitly dated source statements and the actual difference.
3. **Claim + Check:** the speaker's claim beside supporting/contradictory independent evidence.
4. **Question + Answer:** the correctly associated question and answer, without invented dialogue.
5. **Consequence + Watchpoint:** a supported conditional mechanism and a concrete next observation.

Quote-led fast coverage and explained/comparative coverage share source, selection, edit,
review, package and correction history. No daily clip quota, fixed template or mandatory
commentary/number is introduced. A current clip and an explicitly archival clip stay distinct.

Original audio governs spoken wording. Preserve speaker/event/date, exact source-time spans,
qualifiers, negations, units and adequate surrounding context. Official text/ASR support the
work but do not prove audio delivery or timing. No fabricated speech, cloned voice, synthetic
speaker, meaning-changing splice or question/answer substitution. Translations are labelled.
Keep what the speaker said, what independent evidence establishes, and CC interpretation
separate. A true quotation does not verify its claim or create Core numeric/forecast authority.

Use the existing Speech Highlight Relay, native editorial roles, deterministic media helpers
and compatible review/delivery owners. Bounded Sol-Light selection/preparation and Sol-MAX
meaning/context/SEO work supplement code-owned acquisition, alignment, cuts/cues and hashes.
Luna remains the genuine X-intake filter where applicable. Actual capable picture/audio review
is required for a quality claim; absent hearing evidence remains NOT VERIFIED. Preserve source,
rights, third-party, correction and review bindings. An item-specific HOLD does not stop other
legitimate private engineering or eligible sources.

Initial destinations are YouTube Shorts and TikTok. Prepare truthful native media/captions,
source attribution and metadata; upload/draft/publication require separate exact authority.
TikTok draft delivery is not publication. Public availability, permission, a crop/logo/captions
and monetization eligibility are separate questions; promise no automatic clearance/revenue.

V3 may receive a source directly or through existing qualified discovery without waiting for
a V1 article, V2 completion or the complete database. Reuse source/story/artifact memory and
existing media job/outbox ownership when needed; no parallel scheduler/store/clipper/uploader
or analyzer. Shared/recycled evidence remains one source, never independent corroboration.

Measure usable eligible clips, honest held items, source-to-ready latency, duplicate/recovery
work and actual review effort. Audience return, retention, saves, questions, deeper-content
visits and cost remain observed metrics or unknown. Learning can alter selection/packaging,
never quotation, evidence, certainty or analytical truth. All five formats and intended source
classes remain the full roadmap; one Fed clip cannot certify them or whole-product completion.

Decision provenance: owner proposal SHA-256 `cbba9210a082144cc72ab17e8bb0e8afaf9b832ce82c575121703e2448214480` and completion-plan SHA-256 `8cb6bdac27b70c8d982b46142c1532857099e538da817b470e2831cf432651cd` under `A:/Capital Chronicle/research-audits/2026-10-23-contentops-completion-plan/`; L1 mandate chat `01a0c999-b6b3-7b52-8f8a-a7ecf53d3220`, human turn `01a165a5-ab57-74a0-a98f-f4d2e66027f3`, and this L2's exclusive Tower handoff. Those dated reports remain design/evidence provenance; current repository authority and actual implementation govern. This is candidate-branch adoption until normal integration, not a claim of accepted-master merge.

## Editorial media and data release standard — 2026-10-24

Jim's current CONTENTOPS_V1_EDITORIAL_MEDIA_AND_DATA_RELEASE_STANDARD_V1 makes a relevant, authentic, lawfully reusable photograph and a useful source-bound quantitative chart mandatory for each newly fully release-ready V1 canonical article. A missing asset or unresolved source/rights/identity binding is a release hold, not a completed media package. Historical articles, reviews and proof remain dated history and are not silently promoted. This supersedes any current-looking language that treats empty media/gap notices or fact cards as full release readiness.

Use the existing native flow: story/evidence/data/visual plan -> bounded Neo/source discovery and exact lawful original -> deterministic admitted-data chart -> actual Sol6.1 MAX writing/SEO and bounded same-writer revision -> canonical and eight appropriate previews -> exact revision-bound review/preparation -> sole existing publisher/recovery. Luna MAX filters only genuine X input; Sol6.1 Light plans; Sol6.1 MAX owns prose. Photos have separate source/license/date/attribution/caption/alt and inspected-pixel bindings. Archive context is labelled and never counted as factual corroboration. Charts retain metric/series, unit/currency, period, actual/estimate/forecast, missingness, source and transformation identity. No fabricated history, interpolation, copied proprietary chart or proxy/numeric-authority drift.

An explicitly requested editorial refinement of unchanged retained facts uses the existing source/history owner with EDITORIAL_REVISION, exact prior article/source hashes and no new factual-evidence claim. It does not constitute fresh news or proof of daily throughput. New preparation and public sends must meet the current standard; an old UNKNOWN_WRITE still requires exact readback/reconciliation without retry. Source/copy/media changes invalidate the corresponding prepared review. Actual rendered desktop/mobile canonical and derivative inspection remains required.

V1 is the sole active product priority. V2 and V3 work remain owner-paused until final V1 actually operates live daily; no video/speech dependency or work is authorized by this standard. Runtime, four Automations and publication stay paused; adoption grants no deployment, merge, activation, platform draft/upload/post, spend or new store/scheduler/publisher authority. Historical acceptance and native daily-live proof remain distinct.
