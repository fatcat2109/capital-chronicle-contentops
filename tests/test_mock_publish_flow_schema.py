import os
import json
from live_contentops.mock_publish_flow import validate_mock_publish_result

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "mock_publish_flow")

def test_schemas_are_valid():
    with open(os.path.join(FIX_DIR, "valid_mock_publish_ready.json"), "r", encoding="utf-8") as f:
        rec = json.load(f)
    appr = {"approval_state": "operator_approved_for_mock_publish"}
    ks = {"mock_publish_allowed_when_enabled": True}
    res = validate_mock_publish_result(rec, approval_rec=appr, ks=ks)
    assert res["valid"] is True
