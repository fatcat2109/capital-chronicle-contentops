import json
import os
import jsonschema
import re

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas", "llm_assisted_draft_review_packet.schema.json")

def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_review_packet(packet):
    schema = load_schema()
    try:
        jsonschema.validate(instance=packet, schema=schema)
    except jsonschema.ValidationError as e:
        return {
            "valid": False,
            "errors": [f"Schema validation failed: {e.message}"],
            "packet_status": "blocked",
            "blocked_reasons": [f"Schema validation failed: {e.message}"]
        }

    errors = []
    
    # Strict Operator Flags
    if not packet.get("operator_supplied"):
        errors.append("operator_must_supply_draft")
    if packet.get("repo_llm_provider_call_used"):
        errors.append("repo_must_not_call_llm")

    # Safety Review Pins
    sr = packet.get("safety_review", {})
    if not sr.get("manual_review_required"): errors.append("safety_flag_must_be_true:manual_review_required")
    if not sr.get("not_public_postable"): errors.append("safety_flag_must_be_true:not_public_postable")
    if not sr.get("no_financial_advice"): errors.append("safety_flag_must_be_true:no_financial_advice")
    if not sr.get("no_signal_language"): errors.append("safety_flag_must_be_true:no_signal_language")
    if not sr.get("no_execution_language"): errors.append("safety_flag_must_be_true:no_execution_language")
    
    if sr.get("public_postable"): errors.append("safety_flag_must_be_false:public_postable")
    if sr.get("publish_ready"): errors.append("safety_flag_must_be_false:publish_ready")
    if sr.get("auto_publish"): errors.append("safety_flag_must_be_false:auto_publish")
    if sr.get("auto_approval"): errors.append("safety_flag_must_be_false:auto_approval")
    if sr.get("repo_llm_provider_call_used"): errors.append("safety_flag_must_be_false:repo_llm_provider_call_used")
    if sr.get("provider_call_used_by_repo"): errors.append("safety_flag_must_be_false:provider_call_used_by_repo")
    if sr.get("search_call_used_by_repo"): errors.append("safety_flag_must_be_false:search_call_used_by_repo")
    if sr.get("network_call_used_by_repo"): errors.append("safety_flag_must_be_false:network_call_used_by_repo")
    if sr.get("platform_action_used_by_repo"): errors.append("safety_flag_must_be_false:platform_action_used_by_repo")
    if sr.get("credential_or_env_read_used"): errors.append("safety_flag_must_be_false:credential_or_env_read_used")
    if sr.get("platform_api_payload_generated"): errors.append("safety_flag_must_be_false:platform_api_payload_generated")

    # Source linkage
    declared_sources = set(packet.get("source_references_used", []))
    
    # Text Analysis
    draft_text = packet.get("draft_text", "").lower()
    
    forbidden_signals = [
        "\\bbuy\\b", "\\bsell\\b", "\\bhold\\b", "\\blong\\b", "\\bshort\\b",
        "\\bentry\\b", "\\bexit\\b", "\\btarget\\b", "position sizing", 
        "\\bbroker\\b", "order routing", "\\bexecution\\b", "\\bsignal\\b", "model says"
    ]
    for sig in forbidden_signals:
        if re.search(sig, draft_text):
            errors.append(f"forbidden_signal_in_draft:{sig.replace(chr(92)+'b', '')}")

    alpha_implications = [
        "capital chronicle alpha says", "artifact_id", "source_artifact_id",
        "dqr_status", "forecast_readiness_status", "our model predicts"
    ]
    for alpha in alpha_implications:
        if alpha in draft_text:
            errors.append(f"forbidden_alpha_implication_in_draft:{alpha}")

    # Claims analysis
    for claim in packet.get("claims", []):
        ctype = claim.get("claim_type")
        crisk = claim.get("claim_risk")
        ctext = claim.get("claim_text", "").lower()

        if ctype == "forbidden_claim":
            errors.append(f"claim_type_forbidden:{claim.get('claim_id')}")
        if crisk == "blocked":
            errors.append(f"claim_risk_blocked:{claim.get('claim_id')}")

        if ctype in ["cited_factual_claim", "current_factual_claim"]:
            if not claim.get("has_citation") or not claim.get("source_ids"):
                errors.append(f"claim_missing_citation:{claim.get('claim_id')}")
            for sid in claim.get("source_ids", []):
                if sid not in declared_sources:
                    errors.append(f"claim_source_not_in_grounded_brief:{claim.get('claim_id')}:{sid}")

        for sig in forbidden_signals:
            if re.search(sig, ctext):
                errors.append(f"forbidden_signal_in_claim:{claim.get('claim_id')}")

        for alpha in alpha_implications:
            if alpha in ctext:
                errors.append(f"forbidden_alpha_implication_in_claim:{claim.get('claim_id')}")

    if errors:
        return {
            "valid": False,
            "errors": errors,
            "packet_status": "blocked",
            "blocked_reasons": errors
        }

    return {
        "valid": True,
        "errors": [],
        "packet_status": "pass",
        "blocked_reasons": []
    }

def validate_review_packet_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        packet = json.load(f)
    return validate_review_packet(packet)
