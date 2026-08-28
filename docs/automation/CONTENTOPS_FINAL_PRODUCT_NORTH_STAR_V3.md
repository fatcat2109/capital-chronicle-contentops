# Capital Chronicle ContentOps — Final Product North Star V3

Authority date: 2026-08-28
Status: `CURRENT_ROOT_PRODUCT_NORTH_STAR / EARLY_ATTRIBUTED_INTELLIGENCE`

This revision records Jim's 2026-08-28 owner direction. It supersedes conflicting current-looking wording that requires official/primary confirmation before ContentOps may cover a credible market-moving report, leak, or unconfirmed development. It also supersedes older Desktop-primary routine-editorial wording: current V1 routine execution is the Simple 9Router/Gemini path defined by `CONTENTOPS_V1_SIMPLE_GEMINI_RUNTIME_RESET_V1.md`.

## 1. Product role

Capital Chronicle/Core Analyzer owns proprietary analytical and numeric truth. ContentOps is the autonomous early-signal financial newsroom, media-production, distribution, readback/reconciliation, organic audience-acquisition, and bounded-learning engine.

The V1 product promise is:

> Tell readers early what credible sources are reporting, exactly label what is confirmed versus unconfirmed, relayed, leaked, disputed, or rumor, explain why it matters now, and update the state when evidence changes.

The North Star is:

> Build an autonomous early-signal financial newsroom that reliably publishes 5–8 useful articles per production day by surfacing credible market-moving reports before official confirmation when warranted, preserving exact source attribution and visible epistemic state, adding Capital Chronicle's evidence-bounded analysis, criticism, and contrarian framing, then distributing and learning what drives qualified audience growth — without ever converting an unconfirmed report into confirmed fact or engagement into truth authority.

The moat is not waiting until everything is official. The moat is minimizing **time-to-awareness** while preserving **epistemic honesty**.

## 2. Alpha-speed doctrine

Financial markets often price credible reporting before an issuer, government, regulator, or other primary actor confirms it. A newsroom that requires primary confirmation for every market-relevant development systematically publishes after part of the informational value has decayed.

Therefore:

- official confirmation is **not** a universal prerequisite for publication;
- a credible Tier-1/Tier-2/reputable newsroom report may itself be the publishable event;
- the factual proposition may be `Publisher X reports Y`, even while `Y happened` remains unconfirmed;
- a direct accepted newsroom-owned social post may prove that newsroom's reporting act without proving the underlying event;
- an explicitly trusted market-news relay may support the narrower proposition `Relay R, citing Publisher X, reports Y`; it does not silently become Publisher X or prove Y;
- an unrelated official document never confirms or disproves a different reported event merely because it concerns the same company, government, market, or entity;
- confirmation, denial, dispute, or material clarification is a new editorial event and should normally become `FOLLOW_UP_UPDATE`, not a retroactive reason the timely attributed article should never have existed.

Do not spend scarce GET/model budget hunting for an official source merely to upgrade a timely credible attributed report into confirmed fact. Spend evidence budget on proving the proposition actually being published.

## 3. Separate report truth from event truth

ContentOps must maintain two distinct truth questions:

1. **REPORT TRUTH** — did the named source actually report, post, file, state, or relay the proposition being attributed to it?
2. **EVENT TRUTH** — is the underlying event independently established as having occurred?

A PASS on report truth does not imply a PASS on event truth.

Examples:

- `WSJ reports Nvidia paused part of a financing program` may be supported by an exact WSJ report or accepted WSJ-owned reporting surface even if Nvidia has not confirmed it.
- `Nvidia paused part of the program` requires evidence appropriate to presenting the underlying event as observed fact.
- `A trusted market-news relay, citing WSJ, says Nvidia paused part of the program` may be supported by the exact trusted relay record, but must remain visibly relayed and unconfirmed until stronger provenance arrives.

The model never upgrades report truth into event truth by judgment.

## 4. Epistemic state is first-class product data

Every current-event article must carry an explicit machine-readable epistemic state that survives canonical writing, qualification, derivative packaging, publication/readback, and follow-up reconciliation.

Keep these axes separate rather than collapsing them into one confidence score.

### 4.1 Evidence basis

Use the narrowest basis actually proven:

- `PRIMARY_EVENT_EVIDENCE` — exact primary/official/first-party record proves the event proposition being stated.
- `DIRECT_REPUTABLE_REPORT` — exact accepted reputable publisher/newsroom record proves that publisher reported the proposition.
- `DIRECT_NEWSROOM_SOCIAL_REPORT` — exact accepted newsroom-owned social record proves that newsroom posted/reported the proposition.
- `TRUSTED_RELAY_ATTRIBUTED_REPORT` — exact owner-approved/registry-approved relay record explicitly attributes the proposition to a reputable publisher or named source; this proves only the relay's attributed report unless the original report is separately resolved.
- `TRUSTED_MARKET_RUMOR` — only for an explicitly approved rumor/market-intelligence source and only when the record itself supports rumor treatment. Arbitrary X/social commentary never receives this class.

### 4.2 Underlying-event confirmation state

- `CONFIRMED`
- `UNCONFIRMED`
- `PARTIALLY_CONFIRMED`
- `DISPUTED_OR_DENIED`
- `SUPERSEDED`

`UNCONFIRMED` is a valid publication state. It is not a synonym for false and it is not permission to write the event as confirmed.

### 4.3 Origin characterization

Use only when supported by the source itself:

- `ON_RECORD`
- `ANONYMOUS_OR_INTERNAL_SOURCES`
- `LEAK`
- `RUMOR`
- `UNSPECIFIED`

Never infer `LEAK`, `internal sources`, or `RUMOR` merely because no official source exists.

### 4.4 Source multiplicity

- `SINGLE_SOURCE`
- `MULTI_SOURCE`

Multiplicity informs reader labeling and risk handling. It does not replace source quality or claim-specific evidence.

## 5. Public labeling contract

Reader-facing uncertainty must be visible where it materially changes interpretation. The exact surface wording may vary by platform, but its meaning may not disappear.

Examples of valid labels/forms include:

- `CONFIRMED`
- `UNCONFIRMED REPORT — WSJ`
- `SINGLE-SOURCE REPORT — REUTERS`
- `REPORTED LEAK — BLOOMBERG` only when Bloomberg's record supports leak characterization
- `RELAYED / UNCONFIRMED — citing WSJ`
- `MARKET RUMOR — UNCONFIRMED` only under an approved rumor-source contract
- `DISPUTED` / `DENIED` when later evidence requires it

For an unconfirmed or relayed article:

- headline/dek must retain material attribution or an equally prominent epistemic label;
- the opening paragraph must make the reporting state clear;
- factual details must remain no broader than the exact source record;
- analysis of consequences must be conditional when it depends on the unconfirmed event, e.g. `If the report is accurate...`;
- all eight derivatives must preserve the epistemic state rather than stripping the warning for engagement.

A derivative may compress wording, never certainty.

## 6. Evidence burden follows the claim actually made

Evidence is claim- and mode-specific, not institutionally maximal by default.

For ordinary market/company/policy reporting, one exact accepted reputable secondary may support a narrow attributed claim when the public proposition remains `Publisher reports X`. Existing `reputable_secondary_source`, attribution-required claim handling, and `SUPPORTED_ATTRIBUTED_SINGLE_SECONDARY` semantics are reusable foundation.

Primary/official evidence is preferred when cheaply available and directly relevant, but it is optional for a narrow attributed report unless the article wants to state the underlying event as confirmed fact.

Search, RSS, sitemap, or locator bytes remain locator/report-provenance material only unless their existing source contract explicitly permits a narrower factual use. They never become proprietary Capital Chronicle analytical authority.

X/social handling is layered:

- arbitrary social posts remain discovery/ranking only;
- an exact accepted newsroom-owned post may establish that newsroom's reporting act;
- an exact approved trusted relay may establish the relay's attributed statement, not the underlying event and not the original publisher's exact report unless that provenance is separately verified.

High-harm allegations, misconduct/crime, casualty/death claims, conflict claims, and similarly consequential assertions retain enhanced claim-risk handling. The early-signal doctrine does not authorize unsupported allegations or remove existing corroboration where material harm risk justifies it. Prefer narrower reporting-of-reporting language over false certainty.

## 7. Capital Chronicle analysis and editorial edge

Public prose preserves distinct layers:

- `OBSERVED_FACT`
- `ATTRIBUTED_REPORT_OR_INTERPRETATION`
- `CAPITAL_CHRONICLE_ANALYSIS`
- `SCENARIO_OR_UNCERTAINTY`

Capital Chronicle analysis may be strong, critical, skeptical, or contrarian when its factual premises are supported. For unconfirmed developments, the analysis must explicitly condition mechanisms and consequences on the report being accurate.

Blandness is a product failure. Fabricated outrage is also a product failure.

The newsroom should answer, where the evidence permits:

- what is being reported now;
- who is reporting it and on what basis;
- what is confirmed versus still unknown;
- why the market should care before official confirmation;
- what mechanism or second-order effect matters;
- who wins/loses or what constraint shifts if the report is accurate;
- what would confirm, deny, or materially change the interpretation;
- what Capital Chronicle thinks the market may be missing.

Engagement may improve angle, packaging, timing, and distribution. It may never change factual truth, epistemic state, source attribution, permissions, or CC numeric authority.

## 8. Current V1 routine execution architecture

Current routine V1 is `SIMPLE_GEMINI_RUNTIME`, not Desktop Automations.

Canonical zero-write flow:

```text
current headline sidecars + canonical reconciled published memory + optional read-only CC context
-> published-memory dedupe
-> deterministic sourceability/provenance-aware ordering of the full eligible universe
-> <=32 candidates
-> one vx/gemini-3.5-flash(high) selector
-> one primary + <=2 useful ordered fallbacks
-> classify candidate report/event epistemic state
-> shared <=6 deterministic GET/report-provenance budget across the fixed plan
-> prove the narrowest publishable proposition, preferring report provenance over unnecessary official-confirmation hunting for explicitly attributed reputable reports
-> one vx/gemini-3.5-flash(high) writer for the first eligible candidate
-> deterministic claim + source + epistemic-label validation
-> at most one vx/gemini-3.5-flash(high) revision without source expansion
-> one qualified zero-write article
-> exactly eight UNDISPATCHED derivative intents/previews preserving epistemic state
-> separate DurablePublicationCoordinator only after explicit public-write authority
```

Locked ceilings per Simple article opportunity:

- candidate packet <=32;
- one selector;
- <=3 admitted candidates;
- <=6 deterministic source/provenance GETs total;
- one writer maximum;
- one revision maximum;
- <=3 logical Flash calls total;
- Codex runtime model calls = 0;
- public/provider/coordinator writes = 0 in zero-write proof;
- `UNKNOWN_WRITE = 0`.

No second selection, frontier reopening, broad evidence-ready pool, routine Codex URL discovery, or official-confirmation hunt may be added merely to make a report look more certain.

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

`BREAKING_BRIEF` is the natural home for a narrow credible unconfirmed report when analytical depth is not yet supported. `STANDARD_NEWS_ANALYSIS`, `CAPITAL_CHRONICLE_VIEW`, and `WHAT_THE_MARKET_IS_MISSING` may analyze an unconfirmed report only with explicit conditionality and without laundering uncertainty into fact.

Quiet day is not silent-day permission. Lower materiality or mode before giving up; never lower truth or attribution standards.

## 10. Output contract

During zero-write build/proof, the throughput benchmark remains:

`4 QUALIFIED ZERO-PUBLIC-WRITE ARTICLES / 32 DERIVATIVE INTENTS per newsroom production day`

It is telemetry and a daily-output health metric, not a prerequisite for advancing one safe article.

Final V1 operating target after public-write authority remains **5–8 PUBLISHED ARTICLES** per newsroom production day, with every counted article useful and non-filler.

Candidate-level abstention is valid. Whole-day silent success below the active floor is not. Without an exact hard external blocker, a below-floor day is `DEGRADED_DAILY_OUTPUT_DEFICIT`.

Do not manufacture filler, but do not call a credible attributed report ineligible merely because the subject has not yet confirmed it.

Routine windows remain 17:00, 21:00, 23:00, and following 01:00 Asia/Bangkok under one deterministic newsroom production day. No fifth routine task merely to chase quota.

## 11. Publication and update lifecycle

Substack is canonical. The eight V1 derivative destinations remain Telegram, Discord, X, LinkedIn, Facebook Page, Instagram Business, Threads, and YouTube Community.

Publication lifecycle:

`qualified article -> canonical Substack publish/readback -> eight derivative attempts -> destination-local recovery -> strict reconciliation`

`UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`

Epistemic lifecycle is separate from publication lifecycle:

`UNCONFIRMED/RELAYED -> CONFIRMED | PARTIALLY_CONFIRMED | DISPUTED_OR_DENIED | SUPERSEDED`

A confirmation/denial update should preserve linkage to the original story/update chain and make the state change visible. Never silently rewrite history so an earlier unconfirmed report appears to have been confirmed at publication time.

## 12. Completed foundation and current acceptance route

Accepted/reusable foundations include:

- current intake, published memory/dedupe, production-day accounting, bounded deficit recovery;
- current Simple Gemini selection/writer/revision and lightweight four-window scheduler;
- sourceability-aware full-universe preselection and exact-route health reuse;
- PR #19 retrieval/discovery donors under current Simple economics only;
- PR #20 canonical article/package proof;
- PR #29 validate-after/material-claim concepts;
- claim-scoped reputable-secondary attribution semantics;
- Institutional Edge fact/analysis separation and eight-mode editorial behavior;
- native exactly-eight derivative packaging;
- canonical Substack transports, readback/reconciliation, and completed Italy nine-surface canary;
- V5 read model/UI foundation.

The Simple report-truth/event-truth epistemic adapter, attributed-publisher direct/RSS pinning,
and native preview quality correction are accepted implementation in PR #37. The article/eight-
preview runtime proof is closed by the current Al Jazeera owner-review package.

The owner has now authorized one further narrow activation: an exact record from the owner-curated
canonical X-list intake may support only a relay-of-reporting proposition (`Relay R, citing
Publisher P, reports X`) or an explicitly marked market-rumor proposition. It remains
`UNCONFIRMED`, never proves the cited publisher's original report or X itself, and cannot bypass
high-harm enhanced evidence. Arbitrary social rows remain discovery-only. This activation is
zero-GET eligible after deterministic provenance validation. The next distinct gate is separate
routine public-write/readback authority.

Current sequence:

1. preserve the accepted PR #37 early-attributed-intelligence / epistemic-state Growth Edge slice and its current article plus eight zero-write previews;
2. obtain separate routine public-write/readback authority and wire the accepted Simple article to the existing publication coordinator without rebuilding transports;
3. prove a real production day at 5–8 useful published articles without filler;
4. obtain explicit `V1_FINAL_PRODUCT_ACCEPTED`;
5. only then proceed to isolated V2 continuation.

## 13. Canonical UI

`ui/contentops_v5/` should eventually expose epistemic truth that matters operationally and to publication review, including confirmed/unconfirmed/relayed/disputed state where available, alongside runtime/output deficit/evidence/publication/UNKNOWN/cost truth.

Do not create a separate V1 UI stack for this feature. UI work is not part of the current PR #37 editorial-path closure unless required by a later exact task.

## 14. Hard boundaries

Never:

- fabricate a report, source, leak, rumor, quote, number, or event;
- present `UNCONFIRMED`, `RELAYED`, or `RUMOR` as confirmed fact;
- claim Publisher X reported Y when only an untrusted third party says so;
- infer `LEAK`, `internal source`, or `RUMOR` without source support;
- let an unrelated same-entity official document validate a different story;
- publish unsupported high-harm allegations;
- promote external reporting into Capital Chronicle proprietary probability/forecast/scenario/regime/valuation/decision authority;
- expose secrets/session material;
- widen public-write permission by implication;
- destructively mutate production state;
- blind-retry an ambiguous write.

Protected historical `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.

## PR #37 current-host closeout (2026-08-28)

The single permitted current opportunity closed the article and preview gate: one exact Al Jazeera
report qualified as `DIRECT_REPUTABLE_REPORT / UNCONFIRMED / UNSPECIFIED / SINGLE_SOURCE`,
deterministic validation passed, and exactly eight preview-only undispatched packages preserved the
epistemic state. The selected story used direct reporting; relay-only and rumor-only current-host
qualification therefore remains unobserved rather than inferred. Separate public-write/readback
authority remains ungranted.
