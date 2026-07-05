import json
import re
from pathlib import Path
import jsonschema

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "pre_alpha_content_lane_policy_packet.schema.json"

FORBIDDEN_FINANCIAL_PATTERNS = [
    r"\bbuy\b", r"\bsell\b", r"\bhold\b", r"\blong\b", r"\bshort\b", 
    r"\bentry\b", r"\bexit\b", r"\btarget\b", r"position sizing", 
    r"\bsignal\b", r"model says", r"\bexecution\b", r"\bbroker\b", 
    r"order-routing"
]

FORBIDDEN_PRE_ALPHA_CLAIMS = [
    r"\bdqr\b", r"forecast readiness", r"\blineage\b"
]

def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_policy_packet(payload: dict) -> dict:
    schema = load_schema()
    
    try:
        jsonschema.validate(instance=payload, schema=schema)
    except jsonschema.ValidationError as e:
        return {"packet_status": "blocked", "reasons": [f"Schema validation failed: {e.message}"]}

    reasons = []

    # Hard blocked boolean flags
    if payload.get("public_postable"):
        reasons.append("public_postable must be false")
    if payload.get("publish_ready"):
        reasons.append("publish_ready must be false")
    if payload.get("auto_publish"):
        reasons.append("auto_publish must be false")
    if payload.get("auto_approval"):
        reasons.append("auto_approval must be false")
    if payload.get("platform_api_payload_generated"):
        reasons.append("platform_api_payload_generated must be false")
    if payload.get("provider_call_used_by_repo"):
        reasons.append("provider_call_used_by_repo must be false")
    if payload.get("search_call_used_by_repo"):
        reasons.append("search_call_used_by_repo must be false")
    if payload.get("network_call_used_by_repo"):
        reasons.append("network_call_used_by_repo must be false")
    if payload.get("credential_or_env_read_used"):
        reasons.append("credential_or_env_read_used must be false")
    if payload.get("raw_vendor_redistribution_allowed"):
        reasons.append("raw_vendor_redistribution_allowed must be false")
    if payload.get("hidden_missing_proxy_degraded_data"):
        reasons.append("hidden_missing_proxy_degraded_data must be false")

    lane = payload.get("lane")
    claims_artifact_backed = payload.get("claims_artifact_backed")
    source_artifact_ids = payload.get("source_artifact_ids", [])
    text_content = payload.get("text_content", "").lower()

    # Artifact backed rules
    if claims_artifact_backed and not source_artifact_ids:
        reasons.append("Cannot claim artifact-backed status without explicit real artifact references")
    
    # Check for invented IDs
    for a_id in source_artifact_ids:
        if "fake" in a_id.lower() or "mock" in a_id.lower() or "invented" in a_id.lower():
            reasons.append(f"Invented source artifact ID detected: {a_id}")

    if lane == "future_artifact_backed_cc":
        if not claims_artifact_backed or not source_artifact_ids:
            reasons.append("Future artifact-backed lane requires explicit real artifact references and claims_artifact_backed=true")

    if lane == "pre_alpha_general_process":
        for pattern in FORBIDDEN_PRE_ALPHA_CLAIMS:
            if re.search(pattern, text_content):
                reasons.append(f"Forbidden DQR/forecast readiness/lineage claim in pre-alpha lane: {pattern}")

    # Financial / Signal language check
    for pattern in FORBIDDEN_FINANCIAL_PATTERNS:
        if re.search(pattern, text_content):
            reasons.append(f"Forbidden financial/signal language detected: {pattern}")

    if reasons:
        return {
            "packet_status": "blocked",
            "reasons": reasons
        }

    return {
        "packet_status": "pass",
        "reasons": ["Packet passes local-only policy readiness rules."]
    }
