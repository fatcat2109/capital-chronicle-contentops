# Capital Chronicle ContentOps — Current V6/Post-v1 Master Plan

Authority date: 2026-08-06

Repository: `fatcat2109/capital-chronicle-contentops`

Verified remote master reconciled onto:

`6b6f8718532a4c3f077b09e14f3ca9a4083d4734`

Plan authoring base:

`c87e338f25922f4d03454ba199139353ca7198ff`

Historical accepted release:

`PASS_CONTENTOPS_V1_0_OPERATOR_ACCEPTED`

Current accepted master classification:

`PASS_WAVE01_CANONICAL_ORCHESTRATOR_BOUNDARY_ACCEPTED_AND_MERGED`

Current product-direction classification:

`CONTENTOPS_NEWSROOM_AND_CONTENT_FACTORY_SCOPE_OWNER_APPROVED`

Current durable prerequisite status:

`COMPLETE_ACCEPTED_AND_MERGED_AS_MINIMUM_DURABLE_PREREQUISITE`

Current next task:

`TASK_CONTENTOPS_EXACT_AUTHORIZED_LIVE_COHORT_V1`

Current next-task mode:

`REQUIRES_EXACT_OWNER_AUTHORIZED_LIVE_SCOPE`

Current work package routing:

- Work Package C — dual-lane CORE V0 shadow newsroom: `COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`
- Work Package D — diversity, SEO, image, and chart closure: `COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`
- Work Package E — repeated shadow soak and recovery: `COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`, audit `PASS_WITH_CAVEAT_ACCEPTED_FOR_MASTER_MERGE`, launch readiness `READY_WITH_EXPLICIT_CAVEATS`
- Work Package F — exact authorized live cohort: `READY_REQUIRES_EXACT_OWNER_LIVE_SCOPE`

Work Package D passed independent audit and is merged. Work Package E passed independent
audit `PASS_WITH_CAVEAT_ACCEPTED_FOR_MASTER_MERGE` and is fast-forward merged into `master` at accepted source HEAD `3770ff1c2fe77129c634af3263cbc4e31085b900`; it
is an accelerated logical soak, so calendar uptime and live reliability are still not
claimed by it. The live cohort must not start without an exact owner-authorized live scope.

Final pre-launch LLM model authority `CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2`
(superseding V1, which prohibited all fallback and is retained only as historical lineage)
binds gateway `9router` and the exact ordered model pool for every applicable LLM task in
Work Packages F and G: P0 `new/claude-fable-5`, P1 `new/gpt-5.6-sol-xhigh`, P2
`new/claude-opus-5`, P3 `vx/gemini-3.1-pro-preview(high)`. Ordered fallback is
owner-authorized for bounded resilience and is not a quality-gate bypass; per attempt,
`requested_model == provider-observed resolved model` is still required and silent
provider-side substitution remains forbidden. Every logical invocation carries an immutable
bounded retry budget — 6 total provider attempts, 3 fallback transitions, 1 same-model
retry, per-model ceilings (2, 2, 1, 1), 1 structured-output repair against the total, 45 s
cumulative retry sleep, 300 s wall clock — that no model change or process reconstruction
resets. Runtime verification is `PROVIDER_VERIFIED`: the latest bounded no-write preflight
probed all four authorized models at 4/4 `HEALTHY`, 0 unavailable, 0 identity mismatch, 0
identity unverifiable, disposition `MODEL_IDENTITY_PROVIDER_VERIFIED` (Gemini correction
commit `a3d42dab03ac4ceb09a4106d46e37d65e08cad77`). For P3 the authorized pool identity
stays the opaque string `vx/gemini-3.1-pro-preview(high)` while the request is sent as wire
model `vx/gemini-3.1-pro-preview` plus reasoning effort `high` and the provider reports
`gemini-3.1-pro-preview` — an authorized request transformation, not substitution. This
authority grants no public live cohort authority.

## 1. Current authority

Read in this order:

1. `AGENTS.md`
2. `docs/CURRENT_CONTEXT.md`
3. `docs/AI_BUILDER_BOOTSTRAP.md`
4. `docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md`
5. `docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/FINAL_PRODUCT_SCOPE_OVERLAY_V2.md`
6. `docs/automation/CONTENTOPS_FINAL_PRODUCT_SCOPE_CLOSEOUT_AND_LAUNCH_MASTER_PLAN_V1.md`
7. current committed status, maturity, and exact task-specific files.

The institutional packet and older V6 plans remain evidence and design references. Where they conflict with the current product ownership, operating modes, content-diversification requirement, or build sequencing, the current overlays and final closeout plan govern.

## 2. Protected historical release

ContentOps `v1.0` remains immutable historical authority:

- release commit `6983bfb3ef300414b744f3f8f97ca81ff699348b`;
- one exact story-scoped Treasury release;
- canonical Substack plus eight Tier-1 text/image derivatives;
- strict readback and bounded repair;
- machine verification and operator acceptance.

Do not rerun, edit, delete, recreate, move, or retag accepted outputs or evidence.

The release proves one bounded production cycle. It does not prove a continuously operating, diversified, restart-safe newsroom.

## 3. Correct product boundary

### Capital Chronicle main project owns intelligence

Capital Chronicle owns:

- daily economic and market analysis;
- microeconomic, macroeconomic, and global-macro reports;
- scenarios and probabilistic views;
- model calculations;
- Bayesian cases and updates;
- forecasts and market-regime authority;
- numeric truth;
- realized-outcome comparison and analytical error attribution.

### ContentOps owns the newsroom and content factory

ContentOps owns:

- headlines, breaking news, and business-news intake;
- event clustering, duplicates, corrections, and update chains;
- evidence/permission/freshness/material-delta gates;
- editorial ranking, story selection, hold, reject, and no-publication decisions;
- content diversity and portfolio concentration control;
- article mode, framing, writing, editing, SEO, images, and charts;
- native platform packages;
- publication control, readback, reconciliation, incidents, and content-performance learning;
- faithful transformation of governed Capital Chronicle analysis packets.

ContentOps must not independently originate authoritative economic scenarios, model outputs, Bayesian probabilities, forecasts, market regimes, or numeric truth.

## 4. Final product

Capital Chronicle ContentOps is an AI-native autonomous newsroom and content factory with two input lanes.

### Newsroom lane

```text
fresh governed headlines and primary-source events
→ normalize, cluster, and identify update chains
→ verify evidence, permission, freshness, and material delta
→ rank editorial value and portfolio fit
→ select, hold, reject, or publish nothing
→ report, edit, optimize, visualize, package, publish, read back, and learn
```

### Capital Chronicle analysis lane

```text
governed Capital Chronicle analysis packet
→ verify exact lineage, claims, permissions, calculations, scenarios, and limitations
→ choose content mode, audience, framing, and search intent
→ produce article, report, image/chart, newsletter, and platform-native packages
→ review analytical fidelity
→ publish, read back, reconcile, and measure content performance
```

## 5. Content diversification

The final product must support a diversified universe, including:

- U.S. equities and Big Tech;
- sector and industry trends;
- earnings and filings;
- economic releases;
- political and policy news;
- central banks, rates, credit, and liquidity;
- FX, commodities, energy, and materials;
- geopolitics, trade, sanctions, and supply chains;
- regulation, law, and corporate governance;
- global corporate events;
- Capital Chronicle daily, microeconomic, macroeconomic, global-macro, scenario, model, and Bayesian analysis products.

Diversification is enforced through ranking and rolling concentration penalties, not mandatory filler quotas. `NO_PUBLICATION` is valid.

## 6. SEO, image, and chart requirements

SEO is a production system, not a self-awarded score. Each canonical long-form package must bind search intent, target reader, keyword/query cluster, headline, slug, meta description, structure, citations, internal-link suggestions, visual metadata, canonical URL, and measurement hooks.

Images must be useful, rights/provenance bound, story appropriate, and platform adapted. Image search is discovery only and never grants reuse rights or factual authority.

Charts must be deterministic and reproducible from Capital Chronicle packet data or approved official/public data. Every chart records source, metric, unit, timestamps, frequency, sample, transformations, revision/partial-period state, method, and final hash. ContentOps may visualize authorized calculations; it may not create analytical truth.

## 7. Operating modes

- `AUTONOMOUS_DEFAULT`: default; public writes only when exact deterministic gates pass.
- `SUPERVISED_OPERATOR_GATE`: optional owner toggle before public write.
- `SHADOW_ONLY`: full product cycle with zero public writes.
- `KILL_SWITCH`: blocks new public writes while preserving readback, reconciliation, and recovery.

Older universal mandatory-approval language is superseded. Historical supervised evidence remains valid.

## 8. Current maturity

### Proven

- exact evidence and permission handling;
- one canonical production-orchestrator boundary;
- durable operational store and canonical state machine (Wave 02, merged and accepted);
- bounded Substack-first publication and Tier-1 derivatives;
- visual generation and platform packaging;
- strict readback and bounded repair;
- fail-closed ineligible-story behavior;
- editorial, freshness, and evidence foundations;
- canonical V5 review UI.

### Candidate or partial

- candidate ranking and decision windows;
- cross-domain shadow-newsroom artifacts;
- editorial revision and SEO hygiene;
- content-performance and learning foundations.

### Not yet proven

- repeated fresh diversified headline intake;
- reliable duplicate/update-chain clustering in routine operation;
- breaking-news and business-news desk performance;
- faithful repeated Capital Chronicle analysis transformations;
- full SEO/image/chart closure across diverse stories;
- restart-safe repeated shadow operation;
- a bounded autonomous live cohort;
- rolling performance learning and final launch SLOs.

## 9. Build doctrine

Use FAST SHIP + CORE V0.

Prefer one heavy bounded end-to-end capability over horizontal infrastructure. Reuse accepted components. Add or harden durable state, approval, outbox, scheduler, provider, adapter, or UI components only when they directly block the final product loop.

Support docs, tests, and evidence should remain proportionate and directly support user-visible capability.

## 10. Final closeout sequence

The detailed requirements and launch gates are in:

`docs/automation/CONTENTOPS_FINAL_PRODUCT_SCOPE_CLOSEOUT_AND_LAUNCH_MASTER_PLAN_V1.md`

Completed:

1. product-authority reconciliation — `COMPLETE_OWNER_APPROVED`;
2. minimum durable prerequisite — `COMPLETE_ACCEPTED_AND_MERGED_AS_MINIMUM_DURABLE_PREREQUISITE`.

Remaining sequence:

```text
dual-lane CORE V0 in SHADOW_ONLY   [COMPLETE — ACCEPTED AND MERGED WITH CAVEAT]
→ diversity, SEO, image, and chart closure   [COMPLETE — ACCEPTED AND MERGED WITH CAVEAT]
→ repeated shadow soak and recovery   [COMPLETE — ACCEPTED AND MERGED WITH CAVEAT]
→ exact authorized live cohort   [CURRENT — REQUIRES EXACT OWNER LIVE SCOPE]
→ final acceptance and new release identity
```

This is current build authority. The older horizontal Wave 03–15 hardening roadmap remains valid historical planning and is revisited only where an item directly blocks this sequence or a launch gate.

## 11. Canonical product surfaces

- backend: `live_contentops/`;
- canonical production migration anchor: `live_contentops.eight_platform_substack_first_pipeline_v1`;
- canonical durable operational store: `live_contentops/durable_operational_store_v1.py`;
- canonical UI: `ui/contentops_v5/`;
- strategy/status: current product-direction overlay, final-product scope overlay, this master plan, and exact committed task evidence.

Do not create a second production runner, state store, approval engine, outbox, scheduler, provider gateway, dashboard, numeric-analysis path, or macro-analysis engine.

## 12. Safety invariants

- Never bypass evidence, claim permission, freshness, DQR, or point-in-time authority.
- Never fabricate numeric truth, analytical output, quote, source, image event, or public readback.
- Never persist or print raw credentials, tokens, cookies, browser storage, private keys, or session material.
- Never retry an unknown write blindly.
- Never mutate approved bytes without a new exact authorization record.
- Never modify or retag accepted `v1.0` evidence.
- Never mutate the Capital Chronicle main project from a ContentOps task.
- Never treat engagement as factual authority.

## 13. Current routing

Jim approved this product direction on 2026-08-06. The exact builder task authorized by current authority is:

`TASK_CONTENTOPS_EXACT_AUTHORIZED_LIVE_COHORT_V1`

Status:

`READY_REQUIRES_EXACT_OWNER_LIVE_SCOPE`

Work Packages C, D, and E are each accepted and merged into `master` as
`COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`. Do not reopen, re-audit, retest, or re-merge
them. Work Package E's accepted caveats remain truthful: it is an accelerated logical soak,
so calendar uptime and live reliability are not claimed by it.

Work Package F is the current next product task. It must not start without an exact
owner-authorized live scope defining destinations, accounts, and public-write authority.

Wave 02 is complete and accepted as the minimum durable prerequisite; do not reopen it. The older automatic next action `TASK_CONTENTOPS_EXACT_APPROVAL_ENVELOPE_TRANSACTIONAL_OUTBOX_AND_EXPIRY_V1` is no longer the current next-task authority.

This routing grants no credential, provider, browser/CDP, network-intake, scheduler/outbox execution, dispatch, publication, or public-write authority. Any live cohort requires a separate exact authorization.
