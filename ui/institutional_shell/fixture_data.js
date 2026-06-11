/* Institutional Shell Prototype fixture (0160). */
/* Local-only, fixture-driven. Derived from the accepted 0159 valid view-model */
/* fixture. No network, no fetch, no remote URLs, no secrets, no env paths. */
window.CC_INSTITUTIONAL_SHELL_FIXTURE = {
  packet_id: "institutional_shell_prototype_0160",
  shell_mode: "static_local_only",
  view_model_contract_version: "v2",
  global_state: {
    repo_path_label: "cc-live-contentops",
    branch_label: "master",
    accepted_head_short: "15b87ff",
    system_mode: "local_pre_alpha",
    kill_switch_status: "active",
    live_posting_enabled_now: false,
    platform_api_allowed_now: false,
    credential_state_summary: "credentials_present_redacted_no_values",
    current_gate: "telegram_official_docs_credential_validation_gate",
    next_allowed_action: "await_operator_audit",
    active_blockers: [],
    evidence_count: 12,
    known_residual_drift_count: 0,
    not_public_postable_count: 12,
    manual_review_required_count: 12
  },
  global_safety_banners: [
    { id: "LOCAL_ONLY", tone: "locked" },
    { id: "DRY_RUN_ONLY", tone: "locked" },
    { id: "REVIEW_ONLY", tone: "review" },
    { id: "MANUAL_REVIEW_REQUIRED", tone: "review" },
    { id: "NOT_PUBLIC_POSTABLE", tone: "locked" },
    { id: "LIVE_DISABLED", tone: "locked" },
    { id: "KILL_SWITCH_ACTIVE", tone: "blocked" },
    { id: "SECRET_REDACTED", tone: "redacted" },
    { id: "NO_FINANCIAL_ADVICE", tone: "caution" },
    { id: "NO_SIGNAL_LANGUAGE", tone: "caution" }
  ],
  status_token_tones: {
    PASS: "pass",
    DEGRADED: "degraded",
    BLOCKED: "blocked",
    REVIEW_REQUIRED: "review",
    NOT_PUBLIC_POSTABLE: "locked",
    LIVE_DISABLED: "locked",
    UNKNOWN: "unknown",
    PROXY_ONLY: "proxy",
    STALE: "degraded",
    SECRET_REDACTED: "redacted",
    CREDENTIAL_PRESENT_REDACTED: "redacted",
    CREDENTIAL_VALIDATED_NO_POST: "locked",
    API_VALIDATED_NO_POST: "locked",
    CHANNEL_PERMISSION_UNVALIDATED: "degraded",
    DQR_BLOCKING: "blocked",
    FORECAST_NOT_READY: "degraded",
    MANUAL_ONLY: "review",
    DRY_RUN_ONLY: "locked",
    KILL_SWITCH_ACTIVE: "blocked"
  },
  redaction_policy: {
    redact_secrets: true,
    redact_env_paths: true,
    redact_raw_platform_responses: true,
    redact_request_urls: true,
    no_raw_vendor_data: true
  },
  screenshot_safe_mode: {
    present: true,
    active_label: "SCREENSHOT-SAFE / LOCAL ONLY / NOT PUBLIC-POSTABLE / LIVE DISABLED",
    note: "Secrets, env paths, raw platform responses, raw request URLs and raw vendor data are redacted."
  },
  components_catalog: [
    "global_safety_ribbon", "command_center_status_header", "gate_card",
    "blocked_reason_stack", "evidence_link_card", "source_lineage_panel",
    "data_sufficiency_matrix", "forecast_readiness_card", "credential_redaction_badge",
    "platform_readiness_card", "telegram_gate_stepper", "approval_decision_card",
    "audit_timeline", "draft_inspector_panel", "claim_risk_panel",
    "content_lane_badge", "publish_disabled_control", "screenshot_safe_watermark",
    "limitation_strip", "freshness_chip", "proxy_only_warning", "missing_data_row",
    "not_public_postable_banner", "manual_review_required_banner",
    "kill_switch_indicator", "forbidden_action_tooltip"
  ],
  command_center_detail: {
    hero_status_band: {
      title: "Capital Chronicle ContentOps Command Center",
      system_mode: "local / static / fixture-driven",
      accepted_head: "1c03ca0",
      kill_switch: "active",
      public_state: "not_public_postable",
      live_api_state: "disabled",
      current_gate: "0161 command center screen implementation",
      next_allowed_action: "AWAIT OPERATOR/CHATGPT AUDIT_OF_0161_EVIDENCE_BEFORE_ANY_NEXT_TASK"
    },
    executive_status_cards: [
      { id: "system_safety", title: "System Safety", state: "PASS", detail: "Kill switch active. Live disabled. Review-only. Not public-postable." },
      { id: "build_baseline", title: "Build Baseline", state: "PASS", detail: "Accepted HEAD 1c03ca0. 0160 static shell prototype accepted." },
      { id: "publish_automation", title: "Publish Automation", state: "LIVE_DISABLED", detail: "Dry-run only. Platform API disabled. One-button publish-all disabled." },
      { id: "telegram_pilot_gate", title: "Telegram Pilot Gate", state: "API_VALIDATED_NO_POST", detail: "Credentials redacted. sendMessage disabled. Channel permission unvalidated." },
      { id: "evidence_audit", title: "Evidence / Audit", state: "PASS", detail: "Full suite green at fixture baseline. Secret scan clean. Forbidden scope clean." },
      { id: "ui_rebuild_track", title: "UI Rebuild Track", state: "REVIEW_REQUIRED", detail: "0157-0160 accepted. 0161 current. Antigravity future-only." },
      { id: "content_studio_track", title: "Content Studio Track", state: "REVIEW_REQUIRED", detail: "Review-only. Source/evidence required. No final social copy." },
      { id: "residual_drift", title: "Residual Drift", state: "MANUAL_ONLY", detail: "Local env file and strategy docs untouched/untracked. No cleanup allowed." }
    ],
    gate_timeline: [
      { gate: "0157", label: "UI/UX master plan", state: "PASS" },
      { gate: "0158", label: "design system", state: "PASS" },
      { gate: "0159", label: "view-model contract", state: "PASS" },
      { gate: "0160", label: "static shell prototype", state: "PASS" },
      { gate: "0161", label: "command center screen", state: "REVIEW_REQUIRED" },
      { gate: "0162", label: "content studio rebuild", state: "UNKNOWN" },
      { gate: "0163", label: "publish readiness tower", state: "UNKNOWN" },
      { gate: "0164", label: "evidence vault", state: "UNKNOWN" },
      { gate: "0165", label: "calendar/workflow board", state: "UNKNOWN" },
      { gate: "0166", label: "visual export/screenshot-safe mode", state: "UNKNOWN" },
      { gate: "0167", label: "Antigravity browser QA", state: "UNKNOWN" },
      { gate: "0168", label: "Cline polish pass", state: "UNKNOWN" }
    ],
    blocked_action_matrix: [
      { action: "live_posting", state: "disabled" },
      { action: "scheduler", state: "disabled" },
      { action: "platform_api", state: "disabled" },
      { action: "provider_llm_api", state: "disabled" },
      { action: "scraping", state: "disabled" },
      { action: "autonomous_replies_dms", state: "disabled" },
      { action: "one_button_publish_all", state: "disabled" },
      { action: "public_ready_final_copy", state: "disabled" },
      { action: "credential_display", state: "disabled" },
      { action: "raw_env_paths", state: "disabled" },
      { action: "raw_request_urls", state: "disabled" },
      { action: "raw_platform_responses", state: "disabled" },
      { action: "broker_execution_order_routing", state: "disabled" }
    ],
    evidence_summary: {
      full_suite_result: "1402 passed, 28 skipped (fixture baseline)",
      focused_tests_result: "shell + command center focused tests passing (fixture baseline)",
      cli_summaries: "passing",
      secret_scan_status: "clean (0 secrets)",
      forbidden_scope_status: "clean",
      git_status_summary: "only known residual drift untouched",
      known_residual_drift: "untouched",
      evidence_packet_required: true
    },
    telegram_gate_state: {
      credential_presence: "redacted_presence_only",
      official_docs_gate: "implemented",
      live_getme: "not_run_unless_explicitly_executed_later",
      channel_write_permission: "unvalidated",
      send_message: "disabled",
      live_adapter: "disabled",
      posting: "disabled",
      next_step: "requires separate audit/gate"
    },
    publish_automation_state: {
      mode: "dry_run_only",
      platform_capability_registry: "modeled",
      dry_run_batch_manifest: "modeled",
      redacted_audit: "modeled",
      manual_approval_required: true,
      live: "disabled",
      one_button_publish_all: "disabled"
    },
    content_studio_state: {
      content_lanes: "process lane + grounded-news context lane",
      grounded_news: "hook_not_signal",
      review_only: true,
      source_evidence_required: true,
      not_public_postable: true,
      final_social_copy_generated_by_repo: false
    },
    ui_rebuild_state: {
      accepted: ["0157", "0158", "0159", "0160"],
      current: "0161",
      antigravity: "future_only",
      browser_qa: "none_yet",
      screenshots: "none_yet"
    },
    residual_drift_panel: {
      env_local: "exists locally; must remain untouched/untracked",
      strategy_docs_pdfs: "untracked if present; untouched",
      old_bundles: "project_sources_bundle_AFTER_0074 and recovered_strategy_docs untouched",
      cleanup_commands_allowed: false
    },
    next_allowed_action_panel: {
      directive: "AWAIT OPERATOR/CHATGPT AUDIT_OF_0161_EVIDENCE_BEFORE_ANY_NEXT_TASK",
      future_task: "0162 Content Studio Rebuild only after audit"
    }
  },
  content_studio_detail: {
    hero_status_band: {
      title: "Capital Chronicle Content Studio",
      content_mode: "review-only / fixture-driven / local-only",
      public_state: "not_public_postable",
      generation_state: "external/manual draft only",
      current_gate: "0162 Content Studio screen rebuild",
      next_allowed_action: "AWAIT OPERATOR/CHATGPT AUDIT_OF_0162_EVIDENCE_BEFORE_ANY_NEXT_TASK"
    },
    safety_banners: [
      "LOCAL_ONLY", "REVIEW_ONLY", "MANUAL_REVIEW_REQUIRED", "NOT_PUBLIC_POSTABLE",
      "LIVE_DISABLED", "SECRET_REDACTED", "NO_FINANCIAL_ADVICE", "NO_SIGNAL_LANGUAGE",
      "MISSING_DATA_VISIBLE", "FORECAST_NOT_READY"
    ],
    content_lanes: [
      {
        lane_id: "pre_alpha_process",
        title: "Pre-Alpha Process Lane",
        state: "allowed_review_only",
        detail: "Process/philosophy/education narratives about how Capital Chronicle works. Review-only, never auto-published."
      },
      {
        lane_id: "grounded_news_context",
        title: "Grounded News Context Lane",
        state: "allowed_with_constraints",
        detail: "Source-cited educational/process context only. News is a hook, not a signal. Source metadata supplied externally."
      },
      {
        lane_id: "future_artifact_backed",
        title: "Future Artifact-Backed Lane",
        state: "blocked",
        detail: "Blocked until real approved Capital Chronicle artifacts exist. Fake fixture artifacts are not allowed."
      }
    ],
    lane_rules: {
      lane_mixing: "blocked",
      future_artifact_fixture_use: "blocked",
      source_artifact_ids_invented: "blocked",
      capital_chronicle_alpha_implied_before_approval: "blocked"
    },
    grounded_news_rule_panel: {
      news_is_hook_not_signal: true,
      source_metadata_supplied_externally: true,
      repo_searches_or_fetches_news: false,
      market_direction_claims: "blocked",
      model_predicts_claims: "blocked",
      actionable_trade_framing: "blocked"
    },
    source_evidence_requirements: [
      { field: "source_url", requirement: "required for factual/current claims" },
      { field: "source_date", requirement: "required for factual/current claims" },
      { field: "source_summary", requirement: "required" },
      { field: "claim_risk_notes", requirement: "required" },
      { field: "freshness_label", requirement: "required" },
      { field: "limitation_label", requirement: "required" },
      { field: "artifact_id", requirement: "real artifact ID required later for artifact-backed content" },
      { field: "missing_source", requirement: "blocks publish-readiness" }
    ],
    draft_review_only_panel: {
      draft_origin: "externally drafted / manual draft only",
      repo_calls_provider_llm_api: false,
      draft_is_review_only: true,
      final_public_copy_generation: "disabled",
      manual_jim_review_required: true
    },
    claim_risk_classifier: [
      { class: "first_party_philosophy", handling: "allowed" },
      { class: "evergreen_education", handling: "allowed" },
      { class: "cited_factual_claim", handling: "allowed_with_citation" },
      { class: "current_factual_claim_requiring_citation", handling: "requires_citation" },
      { class: "market_sensitive_claim", handling: "blocked_or_transformed_to_evergreen_education" },
      { class: "forbidden_claim", handling: "blocked" }
    ],
    guardrail_results: [
      { category: "buy_sell_hold", state: "forbidden" },
      { category: "long_short", state: "forbidden" },
      { category: "position_sizing", state: "forbidden" },
      { category: "entries_exits", state: "forbidden" },
      { category: "target_prices", state: "forbidden" },
      { category: "guaranteed_prediction", state: "forbidden" },
      { category: "signal_service_framing", state: "forbidden" },
      { category: "execution_broker_order_routing", state: "forbidden" },
      { category: "fake_alpha", state: "forbidden" },
      { category: "unsupported_numeric_market_claims", state: "forbidden" },
      { category: "raw_vendor_data_redistribution", state: "forbidden" },
      { category: "hidden_missing_degraded_proxy_data", state: "forbidden" }
    ],
    limitations_refusal_mode: {
      missing_stays_missing: true,
      degraded_stays_degraded: true,
      proxy_only_is_labeled: true,
      forecast_readiness_can_stay_blocked: true,
      no_forecast_is_valid_output: true,
      uncertainty_must_be_visible: true
    },
    platform_fit_preview: [
      { platform: "substack", fit: "long-form home", mode: "dry_run_read_only" },
      { platform: "linkedin", fit: "professional process insight", mode: "dry_run_read_only" },
      { platform: "x", fit: "short education/process hooks", mode: "dry_run_read_only" },
      { platform: "threads", fit: "conversational mirror", mode: "dry_run_read_only" },
      { platform: "telegram", fit: "future pilot only after gates", mode: "dry_run_read_only" }
    ],
    platform_fit_constraints: {
      export_to_platform: "disabled",
      schedule: "disabled",
      publish: "disabled",
      live_api: "disabled"
    },
    editorial_quality_state: {
      review_completeness: "fixture_static",
      evidence_completeness: "fixture_static",
      limitation_visibility: "fixture_static",
      guardrail_cleanliness: "fixture_static",
      manual_review_pending: true,
      implies_publish_ready: false
    },
    decision_ledger_handoff: {
      operator_decision_required: true,
      approval_is_automatic: false,
      revocation_supported: true,
      evidence_refs_required: true,
      public_ready_approval_enabled_now: false
    },
    draft_inspector_handoff: {
      next_drilldown_surface: "draft_inspector",
      source_lineage_must_remain_visible: true,
      guardrails_must_remain_visible: true
    },
    blocked_action_matrix: [
      { action: "generate_final_public_copy", state: "disabled" },
      { action: "auto_approve", state: "disabled" },
      { action: "publish", state: "disabled" },
      { action: "schedule", state: "disabled" },
      { action: "provider_llm_api", state: "disabled" },
      { action: "news_search_fetch", state: "disabled" },
      { action: "platform_api", state: "disabled" },
      { action: "scrape_metrics", state: "disabled" },
      { action: "artifact_backed_without_real_artifacts", state: "disabled" },
      { action: "create_market_signal", state: "disabled" },
      { action: "credential_display", state: "disabled" },
      { action: "one_button_publish_all", state: "disabled" }
    ],
    evidence_summary: {
      content_studio_workbench: "linked (concept)",
      grounded_news_rule: "linked",
      external_draft_review: "linked",
      decision_ledger: "linked",
      platform_fit_readiness_dry_run: "linked",
      evidence_packet_required: true
    },
    next_allowed_action_panel: {
      directive: "AWAIT OPERATOR/CHATGPT AUDIT_OF_0162_EVIDENCE_BEFORE_ANY_NEXT_TASK",
      future_task: "0163 Publish Readiness Tower only after audit"
    }
  },
  publish_readiness_tower_detail: {
    hero_status_band: {
      title: "Capital Chronicle Publish Readiness Tower",
      publish_mode: "dry-run / readiness-only / local-only",
      public_state: "not_public_postable",
      live_state: "disabled",
      platform_api_state: "disabled",
      scheduler_state: "disabled",
      current_gate: "0163 Publish Readiness Tower screen",
      next_allowed_action: "AWAIT OPERATOR/CHATGPT AUDIT_OF_0163_EVIDENCE_BEFORE_ANY_NEXT_TASK"
    },
    safety_banners: [
      "LOCAL_ONLY", "DRY_RUN_ONLY", "REVIEW_ONLY", "MANUAL_REVIEW_REQUIRED",
      "NOT_PUBLIC_POSTABLE", "LIVE_DISABLED", "API_VALIDATED_NO_POST",
      "CHANNEL_PERMISSION_UNVALIDATED", "KILL_SWITCH_ACTIVE", "SECRET_REDACTED",
      "NO_FINANCIAL_ADVICE", "NO_SIGNAL_LANGUAGE"
    ],
    platform_capability_registry_panel: [
      { platform_id: "telegram", display_name: "Telegram", intended_use: "future pilot channel", dry_run_render: "modeled", credential_state: "redacted_presence_only", docs_verification: "implemented", manual_review_required: true, not_public_postable: true, live_api: "disabled", scheduling: "disabled", next_blocker: "channel write permission unvalidated; separate GO required" },
      { platform_id: "x", display_name: "X", intended_use: "short education/process hooks", dry_run_render: "modeled", credential_state: "not_configured_redacted", docs_verification: "pending", manual_review_required: true, not_public_postable: true, live_api: "disabled", scheduling: "disabled", next_blocker: "docs verification + credentials pending" },
      { platform_id: "linkedin", display_name: "LinkedIn", intended_use: "professional process insight", dry_run_render: "modeled", credential_state: "not_configured_redacted", docs_verification: "pending", manual_review_required: true, not_public_postable: true, live_api: "disabled", scheduling: "disabled", next_blocker: "docs verification + credentials pending" },
      { platform_id: "threads", display_name: "Threads", intended_use: "conversational mirror", dry_run_render: "modeled", credential_state: "not_configured_redacted", docs_verification: "pending", manual_review_required: true, not_public_postable: true, live_api: "disabled", scheduling: "disabled", next_blocker: "docs verification + credentials pending" },
      { platform_id: "substack", display_name: "Substack", intended_use: "long-form home", dry_run_render: "modeled", credential_state: "not_configured_redacted", docs_verification: "pending", manual_review_required: true, not_public_postable: true, live_api: "disabled", scheduling: "disabled", next_blocker: "docs verification + credentials pending" },
      { platform_id: "facebook_page", display_name: "Facebook Page", intended_use: "process distribution", dry_run_render: "modeled", credential_state: "not_configured_redacted", docs_verification: "pending", manual_review_required: true, not_public_postable: true, live_api: "disabled", scheduling: "disabled", next_blocker: "docs verification + credentials pending" },
      { platform_id: "instagram", display_name: "Instagram", intended_use: "visual process recap", dry_run_render: "modeled", credential_state: "not_configured_redacted", docs_verification: "pending", manual_review_required: true, not_public_postable: true, live_api: "disabled", scheduling: "disabled", next_blocker: "docs verification + credentials pending" },
      { platform_id: "tiktok", display_name: "TikTok", intended_use: "short explainer", dry_run_render: "modeled", credential_state: "not_configured_redacted", docs_verification: "pending", manual_review_required: true, not_public_postable: true, live_api: "disabled", scheduling: "disabled", next_blocker: "docs verification + credentials pending" }
    ],
    dry_run_batch_manifest_panel: {
      dry_run_only: true,
      fixture_mock_payload_only: true,
      real_platform_payload_dispatch: false,
      source_lineage_required: true,
      limitation_visibility_required: true,
      idempotency_policy_modeled: true,
      partial_failure_policy_modeled: true,
      redacted_audit_required: true,
      manual_approval_gate_required: true
    },
    manual_approval_gate_panel: {
      approval_required_before_live_publish: true,
      current_state: "review_only_dry_run",
      public_ready_approval_enabled_now: false,
      operator_decision_required: true,
      revocation_supported: true,
      auto_approval: false
    },
    kill_switch_gate_panel: {
      kill_switch_active: true,
      blocks_publishing: true,
      no_publish_while_active: true,
      must_be_audited_in_future_live_tasks: true
    },
    credential_secret_state_panel: {
      credentials_local_only_out_of_band: true,
      credential_values_displayed: false,
      token_chat_id_redacted: true,
      env_path_shown: false,
      secret_redaction_required: true,
      credential_read_in_this_task: false,
      validation_implies_posting_permission: false
    },
    redacted_audit_gate_panel: {
      audit_events_modeled: true,
      unredacted_secrets_in_audit: false,
      raw_request_urls_in_audit: false,
      raw_platform_responses_in_audit: false,
      raw_env_path_in_audit: false,
      future_platform_responses_must_be_redacted: true,
      evidence_packet_must_be_secret_safe: true
    },
    official_docs_gate_panel: {
      per_platform_docs_verification_required: true,
      telegram_official_docs_gate: "implemented",
      other_platforms_require_future_verification: true,
      docs_verification_is_runtime_authority: false,
      docs_verification_enables_live_posting: false
    },
    telegram_pilot_tower_panel: {
      sub_gates: [
        { gate: "credential_presence", state: "redacted_presence_only" },
        { gate: "official_docs_verification", state: "implemented" },
        { gate: "getme_token_validation", state: "gate_implemented_live_run_status_separate_later" },
        { gate: "channel_write_permission", state: "unvalidated" },
        { gate: "dry_run_payload_preview", state: "modeled_only" },
        { gate: "manual_approval", state: "required" },
        { gate: "kill_switch", state: "active" },
        { gate: "send_message", state: "disabled" },
        { gate: "live_adapter", state: "disabled" },
        { gate: "posting", state: "disabled" },
        { gate: "scheduler", state: "disabled" }
      ],
      next_step: "next Telegram live step requires a separate explicit operator/ChatGPT GO"
    },
    publish_disabled_control_surface: [
      { control: "publish", state: "disabled" },
      { control: "schedule", state: "disabled" },
      { control: "connect_api", state: "disabled" },
      { control: "oauth", state: "disabled" },
      { control: "send_message", state: "disabled" },
      { control: "getme_live_call", state: "disabled" },
      { control: "upload_media", state: "disabled" },
      { control: "publish_all", state: "disabled" },
      { control: "auto_post", state: "disabled" },
      { control: "scrape_metrics", state: "disabled" },
      { control: "reply_dm", state: "disabled" }
    ],
    idempotency_partial_failure_panel: {
      idempotency_required_before_live: true,
      duplicate_prevention_required: true,
      partial_failure_policy_required: true,
      rollback_manual_fallback_required: true,
      current_live_retry_loop: false
    },
    future_live_handoff_panel: {
      live_adapter_absent_disabled: true,
      one_platform_live_requires_explicit_go: true,
      autonomous_posting: false,
      autonomous_replies_dms: false,
      platform_by_platform_rollout_only: true
    },
    evidence_summary: {
      publish_automation_readiness: "linked",
      platform_capability_registry: "linked",
      dry_run_manifest: "linked",
      credential_policy: "linked",
      redacted_audit_log: "linked",
      telegram_gate: "linked",
      validation_test_scan_evidence_required: true
    },
    next_allowed_action_panel: {
      directive: "AWAIT OPERATOR/CHATGPT AUDIT_OF_0163_EVIDENCE_BEFORE_ANY_NEXT_TASK",
      future_task: "0164 Evidence Vault only after audit"
    }
  },
  screens: [
    {
      screen_id: "command_center",
      title: "Command Center",
      purpose: "Global operational status landing. State before action.",
      primary_components: ["global_safety_ribbon", "command_center_status_header", "blocked_reason_stack", "kill_switch_indicator"],
      required_banners: ["LOCAL_ONLY", "KILL_SWITCH_ACTIVE", "LIVE_DISABLED"],
      required_status_tokens: ["PASS", "DEGRADED", "BLOCKED", "KILL_SWITCH_ACTIVE"],
      evidence_refs: ["evidence_vault_link"],
      blocked_reasons: ["Live posting disabled by kill switch", "Awaiting operator audit before next task"],
      blocked_action_policy: "no_live_action",
      redaction_state: "no_secrets",
      forbidden_controls: ["publish", "schedule", "connect", "oauth", "one_button_publish_all"],
      screenshot_safe_behavior: "redacted_no_secrets_no_false_readiness"
    },
    {
      screen_id: "content_lane_control",
      title: "Content Lane Control",
      purpose: "Lane separation and lane policy. No lane mixing.",
      primary_components: ["content_lane_badge", "not_public_postable_banner", "blocked_reason_stack"],
      required_banners: ["NOT_PUBLIC_POSTABLE", "REVIEW_ONLY"],
      required_status_tokens: ["NOT_PUBLIC_POSTABLE", "MANUAL_ONLY", "BLOCKED"],
      evidence_refs: ["lane_policy_ref"],
      blocked_reasons: ["Artifact-backed lane blocked until real approved artifacts exist", "Lane mixing blocked"],
      blocked_action_policy: "no_lane_mixing",
      redaction_state: "no_secrets",
      forbidden_controls: ["publish", "schedule", "connect", "oauth", "one_button_publish_all", "lane_mix_enable"],
      screenshot_safe_behavior: "redacted_no_secrets_no_false_readiness"
    },
    {
      screen_id: "daily_content_studio",
      title: "Daily Content Studio",
      purpose: "Daily run packet view, review-only. No final copy generation.",
      primary_components: ["draft_inspector_panel", "limitation_strip", "not_public_postable_banner", "manual_review_required_banner"],
      required_banners: ["NOT_PUBLIC_POSTABLE", "REVIEW_ONLY", "MANUAL_REVIEW_REQUIRED"],
      required_status_tokens: ["REVIEW_REQUIRED", "NOT_PUBLIC_POSTABLE", "DEGRADED"],
      evidence_refs: ["source_lineage_ref"],
      blocked_reasons: ["Draft requires source and limitation context before review can complete"],
      blocked_action_policy: "no_final_copy_generation",
      redaction_state: "no_secrets_no_final_copy",
      forbidden_controls: ["publish", "schedule", "connect", "oauth", "one_button_publish_all", "final_copy_generation"],
      screenshot_safe_behavior: "redacted_no_secrets_no_false_readiness"
    },
    {
      screen_id: "draft_inspector",
      title: "Draft Inspector",
      purpose: "One draft deep: source/lineage, draft/review text, guardrails/limitations.",
      primary_components: ["source_lineage_panel", "draft_inspector_panel", "claim_risk_panel", "limitation_strip"],
      required_banners: ["NOT_PUBLIC_POSTABLE", "MANUAL_REVIEW_REQUIRED"],
      required_status_tokens: ["REVIEW_REQUIRED", "DEGRADED", "BLOCKED"],
      evidence_refs: ["per_claim_source_ref"],
      blocked_reasons: ["Unsupported numeric/current claim must be sourced before review"],
      blocked_action_policy: "no_public_ready_state",
      redaction_state: "no_secrets",
      forbidden_controls: ["publish", "schedule", "connect", "oauth", "one_button_publish_all", "approve_public_ready"],
      screenshot_safe_behavior: "redacted_no_secrets_no_false_readiness"
    },
    {
      screen_id: "grounded_news_angle_lab",
      title: "Grounded News Angle Lab",
      purpose: "Grounded-news angles from supplied sources. News is a hook, not a signal.",
      primary_components: ["evidence_link_card", "proxy_only_warning", "limitation_strip", "not_public_postable_banner"],
      required_banners: ["PROXY_ONLY", "NOT_PUBLIC_POSTABLE", "NO_SIGNAL_LANGUAGE"],
      required_status_tokens: ["PROXY_ONLY", "REVIEW_REQUIRED", "DEGRADED"],
      evidence_refs: ["angle_citation_ref"],
      blocked_reasons: ["Current source metadata must be supplied externally; no repo web/search call"],
      blocked_action_policy: "no_repo_web_search_call",
      redaction_state: "no_secrets",
      forbidden_controls: ["publish", "schedule", "connect", "oauth", "one_button_publish_all", "repo_web_search_call"],
      screenshot_safe_behavior: "redacted_no_secrets_no_false_readiness"
    },
    {
      screen_id: "publish_readiness_tower",
      title: "Publish Readiness Tower",
      purpose: "Dry-run readiness matrix and gates. Live disabled, credentials redacted.",
      primary_components: ["platform_readiness_card", "gate_card", "credential_redaction_badge", "publish_disabled_control"],
      required_banners: ["LIVE_DISABLED", "DRY_RUN_ONLY", "NOT_PUBLIC_POSTABLE", "SECRET_REDACTED"],
      required_status_tokens: ["LIVE_DISABLED", "DRY_RUN_ONLY", "BLOCKED", "SECRET_REDACTED"],
      evidence_refs: ["readiness_evidence_ref"],
      blocked_reasons: ["Platform API disabled", "Scheduler disabled", "Manual approval required", "One-button publish-all disabled"],
      blocked_action_policy: "no_publish_all",
      redaction_state: "credentials_redacted_no_values",
      forbidden_controls: ["publish", "schedule", "connect", "oauth", "one_button_publish_all"],
      screenshot_safe_behavior: "redacted_no_secrets_no_false_readiness"
    },
    {
      screen_id: "telegram_pilot_gate",
      title: "Telegram Pilot Gate",
      purpose: "Read-only redacted gate status. No live calls from the UI.",
      primary_components: ["telegram_gate_stepper", "credential_redaction_badge", "gate_card", "publish_disabled_control"],
      required_banners: ["SECRET_REDACTED", "LIVE_DISABLED", "API_VALIDATED_NO_POST", "CHANNEL_PERMISSION_UNVALIDATED"],
      required_status_tokens: ["CREDENTIAL_PRESENT_REDACTED", "API_VALIDATED_NO_POST", "CHANNEL_PERMISSION_UNVALIDATED", "LIVE_DISABLED"],
      evidence_refs: ["gate_evidence_ref"],
      blocked_reasons: ["Bot token presence redacted only", "Target channel presence redacted only", "Channel write permission unvalidated", "Next gate required before posting"],
      blocked_action_policy: "no_getme_no_sendmessage_no_post",
      redaction_state: "token_chatid_never_shown",
      forbidden_controls: ["publish", "schedule", "connect", "oauth", "one_button_publish_all", "getme_call", "sendmessage", "live_adapter"],
      gate_steps: [
        { step: "presence_check", state: "CREDENTIAL_PRESENT_REDACTED" },
        { step: "official_docs", state: "PASS" },
        { step: "getme_validation_no_post", state: "API_VALIDATED_NO_POST" },
        { step: "channel_permission_future", state: "CHANNEL_PERMISSION_UNVALIDATED" },
        { step: "explicit_go_future", state: "LIVE_DISABLED" }
      ],
      screenshot_safe_behavior: "redacted_no_secrets_no_false_readiness"
    },
    {
      screen_id: "approval_queue",
      title: "Approval Queue",
      purpose: "Human review queue. Human approval only, no auto-approval.",
      primary_components: ["approval_decision_card", "audit_timeline", "manual_review_required_banner"],
      required_banners: ["MANUAL_REVIEW_REQUIRED", "REVIEW_ONLY"],
      required_status_tokens: ["REVIEW_REQUIRED", "MANUAL_ONLY", "PASS", "BLOCKED"],
      evidence_refs: ["per_item_evidence_ref"],
      blocked_reasons: ["Decision requires a human reviewer", "No auto-approval path"],
      blocked_action_policy: "no_auto_approval",
      redaction_state: "history_redacted_safe",
      forbidden_controls: ["publish", "schedule", "connect", "oauth", "one_button_publish_all", "auto_approval"],
      screenshot_safe_behavior: "redacted_no_secrets_no_false_readiness"
    },
    {
      screen_id: "content_calendar",
      title: "Content Calendar",
      purpose: "Planning calendar; never public-ready. No scheduling or live state.",
      primary_components: ["content_lane_badge", "not_public_postable_banner", "manual_review_required_banner"],
      required_banners: ["NOT_PUBLIC_POSTABLE", "REVIEW_ONLY", "MANUAL_REVIEW_REQUIRED"],
      required_status_tokens: ["NOT_PUBLIC_POSTABLE", "REVIEW_REQUIRED", "MANUAL_ONLY"],
      evidence_refs: ["item_source_needed_ref"],
      blocked_reasons: ["No scheduled state", "No system live-publish", "No auto-publish-ready", "No public-ready marking"],
      blocked_action_policy: "no_scheduled_or_live_state",
      redaction_state: "no_secrets",
      allowed_item_states: ["idea", "source-needed", "draft-review", "blocked", "operator-approved-for-manual", "manually-posted", "metrics-entered"],
      forbidden_controls: ["publish", "schedule", "connect", "oauth", "one_button_publish_all", "scheduled_post", "auto_publish", "live_state"],
      screenshot_safe_behavior: "redacted_no_secrets_no_false_readiness"
    },
    {
      screen_id: "evidence_vault",
      title: "Evidence Vault",
      purpose: "Evidence, lineage, data sufficiency, freshness, missing data — all visible.",
      primary_components: ["evidence_link_card", "source_lineage_panel", "data_sufficiency_matrix", "freshness_chip", "missing_data_row", "audit_timeline"],
      required_banners: ["PROXY_ONLY", "MISSING_DATA_VISIBLE", "DQR_BLOCKING"],
      required_status_tokens: ["PASS", "DEGRADED", "PROXY_ONLY", "STALE", "UNKNOWN", "DQR_BLOCKING"],
      evidence_refs: ["artifact_evidence_ref"],
      blocked_reasons: ["Data quality / sufficiency blocking on at least one dimension"],
      blocked_action_policy: "no_live_data_fetch",
      redaction_state: "no_raw_vendor_data_references_only",
      forbidden_controls: ["publish", "schedule", "connect", "oauth", "one_button_publish_all", "live_data_fetch"],
      screenshot_safe_behavior: "redacted_no_secrets_no_false_readiness"
    },
    {
      screen_id: "visual_export_studio",
      title: "Visual Export Studio",
      purpose: "Screenshot/briefing-safe export of redacted views. No file/network export.",
      primary_components: ["screenshot_safe_watermark", "screenshot_safe_toggle", "visual_export_preview"],
      required_banners: ["SECRET_REDACTED", "NOT_PUBLIC_POSTABLE", "LIVE_DISABLED"],
      required_status_tokens: ["SECRET_REDACTED", "NOT_PUBLIC_POSTABLE", "LIVE_DISABLED"],
      evidence_refs: ["report_card_evidence_ref"],
      blocked_reasons: ["No unredacted capture", "No file write", "No network export"],
      blocked_action_policy: "no_unredacted_capture",
      redaction_state: "redact_secrets_env_responses_urls",
      forbidden_controls: ["publish", "schedule", "connect", "oauth", "one_button_publish_all", "file_write", "network_export", "unredacted_capture"],
      screenshot_safe_behavior: "redacted_no_secrets_no_false_readiness"
    },
    {
      screen_id: "settings_safety_policy",
      title: "Settings / Safety Policy",
      purpose: "Read-only posture and policy. No credentials, no API or live toggles.",
      primary_components: ["safety_policy_panel", "posture_summary_row", "kill_switch_indicator"],
      required_banners: ["LIVE_DISABLED", "KILL_SWITCH_ACTIVE", "DRY_RUN_ONLY"],
      required_status_tokens: ["LIVE_DISABLED", "KILL_SWITCH_ACTIVE", "DRY_RUN_ONLY"],
      evidence_refs: [],
      blocked_reasons: ["Policy display only", "No credential values displayed", "No API or live publishing toggles"],
      blocked_action_policy: "no_credential_display",
      redaction_state: "no_credentials_displayed",
      policy_flags: [
        { name: "live_posting_enabled", state: "false", read_only: true },
        { name: "scheduler_enabled", state: "false", read_only: true },
        { name: "scraping_enabled", state: "false", read_only: true },
        { name: "kill_switch", state: "active", read_only: true }
      ],
      forbidden_controls: ["publish", "schedule", "connect", "oauth", "one_button_publish_all", "api_controls", "live_publishing_toggle", "credential_display"],
      screenshot_safe_behavior: "redacted_no_secrets_no_false_readiness"
    }
  ]
};
