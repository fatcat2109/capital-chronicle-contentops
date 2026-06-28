import json
from pathlib import Path
import pytest
from live_contentops import payload_preview_hash_v6 as preview_hash


def test_committed_preview_hash_packet_properties():
    out_dir = Path("docs/automation/V6_PAYLOAD_PREVIEW_HASH")
    preview_hash.main(["--output-dir", str(out_dir)])
    
    packet_file = out_dir / "payload_preview_hash_packet.json"
    assert packet_file.exists()
    
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["payload_preview_status"] == "READY_FOR_OPERATOR_REVIEW"
    assert data["payload_hash_created"] is True
    assert data["exact_payload_preview_created"] is True
    assert data["evidence_complete"] is True
    assert data["source_preflight_ready"] is True
    
    # Critical security locks
    assert data["approval_valid_for_dispatch"] is False
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["outbox_entry_created"] is False
    assert data["destination_binding_complete"] is False
    assert data["credentials_hydrated"] is False
    assert data["browser_session_started"] is False
    assert data["public_postable"] is False
    assert data["kill_switch_active"] is True
    
    # Next task recommended
    assert data["next_recommended_task"] == "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_SIGNATURE_BINDING_LANE_HEAVY_BATCH_V0"


def test_payload_preview_is_review_only():
    out_dir = Path("docs/automation/V6_PAYLOAD_PREVIEW_HASH")
    preview_hash.main(["--output-dir", str(out_dir)])
    
    preview_file = out_dir / "payload_preview_exact_review.json"
    assert preview_file.exists()
    
    data = json.loads(preview_file.read_text(encoding="utf-8"))
    assert data["payload_type"] == "review_only_payload_preview"
    assert data["visibility_class"] == "review_only_payload_preview"
    assert data["approval_required"] is True
    assert data["dispatch_ready"] is False
    assert data["public_postable"] is False
    assert data["is_local_only"] is True


def test_hash_is_deterministic(tmp_path):
    out_dir1 = tmp_path / "run1"
    out_dir2 = tmp_path / "run2"
    
    preview_hash.main(["--output-dir", str(out_dir1)])
    preview_hash.main(["--output-dir", str(out_dir2)])
    
    rec1 = json.loads((out_dir1 / "V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json").read_text(encoding="utf-8"))
    rec2 = json.loads((out_dir2 / "V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json").read_text(encoding="utf-8"))
    
    assert rec1["payload_hash"] == rec2["payload_hash"]
    assert rec1["payload_hash_algorithm"] == "sha256"


def test_hash_is_sensitive_to_changes(tmp_path):
    # Setup baseline fixture
    base_fixture = tmp_path / "fixture.json"
    base_fixture.write_text(json.dumps({
        "intended_content_lane": "Substack",
        "topic_statement": "Grounding spec",
        "factual_claims": ["Claim 1", "Claim 2"],
        "intended_canonical_article_angle": "Angle A"
    }), encoding="utf-8")
    
    out_base = tmp_path / "base"
    preview_hash.main(["--fixture-file", str(base_fixture), "--output-dir", str(out_base)])
    h_base = json.loads((out_base / "V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json").read_text(encoding="utf-8"))["payload_hash"]
    
    # Change body text
    fixture_changed_text = tmp_path / "fixture_changed_text.json"
    fixture_changed_text.write_text(json.dumps({
        "intended_content_lane": "Substack",
        "topic_statement": "Grounding spec",
        "factual_claims": ["Claim 1", "Claim 2", "Claim 3"],
        "intended_canonical_article_angle": "Angle A"
    }), encoding="utf-8")
    
    out_changed_text = tmp_path / "changed_text"
    preview_hash.main(["--fixture-file", str(fixture_changed_text), "--output-dir", str(out_changed_text)])
    h_changed_text = json.loads((out_changed_text / "V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json").read_text(encoding="utf-8"))["payload_hash"]
    
    assert h_base != h_changed_text
    
    # Change platform lane
    fixture_changed_lane = tmp_path / "fixture_changed_lane.json"
    fixture_changed_lane.write_text(json.dumps({
        "intended_content_lane": "Telegram",
        "topic_statement": "Grounding spec",
        "factual_claims": ["Claim 1", "Claim 2"],
        "intended_canonical_article_angle": "Angle A"
    }), encoding="utf-8")
    
    out_changed_lane = tmp_path / "changed_lane"
    preview_hash.main(["--fixture-file", str(fixture_changed_lane), "--output-dir", str(out_changed_lane)])
    h_changed_lane = json.loads((out_changed_lane / "V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json").read_text(encoding="utf-8"))["payload_hash"]
    
    assert h_base != h_changed_lane


def test_forbidden_terms_raise_error(tmp_path):
    bad_fixture = tmp_path / "bad_fixture.json"
    bad_fixture.write_text(json.dumps({
        "intended_content_lane": "Substack",
        "topic_statement": "Secret token is present here",
        "factual_claims": ["Claim 1"],
        "intended_canonical_article_angle": "Angle"
    }), encoding="utf-8")
    
    out_dir = tmp_path / "out"
    with pytest.raises(ValueError, match="forbidden_hash_input_material"):
        preview_hash.main(["--fixture-file", str(bad_fixture), "--output-dir", str(out_dir)])


def test_no_sensitive_values_in_artifacts():
    out_dir = Path("docs/automation/V6_PAYLOAD_PREVIEW_HASH")
    preview_hash.main(["--output-dir", str(out_dir)])
    
    files = [
        out_dir / "payload_preview_hash_packet.json",
        out_dir / "payload_preview_exact_review.json",
        out_dir / "payload_hash_record.json",
        out_dir / "payload_hash_inputs_redacted.json",
        out_dir / "payload_preview_blocker_report.md",
        out_dir / "payload_preview_runbook.md",
        out_dir / "implementation_report.md",
        out_dir / "next_task_pointer.md"
    ]
    
    for f in files:
        assert f.exists()
        content = f.read_text(encoding="utf-8")
        assert "discord.com/api/webhooks" not in content
        assert "token_value" not in content.lower()
        assert "cookie_value" not in content.lower()
        assert "secret_key" not in content.lower()
        assert "env_value" not in content.lower()


def test_module_contains_no_forbidden_behavior():
    attrs = dir(preview_hash)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
