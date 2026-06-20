import type { LocalPreflightBundlePacket } from '../types';

export const preflightBundlePacket: LocalPreflightBundlePacket = {
  "candidate_field_count": 27,
  "generated_at_epoch": 0,
  "global_blocked_reasons": [
    "x_app_access_gap",
    "spend_gate_unresolved",
    "rate_budget_gap",
    "read_only_endpoint_proof_gap",
    "no_arbitrary_dm_allowed",
    "operator_inbox_proof_required",
    "channel_admin_proof_required",
    "bot_permission_gap",
    "channel_state_symbolic_only",
    "manual_export_only",
    "linkedin_organization_page_proof_missing",
    "meta_app_review_closed",
    "meta_app_account_proof_required",
    "tiktok_app_audit_closed",
    "creator_account_proof_required",
    "video_publish_proof_required",
    "youtube_quota_unresolved",
    "youtube_oauth_flow_closed",
    "upload_proof_required"
  ],
  "global_missing_proofs": [
    "x_app_access_gap",
    "spend_gate_unresolved",
    "rate_budget_gap",
    "read_only_endpoint_proof_gap",
    "no_arbitrary_dm_allowed",
    "operator_inbox_proof_required",
    "channel_admin_proof_required",
    "bot_permission_gap",
    "channel_state_symbolic_only",
    "manual_export_only",
    "linkedin_organization_page_proof_missing",
    "meta_app_review_closed",
    "meta_app_account_proof_required",
    "tiktok_app_audit_closed",
    "creator_account_proof_required",
    "video_publish_proof_required",
    "youtube_quota_unresolved",
    "youtube_oauth_flow_closed",
    "upload_proof_required"
  ],
  "matrix_version": "0174UU_LOCAL_PREFLIGHT_BUNDLE_V5_READ_MODEL_PRECHECK_CONTRACT_V1",
  "next_recommended_task": "TASK_CONTENTOPS_0174UV_V5_COCKPIT_READ_MODEL_INTEGRATION_V0",
  "packet_hash": "c853aefbe2574348acd1f708044a893a5372eb89bb28b4cba69ecfe6216ae5fe",
  "packet_hash_algorithm": "sha256",
  "packet_id": "local_preflight_bundle_v5_read_model_precheck_packet_d783ae2ac1c153dcb6bf709a",
  "platform_count": 10,
  "platform_states": [
    {
      "account_binding_status": "symbolic",
      "approval_gate_status": "blocked",
      "blocked_reasons": [
        "x_app_access_gap",
        "spend_gate_unresolved",
        "rate_budget_gap",
        "read_only_endpoint_proof_gap"
      ],
      "credential_mock_audit_status": "blocked",
      "credential_slot_status": "key_names_only",
      "dispatch_ready": false,
      "endpoint_family": "live_read_only",
      "evidence_packet_status": "blocked",
      "hidden_or_absent_fields": [
        "raw_secrets",
        "credential_values",
        "token_slices",
        "hashes",
        "raw_api_responses",
        "env_values"
      ],
      "kill_switch_status": "open_fails_closed",
      "live_read_allowed": false,
      "live_write_allowed": false,
      "manual_export_status": "not_applicable",
      "missing_proofs": [
        "x_app_access_gap",
        "spend_gate_unresolved",
        "rate_budget_gap",
        "read_only_endpoint_proof_gap"
      ],
      "platform_id": "x",
      "platform_role": "primary_distribution",
      "preflight_simulation_status": "blocked",
      "primary_or_secondary_or_expansion": "primary",
      "public_post_allowed": false,
      "rate_budget_status": "blocked",
      "readiness_cleared": false,
      "redaction_required_fields": [
        "raw_api_responses"
      ],
      "safe_display_fields": [
        "platform_id",
        "platform_role",
        "primary_or_secondary_or_expansion",
        "endpoint_family"
      ],
      "v5_display_status": "hidden_fields_only"
    },
    {
      "account_binding_status": "symbolic",
      "approval_gate_status": "blocked",
      "blocked_reasons": [
        "no_arbitrary_dm_allowed",
        "operator_inbox_proof_required"
      ],
      "credential_mock_audit_status": "blocked",
      "credential_slot_status": "key_names_only",
      "dispatch_ready": false,
      "endpoint_family": "live_read_only",
      "evidence_packet_status": "blocked",
      "hidden_or_absent_fields": [
        "raw_secrets",
        "credential_values",
        "token_slices",
        "hashes",
        "raw_api_responses",
        "env_values"
      ],
      "kill_switch_status": "open_fails_closed",
      "live_read_allowed": false,
      "live_write_allowed": false,
      "manual_export_status": "not_applicable",
      "missing_proofs": [
        "no_arbitrary_dm_allowed",
        "operator_inbox_proof_required"
      ],
      "platform_id": "telegram_remote_operator",
      "platform_role": "remote_operator_review",
      "preflight_simulation_status": "blocked",
      "primary_or_secondary_or_expansion": "expansion",
      "public_post_allowed": false,
      "rate_budget_status": "blocked",
      "readiness_cleared": false,
      "redaction_required_fields": [
        "raw_api_responses"
      ],
      "safe_display_fields": [
        "platform_id",
        "platform_role",
        "primary_or_secondary_or_expansion",
        "endpoint_family"
      ],
      "v5_display_status": "hidden_fields_only"
    },
    {
      "account_binding_status": "symbolic",
      "approval_gate_status": "blocked",
      "blocked_reasons": [
        "channel_admin_proof_required",
        "bot_permission_gap",
        "channel_state_symbolic_only"
      ],
      "credential_mock_audit_status": "blocked",
      "credential_slot_status": "key_names_only",
      "dispatch_ready": false,
      "endpoint_family": "live_read_only",
      "evidence_packet_status": "blocked",
      "hidden_or_absent_fields": [
        "raw_secrets",
        "credential_values",
        "token_slices",
        "hashes",
        "raw_api_responses",
        "env_values"
      ],
      "kill_switch_status": "open_fails_closed",
      "live_read_allowed": false,
      "live_write_allowed": false,
      "manual_export_status": "not_applicable",
      "missing_proofs": [
        "channel_admin_proof_required",
        "bot_permission_gap",
        "channel_state_symbolic_only"
      ],
      "platform_id": "telegram_channel_destination",
      "platform_role": "controlled_channel_distribution",
      "preflight_simulation_status": "blocked",
      "primary_or_secondary_or_expansion": "secondary",
      "public_post_allowed": false,
      "rate_budget_status": "blocked",
      "readiness_cleared": false,
      "redaction_required_fields": [
        "raw_api_responses"
      ],
      "safe_display_fields": [
        "platform_id",
        "platform_role",
        "primary_or_secondary_or_expansion",
        "endpoint_family"
      ],
      "v5_display_status": "hidden_fields_only"
    },
    {
      "account_binding_status": "bound",
      "approval_gate_status": "manual_only",
      "blocked_reasons": [
        "manual_export_only"
      ],
      "credential_mock_audit_status": "manual_only",
      "credential_slot_status": "manual_no_credential",
      "dispatch_ready": false,
      "endpoint_family": "manual",
      "evidence_packet_status": "manual_only",
      "hidden_or_absent_fields": [
        "raw_secrets",
        "credential_values",
        "token_slices",
        "hashes",
        "raw_api_responses",
        "env_values"
      ],
      "kill_switch_status": "not_applicable",
      "live_read_allowed": false,
      "live_write_allowed": false,
      "manual_export_status": "manual_export_only",
      "missing_proofs": [
        "manual_export_only"
      ],
      "platform_id": "substack_newsletter",
      "platform_role": "owned_long_form",
      "preflight_simulation_status": "manual_only",
      "primary_or_secondary_or_expansion": "primary",
      "public_post_allowed": false,
      "rate_budget_status": "limit_not_applicable",
      "readiness_cleared": false,
      "redaction_required_fields": [
        "raw_api_responses"
      ],
      "safe_display_fields": [
        "platform_id",
        "platform_role",
        "primary_or_secondary_or_expansion",
        "endpoint_family"
      ],
      "v5_display_status": "hidden_fields_only"
    },
    {
      "account_binding_status": "symbolic",
      "approval_gate_status": "blocked",
      "blocked_reasons": [
        "linkedin_organization_page_proof_missing"
      ],
      "credential_mock_audit_status": "blocked",
      "credential_slot_status": "key_names_only",
      "dispatch_ready": false,
      "endpoint_family": "live_read_only",
      "evidence_packet_status": "blocked",
      "hidden_or_absent_fields": [
        "raw_secrets",
        "credential_values",
        "token_slices",
        "hashes",
        "raw_api_responses",
        "env_values"
      ],
      "kill_switch_status": "open_fails_closed",
      "live_read_allowed": false,
      "live_write_allowed": false,
      "manual_export_status": "not_applicable",
      "missing_proofs": [
        "linkedin_organization_page_proof_missing"
      ],
      "platform_id": "linkedin",
      "platform_role": "professional_credibility",
      "preflight_simulation_status": "blocked",
      "primary_or_secondary_or_expansion": "secondary",
      "public_post_allowed": false,
      "rate_budget_status": "blocked",
      "readiness_cleared": false,
      "redaction_required_fields": [
        "raw_api_responses"
      ],
      "safe_display_fields": [
        "platform_id",
        "platform_role",
        "primary_or_secondary_or_expansion",
        "endpoint_family"
      ],
      "v5_display_status": "hidden_fields_only"
    },
    {
      "account_binding_status": "symbolic",
      "approval_gate_status": "blocked",
      "blocked_reasons": [
        "meta_app_review_closed",
        "meta_app_account_proof_required"
      ],
      "credential_mock_audit_status": "blocked",
      "credential_slot_status": "key_names_only",
      "dispatch_ready": false,
      "endpoint_family": "live_read_only",
      "evidence_packet_status": "blocked",
      "hidden_or_absent_fields": [
        "raw_secrets",
        "credential_values",
        "token_slices",
        "hashes",
        "raw_api_responses",
        "env_values"
      ],
      "kill_switch_status": "open_fails_closed",
      "live_read_allowed": false,
      "live_write_allowed": false,
      "manual_export_status": "not_applicable",
      "missing_proofs": [
        "meta_app_review_closed",
        "meta_app_account_proof_required"
      ],
      "platform_id": "threads",
      "platform_role": "expansion_distribution",
      "preflight_simulation_status": "blocked",
      "primary_or_secondary_or_expansion": "expansion",
      "public_post_allowed": false,
      "rate_budget_status": "blocked",
      "readiness_cleared": false,
      "redaction_required_fields": [
        "raw_api_responses"
      ],
      "safe_display_fields": [
        "platform_id",
        "platform_role",
        "primary_or_secondary_or_expansion",
        "endpoint_family"
      ],
      "v5_display_status": "hidden_fields_only"
    },
    {
      "account_binding_status": "symbolic",
      "approval_gate_status": "blocked",
      "blocked_reasons": [
        "meta_app_review_closed",
        "meta_app_account_proof_required"
      ],
      "credential_mock_audit_status": "blocked",
      "credential_slot_status": "key_names_only",
      "dispatch_ready": false,
      "endpoint_family": "live_read_only",
      "evidence_packet_status": "blocked",
      "hidden_or_absent_fields": [
        "raw_secrets",
        "credential_values",
        "token_slices",
        "hashes",
        "raw_api_responses",
        "env_values"
      ],
      "kill_switch_status": "open_fails_closed",
      "live_read_allowed": false,
      "live_write_allowed": false,
      "manual_export_status": "not_applicable",
      "missing_proofs": [
        "meta_app_review_closed",
        "meta_app_account_proof_required"
      ],
      "platform_id": "instagram",
      "platform_role": "expansion_distribution",
      "preflight_simulation_status": "blocked",
      "primary_or_secondary_or_expansion": "expansion",
      "public_post_allowed": false,
      "rate_budget_status": "blocked",
      "readiness_cleared": false,
      "redaction_required_fields": [
        "raw_api_responses"
      ],
      "safe_display_fields": [
        "platform_id",
        "platform_role",
        "primary_or_secondary_or_expansion",
        "endpoint_family"
      ],
      "v5_display_status": "hidden_fields_only"
    },
    {
      "account_binding_status": "symbolic",
      "approval_gate_status": "blocked",
      "blocked_reasons": [
        "meta_app_review_closed",
        "meta_app_account_proof_required"
      ],
      "credential_mock_audit_status": "blocked",
      "credential_slot_status": "key_names_only",
      "dispatch_ready": false,
      "endpoint_family": "live_read_only",
      "evidence_packet_status": "blocked",
      "hidden_or_absent_fields": [
        "raw_secrets",
        "credential_values",
        "token_slices",
        "hashes",
        "raw_api_responses",
        "env_values"
      ],
      "kill_switch_status": "open_fails_closed",
      "live_read_allowed": false,
      "live_write_allowed": false,
      "manual_export_status": "not_applicable",
      "missing_proofs": [
        "meta_app_review_closed",
        "meta_app_account_proof_required"
      ],
      "platform_id": "facebook_page",
      "platform_role": "expansion_distribution",
      "preflight_simulation_status": "blocked",
      "primary_or_secondary_or_expansion": "expansion",
      "public_post_allowed": false,
      "rate_budget_status": "blocked",
      "readiness_cleared": false,
      "redaction_required_fields": [
        "raw_api_responses"
      ],
      "safe_display_fields": [
        "platform_id",
        "platform_role",
        "primary_or_secondary_or_expansion",
        "endpoint_family"
      ],
      "v5_display_status": "hidden_fields_only"
    },
    {
      "account_binding_status": "symbolic",
      "approval_gate_status": "blocked",
      "blocked_reasons": [
        "tiktok_app_audit_closed",
        "creator_account_proof_required",
        "video_publish_proof_required"
      ],
      "credential_mock_audit_status": "blocked",
      "credential_slot_status": "key_names_only",
      "dispatch_ready": false,
      "endpoint_family": "live_read_only",
      "evidence_packet_status": "blocked",
      "hidden_or_absent_fields": [
        "raw_secrets",
        "credential_values",
        "token_slices",
        "hashes",
        "raw_api_responses",
        "env_values"
      ],
      "kill_switch_status": "open_fails_closed",
      "live_read_allowed": false,
      "live_write_allowed": false,
      "manual_export_status": "not_applicable",
      "missing_proofs": [
        "tiktok_app_audit_closed",
        "creator_account_proof_required",
        "video_publish_proof_required"
      ],
      "platform_id": "tiktok",
      "platform_role": "later_video_distribution",
      "preflight_simulation_status": "blocked",
      "primary_or_secondary_or_expansion": "expansion",
      "public_post_allowed": false,
      "rate_budget_status": "blocked",
      "readiness_cleared": false,
      "redaction_required_fields": [
        "raw_api_responses"
      ],
      "safe_display_fields": [
        "platform_id",
        "platform_role",
        "primary_or_secondary_or_expansion",
        "endpoint_family"
      ],
      "v5_display_status": "hidden_fields_only"
    },
    {
      "account_binding_status": "symbolic",
      "approval_gate_status": "blocked",
      "blocked_reasons": [
        "youtube_quota_unresolved",
        "youtube_oauth_flow_closed",
        "upload_proof_required"
      ],
      "credential_mock_audit_status": "blocked",
      "credential_slot_status": "key_names_only",
      "dispatch_ready": false,
      "endpoint_family": "live_read_only",
      "evidence_packet_status": "blocked",
      "hidden_or_absent_fields": [
        "raw_secrets",
        "credential_values",
        "token_slices",
        "hashes",
        "raw_api_responses",
        "env_values"
      ],
      "kill_switch_status": "open_fails_closed",
      "live_read_allowed": false,
      "live_write_allowed": false,
      "manual_export_status": "not_applicable",
      "missing_proofs": [
        "youtube_quota_unresolved",
        "youtube_oauth_flow_closed",
        "upload_proof_required"
      ],
      "platform_id": "youtube",
      "platform_role": "later_video_distribution",
      "preflight_simulation_status": "blocked",
      "primary_or_secondary_or_expansion": "expansion",
      "public_post_allowed": false,
      "rate_budget_status": "blocked",
      "readiness_cleared": false,
      "redaction_required_fields": [
        "raw_api_responses"
      ],
      "safe_display_fields": [
        "platform_id",
        "platform_role",
        "primary_or_secondary_or_expansion",
        "endpoint_family"
      ],
      "v5_display_status": "hidden_fields_only"
    }
  ],
  "room_binding_prechecks": [
    {
      "binding_status": "ready_for_read_model_design",
      "disabled_affordances": [
        "live_dispatch_toggle"
      ],
      "hidden_fields_count": 1,
      "missing_contracts": [],
      "no_live_action_affordances": true,
      "redacted_fields_count": 0,
      "required_contracts": [
        "platform_universe_registry_v2",
        "local_content_governance_summary_mart_contract",
        "rate_budget_kill_switch_matrix_contract"
      ],
      "room_id": "command_center",
      "safe_fields_count": 2,
      "safety_notes": "Verified: local preflight bundle safety policy holds. No live action affordances exist."
    },
    {
      "binding_status": "ready_for_read_model_design",
      "disabled_affordances": [],
      "hidden_fields_count": 0,
      "missing_contracts": [],
      "no_live_action_affordances": true,
      "redacted_fields_count": 2,
      "required_contracts": [
        "redacted_immutable_audit_ledger_v2_contract",
        "live_read_only_research_evidence_packet_dry_run_schema_contract"
      ],
      "room_id": "evidence_vault",
      "safe_fields_count": 0,
      "safety_notes": "Verified: local preflight bundle safety policy holds. No live action affordances exist."
    },
    {
      "binding_status": "ready_for_read_model_design",
      "disabled_affordances": [
        "approval_signature_field"
      ],
      "hidden_fields_count": 1,
      "missing_contracts": [],
      "no_live_action_affordances": true,
      "redacted_fields_count": 0,
      "required_contracts": [
        "live_read_only_research_approval_packet_schema_contract"
      ],
      "room_id": "approval_queue",
      "safe_fields_count": 1,
      "safety_notes": "Verified: local preflight bundle safety policy holds. No live action affordances exist."
    },
    {
      "binding_status": "ready_for_read_model_design",
      "disabled_affordances": [],
      "hidden_fields_count": 0,
      "missing_contracts": [],
      "no_live_action_affordances": true,
      "redacted_fields_count": 0,
      "required_contracts": [
        "platform_preflight_dry_run_request_budget_contract"
      ],
      "room_id": "platform_payload_preview",
      "safe_fields_count": 2,
      "safety_notes": "Verified: local preflight bundle safety policy holds. No live action affordances exist."
    },
    {
      "binding_status": "ready_for_read_model_design",
      "disabled_affordances": [],
      "hidden_fields_count": 0,
      "missing_contracts": [],
      "no_live_action_affordances": true,
      "redacted_fields_count": 0,
      "required_contracts": [
        "live_read_only_research_local_preflight_simulation_contract"
      ],
      "room_id": "substack_manual_export",
      "safe_fields_count": 2,
      "safety_notes": "Verified: local preflight bundle safety policy holds. No live action affordances exist."
    },
    {
      "binding_status": "ready_for_read_model_design",
      "disabled_affordances": [
        "raw_secret_material"
      ],
      "hidden_fields_count": 1,
      "missing_contracts": [],
      "no_live_action_affordances": true,
      "redacted_fields_count": 0,
      "required_contracts": [
        "read_only_credential_slot_check_validation_contract",
        "credential_handle_dotenv_secret_boundary_v2_contract"
      ],
      "room_id": "credential_boundary",
      "safe_fields_count": 1,
      "safety_notes": "Verified: local preflight bundle safety policy holds. No live action affordances exist."
    },
    {
      "binding_status": "ready_for_read_model_design",
      "disabled_affordances": [],
      "hidden_fields_count": 0,
      "missing_contracts": [],
      "no_live_action_affordances": true,
      "redacted_fields_count": 1,
      "required_contracts": [
        "platform_account_binding_registry_v2_contract"
      ],
      "room_id": "account_binding",
      "safe_fields_count": 1,
      "safety_notes": "Verified: local preflight bundle safety policy holds. No live action affordances exist."
    },
    {
      "binding_status": "ready_for_read_model_design",
      "disabled_affordances": [],
      "hidden_fields_count": 0,
      "missing_contracts": [],
      "no_live_action_affordances": true,
      "redacted_fields_count": 0,
      "required_contracts": [
        "supervised_live_read_only_research_gate_precheck_contract"
      ],
      "room_id": "live_readiness_gate",
      "safe_fields_count": 2,
      "safety_notes": "Verified: local preflight bundle safety policy holds. No live action affordances exist."
    },
    {
      "binding_status": "ready_for_read_model_design",
      "disabled_affordances": [],
      "hidden_fields_count": 0,
      "missing_contracts": [],
      "no_live_action_affordances": true,
      "redacted_fields_count": 0,
      "required_contracts": [
        "manual_publish_record_metrics_ledger_contract"
      ],
      "room_id": "manual_publish_metrics",
      "safe_fields_count": 2,
      "safety_notes": "Verified: local preflight bundle safety policy holds. No live action affordances exist."
    },
    {
      "binding_status": "ready_for_read_model_design",
      "disabled_affordances": [],
      "hidden_fields_count": 0,
      "missing_contracts": [],
      "no_live_action_affordances": true,
      "redacted_fields_count": 0,
      "required_contracts": [
        "content_performance_review_editorial_feedback_contract"
      ],
      "room_id": "content_performance_review",
      "safe_fields_count": 2,
      "safety_notes": "Verified: local preflight bundle safety policy holds. No live action affordances exist."
    },
    {
      "binding_status": "ready_for_read_model_design",
      "disabled_affordances": [],
      "hidden_fields_count": 0,
      "missing_contracts": [],
      "no_live_action_affordances": true,
      "redacted_fields_count": 0,
      "required_contracts": [
        "internal_alpha_artifact_intake_content_eligibility_contract"
      ],
      "room_id": "internal_alpha_artifact_intake",
      "safe_fields_count": 2,
      "safety_notes": "Verified: local preflight bundle safety policy holds. No live action affordances exist."
    },
    {
      "binding_status": "ready_for_read_model_design",
      "disabled_affordances": [],
      "hidden_fields_count": 0,
      "missing_contracts": [],
      "no_live_action_affordances": true,
      "redacted_fields_count": 0,
      "required_contracts": [
        "live_read_only_research_approval_packet_schema_contract"
      ],
      "room_id": "writer_studio",
      "safe_fields_count": 2,
      "safety_notes": "Verified: local preflight bundle safety policy holds. No live action affordances exist."
    },
    {
      "binding_status": "ready_for_read_model_design",
      "disabled_affordances": [],
      "hidden_fields_count": 0,
      "missing_contracts": [],
      "no_live_action_affordances": true,
      "redacted_fields_count": 0,
      "required_contracts": [
        "live_read_only_research_approval_packet_schema_contract"
      ],
      "room_id": "grounded_news_workbench",
      "safe_fields_count": 2,
      "safety_notes": "Verified: local preflight bundle safety policy holds. No live action affordances exist."
    }
  ],
  "room_count": 13,
  "safety_flags": {
    "autonomous_posting_allowed": false,
    "browser_session_used": false,
    "credential_hydrated": false,
    "credential_values_accessed": false,
    "current_truth_promoted": false,
    "dispatch_ready": false,
    "dm_or_reply_automation_allowed": false,
    "dqr_cleared": false,
    "env_read": false,
    "ingestion_repo_mutated": false,
    "live_read_allowed": false,
    "live_write_allowed": false,
    "local_only": true,
    "network_performed": false,
    "platform_api_called": false,
    "provider_api_called": false,
    "public_post_allowed": false,
    "read_model_precheck_only": true,
    "readiness_cleared": false,
    "scheduler_enabled": false,
    "scraping_performed": false,
    "secret_output_allowed": false,
    "ui_mutated": false
  },
  "source_baseline_commit": "25e88d61625a3c5ed55e1b79a53854fe07632487",
  "source_ref_count": 17,
  "source_refs": [
    {
      "artifact_family": "platforms",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.platform_universe_registry_v2",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "7230b31865d62341843d937266a7685c2ee721fccb4b1fd18550633a422fe758",
      "source_ref_id": "platform_universe_registry_v2",
      "source_status": "valid",
      "task_family": "universe_registry",
      "ui_mutated": false
    },
    {
      "artifact_family": "bindings",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.platform_account_binding_registry_v2_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "5e9320282937510b2ec9e1ffaf01a498a3a166385f9b202dc7dc5328a898850e",
      "source_ref_id": "platform_account_binding_registry_v2_contract",
      "source_status": "valid",
      "task_family": "account_binding",
      "ui_mutated": false
    },
    {
      "artifact_family": "secret_boundary",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.credential_handle_dotenv_secret_boundary_v2_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "25b0e3bcd41de07cd4ff79d7bce1d5dca3789a1bd6eb47d871f2cb6dddf1b8f7",
      "source_ref_id": "credential_handle_dotenv_secret_boundary_v2_contract",
      "source_status": "valid",
      "task_family": "secret_boundary",
      "ui_mutated": false
    },
    {
      "artifact_family": "approval_schema",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.live_read_only_research_approval_packet_schema_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "ee8ec710e41729a6463f1f4cd6d83d04319c18408c97a85c2b851098a9936427",
      "source_ref_id": "live_read_only_research_approval_packet_schema_contract",
      "source_status": "valid",
      "task_family": "live_read_only_research_approval",
      "ui_mutated": false
    },
    {
      "artifact_family": "evidence_schema",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.live_read_only_research_evidence_packet_dry_run_schema_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "1efdd3c9951c22ef0c79661a21045d0df26582b95ade698df2765df020c702a8",
      "source_ref_id": "live_read_only_research_evidence_packet_dry_run_schema_contract",
      "source_status": "valid",
      "task_family": "live_read_only_research_evidence",
      "ui_mutated": false
    },
    {
      "artifact_family": "runbook_gate",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.live_read_only_research_runbook_approval_gate_dry_run_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "8518cbd3e3b2573530482d28b392e5499bf8b83b276562e02794c4156eba51d5",
      "source_ref_id": "live_read_only_research_runbook_approval_gate_dry_run_contract",
      "source_status": "valid",
      "task_family": "live_read_only_research_runbook",
      "ui_mutated": false
    },
    {
      "artifact_family": "simulation_gate",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.live_read_only_research_local_preflight_simulation_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "9c9235bf079c96324b7d26e79b5a87dfc27d3f96d961515f29ebae151ae071fa",
      "source_ref_id": "live_read_only_research_local_preflight_simulation_contract",
      "source_status": "valid",
      "task_family": "live_read_only_research_simulation",
      "ui_mutated": false
    },
    {
      "artifact_family": "slot_check",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.read_only_credential_slot_check_validation_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "26712637152ffb2a7e11e781929d651741763b3f80237214b34e28eb0826959a",
      "source_ref_id": "read_only_credential_slot_check_validation_contract",
      "source_status": "valid",
      "task_family": "read_only_credential_slot_check",
      "ui_mutated": false
    },
    {
      "artifact_family": "mock_audit",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.read_only_credential_slot_inspection_mock_audit_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "408babbd861e4f6b3e235979f8d73220387c689deb59571117cafe5e052e8cac",
      "source_ref_id": "read_only_credential_slot_inspection_mock_audit_contract",
      "source_status": "valid",
      "task_family": "read_only_credential_slot_inspection",
      "ui_mutated": false
    },
    {
      "artifact_family": "gate_precheck",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.supervised_live_read_only_research_gate_precheck_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "151f9bd42e0563e7eb409de85fa238d128b7cf2f0763fb7d4b479d39add2f75b",
      "source_ref_id": "supervised_live_read_only_research_gate_precheck_contract",
      "source_status": "valid",
      "task_family": "supervised_live_read_only_research",
      "ui_mutated": false
    },
    {
      "artifact_family": "budget_decision",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.platform_preflight_dry_run_request_budget_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "a43674c677456109c14786d2e88de05aa3d7d8c7e3919d23d29c71cb20f9821b",
      "source_ref_id": "platform_preflight_dry_run_request_budget_contract",
      "source_status": "valid",
      "task_family": "platform_preflight_dry_run",
      "ui_mutated": false
    },
    {
      "artifact_family": "kill_switch_packet",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.rate_budget_kill_switch_matrix_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "e37e5701f1b3c5a25a651ef99d1f6d649d15c422560dfa44468f7a5f46159126",
      "source_ref_id": "rate_budget_kill_switch_matrix_contract",
      "source_status": "valid",
      "task_family": "rate_budget_kill_switch",
      "ui_mutated": false
    },
    {
      "artifact_family": "ledger_rules",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.redacted_immutable_audit_ledger_v2_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "c64003df97a919698fd43934eb7371946e3dea3496d96dfa27d4a020e421c818",
      "source_ref_id": "redacted_immutable_audit_ledger_v2_contract",
      "source_status": "valid",
      "task_family": "audit_ledger",
      "ui_mutated": false
    },
    {
      "artifact_family": "summary_mart",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.local_content_governance_summary_mart_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "019fa15c50168a7a9f0473257e58ddf49013c8853d0f28b5f29710b5df59f183",
      "source_ref_id": "local_content_governance_summary_mart_contract",
      "source_status": "valid",
      "task_family": "governance_summary",
      "ui_mutated": false
    },
    {
      "artifact_family": "metrics_ledger",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.manual_publish_record_metrics_ledger_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "76d70cedc54c6457a34981a58897a59509bdfcbb51f750d7443dead54d3b1789",
      "source_ref_id": "manual_publish_record_metrics_ledger_contract",
      "source_status": "valid",
      "task_family": "manual_publish",
      "ui_mutated": false
    },
    {
      "artifact_family": "feedback_loop",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.content_performance_review_editorial_feedback_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "7e342b5ac09861dc715ed25d9abe9626e70475f7d82e5048064902bcfbbaaebc",
      "source_ref_id": "content_performance_review_editorial_feedback_contract",
      "source_status": "valid",
      "task_family": "performance_review",
      "ui_mutated": false
    },
    {
      "artifact_family": "intake_eligibility",
      "consumed": true,
      "credential_values_accessed": false,
      "env_read": false,
      "ingestion_mutated": false,
      "live_capability_added": false,
      "module_name": "live_contentops.internal_alpha_artifact_intake_content_eligibility_contract",
      "platform_api_called": false,
      "source_hash_or_packet_hash": "7e7f3c15a7e164915ee979f0dbdd66ea614412ac5287b94f86d118859a955f74",
      "source_ref_id": "internal_alpha_artifact_intake_content_eligibility_contract",
      "source_status": "valid",
      "task_family": "artifact_intake",
      "ui_mutated": false
    }
  ],
  "task_label": "TASK_CONTENTOPS_0174UU_LOCAL_PREFLIGHT_BUNDLE_AND_V5_READ_MODEL_BINDING_PRECHECK_V0",
  "u9_audit_entry_families": [
    "local_preflight_bundle_v5_read_model_precheck_future",
    "local_preflight_bundle_v5_read_model_precheck_future",
    "local_preflight_bundle_v5_read_model_precheck_future",
    "local_preflight_bundle_v5_read_model_precheck_future",
    "local_preflight_bundle_v5_read_model_precheck_future",
    "local_preflight_bundle_v5_read_model_precheck_future",
    "local_preflight_bundle_v5_read_model_precheck_future",
    "local_preflight_bundle_v5_read_model_precheck_future",
    "local_preflight_bundle_v5_read_model_precheck_future",
    "local_preflight_bundle_v5_read_model_precheck_future"
  ],
  "u9_audit_entry_ids": [
    "ledger_entry_417d1531d7c8ce97d003454e",
    "ledger_entry_68254b674aea3b0badafe817",
    "ledger_entry_4f46cec578046f2e0a01325d",
    "ledger_entry_7c54c8194b4134a5a4f8084d",
    "ledger_entry_d1a233eadfbff89858c3db4d",
    "ledger_entry_15c93c4371cef6fc430a6644",
    "ledger_entry_3050faa76218c1d961cb07a6",
    "ledger_entry_d1e8bb1c1de1ad8e035ca974",
    "ledger_entry_c3df2afce5eeec36d9614951",
    "ledger_entry_d897cd92288be3f2612a11f2"
  ],
  "ui_binding_policy": "strict_read_model_precheck_v5_isolation",
  "v5_candidate_fields": [
    {
      "current_truth_policy": "reference_only",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_command_center_platform_registry_list",
      "field_kind": "metadata",
      "field_name": "platform_registry_list",
      "forbidden_affordance_reason": "",
      "room_id": "command_center",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "universe_registry",
      "source_ref_id": "source_ref_universe_registry",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "reference_only",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_command_center_global_readiness_status",
      "field_kind": "status",
      "field_name": "global_readiness_status",
      "forbidden_affordance_reason": "",
      "room_id": "command_center",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "governance_summary",
      "source_ref_id": "source_ref_governance_summary",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "future_gate",
      "display_policy": "hidden",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_command_center_live_dispatch_toggle",
      "field_kind": "control",
      "field_name": "live_dispatch_toggle",
      "forbidden_affordance_reason": "live_action_blocked_local_only",
      "room_id": "command_center",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "rate_budget_kill_switch",
      "source_ref_id": "source_ref_rate_budget_kill_switch",
      "user_action_affordance": "disabled_future_gate"
    },
    {
      "current_truth_policy": "historical_evidence",
      "display_policy": "redacted",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_evidence_vault_u9_ledger_entries",
      "field_kind": "json_ledger",
      "field_name": "u9_ledger_entries",
      "forbidden_affordance_reason": "",
      "room_id": "evidence_vault",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "audit_ledger",
      "source_ref_id": "source_ref_audit_ledger",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "historical_evidence",
      "display_policy": "redacted",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_evidence_vault_evidence_packet_records",
      "field_kind": "json_packet",
      "field_name": "evidence_packet_records",
      "forbidden_affordance_reason": "",
      "room_id": "evidence_vault",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "live_read_only_research_evidence",
      "source_ref_id": "source_ref_live_read_only_research_evidence",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "current_state",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_approval_queue_pending_operator_actions",
      "field_kind": "list",
      "field_name": "pending_operator_actions",
      "forbidden_affordance_reason": "",
      "room_id": "approval_queue",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "live_read_only_research_approval",
      "source_ref_id": "source_ref_live_read_only_research_approval",
      "user_action_affordance": "manual_review_only"
    },
    {
      "current_truth_policy": "future_gate",
      "display_policy": "hidden",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_approval_queue_approval_signature_field",
      "field_kind": "signature",
      "field_name": "approval_signature_field",
      "forbidden_affordance_reason": "live_action_blocked_local_only",
      "room_id": "approval_queue",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "live_read_only_research_approval",
      "source_ref_id": "source_ref_live_read_only_research_approval",
      "user_action_affordance": "disabled_future_gate"
    },
    {
      "current_truth_policy": "reference_only",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_platform_payload_preview_dry_run_payload_preview",
      "field_kind": "json_preview",
      "field_name": "dry_run_payload_preview",
      "forbidden_affordance_reason": "",
      "room_id": "platform_payload_preview",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "platform_preflight_dry_run",
      "source_ref_id": "source_ref_platform_preflight_dry_run",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "reference_only",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_platform_payload_preview_rendered_social_media_preview",
      "field_kind": "html",
      "field_name": "rendered_social_media_preview",
      "forbidden_affordance_reason": "",
      "room_id": "platform_payload_preview",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "platform_preflight_dry_run",
      "source_ref_id": "source_ref_platform_preflight_dry_run",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "current_state",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_substack_manual_export_manual_export_manifest",
      "field_kind": "json",
      "field_name": "manual_export_manifest",
      "forbidden_affordance_reason": "",
      "room_id": "substack_manual_export",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "dry_run_preview",
      "source_ref_id": "source_ref_dry_run_preview",
      "user_action_affordance": "manual_review_only"
    },
    {
      "current_truth_policy": "historical_evidence",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_substack_manual_export_export_package_checksum",
      "field_kind": "hash",
      "field_name": "export_package_checksum",
      "forbidden_affordance_reason": "",
      "room_id": "substack_manual_export",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "dry_run_preview",
      "source_ref_id": "source_ref_dry_run_preview",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "reference_only",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_credential_boundary_credential_slots_schema",
      "field_kind": "json_schema",
      "field_name": "credential_slots_schema",
      "forbidden_affordance_reason": "",
      "room_id": "credential_boundary",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "read_only_credential_slot_check",
      "source_ref_id": "source_ref_read_only_credential_slot_check",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "future_gate",
      "display_policy": "hidden",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_credential_boundary_raw_secret_material",
      "field_kind": "secret",
      "field_name": "raw_secret_material",
      "forbidden_affordance_reason": "live_action_blocked_local_only",
      "room_id": "credential_boundary",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "secret_boundary",
      "source_ref_id": "source_ref_secret_boundary",
      "user_action_affordance": "disabled_future_gate"
    },
    {
      "current_truth_policy": "current_state",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_account_binding_bound_accounts_list",
      "field_kind": "list",
      "field_name": "bound_accounts_list",
      "forbidden_affordance_reason": "",
      "room_id": "account_binding",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "account_binding",
      "source_ref_id": "source_ref_account_binding",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "reference_only",
      "display_policy": "redacted",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_account_binding_oauth_client_id",
      "field_kind": "id_string",
      "field_name": "oauth_client_id",
      "forbidden_affordance_reason": "",
      "room_id": "account_binding",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "account_binding",
      "source_ref_id": "source_ref_account_binding",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "current_state",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_live_readiness_gate_gate_precheck_results",
      "field_kind": "json",
      "field_name": "gate_precheck_results",
      "forbidden_affordance_reason": "",
      "room_id": "live_readiness_gate",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "supervised_live_read_only_research",
      "source_ref_id": "source_ref_supervised_live_read_only_research",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "historical_evidence",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_live_readiness_gate_post_pilot_ledger_status",
      "field_kind": "status",
      "field_name": "post_pilot_ledger_status",
      "forbidden_affordance_reason": "",
      "room_id": "live_readiness_gate",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "supervised_live_read_only_research",
      "source_ref_id": "source_ref_supervised_live_read_only_research",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "historical_evidence",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_manual_publish_metrics_manual_publish_ledger",
      "field_kind": "json_ledger",
      "field_name": "manual_publish_ledger",
      "forbidden_affordance_reason": "",
      "room_id": "manual_publish_metrics",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "manual_publish",
      "source_ref_id": "source_ref_manual_publish",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "historical_evidence",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_manual_publish_metrics_published_metrics_record",
      "field_kind": "record",
      "field_name": "published_metrics_record",
      "forbidden_affordance_reason": "",
      "room_id": "manual_publish_metrics",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "manual_publish",
      "source_ref_id": "source_ref_manual_publish",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "historical_evidence",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_content_performance_review_performance_review_packet",
      "field_kind": "json",
      "field_name": "performance_review_packet",
      "forbidden_affordance_reason": "",
      "room_id": "content_performance_review",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "performance_review",
      "source_ref_id": "source_ref_performance_review",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "historical_evidence",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_content_performance_review_editorial_feedback_loop",
      "field_kind": "json",
      "field_name": "editorial_feedback_loop",
      "forbidden_affordance_reason": "",
      "room_id": "content_performance_review",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "performance_review",
      "source_ref_id": "source_ref_performance_review",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "historical_evidence",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_internal_alpha_artifact_intake_intake_content_eligibility_report",
      "field_kind": "json",
      "field_name": "intake_content_eligibility_report",
      "forbidden_affordance_reason": "",
      "room_id": "internal_alpha_artifact_intake",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "artifact_intake",
      "source_ref_id": "source_ref_artifact_intake",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "historical_evidence",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_internal_alpha_artifact_intake_artifact_idea_seed_packet",
      "field_kind": "json",
      "field_name": "artifact_idea_seed_packet",
      "forbidden_affordance_reason": "",
      "room_id": "internal_alpha_artifact_intake",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "artifact_intake",
      "source_ref_id": "source_ref_artifact_intake",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "reference_only",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_writer_studio_ai_writer_output",
      "field_kind": "json",
      "field_name": "ai_writer_output",
      "forbidden_affordance_reason": "",
      "room_id": "writer_studio",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "editorial_writer",
      "source_ref_id": "source_ref_editorial_writer",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "reference_only",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_writer_studio_editorial_brief",
      "field_kind": "json",
      "field_name": "editorial_brief",
      "forbidden_affordance_reason": "",
      "room_id": "writer_studio",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "editorial_writer",
      "source_ref_id": "source_ref_editorial_writer",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "reference_only",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_grounded_news_workbench_grounded_news_angle_workbench",
      "field_kind": "json",
      "field_name": "grounded_news_angle_workbench",
      "forbidden_affordance_reason": "",
      "room_id": "grounded_news_workbench",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "editorial_writer",
      "source_ref_id": "source_ref_editorial_writer",
      "user_action_affordance": "read_only"
    },
    {
      "current_truth_policy": "reference_only",
      "display_policy": "safe_to_show",
      "evidence_ref": "proof:0174UU",
      "field_id": "v5_field_grounded_news_workbench_grounded_research_brief",
      "field_kind": "json",
      "field_name": "grounded_research_brief",
      "forbidden_affordance_reason": "",
      "room_id": "grounded_news_workbench",
      "sample_value_classification": "mock_or_metadata_only",
      "source_family": "editorial_writer",
      "source_ref_id": "source_ref_editorial_writer",
      "user_action_affordance": "read_only"
    }
  ]
};
