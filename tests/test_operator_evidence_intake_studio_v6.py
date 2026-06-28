import json
from pathlib import Path
from live_contentops import operator_evidence_intake_studio_v6 as studio


def test_committed_packet_is_blocked():
    out_dir = Path("docs/automation/V6_OPERATOR_EVIDENCE_INTAKE_STUDIO")
    studio.main(["--output-dir", str(out_dir)])
    
    packet_file = out_dir / "operator_evidence_intake_studio_packet.json"
    assert packet_file.exists()
    
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["evidence_complete"] is False
    assert data["dispatch_allowed_now"] is False
    assert data["live_write_allowed_now"] is False
    assert data["approval_valid_for_dispatch"] is False
    assert data["kill_switch_active"] is True
    assert data["network_scope"] == "passive_static_resource"
    assert "google_fonts" in data["declared_external_resources"]
    assert data["offline_fallback_enabled"] is True
    assert data["next_recommended_task"] == "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0"


def test_all_10_slots_exist_in_artifacts():
    out_dir = Path("docs/automation/V6_OPERATOR_EVIDENCE_INTAKE_STUDIO")
    studio.main(["--output-dir", str(out_dir)])
    
    # 1. Authoring template
    template_file = out_dir / "operator_evidence_fixture.authoring_template.json"
    assert template_file.exists()
    template = json.loads(template_file.read_text(encoding="utf-8"))
    assert set(template.keys()) == set(studio.REQUIRED_SLOTS)
    
    # 2. Guidance
    guidance_file = out_dir / "operator_evidence_slot_guidance.json"
    assert guidance_file.exists()
    guidance = json.loads(guidance_file.read_text(encoding="utf-8"))
    assert set(guidance.keys()) == set(studio.REQUIRED_SLOTS)


def test_guidance_forbids_prohibited_patterns():
    rules = studio.get_redaction_rules()
    restricted = rules["restricted_keywords"]
    
    # Assert critical patterns are in list
    assert "webhook" in restricted
    assert "token" in restricted
    assert "cookie" in restricted
    assert "secret" in restricted
    assert "password" in restricted
    assert "appdata" in restricted
    assert "temp" in restricted
    
    # Check compliance categories
    redactions = rules["strict_redactions"]
    assert "financial_advice" in redactions
    assert "fake_citations" in redactions
    assert "webhooks" in redactions


def test_no_sensitive_values_leak_in_output():
    out_dir = Path("docs/automation/V6_OPERATOR_EVIDENCE_INTAKE_STUDIO")
    studio.main(["--output-dir", str(out_dir)])
    
    files = [
        out_dir / "operator_evidence_intake_studio_packet.json",
        out_dir / "operator_evidence_fixture.validation_preview.json",
        out_dir / "operator_evidence_common_rejection_reasons.md",
        out_dir / "operator_evidence_submission_runbook.md",
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
    attrs = dir(studio)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs


def test_synthetic_complete_fixture_does_not_leak_to_git(tmp_path):
    # Simulate a filled fixture in tmp_path
    fixture_data = {slot: ["CLAIM"] if slot in ["factual_claims", "citation_candidates", "supporting_artifacts"] else "VALID_DATA" for slot in studio.REQUIRED_SLOTS}
    # Affirm disclaimer manually
    fixture_data["no_signal_disclosure"] = "Verified: No signals are contained in this content."
    fixture_data["operator_idea_source_ref"] = "docs/sources/verified_fact.pdf"
    
    fixture_file = tmp_path / "operator_evidence_fixture.json"
    with open(fixture_file, "w", encoding="utf-8") as f:
        json.dump(fixture_data, f)
        
    out_dir = tmp_path / "studio_output"
    
    studio.main(["--fixture-file", str(fixture_file), "--output-dir", str(out_dir)])
    
    packet_file = out_dir / "operator_evidence_intake_studio_packet.json"
    assert packet_file.exists()
    
    data = json.loads(packet_file.read_text(encoding="utf-8"))
    assert data["evidence_complete"] is True
    assert data["intake_studio_status"] == "VALIDATION_SUCCESS_READY_FOR_HUMAN_REVIEW"
    
    # Verify that committed docs folder is untouched by this temp validation run
    committed_packet = Path("docs/automation/V6_OPERATOR_EVIDENCE_INTAKE_STUDIO/operator_evidence_intake_studio_packet.json")
    if committed_packet.exists():
        committed_data = json.loads(committed_packet.read_text(encoding="utf-8"))
        assert committed_data["evidence_complete"] is False
