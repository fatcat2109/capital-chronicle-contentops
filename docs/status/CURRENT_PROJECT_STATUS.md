# Capital Chronicle ContentOps — Current Project Status

## last_updated_by_task
TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_EXPORT_AND_ARTICLE_STUDIO_ON_CANONICAL_V5_DASHBOARD_HEAVY_BATCH_V0

## last_verified_repo
fatcat2109/capital-chronicle-contentops

## last_verified_branch
master

## last_verified_remote_sha
f688294d210065c21fe74740db8818ee09c526d2

## current_product_phase
V6 local-first product loop consolidation on the canonical V5 dashboard surface.

## current_product_lane
Substack manual export article studio integrated into the canonical V5 dashboard using fixture-only packets and deterministic hashes.

## accepted_baseline_summary
The accepted baseline is commit `f688294d210065c21fe74740db8818ee09c526d2` on `origin/master`. The V6 Substack manual export article studio lane is integrated into canonical V5 with fixture-only packets and deterministic hashes; live publish remains disabled.

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
V6 local deterministic loop components exist for research packets, canonical article drafts, Substack manual export packets, editorial review, variant preview/hash approval, Discord dry-run outbox, redacted audit, manual fallback, approval queue/evidence vault packets, and live-pilot blocked/ready state. Fixture-only V6 approval/evidence and Substack article studio cards are integrated into the canonical V5 dashboard views.

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
TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_EXPORT_AND_ARTICLE_STUDIO_ON_CANONICAL_V5_DASHBOARD_HEAVY_BATCH_V0

## latest changed areas
- `live_contentops/substack_manual_export_article_studio_v6.py`
- `docs/automation/V6_SUBSTACK_MANUAL_EXPORT_ARTICLE_STUDIO/`
- `docs/runbooks/V6_SUBSTACK_MANUAL_EXPORT_ARTICLE_STUDIO_RUNBOOK.md`
- `tests/test_substack_manual_export_article_studio_v6.py`
- `ui/contentops_v5/src/`

## current next recommended task
TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_APPROVAL_AND_EXPORT_EVIDENCE_HARDENING_V0

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
