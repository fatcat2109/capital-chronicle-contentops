import json
from pathlib import Path
from live_contentops import project_sources_upload_bundle_v6 as upload_lane


def write_temp_readiness_inputs(tmp_path, missing_bundle=False, **kwargs):
    readiness_bundle = {
        "readiness_evidence_bundle_packet_id": "bundle_fbe34af9e66e",
        "source_supervised_dispatch_readiness_packet_id": "readiness_34edf10af116",
        "unresolved_blockers": ["evidence_incomplete", "operator_idea_source_ref_missing", "note"]
    }
    dispatch_readiness = {
        "supervised_dispatch_readiness_packet_id": "readiness_34edf10af116",
        "readiness_status": "DISPATCH_READINESS_BLOCKED_PENDING_REQUIREMENTS"
    }

    rb_path = tmp_path / "readiness_evidence_bundle_packet.json"
    dr_path = tmp_path / "supervised_dispatch_readiness_packet.json"

    if not missing_bundle:
        rb_path.write_text(json.dumps(readiness_bundle, indent=2), encoding="utf-8")
    dr_path.write_text(json.dumps(dispatch_readiness, indent=2), encoding="utf-8")

    return rb_path, dr_path


def test_missing_artifacts_triggers_blocked_status(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path, missing_bundle=True)
    
    packet, files = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)
    
    assert packet["bundle_status"] == "PROJECT_SOURCES_UPLOAD_BUNDLE_BLOCKED_MISSING_ARTIFACTS"
    assert packet["dispatch_allowed_now"] is False
    assert packet["approval_valid_for_dispatch"] is False
    assert packet["public_postable"] is False


def test_valid_readiness_produces_ready_with_blockers(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path)
    
    packet, files = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)
    
    assert packet["bundle_status"] == "PROJECT_SOURCES_UPLOAD_BUNDLE_READY_WITH_DISPATCH_BLOCKERS"
    assert packet["dispatch_allowed_now"] is False
    assert packet["approval_valid_for_dispatch"] is False
    assert packet["public_postable"] is False
    
    # Verify note is filtered out
    assert "note" not in packet["unresolved_blockers"]
    assert "evidence_incomplete" in packet["unresolved_blockers"]


def test_file_list_contents_and_safety(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path)
    packet, files = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)
    
    for f in files:
        assert not f.startswith("A:")
        assert not f.startswith("C:")
        assert f.endswith(".md") or f.endswith(".json") or f.endswith(".txt")
        assert ".env" not in f
        assert "browser" not in f.lower()
        assert "session" not in f.lower()


def test_new_chat_continuation_starts_with_task_label(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path)
    packet, files = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)
    
    content = upload_lane.generate_new_chat_continuation_markdown(
        packet["bundle_generation_head"], packet["unresolved_blockers"]
    )
    lines = content.strip().splitlines()
    assert lines[0] == "TASK_CONTENTOPS_V6_PROJECT_SOURCES_REFRESH_CONTINUATION_AFTER_READINESS_BUNDLE_V0"
    assert "cc-live-contentops" in content
    assert "master" in content
    assert "Baseline before upload bundle task" in content


def test_replacement_guide_safety_warnings():
    guide = upload_lane.generate_replacement_guide_markdown()
    
    assert "never upload `.env` files" in guide.lower()
    assert "credentials" in guide.lower()
    assert "browser" in guide.lower()
    assert "session" in guide.lower()
    assert "do not delete or modify the master plan" in guide.lower()


def test_current_state_summary_details(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path)
    packet, files = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)
    
    summary = upload_lane.generate_current_state_summary_markdown(
        packet["bundle_generation_head"], packet["unresolved_blockers"]
    )
    
    assert "Baseline before upload bundle task" in summary
    assert "Current generation HEAD" in summary
    assert "master" in summary
    assert upload_lane.TASK_LABEL in summary
    assert "Post-Push Audit Required" in summary


def test_webhook_and_secrets_hygiene(tmp_path):
    rb_path, dr_path = write_temp_readiness_inputs(tmp_path)
    packet, files = upload_lane.materialize_project_sources_upload_bundle_packets(rb_path, dr_path)
    
    # Check templates
    docs = [
        upload_lane.generate_replacement_guide_markdown(),
        upload_lane.generate_new_chat_continuation_markdown(packet["bundle_generation_head"], packet["unresolved_blockers"]),
        upload_lane.generate_current_state_summary_markdown(packet["bundle_generation_head"], packet["unresolved_blockers"]),
        upload_lane.generate_operator_next_actions_markdown(),
        upload_lane.generate_implementation_report_markdown(packet["bundle_status"], packet["bundle_generation_head"]),
        upload_lane.generate_next_task_pointer_markdown(),
        json.dumps(packet)
    ]
    
    for doc in docs:
        assert "discord.com/api/webhooks" not in doc
        assert "http" not in doc or "github.com" in doc or "substack" in doc or "docs/automation" in doc
        assert "token_value" not in doc.lower()
        assert "cookie_value" not in doc.lower()
        assert "secret_key" not in doc.lower()
        assert "env_value" not in doc.lower()


def test_no_forbidden_behavior_in_module():
    attrs = dir(upload_lane)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
