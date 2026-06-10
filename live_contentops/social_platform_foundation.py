import json
import os
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("social_platform_foundation_packet.schema.json")

SUPPORTED_PLATFORMS = [
    "x",
    "linkedin",
    "telegram",
    "threads_manual",
    "substack_newsletter",
    "facebook_page",
    "instagram",
    "tiktok",
]

# Per-platform flags that must never be enabled in this local-only foundation.
FORBIDDEN_TRUE_FLAGS = [
    "live_posting_enabled_now",
    "platform_api_allowed_now",
    "credential_required_now",
    "credential_read_allowed_now",
    "scheduler_allowed_now",
    "scraping_allowed_now",
    "autonomous_reply_or_dm_allowed_now",
    "public_ready_allowed_now",
]

# Per-platform flags that must always be true.
REQUIRED_TRUE_FLAGS = [
    "manual_review_required",
    "not_public_postable",
]

# Map a per-platform forbidden flag to a deterministic error label.
_FORBIDDEN_ERROR = {
    "live_posting_enabled_now": "live_posting_enabled_now_must_be_false",
    "platform_api_allowed_now": "platform_api_allowed_now_must_be_false",
    "credential_required_now": "credential_required_now_must_be_false",
    "credential_read_allowed_now": "credential_read_allowed_now_must_be_false",
    "scheduler_allowed_now": "scheduler_allowed_now_must_be_false",
    "scraping_allowed_now": "scraping_allowed_now_must_be_false",
    "autonomous_reply_or_dm_allowed_now": "autonomous_reply_or_dm_allowed_now_must_be_false",
    "public_ready_allowed_now": "public_ready_allowed_now_must_be_false",
}

_REQUIRED_ERROR = {
    "manual_review_required": "manual_review_required_must_be_true",
    "not_public_postable": "not_public_postable_must_be_true",
}


def validate_social_platform_foundation_packet(packet):
    errors = []

    base_uri = f"file:///{SCHEMAS_DIR.replace(chr(92), '/')}/"
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=PACKET_SCHEMA)

    try:
        jsonschema.validate(instance=packet, schema=PACKET_SCHEMA, resolver=resolver)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if packet.get("runtime_authority"):
        errors.append("runtime_authority_must_be_false")

    # Per-platform control-plane enforcement.
    matrix = packet.get("platform_fit_matrix", [])
    for entry in matrix:
        platform = entry.get("platform", "unknown")
        for flag in FORBIDDEN_TRUE_FLAGS:
            if entry.get(flag) is True:
                errors.append(f"{_FORBIDDEN_ERROR[flag]}:{platform}")
        for flag in REQUIRED_TRUE_FLAGS:
            if entry.get(flag) is not True:
                errors.append(f"{_REQUIRED_ERROR[flag]}:{platform}")

    # Safety policy enforcement.
    safety = packet.get("safety_policy", {})
    if safety.get("no_financial_advice_required") is not True:
        errors.append("missing_safety_disclaimer:no_financial_advice")
    if safety.get("no_signal_language_required") is not True:
        errors.append("missing_safety_disclaimer:no_signal_language")
    if safety.get("source_references_required") is not True:
        errors.append("source_references_must_be_required")

    # Approval policy enforcement.
    approval = packet.get("approval_policy", {})
    if approval.get("manual_review_required") is not True:
        errors.append("approval_manual_review_required_must_be_true")
    if approval.get("auto_approval_allowed_now") is True:
        errors.append("auto_approval_allowed_now_must_be_false")

    # Manual export policy enforcement.
    export = packet.get("manual_export_policy", {})
    if export.get("manual_export_only") is not True:
        errors.append("manual_export_only_must_be_true")
    if export.get("live_dispatch_allowed_now") is True:
        errors.append("live_dispatch_allowed_now_must_be_false")

    # Unsafe secret placeholder scan.
    packet_str = json.dumps(packet)
    unsafe_tokens = [
        "FAKE_SECRET",
        "fake_token_123",
        "Bearer FAKE_TOKEN",
        "api_key=FAKE_KEY",
        "password=FAKE_PASSWORD",
    ]
    for t in unsafe_tokens:
        if t in packet_str:
            errors.append(f"unsafe_secret_detected:{t}")

    # Forbidden trading/signal/execution language scan.
    signal_tokens = [
        "Capital Chronicle alpha says",
        "our model predicts",
        "our signal says",
        "model says",
        "buy",
        "sell",
        "hold",
        "long",
        "short",
        "entry",
        "exit",
        "target price",
        "position sizing",
        "broker",
        "order routing",
        "execution",
        "signal",
        "guaranteed",
    ]
    word_bound_tokens = {"buy", "sell", "hold", "long", "short", "entry", "exit"}

    def scan_for_signals(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                scan_for_signals(v)
        elif isinstance(obj, list):
            for i in obj:
                scan_for_signals(i)
        elif isinstance(obj, str):
            v_lower = obj.lower()
            for st in signal_tokens:
                st_lower = st.lower()
                if st_lower in v_lower:
                    if st in word_bound_tokens:
                        if st_lower in v_lower.split():
                            errors.append(f"unsafe_signal_detected:{st}")
                    else:
                        errors.append(f"unsafe_signal_detected:{st}")

    scan_for_signals(packet)

    # "Capital Chronicle alpha says" requires real approved artifacts.
    linkage = packet.get("seo_newsletter_policy_linkage", {})
    if "Capital Chronicle alpha says" in packet_str:
        if linkage.get("real_approved_artifacts_present") is not True:
            errors.append("alpha_claim_without_real_artifact")

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    valid = len(errors) == 0
    return {"valid": valid, "errors": sorted(set(errors))}


def summary():
    return {
        "packet_status": "pass",
        "platform_count": len(SUPPORTED_PLATFORMS),
        "live_posting_enabled_count": 0,
        "platform_api_enabled_count": 0,
        "credential_read_enabled_count": 0,
        "scheduler_enabled_count": 0,
        "scraping_enabled_count": 0,
        "autonomous_reply_dm_enabled_count": 0,
        "public_ready_allowed_count": 0,
        "manual_review_required_all": True,
        "not_public_postable_all": True,
        "unsafe_language_count": 0,
        "provider_call_used_by_repo": False,
        "search_call_used_by_repo": False,
        "network_call_used_by_repo": False,
        "platform_action_used_by_repo": False,
        "credential_or_env_read_used": False,
        "newsletter_send_enabled": False,
        "cms_integration_enabled": False,
    }


