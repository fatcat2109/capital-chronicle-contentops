with open("tests/test_scd_canonical_draft_lifecycle.py", "a", encoding="utf-8") as f:
    f.write("""

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
    data = {"schema_version": "1.0", "validation_state": "PASS", "note": "call the provider API"}
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
""")
print("Appended tests.")
