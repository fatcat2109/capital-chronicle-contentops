import os
import json
from live_contentops.operator_ui_ux_spec import validate_operator_ui_ux_spec_packet, validate_content_calendar_spec_packet

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "operator_ui_ux")

def test_schemas_are_valid():
    res1 = validate_operator_ui_ux_spec_packet(json.load(open(os.path.join(FIX_DIR, "valid_operator_console_spec.json"))))
    assert res1["valid"] is True
    
    res2 = validate_content_calendar_spec_packet(json.load(open(os.path.join(FIX_DIR, "valid_content_calendar_spec.json"))))
    assert res2["valid"] is True
