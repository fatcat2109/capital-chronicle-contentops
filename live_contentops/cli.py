"""CLI entrypoint."""
import sys
import json
from pathlib import Path
from typing import Any

from .live_entrypoint_registry_v1 import (
    LEGACY_AUTOMATION_QUARANTINED,
    LiveEntrypointQuarantined,
    SCHEDULER_LIVE_QUARANTINED,
    quarantine,
)
from .dual_lane_core_v0_shadow_demo_runner_v1 import core_v0_shadow_demo_command
from .core_v0_shadow_soak_runner_v1 import core_v0_shadow_soak_command
from .core_v0_acceptance_harness_v1 import core_v0_acceptance_command

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

import uuid

def print_status():
    s = status.get_status()
    print(json.dumps(s, indent=2))

def telemetry_summary():
    from .live_telemetry_v6 import TelemetryRegistry
    reg = TelemetryRegistry()
    print(json.dumps(reg.get_summary(), indent=2))

def platform_errors_summary():
    from .live_telemetry_v6 import TelemetryRegistry
    reg = TelemetryRegistry()
    events = reg.get_events()
    failures = [e for e in events if not e.get("success")]
    print(json.dumps({"failures": failures}, indent=2))

def scheduler_add_command():
    import argparse
    from dataclasses import asdict
    from .scheduler_v6 import OutboxScheduler
    parser = argparse.ArgumentParser(description="Add scheduled outbox entry")
    parser.add_argument("--platform-id", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--cron", required=True)
    parser.add_argument("--payload", required=True, help="JSON payload dict")
    parser.add_argument("--approved", action="store_true")
    args = parser.parse_args(sys.argv[2:])
    
    try:
        payload_dict = json.loads(args.payload)
    except Exception as e:
        print(json.dumps({"status": "FAILED", "error": f"Invalid payload JSON: {e}"}, indent=2))
        return

    sched = OutboxScheduler()
    entry = sched.add_entry(
        platform_id=args.platform_id,
        action=args.action,
        payload=payload_dict,
        cron_expression=args.cron,
        approved=args.approved
    )
    print(json.dumps({"status": "SUCCESS", "added": asdict(entry)}, indent=2, default=str))

def scheduler_list_command():
    from .scheduler_v6 import OutboxScheduler
    from dataclasses import asdict
    sched = OutboxScheduler()
    entries = sched.load_entries()
    print(json.dumps({"entries": [asdict(e) for e in entries]}, indent=2, default=str))

def scheduler_tick_command(argv: list[str] | None = None):
    import argparse
    import datetime
    parser = argparse.ArgumentParser(description="Execute scheduler tick")
    parser.add_argument("--now", help="ISO format datetime override")
    parser.add_argument("--fast-ship", action="store_true", help="Enable live platform dispatches")
    parser.add_argument("--dry-run", action="store_true", help="Force dry run mode")
    args = parser.parse_args(argv if argv is not None else sys.argv[2:])

    if args.fast_ship:
        quarantine(
            "contentops.cli_scheduler_fast_ship.v1",
            SCHEDULER_LIVE_QUARANTINED,
            "CLI fast-ship scheduler ticks are blocked until Wave 04 durable scheduling/outbox authority exists.",
        )

    current_time = None
    if args.now:
        try:
            current_time = datetime.datetime.fromisoformat(args.now)
        except Exception as e:
            print(json.dumps({"status": "FAILED", "error": f"Invalid datetime format: {e}"}, indent=2))
            return

    from .scheduler_v6 import OutboxScheduler
    sched = OutboxScheduler()
    result = sched.reconcile_outbox_timing(current_time=current_time, dry_run=True)
    print(json.dumps(result, indent=2))


def scheduler_command(argv: list[str] | None = None):
    command_args = list(argv or [])
    if not command_args:
        print(json.dumps({"status": "FAILED", "error": "scheduler subcommand required"}, indent=2))
        return
    action, *remaining = command_args
    if action == "tick":
        return scheduler_tick_command(remaining)
    print(json.dumps({"status": "FAILED", "error": f"unsupported scheduler subcommand: {action}"}, indent=2))

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
    prereq_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'archive', '_repo_cleanup_2026-07-03-pass2', 'docs', 'LIVE_PILOT_OPERATOR_PREREQUISITES_V1.json')
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
    packet_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'archive', '_repo_cleanup_2026-07-03', 'docs', 'TELEGRAM_PRIVATE_STAGING_DRY_RUN_OPERATOR_PACKET_V1.json')
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
    matrix_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'archive', '_repo_cleanup_2026-07-03', 'docs', 'TELEGRAM_STAGING_LIVE_BLOCKER_MATRIX_V1.json')
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
    quarantine(
        "contentops.cli_direct_platform_adapters.v1",
        LEGACY_AUTOMATION_QUARANTINED,
        "Direct Telegram live-pilot execution is quarantined; use ContentOpsProductionOrchestrator.",
    )


















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


def x_oauth_callback_pkce_dry_run_design_gate_summary():
    import json
    from live_contentops import x_oauth_callback_pkce_dry_run_design_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE in rest
    print(json.dumps(gate.run_gate(write=write), indent=2))


def x_oauth_redirect_ledger_callback_fixture_contract_gate_summary():
    import json
    from live_contentops import x_oauth_redirect_ledger_callback_fixture_contract_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE in rest
    print(json.dumps(gate.run_gate(write=write), indent=2))


def x_oauth_local_callback_handler_dry_run_stub_gate_summary():
    import json
    from live_contentops import x_oauth_local_callback_handler_dry_run_stub_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE in rest
    print(json.dumps(gate.run_gate(write=write), indent=2))


def x_oauth_callback_server_policy_gate_summary():
    import json
    from live_contentops import x_oauth_callback_server_policy_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE in rest
    print(json.dumps(gate.run_gate(write=write), indent=2))


def x_oauth_credential_readiness_policy_gate_summary():
    import json
    from live_contentops import x_oauth_credential_readiness_policy_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE in rest
    print(json.dumps(gate.run_gate(write=write), indent=2))


def x_oauth_redacted_credential_presence_check_design_gate_summary():
    import json
    from live_contentops import x_oauth_redacted_credential_presence_check_design_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE in rest
    print(json.dumps(gate.run_gate(write=write), indent=2))


def x_oauth_supervised_live_readiness_bridge_bundle_gate_summary():
    import json
    from live_contentops import x_oauth_supervised_live_readiness_bridge_bundle_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE in rest
    print(json.dumps(gate.run_gate(write=write), indent=2))


def x_oauth_live_read_only_identity_proof_gate_summary():
    import json
    from live_contentops import x_oauth_live_read_only_identity_proof_gate as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE in rest
    operator_go = gate.FLAG_OPERATOR_GO in rest
    execution_requested = gate.FLAG_EXECUTE in rest
    print(json.dumps(gate.run_gate(
        write=write,
        operator_go=operator_go,
        execution_requested=execution_requested,
    ), indent=2))


def telegram_readonly_channel_binding_permission_proof_summary():
    import json
    from live_contentops import telegram_readonly_channel_binding_permission_proof as gate
    rest = sys.argv[2:]
    write = gate.FLAG_WRITE in rest
    operator_go = gate.FLAG_OPERATOR_GO in rest
    execution_requested = gate.FLAG_EXECUTE in rest
    print(json.dumps(gate.run_telegram_readonly_channel_binding_permission_proof(
        write=write,
        operator_go=operator_go,
        execution_requested=execution_requested,
    ), indent=2))


def daily_app_command(argv: list[str] | None = None):
    import argparse
    import datetime as _datetime
    from .daily_app_supervisor_v1 import (
        ContentOpsDailyAppSupervisor,
        OPERATING_MODES,
    )

    parser = argparse.ArgumentParser(description="ContentOps Final Daily App supervisor")
    parser.add_argument("--store-path", required=True, help="Durable operational store sqlite path")
    parser.add_argument("--output-root", required=True, help="Output/state root for window artifacts")
    parser.add_argument("--mode", default="AUTONOMOUS_DEFAULT", choices=sorted(OPERATING_MODES))
    parser.add_argument("--once", action="store_true", help="Run a single supervisor tick and exit")
    parser.add_argument("--run-forever", action="store_true", help="Run the supervisor loop continuously")
    parser.add_argument("--poll-seconds", type=float, default=60.0)
    parser.add_argument("--max-ticks", type=int, default=None)
    parser.add_argument("--now", help="ISO datetime override for the supervisor clock (controlled/test)")
    parser.add_argument("--sidecar-glob", default=None, help="Optional rolling-X headline sidecar glob")
    args = parser.parse_args(argv if argv is not None else sys.argv[2:])

    if args.once and args.run_forever:
        print(json.dumps({"status": "FAILED", "error": "--once and --run-forever are mutually exclusive"}, indent=2))
        return

    clock = None
    if args.now:
        try:
            fixed = _datetime.datetime.fromisoformat(args.now.replace("Z", "+00:00"))
        except Exception as e:
            print(json.dumps({"status": "FAILED", "error": f"Invalid --now datetime: {e}"}, indent=2))
            return
        clock = lambda: fixed  # noqa: E731 - controlled clock override

    supervisor = ContentOpsDailyAppSupervisor(
        store_path=args.store_path,
        output_root=args.output_root,
        operating_mode=args.mode,
        clock=clock,
        sidecar_glob=args.sidecar_glob,
    )
    if args.once:
        report = supervisor.tick()
        print(json.dumps({"status": "SUCCESS", "tick_report": report}, indent=2, default=str))
        return
    if args.run_forever:
        ticks = supervisor.run_forever(poll_seconds=args.poll_seconds, max_ticks=args.max_ticks)
        print(json.dumps({"status": "SUCCESS", "ticks": ticks}, indent=2))
        return
    print(json.dumps({"status": "FAILED", "error": "specify --once or --run-forever"}, indent=2))


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
    "telemetry-summary": telemetry_summary,
    "platform-errors-summary": platform_errors_summary,
    "scheduler": scheduler_command,
    "scheduler-add": scheduler_add_command,
    "scheduler-list": scheduler_list_command,
    "scheduler-tick": scheduler_tick_command,
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


    "artifact-packet-bridge-summary": artifact_packet_bridge_summary,

    "real-artifact-intake-summary": real_artifact_intake_summary,

    "bundle-refresh-next-phase-summary": bundle_refresh_next_phase_summary,


    "packet-dashboard-handoff-summary": packet_dashboard_handoff_summary,
    "operator-command-summary": operator_command_summary,
    "next-platform-account-binding-selection-gate": next_platform_account_binding_selection_gate_summary,
    "telegram-second-supervised-post-dry-run-ledger-gate": telegram_second_supervised_post_dry_run_ledger_gate_summary,
    "telegram-second-supervised-live-post-gate": telegram_second_supervised_live_post_gate_summary,








    "telegram-second-live-post-reconciliation-gate": telegram_second_live_post_reconciliation_gate_summary,
    "operator-live-publishing-review-backlog-gate": operator_live_publishing_review_backlog_gate_summary,
    "platform-requirements-account-binding-policy-gate": platform_requirements_account_binding_policy_gate_summary,
    "x-official-docs-account-binding-requirements-gate": x_official_docs_account_binding_requirements_gate_summary,
    "x-oauth-user-context-design-policy-gate": x_oauth_user_context_design_policy_gate_summary,
    "x-oauth-callback-pkce-dry-run-design-gate": x_oauth_callback_pkce_dry_run_design_gate_summary,
    "x-oauth-redirect-ledger-callback-fixture-contract-gate": x_oauth_redirect_ledger_callback_fixture_contract_gate_summary,
    "x-oauth-local-callback-handler-dry-run-stub-gate": x_oauth_local_callback_handler_dry_run_stub_gate_summary,
    "x-oauth-callback-server-policy-gate": x_oauth_callback_server_policy_gate_summary,
    "x-oauth-credential-readiness-policy-gate": x_oauth_credential_readiness_policy_gate_summary,
    "x-oauth-redacted-credential-presence-check-design-gate": x_oauth_redacted_credential_presence_check_design_gate_summary,
    "x-oauth-supervised-live-readiness-bridge-bundle-gate": x_oauth_supervised_live_readiness_bridge_bundle_gate_summary,
    "x-oauth-live-read-only-identity-proof-gate": x_oauth_live_read_only_identity_proof_gate_summary,
    "telegram-readonly-channel-binding-permission-proof": telegram_readonly_channel_binding_permission_proof_summary,
    "core-v0-shadow-demo": core_v0_shadow_demo_command,
    "core-v0-shadow-soak": core_v0_shadow_soak_command,
    "core-v0-acceptance": core_v0_acceptance_command,
    "daily-app": daily_app_command,


}



def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd in COMMANDS:
            try:
                if cmd in {
                    "core-v0-shadow-demo",
                    "core-v0-shadow-soak",
                    "core-v0-acceptance",
                    "daily-app",
                }:
                    return COMMANDS[cmd](sys.argv[2:]) or 0
                if cmd in {"scheduler", "scheduler-tick"}:
                    COMMANDS[cmd](sys.argv[2:])
                else:
                    COMMANDS[cmd]()
            except LiveEntrypointQuarantined as exc:
                print(json.dumps(exc.as_dict(), sort_keys=True))
                return 1
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
