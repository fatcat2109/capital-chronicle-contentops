# Capital Chronicle ContentOps — Current Stale Docs Manifest V1

Authority date: 2026-08-31
Status: `CURRENT_STALE_AUTHORITY_MANIFEST`

Purpose: prevent fresh sessions from reviving obsolete V1 quota, scheduler, canary, owner-gate,
V2-resumption, Speech Highlight Relay, or sequencing assumptions.

## 1. Current routing authority

Fresh V1 work must route from:

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md`
4. this manifest
5. `docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md`
6. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
7. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`
8. `docs/automation/CONTENTOPS_V1_POST_ACCEPTANCE_ACTIVATION_AUTHORITY_V1.md`
9. `docs/automation/CONTENTOPS_V1_SIMPLE_GEMINI_RUNTIME_RESET_V1.md`
10. `docs/codegraph/V1_CONTEXT.md`
11. current lane pointer, including
    `docs/automation/CONTENTOPS_LIGHTWEIGHT_SPEECH_HIGHLIGHT_RELAY_CURRENT_EXECUTION_POINTER_V1.md`
    for Relay work
12. exact current code/tests/evidence/host truth.

## 2. Current owner state

The merge commit `db0befb8ad44f1080c67fcb801e5470ce7852369` records:

- `V1_FINAL_PRODUCT_ACCEPTED = TRUE`;
- routine V1 public-write/readback authority is granted for the accepted V1 path;
- V2 public-write authority remains zero unless separately granted.

Any file saying routine V1 public-write/readback remains ungranted or `V1_FINAL_PRODUCT_ACCEPTED` is pending is stale for current routing.

Jim's 2026-08-31 product decision additionally makes these current:

- V1 activation/runtime completion remains the immediate primary priority;
- the lightweight Speech Highlight Relay is a separate interim capability;
- main V2 is paused until Jim explicitly resumes it;
- the Relay is not V2 progress and has no duplicate-owner authority; and
- Relay public-write authority remains zero unless a later exact grant changes it.

## 3. Superseded semantics

Treat the following claims as stale/non-routing unless an even newer explicit owner instruction changes them:

- no mandatory live-output floor or zero whole-day publication is healthy success;
- 5–8/day is merely aspirational and zero is a successful live production day;
- candidate-level abstention makes a below-target whole day healthy;
- a perfect 4/32 zero-write proof is required before one safe article or before V1 acceptance;
- the Italy nine-surface canary is pending or must be repeated merely to prove transport;
- production-day accounting/bounded deficit recovery has never existed;
- PR #19 discovery donors, PR #20 article/package proof, or PR #37 early-attributed-intelligence/epistemic/native-preview capability are unimplemented;
- first-party locator/publisher pinning is the next V1 implementation task;
- per-trigger 35-call discovery is accepted routine production policy;
- native Desktop Automations or SDK/App-Server fallback own routine V1 editorial execution;
- legacy rolling-X split-phase ownership is the current critical path;
- arbitrary X-list membership grants factual/relay/rumor authority;
- official/primary confirmation is required before every reputable attributed report;
- report truth and event truth are interchangeable;
- routine V1 public-write/readback authority remains zero;
- `V1_FINAL_PRODUCT_ACCEPTED` is still forbidden/pending;
- PR #38 emergency-stop/process coverage for Simple remains missing;
- PR #39 single routine-owner production composition remains missing;
- the actual persistent Simple scheduler still lacks a production handoff into the existing durable publication coordinator;
- a component-only supervisor bridge is sufficient proof of the current persistent scheduler route;
- V2 has any public-write authority;
- V1 acceptance automatically activates the old V2-after-V1 roadmap;
- the Speech Highlight Relay is the V2 Retention-Native Video Factory, resumes V2, or inherits V2
  worker/model/orchestration requirements;
- public availability, platform posting, speaker identity, attribution, cropping, subtitles, or a
  short excerpt establishes source-footage reuse permission;
- the Relay may own another scheduler, durable store, publisher/publication coordinator, browser,
  truth system, or model router;
- current V1 article publication authority covers Relay video/Reel/Short uploads; or
- the historical/current V2 shadow publication control plane is a live Relay publication owner.

## 4. Current replacement semantics

- V1 is `EARLY_ATTRIBUTED_INTELLIGENCE`: one exact reputable report may support a narrow attributed proposition while the underlying event remains visibly unconfirmed.
- Exact owner-curated canonical-X records may support only narrow relay-of-reporting or explicit-rumor propositions under the accepted record-scoped provenance contract.
- Routine editorial ownership is Simple Gemini under the accepted 32/6/3/1 economics; Desktop/SDK/legacy rolling-X routes are historical/non-routing.
- Merged PR #38 already closes current authority/static-safety and emergency-stop/process coverage for the canonical Simple scheduler/runtime.
- Merged PR #39 already closes single-owner composition: current Final Daily App production composition routes routine V1 through `SIMPLE_GEMINI_RUNTIME`; Native Desktop/legacy rolling-X are compatibility-only/non-routing.
- Corrected PR #42 closes the actual persistent Simple scheduler -> existing `DurablePublicationCoordinator` handoff. Stable slot identity is the durable work-item identity; the publication plan is persisted/reconstructed without model/source re-execution; recovery runs before fresh work; interrupted qualified slots resume without another Simple/model/source call; unresolved backlog blocks current-plan registration/republication; terminal duplicate ticks do not duplicate semantic/public intent.
- `DurablePublicationCoordinator` remains the sole public-write/readback/reconciliation owner. Canonical Substack `/p/...` reconciliation precedes exactly-eight derivative rematerialization. Do not build another publisher/store/scheduler/package stack.
- Historical Italy publication proves the nine-surface transport/reconciliation stack. Current live account/session/readiness still requires read-only revalidation before the first new live write.
- Live daily-output success is based on strictly reconciled published canonical articles, not merely zero-write qualified article records.
- Published-vs-qualified accounting is implemented in the current master lineage.
- Current activation order is read-only host preflight -> one live canary -> routine four-window live enablement.
- Current Relay order is planning authority -> one later `REUSE_CLEAR`, official-timed-transcript,
  zero-write vertical slice -> bounded generalization. It ends at `PUBLICATION_HOLD` until exact
  Relay publication authority exists.
- Main V2 remains paused. Its code, plans, and branch artifacts are donor evidence only unless Jim
  explicitly resumes that product.

## 5. Historical/non-routing families

Historical evidence remains evidence. Do not delete it merely because its routing conclusion is superseded.

Treat these as historical/non-routing unless current authority explicitly promotes a concrete capability:

- `docs/automation/TASK_*`
- dated canary/rehearsal/soak/closeout packets
- `docs/archive/**`
- old V6 execution-plan/status packets
- old browser/design QA evidence
- branch-specific handoffs
- prior generated status snapshots
- old Desktop Automation/SDK routine-editorial instructions
- protected `v1.0` release evidence.

## 6. Current-looking files that may contain stale historical wording

The active root spine listed in section 1 has been recompressed for the current corrected-PR42 state. Any older revision of those files is historical only.

Other current-looking families may still contain useful historical detail but cannot override the root spine, including:

- `docs/automation/CONTENTOPS_DAILY_LIVE_V1_NORTH_STAR.md`
- `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/**`
- `docs/status/CONTENTOPS_V1_FULL_AUTOMATION_NINE_SURFACE_HANDOFF_V1.md`
- `docs/status/CURRENT_FULL_AUTOMATION_FINAL_PRODUCT_STATUS.md`
- `docs/status/CONTENTOPS_V1_FINAL_PRODUCT_FOUR_WINDOW_CLOSED_LOOP_COMPLETION_EVIDENCE_V1.md`
- `docs/automation/CONTENTOPS_FINAL_PRODUCT_SCOPE_CLOSEOUT_AND_LAUNCH_MASTER_PLAN_V1.md`
- historical `CONTENTOPS_V1_FIRST_REAL_5_8_ARTICLE_PRODUCTION_DAY_V1/**` conclusions about zero-output success;
- old task/setup packets that infer current host state from configuration alone.

While the 2026-08-31 pause is current, these V2 product-detail files remain dormant design/history
and must not route implementation by themselves:

- `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_NORTH_STAR_V2.md`;
- `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_MASTER_PLAN_V2.md`;
- `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_TASK_GRAPH_V2.md`;
- `docs/automation/CONTENTOPS_V2_FREEFORM_CHAPTERIZED_HIGH_XHIGH_OWNER_OVERRIDE_V1.md`;
- `docs/automation/CONTENTOPS_V2_LANE_B_HYBRID_OWNER_DECISION_AND_AB_AUDIT_V1.md`;
- `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_CURRENT_EXECUTION_POINTER_V1.md`;
- `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_SUPERSESSION_MAP_V1.md`;
- `docs/status/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_DIRECTION_OVERLAY_V1.md`;
- `docs/status/CURRENT_PRODUCT_DIRECTION_EDITORIAL_EDGE_OVERLAY_V1.md`.

Their reusable technical evidence remains evidence. Their old exact-next tasks, after-V1 trigger,
worker policy, and sequencing are non-routing until a fresh Jim V2-resumption decision.

## 7. Stale-document handling rule

When a document contains both useful historical evidence and stale current-routing language:

1. preserve immutable historical evidence;
2. mark the file/family non-routing here and/or in the authority map;
3. rewrite actively read root/pointer files to current semantics;
4. do not resurrect a stale route merely because its artifact is detailed.

Legacy CI compatibility markers retained in current authority files are semantic regression anchors only; they do not revive the stale routes those labels historically described.

## 8. Hard current boundaries

- V1 product acceptance and routine article public-write/readback authority are already granted.
- Corrected PR #42 is repository/CI bridge proof only; it does not prove today's host account/session/readiness/recovery state or a new live public write.
- Exact current-host account/identity/readiness/recovery proof is still required before the first new live write.
- `UNKNOWN_WRITE = STOP RETRY -> READ BACK -> RECONCILE`.
- V2 public-write authority remains zero.
- Speech Highlight Relay public-write authority remains zero; current V1 article authority does not
  include Relay video uploads.
- Main V2 remains paused; the Relay is separate and cannot reactivate it.
- Protected historical `v1.0` remains immutable at `6983bfb3ef300414b744f3f8f97ca81ff699348b`.
