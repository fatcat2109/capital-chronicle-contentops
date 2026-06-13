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

    if packet.get("redaction_proof_state") != PASS:
        blocked.append("redaction_proof_state must be PASS")

    return _result(blocked, review, unknown)

def validate_provider_request_packet_budget_binding(packet):
    ok, msg = _schema_ok(packet, "scd_provider_request_packet_budget_binding.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)

    if packet.get("budget_binding_state") != PASS:
        blocked.append("budget_binding_state must be PASS")

    return _result(blocked, review, unknown)

def validate_provider_request_packet_audit_manifest(packet):
    ok, msg = _schema_ok(packet, "scd_provider_request_packet_audit_manifest.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)

    refs = ["prompt_pack_ref", "canonical_draft_ref", "budget_ref", "credential_envelope_ref", "audit_manifest_ref"]
    for r in refs:
        if not packet.get(r):
            unknown.append(f"{r} missing")

    if unknown and packet.get("validation_state") == PASS:
        blocked.append("claimed PASS but refs are missing")

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
        val = packet.get(f)
        if val == BLOCKED:
            blocked.append(f"{f} is BLOCKED")
        elif val == REVIEW_REQUIRED:
            review.append(f"{f} is REVIEW_REQUIRED")
        elif val != PASS:
            unknown.append(f"{f} missing or UNKNOWN")

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

    if packet.get("symbolic_provider_name") == "UNKNOWN_PROVIDER":
        unknown.append("symbolic_provider_name is UNKNOWN_PROVIDER")
    if packet.get("symbolic_endpoint_family") == "UNKNOWN_ENDPOINT":
        unknown.append("symbolic_endpoint_family is UNKNOWN_ENDPOINT")

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

def build_provider_request_packet_dry_run(
    api_gate_report,
    credential_envelope_evidence,
    request_budget_evidence,
    provider_allowlist_evidence,
    redaction_proof_evidence,
    budget_binding_evidence,
    provider_symbol_evidence,
    endpoint_family_evidence,
    prompt_pack_ref,
    canonical_draft_ref,
    budget_ref,
    credential_envelope_ref,
    manifest_ref
):
    blocked, review, unknown = [], [], []

    def _get_state(ev, key="validation_state"):
        if not ev:
            return UNKNOWN
        return ev.get(key, UNKNOWN)

    api_gate_state = _get_state(api_gate_report)
    cred_env_state = _get_state(credential_envelope_evidence)
    req_bud_state = _get_state(request_budget_evidence)
    allowlist_state = _get_state(provider_allowlist_evidence)
    redact_state = _get_state(redaction_proof_evidence)
    bind_state = _get_state(budget_binding_evidence)

    # Operator API approval is checked from either explicit evidence (if passed) or api_gate_report if it holds it.
    op_present = False
    if api_gate_report:
        op_present = api_gate_report.get("explicit_operator_api_approval_present", False)

    states = [api_gate_state, cred_env_state, req_bud_state, allowlist_state, redact_state, bind_state]

    sym_name = "UNKNOWN_PROVIDER"
    if provider_symbol_evidence:
        sym_name = provider_symbol_evidence.get("symbolic_provider_name", sym_name)
        if "symbolic_provider_name" not in provider_symbol_evidence:
            unknown.append("symbolic_provider_name missing in evidence")
            states.append(UNKNOWN)
    else:
        unknown.append("provider_symbol_evidence missing")
        states.append(UNKNOWN)

    sym_ep = "UNKNOWN_ENDPOINT"
    if endpoint_family_evidence:
        sym_ep = endpoint_family_evidence.get("symbolic_endpoint_family", sym_ep)
        if "symbolic_endpoint_family" not in endpoint_family_evidence:
            unknown.append("symbolic_endpoint_family missing in evidence")
            states.append(UNKNOWN)
    else:
        unknown.append("endpoint_family_evidence missing")
        states.append(UNKNOWN)

    if not op_present:
        unknown.append("explicit_operator_api_approval_present missing")
        states.append(UNKNOWN)

    # Check if refs missing
    if not prompt_pack_ref: unknown.append("prompt_pack_ref missing")
    if not canonical_draft_ref: unknown.append("canonical_draft_ref missing")
    if not budget_ref: unknown.append("budget_ref missing")
    if not credential_envelope_ref: unknown.append("credential_envelope_ref missing")
    if not manifest_ref: unknown.append("manifest_ref missing")

    if unknown: states.append(UNKNOWN)

    rolled = _rollup(states)

    packet = {
        "schema_version": "1.0",
        "batch_id": (api_gate_report or {}).get("batch_id", "unknown"),
        "provider_api_gate_readiness_state": api_gate_state,
        "credential_envelope_state": cred_env_state,
        "request_budget_state": req_bud_state,
        "provider_allowlist_state": allowlist_state,
        "explicit_operator_api_approval_present": op_present,
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
        "symbolic_provider_name": sym_name,
        "symbolic_endpoint_family": sym_ep,
        "prompt_pack_ref": prompt_pack_ref,
        "canonical_draft_ref": canonical_draft_ref,
        "budget_ref": budget_ref,
        "credential_envelope_ref": credential_envelope_ref,
        "audit_manifest_ref": manifest_ref,
        "redaction_proof_state": redact_state,
        "budget_binding_state": bind_state,
        "validation_state": rolled
    }

    res = validate_provider_request_packet_dry_run(packet)
    if res["validation_state"] != PASS:
        packet["validation_state"] = res["validation_state"]
    # The packet validation state was set to 'rolled' which we trust, but let's take reasons from both
    reasons = res["reasons"] + blocked + review + unknown
    reasons = [r for r in list(dict.fromkeys(reasons)) if r != "ok"]
    if not reasons: reasons = ["ok"]
    packet["reasons"] = reasons
    return packet

PROVIDER_REQUEST_PACKET_DRY_RUN_VALIDATORS = {
    "dry_run": validate_provider_request_packet_dry_run,
    "payload_redaction": validate_provider_request_payload_redaction,
    "budget_binding": validate_provider_request_packet_budget_binding,
    "audit_manifest": validate_provider_request_packet_audit_manifest
}
