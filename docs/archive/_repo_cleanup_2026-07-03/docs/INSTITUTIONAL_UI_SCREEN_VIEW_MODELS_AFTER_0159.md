# Institutional UI Screen View Models (After 0159)

Task label: TASK_CONTENTOPS_0159_INSTITUTIONAL_UI_VIEW_MODEL_CONTRACT_V2_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops
Branch: master
Authority: governed by
`docs/INSTITUTIONAL_UI_VIEW_MODEL_CONTRACT_V2_AFTER_0159.md`.

Contract/spec only. No active front-end code. Each screen below binds at least 3
components, at least 2 required status tokens, at least 1 safety banner, an
evidence_ref policy, a blocked_action policy, and a redaction policy.

---

## 1. command_center
- title: Command Center
- purpose: global operational status landing.
- layout_region: main.
- primary_components: global_safety_ribbon, command_center_status_header,
  blocked_reason_stack, kill_switch_indicator.
- data_dependencies: global_state, active_blockers, safety counters.
- required_banners: LOCAL_ONLY, KILL_SWITCH_ACTIVE, LIVE_DISABLED.
- required_status_tokens: PASS, DEGRADED, BLOCKED, KILL_SWITCH_ACTIVE.
- evidence_refs: none required (posture screen); links out to evidence_vault.
- blocked_reason_refs: global active_blockers.
- redaction_requirements: no secrets; credential_state_summary redacted only.
- forbidden_controls: any live action button, publish, schedule, connect.
- empty_state: UNKNOWN posture with reason; never blank.
- screenshot_safe_behavior: posture + counters safe; no secrets/env paths.
- fixture_id: vm_command_center.
- future_frontend_notes: shows kill switch active, latest accepted HEAD, current
  gate, safety counters, top blockers, next allowed action. No live buttons.

## 2. content_lane_control
- title: Content Lane Control
- purpose: lane separation and lane policy.
- layout_region: main.
- primary_components: content_lane_badge, not_public_postable_banner,
  blocked_reason_stack.
- data_dependencies: lane registry, lane policies.
- required_banners: NOT_PUBLIC_POSTABLE, REVIEW_ONLY.
- required_status_tokens: NOT_PUBLIC_POSTABLE, MANUAL_ONLY, BLOCKED.
- evidence_refs: lane policy references.
- blocked_reason_refs: lane mixing blocked; artifact-backed lane blocked.
- redaction_requirements: no secrets.
- forbidden_controls: publish, lane-mix enable.
- empty_state: "no lanes" UNKNOWN.
- screenshot_safe_behavior: lane policy text safe.
- fixture_id: vm_content_lane_control.
- future_frontend_notes: pre-alpha process lane allowed; grounded-news context
  allowed with citations and non-signal constraints; future artifact-backed lane
  blocked until real approved artifacts exist; lane mixing blocked.

## 3. daily_content_studio
- title: Daily Content Studio
- purpose: daily run packet view, review-only.
- layout_region: main.
- primary_components: draft_inspector_panel, limitation_strip,
  not_public_postable_banner, manual_review_required_banner.
- data_dependencies: daily run packet, source requirements.
- required_banners: NOT_PUBLIC_POSTABLE, REVIEW_ONLY, MANUAL_REVIEW_REQUIRED.
- required_status_tokens: REVIEW_REQUIRED, NOT_PUBLIC_POSTABLE, DEGRADED.
- evidence_refs: source lineage references for each draft.
- blocked_reason_refs: missing source/limitation reasons.
- redaction_requirements: no secrets; no final public-ready copy.
- forbidden_controls: publish, schedule, final-copy generation.
- empty_state: "no run packet" neutral.
- screenshot_safe_behavior: review-only; no final copy.
- fixture_id: vm_daily_content_studio.
- future_frontend_notes: run packet status; source requirements; review-only
  state; not-public-postable banner; no final copy generation.

## 4. draft_inspector
- title: Draft Inspector
- purpose: one draft, deep.
- layout_region: main (three columns).
- primary_components: source_lineage_panel, draft_inspector_panel,
  claim_risk_panel, limitation_strip.
- data_dependencies: selected draft, sources, claims, limitations.
- required_banners: NOT_PUBLIC_POSTABLE, MANUAL_REVIEW_REQUIRED.
- required_status_tokens: REVIEW_REQUIRED, DEGRADED, BLOCKED.
- evidence_refs: per-claim source references.
- blocked_reason_refs: unsupported claim reasons.
- redaction_requirements: no secrets; no public-ready state.
- forbidden_controls: publish, approve-public-ready.
- empty_state: "no draft selected".
- screenshot_safe_behavior: evidence-first; no final public-ready state.
- fixture_id: vm_draft_inspector.
- future_frontend_notes: three-column model — source/lineage, draft/review text,

---

## 5. grounded_news_angle_lab
- title: Grounded News Angle Lab
- purpose: grounded-news angles from supplied sources.
- layout_region: main.
- primary_components: evidence_link_card, proxy_only_warning, limitation_strip,
  not_public_postable_banner.
- data_dependencies: externally-supplied current source metadata.
- required_banners: PROXY_ONLY, NOT_PUBLIC_POSTABLE, NO_SIGNAL_LANGUAGE.
- required_status_tokens: PROXY_ONLY, REVIEW_REQUIRED, DEGRADED.
- evidence_refs: source citations required for each angle.
- blocked_reason_refs: missing-source reasons.
- redaction_requirements: no secrets; references only.
- forbidden_controls: repo web/search call, publish.
- empty_state: "no sources supplied" UNKNOWN.
- screenshot_safe_behavior: citations safe; no signal framing.
- fixture_id: vm_grounded_news_angle_lab.
- future_frontend_notes: news is a hook, not a signal; current source metadata
  must be supplied externally; no repo web/search call.

## 6. publish_readiness_tower
- title: Publish Readiness Tower
- purpose: dry-run readiness matrix and gates.
- layout_region: main.
- primary_components: platform_readiness_card, gate_card,
  credential_redaction_badge, publish_disabled_control.
- data_dependencies: platform capability registry, readiness packet (redacted).
- required_banners: LIVE_DISABLED, DRY_RUN_ONLY, NOT_PUBLIC_POSTABLE,
  SECRET_REDACTED.
- required_status_tokens: LIVE_DISABLED, DRY_RUN_ONLY, BLOCKED, SECRET_REDACTED.
- evidence_refs: readiness evidence references.
- blocked_reason_refs: per-platform blocking reasons.
- redaction_requirements: credentials redacted; no values.
- forbidden_controls: publish-all, one_button_publish_all, connect, OAuth.
- empty_state: "no platforms registered" UNKNOWN.
- screenshot_safe_behavior: every platform LIVE_DISABLED; no secrets.
- fixture_id: vm_publish_readiness_tower.
- future_frontend_notes: platform matrix; dry-run state; live disabled;
  credentials redacted; approval gate required; one-button publish-all disabled.

## 7. telegram_pilot_gate
- title: Telegram Pilot Gate
- purpose: read-only redacted gate status.
- layout_region: main.
- primary_components: telegram_gate_stepper, credential_redaction_badge,
  gate_card, publish_disabled_control.
- data_dependencies: existing telegram gate packet summary (redacted only).
- required_banners: SECRET_REDACTED, LIVE_DISABLED, API_VALIDATED_NO_POST,
  CHANNEL_PERMISSION_UNVALIDATED.
- required_status_tokens: CREDENTIAL_PRESENT_REDACTED, API_VALIDATED_NO_POST,
  CHANNEL_PERMISSION_UNVALIDATED, LIVE_DISABLED.
- evidence_refs: gate evidence references (redacted).
- blocked_reason_refs: next-gate-required reasons.
- redaction_requirements: token/chat-id never shown; presence as token only.
- forbidden_controls: getMe call, sendMessage, posting, live adapter.
- empty_state: "gate not evaluated" UNKNOWN step.
- screenshot_safe_behavior: redacted steps only; no values, no URLs, no responses.
- fixture_id: vm_telegram_pilot_gate.
- future_frontend_notes: bot token presence redacted; target channel presence
  redacted; getMe validation state if available; channel write permission
  unvalidated unless future gate; sendMessage disabled; posting disabled; live
  adapter disabled.

## 8. approval_queue
- title: Approval Queue
- purpose: human review queue.
- layout_region: main.
- primary_components: approval_decision_card, audit_timeline,
  manual_review_required_banner.
- data_dependencies: pending items, decision history.
- required_banners: MANUAL_REVIEW_REQUIRED, REVIEW_ONLY.
- required_status_tokens: REVIEW_REQUIRED, MANUAL_ONLY, PASS, BLOCKED.
- evidence_refs: per-item evidence references.
- blocked_reason_refs: rejection/revision reasons.
- redaction_requirements: history redacted-safe.
- forbidden_controls: auto-approval, publish.
- empty_state: "no items awaiting decision".
- screenshot_safe_behavior: decisions/history safe (redacted).
- fixture_id: vm_approval_queue.
- future_frontend_notes: decision state; revocation support; evidence refs; human
  approval only; no auto-approval.


---

## 9. content_calendar
- title: Content Calendar
- purpose: planning calendar; never public-ready.
- layout_region: main.
- primary_components: content_lane_badge, not_public_postable_banner,
  manual_review_required_banner.
- data_dependencies: planned items by date and lane.
- required_banners: NOT_PUBLIC_POSTABLE, REVIEW_ONLY, MANUAL_REVIEW_REQUIRED.
- required_status_tokens: NOT_PUBLIC_POSTABLE, REVIEW_REQUIRED, MANUAL_ONLY.
- evidence_refs: per-item source-needed references.
- blocked_reason_refs: blocked-item reasons.
- redaction_requirements: no secrets.
- forbidden_controls: scheduled-post, auto-publish, live state.
- empty_state: empty calendar with "planning only" note.
- screenshot_safe_behavior: planning only; no public-ready marking.
- fixture_id: vm_content_calendar.
- future_frontend_notes: item states are idea / source-needed / draft-review /
  blocked / operator-approved-for-manual / manually-posted / metrics-entered. No
  scheduled or live state.

## 10. evidence_vault
- title: Evidence Vault
- purpose: evidence, lineage, sufficiency, discipline.
- layout_region: main.
- primary_components: evidence_link_card, source_lineage_panel,
  data_sufficiency_matrix, freshness_chip, missing_data_row, audit_timeline.
- data_dependencies: task evidence packets, commits, validation results,
  secret-scan results, forbidden-scope matrix.
- required_banners: PROXY_ONLY, MISSING_DATA_VISIBLE, DQR_BLOCKING.
- required_status_tokens: PASS, DEGRADED, PROXY_ONLY, STALE, UNKNOWN, DQR_BLOCKING.
- evidence_refs: required for every artifact.
- blocked_reason_refs: DQR-blocking and missing-data reasons.
- redaction_requirements: no raw vendor data; references only; scans redacted-safe.
- forbidden_controls: live data fetch, publish.
- empty_state: "no evidence" UNKNOWN; never blank.
- screenshot_safe_behavior: references and states only; no raw payloads.
- fixture_id: vm_evidence_vault.
- future_frontend_notes: task evidence packets; commits; validation results;
  secret scans; forbidden-scope matrix; active blockers; next-task discipline.

## 11. visual_export_studio
- title: Visual Export Studio
- purpose: screenshot/briefing-safe export of redacted views.
- layout_region: main.
- primary_components: screenshot_safe_watermark, screenshot_safe_toggle,
  visual_export_preview.
- data_dependencies: current screen view models (redacted).
- required_banners: SECRET_REDACTED, NOT_PUBLIC_POSTABLE, LIVE_DISABLED.
- required_status_tokens: SECRET_REDACTED, NOT_PUBLIC_POSTABLE, LIVE_DISABLED.
- evidence_refs: optional report-card evidence references.
- blocked_reason_refs: none required.
- redaction_requirements: redact secrets/env paths/raw responses/request URLs.
- forbidden_controls: file write, network export, unredacted capture.
- empty_state: "nothing to export".
- screenshot_safe_behavior: safe mode hides secrets; no false readiness.
- fixture_id: vm_visual_export_studio.
- future_frontend_notes: screenshot-safe mode; redacted mode; report-card mode;
  no secrets; no raw vendor data; no false readiness.

## 12. settings_safety_policy
- title: Settings / Safety Policy
- purpose: read-only posture and policy.
- layout_region: main.
- primary_components: safety_policy_panel, posture_summary_row,
  kill_switch_indicator.
- data_dependencies: policy flags (read-only).
- required_banners: LIVE_DISABLED, KILL_SWITCH_ACTIVE, DRY_RUN_ONLY.
- required_status_tokens: LIVE_DISABLED, KILL_SWITCH_ACTIVE, DRY_RUN_ONLY.
- evidence_refs: none required.
- blocked_reason_refs: none required.
- redaction_requirements: no credentials displayed.
- forbidden_controls: API controls, live publishing toggles, credential display.
- empty_state: defaults to safest posture display.
- screenshot_safe_behavior: policy state only; no credentials.
- fixture_id: vm_settings_safety_policy.
- future_frontend_notes: policy display only; no credentials display; no API
  controls; no live publishing toggles.

---

## Coverage Note

This doc defines all 12 required screens. Every screen binds at least 3
components, at least 2 required status tokens, at least 1 safety banner, an
evidence_ref policy, a blocked_action policy, and a redaction policy. No screen
includes any live, publish, schedule, connect, scrape, credential-revealing, or
signal-service capability.

  guardrails/limitations. No final public-ready state.
