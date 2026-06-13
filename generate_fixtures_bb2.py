import json
import os

os.makedirs("fixtures/scd_canonical_draft_lifecycle", exist_ok=True)

fixtures = {
    "blocked_repair_patch_plan_full_rewrite.json": {
        "schema_version": "1.0",
        "patch_ref": "patch",
        "note": "full rewrite loop"
    },
    "blocked_repair_patch_plan_provider_api.json": {
        "schema_version": "1.0",
        "patch_ref": "patch",
        "note": "use provider api"
    },
    "blocked_repair_patch_plan_financial_signal.json": {
        "schema_version": "1.0",
        "patch_ref": "patch",
        "note": "price target"
    },
    "blocked_validation_result_provider_api.json": {
        "schema_version": "1.0",
        "validation_state": "PASS",
        "note": "network access"
    },
    "blocked_validation_result_financial_signal.json": {
        "schema_version": "1.0",
        "validation_state": "PASS",
        "note": "model says buy"
    },
    "blocked_lifecycle_report_retry_until_pass.json": {
        "schema_version": "1.0",
        "lifecycle_state": "PASS",
        "validation_state": "PASS",
        "note": "retry until pass"
    },
    "blocked_lifecycle_report_provider_ready.json": {
        "schema_version": "1.0",
        "lifecycle_state": "PASS",
        "validation_state": "PASS",
        "provider_ready": True
    }
}

for filename, content in fixtures.items():
    with open(f"fixtures/scd_canonical_draft_lifecycle/{filename}", "w") as f:
        json.dump(content, f, indent=2)

print("Generated new fixtures.")
