"""Local-only provider live-gate readiness and operator approval contract (SCD, 0174BD)."""
from live_contentops.scd_domain_model import PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN, _schema_ok, _result
from live_contentops.scd_canonical_draft_lifecycle import _common_safety_blocks

def _rollup(states):
    if BLOCKED in states: return BLOCKED
    if UNKNOWN in states: return UNKNOWN
    if REVIEW_REQUIRED in states: return REVIEW_REQUIRED
    return PASS

def validate_provider_live_gate_readiness_input(packet):
    ok, msg = _schema_ok(packet, "scd_provider_live_gate_readiness_input.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    upstream_states = [
        "quota_retry_policy_state",
        "prompt_pack_state",
        "canonical_draft_lifecycle_state",
        "provider_gateway_dry_run_state",
        "batch_dry_run_report_state",
        "aggregate_spend_ceiling_state"
    ]
    
    for state_field in upstream_states:
        val = packet.get(state_field)
        if val != PASS:
            blocked.append(f"{state_field} must be PASS")

    if not packet.get("operator_approval_required"):
        blocked.append("operator_approval_required must be true")
    if not packet.get("explicit_api_gate_required"):
        blocked.append("explicit_api_gate_required must be true")
        
    false_fields = [
        "executable",
        "provider_api_allowed",
        "network_allowed",
        "credentials_required",
        "env_read_allowed",
        "credential_lookup_performed",
        "api_key_present",
        "provider_ready",
        "live_ready",
        "public_ready"
    ]
    for field in false_fields:
        if packet.get(field):
            blocked.append(f"{field} must be false")
            
    return _result(blocked, review, unknown)

def validate_provider_live_gate_operator_approval(packet):
    ok, msg = _schema_ok(packet, "scd_provider_live_gate_operator_approval.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    state = packet.get("operator_approval_state")
    if state == "APPROVED_FOR_FUTURE_LIVE_GATE_REVIEW":
        pass
    elif state == "APPROVED_TO_EXECUTE":
        blocked.append("APPROVED_TO_EXECUTE is forbidden")
    elif not state:
        review.append("missing operator approval state")
    elif state == "STALE":
        review.append("stale operator approval")
    else:
        review.append("unknown or incomplete operator approval state")
        
    wording = packet.get("approval_wording", "").lower()
    unsafe_words = ["execute", "send", "call provider", "use api", "go live", "dispatch", "post", "publish", "webhook", "token", "key", "oauth"]
    for w in unsafe_words:
        if w in wording:
            blocked.append(f"approval wording contains unsafe word: {w}")

    return _result(blocked, review, unknown)

def validate_provider_live_gate_readiness_report(packet):
    ok, msg = _schema_ok(packet, "scd_provider_live_gate_readiness_report.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    false_fields = [
        "executable",
        "provider_api_allowed",
        "network_allowed",
        "credentials_required",
        "env_read_allowed",
        "credential_lookup_performed",
        "api_key_present",
        "provider_ready",
        "live_ready",
        "public_ready"
    ]
    for field in false_fields:
        if packet.get(field):
            blocked.append(f"{field} must be false")
            
    wording = (" ".join(packet.get("reasons", [])) + " " + packet.get("operator_approval_state", "") + " " + packet.get("approval_wording", "")).lower()
    unsafe_words = ["execute", "send", "call provider", "use api", "go live", "dispatch", "post", "publish", "webhook", "token", "key", "oauth"]
    for w in unsafe_words:
        if w in wording:
            blocked.append(f"reasons wording contains unsafe word: {w}")

    states = []
    sub_state_keys = [
        "readiness_input_state",
        "operator_approval_state",
        "audit_manifest_state",
        "quota_retry_policy_state",
        "prompt_pack_state",
        "canonical_draft_lifecycle_state",
        "provider_gateway_dry_run_state",
        "batch_dry_run_report_state",
        "aggregate_spend_ceiling_state"
    ]
    for k in sub_state_keys:
        if k in packet:
            states.append(packet[k])

    if states:
        rolled = _rollup(states)
    else:
        rolled = UNKNOWN
        
    claim = packet.get("validation_state")
    if claim != rolled:
        blocked.append(f"claimed validation_state {claim} != rolled up state {rolled}")

    if claim == PASS and rolled != PASS:
        blocked.append("PASS only allowed if all sub-states are PASS")
        
    if rolled == UNKNOWN:
        unknown.append("rolled up state is UNKNOWN")
    elif rolled == REVIEW_REQUIRED:
        review.append("rolled up state is REVIEW_REQUIRED")
    elif rolled == BLOCKED:
        blocked.append("rolled up state is BLOCKED")

    return _result(blocked, review, unknown)

def validate_provider_live_gate_audit_manifest(packet):
    ok, msg = _schema_ok(packet, "scd_provider_live_gate_audit_manifest.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    refs = packet.get("upstream_lineage_refs")
    if not refs:
        unknown.append("upstream_lineage_refs missing or empty")
        
    if unknown and packet.get("validation_state") == PASS:
        blocked.append("cannot be PASS if refs are missing")

    return _result(blocked, review, unknown)

def build_provider_live_gate_readiness_report(input_packet, approval_packet, manifest_packet):
    res_input = validate_provider_live_gate_readiness_input(input_packet)
    res_approval = validate_provider_live_gate_operator_approval(approval_packet)
    res_manifest = validate_provider_live_gate_audit_manifest(manifest_packet)
    
    states = [res_input["validation_state"], res_approval["validation_state"], res_manifest["validation_state"]]
    rolled = _rollup(states)
    
    reasons = res_input["reasons"] + res_approval["reasons"] + res_manifest["reasons"]
    reasons = [r for r in list(dict.fromkeys(reasons)) if r != "ok"]
    if not reasons:
        reasons = ["ok"]
        
    return {
        "schema_version": "1.0",
        "batch_id": input_packet.get("batch_id", "unknown"),
        "validation_state": rolled,
        "readiness_input_state": res_input["validation_state"],
        "operator_approval_state": res_approval["validation_state"],
        "audit_manifest_state": res_manifest["validation_state"],
        "quota_retry_policy_state": input_packet.get("quota_retry_policy_state", "UNKNOWN"),
        "prompt_pack_state": input_packet.get("prompt_pack_state", "UNKNOWN"),
        "canonical_draft_lifecycle_state": input_packet.get("canonical_draft_lifecycle_state", "UNKNOWN"),
        "provider_gateway_dry_run_state": input_packet.get("provider_gateway_dry_run_state", "UNKNOWN"),
        "batch_dry_run_report_state": input_packet.get("batch_dry_run_report_state", "UNKNOWN"),
        "aggregate_spend_ceiling_state": input_packet.get("aggregate_spend_ceiling_state", "UNKNOWN"),
        "provider_ready": False,
        "live_ready": False,
        "public_ready": False,
        "executable": False,
        "provider_api_allowed": False,
        "network_allowed": False,
        "credentials_required": False,
        "env_read_allowed": False,
        "credential_lookup_performed": False,
        "api_key_present": False,
        "reasons": reasons
    }

PROVIDER_LIVE_GATE_READINESS_VALIDATORS = {
    "readiness_input": validate_provider_live_gate_readiness_input,
    "operator_approval": validate_provider_live_gate_operator_approval,
    "readiness_report": validate_provider_live_gate_readiness_report,
    "audit_manifest": validate_provider_live_gate_audit_manifest
}
