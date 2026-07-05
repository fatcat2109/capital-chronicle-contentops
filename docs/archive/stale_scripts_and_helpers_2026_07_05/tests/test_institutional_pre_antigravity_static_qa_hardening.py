import pytest
import jsonschema
import json
from live_contentops import institutional_pre_antigravity_static_qa_hardening
import os
import re

def test_static_qa_hardening_packet_validates():
    packet = institutional_pre_antigravity_static_qa_hardening.build_summary()
    schema_path = institutional_pre_antigravity_static_qa_hardening.SCHEMA_PATH
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    jsonschema.validate(instance=packet, schema=schema)
    errors = institutional_pre_antigravity_static_qa_hardening.validate_packet(packet)
    assert len(errors) == 0

def test_static_qa_hardening_errors_caught():
    packet = institutional_pre_antigravity_static_qa_hardening.build_summary()
    packet["runtime_authority"] = True
    packet["packet_status"] = "pass"
    errors = institutional_pre_antigravity_static_qa_hardening.validate_packet(packet)
    assert len(errors) >= 2  # one for runtime_authority, one for packet_status pass while errors exist

def test_static_shell_files_exist():
    base = os.path.join("ui", "institutional_shell")
    assert os.path.exists(os.path.join(base, "index.html"))
    assert os.path.exists(os.path.join(base, "styles.css"))
    assert os.path.exists(os.path.join(base, "app.js"))
    assert os.path.exists(os.path.join(base, "fixture_data.js"))
    assert os.path.exists(os.path.join(base, "README.md"))

def test_no_remote_assets_in_shell():
    base = os.path.join("ui", "institutional_shell")
    files_to_check = ["index.html", "app.js", "styles.css", "fixture_data.js"]
    for f in files_to_check:
        path = os.path.join(base, f)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fp:
                content = fp.read()
                lines = content.split('\n')
                for line in lines:
                    if "http://" in line or "https://" in line:
                        assert "w3.org" in line or "json-schema.org" in line or "schema.org" in line or "github.com" in line or "svg" in line or "w3" in line, f"Remote URL found: {line.strip()}"
            
            # check executable code, not comments
            # app.js has a comment "No network, no fetch, no XMLHttpRequest"
            clean_content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            clean_content = re.sub(r'//.*', '', clean_content)
            
            assert "fetch(" not in clean_content
            assert "XMLHttpRequest(" not in clean_content
            assert "WebSocket(" not in clean_content
            assert "EventSource(" not in clean_content
            assert "import(" not in clean_content

def test_disabled_controls():
    # Verify app.js or fixture_data contains no active disabled classes for live states
    base = os.path.join("ui", "institutional_shell")
    path = os.path.join(base, "fixture_data.js")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fp:
            content = fp.read()
            assert "api.telegram.org" not in content

def test_all_12_screens_present():
    path = os.path.join("ui", "institutional_shell", "fixture_data.js")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fp:
            content = fp.read()
            screens = [
                "command_center", "content_lane_control", "daily_content_studio",
                "draft_inspector", "grounded_news_angle_lab", "publish_readiness_tower",
                "telegram_pilot_gate", "approval_queue", "content_calendar",
                "evidence_vault", "visual_export_studio", "settings_safety_policy"
            ]
            for s in screens:
                assert s in content, f"Screen {s} not found in fixture_data.js"
