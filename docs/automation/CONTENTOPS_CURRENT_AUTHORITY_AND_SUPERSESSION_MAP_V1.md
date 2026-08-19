# Capital Chronicle ContentOps — Current Authority and Supersession Map V1

Authority date: 2026-08-20
Status: `CURRENT_ROOT_AUTHORITY_MAP`

This file prevents fresh sessions from treating historical plans, task handoffs, machine status, or unmerged branches as current routing.

## Canonical read path

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. this map
4. `docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md`
5. `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`
6. `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md`
7. `docs/codegraph/V1_CONTEXT.md` or `docs/codegraph/V2_CONTEXT.md`
8. current lane pointer
9. nearest scoped `AGENTS.md`
10. exact code/tests/evidence

CodeGraph's recorded `Source HEAD` is the newest commit that changed an indexed source, so it may legitimately differ from the current branch/master tip after generated-only or tree-identical merge commits. Do not infer staleness from that SHA mismatch alone. Use the deterministic generator/check or exact indexed-source digest on the ref being operated on; if it detects indexed-source drift, use CodeGraph only for discovery until regenerated.

## CURRENT_ROOT_AUTHORITY

- `AGENTS.md` — repository operating contract and authority hierarchy.
- `docs/automation/CONTENTOPS_CURRENT_AUTHORITY_AND_SUPERSESSION_MAP_V1.md` — this classification/routing map.
- `docs/automation/CONTENTOPS_CAPABILITY_ROUTED_HYBRID_EXECUTION_POLICY_V1.md` — current execution-routing policy; it changes execution mechanics only and cannot widen product/truth/public-write authority.
- `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md` — durable final-product objective and boundaries.
- `docs/automation/CONTENTOPS_FINAL_PRODUCT_MASTER_PLAN_V3.md` — ordered root capability plan and final acceptance criteria.
- `docs/CURRENT_CONTEXT.md` — compact bootstrap/current-status pointer; never stronger than the root files above.
- `docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md` — compact owner-direction pointer; subordinate to root authority.

## EXECUTION ROUTING SUPERSESSION

`CAPABILITY_ROUTED_HYBRID` is current execution routing on `master` and supersedes older `MAIN_CODEX only` wording **for execution routing only**.

The capability router is:

- `WEB_STATIC` for repository-static work provable from fresh GitHub bytes;
- `WEB_CI` for bounded implementation whose required mechanics can be proven by safe deterministic GitHub Actions;
- `CODEX_EXECUTION` when correctness requires an interactive runtime/environment/browser/debug loop;
- `OWNER_GATED_EXTERNAL` for secrets, live/public writes, destructive canonical changes, provider/browser publication expansion, legal/rights release boundaries, material Core Analyzer numeric-authority changes, or equivalent irreversible external actions.

Older `MAIN_CODEX only` execution statements in `docs/automation/CONTENTOPS_FINAL_PRODUCT_NORTH_STAR_V3.md`, `docs/CURRENT_CONTEXT.md`, `docs/status/CURRENT_PRODUCT_DIRECTION_OVERLAY.md`, current lane pointers, `video/AGENTS.md`, or V2 creative-policy documents are superseded only to the extent they conflict with this execution router. Their product, truth, numeric, rights, V1/V2 isolation, public-write, recovery, and actual-artifact acceptance rules remain in force.

No execution lane receives factual, numeric, Capital Chronicle/Core Analyzer, permission, credential, destination-identity, rights, or public-write authority by implication.

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

Generated CodeGraph is discovery tooling, not product authority. A recorded `Source HEAD` may legitimately lag the operated ref tip after generated-only or tree-identical merge commits. Treat CodeGraph as stale only when the deterministic check/source digest shows indexed-source drift; until regeneration, exact current code/tests/evidence outrank it.

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
- older `MAIN_CODEX only` wording where it conflicts with the owner-authorized capability router; execution-only supersession does not alter the product/safety meaning of the containing document.

## ARCHIVE_DELETE_CANDIDATE

Only delete a historical document later when all are true:

- it is redundant with another preserved artifact;
- it contains no unique accepted evidence/provenance;
- its only function is obsolete routing/handoff;
- deletion materially reduces context confusion.

Candidates should be reviewed in bounded cleanup batches. Do not delete accepted evidence, actual-media artifacts, or protected release records merely to reduce file count.

## Branch authority

A remote branch is not current repository authority merely because it is ahead of `master`. Jim may explicitly authorize a branch-scoped pilot or candidate policy without authorizing a merge. Product concepts may be implemented under the execution lane selected by the capability router when current product authority schedules them.

## Conflict resolution

When documents conflict:

1. Jim's latest explicit instruction wins.
2. Fresh GitHub refs/commits/diffs/exact code/evidence establish repository truth.
3. Root V3 authority governs product boundaries and sequence.
4. The current execution policy governs engineering execution routing only.
5. Current lane authority governs lane-specific product/implementation detail where compatible.
6. Historical plans/status/handoffs provide context, not routing.

No builder or Web lane should resurrect a superseded task or authority merely because its older plan is more detailed.
