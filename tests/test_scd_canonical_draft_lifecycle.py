import json
import pytest
from pathlib import Path
from live_contentops.scd_canonical_draft_lifecycle import (
    validate_canonical_draft_lifecycle_input,
    validate_canonical_draft_attempt_ledger_entry,
    validate_canonical_draft_validation_result,
    validate_targeted_repair_patch_plan,
    validate_canonical_draft_lifecycle_report,
    build_attempt_ledger_entry,
    build_lifecycle_report,
    CANONICAL_DRAFT_LIFECYCLE_VALIDATORS
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "scd_canonical_draft_lifecycle"

def _load(name):
    with open(FIXTURES_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)

def test_pass_lifecycle_input_canonical_generated_once():
    data = _load("pass_lifecycle_input_canonical_generated_once.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "PASS"

def test_pass_attempt_ledger_entry_canonical_generation_1():
    data = _load("pass_attempt_ledger_entry_canonical_generation_1.json")
    res = validate_canonical_draft_attempt_ledger_entry(data)
    assert res["validation_state"] == "PASS"

def test_pass_validation_result_local():
    data = _load("pass_validation_result_local.json")
    res = validate_canonical_draft_validation_result(data)
    assert res["validation_state"] == "PASS"

def test_pass_repair_patch_plan_targeted_repair():
    data = _load("pass_repair_patch_plan_targeted_repair.json")
    res = validate_targeted_repair_patch_plan(data)
    assert res["validation_state"] == "PASS"

def test_pass_lifecycle_report_final():
    data = _load("pass_lifecycle_report_final.json")
    res = validate_canonical_draft_lifecycle_report(data)
    assert res["validation_state"] == "PASS"

def test_blocked_quota_policy_not_pass():
    data = _load("blocked_quota_policy_not_pass.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "BLOCKED"
    assert any("quota_policy_summary" in r for r in res["reasons"])

def test_blocked_prompt_pack_not_pass():
    data = _load("blocked_prompt_pack_not_pass.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "BLOCKED"

def test_blocked_dry_run_result_not_pass():
    data = _load("blocked_dry_run_result_not_pass.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "BLOCKED"

def test_blocked_canonical_attempt_count_gt_1():
    data = _load("blocked_canonical_attempt_count_gt_1.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "BLOCKED"
    assert any("canonical_generation" in r for r in res["reasons"])

def test_blocked_targeted_repair_attempt_count_gt_1():
    data = _load("blocked_targeted_repair_attempt_count_gt_1.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "BLOCKED"

def test_blocked_total_provider_call_plans_gt_2():
    data = _load("blocked_total_provider_call_plans_gt_2.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "BLOCKED"
    assert any("total provider-call plans" in r for r in res["reasons"])

def test_blocked_platform_variant_before_pass():
    data = _load("blocked_platform_variant_before_pass.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "BLOCKED"
    assert any("platform_variant_requested" in r for r in res["reasons"])

def test_blocked_transition_back_to_canonical_planning():
    data = _load("blocked_transition_back_to_canonical_planning.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "BLOCKED"

def test_blocked_full_rewrite_loop_language():
    data = _load("blocked_full_rewrite_loop_language.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "BLOCKED"

def test_blocked_provider_network_api_implication():
    data = _load("blocked_provider_network_api_implication.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "BLOCKED"

def test_blocked_financial_signal_language():
    data = _load("blocked_financial_signal_language.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "BLOCKED"

def test_review_required_second_failure():
    data = _load("review_required_second_failure.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "REVIEW_REQUIRED"

def test_review_required_critique_enabled_without_budget():
    data = _load("review_required_critique_enabled_without_budget.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "REVIEW_REQUIRED"

def test_unknown_missing_canonical_draft_hash():
    data = _load("unknown_missing_canonical_draft_hash.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "UNKNOWN"

def test_unknown_missing_provider_dry_run_result_ref():
    data = _load("unknown_missing_provider_dry_run_result_ref.json")
    res = validate_canonical_draft_lifecycle_input(data)
    assert res["validation_state"] == "UNKNOWN"

def test_build_attempt_ledger_entry():
    res = build_attempt_ledger_entry({}, "canonical_generation", 1)
    assert res["operation"] == "canonical_generation"
    assert res["attempt_index"] == 1
    assert res["provider_call_plan_ref"] == "canonical_generation_plan_1"

def test_build_lifecycle_report():
    input_packet = {"lifecycle_state": "PASS"}
    ledger = [{"operation": "canonical_generation"}]
    val = {"validation_state": "PASS"}
    rep = build_lifecycle_report(input_packet, ledger, val)
    assert rep["attempt_count_canonical"] == 1
    assert rep["attempt_count_repair"] == 0
    assert rep["total_provider_call_plans"] == 1
    assert rep["lifecycle_state"] == "PASS"
    assert rep["validation_state"] == "PASS"


def test_blocked_repair_patch_plan_full_rewrite():
    data = _load("blocked_repair_patch_plan_full_rewrite.json")
    res = validate_targeted_repair_patch_plan(data)
    assert res["validation_state"] == "BLOCKED"

def test_blocked_repair_patch_plan_provider_api():
    data = _load("blocked_repair_patch_plan_provider_api.json")
    res = validate_targeted_repair_patch_plan(data)
    assert res["validation_state"] == "BLOCKED"

def test_blocked_repair_patch_plan_financial_signal():
    data = _load("blocked_repair_patch_plan_financial_signal.json")
    res = validate_targeted_repair_patch_plan(data)
    assert res["validation_state"] == "BLOCKED"

def test_blocked_validation_result_provider_api():
    data = _load("blocked_validation_result_provider_api.json")
    res = validate_canonical_draft_validation_result(data)
    assert res["validation_state"] == "BLOCKED"

def test_blocked_validation_result_financial_signal():
    data = _load("blocked_validation_result_financial_signal.json")
    res = validate_canonical_draft_validation_result(data)
    assert res["validation_state"] == "BLOCKED"

def test_blocked_lifecycle_report_retry_until_pass():
    data = _load("blocked_lifecycle_report_retry_until_pass.json")
    res = validate_canonical_draft_lifecycle_report(data)
    assert res["validation_state"] == "BLOCKED"

def test_blocked_lifecycle_report_provider_ready():
    data = _load("blocked_lifecycle_report_provider_ready.json")
    res = validate_canonical_draft_lifecycle_report(data)
    assert res["validation_state"] == "BLOCKED"

def test_mutation_repair_patch_plan_note():
    data = {"schema_version": "1.0", "patch_ref": "p", "note": "rewrite the entire draft repeatedly"}
    res = validate_targeted_repair_patch_plan(data)
    assert res["validation_state"] == "BLOCKED"

def test_mutation_validation_result_note():
    data = {"schema_version": "1.0", "validation_state": "PASS", "note": "call the webhook"}
    res = validate_canonical_draft_validation_result(data)
    assert res["validation_state"] == "BLOCKED"

def test_mutation_report_note():
    data = {"schema_version": "1.0", "lifecycle_state": "PASS", "validation_state": "PASS", "note": "generate until pass"}
    res = validate_canonical_draft_lifecycle_report(data)
    assert res["validation_state"] == "BLOCKED"

def test_mutation_report_provider_ready():
    data = {"schema_version": "1.0", "lifecycle_state": "PASS", "validation_state": "PASS", "provider_ready": True}
    res = validate_canonical_draft_lifecycle_report(data)
    assert res["validation_state"] == "BLOCKED"
