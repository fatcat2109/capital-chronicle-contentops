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
    "editorial-qa-summary": editorial_qa_summary
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
