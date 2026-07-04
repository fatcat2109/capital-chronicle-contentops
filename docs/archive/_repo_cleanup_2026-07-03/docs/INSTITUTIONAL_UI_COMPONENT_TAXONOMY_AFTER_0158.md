# Institutional UI Component Taxonomy (After 0158)

Task label: TASK_CONTENTOPS_0158_INSTITUTIONAL_DESIGN_SYSTEM_AND_FUTURISTIC_FINTECH_VISUAL_CONTRACT_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by
`docs/INSTITUTIONAL_DESIGN_SYSTEM_AND_FUTURISTIC_FINTECH_VISUAL_CONTRACT_AFTER_0158.md`.

Planning/spec only. No active front-end code is created here. Each component below
defines: component_id, display_name, screen_usage, required_status_tokens,
required_fields, forbidden_fields, blocked_behavior, empty_state,
redaction_behavior, test_contract, and future_view_model_dependency.

Components are grouped by:
1. Global frame components
2. Safety / gating components
3. Evidence and audit components
4. Content review components
5. Platform readiness components
6. Telegram-specific pilot components
7. Data sufficiency / forecast readiness components
8. Calendar / workflow components
9. Screenshot / export components
10. Settings / safety policy components

---

## 1. Global Frame Components

### global_safety_ribbon — Global Safety Ribbon
- screen_usage: all screens (top, sticky).
- required_status_tokens: KILL_SWITCH_ACTIVE, LIVE_DISABLED, NOT_PUBLIC_POSTABLE.
- required_fields: kill_switch_status, live_disabled, not_public_postable,
  review_only, local_only.
- forbidden_fields: any secret value, env path, raw token, publish_ready=true.
- blocked_behavior: if posture cannot be derived, render BLOCKED ribbon with
  reason; never render empty/clear.
- empty_state: never empty; defaults to most-restrictive safe posture.
- redaction_behavior: shows redacted tokens only; never a credential value.
- test_contract: ribbon nodes exist on first paint; kill-switch + live-disabled
  visible; no secret/env-path strings present.
- future_view_model_dependency: view_model.global_safety_header.

### command_center_status_header — Command Center Status Header
- screen_usage: Command Center (and as screen sub-header pattern).
- required_status_tokens: PASS, DEGRADED, BLOCKED, REVIEW_REQUIRED.
- required_fields: overall_posture, blocked_count, review_required_count,
  ready_for_review_count, last_evaluated_at.
- forbidden_fields: market_direction, pnl, signal_strength, public_ready.
- blocked_behavior: BLOCKED posture surfaces a blocked reason stack.
- empty_state: shows UNKNOWN posture with reason if no data.
- redaction_behavior: no secrets; timestamps in mono.
- test_contract: overall posture token present; counts render; no signal fields.
- future_view_model_dependency: view_model.command_center.status_header.

### content_lane_badge — Content Lane Badge
- screen_usage: Content Lane Control, Daily Content Studio, Draft Inspector.
- required_status_tokens: NOT_PUBLIC_POSTABLE, MANUAL_ONLY.
- required_fields: lane_id, lane_name, lane_policy_summary.
- forbidden_fields: public_ready, publish_ready, signal_language.
- blocked_behavior: lane with policy violation renders BLOCKED with reason.
- empty_state: "lane unassigned" UNKNOWN badge.
- redaction_behavior: n/a (no secrets).
- test_contract: lane badge shows lane policy; not-public-postable visible.
- future_view_model_dependency: view_model.content_lane.badge.

### forbidden_action_tooltip — Forbidden Action Tooltip
- screen_usage: any gated control.
- required_status_tokens: LIVE_DISABLED, BLOCKED.
- required_fields: action_id, reason, future_gate_required.
- forbidden_fields: any enabling handler, any live endpoint.
- blocked_behavior: explains why the action is disabled; never enables it.
- empty_state: n/a (only present on gated controls).
- redaction_behavior: no secrets in reason text.
- test_contract: tooltip present on disabled controls with a reason; control is
  non-interactive.

---

## 2. Safety / Gating Components

### gate_card — Gate Card
- screen_usage: Publish Readiness Tower, Telegram Pilot Gate, Command Center.
- required_status_tokens: BLOCKED, LIVE_DISABLED, DRY_RUN_ONLY, REVIEW_REQUIRED.
- required_fields: gate_id, gate_name, gate_state, blocking_reasons[], next_gate_required.
- forbidden_fields: live_endpoint, enabled_publish_handler, public_ready.
- blocked_behavior: shows blocking_reasons; offers no live action.
- empty_state: UNKNOWN gate with reason.
- redaction_behavior: no secrets; gate references only.
- test_contract: gate state token present; blocking reasons render; no live action.
- future_view_model_dependency: view_model.gates[].

### blocked_reason_stack — Blocked Reason Stack
- screen_usage: any screen with BLOCKED state.
- required_status_tokens: BLOCKED.
- required_fields: reasons[] (each with code + plain_language_text).
- forbidden_fields: secrets, env paths.
- blocked_behavior: this IS the blocked explainer; never empty when BLOCKED.
- empty_state: hidden only when no blocked state exists.
- redaction_behavior: reasons must not contain secrets/paths.
- test_contract: every blocked state has at least one reason with text.
- future_view_model_dependency: view_model.*.blocked_reasons.

### publish_disabled_control — Publish Disabled Control
- screen_usage: Publish Readiness Tower, Telegram Pilot Gate.
- required_status_tokens: LIVE_DISABLED, NOT_PUBLIC_POSTABLE.
- required_fields: control_id, disabled=true, disabled_reason, future_gate_required.
- forbidden_fields: onClick publish handler, live endpoint, one_button_publish_all.
- blocked_behavior: always disabled; renders reason; never posts.
- empty_state: n/a.
- redaction_behavior: no secrets in reason.
- test_contract: control is disabled and non-interactive; no publish handler exists.
- future_view_model_dependency: view_model.controls[].publish_disabled.

### not_public_postable_banner — Not Public Postable Banner
- screen_usage: all content screens.
- required_status_tokens: NOT_PUBLIC_POSTABLE.
- required_fields: visible=true, copy.
- forbidden_fields: public_ready, publish_ready.
- blocked_behavior: always visible on content screens.
- empty_state: never empty on content screens.
- redaction_behavior: n/a.
- test_contract: banner present on every content screen.
- future_view_model_dependency: view_model.global_safety_header.not_public_postable.

### manual_review_required_banner — Manual Review Required Banner
- screen_usage: Daily Content Studio, Draft Inspector, Approval Queue.
- required_status_tokens: REVIEW_REQUIRED, MANUAL_ONLY.
- required_fields: visible=true, copy.
- forbidden_fields: auto_approval, public_ready.
- blocked_behavior: visible whenever review is pending.
- empty_state: shown by default (safe).
- redaction_behavior: n/a.
- test_contract: banner present where review is required.
- future_view_model_dependency: view_model.*.manual_review_required.

### kill_switch_indicator — Kill Switch Indicator
- screen_usage: Global Safety Ribbon, Command Center, Settings.
- required_status_tokens: KILL_SWITCH_ACTIVE.
- required_fields: kill_switch_status.
- forbidden_fields: any disable-kill-switch control wired to live action.
- blocked_behavior: when active, reinforces all live actions disabled.
- empty_state: defaults to active (safe) if unknown.
- redaction_behavior: n/a.
- test_contract: indicator reflects kill_switch_status; defaults safe.
- future_view_model_dependency: view_model.global_safety_header.kill_switch_status.

### screenshot_safe_watermark — Screenshot-Safe Watermark
- screen_usage: all screens in screenshot-safe mode; Visual Export Studio.
- required_status_tokens: NOT_PUBLIC_POSTABLE, LIVE_DISABLED.
- required_fields: watermark_label, safe_mode_active.
- forbidden_fields: secrets, env paths.
- blocked_behavior: n/a (informational).
- empty_state: absent when safe mode off; present when on.
- redaction_behavior: confirms redaction is active.
- test_contract: watermark present when safe mode active; carries safe label.
- future_view_model_dependency: view_model.export.safe_mode.


---

## 3. Evidence and Audit Components

### evidence_link_card — Evidence Link Card
- screen_usage: Evidence Vault, Draft Inspector, Grounded News Angle Lab.
- required_status_tokens: PASS, DEGRADED, PROXY_ONLY, STALE, UNKNOWN.
- required_fields: evidence_id, source_label, source_ref, retrieved_at, sufficiency_state.
- forbidden_fields: raw_vendor_payload, secret, env_path, raw_request_url.
- blocked_behavior: missing source renders BLOCKED/UNKNOWN with reason.
- empty_state: "no evidence linked" UNKNOWN row, never hidden silently.
- redaction_behavior: no raw vendor data; references/labels only.
- test_contract: evidence shows source + retrieved_at + sufficiency; no raw payload.
- future_view_model_dependency: view_model.evidence[].

### source_lineage_panel — Source Lineage Panel
- screen_usage: Evidence Vault, Draft Inspector.
- required_status_tokens: PASS, DEGRADED, PROXY_ONLY, STALE.
- required_fields: lineage_steps[] (origin -> transform -> artifact), artifact_ref.
- forbidden_fields: raw vendor payload, secrets.
- blocked_behavior: broken lineage renders BLOCKED with the missing step.
- empty_state: "lineage unavailable" UNKNOWN.
- redaction_behavior: references only; no raw data dumps.
- test_contract: lineage steps render in order; missing step visible.
- future_view_model_dependency: view_model.evidence[].lineage.

### audit_timeline — Audit Timeline
- screen_usage: Approval Queue, Evidence Vault, Settings.
- required_status_tokens: PASS, REVIEW_REQUIRED, BLOCKED, SECRET_REDACTED.
- required_fields: events[] (ts, actor, action, redacted_detail).
- forbidden_fields: secret values, credentials, env paths, raw platform response.
- blocked_behavior: events with secret content are redacted, not shown raw.
- empty_state: "no audit events" neutral row.
- redaction_behavior: every event detail is redacted-safe.
- test_contract: events render with redacted detail; no secret-like strings.
- future_view_model_dependency: view_model.audit.events[].

### limitation_strip — Limitation Strip
- screen_usage: Daily Content Studio, Draft Inspector, Grounded News Angle Lab.
- required_status_tokens: DEGRADED, REVIEW_REQUIRED.
- required_fields: limitations[] (text).
- forbidden_fields: public_ready, signal_language.
- blocked_behavior: never hidden; persists in screenshot-safe mode.
- empty_state: "no stated limitations" explicit note (not blank).
- redaction_behavior: n/a.
- test_contract: limitations visible and persist in safe mode.
- future_view_model_dependency: view_model.*.limitations[].

### claim_risk_panel — Claim Risk Panel
- screen_usage: Draft Inspector.
- required_status_tokens: REVIEW_REQUIRED, BLOCKED, DEGRADED.
- required_fields: claims[] (claim_text, support_state, source_ref_or_unsupported).
- forbidden_fields: actionable trade language, signal_language, public_ready.
- blocked_behavior: unsupported current/numeric claim renders BLOCKED with reason.
- empty_state: "no flagged claims" note.
- redaction_behavior: n/a.
- test_contract: unsupported claims flagged; no actionable/signal language.
- future_view_model_dependency: view_model.draft.claim_risk[].


---

## 4. Content Review Components

### draft_inspector_panel — Draft Inspector Panel
- screen_usage: Draft Inspector, Daily Content Studio.
- required_status_tokens: REVIEW_REQUIRED, NOT_PUBLIC_POSTABLE, DEGRADED.
- required_fields: draft_id, lane_id, sources[], limitations[], evidence_refs[], draft_body_preview.
- forbidden_fields: public_ready, publish_ready, final_social_copy, signal_language.
- blocked_behavior: draft missing source/limitation renders REVIEW_REQUIRED + reason; evidence shown before body.
- empty_state: "no draft selected" neutral panel.
- redaction_behavior: no secrets; external-LLM prompt is handoff text only (repo does not execute).
- test_contract: evidence/limitations render before body; no public-ready/final-copy fields.
- future_view_model_dependency: view_model.draft.inspector.

### approval_decision_card — Approval Decision Card
- screen_usage: Approval Queue, Draft Inspector.
- required_status_tokens: REVIEW_REQUIRED, MANUAL_ONLY, PASS, BLOCKED.
- required_fields: item_id, decision_options[approve/request_revision/reject], reviewer_required, decision_history[].
- forbidden_fields: auto_approval, public_ready, one_button_publish_all.
- blocked_behavior: no decision auto-applies; reviewer required; live publish never offered.
- empty_state: "no items awaiting decision" note.
- redaction_behavior: history details redacted-safe.
- test_contract: decision requires reviewer; no auto-approval/public-ready path.
- future_view_model_dependency: view_model.approval_queue.items[].

### markdown_review_export_view — Markdown Review Export View
- screen_usage: Daily Content Studio, Visual Export Studio.
- required_status_tokens: REVIEW_ONLY (banner), NOT_PUBLIC_POSTABLE.
- required_fields: export_markdown_preview, review_only=true.
- forbidden_fields: public_ready, publish_ready, final_social_copy.
- blocked_behavior: export is review-only text; never a publish action.
- empty_state: "nothing to export" note.
- redaction_behavior: no secrets/env paths in exported text.
- test_contract: export is review-only; no publish handler; no secrets.
- future_view_model_dependency: view_model.studio.markdown_export.


---

## 5. Platform Readiness Components

### platform_readiness_card — Platform Readiness Card
- screen_usage: Publish Readiness Tower, Command Center.
- required_status_tokens: LIVE_DISABLED, DRY_RUN_ONLY, BLOCKED, DEGRADED.
- required_fields: platform_id, capability_state, live_disabled=true, dry_run_only=true, blocking_reasons[].
- forbidden_fields: live_endpoint, enabled_publish_handler, public_ready, one_button_publish_all.
- blocked_behavior: every platform shows LIVE_DISABLED; live action never offered.
- empty_state: "platform not registered" UNKNOWN card.
- redaction_behavior: no credentials; capability references only.
- test_contract: LIVE_DISABLED present on each platform; no live action handler.
- future_view_model_dependency: view_model.publish_readiness.platforms[].

### content_lane_readiness_row — Content Lane Readiness Row
- screen_usage: Publish Readiness Tower.
- required_status_tokens: NOT_PUBLIC_POSTABLE, REVIEW_REQUIRED, LIVE_DISABLED.
- required_fields: lane_id, readiness_state, manual_review_required=true.
- forbidden_fields: public_ready, auto_publish.
- blocked_behavior: lane not review-complete renders REVIEW_REQUIRED.
- empty_state: neutral "no lanes" row.
- redaction_behavior: n/a.
- test_contract: manual-review-required visible; not-public-postable visible.
- future_view_model_dependency: view_model.publish_readiness.lanes[].

---

## 6. Telegram-Specific Pilot Components

### telegram_gate_stepper — Telegram Gate Stepper
- screen_usage: Telegram Pilot Gate.
- required_status_tokens: CREDENTIAL_PRESENT_REDACTED, CREDENTIAL_VALIDATED_NO_POST, API_VALIDATED_NO_POST, CHANNEL_PERMISSION_UNVALIDATED, LIVE_DISABLED, DRY_RUN_ONLY.
- required_fields: steps[] (presence_check, official_docs, getme_validation_no_post, channel_permission_future, explicit_go_future), current_step, next_gate_required.
- forbidden_fields: getme_call_handler, sendmessage_handler, token_value, chat_id_value, request_url, raw_response.
- blocked_behavior: read-only display of existing gate state; never calls getMe/sendMessage; posting blocked.
- empty_state: "gate not yet evaluated" UNKNOWN step.
- redaction_behavior: credential states are redacted tokens only; never values/snippets/lengths/hashes.
- test_contract: stepper is display-only; no API handler; SECRET_REDACTED on credential states; channel permission unvalidated.
- future_view_model_dependency: view_model.telegram_gate.steps[] (sourced from existing gate packet summary, redacted).

### credential_redaction_badge — Credential Redaction Badge
- screen_usage: Telegram Pilot Gate, Settings, Platform Readiness Card.
- required_status_tokens: SECRET_REDACTED, CREDENTIAL_PRESENT_REDACTED.
- required_fields: credential_label, present_boolean_or_unknown, redacted=true.
- forbidden_fields: value, snippet, length, hash, env_path.
- blocked_behavior: shows presence as boolean/redacted token only.
- empty_state: UNKNOWN badge if presence not checked.
- redaction_behavior: never reveals value/snippet/length/hash; boolean/token only.
- test_contract: badge shows redacted token; no secret-like string; no env path.
- future_view_model_dependency: view_model.credentials[].redacted_state.


---

## 7. Data Sufficiency / Forecast Readiness Components

### data_sufficiency_matrix — Data Sufficiency Matrix
- screen_usage: Evidence Vault, Command Center.
- required_status_tokens: PASS, DEGRADED, PROXY_ONLY, STALE, UNKNOWN, DQR_BLOCKING.
- required_fields: dimensions[] (name, coverage_state, freshness_state, proxy_flag), overall_sufficiency.
- forbidden_fields: market_direction, signal_strength, public_ready.
- blocked_behavior: DQR_BLOCKING renders blocked overall with the failing dimension.
- empty_state: "no sufficiency data" UNKNOWN matrix; never blank.
- redaction_behavior: no raw vendor data; coverage states only.
- test_contract: missing/degraded/proxy/stale visible; DQR_BLOCKING never collapses to PASS.
- future_view_model_dependency: view_model.data_sufficiency.matrix.

### forecast_readiness_card — Forecast Readiness Card
- screen_usage: Command Center, Evidence Vault.
- required_status_tokens: FORECAST_NOT_READY, DQR_BLOCKING, REVIEW_REQUIRED, PASS.
- required_fields: readiness_state, gating_factors[], forecast_not_ready_reason.
- forbidden_fields: guaranteed_prediction, signal_language, buy_sell_hold, public_ready.
- blocked_behavior: when not ready, shows FORECAST_NOT_READY + gating factors; never claims readiness.
- empty_state: defaults to FORECAST_NOT_READY (safe) if unknown.
- redaction_behavior: n/a.
- test_contract: readiness never claimed while gating factors exist; no guaranteed-prediction language.
- future_view_model_dependency: view_model.forecast_readiness.

### freshness_chip — Freshness Chip
- screen_usage: Evidence Vault, Data Sufficiency Matrix, Evidence Link Card.
- required_status_tokens: PASS, STALE.
- required_fields: as_of, freshness_threshold, freshness_state.
- forbidden_fields: secrets.
- blocked_behavior: past threshold renders STALE.
- empty_state: UNKNOWN chip if no timestamp.
- redaction_behavior: timestamps only; no secrets.
- test_contract: stale data renders STALE; never silently fresh.
- future_view_model_dependency: view_model.evidence[].freshness.

### proxy_only_warning — Proxy-Only Warning
- screen_usage: Evidence Vault, Grounded News Angle Lab, Data Sufficiency Matrix.
- required_status_tokens: PROXY_ONLY.
- required_fields: proxy_reason, real_source_absent=true.
- forbidden_fields: implied_real_source, public_ready.
- blocked_behavior: proxy data always labeled; never presented as real source.
- empty_state: absent only when no proxy data.
- redaction_behavior: n/a.
- test_contract: proxy data carries PROXY_ONLY; never implies real source.
- future_view_model_dependency: view_model.evidence[].proxy_only.

### missing_data_row — Missing Data Row
- screen_usage: Evidence Vault, Data Sufficiency Matrix.
- required_status_tokens: UNKNOWN, DEGRADED.
- required_fields: field_name, missing_reason.
- forbidden_fields: silent_omission, fabricated_value.
- blocked_behavior: missing data is shown as an explicit row with reason.
- empty_state: this IS the empty/missing representation.
- redaction_behavior: n/a.
- test_contract: missing data never hidden; row + reason present.
- future_view_model_dependency: view_model.*.missing_rows[].


---

## 8. Calendar / Workflow Components

### content_calendar_grid — Content Calendar Grid
- screen_usage: Content Calendar.
- required_status_tokens: NOT_PUBLIC_POSTABLE, REVIEW_REQUIRED, MANUAL_ONLY.
- required_fields: planned_items[] (date, lane_id, status), planning_only=true.
- forbidden_fields: public_ready, publish_ready, scheduled_post, auto_publish.
- blocked_behavior: calendar never marks public-ready; no scheduling control.
- empty_state: empty calendar with "planning only" note.
- redaction_behavior: n/a.
- test_contract: no public-ready marking; no scheduler control; planning_only present.
- future_view_model_dependency: view_model.calendar.items[].

### workflow_board_column — Workflow Board Column
- screen_usage: Approval Queue.
- required_status_tokens: REVIEW_REQUIRED, PASS, BLOCKED, MANUAL_ONLY.
- required_fields: column_id, items[], wip_count.
- forbidden_fields: auto_advance, public_ready, one_button_publish_all.
- blocked_behavior: items advance only via manual decision.
- empty_state: "no items" column note.
- redaction_behavior: item details redacted-safe.
- test_contract: no auto-advance; manual decision required.
- future_view_model_dependency: view_model.workflow.columns[].

---

## 9. Screenshot / Export Components

### visual_export_preview — Visual Export Preview
- screen_usage: Visual Export Studio.
- required_status_tokens: NOT_PUBLIC_POSTABLE, LIVE_DISABLED, SECRET_REDACTED.
- required_fields: safe_mode_active, redacted_fields[], watermark_label.
- forbidden_fields: secrets, env_paths, raw_vendor_data, raw_platform_response, raw_request_url, public_ready.
- blocked_behavior: export is an on-screen, redacted, capture-ready view; never writes files or calls network.
- empty_state: "nothing to export" note.
- redaction_behavior: all secret/credential fields redacted; no env paths.
- test_contract: safe mode hides secrets; watermark present; no false readiness; no file/network export.
- future_view_model_dependency: view_model.export.preview.

### screenshot_safe_toggle — Screenshot-Safe Toggle
- screen_usage: global control (shell), Visual Export Studio.
- required_status_tokens: SECRET_REDACTED.
- required_fields: safe_mode_active (boolean).
- forbidden_fields: reveal_secrets handler.
- blocked_behavior: turning on safe mode hides all redacted detail and never upgrades non-PASS to PASS.
- empty_state: n/a.
- redaction_behavior: enabling strengthens redaction; never weakens it.
- test_contract: safe mode on => no secrets visible; no false PASS.
- future_view_model_dependency: view_model.export.safe_mode.

---

## 10. Settings / Safety Policy Components

### safety_policy_panel — Safety Policy Panel
- screen_usage: Settings / Safety Policy.
- required_status_tokens: LIVE_DISABLED, KILL_SWITCH_ACTIVE, NOT_PUBLIC_POSTABLE, DRY_RUN_ONLY.
- required_fields: policy_flags[] (name, state, read_only=true).
- forbidden_fields: enable_live_handler, enable_scheduler_handler, enable_scraping_handler.
- blocked_behavior: all live flags shown false and read-only; no enabling control.
- empty_state: defaults to safest posture display.
- redaction_behavior: no secrets; policy state only.
- test_contract: all live flags false and read-only; no enabling handler.
- future_view_model_dependency: view_model.settings.safety_policy.

### posture_summary_row — Posture Summary Row
- screen_usage: Settings / Safety Policy, Command Center.
- required_status_tokens: PASS, DEGRADED, BLOCKED, KILL_SWITCH_ACTIVE.
- required_fields: posture_label, kill_switch_status, evaluated_at.
- forbidden_fields: market_direction, pnl, signal_strength.
- blocked_behavior: reflects overall posture; defaults safe when unknown.
- empty_state: UNKNOWN posture row.
- redaction_behavior: n/a.
- test_contract: posture + kill switch render; no market/signal fields.
- future_view_model_dependency: view_model.settings.posture.

---

## Component Coverage Note

This taxonomy defines 30 components across the 10 groups, covering every component
named in the 0158 visual contract section 9, including the explicitly required
Global Safety Ribbon, Gate Card, Evidence Link Card, Credential Redaction Badge,
Telegram Gate Stepper, Not Public Postable Banner, and Kill Switch Indicator.
Every component is display/review-only and carries no live, publish, scheduling,
scraping, credential-revealing, or signal-service capability.

- future_view_model_dependency: view_model.controls[].forbidden_reason.
