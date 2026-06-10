import os
import json
from live_contentops.platform_official_docs_verification import validate_platform_official_docs_verification_packet

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "platform_official_docs")

def test_schemas_are_valid():
    with open(os.path.join(FIX_DIR, "valid_operator_supplied_official_docs_packet.json"), "r", encoding="utf-8") as f:
        rec = json.load(f)
    res = validate_platform_official_docs_verification_packet(rec)
    assert res["valid"] is True
