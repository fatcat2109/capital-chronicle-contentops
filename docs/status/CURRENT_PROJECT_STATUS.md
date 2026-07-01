# Capital Chronicle ContentOps — Current Project Status

## last_updated_by_task
TASK_CONTENTOPS_V6_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW_HEAVY_BATCH_V0

## last_verified_repo
fatcat2109/capital-chronicle-contentops

## last_verified_branch
master

## last_verified_remote_sha
073e1488c035655519db1d6006c646ef67e23b20

## current_product_phase
V6 local-first platform variant final review and approval packet preview on the canonical V5 dashboard surface

## current_product_lane
platform variant final review and approval packet preview

## accepted_baseline_summary
Next article platform variant final review and approval packet preview completed and accepted after push/readback at `073e1488c035655519db1d6006c646ef67e23b20`; previous accepted baseline was `dbfd6e3bc6ec2cfc345a995383f9a74421b44cb7`. No live/provider/platform/LLM execution occurred.

## status_sha_model
- current remote HEAD verified before this docs/status refresh (`last_verified_remote_sha`): `073e1488c035655519db1d6006c646ef67e23b20`
- accepted product baseline (`accepted_product_baseline_sha`): `073e1488c035655519db1d6006c646ef67e23b20`
- previous accepted product baseline: `dbfd6e3bc6ec2cfc345a995383f9a74421b44cb7`
- Rule: feature commits may advance repo HEAD beyond the accepted product baseline; status-only repair commits update ledger metadata but do not become product baselines unless explicitly accepted.

## canonical_dashboard_surface
`ui/contentops_v5/` is the canonical current dashboard/app surface unless a newer committed authority document supersedes it.

Canonical entrypoint: `ui/contentops_v5/src/App.tsx`.
Canonical package: `ui/contentops_v5/package.json`.

V6 backend/read-model packets are allowed to exist, but canonical UI integration must target V5.

## legacy_ui_surfaces
- `ui/institutional_operator_cockpit_v4/` — fallback/reference only.
- `ui/institutional_operator_cockpit_v3/` — legacy reference.
- `ui/institutional_operator_cockpit_v2/` — legacy reference.
- `ui/institutional_shell/` — legacy sandbox reference.
- `ui/daily_content_studio/` — legacy sandbox reference.
- `ui/operator_evidence_intake_studio/` — specialized legacy/reference intake studio unless superseded by V5 integration.

## stale_or_deprecated_surfaces
- `ui/operator_approval_queue_evidence_vault/` is absent and is not canonical product UI.
- Standalone generated dashboards must not become canonical through convenience.

## current_v6_loop_status
V6 local deterministic loop components exist for research packets, canonical article drafts, manual distribution evidence registry/readiness summaries, Substack/LinkedIn/X manual publication evidence, operator-supplied feedback intake/backlog summary, and the local V5 feedback/backlog adapter regen/check guardrail. The canonical V5 dashboard remains `ui/contentops_v5/`.

## dispatch/live status
Dispatch/live remains blocked. No autonomous publish, schedule, retry, queue execution, platform API call, provider call, credential read, env value read, browser session read, DM, comment, like, reaction, or live send is authorized by this status ledger.

## provider/env/credential status
Provider/env/credential handling remains gated. Env/key presence may appear only as committed boolean/key-name evidence in approved tasks. No raw env values, credential values, webhook URLs, provider keys, browser session data, token material, cookie/localStorage/sessionStorage data, or secret-derived metadata may be printed or committed.

## active blockers
- Live/provider/platform execution remains disabled unless a future exact approved live task clears all gates.
- LinkedIn lane is fixture/operator-supplied evidence only; no API, browser automation, URL fetch/scrape, public URL verification, or platform action is authorized.
- Substack manual publication evidence remains fixture/operator-supplied where public URL or metrics evidence is present.
- Future product UI work must remain on `ui/contentops_v5/` unless a newer committed authority doc supersedes this ledger.
- Standalone approval queue UI must not be revived as canonical.

## accepted caveats
- GitHub remote commits and fetched repo files remain runtime authority above this status doc.
- If this status doc conflicts with GitHub remote or newer committed authority docs, the worker must stop and report BLOCKED for reconciliation.
- Do not use chat memory or Project Sources as runtime authority when status doc and repo files disagree.
- Project Sources are context only; GitHub remote and repo-local tests/evidence win.

## latest accepted task
TASK_CONTENTOPS_V6_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW_HEAVY_BATCH_V0

## latest changed areas
- `live_contentops/platform_variant_final_review_to_approval_packet_preview_v6.py`
- `live_contentops/platform_variant_approval_packet_preview_v5_adapter_codegen_v6.py`
- `docs/automation/V6_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW/`
- `tests/test_platform_variant_final_review_to_approval_packet_preview_v6.py`
- `tests/test_platform_variant_approval_packet_preview_ui_guardrail_v6.py`
- `tests/test_platform_variant_approval_packet_preview_v5_adapter_codegen_v6.py`
- `docs/runbooks/V6_PLATFORM_VARIANT_FINAL_REVIEW_TO_APPROVAL_PACKET_PREVIEW_RUNBOOK.md`
- `ui/contentops_v5/src/data/platformVariantApprovalPacketPreviewAdapter.ts`

## current next recommended task
TASK_CONTENTOPS_V6_APPROVAL_PACKET_PREVIEW_TO_DISPATCH_OUTBOX_DRY_RUN_HEAVY_BATCH_V0

## next-task safety notes
Read this status ledger and the JSON status file before planning. For UI work, target `ui/contentops_v5/`, not V4/static pages. Do not read env values, credentials, browser session data, provider keys, webhook URLs, cookies, local storage, or session storage. Do not dispatch or publish. Treat next-task text as a soft recommendation only.

## mandatory read-before-work files
- `docs/status/CURRENT_PROJECT_STATUS.md`
- `docs/status/current_project_status.json`
- `docs/status/DASHBOARD_SURFACE_AUTHORITY.md`
- `docs/status/STATUS_LEDGER_SHA_MODEL.md`
- `docs/status/STATUS_AND_PROGRESS_DOCS_MAP.md`

## mandatory update-after-work fields
- last_updated_by_task
- last_verified_remote_sha
- current_product_phase
- current_product_lane
- accepted_baseline_summary
- canonical_dashboard_surface when changed
- stale_or_deprecated_surfaces when changed
- current_v6_loop_status
- dispatch/live status
- provider/env/credential status
- active blockers
- latest accepted task
- latest changed areas
- current next recommended task

## Latest V6 LinkedIn Manual Publication Evidence Loop Update

- LinkedIn manual publication evidence loop is accepted as product baseline at `83c53fd3a39b377d9f74fa70cd8b6a5357689ecb`.
- Added deterministic LinkedIn manual export, approval/export evidence, operator handoff, URL/audit import, and manual metrics summary builders.
- Added committed sample packets under `docs/automation/V6_LINKEDIN_*`.
- Added runbooks and tests for every LinkedIn packet stage.
- Surfaced LinkedIn fixture evidence in canonical V5 Manual Export, Approval Queue, and Evidence Vault.
- LinkedIn API, browser automation, URL fetch/scrape/network verification, live publish, provider calls, dispatch/send/schedule/approve controls, DMs, comments, likes, reactions, env/credential reads, and browser-session access remain disabled/false.


## X Manual Publication Evidence Loop Update

- Current lane: X manual publication evidence loop integrated into canonical V5.
- Components: X manual export, approval/export evidence, operator handoff, URL/audit import, and manual metrics summary.
- Safety: fixture/operator-supplied only; `x_api_used=false`, `url_network_verified=false`, `metrics_network_verified=false`, no env/credential/browser session/network/live action.
- Baseline note: `accepted_product_baseline_sha` is now repaired to the pushed/readback X feature commit `98fce130a9f98e34cc8ac0454986081697efc8c1`.

## Manual Distribution Evidence Registry v0 Update

- Latest task: `TASK_CONTENTOPS_V6_MANUAL_DISTRIBUTION_EVIDENCE_REGISTRY_CONSOLIDATION_HEAVY_BATCH_V0`.
- Current lane: manual distribution evidence registry consolidation across Substack, LinkedIn, and X; no new platform lane.
- Canonical dashboard remains `ui/contentops_v5/`.
- Registry consolidates committed fixture/operator-supplied packet IDs, hashes, provenance, safety flags, blocked controls, and V5 labels.
- Accepted product baseline is `d86b0831f32de504288545edcf0321f89f9a1cbd` after registry feature push/readback; previous product baseline was `98fce130a9f98e34cc8ac0454986081697efc8c1`.
- Live/provider/platform execution remains blocked; Project Sources/chat memory remain context only.

## Manual Distribution Registry Operator Audit View Refinement

- Latest task: `TASK_CONTENTOPS_V6_MANUAL_DISTRIBUTION_REGISTRY_OPERATOR_AUDIT_VIEW_REFINEMENT_V0`.
- Current lane: registry operator audit view refinement on canonical `ui/contentops_v5/`.
- Scope: replace duplicated registry summary JSX with a reusable registry-first panel while preserving detailed evidence cards.
- Accepted product baseline is `9375e6ef8b5d109161f5e27350a8d458419e5809` after UI refinement push/readback; previous product baseline was `d86b0831f32de504288545edcf0321f89f9a1cbd`.
- Live/provider/platform execution remains blocked.

## Manual Distribution Registry Packet Drilldown Audit

- Latest task: `TASK_CONTENTOPS_V6_MANUAL_DISTRIBUTION_REGISTRY_PACKET_DRILLDOWN_AUDIT_V0`.
- Current lane: manual distribution registry packet drilldown audit on canonical `ui/contentops_v5/`.
- Scope: add read-only packet ID/hash drilldown for export, approval, handoff, URL audit, and metrics bindings across Substack, LinkedIn, and X.
- Accepted product baseline is `76f4ba616693aac1462e32dbbe80cc652154f928` after packet drilldown push/readback; previous product baseline was `9375e6ef8b5d109161f5e27350a8d458419e5809`.
- Live/provider/platform execution remains blocked.

## Manual Distribution Registry Packet Source-Path Audit

- Latest task: `TASK_CONTENTOPS_V6_MANUAL_DISTRIBUTION_REGISTRY_PACKET_SOURCE_PATH_AUDIT_V0`.
- Current lane: manual distribution registry packet source-path audit.
- Scope: deterministic local verification that every registry packet binding source path exists under `docs/automation/` and that packet IDs/hashes match source packet fields.
- Accepted product baseline is `16d29f86a1f81c8c39da1ccf8bac46623cf19c27` after source-path audit push/readback; previous product baseline was `76f4ba616693aac1462e32dbbe80cc652154f928`.
- Live/provider/platform execution remains blocked; canonical dashboard remains `ui/contentops_v5/`.

## Manual Distribution Registry Audit Index and Readiness Summary

- Latest task: `TASK_CONTENTOPS_V6_MANUAL_DISTRIBUTION_REGISTRY_AUDIT_INDEX_AND_READINESS_SUMMARY_V0`.
- Current lane: manual distribution registry audit index/readiness summary.
- Scope: bind registry and source-path audit packets into deterministic local operator-review readiness packet.
- Accepted product/audit baseline is `1796277bbcbf9a92c7bb54c5005678d3cbbf1e6c` after audit index push/readback; previous baseline was `16d29f86a1f81c8c39da1ccf8bac46623cf19c27`.
- Current loop components include Manual Distribution Registry source-path audit and audit index/readiness summary.
- Backend status modules include `live_contentops/manual_distribution_evidence_registry_source_path_audit_v6.py` and `live_contentops/manual_distribution_registry_audit_index_v6.py`.
- Live/provider/platform execution remains blocked; canonical dashboard remains `ui/contentops_v5/`.

## Manual Distribution Registry Audit Index UI Summary

- Latest task: `TASK_CONTENTOPS_V6_MANUAL_DISTRIBUTION_REGISTRY_AUDIT_INDEX_UI_SUMMARY_V0`.
- Current lane: manual distribution registry audit index UI summary.
- Scope: surface registry readiness, source-path audit status, blockers, caveats, non-readiness claims, and safety flags in canonical V5.
- Accepted product/audit baseline is `68ac1e1b8e3f6fb806515fe9ea0f26dc373fe2db` after audit index UI summary push/readback; previous baseline was `1796277bbcbf9a92c7bb54c5005678d3cbbf1e6c`.
- Live/provider/platform execution remains blocked; canonical dashboard remains `ui/contentops_v5/`.

## Manual Distribution Registry Audit Index Adapter Regen Guardrail

- Latest task: `TASK_CONTENTOPS_V6_OPERATOR_SUPPLIED_FEEDBACK_INTAKE_AND_BACKLOG_LOOP_V0`.
- Current lane: manual distribution registry audit-index adapter regen guardrail.
- Scope: add deterministic local V5 adapter regeneration/check guardrail for committed registry and audit-index packets.
- Accepted product/audit baseline is `3543afe8207bbb8c63eaa90fcbb0f413e57a0bcc` after guardrail push/readback; previous baseline was `68ac1e1b8e3f6fb806515fe9ea0f26dc373fe2db`.
- Final status repair commit updates governance metadata only and does not become the product/audit baseline.
- Live/provider/platform execution remains blocked; canonical dashboard remains `ui/contentops_v5/`.
## Operator-Supplied Feedback Intake and Backlog Loop

- Latest task: `TASK_CONTENTOPS_V6_OPERATOR_SUPPLIED_FEEDBACK_INTAKE_AND_BACKLOG_LOOP_V0`.
- Current lane: local/manual-only operator feedback and questions intake feeding deterministic next-article backlog candidates.
- Scope: feedback intake packet, backlog summary packet, runbook, focused tests, and canonical V5 Approval Queue/Evidence Vault read-only cards.
- Safety: operator-supplied fixture text only; no LLM/provider call, URL fetch/scrape, platform API, browser session read, env/credential read, live publish, send, approve, dispatch, schedule, reply, DM, like, repost, or quote-post.
- Accepted product/audit baseline is `184062956f4c70509ad1c14b63d7837d9bcb1c58` after feedback/backlog loop push/readback; previous baseline was `3543afe8207bbb8c63eaa90fcbb0f413e57a0bcc`.
