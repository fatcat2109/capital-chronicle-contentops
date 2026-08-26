# Capital Chronicle ContentOps — Final Product North Star V3

Authority date: 2026-08-24
Status: `CURRENT_ROOT_PRODUCT_NORTH_STAR`

## 1. Product role

Capital Chronicle/Core Analyzer is the intelligence and decision-product authority. ContentOps is the evidence-governed newsroom, media-production, organic audience-acquisition, distribution, observation, and bounded-learning engine.

Canonical product flow:

`Core Analyzer intelligence -> explicit publication-safe handoff + public evidence -> ContentOps newsroom -> V1 publishing + V2 media -> observation -> bounded learning -> audience/business utility`

Truth, permissions, rights, exact identity, numeric authority, and recovery are hard boundaries. Growth and output volume may never weaken them.

## 2. Owner output contract and locked evidence state

Jim's latest explicit owner direction is authoritative.

### Nine-surface canary — complete

The owner-scoped Italy canary already published one canonical Substack article plus exactly eight
derivative packages. All nine public objects were read back and reconciled with `UNKNOWN_WRITE=0`.
This is completed technical evidence and must not be routed again merely to prove publication.
Any still-desired owner aesthetic/business review is evidence review only and authorizes no second
write.

### Throughput benchmark

During the current V1 build/proof phase, one newsroom production day must produce at least:

`4 QUALIFIED ZERO-PUBLIC-WRITE ARTICLES / 32 DERIVATIVE INTENTS`

A qualified throughput article must clear the normal production validation contract and persist its
native package intents. The first real four-opportunity proof already ran and truthfully failed at
`0 qualified articles / 0 derivative intents` after 40 distinct stories. A future rerun remains a
throughput/economics KPI and daily-output diagnostic; it is not a prerequisite for proving or
advancing one safe qualified article through the canonical path.

### Final V1 target

After public-write authority is granted and final V1 is accepted, the operating target is:

`5–8 PUBLISHED ARTICLES PER NEWSROOM PRODUCTION DAY`

This is an output requirement, not permission to create filler or unsupported claims.

### Fast-ship single-article path

One ordinary `BREAKING_BRIEF` and exactly eight undispatched derivative intents now pass the
canonical zero-write path. Hard blockers are empty and public/provider/unknown writes are zero.
PR #20 is independently owner-audited and accepted. Reuse this canonical path; do not route another
article proof merely to re-establish it.

### Abstention semantics

Candidate-level abstention is valid. Whole-day silent success is not.

`NO_PUBLICATION` may terminate a specific candidate or bounded attempt. If the production day remains below the active daily floor/target, the system must continue the useful editorial search/catch-up process at later eligible opportunities until the floor is met or an exact hard external blocker is established.

A production day ending below the build floor without a proven hard external blocker is:

`DEGRADED_DAILY_OUTPUT_DEFICIT`

It must never be reported as healthy success merely because individual candidate abstentions were governed.

Every routine opportunity below the final minimum of five is an editorial opportunity, not a quota
checkpoint exit. It must walk the governed candidate universe unless that universe is genuinely
exhausted or an exact hard external blocker exists. Catch-up capacity must keep five reachable
through later routine windows; routine-opportunity accounting remains a separate 0..4 counter.

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

This cross-midnight accounting, the 4-floor counters, and bounded deficit recovery are accepted
current foundation. Reuse them; do not rebuild them.

## 4. Execution architecture — FDA-G and Codex are distinct

FDA-G is the always-on low-cost runtime/intake/state authority. It can ingest, maintain durable state, evaluate cheap opportunity metadata, reconcile, and expose current truth.

Desktop standalone fresh-run Automations are the primary routine heavy-editorial brain. Each
routine opportunity uses a fresh `gpt-5.6-sol / HIGH` coordinator, which starts one fresh isolated
`gpt-5.6-sol / HIGH` final writer only at a warranted article boundary and permits at most one
bounded same-worker HIGH repair from concrete deterministic validation deltas.

Editorial ordering is `LLM-FIRST / VALIDATE-AFTER`: current headlines, published memory, and
optional read-only CC context reach the editorial brain before evidence-ready/sourceability/
capability perfection can veto ordinary writing. The worker returns explicit citations and
material-claim bindings; deterministic retrieval verifies the cited bytes after generation.

Therefore:

- deterministic validators remain factual, numeric, permission, gate, and publication authority;
- neither Desktop coordinator nor HIGH worker has public-write authority;
- the official ChatGPT-authenticated Codex App Server/SDK provider remains the proven resilient
  missed/failed-primary fallback, immediate direct path, and benchmark path;
- accepted Desktop and SDK receipts share one canonical run identity and may not produce duplicate
  articles or public objects.

The current heavy-editorial architecture is:

`FDA-G / existing V1 runtime -> fresh standalone Desktop HIGH coordinator -> fresh isolated HIGH writer when warranted -> deterministic validate-after -> zero-write or separately authorized publication lifecycle`

No second newsroom/store/publisher/control plane.

## 5. Routine schedule policy

The four routine opportunities are:

- London 17:00 Monday–Friday;
- New York 21:00 Monday–Friday;
- New York 23:00 Monday–Friday;
- New York 01:00 Tuesday–Saturday;
- timezone: Asia/Bangkok;
- coordinator: `gpt-5.6-sol / HIGH`;
- final editorial worker: one fresh isolated `gpt-5.6-sol / HIGH`; no current ContentOps request may exceed `CONTENTOPS_CODEX_MAX_REASONING_EFFORT = HIGH`.

Do not create a fifth routine opportunity merely to satisfy the daily floor. Catch-up belongs inside the existing production-day logic and bounded candidate walk.

Current host truth proves exactly these four existing native Automations, all paused on
`gpt-5.6-sol / HIGH`. All four prompt hashes now match the same repo-derived FAST-SHIP routine
prompt. It does not authorize enablement. Zero-write Automation enablement/calendar-time proof and
routine public-write authority remain distinct decisions. Calendar-time unattended execution
remains unproven.

## 6. Material-event wake truth

FDA-G may detect and prioritize material events for the existing runtime. This grants no extra model
turn, bypasses no gate, and supplies no public-write authority.

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

Editorial eligibility and destination readiness are separate axes. In zero-write/SHADOW_ONLY, a
readiness HOLD cannot veto canonical article generation, validation, or eight undispatched
derivative intents. At public-write time, Substack readiness gates its dispatch and derivative
readiness is destination-local; neither can erase a valid canonical article.

A derivative-local outage does not erase canonical truth. The completed Italy canary supplies the
required nine-surface technical proof for its exact owner-scoped obligation; it grants no routine
public-write expansion.

## 11. Current acceptance route

Accepted sequence facts:

- the growth-first newsroom/evidence/publication foundation is current;
- the real Italy nine-surface canary is complete and reconciled;
- the first 4/32 proof ran and failed truthfully at `0/4 / 0/32`;
- production-day accounting and bounded deficit recovery are accepted;
- PR #19 provider-resilient batch/tail discovery is accepted and reusable after producing four
  governed ready candidates in three batch turns with 712,842 accounted tokens;
- PR #20's canonical worker-return normalization and ordinary zero-write article path are accepted;
- the four existing paused host prompts are normalized and read back to one repo-derived hash.

Current progression order:

1. preserve the accepted PR #19 discovery and PR #20 article path;
2. preserve the completed four-prompt normalization/readback with all objects paused;
3. obtain exact zero-write Automation enablement authority and calendar-time unattended proof;
4. complete fresh current-epoch V5 acceptance and separate routine public-write/final-product
   authority decisions;
5. only after explicit V1 acceptance begin authorized V2 continuation.

## 12. Canonical UI

`ui/contentops_v5/` must expose truthful runtime, evidence, authority, publication/recovery, cost, and daily production state. During build it must show qualified articles versus the `4` floor and remaining deficit. It must not present an unmet daily floor as a generic healthy idle state.

The V5 read-model and production-day mechanics are accepted foundation. Final closure requires a
fresh current-source/runtime-epoch desktop/mobile rendered audit, not a mechanical rebuild.

Provider/runtime state displayed in the UI must come from an actual safe observable source.
Configured schedule policy must never be rendered as current Desktop Automation state.

## 13. Hard stops

Never expose secrets/session material; fabricate facts or Core Analyzer truth; widen publication permission; write to the wrong public account; destructively mutate production state; blind-retry ambiguous writes; or invent automation/task existence.

Protected historical `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.
