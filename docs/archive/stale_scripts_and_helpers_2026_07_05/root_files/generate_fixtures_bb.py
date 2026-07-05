import json
import os

os.makedirs("fixtures/scd_canonical_draft_lifecycle", exist_ok=True)

fixtures = {
    "pass_lifecycle_input_canonical_generated_once.json": {
        "schema_version": "1.0",
        "lifecycle_state": "CANONICAL_GENERATED_ONCE",
        "quota_policy_summary": "PASS",
        "prompt_pack_summary": "PASS",
        "provider_gateway_dry_run_result_summary": "PASS",
        "canonical_draft_ref": "ref",
        "canonical_draft_hash": "hash123",
        "local_validator_result": "PASS",
        "attempt_ledger_entries": [
            {"schema_version": "1.0", "operation": "canonical_generation", "attempt_index": 1, "provider_call_plan_ref": "plan", "result_summary": "PASS"}
        ]
    },
    "pass_attempt_ledger_entry_canonical_generation_1.json": {
        "schema_version": "1.0",
        "operation": "canonical_generation",
        "attempt_index": 1,
        "provider_call_plan_ref": "plan",
        "result_summary": "PASS"
    },
    "pass_validation_result_local.json": {
        "schema_version": "1.0",
        "validation_state": "PASS"
    },
    "pass_repair_patch_plan_targeted_repair.json": {
        "schema_version": "1.0",
        "patch_ref": "patch"
    },
    "pass_lifecycle_report_final.json": {
        "schema_version": "1.0",
        "lifecycle_state": "PASS",
        "validation_state": "PASS",
        "attempt_count_canonical": 1,
        "attempt_count_repair": 0,
        "total_provider_call_plans": 1
    },
    "blocked_quota_policy_not_pass.json": {
        "schema_version": "1.0",
        "lifecycle_state": "BRIEF_READY",
        "quota_policy_summary": "BLOCKED"
    },
    "blocked_prompt_pack_not_pass.json": {
        "schema_version": "1.0",
        "lifecycle_state": "CANONICAL_GENERATED_ONCE",
        "quota_policy_summary": "PASS",
        "prompt_pack_summary": "BLOCKED"
    },
    "blocked_dry_run_result_not_pass.json": {
        "schema_version": "1.0",
        "lifecycle_state": "CANONICAL_GENERATED_ONCE",
        "quota_policy_summary": "PASS",
        "prompt_pack_summary": "PASS",
        "provider_gateway_dry_run_result_summary": "BLOCKED"
    },
    "blocked_canonical_attempt_count_gt_1.json": {
        "schema_version": "1.0",
        "lifecycle_state": "CANONICAL_GENERATED_ONCE",
        "quota_policy_summary": "PASS",
        "attempt_ledger_entries": [
            {"schema_version": "1.0", "operation": "canonical_generation", "attempt_index": 1},
            {"schema_version": "1.0", "operation": "canonical_generation", "attempt_index": 2}
        ]
    },
    "blocked_targeted_repair_attempt_count_gt_1.json": {
        "schema_version": "1.0",
        "lifecycle_state": "TARGETED_REPAIR_APPLIED_ONCE",
        "quota_policy_summary": "PASS",
        "attempt_ledger_entries": [
            {"schema_version": "1.0", "operation": "canonical_generation", "attempt_index": 1},
            {"schema_version": "1.0", "operation": "targeted_repair", "attempt_index": 1},
            {"schema_version": "1.0", "operation": "targeted_repair", "attempt_index": 2}
        ]
    },
    "blocked_total_provider_call_plans_gt_2.json": {
        "schema_version": "1.0",
        "lifecycle_state": "TARGETED_REPAIR_APPLIED_ONCE",
        "quota_policy_summary": "PASS",
        "prompt_pack_summary": "PASS",
        "provider_gateway_dry_run_result_summary": "PASS",
        "attempt_ledger_entries": [
            {"schema_version": "1.0", "operation": "canonical_generation", "attempt_index": 1},
            {"schema_version": "1.0", "operation": "targeted_repair", "attempt_index": 1},
            {"schema_version": "1.0", "operation": "other", "attempt_index": 1}
        ]
    },
    "blocked_platform_variant_before_pass.json": {
        "schema_version": "1.0",
        "lifecycle_state": "CANONICAL_GENERATED_ONCE",
        "quota_policy_summary": "PASS",
        "prompt_pack_summary": "PASS",
        "provider_gateway_dry_run_result_summary": "PASS",
        "platform_variant_requested": True
    },
    "blocked_transition_back_to_canonical_planning.json": {
        "schema_version": "1.0",
        "lifecycle_state": "CANONICAL_DRAFT_PLANNED",
        "quota_policy_summary": "PASS",
        "attempt_ledger_entries": [
            {"schema_version": "1.0", "operation": "canonical_generation", "attempt_index": 1}
        ]
    },
    "blocked_full_rewrite_loop_language.json": {
        "schema_version": "1.0",
        "lifecycle_state": "BRIEF_READY",
        "quota_policy_summary": "PASS",
        "operator_context_ref": "full rewrite loop"
    },
    "blocked_provider_network_api_implication.json": {
        "schema_version": "1.0",
        "lifecycle_state": "BRIEF_READY",
        "quota_policy_summary": "PASS",
        "operator_context_ref": "api-key"
    },
    "blocked_financial_signal_language.json": {
        "schema_version": "1.0",
        "lifecycle_state": "BRIEF_READY",
        "quota_policy_summary": "PASS",
        "operator_context_ref": "price target"
    },
    "review_required_second_failure.json": {
        "schema_version": "1.0",
        "lifecycle_state": "TARGETED_REPAIR_APPLIED_ONCE",
        "quota_policy_summary": "PASS",
        "prompt_pack_summary": "PASS",
        "provider_gateway_dry_run_result_summary": "PASS",
        "canonical_draft_hash": "hash123",
        "local_validator_result": "second_failure"
    },
    "review_required_critique_enabled_without_budget.json": {
        "schema_version": "1.0",
        "lifecycle_state": "CANONICAL_GENERATED_ONCE",
        "quota_policy_summary": "PASS",
        "prompt_pack_summary": "PASS",
        "provider_gateway_dry_run_result_summary": "PASS",
        "canonical_draft_hash": "hash123",
        "local_validator_result": "critique_budget_issue"
    },
    "unknown_missing_canonical_draft_hash.json": {
        "schema_version": "1.0",
        "lifecycle_state": "LOCAL_VALIDATED",
        "quota_policy_summary": "PASS",
        "local_validator_result": "PASS",
        "prompt_pack_summary": "PASS",
        "provider_gateway_dry_run_result_summary": "PASS"
    },
    "unknown_missing_provider_dry_run_result_ref.json": {
        "schema_version": "1.0",
        "lifecycle_state": "CANONICAL_DRAFT_PLANNED",
        "quota_policy_summary": "PASS",
        "canonical_draft_hash": "hash123",
        "provider_gateway_dry_run_result_summary": ""
    }
}

for filename, content in fixtures.items():
    with open(f"fixtures/scd_canonical_draft_lifecycle/{filename}", "w") as f:
        json.dump(content, f, indent=2)

print("Generated fixtures.")
