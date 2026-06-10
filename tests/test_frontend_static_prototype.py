import os
import json
from live_contentops.frontend_static_prototype import validate_frontend_static_prototype_packet, validate_static_html

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "frontend_static_prototype")

def _load(name):
    with open(os.path.join(FIX_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)

def test_valid_operator_console_fixture():
    res = validate_frontend_static_prototype_packet(_load("operator_console_fixture.json"))
    assert res["valid"] is True

def test_invalid_live_action_enabled():
    res = validate_frontend_static_prototype_packet(_load("invalid_live_action_enabled.json"))
    assert res["valid"] is False

def test_invalid_external_script_reference():
    res = validate_frontend_static_prototype_packet(_load("invalid_external_script_reference.json"))
    assert res["valid"] is False

def test_invalid_secret_visible():
    res = validate_frontend_static_prototype_packet(_load("invalid_secret_visible.json"))
    assert res["valid"] is False

def test_static_html_safety():
    html_safe = "<html><body><h1>UI Placeholder</h1></body></html>"
    res = validate_static_html(html_safe)
    assert res["valid"] is True

    html_unsafe1 = "<html><script src='x'></script></html>"
    assert validate_static_html(html_unsafe1)["valid"] is False

    html_unsafe2 = "<html><body>FAKE_SECRET</body></html>"
    assert validate_static_html(html_unsafe2)["valid"] is False
    
    html_unsafe3 = "<html><body>http://example.com</body></html>"
    assert validate_static_html(html_unsafe3)["valid"] is False
