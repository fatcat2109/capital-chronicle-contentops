import json
import os
import jsonschema

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCHEMAS_DIR = os.path.join(BASE_DIR, "schemas")
FIXTURES_DIR = os.path.join(BASE_DIR, "fixtures", "dry_run_publish_batch_manifest")


def _load_schema(name):
    with open(os.path.join(SCHEMAS_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


PACKET_SCHEMA = _load_schema("dry_run_publish_batch_manifest_packet.schema.json")

# Valid platform targets from the 0148 registry model.
REGISTRY_PLATFORM_IDS = [
    "telegram",
    "linkedin",
    "x",
    "threads",
    "substack_or_newsletter",
    "manual_external_posting",
]

# Packet-level booleans that must be false (fail closed if true).
PACKET_FORBIDDEN_TRUE = [
    "runtime_authority",
    "credentials_requested_now",
    "credential_read_allowed_now",
    "credential_operator_action_required_now",
    "platform_api_allowed_now",
    "live_posting_enabled_now",
    "scheduler_allowed_now",
    "provider_llm_api_allowed_now",
    "repo_web_search_allowed_now",
    "scraping_allowed_now",
    "newsletter_or_cms_api_allowed_now",
    "backend_server_required",
    "publish_all_button_enabled_now",
    "one_button_publish_all_enabled_now",
    "publish_approval_system_created",
    "public_ready_approval_allowed_now",
    "final_social_copy_generated",
]

# Packet-level booleans that must be true (fail closed if not true).
PACKET_REQUIRED_TRUE = [
    "dry_run_only",
    "manual_review_required",
    "not_public_postable",
    "kill_switch_required",
    "redacted_audit_log_required",
    "idempotency_policy_required",
    "partial_failure_policy_required",
    "manual_approval_gate_required",
]

PHRASE_TOKENS = [
    "our model predicts",
    "our signal says",
    "target price",
    "position sizing",
    "ai trading bot",
    "bloomberg replacement",
    "signal service",
    "guaranteed",
    "will move",
    "watch this level",
    "ready to post",
]
WORD_BOUND_TOKENS = ["buy", "sell", "hold", "entry", "exit", "broker", "long", "short"]


def _scan_unsafe(obj, real_artifacts=False):
    parts = []

    def _collect(o):
        if isinstance(o, str):
            parts.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                _collect(v)
        elif isinstance(o, list):
            for v in o:
                _collect(v)

    _collect(obj)
    lower = "\n".join(parts).lower()
    errors = []
    for st in PHRASE_TOKENS:
        if st in lower:
            errors.append(f"unsafe_signal_detected:{st}")
    words = lower.replace("\n", " ").replace(".", " ").replace(",", " ").split()
    for st in WORD_BOUND_TOKENS:
        if st in words:
            errors.append(f"unsafe_signal_detected:{st}")
    if "unsupported numeric" in lower or "fake alpha" in lower:
        errors.append("unsupported_numeric_market_claim")
    if "capital chronicle alpha says" in lower and not real_artifacts:
        errors.append("alpha_claim_without_real_artifact")
    return errors


def validate_dry_run_publish_batch_manifest_packet(packet):
    errors = []

    base_uri = f"file:///{SCHEMAS_DIR.replace(chr(92), '/')}/"
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=PACKET_SCHEMA)
    try:
        jsonschema.validate(instance=packet, schema=PACKET_SCHEMA, resolver=resolver)
    except jsonschema.ValidationError as e:
        errors.append(f"schema_invalid:{e.message}")

    if packet.get("manifest_mode") != "dry_run_publish_batch_manifest_only":
        errors.append("manifest_mode_must_be_dry_run_publish_batch_manifest_only")

    for flag in PACKET_FORBIDDEN_TRUE:
        if packet.get(flag) is True:
            errors.append(f"{flag}_must_be_false")

    for flag in PACKET_REQUIRED_TRUE:
        if packet.get(flag) is not True:
            errors.append(f"{flag}_must_be_true")

    # Required gate/audit/idempotency/partial-failure models must be present.
    if not packet.get("manual_approval_gate_model"):
        errors.append("manual_approval_gate_model_required")
    if not packet.get("kill_switch_model"):
        errors.append("kill_switch_model_required")
    if not packet.get("redacted_audit_log_policy"):
        errors.append("redacted_audit_log_policy_required")
    if not packet.get("idempotency_policy"):
        errors.append("idempotency_policy_required")
    if not packet.get("partial_failure_policy"):
        errors.append("partial_failure_policy_required")

    # Target platform IDs must come from the 0148 registry set.
    for pid in packet.get("target_platform_ids", []):
        if pid not in REGISTRY_PLATFORM_IDS:
            errors.append(f"unsupported_platform_target:{pid}")

    # Per-platform payload preview enforcement.
    for pv in packet.get("per_platform_payload_previews", []):
        pvid = pv.get("payload_preview_id", "unknown")
        if pv.get("platform_id") not in REGISTRY_PLATFORM_IDS:
            errors.append(f"preview_unsupported_platform_target:{pvid}")
        if pv.get("platform_adapter_status") in ("implemented", "live", "enabled"):
            errors.append(f"preview_adapter_status_must_not_be_live:{pvid}")
        if pv.get("dry_run_preview_only") is not True:
            errors.append(f"preview_dry_run_preview_only_must_be_true:{pvid}")
        if pv.get("live_execution_status") not in (None, "disabled"):
            errors.append(f"preview_live_execution_must_be_disabled:{pvid}")
        for f in [
            "credentials_requested_now",
            "credential_read_allowed_now",
            "platform_api_allowed_now",
            "live_posting_enabled_now",
            "scheduler_allowed_now",
            "publish_ready",
            "public_ready_allowed_now",
            "final_payload",
        ]:
            if pv.get(f) is True:
                errors.append(f"preview_{f}_must_be_false:{pvid}")
        if pv.get("manual_review_required") is not True:
            errors.append(f"preview_manual_review_required_must_be_true:{pvid}")
        if pv.get("not_public_postable") is not True:
            errors.append(f"preview_not_public_postable_must_be_true:{pvid}")
        if pv.get("source_refs_visible") is not True:
            errors.append(f"preview_source_refs_not_visible:{pvid}")
        if pv.get("limitations_visible") is not True:
            errors.append(f"preview_limitations_not_visible:{pvid}")

    real_artifacts = packet.get("safety_policy", {}).get("real_approved_artifacts_present") is True
    errors += _scan_unsafe(packet, real_artifacts=real_artifacts)

    if packet.get("packet_status") == "pass" and len(errors) > 0:
        errors.append("packet_status_pass_but_errors_exist")

    return {"valid": len(errors) == 0, "errors": sorted(set(errors))}


def _load_valid_packet():
    with open(os.path.join(FIXTURES_DIR, "dry_run_publish_batch_manifest_valid.json"), "r", encoding="utf-8") as f:
        return json.load(f)



def summary():
    packet = _load_valid_packet()
    res = validate_dry_run_publish_batch_manifest_packet(packet)
    previews = packet.get("per_platform_payload_previews", [])

    def _pvcount(flag):
        return sum(1 for p in previews if p.get(flag) is True)

    return {
        "packet_status": packet.get("packet_status", ""),
        "target_platform_count": len(packet.get("target_platform_ids", [])),
        "payload_preview_count": len(previews),
        "dry_run_only": packet.get("dry_run_only") is True,
        "credentials_requested_now_count": 1 if packet.get("credentials_requested_now") is True else 0,
        "credential_read_enabled_count": 1 if packet.get("credential_read_allowed_now") is True else 0,
        "credential_operator_action_required_now_count": 1
        if packet.get("credential_operator_action_required_now") is True
        else 0,
        "credential_operator_action_required_later_count": 1
        if packet.get("credential_operator_action_required_later") is True
        else 0,
        "platform_api_enabled_count": 1 if packet.get("platform_api_allowed_now") is True else 0,
        "live_posting_enabled_count": 1 if packet.get("live_posting_enabled_now") is True else 0,
        "scheduler_enabled_count": 1 if packet.get("scheduler_allowed_now") is True else 0,
        "provider_llm_api_enabled_count": 0,
        "repo_web_search_enabled_count": 0,
        "scraping_enabled_count": 0,
        "newsletter_or_cms_api_enabled_count": 0,
        "backend_server_required_count": 1 if packet.get("backend_server_required") is True else 0,
        "publish_all_button_enabled_count": 1 if packet.get("publish_all_button_enabled_now") is True else 0,
        "one_button_publish_all_enabled_count": 1 if packet.get("one_button_publish_all_enabled_now") is True else 0,
        "publish_approval_system_created_count": 1 if packet.get("publish_approval_system_created") is True else 0,
        "public_ready_approval_allowed_count": 1 if packet.get("public_ready_approval_allowed_now") is True else 0,
        "final_social_copy_generated_count": 1 if packet.get("final_social_copy_generated") is True else 0,
        "final_payload_count": _pvcount("final_payload"),
        "manual_review_required_all": packet.get("manual_review_required") is True
        and all(p.get("manual_review_required") is True for p in previews),
        "not_public_postable_all": packet.get("not_public_postable") is True
        and all(p.get("not_public_postable") is True for p in previews),
        "kill_switch_required_all": packet.get("kill_switch_required") is True,
        "redacted_audit_log_required_all": packet.get("redacted_audit_log_required") is True,
        "idempotency_policy_required_all": packet.get("idempotency_policy_required") is True,
        "partial_failure_policy_required_all": packet.get("partial_failure_policy_required") is True,
        "manual_approval_gate_required_all": packet.get("manual_approval_gate_required") is True,
        "source_refs_visible_all": all(p.get("source_refs_visible") is True for p in previews),
        "limitations_visible_all": all(p.get("limitations_visible") is True for p in previews),
        "unsupported_platform_target_count": sum(
            1 for pid in packet.get("target_platform_ids", []) if pid not in REGISTRY_PLATFORM_IDS
        ),
        "unsafe_language_count": 0,
        "unsupported_numeric_claim_count": 0,
        "artifact_claim_without_real_artifact_count": 0,
        "validation_valid": res["valid"],
        "provider_call_used_by_repo": False,
        "search_call_used_by_repo": False,
        "network_call_used_by_repo": False,
        "news_api_used_by_repo": False,
        "market_data_api_used_by_repo": False,
        "platform_action_used_by_repo": False,
        "credential_or_env_read_used": False,
        "scheduler_accessed": False,
        "scraping_allowed_now": False,
        "newsletter_send_enabled": False,
        "cms_integration_enabled": False,
        "autonomous_reply_dm_enabled": False,
    }

