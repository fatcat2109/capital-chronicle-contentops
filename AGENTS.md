# Capital Chronicle ContentOps — AI Builder Entry Contract

This is the first file every AI IDE/CLI builder must read before touching the repository.

Authority date: 2026-08-07

## 1. Authority model

### Repo-state authority

1. GitHub remote refs/commits/diffs/exact fetched bytes.
2. Current committed code/tests/schemas/evidence.
3. Current status/overlay/master-plan files.
4. Durable operational state and redacted run evidence.
5. Provider/platform strict readback.
6. Worker logs.
7. Project Sources/chat memory/archives.

### Product-direction authority

1. Jim's latest explicit instruction and project instructions.
2. Current committed product-direction overlay/master plan.
3. Older plans/archives.

Never let stale repo plans override a newer explicit owner decision. Reconcile the conflict.

## 2. Protected historical release

ContentOps `v1.0` remains immutable at release commit `6983bfb3ef300414b744f3f8f97ca81ff699348b` with annotated tag `v1.0`.

It proves one bounded Treasury release, not a continuously operating newsroom.

Never rerun, recreate, mutate, move, or retag accepted `v1.0` outputs/evidence.

## 3. Current product direction

Current classification:

`CONTENTOPS_NEWSROOM_AND_CONTENT_FACTORY_SCOPE_OWNER_APPROVED`

Approved future expansion:

`CONTENTOPS_TIER2_PRO_VIDEO_FACTORY_OWNER_DIRECTION_V1`

Capital Chronicle main project owns analytical/numeric authority:

- daily market/economic analysis;
- micro/macro/global-macro reports;
- scenarios/probabilistic views;
- deterministic model calculations;
- Bayesian cases/updates;
- forecasts/regimes;
- numeric truth;
- realized outcomes and analytical error attribution.

ContentOps owns newsroom/media production:

- governed headline/news intake;
- clustering, duplicates, corrections, update chains;
- evidence/permission/freshness/material-delta gates;
- ranking/diversification/hold/reject/no-publication;
- writing/editing/SEO;
- images and deterministic charts from authorized inputs;
- media/platform packages;
- publication control;
- readback/reconciliation/incidents;
- performance learning;
- faithful transformation of governed Capital Chronicle packets.

ContentOps must not create independent analytical authority.

## 4. Mandatory read order

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
12. Tier-2 North Star/Master Plan when reasoning about post-Tier-1 video
13. exact task code/tests/schemas/evidence.

Tier-2 authority docs:

- `docs/automation/CONTENTOPS_TIER2_PRO_VIDEO_FACTORY_NORTH_STAR_V1.md`
- `docs/automation/CONTENTOPS_TIER2_PRO_VIDEO_FACTORY_MASTER_PLAN_V1.md`

## 5. Operating modes

- `AUTONOMOUS_DEFAULT` — product default; public writes only when exact deterministic gates pass.
- `SUPERVISED_OPERATOR_GATE` — optional owner toggle before public write.
- `SHADOW_ONLY` — full product cycle with zero public writes.
- `KILL_SWITCH` — blocks new public writes while preserving readback/reconciliation/recovery.

Historical supervised evidence remains valid. Mandatory human approval is not the universal product default.

Owner direction recorded on 2026-08-07 removes any artificial one-, two-, or three-post
cohort cap. Live scope is resolved dynamically from the canonical registry, non-secret
binding capability, and verified account identity. Only `READY_AUTHENTICATED` and
`READY_NON_BROWSER_BINDING` destinations may receive writes. A fully autonomous
no-publication result remains correct when evidence, freshness, editorial, permission, or
portfolio gates block every candidate; do not weaken those gates to manufacture a post.

The first owner-authorized Work F execution reached article/media/platform-package creation
but correctly stopped before dispatch because the governed market packet was stale and the
9Router adversarial review returned `NEEDS_REVISION`. That result is preserved as historical
Work F evidence and is not a prerequisite for newsroom discovery.

The current rolling-X newsroom vertical slice is governed by:

`rolling 24-hour X discovery → assignment/ranking → targeted story-dependent evidence → first
viable ranked story → article/SEO/visuals → semantic review → bounded revision/re-review →
platform packages → AUTONOMOUS_DEFAULT gates → strict readback/reconciliation`.

The exactly-one governed real cycle for this task completed as `NO_PUBLICATION` with
`ASSIGNMENT_NOT_ACCEPTED` after accepting 1,024 source-event-time-valid headlines. No article,
visual, platform adapter, public write, or unknown write occurred. Evidence is under
`docs/automation/ROLLING_X_NEWSROOM_LIVE_V1/real_cycle/`. X remains discovery/ranking input
only; targeted evidence is acquired only after accepted ranking, and a generic Capital
Chronicle packet is not a discovery prerequisite.

The hierarchical-assignment correction supersedes that assignment architecture, not the
frozen historical result. Every rolling-24h unique headline now enters exactly one
deterministic size-bounded leaf partition. The leaf-scan role prefers exact model
`vx/gemini-3.5-flash(high)` for semantic labor, while the compact global editor uses the
unchanged quality-first pool. Attention and engagement affect priority only, never factual
truth. The 1,024-headline replay produced 16 accepted leaf partitions, 632 leaf clusters,
and a valid 12-item shortlist with zero dropped, duplicated, or unknown IDs. Current
sidecars had no fresh rolling-24h headlines, so no new governed current cycle was started;
`NO_FRESH_CURRENT_HEADLINES` is an operational caveat. Generic Capital Chronicle packets
remain conditional evidence inputs, not discovery prerequisites. Three hundred seconds is
not an end-to-end newsroom quality SLA; each provider invocation remains finite and bounded.

## 6. Canonical Tier-1 surfaces

- backend: `live_contentops/`
- durable store: `live_contentops/durable_operational_store_v1.py`
- production migration anchor: `live_contentops.eight_platform_substack_first_pipeline_v1`
- canonical UI: `ui/contentops_v5/`
- schemas: `schemas/`
- current direction: `docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md`

Do not create a second newsroom, runner authority, state store, approval engine, outbox, scheduler, provider gateway, dashboard, or analysis engine.

### Persistent browser role authority

These are two intentionally separate persistent operator profiles. Their role and binding are
part of the safe repository authority; browser authentication/session state remains outside Git.

- **Chrome `CapitalChronicleBot` on CDP `9222` — ingestion only.** Use only for the upstream
  X List route and `ListLatestTweetsTimeline` headline/raw-sidecar discovery. Never use it for
  ContentOps media publication, platform management, or readback.
- **Microsoft Edge `contentops-social-main` on CDP `9223` — publishing/media management only.**
  Use only through the canonical publishing-profile registry for Substack, X publication,
  LinkedIn, Facebook, Instagram, Threads, YouTube, and other approved media-platform
  management/readback. Never use it for headline ingestion.

Never create, clone, migrate, clean, delete, or substitute either persistent profile. Never
inspect or export cookies, browser storage, tokens, credentials, or session databases. The
authenticated browser state is operator-owned external state and must never be committed.

#### Canonical ingestion continuity lock (permanent)

The canonical X ingestion binding is the existing operator-owned `CapitalChronicleBot`
persistent profile on Chrome CDP `9222`:

```text
browser_family   = CHROME
profile_id       = CapitalChronicleBot
cdp_port         = 9222
role             = INGESTION_ONLY
user_data_dir    = %LOCALAPPDATA%\Google\Chrome\User Data\CapitalChronicleBot
canonical_route  = https://x.com/i/lists/1843870469143048642
```

ContentOps must always reuse it and must never create, clone, reset, migrate, clean, replace,
rename, delete, or silently fall back from it. There is no alternate path, no fallback
profile, no Default/personal Chrome fallback, and no Edge fallback for ingestion. If the
binding is missing or cannot be proven (`PROFILE_BINDING_MISSING` / `PORT_OWNER_UNPROVEN`),
fail closed and never create a replacement. Provider-side session expiration is not a profile
problem: it may require operator reauthentication in that same profile only. Profile
continuity != provider authentication lifetime.

## 7. Canonical live-write authority

The canonical publishing-profile registry remains the only live-write authority. A browser
family/profile role declaration does not grant publication permission; exact destination
readiness must still be dynamically verified as `READY_AUTHENTICATED` or
`READY_NON_BROWSER_BINDING`, with strict readback and reconciliation. Unknown writes follow
`STOP RETRY → READ BACK → RECONCILE`.

## 8. Current Tier-1 state

Work Package C:

`COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`

Work Package D:

`COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`

Work Package E:

`COMPLETE_ACCEPTED_AND_MERGED_WITH_CAVEAT`

Work E launch-readiness:

`READY_WITH_EXPLICIT_CAVEATS`

The accelerated logical soak is not calendar-time live reliability and does not claim full-suite or CI PASS.

## 9. Latest operational task

`TASK_CONTENTOPS_V1_CONTINUOUS_INTELLIGENCE_INTAKE_CC_DATABASE_AND_EDITORIAL_PORTFOLIO_REALIGN_V1`

Status:

`COMPLETE_IMPLEMENTED_AND_VALIDATED`

Owner mid-task realignment: the V1 Daily App is organized around a continuous cheap
intelligence layer — continuous zero-LLM X headline intake lane inside the canonical
supervisor (canonical per-day sidecar store only, append-only, deduplicated, restart-safe);
every editorial decision reconstructs the complete rolling 24h unique headline universe; a
read-only Capital Chronicle data estate catalog with story-scoped context; a published-corpus
read model from existing durable publication truth; explicit breaking/follow-up/deepen/
low-delta novelty classification; bootstrap.v2 window policy with eight daily decision
opportunities and a 5–8 article/day target band (a target, not filler permission). Run Now
uses the SAME canonical newsroom authority as scheduled/material-event cycles; the retired
special run-now gate relaxation grants no bypass. Tier2-A preserved; FDA-G prior epochs
preserved as pre-realignment historical evidence. Prior completed task:

`TASK_CONTENTOPS_V1_TRUE_ONE_CLICK_INGESTION_BOOTSTRAP_AND_RUN_NOW_CONTROL_V1`

Status:

`COMPLETE_IMPLEMENTED_AND_VALIDATED`

V1 runtime/product correction completing the one-click desktop operating contract:

1. `Start_ContentOps_Daily_App.cmd` now safely bootstraps the EXISTING dedicated Chrome
   `CapitalChronicleBot` ingestion profile on CDP 9222 when absent (exact historical
   `Launch_Dashboard.bat` binding, no new/cloned profile, no login automation, REAUTH_REQUIRED
   reported truthfully when the X session needs operator sign-in), reuses it when alive, and
   fails closed on an unproven 9222 owner.
2. One canonical `Run editorial cycle now` operator control (V5 Today +
   `POST /api/daily-app/control/run-now`) records a durable, restart-safe, append-only
   `OPERATOR_REQUESTED` trigger (schema v9, one pending trigger at a time). The persistent
   supervisor consumes it through the exact canonical cycle boundary; only the wait for the
   scheduled window is bypassed — every evidence/review/readiness/publication gate is
   unchanged. KILL_SWITCH is never cleared; no public write is claimed by the control.
   The quarantined `POST /api/run-pipeline` stays locked (423). No public write occurred.

Prior completed task:

`TASK_CONTENTOPS_V1_ONE_CLICK_MORNING_LAUNCH_AND_RESUME_V1`

Status:

`COMPLETE_IMPLEMENTED_AND_VALIDATED`

One-click morning launch/resume for the canonical Daily App: `Start_ContentOps_Daily_App.cmd`
delegates through `scripts/Start-ContentOpsDailyApp.ps1` and
`live_contentops.daily_app_launcher_v1` to the existing canonical
`python -m live_contentops.cli daily-app start ...` command. It is idempotent (no duplicate
supervisor/cycle/public object), reuses the exact production store without reset, fails closed
on ambiguous port ownership, preserves KILL_SWITCH and UNKNOWN_WRITE state, performs only
loopback GET probes and detached local process starts, and emits names-and-presence-only
credential preflight. No public write occurred. Prior completed runtime task:

`TASK_CONTENTOPS_FINAL_DAILY_APP_AUTONOMOUS_PUBLICATION_RUNTIME_AND_TRANSPORT_LOCK_V1`

Status:

`COMPLETE_IMPLEMENTED_AND_VALIDATED`

The Final Daily App has one durable public-write owner, a versioned surface/transport registry,
durable pre-write outbox and attempt markers, restart-safe UNKNOWN_WRITE handling, strict
readback/reconciliation, real read-only readiness probes, Edge 9223 self-bootstrap, and one
production start command. Chrome 9222 remains ingestion-only. The production store is schema
v8 after lossless migration with its prior rows and production epoch preserved. No public write
occurred in this task. Exact evidence is under
`docs/automation/CONTENTOPS_FINAL_DAILY_APP_AUTONOMOUS_PUBLICATION_RUNTIME_AND_TRANSPORT_LOCK_V1/`.

## 10. Current router/model runtime authority

Current authority ID:

`CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2`

Gateway: `9router`. Exact ordered pool:

```text
P0  new/claude-fable-5
P1  new/gpt-5.6-sol-xhigh
P2  new/claude-opus-5
P3  vx/gemini-3.1-pro-preview(high)
```

The V2 runtime/model lineage is integrated from accepted source head
`ae60da22b9a155d25dc783f10285eecd875b9d0f`. V1 remains historical only.

Fallback is owner-authorized for bounded resilience when a model is unavailable or another
eligible transient provider/infrastructure failure occurs. Current operator direction is to
continue through the ordered pool using whichever authorized models remain healthy; a
partially unavailable pool is degraded capacity, not by itself a stop condition. If no
authorized model succeeds within budget, the logical invocation blocks closed.

The default logical invocation has one immutable budget: at most 6 total provider attempts,
3 fallback transitions, 1 same-model retry, 1 structured-output repair (which consumes an
attempt), 45 seconds cumulative retry sleep, and 300 seconds wall clock. The compact
rolling-X global-editor role uses the same unchanged four-model quality order with one
attempt per model and a finite 1,200-second wall budget so degraded capacity cannot consume
the entire invocation before compatible fallback. Budgets never reset on fallback or
restart/reconstruction.

Fallback never bypasses evidence, factual, numeric-authority, permission, freshness,
publication, or policy gates and creates no publication authority. Silent provider
substitution remains forbidden; requested and effective identity must match for each attempt.

For Gemini P3, the authorized pool identity is
`vx/gemini-3.1-pro-preview(high)`, the wire model is
`vx/gemini-3.1-pro-preview`, and wire reasoning effort is `high`. This request
transformation is authorized and is not model substitution.

The quality-first pool remains unchanged globally. Only
`rolling_x_newsroom_leaf_scan` prefers `vx/gemini-3.5-flash(high)` before compatible
authorized fallback models. One bounded no-write probe verified provider-observed identity
`gemini-3.5-flash`. Flash is semantic labor only and grants no factual, analytical,
evidence, or publication authority.

## 11. Current Tier-1 build sequence

```text
Work F canonical cycle: autonomous no-publication with caveat   [EXECUTED]
→ fresh-packet probe: official source remained outside 24h window   [BLOCKED EXTERNAL]
→ wait for a genuinely fresh Capital Chronicle packet and rerun canonical cycle
→ major final Tier-1 UI/UX rebuild using real live states
→ Work Package G final full-automation prelaunch run
→ Tier-1 final acceptance + new release identity
→ freeze accepted Tier-1 baseline
```

The final UI rebuild occurs after Work F so it is designed around real live states: provider/model fallback, platform processing, readback, unknown writes, reconciliation, incidents, cost, and recovery.

## 12. Approved post-Tier-1 Tier-2 direction

After Tier-1 final acceptance/freeze, the approved next product expansion is:

**CONTENTOPS TIER-2 PRO VIDEO FACTORY**

Required production lanes:

- `SHORT_FORM_NATIVE`
- `LONG_FORM_EDITORIAL_15_45M`

15–45 minute long-form professional video is core scope. Short-form is independently directed and compiled; it is not a blind crop of long-form.

A 2–5 minute video may exist later only as an optional derivative.

Tier-2 is a programmable, deterministic-first media factory:

```text
canonical story/evidence
→ video eligibility
→ Director
→ Video Program / Chapter Graph / Scene Graph
→ deterministic-first Asset Engine
→ narration/audio
→ programmable compositor
→ scene/chapter caching
→ FFmpeg/ffprobe
→ deterministic + multimodal QA
→ bounded selective revision
→ long-form + short-form packages
→ exact-authorized upload/readback/reconciliation
→ video-native performance learning
```

Generative video is optional enrichment, not foundation.

Tier-2 implementation is **NOT CURRENT**.

## 13. Historical video material

`docs/automation/VIDEO_FOUNDATION_AND_PAUSE_V1/` remains historical discovery/evidence.

Its future implementation routing is superseded wherever it conflicts with the Tier-2 Pro Video Factory owner direction.

Reuse compatible FFmpeg/media-manifest/platform research. Do not automatically revive indefinite pause policy, avatar-first architecture, stale platform assumptions, or a parallel newsroom/state/publication authority.

## 14. Build doctrine

Use FAST SHIP + heavy bounded end-to-end vertical slices.

Every task should state:

- user problem;
- capability delivered;
- demo path;
- measurable utility delta;
- why now;
- bounded time/cost;
- simplest viable approach;
- focused validation;
- exact next blocker.

Support docs/tests/evidence should remain proportionate and directly support product capability.

Do not reopen accepted work without a real invalidation trigger.

## 15. Fast-ship blocker policy

Stop only for true hard blockers:

- secret/credential exposure;
- fabricated numeric truth;
- unauthorized access/public write;
- destructive unrelated mutation;
- protected release/tag mutation;
- irreconcilable remote/ref mismatch;
- unresolved substantive merge conflict;
- missing required external/operator input that cannot be inferred safely.

Do not stop for unrelated dirty files, absent CI, stale historical docs, mechanical formatting issues, or pre-existing unrelated test noise.

## 16. Safety invariants

- never bypass evidence/permission/freshness/point-in-time authority;
- never fabricate numbers, analysis, quotes, sources, event imagery, or readback;
- never expose raw env values, tokens, webhook URLs, auth headers, cookies, browser storage, private keys, or sessions;
- never retry unknown writes/uploads blindly;
- never mutate approved bytes without new exact authorization;
- never mutate Capital Chronicle main-project authority;
- never modify/retag `v1.0`;
- never treat engagement as factual authority;
- generated media must not masquerade as documentary evidence.

## 17. Commit / evidence discipline

- stage explicit paths only;
- never use `git add .` or `git add -A` for mixed worktrees;
- preserve unrelated changes;
- prefer one bounded product commit;
- verify remote readback;
- do not claim CI PASS when no CI ran;
- use focused tests plus one relevant end-to-end smoke where implementation changes justify it.

## 18. Exact next action

FDA-G genuine calendar-time soak remains active:

`TASK_CONTENTOPS_FINAL_DAILY_APP_GENUINE_CALENDAR_TIME_LIVE_SOAK_V1` — `SOAK_ACTIVE_AWAITING_GENUINE_CALENDAR_TIME_EVIDENCE`

Owner priority override (2026-08-10): after the completed one-click morning launcher task
(`TASK_CONTENTOPS_V1_ONE_CLICK_MORNING_LAUNCH_AND_RESUME_V1`, entry file
`Start_ContentOps_Daily_App.cmd`) and its follow-up V1 correction
(`TASK_CONTENTOPS_V1_TRUE_ONE_CLICK_INGESTION_BOOTSTRAP_AND_RUN_NOW_CONTROL_V1`, Chrome 9222
bootstrap + governed Run Now control), Tier-2 implementation proceeds concurrently with the
continuing FDA-G evidence lane:

`TIER2-A LOCAL LONG-FORM + SHORT-FORM PROGRAMMABLE VERTICAL SLICE`

Tier-2 remains isolated from the live V1 production runtime and has NO video public-write
authority under that reprioritization. This override supersedes the older "do not start Tier-2
before Final Daily App V1 acceptance/freeze" routing text where they conflict. FDA-G has not
been declared accepted.
