# Capital Chronicle ContentOps — Current Authority and Supersession Map V1

Authority date: 2026-08-19
Status: `CURRENT_ROOT_AUTHORITY_MAP`

This file prevents fresh sessions from treating historical plans, task handoffs, machine status, or unmerged branches as current routing.

## Canonical read path

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. this map
4. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
5. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`
6. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md`
7. current lane pointer
8. nearest scoped `AGENTS.md`
9. exact code/tests/evidence

If CodeGraph's recorded source HEAD differs from freshly fetched `master`, use it only for discovery until regenerated.

## CURRENT_ROOT_AUTHORITY

- `AGENTS.md` — repository operating contract and authority hierarchy.
- `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md` — this classification/routing map.
- `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md` — durable final-product objective and boundaries.
- `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md` — ordered root capability plan and final acceptance criteria.
- `docs/CURRENT_CONTEXT.md` — compact bootstrap/current-status pointer; never stronger than the four files above.
- `docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md` — compact owner-direction pointer; subordinate to root authority.

## CURRENT_LANE_AUTHORITY

### V1

- `docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_CURRENT_EXECUTION_POINTER_V3.md` — current V1 lane pointer and exact root-compatible acceptance sequence.
- `docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_NORTH_STAR.md` — durable V1 product detail where compatible with root V3.
- `docs/automation/CONTENTOPS_FINAL_DAILY_APP_V1_MASTER_PLAN.md` — V1 implementation/runtime detail where compatible with root V3.
- `docs/status/CONTENTOPS_V1_FULL_AUTOMATION_NINE_SURFACE_HANDOFF_V1.md` — current implementation/status evidence only; it does not override root sequencing.

Any statement inside older V1 material that V2 must remain deferred until a full V1 freeze is superseded by root V3. V1 runtime/publication authority itself remains unchanged.

### V2

- `docs/automation/CONTENTOPS_TIER2_PRO_VIDEO_FACTORY_NORTH_STAR_V1.md` — V2 durable creative/product detail where compatible with root V3.
- `docs/automation/CONTENTOPS_V2_PRO_VIDEO_FACTORY_MASTER_PLAN_V1.md` — V2 architecture/creative detail where compatible with root V3.
- `docs/automation/CONTENTOPS_V2_FINAL_PRODUCT_TASK_GRAPH_V1.md` — current capability graph; not an independent task/publication grant.
- `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_CURRENT_EXECUTION_POINTER_V2.md` — current lane pointer, subordinate to root V3 and zero-public-write root boundary.
- `docs/automation/CONTENTOPS_V2_FREEFORM_CHAPTERIZED_HIGH_XHIGH_OWNER_OVERRIDE_V1.md` — current creative-worker policy detail only; no independent task/publication authority.
- `video/AGENTS.md` — scoped implementation rules, subordinate to root authority.

No V2 document, adapter, credential, or branch grants video public-write authority. Root V3 currently grants zero.

## CURRENT_IMPLEMENTATION_CONTEXT

- `docs/codegraph/INDEX.md`
- `docs/codegraph/V1_CONTEXT.md`
- `docs/codegraph/V2_CONTEXT.md`
- nearest scoped `AGENTS.md`
- exact implementation modules, tests, current evidence packets, and real rendered/public artifacts.

As of this authority rewrite, generated CodeGraph context predates current `master` and must be regenerated/checkpointed before the next implementation task. It remains useful only as a call-path/discovery aid until refreshed.

## HISTORICAL_EVIDENCE_ONLY

These families may contain durable evidence but must never route a fresh task by themselves:

- completed `docs/automation/TASK_*` evidence folders;
- dated canary/rehearsal/soak/closeout packets;
- historical publication/readback/media artifacts;
- protected `v1.0` release evidence;
- `docs/archive/**`;
- old design/browser QA evidence;
- prior generated status snapshots;
- historical strategy/recovery maps;
- branch-specific handoffs after their implementation has merged or been superseded.

Historical evidence remains valuable for regression comparison, audit, and provenance. It is not current sequencing authority.

## SUPERSEDED_NON_ROUTING

The following working-tree families are explicitly non-routing after this rewrite:

- `docs/CONTENTOPS_OPERATING_RULES_AND_DESIGN_SYSTEM_GOVERNANCE.md` — legacy operating/framework instructions; retained only as a historical supersession marker.
- `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md` — older V1-first/V2-deferred routing summary; root V3 supersedes its sequencing.
- `docs/automation/CONTENTOPS_V2_FRESH_CHAT_HANDOFF_V1.md` — prior task handoff; retained only as a redirect to current authority.
- any status/pointer document whose exact task/branch/HEAD conflicts with this map, root V3, or a freshly fetched GitHub ref.
- any old plan that assigns model/factual/numeric/public-write authority more broadly than root V3.

## ARCHIVE_DELETE_CANDIDATE

Only delete a historical document later when all are true:

- it is redundant with another preserved artifact;
- it contains no unique accepted evidence/provenance;
- its only function is obsolete routing/handoff;
- deletion materially reduces context confusion.

Candidates should be reviewed in bounded cleanup batches. Do not delete accepted evidence, actual-media artifacts, or protected release records merely to reduce file count.

## Branch authority

A remote branch is not current authority merely because it is ahead of `master`. Unmerged experimental branch work is historical/non-authoritative unless Jim explicitly accepts it under current root authority. Product concepts may be independently rebuilt under `MAIN_CODEX` when root V3 schedules them.

## Conflict resolution

When documents conflict:

1. Jim's latest explicit instruction wins.
2. Fresh GitHub refs/commits/diffs/exact code/evidence establish repository truth.
3. Root V3 authority governs product boundaries and sequence.
4. Current lane authority governs lane-specific implementation detail only where compatible.
5. Historical plans/status/handoffs provide context, not routing.

No builder should resurrect a superseded task merely because its plan is more detailed.
