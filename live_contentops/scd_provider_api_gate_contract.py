"""Local-only credential envelope and explicit API gate contract (SCD, 0174BE)."""
import json
from live_contentops.scd_domain_model import PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN, _schema_ok, _result
from live_contentops.scd_canonical_draft_lifecycle import _common_safety_blocks

def _rollup(states):
    if BLOCKED in states: return BLOCKED
    if UNKNOWN in states: return UNKNOWN
    if REVIEW_REQUIRED in states: return REVIEW_REQUIRED
    return PASS

def validate_provider_credential_envelope(packet):
    ok, msg = _schema_ok(packet, "scd_provider_credential_envelope.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    if packet.get("credential_value_present"): blocked.append("credential_value_present is true")
    if packet.get("api_key_present"): blocked.append("api_key_present is true")
    if packet.get("env_read_performed"): blocked.append("env_read_performed is true")
    if packet.get("credential_lookup_performed"): blocked.append("credential_lookup_performed is true")
    
    refs = packet.get("required_credential_refs", [])
    if not refs:
        unknown.append("required_credential_refs missing or empty")
        
    s = json.dumps(packet).lower()
    if "sk-" in s or "bearer " in s or "token=" in s:
        blocked.append("raw api key or token detected")
        
    return _result(blocked, review, unknown)

def validate_explicit_api_gate_policy(packet):
    ok, msg = _schema_ok(packet, "scd_explicit_api_gate_policy.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    if packet.get("provider_allowlist_state") != PASS:
        blocked.append("provider_allowlist_state must be PASS")
        
    endpoint = packet.get("symbolic_endpoint_family", "").lower()
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        blocked.append("real URL/HTTP endpoint present")
        
    if packet.get("provider_client_constructed"): blocked.append("provider_client_constructed is true")
    if packet.get("network_allowed"): blocked.append("network_allowed is true")
    if packet.get("executable"): blocked.append("executable is true")
    
    return _result(blocked, review, unknown)

def validate_provider_api_request_budget(packet):
    ok, msg = _schema_ok(packet, "scd_provider_api_request_budget.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    reqs = packet.get("max_requests", 0)
    if not isinstance(reqs, int) or isinstance(reqs, bool):
        blocked.append("max_requests must be integer")
    elif reqs <= 0:
        blocked.append("max_requests must be small and positive")
    elif reqs > 3:
        blocked.append("max_requests must be <= 3")
        
    for k in ["max_input_tokens", "max_output_tokens", "max_estimated_cost"]:
        if k not in packet:
            blocked.append(f"{k} missing")
        else:
            val = packet[k]
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                blocked.append(f"{k} must be numeric")
            elif val < 0:
                blocked.append(f"{k} must be >= 0")
            
    return _result(blocked, review, unknown)

def validate_provider_api_gate_readiness_report(packet):
    ok, msg = _schema_ok(packet, "scd_provider_api_gate_readiness_report.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    upstream_states = [
        "provider_live_gate_readiness_state",
        "credential_envelope_state",
        "request_budget_state",
        "provider_allowlist_state"
    ]
    for state_field in upstream_states:
        val = packet.get(state_field)
        if val != PASS:
            blocked.append(f"{state_field} must be PASS")
            
    app_state = packet.get("operator_approval_state")
    if app_state == "APPROVED_FOR_FUTURE_API_GATE_REVIEW":
        pass
    elif app_state == "STALE":
        review.append("stale operator approval")
    else:
        blocked.append("operator_approval_state must be APPROVED_FOR_FUTURE_API_GATE_REVIEW")

    if not packet.get("explicit_api_gate_required"): blocked.append("explicit_api_gate_required must be true")
    if not packet.get("explicit_operator_api_approval_present"): blocked.append("explicit_operator_api_approval_present must be true")

    false_fields = [
        "credential_lookup_allowed",
        "env_read_allowed",
        "api_key_present",
        "credential_value_present",
        "provider_client_constructed",
        "network_allowed",
        "executable",
        "live_ready",
        "provider_ready",
        "public_ready"
    ]
    for f in false_fields:
        if packet.get(f):
            blocked.append(f"{f} must be false")
            
    s = json.dumps(packet).lower()
    unsafe_words = ["execute", "send", "call provider now", "live call", "dispatch", "post", "publish"]
    for w in unsafe_words:
        if w in s:
            blocked.append(f"wording contains unsafe word: {w}")
            
    # Rollup check
    states = []
    sub_state_keys = [
        "provider_live_gate_readiness_state",
        "credential_envelope_state",
        "request_budget_state",
        "provider_allowlist_state"
    ]
    for k in sub_state_keys:
        if k in packet:
            states.append(packet[k])
            
    if app_state == "STALE":
        states.append(REVIEW_REQUIRED)
    elif app_state != "APPROVED_FOR_FUTURE_API_GATE_REVIEW":
        states.append(BLOCKED)
    else:
        states.append(PASS)
        
    if states:
        rolled = _rollup(states)
    else:
        rolled = UNKNOWN
        
    claim = packet.get("validation_state")
    if claim != rolled:
        blocked.append(f"claimed validation_state {claim} != rolled up state {rolled}")

    if claim == PASS and rolled != PASS:
        blocked.append("PASS only allowed if all sub-states are PASS")
        
    if rolled == UNKNOWN: unknown.append("rolled up state is UNKNOWN")
    elif rolled == REVIEW_REQUIRED: review.append("rolled up state is REVIEW_REQUIRED")
    elif rolled == BLOCKED: blocked.append("rolled up state is BLOCKED")

    return _result(blocked, review, unknown)

def validate_provider_api_gate_audit_manifest(packet):
    ok, msg = _schema_ok(packet, "scd_provider_api_gate_audit_manifest.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    refs = packet.get("upstream_lineage_refs")
    if not refs:
        unknown.append("upstream_lineage_refs missing or empty")
        
    if unknown and packet.get("validation_state") == PASS:
        blocked.append("cannot be PASS if refs are missing")

    return _result(blocked, review, unknown)

def build_provider_api_gate_readiness_report(envelope, policy, budget, manifest, live_gate_evidence, operator_api_approval):
    res_env = validate_provider_credential_envelope(envelope)
    res_pol = validate_explicit_api_gate_policy(policy)
    res_bud = validate_provider_api_request_budget(budget)
    res_man = validate_provider_api_gate_audit_manifest(manifest)
    
    blocked, review, unknown = [], [], []
    
    live_gate_state = UNKNOWN
    if not live_gate_evidence:
        unknown.append("live_gate_evidence missing")
    else:
        live_gate_state = live_gate_evidence.get("validation_state", UNKNOWN)
        
    op_api_appr_state = UNKNOWN
    req = False
    present = False
    if not operator_api_approval:
        review.append("operator_api_approval missing")
    else:
        op_api_appr_state = operator_api_approval.get("operator_approval_state", UNKNOWN)
        req = operator_api_approval.get("explicit_api_gate_required", False)
        present = operator_api_approval.get("explicit_operator_api_approval_present", False)
        
        if op_api_appr_state != "APPROVED_FOR_FUTURE_API_GATE_REVIEW":
            if op_api_appr_state == "STALE" or op_api_appr_state == "REVIEW_REQUIRED":
                review.append("operator API approval not approved")
            else:
                blocked.append("operator API approval not approved")
                
    op_mapped = PASS if op_api_appr_state == "APPROVED_FOR_FUTURE_API_GATE_REVIEW" else op_api_appr_state
    if not operator_api_approval:
        op_mapped = REVIEW_REQUIRED
    elif op_mapped not in [PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN]:
        op_mapped = BLOCKED

    states = [res_env["validation_state"], res_pol["validation_state"], res_bud["validation_state"], res_man["validation_state"], live_gate_state, op_mapped]
    
    if blocked: states.append(BLOCKED)
    elif unknown: states.append(UNKNOWN)
    elif review: states.append(REVIEW_REQUIRED)

    rolled = _rollup(states)
    
    reasons = res_env["reasons"] + res_pol["reasons"] + res_bud["reasons"] + res_man["reasons"] + blocked + review + unknown
    reasons = [r for r in list(dict.fromkeys(reasons)) if r != "ok"]
    if not reasons: reasons = ["ok"]
    
    return {
        "schema_version": "1.0",
        "batch_id": envelope.get("batch_id", "unknown"),
        "validation_state": rolled,
        "provider_live_gate_readiness_state": live_gate_state,
        "operator_approval_state": op_api_appr_state,
        "explicit_api_gate_required": req,
        "explicit_operator_api_approval_present": present,
        "credential_envelope_state": res_env["validation_state"],
        "request_budget_state": res_bud["validation_state"],
        "provider_allowlist_state": res_pol["validation_state"],
        "credential_lookup_allowed": False,
        "env_read_allowed": False,
        "api_key_present": False,
        "credential_value_present": False,
        "provider_client_constructed": False,
        "network_allowed": False,
        "executable": False,
        "live_ready": False,
        "provider_ready": False,
        "public_ready": False,
        "reasons": reasons
    }

PROVIDER_API_GATE_CONTRACT_VALIDATORS = {
    "credential_envelope": validate_provider_credential_envelope,
    "explicit_api_gate_policy": validate_explicit_api_gate_policy,
    "request_budget": validate_provider_api_request_budget,
    "readiness_report": validate_provider_api_gate_readiness_report,
    "audit_manifest": validate_provider_api_gate_audit_manifest
}
