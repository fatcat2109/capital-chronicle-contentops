# ContentOps V6/Post-v1 Next Task Pointer

Authority date: 2026-08-07

## Current pointer

Current product-direction classification:

`CONTENTOPS_NEWSROOM_AND_CONTENT_FACTORY_SCOPE_OWNER_APPROVED`

Approved post-Tier-1 expansion:

`CONTENTOPS_TIER2_PRO_VIDEO_FACTORY_OWNER_DIRECTION_V1`

Current durable prerequisite:

`COMPLETE_ACCEPTED_AND_MERGED_AS_MINIMUM_DURABLE_PREREQUISITE`

Work Packages C, D, and E are:

`COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`

### Latest product action

`TASK_CONTENTOPS_PROMOTE_AUTONOMOUS_RUN_AND_RERUN_ON_FRESH_GOVERNED_PACKET_V1`

Status:

`BLOCKED_FRESH_CAPITAL_CHRONICLE_PUBLICATION_PACKET_UNAVAILABLE`

The accepted autonomous Work F result is now on `master` at `025164d73`. The current
Capital Chronicle producer emitted publication-authorized packet
`cc-publication-8404fad760faec52b37e`, but its latest market observation was 34.674 hours
old against the 24-hour threshold. The canonical rerun correctly did not start. Owner live
scope remains resolved dynamically from canonical `READY_*` destinations; another approval
or tiny cohort is not current authority. Tier-2 is not current.

Exact next product action:

`REFRESH_GOVERNED_CAPITAL_CHRONICLE_PUBLICATION_EVIDENCE_AND_RERUN_CANONICAL_CYCLE`

Operating mode: `AUTONOMOUS_DEFAULT`

## Current router/model authority

- authority ID: `CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2`
- gateway: `9router`
- exact ordered model pool (opaque exact strings, priority order):
  - P0 `new/claude-fable-5`
  - P1 `new/gpt-5.6-sol-xhigh`
  - P2 `new/claude-opus-5`
  - P3 `vx/gemini-3.1-pro-preview(high)`
- primary preference remains `new/claude-fable-5`;
- ordered fallback is owner-authorized for bounded resilience, and is not a quality-gate
  bypass: fallback output passes the same evidence, editorial, permission, and freshness
  gates as primary output, and never creates publication authority;
- silent provider-side substitution remains forbidden. Per attempt,
  `requested_model == provider-observed resolved model` is still required; a mismatch is
  rejected and the pool is walked only under the deterministic fallback policy;
- every logical invocation allocates one immutable retry budget before its first provider
  call: 6 total provider attempts, 3 fallback transitions, 1 same-model retry, per-model
  attempt ceilings (2, 2, 1, 1), 1 structured-output repair counting against the total,
  45 s cumulative retry sleep, 300 s wall clock. No model change and no process
  reconstruction resets a consumed budget; unbounded retry is not permitted;
- terminal dispositions on exhaustion: `LLM_RETRY_BUDGET_EXHAUSTED`, or
  `BLOCKED_AUTHORIZED_MODEL_POOL_EXHAUSTED` when every authorized model is exhausted;
- runtime verification: `PROVIDER_VERIFIED`. Latest bounded no-write preflight probed all
  four authorized models: 4/4 `HEALTHY`, 0 unavailable, 0 identity mismatch, 0 identity
  unverifiable, disposition `MODEL_IDENTITY_PROVIDER_VERIFIED`. Evidence:
  `docs/automation/CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2/model_router_run_summary.json`,
  Gemini correction commit `a3d42dab03ac4ceb09a4106d46e37d65e08cad77`;
- P3 wire contract: the authorized pool identity stays the opaque string
  `vx/gemini-3.1-pro-preview(high)`. The gateway builds its Vertex endpoint by appending the
  model string to the endpoint path, so the request is sent as wire model
  `vx/gemini-3.1-pro-preview` plus wire reasoning effort `high`, and the provider reports
  identity `gemini-3.1-pro-preview`. This is an authorized request transformation, not
  silent model substitution;
- this authority supersedes `CONTENTOPS_FINAL_PRELAUNCH_LLM_MODEL_AUTHORITY_V1`, which
  prohibited all fallback and is retained only as historical lineage;
- current operator-reported model availability may be degraded; the router continues through
  whichever authorized pool members remain healthy and blocks only when the bounded pool is
  exhausted or a non-fallback-eligible gate fails;
- router authority alone does not grant public-write scope. Jim's recorded Work F task
  separately grants live scope to dynamically verified canonical `READY_*` destinations;
  no renewed cohort authorization is required.

## Work F recorded boundary

Jim's exact 2026-08-07 task supplied destination/account/public-write authority. Do not ask
for another cohort authorization. The scope is all and only dynamically validated canonical
`READY_AUTHENTICATED` and `READY_NON_BROWSER_BINDING` destinations. Kill switch, fail-closed
unknown-write handling, strict readback, and reconciliation remain mandatory.

The recorded run performed no public write because the governed story failed freshness and
semantic-review gates. Its exact next blocker is fresh governed publication evidence, not
owner scope.

The separate rolling-X newsroom path does not wait for that generic packet. Its exactly-one
real cycle accepted 1,024 source-event-time-valid X headlines and terminated truthfully as
`NO_PUBLICATION` with `ASSIGNMENT_NOT_ACCEPTED`; no article, platform adapter, public write,
or unknown write occurred. X is discovery/ranking input only, and targeted evidence follows
accepted ranking. Evidence:
`docs/automation/ROLLING_X_NEWSROOM_LIVE_V1/real_cycle/rolling_x_newsroom_cycle_evidence_v1.json`.

## Rolling-X newsroom vertical slice

`rolling 24-hour X discovery → assignment/ranking → targeted evidence → first viable ranked
story → article/SEO/visuals → bounded semantic revision/review → platform packages →
AUTONOMOUS_DEFAULT gates → strict readback/reconciliation`

This route is complete as an implemented, governed no-publication vertical slice for the
current sidecars. A generic Capital Chronicle packet is not a prerequisite for discovery.

## Current Tier-1 sequence

```text
Work F canonical cycle: autonomous no-publication with caveat   [EXECUTED]
→ fresh-packet probe: official observation outside 24h window   [BLOCKED EXTERNAL]
→ rerun canonical cycle when a genuinely fresh packet exists
→ major final Tier-1 UI/UX rebuild using real live states
→ Work Package G final full-automation prelaunch run
→ Tier-1 final acceptance + new release identity
→ freeze accepted Tier-1 baseline
```

The older broad Wave 03–15 hardening sequence is historical and only re-enters scope when a concrete launch gate requires it.

## Approved post-Tier-1 route

After Tier-1 is accepted and frozen:

```text
TIER2-A local long-form + short-form programmable vertical slice
→ TIER2-B multimodal QA + bounded auto-revision + diverse corpus
→ TIER2-C platform-native private/unlisted/draft readback
→ TIER2-D bounded live video cohort
→ TIER2-E final Tier-2 acceptance + release
```

Tier-2 authority:

- `docs/automation/CONTENTOPS_TIER2_PRO_VIDEO_FACTORY_NORTH_STAR_V1.md`
- `docs/automation/CONTENTOPS_TIER2_PRO_VIDEO_FACTORY_MASTER_PLAN_V1.md`

Required video lanes:

- `SHORT_FORM_NATIVE`
- `LONG_FORM_EDITORIAL_15_45M`

Do not start `TIER2-A` while Tier-1 is unfinished unless Jim explicitly changes product priority.

## Historical video plan

`docs/automation/VIDEO_FOUNDATION_AND_PAUSE_V1/` is historical discovery/evidence and is superseded as future implementation authority wherever it conflicts with the Tier-2 Pro Video Factory direction.

## Preserved boundaries

- no unauthorized provider/browser/platform/scheduler/public action;
- no raw credential/session access;
- no fabricated numeric or analytical truth;
- no synthetic documentary deception;
- no Capital Chronicle main-project mutation;
- no `v1.0` mutation/retag;
- no second newsroom/state/publication authority;
- no blind retry of unknown writes/uploads.
