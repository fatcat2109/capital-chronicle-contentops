# Capital Chronicle ContentOps — Final Product North Star V3

Authority date: 2026-09-01
Status: `CURRENT_ROOT_PRODUCT_NORTH_STAR / EARLY_ATTRIBUTED_INTELLIGENCE / V1_ACCEPTED`

This document records the current product direction. It supersedes conflicting current-looking wording that requires universal official confirmation, routes routine V1 through Desktop Automations, says routine V1 public-write/readback remains ungranted, or says `V1_FINAL_PRODUCT_ACCEPTED` is still pending.

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

Current routine V1 is `SIMPLE_GEMINI_RUNTIME`, not Desktop Automations.

Accepted editorial flow:

```text
current sidecars + canonical reconciled published memory
-> deterministic dedupe/sourceability ordering
-> <=32 candidates
-> one vx/gemini-3.5-flash(high) selector
-> one primary + <=2 useful fallbacks
-> classify report/event epistemic state
-> shared <=6 deterministic source/provenance GETs
-> prove the narrowest publishable proposition
-> one vx/gemini-3.5-flash(high) writer
-> deterministic claim/source/epistemic validation
-> at most one Flash revision without source expansion
-> one qualified article
-> exactly eight native derivative packages preserving epistemic state
```

Locked ceilings: <=32 candidates, one selector, <=3 admissions, <=6 GETs, one writer, <=1 revision, <=3 logical Flash calls, zero Codex runtime model calls.

Do not revive broad ready pools, routine Codex URL discovery, Desktop PREPARE/COMPLETE, SDK editorial fallback, or official-confirmation hunts merely to increase apparent certainty.

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

Accepted publication lifecycle:

`qualified article -> canonical Substack publish/readback -> exactly eight derivative attempts -> destination-local recovery -> strict reconciliation`

A counted published article requires exact canonical identity/readback. Derivatives use the real reconciled canonical `/p/...` URL, never a pending placeholder.

`UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`

Epistemic lifecycle remains separate:

`UNCONFIRMED/RELAYED -> CONFIRMED | PARTIALLY_CONFIRMED | DISPUTED_OR_DENIED | SUPERSEDED`

## 12. Accepted foundation and current activation route

Accepted/reusable foundation includes current intake, published memory/dedupe, production-day accounting foundation, Simple Gemini selection/writer/revision, PR #37 early-attributed intelligence and epistemic state, sourceability ordering, native exactly-eight compiler, canonical Substack transports, durable publication coordinator, strict readback/reconciliation, completed Italy nine-surface canary, V5 read model/UI, merged PR #38 emergency-stop/static-safety closure, merged PR #39 single-owner production composition, and corrected PR #42 actual persistent Simple-scheduler publication handoff.

The corrected routine handoff preserves this North Star rather than adding a new editorial gate: Simple semantic work remains zero-write; a qualified slot maps deterministically to the canonical durable work item; the publication plan is persisted/reconstructed from already-qualified artifacts; coordinator recovery runs before fresh work; interrupted qualified slots resume without another model/source call; unresolved backlog or ambiguous write stays in coordinator/readback recovery rather than blind retry; canonical Substack `/p/...` reconciliation still precedes exactly-eight derivative rematerialization. This is repository/CI proof, not fresh host/account/readiness or live-publication proof.

Current progression is `PRODUCT_FIRST_AUTONOMOUS_V1_RESUME`, not a new activation or acceptance
campaign:

1. merge/deploy/load corrected current bytes;
2. run the already-activated four natural routine windows;
3. observe real conversion, publication, readback, and reconciliation failures;
4. fix measured blockers toward 5–8 useful published articles/day.

A fresh standalone host preflight or one-off canary is conditional diagnostics only when current
evidence materially raises an exact identity/readiness/UNKNOWN/irreversible-risk boundary. The
existing owner still fails closed on those invariants at every actual live write.

Single-owner composition, Simple emergency-stop/process coverage, and the routine Simple publication handoff are already closed. Do not rebuild transports, publication coordinator, store, native packager, Simple editorial path, or historical Italy publication proof.

## 13. Hard boundaries

Never fabricate a report/source/leak/rumor/quote/number/event; present unconfirmed material as confirmed; infer leak/rumor without source support; publish unsupported high-harm allegations; promote external reporting into proprietary CC numeric authority; expose secrets/session material; destructively mutate production state; or blind-retry an ambiguous write.

Chrome `CapitalChronicleBot` CDP 9222 remains ingestion-only. Edge `contentops-social-main` CDP 9223 remains publication/media/readback/authorized-observation only.

Protected historical `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.
