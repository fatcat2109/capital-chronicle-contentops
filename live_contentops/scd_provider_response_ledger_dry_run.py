"""Provider response ledger dry-run contract (SCD, 0174BH)."""
import json
from live_contentops.scd_domain_model import PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN, _schema_ok, _result
from live_contentops.scd_canonical_draft_lifecycle import _common_safety_blocks

def _rollup(states):
    if BLOCKED in states: return BLOCKED
    if UNKNOWN in states: return UNKNOWN
    if REVIEW_REQUIRED in states: return REVIEW_REQUIRED
    return PASS

def _scan_for_hostile_words(packet, blocked):
    s = json.dumps(packet).lower()
    
    # We must not trigger on the schema keys themselves.
    s_scan = s.replace("api_key_present", "").replace("secret_material_detected", "").replace("provider_client_constructed", "")

    unsafe_words = [
        "execute", "send", "call provider now", "live call", 
        "dispatch", "post", "publish", "go live"
    ]
    for w in unsafe_words:
        if w in s_scan:
            blocked.append(f"wording contains unsafe word: {w}")
    
    if "http://" in s_scan or "https://" in s_scan:
        blocked.append("real url present")
    if "authorization" in s_scan:
        blocked.append("authorization header present")
    if "bearer " in s_scan:
        blocked.append("bearer token present")
    if "sk-" in s_scan or "token=" in s_scan:
        blocked.append("raw api key or token present")
    if "api_key" in s_scan:
        blocked.append("api key reference present")
    if "secret" in s_scan:
        blocked.append("secret reference present")
    if "webhook" in s_scan:
        blocked.append("webhook reference present")
    if "provider client" in s_scan:
        blocked.append("provider client reference present")

def _scan_false_flags(packet, blocked):
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
        "public_ready",
        "generated_content_public_ready"
    ]
    for f in false_fields:
        if packet.get(f):
            blocked.append(f"{f} must be false")

def validate_provider_response_receipt_dry_run(packet):
    ok, msg = _schema_ok(packet, "scd_provider_response_receipt_dry_run.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)

    if packet.get("response_receipt_mode") != "DRY_RUN_RESPONSE_ARTIFACT_ONLY":
        blocked.append("response_receipt_mode must be DRY_RUN_RESPONSE_ARTIFACT_ONLY")
    
    if packet.get("local_artifact_only") is not True:
        blocked.append("local_artifact_only must be true")

    if not packet.get("request_packet_ref"):
        unknown.append("request_packet_ref missing")
    if not packet.get("response_artifact_ref"):
        unknown.append("response_artifact_ref missing")

    _scan_false_flags(packet, blocked)
    _scan_for_hostile_words(packet, blocked)

    auth_state = packet.get("response_content_authority_state")
    if auth_state in ["CURRENT_TRUTH", "MARKET_TRUTH", "AUTHORITATIVE", "PUBLICATION_READY"]:
        blocked.append(f"response_content_authority_state cannot be {auth_state}")

    if unknown and packet.get("validation_state") == PASS:
        blocked.append("claimed PASS but refs are missing")

    return _result(blocked, review, unknown)

def validate_provider_response_payload_redaction(packet):
    ok, msg = _schema_ok(packet, "scd_provider_response_payload_redaction.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)

    if not packet.get("response_artifact_ref"):
        unknown.append("response_artifact_ref missing")
    if not packet.get("response_redaction_ref"):
        unknown.append("response_redaction_ref missing")

    if packet.get("raw_response_redistribution_allowed"):
        blocked.append("raw_response_redistribution_allowed must be false")
    
    if packet.get("raw_provider_payload_present"):
        if packet.get("validation_state") == PASS:
            blocked.append("raw_provider_payload_present true cannot PASS")
        # We don't block inherently if it's true, but we don't allow it to PASS.

    if packet.get("secret_material_detected"):
        blocked.append("secret_material_detected must be false")
    if packet.get("auth_header_detected"):
        blocked.append("auth_header_detected must be false")
    if packet.get("endpoint_url_detected"):
        blocked.append("endpoint_url_detected must be false")
    if packet.get("provider_token_detected"):
        blocked.append("provider_token_detected must be false")

    if packet.get("public_ready"):
        blocked.append("public_ready must be false")

    if not packet.get("redacted_response_artifact_present"):
        if packet.get("validation_state") == PASS:
            blocked.append("redacted_response_artifact_present must be true for PASS")

    if unknown and packet.get("validation_state") == PASS:
        blocked.append("claimed PASS but refs are missing")

    _scan_for_hostile_words(packet, blocked)

    return _result(blocked, review, unknown)

def validate_provider_response_audit_manifest(packet):
    ok, msg = _schema_ok(packet, "scd_provider_response_audit_manifest.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)

    upstream = packet.get("upstream_lineage_refs", [])
    if not upstream:
        unknown.append("upstream_lineage_refs missing or empty")

    refs = [
        "request_packet_ref",
        "response_artifact_ref",
        "response_redaction_ref",
        "response_ledger_ref"
    ]
    for r in refs:
        if not packet.get(r):
            unknown.append(f"{r} missing")

    if unknown and packet.get("validation_state") == PASS:
        blocked.append("claimed PASS but refs are missing")

    _scan_for_hostile_words(packet, blocked)

    return _result(blocked, review, unknown)

def validate_provider_response_ledger_entry(packet):
    ok, msg = _schema_ok(packet, "scd_provider_response_ledger_entry.schema.json")
    if not ok: return _result([f"schema: {msg}"], [], [])
    blocked, review, unknown = [], [], []
    blocked += _common_safety_blocks(packet)

    if packet.get("response_ledger_mode") != "DRY_RUN_LEDGER_ONLY":
        blocked.append("response_ledger_mode must be DRY_RUN_LEDGER_ONLY")
    
    if packet.get("local_artifact_only") is not True:
        blocked.append("local_artifact_only must be true")

    if packet.get("symbolic_provider_name") == "UNKNOWN_PROVIDER":
        blocked.append("symbolic_provider_name cannot be UNKNOWN_PROVIDER")
    if packet.get("symbolic_endpoint_family") == "UNKNOWN_ENDPOINT":
        blocked.append("symbolic_endpoint_family cannot be UNKNOWN_ENDPOINT")

    _scan_false_flags(packet, blocked)
    _scan_for_hostile_words(packet, blocked)

    auth_state = packet.get("response_content_authority_state")
    if auth_state in ["CURRENT_TRUTH", "MARKET_TRUTH", "AUTHORITATIVE", "PUBLICATION_READY"]:
        blocked.append(f"response_content_authority_state cannot be {auth_state}")

    refs = [
        "request_packet_ref",
        "prompt_pack_ref",
        "canonical_draft_ref",
        "budget_ref",
        "credential_envelope_ref",
        "request_audit_manifest_ref",
        "response_artifact_ref",
        "response_redaction_ref",
        "response_audit_manifest_ref"
    ]
    for r in refs:
        if not packet.get(r):
            unknown.append(f"{r} missing")

    states = []
    sub_keys = [
        "provider_request_packet_state",
        "response_receipt_state",
        "response_redaction_state",
        "response_audit_manifest_state"
    ]
    for k in sub_keys:
        val = packet.get(k)
        if val:
            states.append(val)
            if val == BLOCKED:
                blocked.append(f"{k} is BLOCKED")
            elif val == UNKNOWN:
                unknown.append(f"{k} is UNKNOWN")
            elif val == REVIEW_REQUIRED:
                review.append(f"{k} is REVIEW_REQUIRED")
        else:
            unknown.append(f"{k} missing")
            states.append(UNKNOWN)

    rolled = _rollup(states)
    claim = packet.get("validation_state")
    
    if claim != rolled:
        blocked.append(f"claimed {claim} != rolled {rolled}")

    if unknown and packet.get("validation_state") == PASS:
        blocked.append("claimed PASS but refs are missing")

    if claim == PASS and rolled != PASS:
        blocked.append("PASS only allowed if all sub-states are PASS")

    return _result(blocked, review, unknown)

def build_provider_response_ledger_entry(
    request_packet,
    response_receipt,
    response_redaction,
    response_audit_manifest,
    request_packet_ref,
    prompt_pack_ref,
    canonical_draft_ref,
    budget_ref,
    credential_envelope_ref,
    request_audit_manifest_ref,
    response_artifact_ref,
    response_redaction_ref,
    response_audit_manifest_ref
):
    blocked, review, unknown = [], [], []

    def _get_state(ev, key="validation_state"):
        if not ev:
            return UNKNOWN
        return ev.get(key, UNKNOWN)

    req_state = _get_state(request_packet)
    rec_state = _get_state(response_receipt)
    red_state = _get_state(response_redaction)
    aud_state = _get_state(response_audit_manifest)

    states = [req_state, rec_state, red_state, aud_state]

    if not request_packet:
        unknown.append("request_packet evidence missing")
    if not response_receipt:
        unknown.append("response_receipt evidence missing")
    if not response_redaction:
        unknown.append("response_redaction evidence missing")
    if not response_audit_manifest:
        unknown.append("response_audit_manifest evidence missing")

    sym_name = "UNKNOWN_PROVIDER"
    sym_ep = "UNKNOWN_ENDPOINT"
    if request_packet:
        sym_name = request_packet.get("symbolic_provider_name", "UNKNOWN_PROVIDER")
        sym_ep = request_packet.get("symbolic_endpoint_family", "UNKNOWN_ENDPOINT")
    
    if sym_name == "UNKNOWN_PROVIDER":
        unknown.append("symbolic_provider_name is UNKNOWN_PROVIDER")
        states.append(UNKNOWN)
    if sym_ep == "UNKNOWN_ENDPOINT":
        unknown.append("symbolic_endpoint_family is UNKNOWN_ENDPOINT")
        states.append(UNKNOWN)

    if not request_packet_ref:
        unknown.append("request_packet_ref missing")
        states.append(UNKNOWN)

    rolled = _rollup(states)

    packet = {
        "schema_version": "1.0",
        "batch_id": (request_packet or {}).get("batch_id", "unknown"),
        "validation_state": rolled,
        "provider_request_packet_state": req_state,
        "response_receipt_state": rec_state,
        "response_redaction_state": red_state,
        "response_audit_manifest_state": aud_state,
        "request_packet_ref": request_packet_ref,
        "prompt_pack_ref": prompt_pack_ref,
        "canonical_draft_ref": canonical_draft_ref,
        "budget_ref": budget_ref,
        "credential_envelope_ref": credential_envelope_ref,
        "request_audit_manifest_ref": request_audit_manifest_ref,
        "response_artifact_ref": response_artifact_ref,
        "response_redaction_ref": response_redaction_ref,
        "response_audit_manifest_ref": response_audit_manifest_ref,
        "symbolic_provider_name": sym_name,
        "symbolic_endpoint_family": sym_ep,
        "response_ledger_mode": "DRY_RUN_LEDGER_ONLY",
        "local_artifact_only": True,
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
        "generated_content_public_ready": False,
        "response_content_authority_state": "DRAFT_REVIEW_ONLY",
        "reasons": ["ok"]
    }

    res = validate_provider_response_ledger_entry(packet)
    if res["validation_state"] != PASS:
        packet["validation_state"] = res["validation_state"]
    
    reasons = res["reasons"] + blocked + review + unknown
    reasons = [r for r in list(dict.fromkeys(reasons)) if r != "ok"]
    if not reasons:
        reasons = ["ok"]
    packet["reasons"] = reasons

    return packet

PROVIDER_RESPONSE_LEDGER_DRY_RUN_VALIDATORS = {
    "receipt": validate_provider_response_receipt_dry_run,
    "payload_redaction": validate_provider_response_payload_redaction,
    "ledger_entry": validate_provider_response_ledger_entry,
    "audit_manifest": validate_provider_response_audit_manifest,
}
