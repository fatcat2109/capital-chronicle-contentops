# V6 Dashboard Authority Recon Report

## Decision

`ui/contentops_v5/` is the canonical current product dashboard. `ui/institutional_operator_cockpit_v4/` is fallback/reference only. Static one-off pages are not canonical dashboards.

## Evidence read

- `docs/status/CURRENT_PROJECT_STATUS.md`
- `docs/status/current_project_status.json`
- `docs/status/TASK_STATUS_UPDATE_PROTOCOL.md`
- `docs/status/DASHBOARD_SURFACE_AUTHORITY.md`
- `docs/automation/0174UI_R3_STATE_RECON/ui_surface_authority_map.md`
- `docs/automation/0174UI_R3_STATE_RECON/master_plan_gap_map.md`
- `docs/automation/0174UI_R3_STATE_RECON/next_task_handoff.md`
- `docs/CAPITAL_CHRONICLE_CONTENTOPS_V5_FINAL_MASTER_PLAN_AND_NORTH_STAR.md`
- V5 app/package/state/types/fixtures/views/tests
- V4 index/view model/renderer/styles
- V6 operator approval/evidence backend, tests, runbook, sample packet

## UI surface classification

| Path | Classification | Reason | Package/build/test status | New features allowed | Browser QA target | Cleanup action | References found |
|---|---|---|---|---|---|---|---|
| `ui/contentops_v5/` | canonical_current | Status JSON and authority map identify V5 as active React/Vite product surface. Repo has package manifest, app shell, navigation, tests, and existing ApprovalQueue/EvidenceVault views. | `npm test -- --run`; `npm run build` | Yes, if safety-gated and inside V5 shell | Yes, primary target | keep; move useful integration here | status docs, authority map, V5 master plan, V5 tests |
| `ui/institutional_operator_cockpit_v4/` | active_reference | Authority map and status docs classify V4 as fallback/reference only. Recent V6 feature block was non-canonical. | static HTML/JS; no V5 package | No | Reference only, not primary QA | remove V6 product feature integration; keep V4 | status docs, authority map, runbook, V4 files |
| `ui/institutional_operator_cockpit_v3/` | legacy_reference | Historic cockpit retained for regression/history only. | static legacy | No | No | keep | authority map |
| `ui/institutional_operator_cockpit_v2/` | legacy_reference | Historic cockpit retained for regression/history only. | static legacy | No | No | keep | authority map |
| `ui/institutional_shell/` | legacy_reference | Legacy sandbox, not canonical dashboard. | static legacy | No | No | keep | authority/status docs |
| `ui/daily_content_studio/` | legacy_reference | Legacy sandbox, not canonical dashboard. | static legacy | No | No | keep | authority/status docs |
| `ui/operator_evidence_intake_studio/` | active_reference | Specialized intake reference; not canonical unless future authority promotes it. | static/specialized reference | No product-dashboard features | No | keep | status docs |
| `ui/operator_approval_queue_evidence_vault/` | stale_wrong_surface | Standalone approval/evidence page was wrong target and is absent in current checkout. | absent | No | No | keep absent; forbid canonical references | status docs, guardrail tests |

## Backend/read-model decision

Keep these valid backend evidence assets. They are not stale merely because the UI target was wrong:

- `live_contentops/operator_approval_queue_evidence_vault_v6.py`
- `tests/test_operator_approval_queue_evidence_vault_v6.py`
- `docs/automation/V6_OPERATOR_APPROVAL_QUEUE_EVIDENCE_VAULT_UI/sample_operator_approval_queue_evidence_vault_packet.json`

## Repair decisions

- Repair runbook to point operators to `ui/contentops_v5/` only.
- Remove non-canonical V6 feature data from V4.
- Integrate fixture-only V6 approval/evidence data into V5 ApprovalQueue/EvidenceVault.
- Keep all live/send/dispatch/approval controls disabled or absent.
