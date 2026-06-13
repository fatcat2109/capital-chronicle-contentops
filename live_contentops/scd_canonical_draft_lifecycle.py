"""Local-only canonical draft lifecycle and attempt ledger contract (SCD, 0174BB).

Defines the state-machine rules and attempt ledger for a content packet before any
provider call is made. No network, no credentials, no UI, no API.
"""
from live_contentops.scd_domain_model import (
    PASS, BLOCKED, REVIEW_REQUIRED, UNKNOWN,
    _schema_ok, _find_language, _scan_secrets, _result, FORBIDDEN_LANGUAGE
)
from live_contentops.scd_platform_payload_compiler import TELEGRAM_API_PATTERNS
from live_contentops.scd_dispatch_gate import NETWORK_API_PATTERNS

LOOP_LANGUAGE_PATTERNS = [
    r"generate until (pass|it passes|success)",
    r"retry until (success|pass|it passes)",
    r"auto[- ]?regenerate",
    r"\bunbounded\b",
    r"rewrite (the )?entire draft repeatedly",
    r"repeatedly rewrite",
    r"infinite (retry|retries|loop)",
    r"loop until (pass|success|it passes)",
    r"keep (re)?generating",
    r"regenerate until",
    r"full rewrite loop",
]

def _scan_all_strings(obj, patterns):
    found = []
    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(k, str):
                    found.extend(_find_language(k, patterns))
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            found.extend(_find_language(node, patterns))
    walk(obj)
    return found

def validate_canonical_draft_lifecycle_input(packet):
    ok, msg = _schema_ok(packet, "scd_canonical_draft_lifecycle_input.schema.json")
    if not ok: return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    blocked += _scan_secrets(packet)
    blocked += [f"network/api: {h}" for h in _scan_all_strings(packet, NETWORK_API_PATTERNS)]
    blocked += [f"telegram/api: {h}" for h in _scan_all_strings(packet, TELEGRAM_API_PATTERNS)]
    blocked += [f"forbidden loop language: {h}" for h in _scan_all_strings(packet, LOOP_LANGUAGE_PATTERNS)]
    blocked += [f"financial/signal language: {h}" for h in _scan_all_strings(packet, FORBIDDEN_LANGUAGE)]

    if packet.get("quota_policy_summary") != PASS:
        blocked.append("quota_policy_summary must be PASS")

    state = packet.get("lifecycle_state")
    ledger = packet.get("attempt_ledger_entries", [])
    cg_count = sum(1 for e in ledger if e.get("operation") == "canonical_generation")
    tr_count = sum(1 for e in ledger if e.get("operation") == "targeted_repair")

    if cg_count > 1:
        blocked.append("canonical_generation attempt count > 1")
    if tr_count > 1:
        blocked.append("targeted_repair attempt count > 1")
    if len(ledger) > 2:
        blocked.append("total provider-call plans > 2")

    if cg_count > 0 and state == "CANONICAL_DRAFT_PLANNED":
        blocked.append("no transition back to CANONICAL_DRAFT_PLANNED after generation")

    if state in ("CANONICAL_GENERATED_ONCE", "LOCAL_VALIDATED", "TARGETED_REPAIR_PLANNED", "TARGETED_REPAIR_APPLIED_ONCE", "PASS"):
        if packet.get("prompt_pack_summary") != PASS:
            blocked.append("prompt_pack_summary must be PASS for canonical generation")
        if packet.get("provider_gateway_dry_run_result_summary") != PASS:
            blocked.append("provider_gateway_dry_run_result_summary must be PASS before CANONICAL_GENERATED_ONCE")

    if packet.get("platform_variant_requested") and state != PASS:
        blocked.append("platform_variant_requested must be false unless lifecycle_state is PASS")

    if state == PASS:
        if packet.get("local_validator_result") != PASS:
            blocked.append("PASS requires local_validator_result PASS")
        if not packet.get("canonical_draft_hash"):
            blocked.append("PASS requires canonical_draft_hash present")

    if not packet.get("canonical_draft_hash"):
        unknown.append("missing canonical_draft_hash")

    if not packet.get("provider_gateway_dry_run_result_summary"):
        unknown.append("missing provider dry-run result ref")

    local_val = packet.get("local_validator_result")
    if local_val == "major_safety_failure":
        blocked.append("BLOCKED after major safety failure")
    elif local_val == "second_failure":
        review.append("REVIEW_REQUIRED after second failure")
    elif local_val == "critique_budget_issue":
        review.append("REVIEW_REQUIRED critique enabled without budget")

    return _result(blocked, review, unknown)

def validate_canonical_draft_attempt_ledger_entry(packet):
    ok, msg = _schema_ok(packet, "scd_canonical_draft_attempt_ledger_entry.schema.json")
    if not ok: return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}
    blocked, review, unknown = [], [], []
    blocked += _scan_secrets(packet)
    blocked += [f"network/api: {h}" for h in _scan_all_strings(packet, NETWORK_API_PATTERNS)]
    blocked += [f"telegram/api: {h}" for h in _scan_all_strings(packet, TELEGRAM_API_PATTERNS)]
    blocked += [f"forbidden loop language: {h}" for h in _scan_all_strings(packet, LOOP_LANGUAGE_PATTERNS)]

    op = packet.get("operation")
    idx = packet.get("attempt_index")
    if op == "canonical_generation" and idx != 1:
        blocked.append("canonical_generation attempt count must be exactly 1")
    if op == "targeted_repair" and idx != 1:
        blocked.append("targeted_repair attempt count must be 1")

    return _result(blocked, review, unknown)

def validate_canonical_draft_validation_result(packet):
    ok, msg = _schema_ok(packet, "scd_canonical_draft_validation_result.schema.json")
    if not ok: return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}
    return _result([], [], [])

def validate_targeted_repair_patch_plan(packet):
    ok, msg = _schema_ok(packet, "scd_targeted_repair_patch_plan.schema.json")
    if not ok: return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}
    return _result([], [], [])

def validate_canonical_draft_lifecycle_report(packet):
    ok, msg = _schema_ok(packet, "scd_canonical_draft_lifecycle_report.schema.json")
    if not ok: return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}
    blocked, review, unknown = [], [], []

    cg = packet.get("attempt_count_canonical", 0)
    tr = packet.get("attempt_count_repair", 0)
    tot = packet.get("total_provider_call_plans", 0)

    if cg > 1:
        blocked.append("canonical_generation attempt count > 1")
    if tr > 1:
        blocked.append("targeted_repair attempt count > 1")
    if tot > 2:
        blocked.append("total provider-call plans > 2")

    return _result(blocked, review, unknown)

def build_attempt_ledger_entry(input_packet, operation, attempt_index):
    return {
        "schema_version": "1.0",
        "operation": operation,
        "attempt_index": attempt_index,
        "provider_call_plan_ref": f"{operation}_plan_{attempt_index}",
        "result_summary": "planned"
    }

def build_lifecycle_report(input_packet, ledger_entries, validation_result):
    cg_count = sum(1 for e in ledger_entries if e.get("operation") == "canonical_generation")
    tr_count = sum(1 for e in ledger_entries if e.get("operation") == "targeted_repair")

    return {
        "schema_version": "1.0",
        "lifecycle_state": input_packet.get("lifecycle_state", "UNKNOWN"),
        "validation_state": validation_result.get("validation_state", UNKNOWN),
        "attempt_count_canonical": cg_count,
        "attempt_count_repair": tr_count,
        "total_provider_call_plans": cg_count + tr_count,
        "reasons": validation_result.get("reasons", [])
    }

CANONICAL_DRAFT_LIFECYCLE_VALIDATORS = {
    "canonical_draft_lifecycle_input": validate_canonical_draft_lifecycle_input,
    "canonical_draft_attempt_ledger_entry": validate_canonical_draft_attempt_ledger_entry,
    "canonical_draft_validation_result": validate_canonical_draft_validation_result,
    "targeted_repair_patch_plan": validate_targeted_repair_patch_plan,
    "canonical_draft_lifecycle_report": validate_canonical_draft_lifecycle_report,
}
