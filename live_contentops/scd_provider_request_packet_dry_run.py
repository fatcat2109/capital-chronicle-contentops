"""Provider request packet dry-run contract (SCD, 0174BF)."""
import json
from live_contentops.scd_domain_model import PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN, _schema_ok, _result
from live_contentops.scd_canonical_draft_lifecycle import _common_safety_blocks

def _rollup(states):
    if BLOCKED in states: return BLOCKED
    if UNKNOWN in states: return UNKNOWN
    if REVIEW_REQUIRED in states: return REVIEW_REQUIRED
    return PASS

def validate_provider_request_payload_redaction(packet):
    ok, msg = _schema_ok(packet, "scd_provider_request_payload_redaction.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    return _result(blocked, review, unknown)

def validate_provider_request_packet_budget_binding(packet):
    ok, msg = _schema_ok(packet, "scd_provider_request_packet_budget_binding.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    return _result(blocked, review, unknown)

def validate_provider_request_packet_audit_manifest(packet):
    ok, msg = _schema_ok(packet, "scd_provider_request_packet_audit_manifest.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    return _result(blocked, review, unknown)

def validate_provider_request_packet_dry_run(packet):
    ok, msg = _schema_ok(packet, "scd_provider_request_packet_dry_run.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)
    
    pass_fields = [
        "provider_api_gate_readiness_state",
        "credential_envelope_state",
        "request_budget_state",
        "provider_allowlist_state",
        "redaction_proof_state",
        "budget_binding_state"
    ]
    for f in pass_fields:
        if packet.get(f) != PASS:
            blocked.append(f"{f} must be PASS")
            
    if packet.get("explicit_operator_api_approval_present") is not True:
        blocked.append("explicit_operator_api_approval_present must be true")
        
    if packet.get("request_packet_mode") != "DRY_RUN_ONLY":
        blocked.append("request_packet_mode must be DRY_RUN_ONLY")
        
    false_fields = [
        "executable",
        "network_allowed",
        "provider_client_constructed",
        "env_read_allowed",
        "credential_lookup_allowed",
        "api_key_present",
        "credential_value_present",
        "provider_ready",
        "live_ready",
        "public_ready"
    ]
    for f in false_fields:
        if packet.get(f):
            blocked.append(f"{f} must be false")
            
    refs = ["prompt_pack_ref", "canonical_draft_ref", "budget_ref", "credential_envelope_ref", "audit_manifest_ref"]
    for r in refs:
        if not packet.get(r):
            unknown.append(f"{r} missing")

    s = json.dumps(packet).lower()
    unsafe_words = ["execute", "send", "call provider now", "live call", "dispatch", "post", "publish"]
    for w in unsafe_words:
        if w in s:
            blocked.append(f"wording contains unsafe word: {w}")
            
    if "http://" in s or "https://" in s:
        blocked.append("real URL present")
    if "authorization" in s:
        blocked.append("authorization header present")
    if "bearer " in s:
        blocked.append("bearer token present")
    if "sk-" in s or "token=" in s:
        blocked.append("raw api key present")
        
    states = []
    for f in pass_fields:
        if f in packet:
            states.append(packet[f])
            
    if blocked: states.append(BLOCKED)
    elif unknown: states.append(UNKNOWN)
    elif review: states.append(REVIEW_REQUIRED)
    
    rolled = _rollup(states)
    claim = packet.get("validation_state")
    if claim != rolled:
        blocked.append(f"claim {claim} != rolled {rolled}")
        
    return _result(blocked, review, unknown)

def build_provider_request_packet_dry_run(api_gate_report, prompt_pack_ref, canonical_draft_ref, budget_ref, credential_envelope_ref, manifest_ref):
    if not api_gate_report:
        api_gate_report = {}
        
    gate_state = api_gate_report.get("validation_state", UNKNOWN)
    if gate_state != PASS:
        rolled = BLOCKED if gate_state in [BLOCKED, REVIEW_REQUIRED] else UNKNOWN
        return {"schema_version": "1.0", "batch_id": "unknown", "validation_state": rolled, "reasons": ["api_gate_report not PASS"]}
        
    packet = {
        "schema_version": "1.0",
        "batch_id": api_gate_report.get("batch_id", "unknown"),
        "provider_api_gate_readiness_state": PASS,
        "credential_envelope_state": PASS,
        "request_budget_state": PASS,
        "provider_allowlist_state": PASS,
        "explicit_operator_api_approval_present": True,
        "request_packet_mode": "DRY_RUN_ONLY",
        "executable": False,
        "network_allowed": False,
        "provider_client_constructed": False,
        "env_read_allowed": False,
        "credential_lookup_allowed": False,
        "api_key_present": False,
        "credential_value_present": False,
        "provider_ready": False,
        "live_ready": False,
        "public_ready": False,
        "symbolic_provider_name": "OPENAI",
        "symbolic_endpoint_family": "CHAT_COMPLETION",
        "prompt_pack_ref": prompt_pack_ref,
        "canonical_draft_ref": canonical_draft_ref,
        "budget_ref": budget_ref,
        "credential_envelope_ref": credential_envelope_ref,
        "audit_manifest_ref": manifest_ref,
        "redaction_proof_state": PASS,
        "budget_binding_state": PASS,
        "validation_state": PASS
    }
    
    res = validate_provider_request_packet_dry_run(packet)
    packet["validation_state"] = res["validation_state"]
    packet["reasons"] = res["reasons"]
    return packet

PROVIDER_REQUEST_PACKET_DRY_RUN_VALIDATORS = {
    "dry_run": validate_provider_request_packet_dry_run,
    "payload_redaction": validate_provider_request_payload_redaction,
    "budget_binding": validate_provider_request_packet_budget_binding,
    "audit_manifest": validate_provider_request_packet_audit_manifest
}
