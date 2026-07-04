# Institutional UI View-Model Contract V2 (After 0159)

Task label: TASK_CONTENTOPS_0159_INSTITUTIONAL_UI_VIEW_MODEL_CONTRACT_V2_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Baseline HEAD before this task: 1ae6e62 — "docs: add institutional design system visual contract"
Scope: contract / spec / data-model only. This task defines machine-readable,
schema-validated view-model contracts and fixtures for the future institutional
local UI. It does NOT implement or modify active front-end code, does NOT run a
backend, does NOT run Antigravity or browser automation, does NOT read
credentials/env, and does NOT call any platform/provider/network API.

## 1. Owner Decision

The owner has decided to convert the accepted 0157 institutional UI master plan
and the 0158 design-system contract into a stable, machine-readable view-model
contract (V2). This contract is committed repo authority for how screen data,
status tokens, components, redaction flags, blocked reasons, evidence references,
and safety banners are represented for the future institutional local control
terminal. It governs the 0160 shell prototype and later screen tasks.

This is a contract/spec/data-model task only. It is not active front-end
implementation, not browser QA, not an Antigravity task, and not a live
platform/API task.

## 2. Accepted Baselines

- 0157 master plan and authority:
  - `docs/INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_MASTER_PLAN_AFTER_0157.md`
  - `docs/INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_BACKLOG_AFTER_0157.md`
  - `docs/INSTITUTIONAL_UI_UX_QUALITY_BAR_AND_ACCEPTANCE_MATRIX_AFTER_0157.md`
  - `schemas/institutional_ui_ux_frontend_rebuild_plan_packet.schema.json`
  - `live_contentops/institutional_ui_ux_frontend_rebuild_plan.py`
- 0158 design system and authority:
  - `docs/INSTITUTIONAL_DESIGN_SYSTEM_AND_FUTURISTIC_FINTECH_VISUAL_CONTRACT_AFTER_0158.md`
  - `docs/INSTITUTIONAL_UI_COMPONENT_TAXONOMY_AFTER_0158.md`
  - `docs/INSTITUTIONAL_STATUS_SEMANTICS_AND_SAFETY_BANNERS_AFTER_0158.md`
  - `docs/INSTITUTIONAL_SCREENSHOT_SAFE_AND_REDACTED_VISUAL_EXPORT_RULES_AFTER_0158.md`
  - `docs/INSTITUTIONAL_DESIGN_SYSTEM_HANDOFF_TO_VIEW_MODEL_AFTER_0158.md`
  - `schemas/institutional_design_system_packet.schema.json`
  - `live_contentops/institutional_design_system.py`

The view-model contract binds directly to the 0158 status token vocabulary (19
tokens), the component taxonomy (component IDs), and the 16 safety banners. This
contract does not supersede Telegram live-gate sequencing.

## 3. Contract Purpose

- A stable JSON contract for future institutional UI rendering.
- Local-only: rendered from `file://` or trivial static open; no server.
- Fixture / mock-data-first: every screen renders from deterministic fixtures.
- CLI-generated view models: produced by a deterministic summary from existing
  repo packets/fixtures, then embedded for `file://` use.
- No browser / platform / API / credential dependency anywhere in the contract.

## 4. Runtime Posture

- Planning / model authority only; not runtime front-end code.
- No live controls of any kind.
- No public-ready content.
- All live/credential/api/scheduler/scraping flags are fail-closed false.

## 5. Canonical Top-Level Packet Fields

| Field | Meaning |
| --- | --- |
| packet_id | Stable packet identifier |
| created_at | UTC timestamp (ISO8601 Z) |
| task_label | This task's label |
| view_model_contract_version | Contract version string ("v2") |
| ui_contract_mode | "contract_only" |
| runtime_authority | false |
| local_only | true |
| fixture_or_mock_data_only | true |
| active_frontend_code_changed | false |
| backend_server_required | false |
| browser_automation_used_now | false |
| antigravity_used_now | false |
| credential_read_allowed_now | false |
| platform_api_allowed_now | false |
| live_posting_enabled_now | false |
| scheduler_allowed_now | false |
| scraping_allowed_now | false |
| public_ready_final_copy_generated | false |
| linked_design_system_packet_id | 0158 design system packet id |
| linked_ui_rebuild_plan_packet_id | 0157 rebuild plan packet id |
| screens | Array of screen view models |
| global_state | Global state model object |
| status_token_registry | Array of status token binding models |
| component_registry | Array of component binding models |
| redaction_policy | Global redaction policy object |
| evidence_ref_policy | Global evidence reference policy object |
| blocked_action_policy | Global blocked-action policy object |
| safety_policy | Global safety policy object |
| fixture_strategy | Fixture strategy object |
| future_handoff | Handoff-to-0160 object |
| blocked_reasons | Array of blocked reason strings |
| packet_status | pass / blocked / fail |

## 6. Global State Model

| Field | Meaning |
| --- | --- |
| repo_path_label | Non-secret repo label |
| branch_label | Branch label |
| accepted_head_short | Accepted short HEAD |
| system_mode | e.g. "local_pre_alpha" |
| kill_switch_status | "active" |
| live_posting_enabled_now | false |
| platform_api_allowed_now | false |
| credential_state_summary | Redacted credential summary (tokens only) |
| current_gate | Current gate label |
| next_allowed_action | Next allowed (non-live) action label |
| active_blockers | Array of blocker strings |
| known_residual_drift_count | Integer count |
| not_public_postable_count | Integer count |
| manual_review_required_count | Integer count |

## 7. Status Token Binding Model

Each status token binding defines:
- status_token_id (from the 0158 vocabulary);
- semantic meaning;
- severity band (info / caution / blocking / locked);
- visual role (design token color role);
- icon role;
- allowed components (component IDs that may render the token);
- forbidden interpretation (e.g., "never market direction").

## 8. Component Binding Model

Each component binding defines:
- component_id (from 0158 taxonomy);
- display_name;
- design_system_component_ref;
- required_status_tokens;
- required_fields;
- optional_fields;
- forbidden_fields;
- redaction_fields;
- blocked_reason_refs;
- evidence_refs;
- empty_state;
- screenshot_safe_state;
- test_contract.


## 9. Screen Model

Each screen defines: screen_id, title, purpose, layout_region,
primary_components, data_dependencies, required_banners, required_status_tokens,
evidence_refs, blocked_reason_refs, redaction_requirements, forbidden_controls,
empty_state, screenshot_safe_behavior, fixture_id, future_frontend_notes. Full
per-screen definitions are in
`docs/INSTITUTIONAL_UI_SCREEN_VIEW_MODELS_AFTER_0159.md`.

## 10. Screenshot-Safe Model

- redact_secrets: true
- redact_env_paths: true
- redact_raw_platform_responses: true
- redact_request_urls: true
- no_raw_vendor_data: true
- no_false_public_ready: true
- limitations_visible: true
- no_signal_language: true
- no_financial_advice: true

## 11. Handoff To 0160 Shell Prototype

- The 0160 shell prototype may render these fixtures.
- No live data, no backend, no browser API calls, no env access, no active
  publishing controls. See
  `docs/INSTITUTIONAL_UI_VIEW_MODEL_HANDOFF_TO_SHELL_PROTOTYPE_AFTER_0159.md`.

## 12. Relationship To Telegram Live-Gate Sequencing

This view-model contract does NOT supersede Telegram live-gate sequencing. The
telegram_pilot_gate screen view model is a read-only, redacted display of existing
gate state. It never calls getMe or sendMessage and never reveals credentials.

- Kill switch is active; live posting disabled.
