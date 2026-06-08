"""CLI entrypoint."""
import sys
import json
from pathlib import Path
from . import status
from . import contracts
from . import contract_validation
from . import policy_engine
from . import policy_rules

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

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "status":
            print_status()
            return 0
        elif cmd == "contracts-summary":
            contracts_summary()
            return 0
        elif cmd == "validate-sample-contracts":
            validate_samples()
            return 0
        elif cmd == "policy-summary":
            policy_summary()
            return 0
        elif cmd == "evaluate-sample-policy":
            evaluate_sample_policy()
            return 0

    print("Usage: python -m live_contentops.cli [status|contracts-summary|validate-sample-contracts|policy-summary|evaluate-sample-policy]")
    return 1

if __name__ == "__main__":
    sys.exit(main())
