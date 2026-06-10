import os
import json
from live_contentops.frontend_static_prototype import validate_frontend_static_prototype_packet

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "frontend_static_prototype")

def test_schemas_are_valid():
    res1 = validate_frontend_static_prototype_packet(json.load(open(os.path.join(FIX_DIR, "operator_console_fixture.json"))))
    assert res1["valid"] is True
