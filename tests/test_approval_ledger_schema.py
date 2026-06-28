import os
import json
from live_contentops.approval_audit_contracts import validate_approval_record

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "approval_ledger")

def test_schemas_are_valid():
    with open(os.path.join(FIX_DIR, "valid_operator_review_required.json"), "r", encoding="utf-8") as f:
        rec = json.load(f)
    res = validate_approval_record(rec)
    assert res["valid"] is True
