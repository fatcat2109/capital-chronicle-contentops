# Capital Chronicle ContentOps — AI Builder Entry Contract

This is the first file every AI IDE/CLI builder must read before touching the repository.

## 1. Current product truth

The immutable historical release is ContentOps `v1.0`: one exact database-authorized Treasury story published to canonical Substack plus eight Tier-1 text/image derivatives, with strict readback, bounded repair, operator acceptance, and annotated tag `v1.0` at commit `6983bfb3ef300414b744f3f8f97ca81ff699348b`.

That release is bounded proof. It is not evidence that a continuously operating, diversified, restart-safe newsroom is complete.

Current accepted master classification:

`PASS_WAVE01_CANONICAL_ORCHESTRATOR_BOUNDARY_ACCEPTED_AND_MERGED`

Current product-direction classification:

`CONTENTOPS_NEWSROOM_AND_CONTENT_FACTORY_SCOPE_OWNER_APPROVED`

Jim approved the final ContentOps product plan on 2026-08-06. That direction is current authority and does not require re-approval.

Current durable prerequisite status:

`COMPLETE_ACCEPTED_AND_MERGED_AS_MINIMUM_DURABLE_PREREQUISITE`

Wave 02 — the durable operational store and canonical state machine — is complete, merged into `master`, and accepted as the minimum durable prerequisite for the final product. Do not redesign, re-audit, retest, or re-merge it.

Current next task:

`TASK_CONTENTOPS_EXACT_AUTHORIZED_LIVE_COHORT_V1`

Work Packages C, D, and E are `COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`. Work Package E — the repeated shadow soak and
recovery — passed independent audit `PASS_WITH_CAVEAT_ACCEPTED_FOR_MASTER_MERGE` and is fast-forward merged into `master` from
branch `agent/contentops-core-v0-repeated-shadow-soak-and-recovery-v1` at accepted source
HEAD `3770ff1c2fe77129c634af3263cbc4e31085b900`, launch-readiness disposition `READY_WITH_EXPLICIT_CAVEATS`. Do not reopen C,
D, or E.

Current next-task mode:

`REQUIRES_EXACT_OWNER_AUTHORIZED_LIVE_SCOPE`

The live cohort is `READY_REQUIRES_EXACT_OWNER_LIVE_SCOPE`. No shadow task grants
credential, provider, browser/CDP, scheduler, dispatch, publication, or public-write
authority; the live cohort requires an exact owner-authorized live scope before it starts.

## 2. Mandatory read order

1. `AGENTS.md`
2. `docs/CURRENT_CONTEXT.md`
3. `docs/AI_BUILDER_BOOTSTRAP.md`
4. `docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md`
5. `docs/status/CURRENT_FULL_AUTOMATION_FINAL_PRODUCT_STATUS.md`
6. `docs/status/CURRENT_PROJECT_STATUS.md`
7. `docs/status/current_project_status.json`
8. `docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/FINAL_PRODUCT_SCOPE_OVERLAY_V2.md`
9. `docs/automation/CONTENTOPS_FINAL_PRODUCT_SCOPE_CLOSEOUT_AND_LAUNCH_MASTER_PLAN_V1.md`
10. `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md`
11. `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md`
12. Exact task-specific code, tests, schemas, and evidence.

Older institutional and V6 documents remain historical, architectural, and evidence references. Where they conflict with current product ownership, operating modes, content-diversification requirements, or final-build sequencing, the current overlay and closeout plan govern.

## 3. Authority order

### Repo-state authority

1. GitHub remote commit, branch, tag, compare/diff, and exact fetched bytes.
2. Current committed code, tests, schemas, and immutable evidence.
3. Current status, overlays, and master-plan files.
4. Durable operational state and exact redacted run evidence.
5. Provider/platform strict readback.
6. Worker logs and local validation.
7. Project Sources, pasted summaries, chat memory, and archives.

### Product-direction authority

1. Jim's latest explicit instruction and current project instructions.
2. Current committed product-direction overlays and master plan.
3. Older plans and archives.

Do not let stale repo plans override a newer explicit owner decision. Reconcile the conflict explicitly.

## 4. Product ownership boundary

### Capital Chronicle main project owns

- daily economic and market analysis;
- microeconomic, macroeconomic, and global-macro reports;
- scenario construction and probabilistic views;
- deterministic model calculations;
- Bayesian cases and updates;
- forecasts, market regimes, numeric truth, realized outcomes, and analytical error attribution.

### ContentOps owns

- headlines, breaking news, and business-news intake;
- event clustering, duplicates, corrections, and update chains;
- evidence, permission, freshness, and material-delta gates;
- editorial ranking, selection, portfolio diversity, hold, reject, and no-publication decisions;
- content mode, framing, writing, editing, SEO, images, and deterministic charts from authorized inputs;
- platform-native packages, publication control, readback, reconciliation, incidents, and content-performance learning;
- faithful transformation of governed Capital Chronicle analysis packets.

ContentOps must not independently create authoritative scenarios, model outputs, Bayesian probabilities, forecasts, market regimes, or numeric truth.

## 5. Final product direction

The final product is an AI-native autonomous newsroom and content factory with two input lanes:

```text
NEWSROOM LANE
fresh governed headlines and primary-source events
→ cluster and rank
→ select, hold, reject, or abstain
→ report, edit, optimize, visualize, package, publish, read back, and learn

CAPITAL CHRONICLE LANE
governed analysis packet
→ validate exact authority and lineage
→ transform faithfully into reports, articles, visuals, and native packages
→ publish, read back, and measure content performance
```

Required content diversity includes U.S. equities/Big Tech, sectors, earnings/filings, economic releases, politics/policy, central banks/rates/credit, FX/commodities/energy, geopolitics/trade/supply chains, regulation/law, global corporate events, and Capital Chronicle analysis products.

## 6. Operating modes

- `AUTONOMOUS_DEFAULT`: product default; public writes only when all exact deterministic gates pass.
- `SUPERVISED_OPERATOR_GATE`: optional owner toggle before public write.
- `SHADOW_ONLY`: full product cycle with zero public writes.
- `KILL_SWITCH`: blocks new public writes while preserving readback, reconciliation, and recovery.

Historical supervised release evidence remains valid. Older universal mandatory-approval language is not current product direction.

## 7. Canonical product surfaces

- canonical UI: `ui/contentops_v5/`;
- canonical UI entrypoint: `ui/contentops_v5/src/App.tsx`;
- canonical backend: `live_contentops/`;
- canonical production migration anchor: `live_contentops.eight_platform_substack_first_pipeline_v1`;
- canonical durable operational store: `live_contentops/durable_operational_store_v1.py`;
- current product direction: `docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md`;
- current final-product overlay: `docs/automation/CONTENTOPS_FULL_AUTOMATION_FINAL_PRODUCT_INSTITUTIONAL_NORTH_STAR_V1/FINAL_PRODUCT_SCOPE_OVERLAY_V2.md`;
- current detailed plan: `docs/automation/CONTENTOPS_FINAL_PRODUCT_SCOPE_CLOSEOUT_AND_LAUNCH_MASTER_PLAN_V1.md`.

Do not revive archived UI or runner surfaces as canonical paths.

## 8. Build doctrine

Use FAST SHIP + CORE V0.

Prefer one heavy bounded end-to-end product task over microtasks or horizontal infrastructure. Reuse accepted components. Add or harden durable state, approval, outbox, scheduler, provider, adapter, or UI work only when it directly blocks the final vertical slice or a launch gate.

Do not create a second runner, state store, approval engine, outbox, scheduler, provider gateway, dashboard, numeric-analysis path, or macro-analysis engine.

## 9. SEO, image, and chart invariants

SEO is an explicit production system with search intent, headline/title, slug, metadata, structure, citations, internal linking, visual metadata, and later observed search metrics. A deterministic checklist score is not observed SEO success.

Images require source/owner/context/rights/provenance or generated-image metadata, plus exact platform bindings. Image discovery does not grant reuse rights or factual authority.

Charts must be deterministic and reproducible from authorized Capital Chronicle data/calculations or approved official/public data. ContentOps may visualize authorized analysis; it may not originate analytical truth.

## 10. Safety and authority invariants

- Never bypass DQR, claim permissions, freshness, point-in-time authority, or story-scoped publication rules.
- Never publish unsupported LLM prose or fabricate numbers, analysis, quotations, sources, images of events, or readback.
- Never persist or print raw environment values, credentials, tokens, webhook URLs, authorization headers, cookies, browser storage, private keys, or session secrets.
- Never retry an unknown write blindly.
- Never mutate approved bytes without a new exact authorization record.
- Never return mock success from a live path.
- Never modify, move, recreate, or retag accepted `v1.0` artifacts.
- Never mutate the Capital Chronicle main project from a ContentOps task.
- Never let engagement metrics modify evidence or analytical truth.

## 11. Current next task

`TASK_CONTENTOPS_EXACT_AUTHORIZED_LIVE_COHORT_V1`

Mode:

`REQUIRES_EXACT_OWNER_AUTHORIZED_LIVE_SCOPE`

Work Package C (dual-lane CORE V0 shadow newsroom) is accepted and merged into `master`.
Work Package D (diversity, SEO, image, and chart closure) is accepted and fast-forward merged
into `master` from branch
`agent/contentops-core-v0-diversity-seo-image-chart-closure-v1`; its status is
`COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`, independent audit
`PASS_WITH_CAVEAT_ACCEPTED_FOR_MASTER_MERGE`, accepted source HEAD
`f83bd5c97479ef0001bac141e78d85eacdaa1cc9`, accepted correction commit
`1088bfb82d29d40fba4d3db1e910bf5d292bd522`, merge method `FAST_FORWARD_ONLY`. Neither is
reopened. Work Package E — the repeated shadow soak and recovery — is accepted and
fast-forward merged into `master` and is `COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`: independent audit `PASS_WITH_CAVEAT_ACCEPTED_FOR_MASTER_MERGE`, accepted
source HEAD `3770ff1c2fe77129c634af3263cbc4e31085b900`, merge method `FAST_FORWARD_ONLY`, starting master `4ad194cbbd4a1843b2e90cdc94bd4f9fe2015182`.

Work Package E proved, from one local command over the accepted pipeline and the accepted
Wave 02 durable store, ten logical newsroom days and thirty completed window decisions,
sixteen complete packages across both lanes, one hundred durable work items with zero lost
and zero double-claimed, sixteen of sixteen recovery and injected-failure drills passed,
one hundred forty-four hash-bound release intents with both `AUTONOMOUS_POLICY` and
`OPERATOR_DECISION` actors, forty-eight unknown-write simulations with zero blind retries,
and a launch-readiness disposition of `READY_WITH_EXPLICIT_CAVEATS`. Zero public writes and
zero outbox executions occurred.

The accepted Work Package D caveats remain truthful and are not converted into a pass: no
full-suite PASS is claimed, no CI PASS is claimed, the full-suite failures are a noisy
pre-existing baseline including two pointer-consistency failures already present at source
parent `3166bb69`, and Browser QA has committed screenshot evidence, hashes, DOM assertions,
and zero console/page errors but no independent pixel-perfect visual PASS.

The accepted Work Package E caveats remain truthful and are likewise not converted into a
pass: the soak is an accelerated logical soak and is **not** calendar uptime; no full-suite
PASS is claimed; no CI PASS is claimed; no real provider or model execution has occurred
yet; only two domains produced complete packages; and no independent pixel-perfect visual
PASS is claimed.

The final build sequence is:

```text
dual-lane CORE V0 in SHADOW_ONLY   [COMPLETE — ACCEPTED AND MERGED WITH CAVEAT]
→ diversity, SEO, image, and chart closure   [COMPLETE — ACCEPTED AND MERGED WITH CAVEAT]
→ repeated shadow soak and recovery   [COMPLETE — ACCEPTED AND MERGED WITH CAVEAT]
→ exact authorized live cohort   [CURRENT — REQUIRES EXACT OWNER LIVE SCOPE]
→ final acceptance and new release identity
```

The older automatic Wave 03 approval-envelope/transactional-outbox sequence is no longer the current next-task authority. It remains valid historical planning and is revisited only when the CORE V0 slice or a launch gate directly requires it.

## Final pre-launch LLM model authority

Authority ID:

`CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2`

Gateway: `9router`. Exact ordered model pool, in preference order:

```text
P0  new/claude-fable-5
P1  new/gpt-5.6-sol-xhigh
P2  new/claude-opus-5
P3  vx/gemini-3.1-pro-preview(high)
```

P0 remains `new/claude-fable-5`. The fallback order above is owner-authorized. Fallback is
for **bounded resilience, not quality-gate bypass**: a fallback model's output passes the
same evidence, editorial, permission, and freshness gates as the primary's, and a fallback
success creates no publication authority.

Every logical LLM invocation allocates one immutable retry budget before its first provider
call: at most 6 total provider attempts, 3 fallback transitions, 1 same-model retry, 1
structured-output repair (which itself consumes an attempt), 45 s cumulative retry sleep,
and a 300 s wall-clock budget. The budget is never reset by a model change or by a process
restart. There is no unbounded retry and no unauthorized model.

Silent provider-side substitution remains forbidden. If the gateway resolves a model other
than the exact requested one, the output is rejected regardless of quality. If the gateway
does not expose effective-model identity, that is recorded as
`MODEL_IDENTITY_NOT_PROVIDER_VERIFIABLE` rather than upgraded to a pass.

This authority supersedes `CONTENTOPS_FINAL_PRELAUNCH_LLM_MODEL_AUTHORITY_V1`, which
prohibited all fallback. V1 is preserved as historical lineage.

Work Package F — the exact authorized live cohort — remains the current product route. A
public live cohort has **not** been authorized by the router task; publication still
requires an explicit live scope defining destinations, accounts, and public-write authority.

### Historical lineage: authority V1

Authority ID:

`CONTENTOPS_FINAL_PRELAUNCH_LLM_MODEL_AUTHORITY_V1`

Gateway: `9router`. Exact required model ID: `new/claude-fable-5`.

Jim's final pre-launch directive: this exact model must be used for every applicable LLM
task in Work Package F (launch-representative exact authorized live cohort) and Work
Package G (final full-automation pre-launch run).

Required invariant:

```text
requested_model == resolved_model == "new/claude-fable-5"
```

No silent alias, fallback, substitution, downgrade, or role-specific alternate model is
acceptable. If the exact effective model cannot be verified, F/G execution must fail closed
with `BLOCKED_EXACT_FINAL_LLM_MODEL_UNAVAILABLE_OR_MISMATCHED`.

Every future LLM invocation must bind: story/work-item ID, role/task ID, gateway, requested
model, resolved/effective model, invocation ID where returned, prompt/version hash, governed
input hash, output hash, attempt, latency, token/cost metadata where returned, and the
validation/recovery result.

Model runtime verification status:

`OWNER_DIRECTIVE_RECORDED_NOT_YET_PROVIDER_VERIFIED`

This is an owner directive recorded as authority. No provider call, credential read, or
model invocation was performed to record it, so the effective model is **not** claimed to
have been verified against the live gateway. The first F/G execution must verify
`requested_model == resolved_model` at runtime and fail closed if it cannot.

Never expose or commit raw API keys, auth headers, endpoint secrets, cookies, session data,
or environment values. This model authority grants no factual, numeric, analytical,
permission, approval, dispatch, or publication authority.


This task grants no credential, provider, browser/CDP, network-intake, scheduler/outbox execution, dispatch, publication, or public-write authority.

## 12. Task protocol

Before implementation:

1. verify repository, branch, remote HEAD, relevant candidate branch, protected tag, and path scope;
2. read the current authority files above;
3. capture the exact task once and do not reopen completed phases without a real invalidation trigger;
4. search for existing implementations and avoid parallel systems;
5. confirm exact no-live/live/provider/browser/network scope.

During implementation:

1. use one locked source worktree and one target/verification worktree unless a real conflict requires otherwise;
2. keep validation focused plus one relevant end-to-end smoke;
3. continue through reversible in-scope defects;
4. stop only for secrets, fabricated numeric truth, unauthorized access/write, destructive unrelated mutation, protected release/tag mutation, irreconcilable remote/ref mismatch, unresolved substantive conflict, or truly missing external input.

After implementation:

1. update only the minimal current authority surfaces;
2. stage explicit scoped paths only;
3. commit and push non-force to the authorized branch;
4. verify remote readback and protected `v1.0`;
5. report exact start/final HEAD, changed files, focused tests/smoke, public/provider/network actions, caveats, utility delta, and exact next blocker.

Work Package D worker PASS has completed independent GitHub/ChatGPT audit as
`PASS_WITH_CAVEAT_ACCEPTED_FOR_MASTER_MERGE`. Later worker PASS claims remain awaiting
independent GitHub/ChatGPT audit.
