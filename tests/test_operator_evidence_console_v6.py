import json
from pathlib import Path
from live_contentops import operator_evidence_console_v6 as console


def test_console_packet_has_secure_flags():
    out_dir = Path("docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE")
    console.main(["--output-dir", str(out_dir)])
    
    packet_file = out_dir / "operator_evidence_console_packet.json"
    assert packet_file.exists()
    
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["evidence_complete"] is False
    assert data["operator_idea_source_ref_resolved"] is False
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["approval_valid_for_dispatch"] is False
    assert data["outbox_entry_created"] is False
    assert data["payload_hash_created"] is False
    assert data["credentials_hydrated"] is False
    assert data["browser_session_started"] is False
    assert data["kill_switch_active"] is True
    assert data["public_postable"] is False
    
    assert data["next_recommended_task"] == "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"
    assert data["validator_next_task"] == "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"
    assert data["next_task_pointer_is_soft"] is True
    assert data.get("raw_secret_output", False) is False
    assert data.get("webhook_url_printed", False) is False


def test_console_scaffold_has_all_10_slots():
    out_dir = Path("docs/automation/V6_OPERATOR_EVIDENCE_CONSOLE")
    console.main(["--output-dir", str(out_dir)])
    
    blank_file = out_dir / "operator_evidence_fixture.blank.json"
    assert blank_file.exists()
    
    blank = json.loads(blank_file.read_text(encoding="utf-8"))
    assert set(blank.keys()) == set(console.REQUIRED_SLOTS)
    
    example_file = out_dir / "operator_evidence_fixture.example.safe_placeholder.json"
    assert example_file.exists()
    
    example = json.loads(example_file.read_text(encoding="utf-8"))
    assert set(example.keys()) == set(console.REQUIRED_SLOTS)
    for slot in console.REQUIRED_SLOTS:
        val = example[slot]
        if isinstance(val, list):
            assert "PLACEHOLDER_REPLACE_BEFORE_REVIEW" in val
        else:
            assert val == "PLACEHOLDER_REPLACE_BEFORE_REVIEW"


def test_no_sensitive_values_in_scaffold_docs():
    instructions = console.generate_fill_instructions()
    assert "discord.com/api/webhooks" not in instructions
    assert "token" not in instructions.lower()
    
    checklist = console.generate_validation_checklist()
    assert "discord.com/api/webhooks" not in checklist
    assert "ghp_" not in checklist
    assert ".env" not in checklist


def test_module_contains_no_forbidden_behavior():
    attrs = dir(console)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
