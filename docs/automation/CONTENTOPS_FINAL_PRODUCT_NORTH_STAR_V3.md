# Capital Chronicle ContentOps — Final Product North Star V3

Authority date: 2026-08-21
Status: `CURRENT_ROOT_PRODUCT_NORTH_STAR`

## 1. Product role

Capital Chronicle/Core Analyzer is the intelligence and decision-product authority. ContentOps is the evidence-governed newsroom, media-production, organic audience-acquisition, distribution, observation, and bounded-learning engine.

Canonical product flow:

`Core Analyzer intelligence -> explicit publication-safe handoff + public evidence -> ContentOps newsroom -> V1 publishing + V2 media -> observation -> bounded learning -> audience/business utility`

Truth, permissions, rights, exact identity, numeric authority, and recovery are hard boundaries. Growth and output volume may never weaken them.

## 2. Owner output contract — current highest-priority V1 rule

Jim's latest explicit owner direction is authoritative.

### Build-phase floor

During the current V1 build/proof phase, one newsroom production day must produce at least:

`4 QUALIFIED ZERO-PUBLIC-WRITE ARTICLES`

A qualified build article must clear the current factual, evidence, numeric, rights, reader-value, authority, and editorial-worker contracts and persist its native package intents. It is not required to be publicly dispatched during build/proof.

### Final V1 target

After public-write authority is granted and final V1 is accepted, the operating target is:

`5–8 PUBLISHED ARTICLES PER NEWSROOM PRODUCTION DAY`

This is an output requirement, not permission to create filler or unsupported claims.

### Abstention semantics

Candidate-level abstention is valid. Whole-day silent success is not.

`NO_PUBLICATION` may terminate a specific candidate or bounded attempt. If the production day remains below the active daily floor/target, the system must continue the useful editorial search/catch-up process at later eligible opportunities until the floor is met or an exact hard external blocker is established.

A production day ending below the build floor without a proven hard external blocker is:

`DEGRADED_DAILY_OUTPUT_DEFICIT`

It must never be reported as healthy success merely because individual candidate abstentions were governed.

Examples of acceptable hard external blockers include source-universe unavailability, provider-wide failure after bounded fallback, required credential/reauth unavailability, runtime unavailability, or evidence authority that is genuinely impossible across the full useful editorial ladder. Truth/evidence gates must never be weakened to avoid a deficit.

## 3. Newsroom production-day semantics

The routine intended windows are 17:00, 21:00, 23:00, and 01:00 Bangkok time. Because the final window crosses local midnight, production accounting must use one deterministic `newsroom_production_day_id` rather than a naive Bangkok calendar date.

The production-day contract must expose at minimum:

- build floor = 4 qualified articles;
- final target = 5–8 published articles;
- qualified count;
- published count;
- remaining deficit;
- production-day state;
- exact hard-block reason when applicable.

Later windows must be able to recover an earlier deficit. Do not create filler merely to make the counter move.

## 4. Execution architecture — FDA-G and Codex are distinct

FDA-G is the always-on low-cost runtime/intake/state authority. It can ingest, maintain durable state, evaluate cheap opportunity metadata, reconcile, and expose current truth.

Current repository code does **not** prove that FDA-G directly launches Codex Desktop. `live_contentops/codex_desktop_newsroom_operator_v1.py` is continuity/routing support and is explicitly not a scheduler or Desktop/model bridge.

Therefore:

- repo configuration describing Codex tasks is not proof that host Codex Automations exist;
- actual Codex Automation inventory/state must be proven from supported host/product evidence;
- do not claim four native Codex tasks are present, paused, enabled, or unattended unless host evidence proves it;
- intended automation configuration and observed automation objects are separate facts.

The preferred routine heavy-editorial architecture is:

`FDA-G background intake/state -> native Codex Automation wake -> HIGH coordinator -> fresh isolated XHIGH editorial worker when warranted -> deterministic validation -> zero-write or authorized publication lifecycle`

No second newsroom/store/publisher/control plane.

## 5. Routine automation intent

The intended four routine Codex opportunities are:

- London 17:00 Monday–Friday;
- New York 21:00 Monday–Friday;
- New York 23:00 Monday–Friday;
- New York 01:00 Tuesday–Saturday;
- timezone: Asia/Bangkok;
- coordinator: `gpt-5.6-sol / HIGH`;
- final editorial worker: one fresh isolated `gpt-5.6-sol / XHIGH` only after a real candidate reaches the article boundary.

Do not create a fifth routine opportunity merely to satisfy the daily floor. Catch-up belongs inside the existing production-day logic and bounded candidate walk.

Until host inventory proves these Automations exist, their status is `UNPROVEN_HOST_AUTOMATION_STATE`.

## 6. Material-event wake truth

FDA-G may detect/prioritize material events. That does not itself prove an immediate native Codex editorial wake.

Until an actual supported execution bridge is proven, classify immediate material-event-to-Codex execution as:

`MATERIAL_EVENT_CODEX_WAKE_NOT_PROVEN`

Do not invent a credential/token bridge as a side effect of this contract. Any separate access-token/API execution bridge is a new execution/security boundary and requires explicit owner approval.

## 7. Editorial spectrum

V1 supports:

1. `BREAKING_BRIEF`
2. `FOLLOW_UP_UPDATE`
3. `STANDARD_NEWS_ANALYSIS`
4. `CAPITAL_CHRONICLE_VIEW`
5. `WHAT_THE_MARKET_IS_MISSING`
6. `EVERGREEN_EXPLAINER`
7. `DATA_OR_DOCUMENT_LENS`
8. `WEEK_AHEAD_OR_WATCH`

Quiet days lower materiality or change mode, not truth standards. The system must exhaust useful lower-rung modes before treating the candidate universe as genuinely unable to contribute toward the daily floor.

## 8. Evidence and analytical authority

Evidence burden follows claim ambition and mode.

One exact current authentic official primary source may support a narrow attributed breaking fact when it directly proves the event. It does not automatically prove disputed allegations, causality, market reaction, future outcomes, valuations, forecasts, scenarios, probabilities, regimes, or proprietary numeric conclusions.

Core Analyzer owns proprietary analytical/numeric truth. ContentOps may publish such material only through exact story-scoped publication-authorized handoff. Context/discovery and internally governed Analyzer material are not public permission.

ContentOps may make clearly labeled qualitative editorial inference from accepted public evidence. It must not represent that as Core Analyzer output.

## 9. Growth objective

V1 is Capital Chronicle's organic growth newsroom. It should produce useful, timely, distinctive content and optimize supported packaging/timing/SEO/distribution for qualified reach, meaningful reads, shares, follows, subscriptions, canonical clicks, repeat readership, and product conversion.

No fake engagement, purchased followers, spam, mass unsolicited DMs, fabricated outrage, or unsupported allegations.

## 10. Distribution and public-object lifecycle

Substack remains canonical. V1 uses exactly eight derivative destinations: Telegram, Discord, X, LinkedIn, Facebook Page, Instagram Business, Threads, and YouTube Community.

Canonical lifecycle:

`qualified article -> exact Substack identity/readiness -> canonical publish/readback -> eight derivative package attempts -> destination-local recovery -> strict reconciliation`

`UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`

A derivative-local outage does not erase canonical truth, but final nine-surface canary acceptance still requires exact proof across all required surfaces under the canary contract.

## 11. Current acceptance route

Current sequence:

1. P0-G3 growth-first multi-mode zero-write proof is accepted and merged.
2. Before continuing the live canary, correct current authority and prove the real Codex automation/execution bridge plus build daily-output-floor behavior.
3. Produce a genuine current qualified canary candidate under zero public write.
4. Obtain explicit one-canary owner public-write grant.
5. Publish/read back canonical Substack plus exactly eight derivatives and finish `UNKNOWN_WRITE=0`.
6. Prove unattended/cold-start operation using only actual proven routine Automations; material-event live execution remains separately owner-gated.
7. Close truthful V5 UI and screenshot-based owner QA.
8. Accept/freeze V1 only after these proofs.

## 12. Canonical UI

`ui/contentops_v5/` must expose truthful runtime, evidence, authority, publication/recovery, cost, and daily production state. During build it must show qualified articles versus the `4` floor and remaining deficit. It must not present an unmet daily floor as a generic healthy idle state.

Automation state displayed in the UI must come from an actual safe observable source. Configured intended schedules must never be rendered as observed `READY/PAUSED` host automation truth.

## 13. Hard stops

Never expose secrets/session material; fabricate facts or Core Analyzer truth; widen publication permission; write to the wrong public account; destructively mutate production state; blind-retry ambiguous writes; or invent automation/task existence.

Protected historical `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.
