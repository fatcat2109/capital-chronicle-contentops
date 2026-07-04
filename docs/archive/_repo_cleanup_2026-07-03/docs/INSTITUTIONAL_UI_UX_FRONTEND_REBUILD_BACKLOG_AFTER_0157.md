# Institutional UI/UX + Front-End Rebuild Backlog (After 0157)

Task label: TASK_CONTENTOPS_0157_INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_MASTER_PLAN_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by
`docs/INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_MASTER_PLAN_AFTER_0157.md`.

This backlog is Cline-ready. Each task is self-contained. Unless a task explicitly
states otherwise:
- Antigravity is NOT allowed.
- Credentials/env reads are NOT allowed.
- Platform/provider/network/search/news/market-data APIs are NOT allowed.
- No live posting, scheduler, autonomous replies/DMs, scraping, live adapter, or
  real publish-all button may be created.
- No secrets, env values, or env paths may appear in any file, fixture, view
  model, DOM, screenshot, or evidence.
- Vanilla HTML/CSS/JS only; no new front-end dependency; no backend/server.

Global stop conditions (apply to every task): see master plan section 16.

---

## 0158 — Design System + Futuristic Fintech Visual Contract

Task label: TASK_CONTENTOPS_0158_INSTITUTIONAL_DESIGN_SYSTEM_VISUAL_CONTRACT_V0

Objective: Define the futuristic-institutional-fintech design system as a committed
contract: color tokens (with exact hex), the status-token palette from master plan
section 6, typography scale, spacing, elevation, table density rules, motion rules,
and iconography rules. Produce a static design-system reference page that renders
swatches and component states from a local fixture.

Allowed scope:
- Create a design-system doc and a design-token JSON contract + schema.
- Create a static, fixture-driven design-system reference page (HTML/CSS/JS).
- Create deterministic fixtures and tests.

Forbidden scope:
- No screen logic, no view-model wiring (that is 0159+).
- No backend, no dependency, no network, no credentials, no Antigravity.

Files to inspect:
- `docs/INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_MASTER_PLAN_AFTER_0157.md`
- `ui/daily_content_studio/styles.css`
- `docs/OPERATOR_UI_UX_AND_CONTENT_CALENDAR_SPEC_AFTER_0135.md`

Expected files to create/modify:
- `docs/INSTITUTIONAL_DESIGN_SYSTEM_AFTER_0158.md`
- `schemas/institutional_design_tokens_packet.schema.json`
- `fixtures/institutional_design_system/design_tokens_valid.json` + negatives
- `ui/institutional/design_system/` static reference page
- `tests/test_institutional_design_system.py`

Contracts: design-token packet validates against schema; status tokens match the
master plan section 6 vocabulary exactly.

Tests: schema validation; status-token completeness; static-asset safety (no fetch/
CDN/external scripts/storage/secrets); security scan clean.

Acceptance criteria: all 10 status tokens defined with label+icon+color; no P&L
color semantics; static page opens from `file://`; tests pass.

Stop conditions: cannot define tokens without a dependency; cannot render without a
server.

Required final evidence fields: see master plan section 17.

---

## 0159 — UI View-Model Contract v2

Task label: TASK_CONTENTOPS_0159_UI_VIEW_MODEL_CONTRACT_V2_V0

Objective: Define the single view-model contract that drives the whole terminal.
It composes existing packets (daily content studio UI data contract, publish
automation readiness, telegram gate status, evidence/audit) into one
schema-validated, redacted, fixture-driven view model with a per-screen section
map and a global safety header.

Allowed scope:
- Create the view-model schema + validator module + CLI summary command.
- Create deterministic valid + negative fixtures.
- Create tests.

Forbidden scope:
- No screen rendering code (that is 0160+).
- No backend, dependency, network, credentials, or Antigravity.

Files to inspect:
- `schemas/daily_content_studio_ui_data_contract_packet.schema.json`
- `schemas/publish_automation_readiness_packet.schema.json`
- `schemas/telegram_official_docs_credential_validation_gate_packet.schema.json`
- `live_contentops/daily_content_studio_ui_data_contract.py`

Expected files to create/modify:
- `docs/UI_VIEW_MODEL_CONTRACT_V2_AFTER_0159.md`
- `schemas/institutional_ui_view_model_packet.schema.json`
- `live_contentops/institutional_ui_view_model.py`
- `fixtures/institutional_ui_view_model/` valid + negatives
- `tests/test_institutional_ui_view_model.py`
- CLI command `pre-alpha-institutional-ui-view-model-summary`

Contracts: global safety header carries kill_switch_status, live_disabled,
not_public_postable; every section carries its status token; SECRET_REDACTED only.

Tests: schema validation; negative fixtures (secret-visible, live-enabled,
public-ready, signal-language) fail closed; CLI summary counters all 0;
security scan clean.

Acceptance criteria: one view model renders every screen's required safety state;
validator fail-closed; tests pass.

Stop conditions: a section would need a real secret/env value to be useful.

Required final evidence fields: see master plan section 17.

Antigravity allowed: No. Credentials/env/API allowed: No.

---

## 0160 — Institutional Shell Prototype

Task label: TASK_CONTENTOPS_0160_INSTITUTIONAL_SHELL_PROTOTYPE_V0

Objective: Build the static terminal shell: left-nav / command palette, global
safety banner row, screen routing (client-side, no server), and empty screen
frames for all 12 screens, driven by the 0159 view model fixture.

Allowed scope:
- Create static shell HTML/CSS/JS under `ui/institutional/`.
- Wire shell to embedded 0159 view-model fixture.
- Create tests for shell safety + navigation presence.

Forbidden scope:
- No per-screen detailed content (that is 0161+).
- No backend, dependency, network, credentials, or Antigravity.

Files to inspect:
- `ui/daily_content_studio/` (app.js, index.html, fixture_data.js pattern)
- `docs/UI_VIEW_MODEL_CONTRACT_V2_AFTER_0159.md`
- `docs/INSTITUTIONAL_DESIGN_SYSTEM_AFTER_0158.md`

Expected files to create/modify:
- `ui/institutional/index.html`, `styles.css`, `app.js`, `fixture_data.js`
- `ui/institutional/README.md`
- `tests/test_institutional_shell.py`

Contracts: shell renders global safety banner within first paint; nav lists all 12
screens; no live/publish/connect controls.

Tests: static-asset safety; nav completeness; banner presence; security scan clean.

Acceptance criteria: shell opens from `file://`; safety banner visible immediately;
all 12 screen frames reachable; tests pass.

Stop conditions: routing requires a server.

Required final evidence fields: see master plan section 17.

Antigravity allowed: No. Credentials/env/API allowed: No.


Antigravity allowed: No. Credentials/env/API allowed: No.

---

## 0161 — Command Center Screen

Task label: TASK_CONTENTOPS_0161_COMMAND_CENTER_SCREEN_V0

Objective: Implement the Command Center landing screen inside the shell: global
posture card (PASS/DEGRADED/BLOCKED), kill-switch state, LIVE_DISABLED banner,
blocked-summary list with reasons, and a "ready for review" count, all from the
0159 view model fixture.

Allowed scope:
- Implement Command Center render logic + styles within `ui/institutional/`.
- Extend fixtures with Command Center sections.
- Create tests.

Forbidden scope:
- No other screens' detailed logic; no live controls; no backend/dependency/
  network/credentials/Antigravity.

Files to inspect:
- `ui/institutional/` shell, `docs/UI_VIEW_MODEL_CONTRACT_V2_AFTER_0159.md`
- `live_contentops/status.py`, `live_contentops/kill_switch.py`

Expected files to create/modify:
- `ui/institutional/app.js`, `styles.css` (Command Center module)
- `fixtures/institutional_ui_view_model/` (Command Center sections)
- `tests/test_institutional_command_center.py`

Contracts: global posture + kill switch + LIVE_DISABLED visible on first paint;
every blocked item shows a reason.

Tests: static-asset safety; posture/kill-switch/blocked-reason presence; 10-second
visibility rule expressed as first-paint assertion; security scan clean.

Acceptance criteria: opening the terminal shows safety posture immediately; all
blocked states explained; tests pass.

Stop conditions: posture cannot be derived from local fixtures.

Required final evidence fields: see master plan section 17.

Antigravity allowed: No. Credentials/env/API allowed: No.

---

## 0162 — Content Studio Rebuild

Task label: TASK_CONTENTOPS_0162_CONTENT_STUDIO_REBUILD_V0

Objective: Rebuild the Daily Content Studio screen (and Content Lane Control +
Draft Inspector + Grounded News Angle Lab) inside the institutional shell:
evidence-first draft views, source lineage, limitations, lane separation,
external-LLM prompt handoff (repo does not execute prompts), REVIEW_REQUIRED and
NOT_PUBLIC_POSTABLE states.

Allowed scope:
- Implement Content Studio cluster screens from the 0159 view model.
- Reuse the accepted 0145 UI data contract fixture content via the view model.
- Create tests.

Forbidden scope:
- No prompt execution; no provider calls; no final public-ready copy; no live
  controls; no backend/dependency/network/credentials/Antigravity.

Files to inspect:
- `ui/daily_content_studio/` (existing screen), `live_contentops/daily_content_studio_ui_data_contract.py`
- `fixtures/daily_content_studio_ui/daily_content_studio_ui_data_contract_valid.json`

Expected files to create/modify:
- `ui/institutional/app.js`, `styles.css` (Content Studio cluster)
- `fixtures/institutional_ui_view_model/` (studio sections)
- `tests/test_institutional_content_studio.py`

Contracts: every draft shows source/evidence/limitation before polished copy;
forbidden actions render disabled+explained; lanes are visibly separated.

Tests: static-asset safety; evidence-first ordering; forbidden-action gating;
negative fixtures (public-ready, signal-language) fail closed; security scan clean.

Acceptance criteria: evidence-first studio renders; review/limitation states
visible; tests pass.

Stop conditions: a draft view requires prompt execution to be meaningful.

Required final evidence fields: see master plan section 17.

Antigravity allowed: No. Credentials/env/API allowed: No.

---

## 0163 — Publish Readiness Tower

Task label: TASK_CONTENTOPS_0163_PUBLISH_READINESS_TOWER_V0

Objective: Implement the Publish Automation Readiness screen + Telegram Pilot Gate
screen: dry-run readiness matrix, platform capability registry view, LIVE_DISABLED
on every platform, BLOCKED reasons, and a read-only redacted Telegram gate status
(SECRET_REDACTED, next-gate-required). No getMe/sendMessage; display only.

Allowed scope:
- Implement readiness + gate screens from the 0159 view model.
- Create tests.

Forbidden scope:
- No live posting/connect/publish-all controls; no getMe/sendMessage; no credential
  read; no backend/dependency/network/Antigravity.

Files to inspect:
- `live_contentops/publish_automation_readiness.py`
- `live_contentops/telegram_official_docs_credential_validation_gate.py`
- `schemas/platform_capability_registry_packet.schema.json`

Expected files to create/modify:
- `ui/institutional/app.js`, `styles.css` (readiness + gate screens)
- `fixtures/institutional_ui_view_model/` (readiness + gate sections)
- `tests/test_institutional_publish_readiness_tower.py`

Contracts: every platform shows LIVE_DISABLED; gate shows SECRET_REDACTED and
next-gate-required; no live control is interactive.

Tests: static-asset safety; LIVE_DISABLED presence; redaction assertions; negative
fixtures (live-enabled, secret-visible) fail closed; security scan clean.

Acceptance criteria: readiness + gate render with all live features visibly gated;
no secrets; tests pass.

Stop conditions: gate display would require a credential read or live call.

Required final evidence fields: see master plan section 17.

Antigravity allowed: No. Credentials/env/API allowed: No.


---

## 0164 — Evidence Vault

Task label: TASK_CONTENTOPS_0164_EVIDENCE_VAULT_V0

Objective: Implement the Evidence Vault screen: source artifacts, lineage, data
sufficiency, and the STALE / PROXY_ONLY / UNKNOWN / DEGRADED states surfaced
explicitly for every artifact. Missing stays visible with reason.

Allowed scope:
- Implement Evidence Vault from the 0159 view model.
- Create tests.

Forbidden scope:
- No raw vendor data redistribution; no live data fetch; no live controls; no
  backend/dependency/network/credentials/Antigravity.

Files to inspect:
- `schemas/source_artifact_export.schema.json`
- `live_contentops/real_artifact_intake.py`, `live_contentops/pipeline_trace.py`
- `docs/UI_VIEW_MODEL_CONTRACT_V2_AFTER_0159.md`

Expected files to create/modify:
- `ui/institutional/app.js`, `styles.css` (Evidence Vault)
- `fixtures/institutional_ui_view_model/` (evidence sections)
- `tests/test_institutional_evidence_vault.py`

Contracts: every artifact shows source + lineage + data-sufficiency; STALE/
PROXY_ONLY/UNKNOWN/DEGRADED never collapse to PASS.

Tests: static-asset safety; missing/degraded/proxy/stale visibility; security scan
clean.

Acceptance criteria: evidence-first vault renders; no hidden gaps; tests pass.

Stop conditions: a sufficiency state would require a live data call.

Required final evidence fields: see master plan section 17.

Antigravity allowed: No. Credentials/env/API allowed: No.

---

## 0165 — Calendar + Workflow Board

Task label: TASK_CONTENTOPS_0165_CALENDAR_WORKFLOW_BOARD_V0

Objective: Implement the Content Calendar planning view and the Approval Queue
workflow board. The calendar is planning-only and NEVER marks anything public-ready;
the approval queue surfaces REVIEW_REQUIRED items and decision history.

Allowed scope:
- Implement calendar + approval-queue screens from the 0159 view model.
- Create tests.

Forbidden scope:
- No scheduling; no auto-schedule; no public-ready marking; no live controls; no
  backend/dependency/network/credentials/Antigravity.

Files to inspect:
- `schemas/content_calendar_spec_packet.schema.json`
- `schemas/approval_queue_summary.schema.json`
- `fixtures/operator_ui_ux/valid_content_calendar_spec.json`

Expected files to create/modify:
- `ui/institutional/app.js`, `styles.css` (calendar + approval queue)
- `fixtures/institutional_ui_view_model/` (calendar + queue sections)
- `tests/test_institutional_calendar_workflow.py`

Contracts: calendar never marks public-ready; approval queue shows REVIEW_REQUIRED;
no scheduling control is interactive.

Tests: static-asset safety; no-public-ready assertion; negative fixtures
(auto-schedule, public-ready) fail closed; security scan clean.

Acceptance criteria: planning calendar + review board render; no scheduling; tests
pass.

Stop conditions: calendar would need a scheduler to be useful.

Required final evidence fields: see master plan section 17.

Antigravity allowed: No. Credentials/env/API allowed: No.

---

## 0166 — Visual Export / Screenshot-Safe Mode

Task label: TASK_CONTENTOPS_0166_VISUAL_EXPORT_SCREENSHOT_SAFE_MODE_V0

Objective: Implement the Visual Export Studio + a global screenshot/briefing-safe
mode toggle. In safe mode, the terminal shows zero secrets, zero env paths, and
asserts no false readiness. Safe mode never invents a PASS it does not have.

Allowed scope:
- Implement safe-mode toggle + export-preview screen from the 0159 view model.
- Create tests.

Forbidden scope:
- No actual file/network export; no live controls; no backend/dependency/network/
  credentials/Antigravity. (Export = an on-screen, redacted, capture-ready view.)

Files to inspect:
- `ui/institutional/` shell + screens
- `docs/INSTITUTIONAL_UI_UX_QUALITY_BAR_AND_ACCEPTANCE_MATRIX_AFTER_0157.md`

Expected files to create/modify:
- `ui/institutional/app.js`, `styles.css` (safe mode + export studio)
- `fixtures/institutional_ui_view_model/` (export sections)
- `tests/test_institutional_visual_export.py`

Contracts: safe mode hides all SECRET_REDACTED detail beyond the redacted token,
shows no env paths, and never upgrades a non-PASS to PASS.

Tests: static-asset safety; safe-mode no-secret assertion; no-false-readiness
assertion; security scan clean.

Acceptance criteria: safe mode produces a capture-ready, secret-free, honest view;
tests pass.

Stop conditions: export would require writing files or a network call.

Required final evidence fields: see master plan section 17.

Antigravity allowed: No. Credentials/env/API allowed: No.


---

## 0167 — Antigravity Browser QA Pass

Task label: TASK_CONTENTOPS_0167_ANTIGRAVITY_BROWSER_QA_PASS_V0

Objective: Run a narrow, screen-by-screen Antigravity browser QA pass against the
Cline-built, locally testable institutional UI (built across 0158–0166). Capture
screenshots, record a walkthrough, confirm the global safety banner, confirm no
interactive live controls, and report visual bugs only.

Allowed scope (Antigravity QA only):
- Open the built `ui/institutional/index.html` in a browser locally.
- Navigate each screen against expected-state QA scripts.
- Capture screenshots and record a walkthrough.
- File a structured visual-bug report doc.

Forbidden scope:
- No architecture design; no scope broadening; no code changes (fixes happen in
  0168); no platform/provider/network/credential calls; no secret inspection; no
  getMe/sendMessage; no live posting/scheduling.

Files to inspect:
- `ui/institutional/` (built UI)
- `docs/ANTIGRAVITY_BROWSER_QA_STRATEGY_AFTER_0157.md`
- `docs/INSTITUTIONAL_UI_UX_QUALITY_BAR_AND_ACCEPTANCE_MATRIX_AFTER_0157.md`

Expected files to create/modify:
- `docs/ANTIGRAVITY_BROWSER_QA_RESULTS_AFTER_0167.md` (evidence report)
- screenshot artifacts under a local QA evidence folder (no secrets in any image)

Contracts: QA evidence must include screenshot list, navigation coverage, visual
bug list, safety-banner confirmation, and a no-live-controls confirmation.

Tests: none authored by Antigravity; the deterministic Cline tests from 0158–0166
remain the structural source of truth.

Acceptance criteria: every screen walked; safety banner confirmed on each; no live
control found interactive; visual bugs catalogued for 0168.

Stop conditions: a Cline-built, locally testable UI does not yet exist; or QA would
require a network/credential/secret.

Required final evidence fields: see master plan section 17, plus screenshot list,
navigation coverage, visual bug list, safety-banner confirmation, no-live-controls
confirmation.

Antigravity allowed: YES (browser QA only, after Cline-built UI exists).
Credentials/env/API allowed: No.

---

## 0168 — Cline Institutional Polish Pass

Task label: TASK_CONTENTOPS_0168_CLINE_INSTITUTIONAL_POLISH_PASS_V0

Objective: Cline fixes the visual/UX issues catalogued in the 0167 Antigravity
evidence. Polish only: spacing, contrast, state-token rendering, table density,
copy clarity, and accessibility. No new screens, no scope expansion.

Allowed scope:
- Edit `ui/institutional/` assets to fix catalogued visual bugs.
- Update/extend tests to lock in fixes.

Forbidden scope:
- No new dependency; no backend; no network/credentials/Antigravity; no live
  controls; no new feature surface.

Files to inspect:
- `docs/ANTIGRAVITY_BROWSER_QA_RESULTS_AFTER_0167.md`
- `ui/institutional/` assets and their tests

Expected files to create/modify:
- `ui/institutional/styles.css`, `app.js` (targeted fixes)
- affected `tests/test_institutional_*.py`
- `docs/INSTITUTIONAL_UI_POLISH_NOTES_AFTER_0168.md`

Contracts: each fix maps to a 0167-reported issue; quality bar still holds; safety
states unchanged.

Tests: static-asset safety; regression tests for fixed issues; full suite passes;
security scan clean.

Acceptance criteria: all actionable 0167 visual bugs resolved or explicitly
deferred with reason; tests pass; no scope creep.

Stop conditions: a fix would require a dependency, a backend, or a live capability.

Required final evidence fields: see master plan section 17.

Antigravity allowed: No. Credentials/env/API allowed: No.

---

## Cross-Task Invariants (0158–0168)

- 0158–0166 and 0168: Antigravity NOT allowed.
- 0167: Antigravity allowed for browser QA only, after a Cline-built UI exists.
- No task creates live posting, scheduler, autonomous replies/DMs, scraping, a
  live adapter, or a real publish-all button.
- No task displays secrets, env values, or env paths.
- No UI task includes a real publish-all button (only visually gated, disabled,
  explained future-state placeholders).
- Every task keeps the kill switch active and live posting disabled.
- Every task leaves residual drift untouched.

