import json
from pathlib import Path


def test_fast_ship_profile_document_content():
    profile_path = Path("docs/automation/V6_FAST_SHIP_OPERATING_PROFILE/fast_ship_operating_profile.md")
    assert profile_path.exists()
    content = profile_path.read_text(encoding="utf-8").lower()
    
    # Assert requested keywords or semantic equivalents
    assert "heavy batch" in content
    assert "fast ship" in content
    assert "live-capable" in content
    assert "env access" in content or "env allowed" in content or "environment access" in content
    assert "ceremony" in content


def test_prompt_style_guide_rules():
    guide_path = Path("docs/automation/V6_FAST_SHIP_OPERATING_PROFILE/prompt_style_guide.md")
    assert guide_path.exists()
    content = guide_path.read_text(encoding="utf-8").lower()
    
    assert "line one" in content or "line-one" in content
    assert "concise safety invariant" in content
    assert "omitted ceremony" in content or "stop repeating" in content or "avoid repeated ceremony" in content


def test_task_classification_matrix():
    matrix_path = Path("docs/automation/V6_FAST_SHIP_OPERATING_PROFILE/task_classification_matrix.json")
    assert matrix_path.exists()
    
    with open(matrix_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    classes = data.get("classes", {})
    required_classes = [
        "implementation_batch",
        "evidence_repair_batch",
        "project_sources_refresh",
        "env_capability_check",
        "provider_live_call",
        "browser_qa",
        "browser_compose_dry_run",
        "live_api_read_probe",
        "live_webhook_pilot",
        "supervised_dispatch_pilot",
        "red_team_security",
        "visual_ui_build",
        "visual_browser_qa"
    ]
    for c in required_classes:
        assert c in classes
        cls_data = classes[c]
        assert "env_allowed" in cls_data
        assert "browser_allowed" in cls_data
        assert "provider_allowed" in cls_data
        assert "live_write_allowed" in cls_data
        assert "required_scope_fields" in cls_data

    # Env allowed but not live write
    env_no_live = classes["env_capability_check"]
    assert env_no_live["env_allowed"] is True
    assert env_no_live["live_write_allowed"] is False

    # Allows browser QA
    assert classes["browser_qa"]["browser_allowed"] is True

    # Live webhook pilot allows live write only with approval/scope fields
    webhook = classes["live_webhook_pilot"]
    assert webhook["live_write_allowed"] is True
    assert "approval_condition" in webhook["required_scope_fields"]

    # Supervised dispatch pilot requirements
    dispatch = classes["supervised_dispatch_pilot"]
    assert dispatch["live_write_allowed"] is True
    for field in [
        "payload_hash_requirement",
        "destination_binding",
        "approval_condition",
        "request_budget",
        "timeout",
        "redacted_audit_fields"
    ]:
        assert field in dispatch["required_scope_fields"] or field.replace("_requirement", "") in dispatch["required_scope_fields"]


def test_continuation_docs_reflect_operating_profile():
    continuation_path = Path("docs/automation/V6_PROJECT_SOURCES_UPLOAD_BUNDLE/NEW_CHAT_CONTINUATION_V6_READINESS.md")
    assert continuation_path.exists()
    content = continuation_path.read_text(encoding="utf-8").lower()
    
    # Continuation should mention fast ship/heavy batch or operating profile rules
    assert "fast ship" in content or "operating profile" in content


def test_no_secret_or_webhook_leakage():
    docs_to_scan = [
        "docs/automation/V6_FAST_SHIP_OPERATING_PROFILE/fast_ship_operating_profile.md",
        "docs/automation/V6_FAST_SHIP_OPERATING_PROFILE/prompt_style_guide.md",
        "docs/automation/V6_FAST_SHIP_OPERATING_PROFILE/live_env_scope_contract.md",
        "docs/automation/V6_FAST_SHIP_OPERATING_PROFILE/task_classification_matrix.json"
    ]
    
    for path in docs_to_scan:
        content = Path(path).read_text(encoding="utf-8").lower()
        assert "discord.com/api/webhooks/1" not in content
        assert "token_value" not in content
        assert "cookie_value" not in content
        assert "secret_key" not in content
