# Capital Chronicle ContentOps — Current Project Status

## last_updated_by_task
TASK_CONTENTOPS_V6_LINKEDIN_MANUAL_PUBLICATION_EVIDENCE_LOOP_V0

## last_verified_repo
fatcat2109/capital-chronicle-contentops

## last_verified_branch
master

## last_verified_remote_sha
fbfd64c8975df7b5ac2daa549641a4b8e31a90c5

## current_product_phase
V6 local-first product loop consolidation on the canonical V5 dashboard surface.

## current_product_lane
LinkedIn manual publication evidence loop integrated into canonical V5 with fixture-only export, approval/export evidence, operator handoff, URL/audit import, and manual metrics summary; no LinkedIn API/network/browser/publish actions.

## accepted_baseline_summary
Accepted product baseline before this lane is `fbfd64c8975df7b5ac2daa549641a4b8e31a90c5`. This task adds deterministic local LinkedIn manual publication evidence loop packets and canonical V5 visibility. All publication URLs and metrics are operator-supplied fixture evidence only; no LinkedIn API, browser automation, URL fetch/scrape/network verification, env/credential/session read, publish, dispatch, schedule, send, approve, DM, comment, like, or reaction is authorized.

## status_sha_model
- current remote HEAD verified before this feature lane (`last_verified_remote_sha`): `fbfd64c8975df7b5ac2daa549641a4b8e31a90c5`
- accepted product baseline (`accepted_product_baseline_sha`): `fbfd64c8975df7b5ac2daa549641a4b8e31a90c5` until the pushed LinkedIn feature commit is accepted by a later status-only repair/readback task.
- Rule: feature commits may advance repo HEAD beyond the accepted product baseline; status-only repair commits update ledger metadata but do not become new product baselines.

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
V6 local deterministic loop components exist for research packets, canonical article drafts, Substack manual publication evidence, and LinkedIn manual publication evidence. LinkedIn now includes manual post export, approval/export evidence, operator handoff, operator-supplied URL/audit import, and manual metrics summary packets. Fixture-only LinkedIn evidence cards are integrated into canonical V5 Manual Export, Approval Queue, and Evidence Vault.

## dispatch/live status
Dispatch/live remains blocked. No autonomous publish, schedule, retry, queue execution, platform API call, provider call, credential read, env value read, browser session read, DM, comment, like, reaction, or live send is authorized by this status ledger.

## provider/env/credential status
Provider/env/credential handling remains gated. Env/key presence may appear only as committed boolean/key-name evidence in approved tasks. No raw env values, credential values, webhook URLs, provider keys, browser session data, token material, cookie/localStorage/sessionStorage data, or secret-derived metadata may be printed or committed.

## active blockers
- Live/provider/platform execution remains disabled unless a future exact approved live task clears all gates.
- LinkedIn lane is fixture/operator-supplied evidence only; no API, browser automation, URL fetch/scrape, public URL verification, or platform action is authorized.
- Future product UI work must remain on `ui/contentops_v5/` unless a newer committed authority doc supersedes this ledger.
- Standalone approval queue UI must not be revived as canonical.

## accepted caveats
- GitHub remote commits and fetched repo files remain runtime authority above this status doc.
- If this status doc conflicts with GitHub remote or newer committed authority docs, the worker must stop and report BLOCKED for reconciliation.
- Do not use chat memory or Project Sources as runtime authority when status doc and repo files disagree.

## latest accepted task
TASK_CONTENTOPS_V6_LINKEDIN_MANUAL_PUBLICATION_EVIDENCE_LOOP_V0

## latest changed areas
- `live_contentops/linkedin_manual_export_v6.py`
- `live_contentops/linkedin_manual_approval_export_evidence_v6.py`
- `live_contentops/linkedin_manual_operator_handoff_v6.py`
- `live_contentops/linkedin_manual_publication_url_audit_import_v6.py`
- `live_contentops/linkedin_publication_audit_review_metrics_summary_v6.py`
- `docs/automation/V6_LINKEDIN_*`
- `docs/runbooks/V6_LINKEDIN_*`
- `tests/test_linkedin_*_v6.py`
- `ui/contentops_v5/src/data/substackManualExportArticleStudioAdapter.ts`
- `ui/contentops_v5/src/views/ManualExportPilotVerification.tsx`
- `ui/contentops_v5/src/views/ApprovalQueue.tsx`
- `ui/contentops_v5/src/views/EvidenceVault.tsx`
- `docs/status/CURRENT_PROJECT_STATUS.md`
- `docs/status/current_project_status.json`

## current next recommended task
TASK_CONTENTOPS_V6_LINKEDIN_PUBLICATION_EVIDENCE_LOOP_ACCEPTANCE_OR_NEXT_LANE_V0

## next-task safety notes
Read this status ledger and the JSON status file before planning. For UI work, target `ui/contentops_v5/`, not V4/static pages. Do not read env values, credentials, browser session data, provider keys, webhook URLs, cookies, local storage, or session storage. Do not dispatch or publish.

## mandatory read-before-work files
- `docs/status/CURRENT_PROJECT_STATUS.md`
- `docs/status/current_project_status.json`
- `docs/status/DASHBOARD_SURFACE_AUTHORITY.md`
- `docs/status/STATUS_LEDGER_SHA_MODEL.md`

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

- Added deterministic LinkedIn manual export, approval/export evidence, operator handoff, URL/audit import, and manual metrics summary builders.
- Added committed sample packets under `docs/automation/V6_LINKEDIN_*`.
- Added runbooks and tests for every LinkedIn packet stage.
- Surfaced LinkedIn fixture evidence in canonical V5 Manual Export, Approval Queue, and Evidence Vault.
- LinkedIn API, browser automation, URL fetch/scrape/network verification, live publish, provider calls, dispatch/send/schedule/approve controls, DMs, comments, likes, reactions, env/credential reads, and browser-session access remain disabled/false.
