import os
import json
from live_contentops.credential_envelope_policy import validate_credential_envelope_policy_packet

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "credential_envelope_policy")

def test_schemas_are_valid():
    with open(os.path.join(FIX_DIR, "valid_no_credentials_loaded_policy.json"), "r", encoding="utf-8") as f:
        rec = json.load(f)
    res = validate_credential_envelope_policy_packet(rec)
    assert res["valid"] is True
