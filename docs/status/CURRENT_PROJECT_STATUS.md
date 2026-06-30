# Capital Chronicle ContentOps — Current Project Status

## last_updated_by_task
TASK_CONTENTOPS_V6_CURRENT_PROJECT_STATUS_LEDGER_AND_DASHBOARD_AUTHORITY_GUARDRAIL_V0

## last_verified_repo
fatcat2109/capital-chronicle-contentops

## last_verified_branch
master

## last_verified_remote_sha
f0cffe4d99bdc5d619f387bbd3e6a6455438a95a

## current_product_phase
V6 local-first product loop consolidation on top of the V5 dashboard surface.

## current_product_lane
Dashboard authority guardrail, status ledger, and future-task protocol.

## accepted_baseline_summary
The accepted baseline is commit `f0cffe4d99bdc5d619f387bbd3e6a6455438a95a` on `origin/master`. Recent V6 backend/read-model tasks produced local deterministic packets for AI research, canonical article production, platform variants, approval queues, Discord dry-run outbox, supervised live-pilot gating, and evidence review. The latest UI repair mistakenly integrated V6 approval queue evidence into V4; this status ledger prevents repeating that targeting mistake.

## canonical_dashboard_surface
`ui/contentops_v5/` is the canonical current dashboard/app surface unless a newer committed authority document supersedes it.

Canonical entrypoint: `ui/contentops_v5/src/App.tsx`.
Canonical package: `ui/contentops_v5/package.json`.

V6 backend/read-model packets are allowed to exist, but canonical UI integration must target V5.

## legacy_ui_surfaces
- `ui/institutional_operator_cockpit_v4/` — fallback/reference only; must not receive new product features.
- `ui/institutional_operator_cockpit_v3/` — legacy reference.
- `ui/institutional_operator_cockpit_v2/` — legacy reference.
- `ui/institutional_shell/` — legacy sandbox reference.
- `ui/daily_content_studio/` — legacy sandbox reference.
- `ui/operator_evidence_intake_studio/` — specialized legacy/reference intake studio unless superseded by V5 integration.

## stale_or_deprecated_surfaces
- `ui/operator_approval_queue_evidence_vault/`, if present, is not canonical product UI and must be removed/deprecated in the dashboard cleanup task.
- Standalone generated dashboards must not become canonical through convenience.

## current_v6_loop_status
V6 local deterministic loop components exist for research packets, canonical article drafts, editorial review, variant preview/hash approval, Discord dry-run outbox, redacted audit, manual fallback, approval queue/evidence vault packets, and live-pilot blocked/ready state.

## dispatch/live status
Dispatch/live remains blocked unless an exact approved live task and exact runtime authority allow it. No autonomous publish, schedule, retry, queue execution, platform API call, or live send is authorized by this status ledger.

## provider/env/credential status
Provider/env/credential handling remains gated. Env/key presence may appear only as committed boolean/key-name evidence in approved tasks. No raw env values, credential values, webhook URLs, provider keys, browser session data, token material, or secret-derived metadata may be printed or committed.

## active blockers
- Canonical V5 dashboard integration for the V6 approval queue/evidence vault is still pending repair.
- V4 contains a recent non-canonical integration and should be treated as reference-only until cleaned up.
- Standalone approval queue UI must not be revived as canonical.
- Live/provider/platform execution remains disabled unless a future exact approved live task clears all gates.

## accepted caveats
- GitHub remote commits and fetched repo files remain runtime authority above this status doc.
- If this status doc conflicts with GitHub remote or newer committed authority docs, the worker must stop and report BLOCKED for reconciliation.
- Do not use chat memory or Project Sources as runtime authority when status doc and repo files disagree.

## latest accepted task
TASK_CONTENTOPS_V6_CURRENT_PROJECT_STATUS_LEDGER_AND_DASHBOARD_AUTHORITY_GUARDRAIL_V0

## latest changed areas
- `docs/status/`
- `tests/test_current_project_status_guardrail_v6.py`

## current next recommended task
TASK_CONTENTOPS_V6_DASHBOARD_AUTHORITY_RECON_AND_STALE_UI_CLEANUP_REPAIR_V0

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
