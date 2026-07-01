# Capital Chronicle ContentOps — Current Project Status

## last_updated_by_task
TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_EXPORT_OPERATOR_HANDOFF_PACKET_V0

## last_verified_repo
fatcat2109/capital-chronicle-contentops

## last_verified_branch
master

## last_verified_remote_sha
af911eaf3fd1f0a85878ccb73361379732a7595b

## current_product_phase
V6 local-first product loop consolidation on the canonical V5 dashboard surface.

## current_product_lane
Substack manual export operator handoff integrated into the canonical V5 dashboard using fixture-only packets, deterministic hashes, pending operator review, and blocked live publish proof.

## accepted_baseline_summary
Accepted product baseline is commit `af911eaf3fd1f0a85878ccb73361379732a7595b` on `origin/master`. This commit adds deterministic Substack manual export operator handoff packet and canonical V5 fixture-only visibility. Live publish, Substack/API/provider calls, env/credential reads, browser-session access, dispatch, send, schedule, and approve controls remain blocked. The next status-only repair commit may advance repo HEAD and must be reported separately in final evidence, not promoted as a product baseline.


## status_sha_model
- current remote HEAD verified before this status-only repair (`last_verified_remote_sha`): `af911eaf3fd1f0a85878ccb73361379732a7595b`
- accepted product baseline (`accepted_product_baseline_sha`): `af911eaf3fd1f0a85878ccb73361379732a7595b`
- status-only repair commit (`last_status_commit_sha`): `84c65844a5ae55178463390fb29d8d9325cf2771` until this repair commit is accepted; final evidence must report the new repo HEAD separately.
- Rule: status-only SHA repair commits update ledger metadata but do not become new product baselines. This prevents infinite SHA-repair loops.

## canonical_dashboard_surface
`ui/contentops_v5/` is the canonical current dashboard/app surface unless a newer committed authority document supersedes it.

Canonical entrypoint: `ui/contentops_v5/src/App.tsx`.
Canonical package: `ui/contentops_v5/package.json`.

V6 backend/read-model packets are allowed to exist, but canonical UI integration must target V5.

## legacy_ui_surfaces
- `ui/institutional_operator_cockpit_v4/` — fallback/reference only; cleaned of the non-canonical V6 approval/evidence product integration.
- `ui/institutional_operator_cockpit_v3/` — legacy reference.
- `ui/institutional_operator_cockpit_v2/` — legacy reference.
- `ui/institutional_shell/` — legacy sandbox reference.
- `ui/daily_content_studio/` — legacy sandbox reference.
- `ui/operator_evidence_intake_studio/` — specialized legacy/reference intake studio unless superseded by V5 integration.

## stale_or_deprecated_surfaces
- `ui/operator_approval_queue_evidence_vault/` is absent and is not canonical product UI.
- Standalone generated dashboards must not become canonical through convenience.

## current_v6_loop_status
V6 local deterministic loop components exist for research packets, canonical article drafts, Substack manual export packets, Substack manual export operator handoff packets, editorial review, variant preview/hash approval, Discord dry-run outbox, redacted audit, manual fallback, approval queue/evidence vault packets, and live-pilot blocked/ready state. Fixture-only V6 approval/evidence, Substack article studio, and Substack manual export operator handoff cards are integrated into the canonical V5 dashboard views.

## dispatch/live status
Dispatch/live remains blocked. No autonomous publish, schedule, retry, queue execution, platform API call, provider call, credential read, env value read, or live send is authorized by this status ledger.

## provider/env/credential status
Provider/env/credential handling remains gated. Env/key presence may appear only as committed boolean/key-name evidence in approved tasks. No raw env values, credential values, webhook URLs, provider keys, browser session data, token material, or secret-derived metadata may be printed or committed.

## active blockers
- Live/provider/platform execution remains disabled unless a future exact approved live task clears all gates.
- Future product UI work must remain on `ui/contentops_v5/` unless a newer committed authority doc supersedes this ledger.
- Standalone approval queue UI must not be revived as canonical.

## accepted caveats
- GitHub remote commits and fetched repo files remain runtime authority above this status doc.
- If this status doc conflicts with GitHub remote or newer committed authority docs, the worker must stop and report BLOCKED for reconciliation.
- Do not use chat memory or Project Sources as runtime authority when status doc and repo files disagree.

## latest accepted task
TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_EXPORT_OPERATOR_HANDOFF_PACKET_V0

## latest changed areas
- `live_contentops/substack_manual_approval_export_evidence_v6.py`
- `tests/test_substack_manual_approval_export_evidence_v6.py`
- `docs/automation/V6_SUBSTACK_MANUAL_APPROVAL_EXPORT_EVIDENCE/`
- `docs/runbooks/V6_SUBSTACK_MANUAL_APPROVAL_EXPORT_EVIDENCE_RUNBOOK.md`
- `ui/contentops_v5/src/data/substackManualExportArticleStudioAdapter.ts`
- `ui/contentops_v5/src/views/SubstackArticleStudioCard.tsx`
- `ui/contentops_v5/src/views/ApprovalQueue.tsx`
- `ui/contentops_v5/src/views/EvidenceVault.tsx`
- `docs/browser_qa/contentops_v5_substack_manual_approval_export_evidence/`
- `docs/status/CURRENT_PROJECT_STATUS.md`
- `docs/status/current_project_status.json`

## current next recommended task
TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_EXPORT_OPERATOR_HANDOFF_PACKET_V0

## next-task safety notes
Read this status ledger and the JSON status file before planning. For UI work, target `ui/contentops_v5/`, not V4/static pages. Do not read env values, credentials, browser session data, provider keys, webhook URLs, cookies, or local storage. Do not dispatch or publish.

## mandatory read-before-work files
- `docs/status/CURRENT_PROJECT_STATUS.md`
- `docs/status/current_project_status.json`
- `docs/status/DASHBOARD_SURFACE_AUTHORITY.md`
- `docs/automation/0174UI_R3_STATE_RECON/ui_surface_authority_map.md`

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


## Latest V6 Operator Handoff Update

- Added `live_contentops/substack_manual_export_operator_handoff_v6.py`.
- Added deterministic handoff sample packet under `docs/automation/V6_SUBSTACK_MANUAL_EXPORT_OPERATOR_HANDOFF/`.
- Surfaced fixture-only handoff evidence in canonical V5 Manual Export, Approval Queue, and Evidence Vault.
- Live publish, Substack API, provider calls, dispatch/send/schedule/approve controls, env/credential reads, and browser-session access remain disabled/false.


Remote/status SHA note for operator handoff: accepted product baseline and last verified remote SHA target `af911eaf3fd1f0a85878ccb73361379732a7595b` after push/readback.
