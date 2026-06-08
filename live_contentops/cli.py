"""CLI entrypoint."""
import sys
import json
from . import status
from . import contracts
from . import contract_validation

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
    # Enum conversion for JSON
    sample["plane_owner"] = sample["plane_owner"].value
    sample["network_reach"] = sample["network_reach"].value
    try:
        contract_validation.validate_contract_dict(sample)
        print(json.dumps({"validation": "SUCCESS", "sample": sample}, indent=2))
    except Exception as e:
        print(json.dumps({"validation": "FAILED", "error": str(e)}, indent=2))

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
            
    print("Usage: python -m live_contentops.cli [status|contracts-summary|validate-sample-contracts]")
    return 1

if __name__ == "__main__":
    sys.exit(main())
