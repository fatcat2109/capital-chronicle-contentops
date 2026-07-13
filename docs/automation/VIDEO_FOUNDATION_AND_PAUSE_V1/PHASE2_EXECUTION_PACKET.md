# Phase 2 Execution Packet

## Task label

`TASK_CONTENTOPS_VIDEO_FOUNDATION_DEEP_REPO_DISCOVERY_AND_EXECUTION_PACKET_V1`

## Phase 1 terminal classification

`PASS_VIDEO_FOUNDATION_DEEP_REPO_DISCOVERY_AND_EXECUTION_PACKET_V1`

Phase 1 local validation passed. Fresh provider-document validation is deferred under the operator override because this packet authorizes no provider execution and no posting. `LIVE_PROVIDER_DOC_REVALIDATION_REQUIRED_BEFORE_PROVIDER_INTEGRATION` remains mandatory. This packet defines Phase 2 but does not authorize it.

---

## 1. Verified starting authority

- Repo: `fatcat2109/capital-chronicle-contentops`
- Branch: `master`
- Verified local HEAD: `821450d0f2b5a18051a1bc684bea2a4709a5ba01`
- Verified upstream: `origin/master`
- Verified remote HEAD: `821450d0f2b5a18051a1bc684bea2a4709a5ba01`
- Expected commit matched: yes
- Tags at HEAD: none
- Unrelated drift preserved: `exports/daily_contentops/fed_funds_policy_signal_article_v1.md`

### Database milestone and independent ContentOps gate

The upstream public/free v1 database foundation is complete and analyzer handoff is ready at `c14e5a7f48d1d949da60c217c4467c2418f1fbf6`, with zero gating and unadjudicated blockers. Its analyzer task `TASK_ANALYZER_FORECAST_INPUT_FABRIC_INTEGRATION_V1` belongs to the database/analyzer program, not ContentOps.

ContentOps remains `FROZEN_WAITING_FOR_PUBLICATION_ELIGIBLE_UPSTREAM_EVIDENCE` because the packet also states `dqr=BLOCKED`, `exact_authority_sufficient=false`, `forecast_runtime_ready=false`, `current_canonical_apply=false`, `broker_execution_ready=false`, and `institutional_exact_authority_complete=false`. Resume route remains `RESUME_TASK_CONTENTOPS_FINAL_AUTOMATION_PIPELINE_CLOSURE_AFTER_UPSTREAM_DQR_STATE_CHANGE` and additionally requires publication permission and freshness evidence.

---

## 2. Exact Phase 2 objective

Build a **local, deterministic, non-posting video foundation and text/image lane pause package** that:

1. introduces a machine-readable lane lock for the canonical text/image public-dispatch lane;
2. keeps prepare-only and read-only reconciliation paths available;
3. defines a canonical explicit video runner and CLI surface;
4. reuses existing chart/media infrastructure and FFmpeg for local proof rendering;
5. adds request-builder boundaries for YouTube and TikTok without live uploads;
6. adds provider abstractions for TTS and avatar systems without live provider calls;
7. adds schemas, tests, and docs so later execution does not rely on chat memory.

Phase 2 must **not** silently wire video into the default text/image runner.

---

## 3. Required architecture decisions resolved from repo evidence

## 3.1 Canonical text/image lane lock design

### Decision

Introduce a dedicated machine-readable lane-lock artifact that is consulted by the canonical runner before any path that can write to public/platform destinations.

### Proposed location

- `docs/automation/VIDEO_FOUNDATION_AND_PAUSE_V1/text_image_lane_lock_v1.json`

### Proposed runtime reader module

- new: `live_contentops/text_image_lane_lock_v1.py`

### Why this location

- it is an automation authority artifact, not a secret;
- `docs/automation/` already houses machine-readable operational contracts;
- this keeps pause semantics explicit, reviewable, and versionable;
- it avoids overloading canonical status docs with a runtime switch.

### Minimal schema

```json
{
  "schema_version": "contentops.text_image_lane_lock.v1",
  "lock_status": "LOCKED" | "UNLOCKED",
  "reason": "<human-readable reason>",
  "allowed_safe_modes": [
    "prepare_generic_fabric",
    "build_operator_audit_packet",
    "reconcile_readbacks",
    "closure_release_verify",
    "video_capability_audit",
    "local_video_proof_render"
  ],
  "blocked_public_modes": [
    "text_image_live_run",
    "resume_derivatives",
    "linkedin_pair_reconciliation",
    "closure_historical_repair",
    "finalize_v1_tag"
  ],
  "updated_at_utc": "<timestamp>",
  "updated_by_task": "<task>"
}
```

## 3.2 How public dispatch is blocked while safe modes remain available

### Decision

The lane lock must be checked inside [live_contentops/eight_platform_substack_first_pipeline_v1.py](live_contentops/eight_platform_substack_first_pipeline_v1.py) before any public-write branch is entered.

### Branches to block

- default live run path
- `--resume-derivatives`
- `--reconcile-linkedin-pair`
- `--closure-historical-repair`
- `--finalize-v1-tag`

### Branches to keep available

- `--prepare-generic-fabric`
- `--build-operator-audit-packet`
- `--reconcile-readbacks`
- `--closure-release-verify`
- future explicit local video proof-render mode
- future request-builder-only video modes

### Why

The current runner exposes multiple indirect write paths; blocking only the default live run would leave bypasses.

## 3.3 Resume authorization without a generic bypass flag

### Decision

Do not introduce a broad `--ignore-lock` flag. Instead:

- lock-aware resume authorization must be narrow and mode-specific;
- a future unlock should be represented by changing the machine-readable lock artifact or by passing an exact reviewed authorization artifact for a specific blocked mode.

### Phase 2 scope

Implement only the lock check and structured blocked output. Do not design a generic bypass flag.

## 3.4 Canonical video runner and CLI shape

### Decision

Add a dedicated video runner module rather than further expanding [live_contentops/eight_platform_substack_first_pipeline_v1.py](live_contentops/eight_platform_substack_first_pipeline_v1.py).

### Proposed module

- new: `live_contentops/video_foundation_runner_v1.py`

### Proposed CLI modes

```text
python -m live_contentops.video_foundation_runner_v1 \
  --run-id <id> \
  --output-dir <dir> \
  --proof-render-local \
  --scene-graph <scene_graph.json>
```

Additional explicit non-posting modes:

- `--build-scene-graph`
- `--build-youtube-request`
- `--build-tiktok-request`
- `--build-provider-request --provider elevenlabs`
- `--build-provider-request --provider heygen`
- `--build-provider-request --provider d_id`
- `--validate-video-packet`

No upload mode in Phase 2.

## 3.5 Short-form vs long-form assignment contracts

### Decision

Use separate explicit assignment contracts.

### Proposed file

- new: `live_contentops/video_assignment_contract_v1.py`

### Contract split

- `short_form_vertical`
  - targets Shorts/TikTok style outputs
  - capped duration and vertical-safe composition
- `long_form_video`
  - future YouTube long-form path
  - different metadata, disclosure, and pacing requirements

## 3.6 Scene graph schema

### Decision

Represent proof renders as deterministic scene graphs bound to evidence/media manifests.

### Proposed file

- new: `live_contentops/video_scene_graph_v1.py`

### Required schema responsibilities

- scene order
- source chart/image references
- per-scene duration
- caption/subtitle text blocks
- claim references
- credit footer/source references
- output aspect and frame spec

## 3.7 Claim-to-script binding

### Decision

Script lines must bind to approved claims by ID, mirroring the article evidence model.

### Proposed file

- new: `live_contentops/video_claim_script_binding_v1.py`

### Rule

No narration/subtitle/script segment should exist without:
- evidence claim IDs,
- source references,
- or explicit non-claim framing tags such as `context`, `transition`, `disclaimer`.

## 3.8 Visual manifest and rights model

### Decision

Reuse and extend [live_contentops/media_manifest_authority_v1.py](live_contentops/media_manifest_authority_v1.py) rather than create a second unrelated media authority system.

### Extend with video-facing packet

- new: `live_contentops/video_media_manifest_v1.py`

### Responsibilities

- chart/image/video asset IDs
- sha256 continuity
- rights status
- source provenance
- whether an asset is allowed in proof render only vs future upload-ready mode

## 3.9 Provider abstraction decision

### Decision

Use a single consolidated boundary module rather than multiple tiny provider-specific modules.

### Proposed file

- new: `live_contentops/video_provider_boundaries_v1.py`

### Why consolidation is better

The current packet had over-fragmented proposed modules. A single provider-boundary file is more coherent for Phase 2 because:

- all provider work is request-builder/schema only;
- no provider runtime execution is allowed in Phase 2;
- grouping TTS/avatar/YouTube/TikTok packet shapes keeps the non-posting boundary easier to reason about.

### Planned responsibilities inside one boundary module

- ElevenLabs request packet schema
- HeyGen request packet schema
- D-ID fallback request packet schema
- YouTube request-builder packet schema
- TikTok request-builder packet schema

## 3.10 Subtitle and source-credit pipeline

### Decision

Subtitles and credits should be local deterministic artifacts generated from the scene graph and claim bindings.

### Proposed files

- new: `live_contentops/video_subtitle_pipeline_v1.py`
- new: `live_contentops/video_source_credit_packet_v1.py`

## 3.11 Deterministic QA

### Decision

Every local proof render should emit a QA packet instead of relying only on human inspection.

### Proposed file

- new: `live_contentops/video_proof_render_qa_v1.py`

### Checks

- output file exists
- expected duration within tolerance
- expected resolution/aspect
- source assets all present
- claim/script segments all bound
- subtitle packet present
- disclosure/footer present
- no network/public write performed

## 3.12 Local metadata probing

### Decision

Introduce a dedicated local video metadata probe because no ffprobe-backed equivalent exists today.

### Proposed file

- new: `live_contentops/video_metadata_probe_v1.py`

### Scope

- local-only probing of width/height/duration/container metadata
- no provider/platform behavior

## 3.13 Operator router

### Decision

Add a simple local operator router that points users to the correct explicit mode and refuses ambiguous public-write requests while lock is active.

### Proposed file

- new: `live_contentops/video_operator_router_v1.py`

## 3.14 Large media artifact policy

### Decision

Do not commit arbitrary large proof renders by default.

### Policy

- commit only bounded, intentionally small, canonical proof artifacts when explicitly needed;
- prefer JSON manifests/metadata over binary accumulation;
- default proof render path should target a bounded docs/automation output area and keep file size small.

---

## 4. Exact files to reuse

### Must reuse directly

- `live_contentops/eight_platform_substack_first_pipeline_v1.py`
- `live_contentops/generic_editorial_fabric_v2.py`
- `live_contentops/cc_evidence_bridge_v2.py`
- `live_contentops/freshness_market_state_v2.py`
- `live_contentops/editorial_visual_research_v2.py`
- `live_contentops/editorial_review_orchestrator_v2.py`
- `live_contentops/distribution_identity_registry_v2.py`
- `live_contentops/media_manifest_authority_v1.py`
- `live_contentops/source_chart_short_video_v1.py`
- `live_contentops/video_platform_capability_matrix_v1.py`
- `live_contentops/edge_cdp_publishing_adapter_v1.py` as capability-boundary reference only
- `live_contentops/macro_chart_renderer_v6.py`

### Must reuse as authority docs/evidence

- `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/platform_delivery_contract_v1.json`
- `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/distribution_identity_persona_registry_v2.json`
- `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/source_evidence_capability_registry_v2.json`
- `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/generic_evidence_freshness_visual_editorial_fabric_v2.md`
- `docs/status/CURRENT_PROJECT_STATUS.md`
- `docs/status/current_project_status.json`
- `docs/automation/FINAL_AUTOMATION_PIPELINE_CLOSURE_V1/contentops_final_closure_20260711_1/*`
- `docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/*`

---

## 5. Exact files to modify in Phase 2

### Runtime files to modify

1. `live_contentops/eight_platform_substack_first_pipeline_v1.py`
2. `live_contentops/video_platform_capability_matrix_v1.py`
3. `live_contentops/source_chart_short_video_v1.py`
4. `live_contentops/media_manifest_authority_v1.py`

### Documentation files to update in Phase 2

- `AGENTS.md`
- `docs/AI_BUILDER_BOOTSTRAP.md`
- `docs/status/CURRENT_PROJECT_STATUS.md`
- `docs/status/current_project_status.json`
- `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md`
- `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md`
- `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_supersession_map.md`
- `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md`
- `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/platform_delivery_contract_v1.json`
- `docs/automation/VIDEO_FOUNDATION_AND_PAUSE_V1/*`

---

## 6. Proposed new files for Phase 2

### Core pause / lock

- `live_contentops/text_image_lane_lock_v1.py`
- `docs/automation/VIDEO_FOUNDATION_AND_PAUSE_V1/text_image_lane_lock_v1.json`

### Canonical video foundation

- `live_contentops/video_foundation_runner_v1.py`
- `live_contentops/video_assignment_contract_v1.py`
- `live_contentops/video_scene_graph_v1.py`
- `live_contentops/video_claim_script_binding_v1.py`
- `live_contentops/video_media_manifest_v1.py`
- `live_contentops/video_subtitle_pipeline_v1.py`
- `live_contentops/video_source_credit_packet_v1.py`
- `live_contentops/video_proof_render_qa_v1.py`
- `live_contentops/video_provider_boundaries_v1.py`
- `live_contentops/video_operator_router_v1.py`
- `live_contentops/video_metadata_probe_v1.py`

### Tests

- `tests/test_text_image_lane_lock_v1.py`
- `tests/test_video_foundation_runner_v1.py`
- `tests/test_video_assignment_contract_v1.py`
- `tests/test_video_scene_graph_v1.py`
- `tests/test_video_claim_script_binding_v1.py`
- `tests/test_video_media_manifest_v1.py`
- `tests/test_video_subtitle_pipeline_v1.py`
- `tests/test_video_source_credit_packet_v1.py`
- `tests/test_video_proof_render_qa_v1.py`
- `tests/test_video_provider_boundaries_v1.py`
- `tests/test_video_metadata_probe_v1.py`
- `tests/test_text_image_runner_pause_guard_v1.py`

---

## 7. File-by-file implementation sequence

## Step 1 — pause lock foundation

1. Add `text_image_lane_lock_v1.json`
2. Add `live_contentops/text_image_lane_lock_v1.py`
3. Update `live_contentops/eight_platform_substack_first_pipeline_v1.py` to read lock and fail closed on public-write branches
4. Add tests proving safe branches still work and blocked branches fail closed

## Step 2 — canonical video contract layer

1. Add `video_assignment_contract_v1.py`
2. Add `video_scene_graph_v1.py`
3. Add `video_claim_script_binding_v1.py`
4. Add tests for contract validation and fail-closed behavior

## Step 3 — local render foundation

1. Add `video_metadata_probe_v1.py`
2. Extend or wrap `source_chart_short_video_v1.py` for proof-render orchestration
3. Add `video_media_manifest_v1.py`
4. Add `video_proof_render_qa_v1.py`
5. Add proof-render tests and a bounded local artifact fixture path

## Step 4 — subtitle and credit sidecars

1. Add `video_subtitle_pipeline_v1.py`
2. Add `video_source_credit_packet_v1.py`
3. Add validation tests

## Step 5 — consolidated provider/request boundaries only

1. Add `video_provider_boundaries_v1.py`
2. Define request-builder packet schemas for ElevenLabs, HeyGen, D-ID, YouTube, TikTok
3. Keep all provider work non-posting and fixture-testable only

## Step 6 — canonical video runner

1. Add `video_foundation_runner_v1.py`
2. Add `video_operator_router_v1.py`
3. Add CLI proof-render and request-builder modes
4. Add tests ensuring no upload/platform write occurs

## Step 7 — docs reconciliation

1. Update builder/bootstrap/status/plan docs
2. Update platform contract to reflect lane lock + explicit video lane
3. Update the `VIDEO_FOUNDATION_AND_PAUSE_V1/` package with final implemented command references

---

## 8. Test matrix for Phase 2

### Existing tests to keep green

- `tests/test_eight_platform_substack_first_pipeline_v1.py`
- `tests/test_video_platform_capability_matrix_v1.py`
- `tests/test_source_chart_short_video_v1.py`
- `tests/test_media_manifest_authority_v1.py`
- `tests/test_macro_chart_renderer_v6.py`
- `tests/test_edge_cdp_publishing_adapter_v1.py`
- `tests/test_generic_evidence_freshness_visual_editorial_fabric_v2.py`

### New focused tests

- lane lock behavior on all blocked/safe branches
- scene graph schema validation
- claim/script binding coverage
- subtitle packet generation
- source-credit packet generation
- local video metadata probing
- proof-render QA packet generation
- consolidated provider-boundary packet generation
- regression proving default text/image runner still does **not** call Shorts/video upload helpers

---

## 9. Local proof-render plan

### Goal

Produce a bounded, deterministic, non-production proof render only.

### Input strategy

Use existing committed chart/image evidence from:
- `docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/`
- or analogous current local fixture assets

### Output strategy

Write to a bounded docs/automation proof-render directory under the new package.

### Artifact expectations

- small vertical mp4
- scene graph JSON
- subtitle sidecar
- credits sidecar
- QA packet
- no upload / no publication

---

## 10. Freeze verification plan

Phase 2 must explicitly prove:

1. default text/image runner blocks public run when lock is active;
2. derivative resume blocks when lock is active;
3. historical repair blocks when lock is active;
4. prepare-generic-fabric still runs;
5. reconcile-readbacks still runs;
6. build-operator-audit-packet still runs;
7. no YouTube Shorts/TikTok helpers are reachable from the default text/image lane;
8. no canonical/frozen public repair evidence is mutated during video-foundation work.

---

## 11. Known risks

1. `eight_platform_substack_first_pipeline_v1.py` is already very large; careless edits could destabilize current text/image behavior.
2. Existing Python image/chart dependencies appear used but not fully formalized in manifests.
3. Fresh official docs for ElevenLabs/HeyGen/D-ID and current YouTube/TikTok details were not re-fetched in this session.
4. Binary proof-render artifacts can bloat the repo if not tightly bounded.
5. A weak pause design could block safe read-only modes or leave indirect write paths open.

---

## 12. Deferred prerequisites and authorization

- Phase 1 blockers: none.
- Deferred prerequisite: `LIVE_PROVIDER_DOC_REVALIDATION_REQUIRED_BEFORE_PROVIDER_INTEGRATION`.
- Phase 2 authorization: not granted by this closeout.
- Live provider or platform execution: prohibited.

---

## 13. Acceptance criteria for Phase 2

Phase 2 is complete when all of the following are true:

1. machine-readable text/image lane lock exists;
2. canonical runner enforces it on every public-write text/image path;
3. safe non-write branches remain available;
4. dedicated canonical video runner exists;
5. scene graph, assignment, claim-script, subtitle, credit, media-manifest, and QA schemas exist;
6. local proof-render path works without network/platform writes;
7. consolidated provider/request boundaries exist but do not call providers;
8. existing regression test proving default runner does not call Shorts/video helpers still passes;
9. docs are reconciled and path-specific;
10. no public evidence history is mutated beyond intended docs/planning/runtime foundation changes.

---

## 14. Explicit no-write boundary for Phase 2

Phase 2 must not:

- publish to Substack or social platforms;
- upload public or private video to YouTube/TikTok;
- call ElevenLabs, HeyGen, or D-ID;
- mutate ingestion repo state;
- create or push release tags;
- rerun frozen public repairs automatically.

It may only:

- write local code/tests/docs,
- perform local proof renders,
- build local request packets,
- run local tests/validation,
- update canonical documentation to reflect the new local-only foundation and lane-lock semantics.
