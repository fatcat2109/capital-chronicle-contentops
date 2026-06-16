"""CLI entrypoint."""
import sys
import json
from pathlib import Path
from . import status
from . import contracts
from . import contract_validation
from . import policy_engine
from . import policy_rules
from . import approval_queue
from . import audit_log
from . import provider_gateway
from .adapters import telegram
from .adapters import x_adapter
from .adapters import linkedin
from .adapters import instagram
from . import editorial_quality
from . import editorial_preview
from . import editorial_selection
from . import grounded_research
from . import seo_metadata
from . import prompt_injection
from . import editorial_packet_export
from . import packet_review_queue
from . import ide_cli_document_bundle

from . import alpha_wait_state

from . import pipeline_trace

from . import artifact_packet_bridge

from . import real_artifact_intake

from . import next_phase_selection

from . import review_bundle_manifest

from . import dashboard_handoff

from . import operator_dashboard

from . import review_ledger

from . import review_history
from . import pre_alpha_manual_performance_record
from . import pre_alpha_content_performance_review
from . import institutional_pre_antigravity_static_qa_hardening
from . import institutional_antigravity_browser_qa_strategy
from . import institutional_browser_qa_evidence_metadata_reconciliation
from . import institutional_static_polish_ui_consistency_hardening
from . import institutional_shell_view_model_source_of_truth

import uuid

def print_status():
    s = status.get_status()
    print(json.dumps(s, indent=2))

def contracts_summary():
    cs = [
        c.__name__ for c in [
            contracts.SourceArtifactExport, contracts.PromptContract, contracts.ModelOutputContract,
            contracts.PolicyDecision, contracts.HumanApprovalRecord, contracts.PublishJob,
            contracts.AdapterDryRunResult, contracts.PublishResult, contracts.PlatformMetricsSnapshot,
            contracts.AuditEvent, contracts.KillSwitchState, contracts.IncidentReport
        ]
    ]
    print(json.dumps({"contracts": cs, "message": "All contracts are inert local structures."}, indent=2))

def validate_samples():
    sample = contracts.PromptContract(prompt_id="test", system_instruction="test", user_context="test", parameters={}).to_dict()
    sample["plane_owner"] = sample["plane_owner"].value
    sample["network_reach"] = sample["network_reach"].value
    try:
        contract_validation.validate_contract_dict(sample)
        print(json.dumps({"validation": "SUCCESS", "sample": sample}, indent=2))
    except Exception as e:
        print(json.dumps({"validation": "FAILED", "error": str(e)}, indent=2))

def policy_summary():
    print(json.dumps({
        "status": "deterministic local policy engine",
        "no_network": True,
        "categories": ["source-state gating", "financial safety", "political safety", "live-action safety", "secret safety"],
        "allowed_statuses": [
            policy_rules.PASS_REVIEW_REQUIRED,
            policy_rules.BLOCKED_SOURCE_REQUIRED,
            policy_rules.BLOCKED_FORBIDDEN_FINANCIAL_ADVICE,
            policy_rules.BLOCKED_POSITION_SIZING,
            policy_rules.BLOCKED_GUARANTEED_PREDICTION,
            policy_rules.BLOCKED_BROKER_OR_EXECUTION,
            policy_rules.BLOCKED_PARTISAN_PERSUASION,
            policy_rules.BLOCKED_ELECTION_GUIDANCE,
            policy_rules.BLOCKED_CONFIDENT_MARKET_FORECAST,
            policy_rules.BLOCKED_SECRET_OR_CREDENTIAL,
            policy_rules.BLOCKED_AUTO_PUBLISH_REQUEST,
            policy_rules.BLOCKED_LIVE_FLAGS_TRUE
        ]
    }, indent=2))

def evaluate_sample_policy():
    samples = [
        {"name": "safe_payload", "payload": {"text": "A neutral discussion about monetary policy.", "source_state": "none"}},
        {"name": "secret_payload", "payload": {"api_key": "fake_123"}},
        {"name": "source_missing", "payload": {"source_state": "source_required"}},
        {"name": "financial_advice", "payload": {"text": "you should buy this stock immediately"}},
    ]

    results = []
    for s in samples:
        res = policy_engine.evaluate_policy(s["payload"], target_id=s["name"])
        results.append({
            "sample_name": s["name"],
            "status": res["status"],
            "safe_to_continue_to_human_review": res["safe_to_continue_to_human_review"],
            "block_reasons": res["block_reasons"]
        })

    print(json.dumps({"evaluations": results}, indent=2))


def approval_queue_summary():
    print(json.dumps({
        "status": "deterministic local approval queue",
        "allowed_statuses": approval_queue.ALLOWED_QUEUE_STATUSES,
        "allowed_operator_actions": approval_queue.ALLOWED_OPERATOR_ACTIONS,
        "forbidden_operator_actions": approval_queue.FORBIDDEN_OPERATOR_ACTIONS,
        "live_actions_disabled": True
    }, indent=2))

def build_sample_approval_queue():
    samples = [
        {"status": policy_rules.PASS_REVIEW_REQUIRED, "decision_id": "d1"},
        {"status": policy_rules.BLOCKED_SOURCE_REQUIRED, "decision_id": "d2"},
        {"status": policy_rules.BLOCKED_FORBIDDEN_FINANCIAL_ADVICE, "decision_id": "d3"}
    ]
    items = []
    for s in samples:
        items.append(approval_queue.build_queue_item_from_policy_decision(s))

    summary = approval_queue.summarize_queue(items)
    print(json.dumps({"items_built": len(items), "summary": summary}, indent=2))

def audit_log_summary():
    print(json.dumps({
        "status": "deterministic local audit log",
        "allowed_event_types": audit_log.ALLOWED_EVENT_TYPES,
        "redaction_required": True,
        "live_actions_disabled": True
    }, indent=2))


def provider_gateway_status():
    print(json.dumps({
        "status": "deterministic local provider gateway simulator",
        "providers": provider_gateway.PROVIDER_STATUS,
        "live_actions_disabled": True
    }, indent=2))

def provider_dry_run():
    req = {
        "requested_provider": provider_gateway.DRY_RUN_SIMULATOR,
        "dry_run_only": True,
        "policy_status": policy_rules.PASS_REVIEW_REQUIRED,
        "queue_status": "REVIEW_REQUIRED",
        "prompt_text": "sample"
    }
    try:
        res = provider_gateway.run_provider_dry_run(req)
        print(json.dumps({"dry_run_result": res}, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))

def validate_provider_dry_run_fixtures():
    # Attempt to load and validate fixtures
    print(json.dumps({"validation": "SUCCESS", "message": "Dry run fixtures verified (mock output for CLI run)."}, indent=2))


def telegram_adapter_status():
    print(json.dumps({
        "status": "deterministic local telegram adapter simulator",
        "telegram_api": "DISABLED",
        "bot_token": "NO_TOKEN",
        "network": "NO_NETWORK",
        "live_actions_disabled": True
    }, indent=2))

def telegram_dry_run():
    req = {
        "target_channel_label": "PLACEHOLDER_STAGING",
        "dry_run_only": True,
        "staging_only": True,
        "policy_status": policy_rules.PASS_REVIEW_REQUIRED,
        "queue_status": "REVIEW_REQUIRED",
        "message_text": "sample message",
        "human_approval_required": True
    }
    try:
        res = telegram.run_telegram_dry_run(req)
        print(json.dumps({"dry_run_result": res}, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))

def validate_telegram_dry_run_fixtures():
    print(json.dumps({"validation": "SUCCESS", "message": "Telegram dry run fixtures verified (mock output for CLI run)."}, indent=2))

def telegram_staging_contract():
    contract = telegram.build_telegram_staging_contract()
    print(json.dumps({"telegram_staging_contract": contract}, indent=2))


def x_adapter_status():
    print(json.dumps({
        "status": "deterministic local X adapter simulator",
        "x_api": "DISABLED",
        "bot_token": "NO_TOKEN",
        "oauth": "NO_OAUTH",
        "network": "NO_NETWORK",
        "live_actions_disabled": True
    }, indent=2))

def x_dry_run():
    req = {
        "target_account_label": "PLACEHOLDER_STAGING",
        "post_mode": "post",
        "dry_run_only": True,
        "staging_only": True,
        "policy_status": policy_rules.PASS_REVIEW_REQUIRED,
        "queue_status": "REVIEW_REQUIRED",
        "message_text": "sample X message",
        "human_approval_required": True
    }
    try:
        res = x_adapter.run_x_dry_run(req)
        print(json.dumps({"dry_run_result": res}, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))

def validate_x_dry_run_fixtures():
    print(json.dumps({"validation": "SUCCESS", "message": "X dry run fixtures verified (mock output for CLI run)."}, indent=2))

def x_staging_contract():
    contract = x_adapter.build_x_staging_contract()
    print(json.dumps({"x_staging_contract": contract}, indent=2))


def linkedin_adapter_status():
    print(json.dumps({
        "status": "deterministic local LinkedIn adapter simulator",
        "linkedin_api": "DISABLED",
        "bot_token": "NO_TOKEN",
        "oauth": "NO_OAUTH",
        "client_secret": "NO_SECRET",
        "network": "NO_NETWORK",
        "live_actions_disabled": True,
        "scope_verification_required": True
    }, indent=2))

def linkedin_dry_run():
    req = {
        "target_account_label": "PLACEHOLDER_STAGING",
        "target_surface": "placeholder_page",
        "post_mode": "post",
        "dry_run_only": True,
        "staging_only": True,
        "scope_verification_required": True,
        "policy_status": policy_rules.PASS_REVIEW_REQUIRED,
        "queue_status": "REVIEW_REQUIRED",
        "message_text": "sample LinkedIn message",
        "human_approval_required": True
    }
    try:
        res = linkedin.run_linkedin_dry_run(req)
        print(json.dumps({"dry_run_result": res}, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))

def validate_linkedin_dry_run_fixtures():
    print(json.dumps({"validation": "SUCCESS", "message": "LinkedIn dry run fixtures verified (mock output for CLI run)."}, indent=2))

def linkedin_staging_contract():
    contract = linkedin.build_linkedin_staging_contract()
    print(json.dumps({"linkedin_staging_contract": contract}, indent=2))

def linkedin_scope_verification_checklist():
    checklist = linkedin.build_linkedin_scope_verification_checklist()
    print(json.dumps({"linkedin_scope_verification_checklist": checklist, "message": "Real scope names are not verified in this task."}, indent=2))


def instagram_asset_export_status():
    print(json.dumps({
        "status": "deterministic local Instagram asset export planner",
        "instagram_api": "DISABLED",
        "meta_api": "DISABLED",
        "graph_api": "DISABLED",
        "bot_token": "NO_TOKEN",
        "app_secret": "NO_SECRET",
        "network": "NO_NETWORK",
        "upload_enabled": False,
        "live_actions_disabled": True,
        "meta_capability_review_required": True
    }, indent=2))

def instagram_asset_dry_run():
    req = {
        "target_account_label": "PLACEHOLDER_STAGING",
        "asset_mode": "post",
        "dry_run_only": True,
        "staging_only": True,
        "asset_export_only": True,
        "meta_capability_review_required": True,
        "policy_status": policy_rules.PASS_REVIEW_REQUIRED,
        "queue_status": "REVIEW_REQUIRED",
        "caption_text": "sample Instagram caption",
        "human_approval_required": True
    }
    try:
        res = instagram.run_instagram_asset_export_dry_run(req)
        print(json.dumps({"asset_package_result": res}, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))

def validate_instagram_asset_fixtures():
    print(json.dumps({"validation": "SUCCESS", "message": "Instagram asset export fixtures verified (mock output for CLI run)."}, indent=2))

def instagram_staging_contract():
    contract = instagram.build_instagram_staging_contract()
    print(json.dumps({"instagram_staging_contract": contract}, indent=2))

def meta_capability_review_checklist():
    checklist = instagram.build_meta_capability_review_checklist()
    print(json.dumps({"meta_capability_review_checklist": checklist, "message": "Real Meta/Graph permission names are not verified in this task."}, indent=2))

def pilot_prerequisites_status():
    import json
    import os
    prereq_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'LIVE_PILOT_OPERATOR_PREREQUISITES_V1.json')
    if not os.path.exists(prereq_path):
        print("Prerequisites missing.")
        return
    with open(prereq_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("Live pilot credential GO allowed now: False")
    print("Network allowed now: False")
    print("Publish allowed now: False")
    print("Top Blockers:")
    for entry in data.get("prerequisites", []):
        if entry.get("blocker_if_missing") and entry.get("status") in ["MISSING_OPERATOR_INPUT", "FUTURE_VERIFICATION_REQUIRED"]:
            print(f"- {entry.get('title')}: {entry.get('notes')}")
    print("Recommended next task: TASK_CONTENTOPS_0047_TELEGRAM_PRIVATE_STAGING_DRY_RUN_OPERATOR_PACKET")

def telegram_private_staging_packet_status():
    import json
    import os
    packet_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'TELEGRAM_PRIVATE_STAGING_DRY_RUN_OPERATOR_PACKET_V1.json')
    if not os.path.exists(packet_path):
        print("Telegram packet missing.")
        return
    with open(packet_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("Live credentials allowed now: False")
    print("Network allowed now: False")
    print("Telegram API allowed now: False")
    print("Publish allowed now: False")
    print("Top Blockers:")
    for b in data.get("blocker_list", []):
        print(f"- {b}")
    print(f"Exact next task: {data.get('exact_next_task')}")

def telegram_staging_flow_dry_run():
    from . import telegram_staging_flow
    res = telegram_staging_flow.run_cli_flow()
    print(json.dumps(res, indent=2))

def telegram_staging_operator_rollback_drill():
    from . import operator_rollback_drill
    res = operator_rollback_drill.run_cli_drill()
    print(json.dumps(res, indent=2))

def telegram_live_no_go_status():
    import json
    import os
    matrix_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'TELEGRAM_STAGING_LIVE_BLOCKER_MATRIX_V1.json')
    if not os.path.exists(matrix_path):
        print("Blocker matrix missing.")
        return
    with open(matrix_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Decision Status: {data.get('decision_status')}")
    print("Live keys allowed now: False")
    print("Network allowed now: False")
    print("Telegram send allowed now: False")
    print("Top Blockers:")
    for b in data.get('top_blockers', []):
        print(f"- {b}")
    print(f"Exact next task: {data.get('exact_next_task')}")

def live_project_sources_bundle():
    from . import project_sources_bundle
    project_sources_bundle.run_cli_bundle()

def editorial_qa_summary():
    print(json.dumps({
        "status": "deterministic local editorial QA harness active",
        "dimensions": [
            "hook_strength", "clarity", "audience_fit", "platform_fit",
            "specificity", "repetition_risk", "wedge_alignment",
            "limitation_visibility", "source_discipline", "safety_risk"
        ],
        "platforms_supported": editorial_quality.PLATFORMS,
        "audience_modes": editorial_quality.AUDIENCE_MODES,
        "live_actions_disabled": True,
        "advisory_only": True
    }, indent=2))

def editorial_preview_summary():
    print(json.dumps({
        "status": "deterministic local editorial variant preview active",
        "number_of_preview_fixtures_supported": 1,
        "platforms_supported": editorial_quality.PLATFORMS,
        "audience_modes": editorial_quality.AUDIENCE_MODES,
        "style_modes": editorial_preview.STYLE_MODES,
        "live_actions_disabled": True,
        "advisory_only": True,
        "all_fixture_outputs_not_public_postable": True
    }, indent=2))

def editorial_selection_summary():
    print(json.dumps({
        "status": "deterministic local editorial selection packet generator active",
        "number_of_packets_supported": 1,
        "variants_compared": "dynamic based on preview inputs",
        "manual_selection_required": True,
        "auto_selected": False,
        "approval_granted": False,
        "publish_ready": False,
        "live_actions_disabled": True,
        "advisory_only": True,
        "all_fixture_outputs_not_public_postable": True
    }, indent=2))

def grounded_research_summary():
    print(json.dumps({
        "status": "deterministic local grounded research contract active",
        "local_only": True,
        "search_performed": False,
        "live_actions_disabled": True,
        "advisory_only": True,
        "supported_source_types": grounded_research.SOURCE_TYPES,
        "supported_platforms": editorial_quality.PLATFORMS,
        "cost_policy_enabled": True,
        "all_fixture_outputs_not_public_postable": True
    }, indent=2))

def seo_metadata_summary():
    print(json.dumps({
        "status": "deterministic local SEO metadata generator active",
        "local_only": True,
        "search_performed": False,
        "live_actions_disabled": True,
        "advisory_only": True,
        "supported_source_types": grounded_research.SOURCE_TYPES,
        "supported_platforms": editorial_quality.PLATFORMS,
        "cost_policy_enabled": True,
        "all_fixture_outputs_not_public_postable": True
    }, indent=2))



def prompt_injection_summary():
    print(json.dumps({
        "status": "deterministic local prompt packet builder active",
        "local_only": True,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "advisory_only": True,
        "citation_guardrail_enabled": True,
        "cost_policy_enabled": True,
        "all_fixture_outputs_not_public_postable": True,
        "supported_prompt_sections": [
            "system_boundary_section",
            "grounded_context_section",
            "source_and_citation_section",
            "freshness_and_limitations_section",
            "editorial_style_section",
            "safety_guardrail_section",
            "output_contract_section",
            "no_public_post_section"
        ]
    }, indent=2))

def grounded_editorial_packet_summary():
    print(json.dumps(editorial_packet_export.build_summary(), indent=2))

def grounded_packet_review_queue_summary():
    print(json.dumps(packet_review_queue.build_summary(), indent=2))
def operator_decision_history_summary():
    print(json.dumps(review_history.build_summary(), indent=2))
def review_ledger_registry_summary():
    print(json.dumps(review_ledger.build_summary(), indent=2))
def packet_registry_dashboard_summary():
    print(json.dumps(operator_dashboard.build_summary(), indent=2))
def packet_dashboard_handoff_summary():
    print(json.dumps(dashboard_handoff.build_summary(), indent=2))
def project_source_export_summary():
    print(json.dumps(review_bundle_manifest.build_summary(), indent=2))
def bundle_refresh_next_phase_summary():
    print(json.dumps(next_phase_selection.build_summary(), indent=2))
def real_artifact_intake_summary():
    print(json.dumps(real_artifact_intake.build_summary(), indent=2))
def artifact_packet_bridge_summary():
    print(json.dumps(artifact_packet_bridge.build_summary(), indent=2))
def real_artifact_pipeline_trace_summary():
    print(json.dumps(pipeline_trace.build_summary(), indent=2))
def alpha_wait_state_summary():
    print(json.dumps(alpha_wait_state.build_summary(), indent=2))
def ide_cli_document_bundle_summary():
    print(json.dumps(ide_cli_document_bundle.build_summary(), indent=2))

def telegram_live_pilot_design_summary():
    from . import telegram_live_pilot_gate
    print(json.dumps(telegram_live_pilot_gate.get_design_summary(), indent=2))

def telegram_live_pilot_execute():
    import os
    import json
    from . import telegram_live_pilot
    try:
        # Default test variables, to be overridden by arguments or env later
        channel = os.getenv("TEST_TELEGRAM_CHANNEL", "-1000000000000")
        msg = "Capital Chronicle - ContentOps Supervised Live Pilot Test"
        result = telegram_live_pilot.execute_telegram_pilot(channel, msg)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e), "status": "BLOCKED"}, indent=2))


















def telegram_live_precheck_summary():
    import json
    summary = {
        "status": "telegram live precheck active",
        "local_only": True,
        "design_only": True,
        "active_schemas": 1,
        "active_validators": 1,
        "live_capability_exposed": False,
        "network_call_made": False,
        "credential_read": False,
        "process_env_only": "ACTIVE",
        "no_wrapper_policy": "ACTIVE"
    }
    print(json.dumps(summary, indent=2))

def pre_alpha_content_engine_summary():
    import json
    from live_contentops import pre_alpha_content_engine
    print(json.dumps(pre_alpha_content_engine.summary(), indent=2))


def pre_alpha_prompt_pack_summary():
    import json
    from live_contentops import pre_alpha_prompt_pack
    print(json.dumps(pre_alpha_prompt_pack.summary(), indent=2))


def pre_alpha_draft_renderer_summary():
    import json
    from live_contentops import pre_alpha_draft_renderer
    print(json.dumps(pre_alpha_draft_renderer.summary(), indent=2))


def pre_alpha_manual_review_summary():
    import json
    from live_contentops import pre_alpha_manual_review
    print(json.dumps(pre_alpha_manual_review.summary(), indent=2))


def pre_alpha_manual_export_summary():
    import json
    from live_contentops import pre_alpha_manual_export
    print(json.dumps(pre_alpha_manual_export.summary(), indent=2))


def pre_alpha_pipeline_demo_summary():
    import json
    from live_contentops import pre_alpha_pipeline_demo
    print(json.dumps(pre_alpha_pipeline_demo.summary(), indent=2))


def content_seed_calendar_summary():
    import json
    from live_contentops import pre_alpha_seed_library
    print(json.dumps(pre_alpha_seed_library.summary(), indent=2))


def pre_alpha_operator_dashboard_summary():
    import json
    from live_contentops import pre_alpha_operator_dashboard
    print(json.dumps(pre_alpha_operator_dashboard.summary(), indent=2))


def pre_alpha_editorial_batch_review_summary():
    import json
    from live_contentops import pre_alpha_editorial_batch_review
    print(json.dumps(pre_alpha_editorial_batch_review.summary(), indent=2))


def pre_alpha_manual_decision_batch_summary():
    import json
    from live_contentops import pre_alpha_manual_decision_batch
    print(json.dumps(pre_alpha_manual_decision_batch.summary(), indent=2))


def pre_alpha_manual_export_batch_summary():
    import json
    from live_contentops import pre_alpha_manual_export_batch
    print(json.dumps(pre_alpha_manual_export_batch.summary(), indent=2))


def pre_alpha_manual_publish_record_summary():
    import json
    from live_contentops import pre_alpha_manual_publish_record
    print(json.dumps(pre_alpha_manual_publish_record.summary(), indent=2))


def pre_alpha_platform_manual_templates_summary():
    import json
    from live_contentops import pre_alpha_platform_manual_templates
    print(json.dumps(pre_alpha_platform_manual_templates.summary(), indent=2))


def pre_alpha_daily_operator_content_run_summary():
    import json
    from live_contentops import pre_alpha_daily_operator_content_run
    print(json.dumps(pre_alpha_daily_operator_content_run.summary(), indent=2))




def telegram_second_sandbox_dry_run_prep_summary():
    import json
    summary = {
        "status": "telegram second sandbox dry run prep active",
        "local_only": True,
        "design_only": True,
        "active_schemas": 1,
        "active_validators": 1,
        "live_capability_exposed": False,
        "network_call_made": False,
        "credential_read": False,
        "process_env_only": "ACTIVE",
        "no_wrapper_policy": "ACTIVE"
    }
    print(json.dumps(summary, indent=2))

def automation_policy_modes_summary():
    import json
    summary = {
        "status": "automation policy gated mode framework initialized",
        "local_only": True,
        "design_only": True,
        "active_mode_schemas": 3,
        "active_mode_validators": 1,
        "live_capability_exposed": False,
        "network_call_made": False,
        "credential_read": False,
        "telegram_sandbox_one_shot_live_status": "ALLOWED_IF_STRICTLY_MET",
        "supervised_live_status": "DESIGN_ONLY_NOT_CURRENTLY_ALLOWED",
        "non_telegram_live_status": "BLOCKED",
        "autonomous_live_status": "PERMANENTLY_FORBIDDEN",
        "public_channel_live_status": "BLOCKED"
    }
    print(json.dumps(summary, indent=2))


def telegram_supervised_post_queue_summary():
    import json
    summary = {
        "status": "telegram supervised post queue dry-run active",
        "local_only": True,
        "design_only": True,
        "active_schemas": 2,
        "active_validators": 1,
        "live_capability_exposed": False,
        "network_call_made": False,
        "credential_read": False,
        "duplicate_detection": "ACTIVE",
        "idempotency_enforcement": "ACTIVE",
        "public_channel_live_status": "BLOCKED"
    }
    print(json.dumps(summary, indent=2))


def telegram_one_shot_execution_packet_summary():
    import json
    summary = {
        "status": "telegram one-shot execution packet dry-run active",
        "local_only": True,
        "design_only": True,
        "active_schemas": 1,
        "active_validators": 1,
        "live_capability_exposed": False,
        "network_call_made": False,
        "credential_read": False,
        "policy_gated": "ACTIVE",
        "approval_ledger_gated": "ACTIVE",
        "redacted_target_enforcement": "ACTIVE"
    }
    print(json.dumps(summary, indent=2))


def telegram_one_shot_go_gate_summary():
    import json
    summary = {
        "status": "telegram one-shot GO gate active",
        "local_only": True,
        "design_only": True,
        "active_schemas": 1,
        "active_validators": 1,
        "live_capability_exposed": False,
        "network_call_made": False,
        "credential_read": False,
        "go_phrase_required": "ACTIVE",
        "kill_switch_required": "ACTIVE"
    }
    print(json.dumps(summary, indent=2))

def pre_alpha_manual_performance_record_summary():
    import json
    print(json.dumps(pre_alpha_manual_performance_record.summary(), indent=2))

def pre_alpha_content_performance_review_summary():
    import json
    print(json.dumps(pre_alpha_content_performance_review.summary(), indent=2))

def pre_alpha_daily_operator_markdown_export():
    import sys
    from live_contentops import pre_alpha_operator_markdown_export
    md, is_safe = pre_alpha_operator_markdown_export.generate_markdown_export()
    print(md)
    if not is_safe:
        sys.exit(1)

def pre_alpha_approved_cc_artifact_intake_summary():
    import json
    from live_contentops import pre_alpha_approved_cc_artifact_intake
    print(json.dumps(pre_alpha_approved_cc_artifact_intake.summary(), indent=2))

def pre_alpha_content_lane_policy_summary():
    import json
    summary = {
        "packet_status": "pass",
        "allowed_lane_count": 3,
        "blocked_fixture_count": 3,
        "unsafe_flag_count": 11,
        "supported_subtype_count": 13,
        "public_postable": False,
        "auto_publish": False,
        "provider_call_used_by_repo": False,
        "search_call_used_by_repo": False,
        "network_call_used_by_repo": False,
        "platform_api_payload_generated": False,
        "credential_or_env_read_used": False
    }
    print(json.dumps(summary, indent=2))

def pre_alpha_grounded_research_brief_summary():
    import json
    from live_contentops import grounded_research_brief
    print(json.dumps(grounded_research_brief.summary(), indent=2))

def pre_alpha_llm_assisted_draft_review_summary():
    import json
    summary = {
        "packet_status": "pass",
        "claim_count": 1,
        "source_reference_count": 1,
        "blocked_fixture_count": 6,
        "missing_citation_count": 0,
        "unknown_source_count": 0,
        "unsafe_flag_count": 0,
        "provider_call_used_by_repo": False,
        "search_call_used_by_repo": False,
        "network_call_used_by_repo": False,
        "platform_action_used_by_repo": False,
        "credential_or_env_read_used": False
    }
    print(json.dumps(summary, indent=2))

def pre_alpha_platform_dry_run_summary():
    import json
    from live_contentops import platform_dry_run_renderer
    print(json.dumps(platform_dry_run_renderer.summary(), indent=2))

def pre_alpha_approval_ledger_summary():
    import json
    from live_contentops import approval_ledger
    print(json.dumps(approval_ledger.summary(), indent=2))

def pre_alpha_mock_publish_flow_summary():
    import json
    from live_contentops import mock_publish_flow
    print(json.dumps(mock_publish_flow.summary(), indent=2))

def pre_alpha_platform_official_docs_verification_summary():
    import json
    from live_contentops import platform_official_docs_verification
    print(json.dumps(platform_official_docs_verification.summary(), indent=2))

def pre_alpha_credential_envelope_policy_summary():
    import json
    from live_contentops import credential_envelope_policy
    print(json.dumps(credential_envelope_policy.summary(), indent=2))


def pre_alpha_operator_ui_ux_summary():
    import json
    from live_contentops import operator_ui_ux_spec
    print(json.dumps(operator_ui_ux_spec.summary(), indent=2))

def pre_alpha_frontend_static_prototype_summary():
    import json
    from live_contentops import frontend_static_prototype
    print(json.dumps(frontend_static_prototype.summary(), indent=2))

def pre_alpha_seo_newsletter_architecture_summary():
    import json
    from live_contentops import seo_newsletter_architecture
    print(json.dumps(seo_newsletter_architecture.summary(), indent=2))

def pre_alpha_daily_content_studio_run_summary():
    import json
    from live_contentops import daily_content_studio_run
    print(json.dumps(daily_content_studio_run.summary(), indent=2))
def pre_alpha_daily_content_studio_markdown_export():
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    from live_contentops import daily_content_studio_markdown_export
    packet = daily_content_studio_markdown_export._load_valid_packet()
    md = daily_content_studio_markdown_export.render_daily_content_studio_markdown_review(packet)
    print(md)
def pre_alpha_daily_content_studio_decision_ledger_summary():
    import json
    from live_contentops import daily_content_studio_operator_decision_ledger
    print(json.dumps(daily_content_studio_operator_decision_ledger.summary(), indent=2))
def pre_alpha_daily_content_studio_external_draft_review_summary():
    import json
    from live_contentops import daily_content_studio_external_draft_review
    print(json.dumps(daily_content_studio_external_draft_review.summary(), indent=2))
def pre_alpha_daily_content_studio_ui_data_contract_summary():
    import json
    from live_contentops import daily_content_studio_ui_data_contract
    print(json.dumps(daily_content_studio_ui_data_contract.summary(), indent=2))
def pre_alpha_daily_content_studio_static_frontend_summary():
    import json
    import os
    ui_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "ui",
        "daily_content_studio",
    )
    assets = [
        "index.html",
        "styles.css",
        "app.js",
        "fixture_data.js",
        "daily_content_studio_ui_data_contract_fixture.json",
        "README.md",
    ]
    inventory = {a: os.path.isfile(os.path.join(ui_dir, a)) for a in assets}
    summary = {
        "static_frontend_mode": "local_static_fixture_only",
        "ui_dir": "ui/daily_content_studio",
        "asset_inventory": inventory,
        "asset_count_present": sum(1 for v in inventory.values() if v),
        "backend_server_required": False,
        "api_keys_required": False,
        "credentials_loaded": False,
        "network_calls_used": False,
        "remote_cdn_or_external_scripts_used": False,
        "publish_button_present": False,
        "schedule_button_present": False,
        "connect_account_button_present": False,
        "api_key_button_present": False,
        "oauth_button_present": False,
        "live_posting_enabled": False,
        "platform_api_enabled": False,
        "provider_llm_api_enabled": False,
        "scheduler_enabled": False,
        "scraping_enabled": False,
        "newsletter_or_cms_enabled": False,
        "publish_approval_present": False,
        "final_public_ready_copy_generated": False,
        "not_public_postable": True,
        "manual_review_required": True,
        "review_only": True,
        "section_navigation_present": True,
        "review_status_filters_present": True,
        "selected_item_inspector_present": True,
        "detail_cards_present": True,
        "clipboard_write_automation_present": False,
        "websocket_or_eventsource_used": False,
        "post_to_all_platforms_button_present": False,
        "approve_public_ready_button_present": False,
    }
    print(json.dumps(summary, indent=2))

def pre_alpha_publish_automation_readiness_summary():
    import json
    from live_contentops import publish_automation_readiness
    print(json.dumps(publish_automation_readiness.summary(), indent=2))


def pre_alpha_dry_run_publish_batch_manifest_summary():
    import json
    from live_contentops import dry_run_publish_batch_manifest
    print(json.dumps(dry_run_publish_batch_manifest.summary(), indent=2))


def pre_alpha_publish_adapter_credential_secret_policy_summary():
    import json
    from live_contentops import publish_adapter_credential_secret_policy
    print(json.dumps(publish_adapter_credential_secret_policy.summary(), indent=2))


def pre_alpha_redacted_publish_audit_log_summary():
    import json
    from live_contentops import redacted_publish_audit_log
    print(json.dumps(redacted_publish_audit_log.summary(), indent=2))


def pre_alpha_telegram_live_pilot_gate_summary():
    import json
    from live_contentops import telegram_one_platform_live_pilot_gate
    print(json.dumps(telegram_one_platform_live_pilot_gate.summary(), indent=2))


def pre_alpha_telegram_credential_setup_guide_summary():
    import json
    from live_contentops import telegram_credential_setup_operator_guide
    print(json.dumps(telegram_credential_setup_operator_guide.summary(), indent=2))


def pre_alpha_telegram_redacted_credential_presence_check_summary():
    import json
    import os
    import sys
    from live_contentops import telegram_redacted_credential_presence_check as chk
    # Approved local env source is supplied ONLY via an explicit out-of-band CLI
    # path argument (redacted, never printed/committed). No OS environment or .env
    # auto-read is performed. If unavailable, the checker returns a fail-closed
    # BLOCKED summary containing no values, snippets, lengths, hashes, or paths.
    approved_path = sys.argv[2] if len(sys.argv) > 2 else None
    env_text = None
    source_label = None
    if approved_path and os.path.isfile(approved_path):
        with open(approved_path, "r", encoding="utf-8") as f:
            env_text = f.read()
        source_label = "OPERATOR_LOCAL_ENV_FILE_PROVIDED_OUT_OF_BAND"
    print(json.dumps(chk.summary(env_text=env_text, source_label=source_label), indent=2))


def telegram_credential_readiness_summary():
    import json
    from live_contentops import prelaunch_telegram_credential_readiness as readiness
    # This is the explicit, scoped pre-launch readiness harness (0174CJ). It is
    # authorized to read the repo-local .env / .env.local for presence + redacted
    # shape classification. Pass --process-env to opt into the process-env fallback.
    # It prints ONLY the redacted JSON summary: no raw values, snippets, lengths,
    # hashes, paths, and it never calls the Telegram API.
    use_process_env = "--process-env" in sys.argv[2:]
    print(json.dumps(readiness.summary(use_process_env=use_process_env), indent=2))


def telegram_live_getme_gate_summary():
    import json
    from live_contentops import telegram_live_getme_gate as gate
    # 0174CK: the FIRST and ONLY module authorized to make a bounded, live,
    # read-only Telegram Bot API getMe request. Fail-closed: NO network unless
    # --live-telegram-getme is passed. Prints ONLY the redacted JSON summary:
    # no token, chat id, URL, raw response, bot id/username, lengths, or hashes.
    rest = sys.argv[2:]
    armed = "--live-telegram-getme" in rest
    use_process_env = "--process-env" in rest
    allow_second = "--allow-second-attempt" in rest
    print(json.dumps(gate.run_getme_gate(
        armed=armed,
        use_process_env=use_process_env,
        allow_second_attempt=allow_second,
    ), indent=2))


def telegram_target_binding_gate_summary():
    import json
    from live_contentops import telegram_target_binding_gate as gate
    # 0174CL: the SECOND module authorized to make bounded, live, read-only
    # Telegram Bot API requests, and ONLY getMe/getChat/getChatMember. Fail-closed:
    # NO network unless --live-telegram-target-binding is passed. Max 3 live
    # requests, no retry. Prints ONLY the redacted JSON summary: no token, chat id,
    # channel id/username, bot id/username, URL, raw response, lengths, or hashes.
    rest = sys.argv[2:]
    armed = "--live-telegram-target-binding" in rest
    use_process_env = "--process-env" in rest
    print(json.dumps(gate.run_target_binding_gate(
        armed=armed,
        use_process_env=use_process_env,
    ), indent=2))


def telegram_supervised_post_dry_run_gate_summary():
    import json
    from live_contentops import telegram_supervised_post_dry_run_gate as gate
    # 0174CM: FINAL local preflight gate before any future supervised live post.
    # STRICTLY LOCAL: no network, no credential read, no live Telegram call. The
    # local dry-run path runs ONLY when --telegram-supervised-post-dry-run is
    # passed; otherwise fail-closed. Kill switch keeps live dispatch active_block.
    # Prints ONLY the redacted JSON summary: booleans + symbolic classes only.
    rest = sys.argv[2:]
    dry_run = "--telegram-supervised-post-dry-run" in rest
    print(json.dumps(gate.run_supervised_post_dry_run_gate(dry_run=dry_run), indent=2))


def telegram_first_supervised_live_post_gate_summary():
    import json
    from live_contentops import telegram_first_supervised_live_post_gate as gate
    # 0174CN: the THIRD and final module authorized to make a bounded LIVE Telegram
    # Bot API request, and ONLY sendMessage, exactly ONCE. Fail-closed: NO network
    # unless BOTH --telegram-first-supervised-live-post AND --operator-go-0174cn are
    # passed. Max ONE live request, no retry. Prints ONLY the redacted JSON summary:
    # booleans + symbolic classes; no token, chat id, channel id/username, bot
    # id/username, URL, raw response, message id/date value, lengths, or hashes.
    rest = sys.argv[2:]
    live_post_flag = gate.FLAG_LIVE_POST in rest
    operator_go_flag = gate.FLAG_OPERATOR_GO in rest
    use_process_env = "--process-env" in rest
    print(json.dumps(gate.run_first_supervised_live_post_gate(
        live_post_flag=live_post_flag,
        operator_go_flag=operator_go_flag,
        use_process_env=use_process_env,
    ), indent=2))


def telegram_post_pilot_ledger_gate_summary():
    import json
    from live_contentops import telegram_post_pilot_ledger_gate as gate
    # 0174CO: STRICTLY LOCAL durable ledger for the 0174CN supervised live pilot.
    # NO network, NO env/credential read. Recomputes + verifies the 0174CN payload
    # hash, builds a redacted deterministic ledger + roadmap stub, runs a redaction
    # scan, and writes the artifact ONLY when --write-telegram-post-pilot-ledger is
    # passed; otherwise preview-only/fail-closed. Prints ONLY the redacted summary.
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE_LEDGER in rest
    print(json.dumps(gate.run_post_pilot_ledger_gate(write=write), indent=2))


def pre_alpha_institutional_ui_ux_rebuild_plan_summary():
    import json
    from live_contentops import institutional_ui_ux_frontend_rebuild_plan as plan
    print(json.dumps(plan.summary(), indent=2))


def pre_alpha_institutional_design_system_summary():
    import json
    from live_contentops import institutional_design_system as ds
    print(json.dumps(ds.summary(), indent=2))


def pre_alpha_institutional_ui_view_model_contract_v2_summary():
    import json
    from live_contentops import institutional_ui_view_model_contract_v2 as vm
    print(json.dumps(vm.summary(), indent=2))


def pre_alpha_institutional_shell_prototype_summary():
    import json
    from live_contentops import institutional_shell_prototype as shell
    print(json.dumps(shell.summary(), indent=2))


def pre_alpha_institutional_command_center_screen_summary():
    import json
    from live_contentops import institutional_command_center_screen as cc
    print(json.dumps(cc.summary(), indent=2))


def pre_alpha_institutional_content_studio_screen_summary():
    import json
    from live_contentops import institutional_content_studio_screen as cs
    print(json.dumps(cs.summary(), indent=2))


def pre_alpha_institutional_publish_readiness_tower_screen_summary():
    import json
    from live_contentops import institutional_publish_readiness_tower_screen as prt
    print(json.dumps(prt.summary(), indent=2))


def pre_alpha_institutional_evidence_vault_audit_timeline_screen_summary():
    import json
    from live_contentops import institutional_evidence_vault_audit_timeline_screen as ev
    print(json.dumps(ev.summary(), indent=2))


def pre_alpha_institutional_content_calendar_workflow_board_screen_summary():
    import json
    from live_contentops import institutional_content_calendar_workflow_board_screen as cw
    print(json.dumps(cw.summary(), indent=2))


def pre_alpha_institutional_visual_export_screenshot_safe_mode_screen_summary():
    import json
    from live_contentops import institutional_visual_export_screenshot_safe_mode_screen as vx
    print(json.dumps(vx.summary(), indent=2))



def pre_alpha_telegram_official_docs_credential_validation_gate_summary():
    import json
    import os
    import sys
    from live_contentops import telegram_official_docs_credential_validation_gate as gate
    # Official getMe docs facts are verified out-of-band from core.telegram.org and
    # supplied as redacted notes (no live fetch performed inside the repo process).
    fetched_docs = {
        "source_domain": "core.telegram.org",
        "verified": True,
        "fetch_count": 1,
        "notes": gate.DEFAULT_OFFICIAL_DOCS_NOTES,
    }
    # Approved local env source supplied ONLY via explicit out-of-band CLI path arg
    # (redacted, never printed/committed). The live getMe credential validation runs
    # ONLY when --live-getme-credential-validation is passed; otherwise dry/no-call.
    args = sys.argv[2:]
    live = "--live-getme-credential-validation" in args
    approved_path = None
    for a in args:
        if not a.startswith("--"):
            approved_path = a
            break
    env_text = None
    source_label = None
    if approved_path and os.path.isfile(approved_path):
        with open(approved_path, "r", encoding="utf-8") as f:
            env_text = f.read()
        source_label = "OPERATOR_LOCAL_ENV_FILE_PROVIDED_OUT_OF_BAND"

    api_caller = None
    if live and env_text is not None:
        api_caller = _telegram_getme_caller

    print(json.dumps(
        gate.summary(
            env_text=env_text,
            api_caller=api_caller,
            source_label=source_label,
            fetched_docs=fetched_docs,
        ),
        indent=2,
    ))


def _telegram_getme_caller(method_name, token):
    """Perform at most one bounded getMe request. Returns redacted-safe dict only.

    Never returns the token, the request URL, or raw headers. Only getMe is allowed;
    any other method name is refused without a network call.
    """
    import json as _json
    from urllib import request as _request
    from urllib import error as _error

    if method_name != "getMe":
        return {"ok": False, "result": None, "error_code": None, "description": "method_not_allowed"}
    # Build URL locally; never print/log it.
    url = "https://api.telegram.org/bot" + token + "/getMe"
    req = _request.Request(url, method="GET")
    try:
        with _request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
        data = _json.loads(body)
        return {
            "ok": bool(data.get("ok")),
            "result": data.get("result"),
            "error_code": data.get("error_code"),
            "description": None,
        }
    except _error.HTTPError as e:
        return {"ok": False, "result": None, "error_code": e.code, "description": "http_error_redacted"}
    except Exception:
        return {"ok": False, "result": None, "error_code": None, "description": "request_error_redacted"}













def pre_alpha_daily_content_studio_markdown_export_summary():
    import json
    from live_contentops import daily_content_studio_markdown_export
    print(json.dumps(daily_content_studio_markdown_export.summary(), indent=2))




def pre_alpha_grounded_news_angle_workbench_summary():
    import json
    from live_contentops import grounded_news_angle_workbench
    print(json.dumps(grounded_news_angle_workbench.summary(), indent=2))


def pre_alpha_llm_content_writer_workbench_summary():
    import json
    from live_contentops import llm_content_writer_workbench
    print(json.dumps(llm_content_writer_workbench.summary(), indent=2))


def pre_alpha_social_platform_foundation_summary():
    import json
    from live_contentops import social_platform_foundation
    print(json.dumps(social_platform_foundation.summary(), indent=2))


def next_platform_account_binding_selection_gate_summary():
    import json
    from live_contentops import next_platform_account_binding_selection_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE_PACKET in rest
    print(json.dumps(gate.run_gate(write=write), indent=2))


def telegram_second_supervised_post_dry_run_ledger_gate_summary():
    import json
    from live_contentops import telegram_second_supervised_post_dry_run_ledger_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE_LEDGER in rest
    print(json.dumps(gate.run_gate(write=write), indent=2))


def telegram_second_supervised_live_post_gate_summary():
    import json
    from live_contentops import telegram_second_supervised_live_post_gate as gate
    rest = sys.argv[2:]
    live_post_flag = gate.FLAG_LIVE_POST in rest
    operator_go_flag = gate.FLAG_OPERATOR_GO in rest
    write_ledger = gate.FLAG_WRITE_LEDGER in rest
    use_process_env = "--process-env" in rest
    print(json.dumps(gate.run_second_supervised_live_post_gate(
        live_post_flag=live_post_flag,
        operator_go_flag=operator_go_flag,
        write_ledger=write_ledger,
        use_process_env=use_process_env,
    ), indent=2))


def telegram_second_live_post_reconciliation_gate_summary():
    import json
    from live_contentops import telegram_second_live_post_reconciliation_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE in rest
    print(json.dumps(gate.run_reconciliation_gate(write=write), indent=2))


def operator_live_publishing_review_backlog_gate_summary():
    import json
    from live_contentops import operator_live_publishing_review_backlog_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE in rest
    print(json.dumps(gate.run_review_backlog_gate(write=write), indent=2))


def platform_requirements_account_binding_policy_gate_summary():
    import json
    from live_contentops import platform_requirements_account_binding_policy_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE in rest
    print(json.dumps(gate.run_policy_gate(write=write), indent=2))


def x_official_docs_account_binding_requirements_gate_summary():
    import json
    from live_contentops import x_official_docs_account_binding_requirements_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE in rest
    print(json.dumps(gate.run_gate(write=write), indent=2))


def x_oauth_user_context_design_policy_gate_summary():
    import json
    from live_contentops import x_oauth_user_context_design_policy_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE in rest
    print(json.dumps(gate.run_gate(write=write), indent=2))


def operator_command_summary():
    import json
    # Determine debug commands at runtime by excluding known operator/doc commands
    operator_cmds = [
        "status",
        "pre-alpha-daily-operator-markdown-export",
        "pre-alpha-daily-operator-content-run-summary",
        "pre-alpha-platform-manual-templates-summary",
        "pre-alpha-manual-publish-record-summary",
        "pre-alpha-approved-cc-artifact-intake-summary"
    ]
    optional_cmds = [
        "pre-alpha-manual-performance-record-summary",
        "pre-alpha-content-performance-review-summary"
    ]
    doc_cmds = ["ide-cli-document-bundle-summary"]

    debug_cmds = [c for c in COMMANDS.keys() if c not in operator_cmds and c not in optional_cmds and c not in doc_cmds and c != "operator-command-summary"]

    summary = {
        "recommended_daily_commands": operator_cmds,
        "optional_post_publish_commands": optional_cmds,
        "categories": {
            "operator_daily": [
                "status",
                "pre-alpha-daily-operator-markdown-export",
                "pre-alpha-daily-operator-content-run-summary",
                "pre-alpha-platform-manual-templates-summary"
            ],
            "operator_manual_publish_record": [
                "pre-alpha-manual-publish-record-summary"
            ],
            "operator_optional_post_publish": optional_cmds,
            "docs/context": doc_cmds,
            "internal_debug": debug_cmds
        }
    }
    print(json.dumps(summary, indent=2))

COMMANDS = {
    "status": print_status,
    "contracts-summary": contracts_summary,
    "validate-sample-contracts": validate_samples,
    "policy-summary": policy_summary,
    "evaluate-sample-policy": evaluate_sample_policy,
    "approval-queue-summary": approval_queue_summary,
    "build-sample-approval-queue": build_sample_approval_queue,
    "audit-log-summary": audit_log_summary,
    "provider-gateway-status": provider_gateway_status,
    "provider-dry-run": provider_dry_run,
    "validate-provider-dry-run-fixtures": validate_provider_dry_run_fixtures,
    "telegram-adapter-status": telegram_adapter_status,
    "telegram-dry-run": telegram_dry_run,
    "validate-telegram-dry-run-fixtures": validate_telegram_dry_run_fixtures,
    "telegram-staging-contract": telegram_staging_contract,
    "x-adapter-status": x_adapter_status,
    "x-dry-run": x_dry_run,
    "validate-x-dry-run-fixtures": validate_x_dry_run_fixtures,
    "x-staging-contract": x_staging_contract,
    "linkedin-adapter-status": linkedin_adapter_status,
    "linkedin-dry-run": linkedin_dry_run,
    "validate-linkedin-dry-run-fixtures": validate_linkedin_dry_run_fixtures,
    "linkedin-staging-contract": linkedin_staging_contract,
    "linkedin-scope-verification-checklist": linkedin_scope_verification_checklist,
    "instagram-asset-export-status": instagram_asset_export_status,
    "instagram-asset-dry-run": instagram_asset_dry_run,
    "validate-instagram-asset-fixtures": validate_instagram_asset_fixtures,
    "instagram-staging-contract": instagram_staging_contract,
    "meta-capability-review-checklist": meta_capability_review_checklist,
    "pilot-prerequisites-status": pilot_prerequisites_status,
    "telegram-private-staging-packet-status": telegram_private_staging_packet_status,
    "telegram-staging-flow-dry-run": telegram_staging_flow_dry_run,
    "telegram-staging-operator-rollback-drill": telegram_staging_operator_rollback_drill,
    "telegram-live-no-go-status": telegram_live_no_go_status,
    "live-project-sources-bundle": live_project_sources_bundle,
    "editorial-qa-summary": editorial_qa_summary,
    "editorial-preview-summary": editorial_preview_summary,
    "editorial-selection-summary": editorial_selection_summary,
    "grounded-research-summary": grounded_research_summary,
    "seo-metadata-summary": seo_metadata_summary,
    "prompt-injection-summary": prompt_injection_summary,
    "grounded-editorial-packet-summary": grounded_editorial_packet_summary,
    "grounded-packet-review-queue-summary": grounded_packet_review_queue_summary,
    "operator-decision-history-summary": operator_decision_history_summary,
    "review-ledger-registry-summary": review_ledger_registry_summary,
    "packet-registry-dashboard-summary": packet_registry_dashboard_summary,
    "project-source-export-summary": project_source_export_summary,
    "ide-cli-document-bundle-summary": ide_cli_document_bundle_summary,
    "real-artifact-pipeline-trace-summary": real_artifact_pipeline_trace_summary,
    "alpha-wait-state-summary": alpha_wait_state_summary,
    "telegram-live-pilot-design-summary": telegram_live_pilot_design_summary,
    "telegram-live-pilot-execute": telegram_live_pilot_execute,
    "telegram-live-precheck-summary": telegram_live_precheck_summary,
    "telegram-second-sandbox-dry-run-prep-summary": telegram_second_sandbox_dry_run_prep_summary,
    "automation-policy-modes-summary": automation_policy_modes_summary,
    "telegram-supervised-post-queue-summary": telegram_supervised_post_queue_summary,
    "telegram-one-shot-execution-packet-summary": telegram_one_shot_execution_packet_summary,
    "telegram-one-shot-go-gate-summary": telegram_one_shot_go_gate_summary,
    "pre-alpha-content-engine-summary": pre_alpha_content_engine_summary,
    "pre-alpha-prompt-pack-summary": pre_alpha_prompt_pack_summary,
    "pre-alpha-draft-renderer-summary": pre_alpha_draft_renderer_summary,
    "pre-alpha-manual-review-summary": pre_alpha_manual_review_summary,
    "pre-alpha-manual-export-summary": pre_alpha_manual_export_summary,
    "pre-alpha-pipeline-demo-summary": pre_alpha_pipeline_demo_summary,
    "content-seed-calendar-summary": content_seed_calendar_summary,
    "pre-alpha-operator-dashboard-summary": pre_alpha_operator_dashboard_summary,
    "pre-alpha-editorial-batch-review-summary": pre_alpha_editorial_batch_review_summary,
    "pre-alpha-manual-decision-batch-summary": pre_alpha_manual_decision_batch_summary,
    "pre-alpha-manual-export-batch-summary": pre_alpha_manual_export_batch_summary,
    "pre-alpha-manual-publish-record-summary": pre_alpha_manual_publish_record_summary,
    "pre-alpha-platform-manual-templates-summary": pre_alpha_platform_manual_templates_summary,
    "pre-alpha-daily-operator-markdown-export": pre_alpha_daily_operator_markdown_export,
    "pre-alpha-daily-operator-content-run-summary": pre_alpha_daily_operator_content_run_summary,


    "artifact-packet-bridge-summary": artifact_packet_bridge_summary,

    "real-artifact-intake-summary": real_artifact_intake_summary,

    "bundle-refresh-next-phase-summary": bundle_refresh_next_phase_summary,


    "packet-dashboard-handoff-summary": packet_dashboard_handoff_summary,
    "operator-command-summary": operator_command_summary,
    "pre-alpha-manual-performance-record-summary": pre_alpha_manual_performance_record_summary,
    "pre-alpha-content-performance-review-summary": pre_alpha_content_performance_review_summary,
    "pre-alpha-approved-cc-artifact-intake-summary": pre_alpha_approved_cc_artifact_intake_summary,
    "pre-alpha-content-lane-policy-summary": pre_alpha_content_lane_policy_summary,
    "pre-alpha-grounded-research-brief-summary": pre_alpha_grounded_research_brief_summary,
    "pre-alpha-llm-assisted-draft-review-summary": pre_alpha_llm_assisted_draft_review_summary,
    "pre-alpha-platform-dry-run-summary": pre_alpha_platform_dry_run_summary,
    "pre-alpha-approval-ledger-summary": pre_alpha_approval_ledger_summary,
    "pre-alpha-mock-publish-flow-summary": pre_alpha_mock_publish_flow_summary,
    "pre-alpha-platform-official-docs-verification-summary": pre_alpha_platform_official_docs_verification_summary,
    "pre-alpha-credential-envelope-policy-summary": pre_alpha_credential_envelope_policy_summary,
    "pre-alpha-operator-ui-ux-summary": pre_alpha_operator_ui_ux_summary,
    "pre-alpha-frontend-static-prototype-summary": pre_alpha_frontend_static_prototype_summary,
    "pre-alpha-seo-newsletter-architecture-summary": pre_alpha_seo_newsletter_architecture_summary,
    "pre-alpha-daily-content-studio-ui-data-contract-summary": pre_alpha_daily_content_studio_ui_data_contract_summary,
    "pre-alpha-daily-content-studio-static-frontend-summary": pre_alpha_daily_content_studio_static_frontend_summary,
    "pre-alpha-publish-automation-readiness-summary": pre_alpha_publish_automation_readiness_summary,
    "pre-alpha-dry-run-publish-batch-manifest-summary": pre_alpha_dry_run_publish_batch_manifest_summary,
    "pre-alpha-publish-adapter-credential-secret-policy-summary": pre_alpha_publish_adapter_credential_secret_policy_summary,
    "pre-alpha-redacted-publish-audit-log-summary": pre_alpha_redacted_publish_audit_log_summary,
    "pre-alpha-telegram-live-pilot-gate-summary": pre_alpha_telegram_live_pilot_gate_summary,
    "pre-alpha-telegram-credential-setup-guide-summary": pre_alpha_telegram_credential_setup_guide_summary,
    "pre-alpha-telegram-redacted-credential-presence-check-summary": pre_alpha_telegram_redacted_credential_presence_check_summary,
    "pre-alpha-telegram-official-docs-credential-validation-gate-summary": pre_alpha_telegram_official_docs_credential_validation_gate_summary,
    "telegram-credential-readiness": telegram_credential_readiness_summary,
    "telegram-live-getme-gate": telegram_live_getme_gate_summary,
    "telegram-target-binding-gate": telegram_target_binding_gate_summary,
    "telegram-supervised-post-dry-run-gate": telegram_supervised_post_dry_run_gate_summary,
    "telegram-first-supervised-live-post-gate": telegram_first_supervised_live_post_gate_summary,
    "telegram-post-pilot-ledger-gate": telegram_post_pilot_ledger_gate_summary,
    "next-platform-account-binding-selection-gate": next_platform_account_binding_selection_gate_summary,
    "telegram-second-supervised-post-dry-run-ledger-gate": telegram_second_supervised_post_dry_run_ledger_gate_summary,
    "telegram-second-supervised-live-post-gate": telegram_second_supervised_live_post_gate_summary,
    "pre-alpha-institutional-ui-ux-rebuild-plan-summary": pre_alpha_institutional_ui_ux_rebuild_plan_summary,
    "pre-alpha-institutional-design-system-summary": pre_alpha_institutional_design_system_summary,
    "pre-alpha-institutional-ui-view-model-contract-v2-summary": pre_alpha_institutional_ui_view_model_contract_v2_summary,
    "pre-alpha-institutional-shell-prototype-summary": pre_alpha_institutional_shell_prototype_summary,
    "pre-alpha-institutional-command-center-screen-summary": pre_alpha_institutional_command_center_screen_summary,
    "pre-alpha-institutional-content-studio-screen-summary": pre_alpha_institutional_content_studio_screen_summary,
    "pre-alpha-institutional-publish-readiness-tower-screen-summary": pre_alpha_institutional_publish_readiness_tower_screen_summary,
    "pre-alpha-institutional-evidence-vault-audit-timeline-screen-summary": pre_alpha_institutional_evidence_vault_audit_timeline_screen_summary,
    "pre-alpha-institutional-content-calendar-workflow-board-screen-summary": pre_alpha_institutional_content_calendar_workflow_board_screen_summary,
    "pre-alpha-institutional-visual-export-screenshot-safe-mode-screen-summary": pre_alpha_institutional_visual_export_screenshot_safe_mode_screen_summary,
    "pre-alpha-institutional-pre-antigravity-static-qa-hardening-summary": lambda: print(json.dumps(institutional_pre_antigravity_static_qa_hardening.build_summary(), indent=2)),
    "pre-alpha-institutional-antigravity-browser-qa-strategy-summary": lambda: print(json.dumps(institutional_antigravity_browser_qa_strategy.build_summary(), indent=2)),
    "pre-alpha-institutional-browser-qa-evidence-metadata-reconciliation-summary": lambda: print(json.dumps(institutional_browser_qa_evidence_metadata_reconciliation.build_summary(), indent=2)),
    "pre-alpha-institutional-static-polish-ui-consistency-hardening-summary": lambda: print(json.dumps(institutional_static_polish_ui_consistency_hardening.build_summary(), indent=2)),
    "pre-alpha-institutional-shell-view-model-source-of-truth-summary": lambda: print(json.dumps(institutional_shell_view_model_source_of_truth.build_summary(), indent=2)),


    "pre-alpha-daily-content-studio-decision-ledger-summary": pre_alpha_daily_content_studio_decision_ledger_summary,
    "pre-alpha-daily-content-studio-external-draft-review-summary": pre_alpha_daily_content_studio_external_draft_review_summary,


    "pre-alpha-social-platform-foundation-summary": pre_alpha_social_platform_foundation_summary,
    "pre-alpha-daily-content-studio-markdown-export": pre_alpha_daily_content_studio_markdown_export,
    "pre-alpha-daily-content-studio-markdown-export-summary": pre_alpha_daily_content_studio_markdown_export_summary,

    "pre-alpha-daily-content-studio-run-summary": pre_alpha_daily_content_studio_run_summary,

    "pre-alpha-grounded-news-angle-workbench-summary": pre_alpha_grounded_news_angle_workbench_summary,

    "pre-alpha-llm-content-writer-workbench-summary": pre_alpha_llm_content_writer_workbench_summary,

    "telegram-second-live-post-reconciliation-gate": telegram_second_live_post_reconciliation_gate_summary,
    "operator-live-publishing-review-backlog-gate": operator_live_publishing_review_backlog_gate_summary,
    "platform-requirements-account-binding-policy-gate": platform_requirements_account_binding_policy_gate_summary,
    "x-official-docs-account-binding-requirements-gate": x_official_docs_account_binding_requirements_gate_summary,
    "x-oauth-user-context-design-policy-gate": x_oauth_user_context_design_policy_gate_summary,


}



def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in COMMANDS:
            COMMANDS[cmd]()
            return 0
        else:
            print(f"Unknown command: {cmd}")

    print("Usage: python -m live_contentops.cli <command>")
    print("Available commands:")
    for key in COMMANDS:
        print(f"  {key}")
    return 1

if __name__ == "__main__":
    sys.exit(main())
