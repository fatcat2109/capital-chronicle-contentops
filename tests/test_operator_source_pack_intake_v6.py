import json
from dataclasses import asdict
from pathlib import Path

from live_contentops.operator_source_pack_intake_v6 import (
    make_source_pack_intake_packet,
    load_json_packet,
    main,
)


def _workflow():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_ACCEPTED_REVIEW_EDITORIAL_WORKFLOW_PACKET_CONTRACT_V0",
        "editorial_workflow_id": "accepted_review_editorial_workflow_xyz789",
        "source_decision_id": "decision_abc123",
        "source_decision_sha256": "h" * 64,
        "source_candidate_id": "candidate_def456",
        "workflow_status": "EDITORIAL_WORKFLOW_PACKET_READY_FOR_OPERATOR_REVIEW",
        "editorial_workflow_packet_available": True,
        "edit_checklist": ["structure_review_required"],
        "factual_review_queue": ["verify_claims_against_operator_sources"],
        "source_grounding_requirements": ["operator_source_pack_required"],
        "required_operator_actions": ["provide_or_confirm_source_pack"],
        "blockers": [],
        "warnings": [],
        "approved_canonical_article_available": False,
        "publication_ready": False,
        "dispatch_allowed": False,
        "platform_variant_generation_allowed": False,
        "outbox_creation_allowed": False,
        "public_url": None,
        "public_metrics": None,
        "review_only": True,
        "human_review_required": True,
        "kill_switch_active": True,
        "runtime_truth": False,
    }


def _manifest(workflow_id="accepted_review_editorial_workflow_xyz789"):
    return {
        "schema_version": "6.0.0",
        "source_pack_id": "operator_source_pack_xyz789",
        "operator_id": "jim",
        "created_at_manual": "2026-06-29T23:00:00+07:00",
        "source_pack_purpose": "Safe testing of grounding context.",
        "editorial_workflow_id": workflow_id,
        "sources": [
            {
                "source_id": "source_1",
                "source_type": "operator_note",
                "title": "Operator grounding notes",
                "locator": "A:/sources/notes_001.txt",
                "provided_by_operator": True,
                "evidence_role": "thesis_support",
                "notes": "Thesis notes for validation."
            }
        ]
    }


def _assert_no_public_state(packet):
    assert packet.approved_canonical_article_available is False
    assert packet.publication_ready is False
    assert packet.dispatch_allowed is False
    assert packet.platform_variant_generation_allowed is False
    assert packet.outbox_creation_allowed is False
    assert packet.public_url is None
    assert packet.public_metrics is None
    assert packet.review_only is True
    assert packet.human_review_required is True
    assert packet.kill_switch_active is True
    assert packet.runtime_truth is False
    assert packet.generated_citations_allowed is False
    assert packet.citations_verified is False


def test_valid_input_emits_source_pack_intake_packet():
    wf = _workflow()
    mf = _manifest()
    packet = make_source_pack_intake_packet(wf, mf)
    assert packet.source_pack_intake_available is True
    assert packet.source_grounding_available_for_editorial_review is True
    assert not packet.blockers
    assert packet.sources_count == 1
    assert packet.source_ids == ["source_1"]
    assert packet.source_types == ["operator_note"]
    assert packet.evidence_roles == ["thesis_support"]
    _assert_no_public_state(packet)


def test_sources_count_and_fields_deterministic():
    wf = _workflow()
    mf = _manifest()
    mf["sources"].append({
        "source_id": "source_2",
        "source_type": "local_markdown",
        "title": "Draft review helper",
        "locator": "A:/sources/helper.md",
        "provided_by_operator": True,
        "evidence_role": "factual_claim_support",
        "notes": "Factual review reference."
    })
    packet = make_source_pack_intake_packet(wf, mf)
    assert packet.sources_count == 2
    assert packet.source_ids == ["source_1", "source_2"]
    assert packet.source_types == ["operator_note", "local_markdown"]
    assert packet.evidence_roles == ["thesis_support", "factual_claim_support"]


def test_mismatched_editorial_workflow_id_fails_closed():
    wf = _workflow()
    mf = _manifest(workflow_id="different_id")
    packet = make_source_pack_intake_packet(wf, mf)
    assert packet.source_pack_intake_available is False
    assert "manifest_editorial_workflow_id_mismatch" in packet.blockers
    _assert_no_public_state(packet)


def test_missing_required_source_pack_top_level_field_fails_closed():
    wf = _workflow()
    for field in ["schema_version", "source_pack_id", "operator_id", "created_at_manual", "source_pack_purpose", "editorial_workflow_id", "sources"]:
        mf = _manifest()
        del mf[field]
        packet = make_source_pack_intake_packet(wf, mf)
        assert packet.source_pack_intake_available is False
        assert f"manifest_{field}_missing" in packet.blockers


def test_sources_empty_fails_closed():
    wf = _workflow()
    mf = _manifest()
    mf["sources"] = []
    packet = make_source_pack_intake_packet(wf, mf)
    assert packet.source_pack_intake_available is False
    assert "manifest_sources_empty" in packet.blockers


def test_source_item_missing_required_field_fails_closed():
    required_source_fields = ["source_id", "source_type", "title", "locator", "provided_by_operator", "evidence_role", "notes"]
    for field in required_source_fields:
        wf = _workflow()
        mf = _manifest()
        del mf["sources"][0][field]
        packet = make_source_pack_intake_packet(wf, mf)
        assert packet.source_pack_intake_available is False
        assert f"source_item_0_{field}_missing" in packet.blockers


def test_invalid_source_type_fails_closed():
    wf = _workflow()
    mf = _manifest()
    mf["sources"][0]["source_type"] = "invalid_type"
    packet = make_source_pack_intake_packet(wf, mf)
    assert packet.source_pack_intake_available is False
    assert "source_item_0_source_type_invalid" in packet.blockers


def test_invalid_evidence_role_fails_closed():
    wf = _workflow()
    mf = _manifest()
    mf["sources"][0]["evidence_role"] = "invalid_role"
    packet = make_source_pack_intake_packet(wf, mf)
    assert packet.source_pack_intake_available is False
    assert "source_item_0_evidence_role_invalid" in packet.blockers


def test_provided_by_operator_false_fails_closed():
    wf = _workflow()
    mf = _manifest()
    mf["sources"][0]["provided_by_operator"] = False
    packet = make_source_pack_intake_packet(wf, mf)
    assert packet.source_pack_intake_available is False
    assert "source_item_0_provided_by_operator_not_true" in packet.blockers


def test_locator_empty_fails_closed():
    wf = _workflow()
    mf = _manifest()
    mf["sources"][0]["locator"] = ""
    packet = make_source_pack_intake_packet(wf, mf)
    assert packet.source_pack_intake_available is False
    assert "source_item_0_locator_missing" in packet.blockers or "source_item_0_locator_empty" in packet.blockers


def test_editorial_workflow_not_eligible_fails_closed():
    for field, val in [
        ("editorial_workflow_packet_available", False),
        ("workflow_status", "OTHER_STATUS"),
        ("approved_canonical_article_available", True),
        ("publication_ready", True),
        ("dispatch_allowed", True),
        ("platform_variant_generation_allowed", True),
        ("outbox_creation_allowed", True),
        ("public_url", "https://example.invalid/pub"),
        ("public_metrics", {"views": 100}),
        ("review_only", False),
        ("kill_switch_active", False),
        ("runtime_truth", True),
    ]:
        wf = _workflow()
        wf[field] = val
        mf = _manifest()
        packet = make_source_pack_intake_packet(wf, mf)
        assert packet.source_pack_intake_available is False
        assert packet.blockers


def test_malformed_json_fails_closed(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{bad", encoding="utf-8")
    try:
        load_json_packet(bad, "malformed_workflow_json")
    except ValueError as exc:
        assert str(exc) == "malformed_workflow_json"
    else:
        raise AssertionError("expected malformed_workflow_json")


def test_non_object_json_fails_closed_without_exception_and_cli_returns_1(tmp_path):
    packet = make_source_pack_intake_packet([], {})
    assert "malformed_workflow_json" in packet.blockers
    _assert_no_public_state(packet)
    
    wf_path = tmp_path / "workflow.json"
    wf_path.write_text("[]", encoding="utf-8")
    mf_path = tmp_path / "manifest.json"
    mf_path.write_text("{}", encoding="utf-8")
    
    output_dir = tmp_path / "out"
    exit_code = main([str(wf_path), str(mf_path), "--output-dir", str(output_dir)])
    assert exit_code == 1
    
    packets = list(output_dir.glob("operator_source_pack_intake_*.json"))
    assert len(packets) == 1
    written = json.loads(packets[0].read_text(encoding="utf-8"))
    assert "malformed_workflow_json" in written["blockers"]
    assert written["source_pack_intake_available"] is False


def test_secret_like_marker_in_manifest_fails_closed_and_raw_value_not_persisted():
    wf = _workflow()
    mf = _manifest()
    mf["sources"][0]["notes"] = "my api_key is secret-val"
    packet = make_source_pack_intake_packet(wf, mf)
    assert packet.source_pack_intake_available is False
    assert "manifest_secret_marker_detected" in packet.blockers
    
    dumped = json.dumps(asdict(packet), sort_keys=True)
    assert "secret-val" not in dumped
    assert packet.source_pack_purpose == "[REDACTED_SECRET_MARKER_DETECTED]"


def test_fake_citation_verification_or_generated_citation_claim_fails_closed():
    wf = _workflow()
    for claim in ["citations_verified", "generated_citations_allowed", "generated_citations", "citations_verified_true"]:
        mf = _manifest()
        mf["sources"][0]["notes"] = f"Claiming {claim} support here."
        packet = make_source_pack_intake_packet(wf, mf)
        assert packet.source_pack_intake_available is False
        assert any("citations_verified_or_generated" in blocker for blocker in packet.blockers)


def test_fake_public_readiness_or_dispatch_claim_fails_closed():
    wf = _workflow()
    for claim in ["approved", "publication_ready", "dispatch_allowed", "outbox_creation_allowed", "public_url", "public_metrics"]:
        mf = _manifest()
        mf["sources"][0]["notes"] = f"Claiming {claim} status."
        packet = make_source_pack_intake_packet(wf, mf)
        assert packet.source_pack_intake_available is False
        assert any(claim in blocker for blocker in packet.blockers)


def test_output_packet_does_not_copy_raw_source_body_content():
    wf = _workflow()
    mf = _manifest()
    mf["sources"][0]["notes"] = "LONG RAW SOURCE CONTENT BODY TEXT"
    packet = make_source_pack_intake_packet(wf, mf)
    dumped = json.dumps(asdict(packet), sort_keys=True)
    assert "LONG RAW SOURCE CONTENT BODY TEXT" not in dumped


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/operator_source_pack_intake_v6.py").read_text(encoding="utf-8")
    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_cli_writes_deterministic_packet(tmp_path):
    wf_path = tmp_path / "workflow.json"
    wf_path.write_text(json.dumps(_workflow(), sort_keys=True), encoding="utf-8")
    mf_path = tmp_path / "manifest.json"
    mf_path.write_text(json.dumps(_manifest(), sort_keys=True), encoding="utf-8")
    
    output_dir = tmp_path / "out"
    assert main([str(wf_path), str(mf_path), "--output-dir", str(output_dir)]) == 0
    first = list(output_dir.glob("operator_source_pack_intake_*.json"))[0]
    first_packet = json.loads(first.read_text(encoding="utf-8"))
    
    assert main([str(wf_path), str(mf_path), "--output-dir", str(output_dir)]) == 0
    second = list(output_dir.glob("operator_source_pack_intake_*.json"))[0]
    second_packet = json.loads(second.read_text(encoding="utf-8"))
    
    assert first_packet["source_pack_intake_id"] == second_packet["source_pack_intake_id"]
    assert first_packet["source_pack_intake_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_OPERATOR_SOURCE_PACK_INTAKE_FOR_EDITORIAL_WORKFLOW")
    paths = [
        Path("live_contentops/operator_source_pack_intake_v6.py"),
        Path("tests/test_operator_source_pack_intake_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_source_pack_intake_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False

def test_public_url_reference_allowed_passes():
    wf = _workflow()
    mf = _manifest()
    mf["sources"][0]["source_type"] = "public_url_reference"
    mf["sources"][0]["locator"] = "https://example.com/some/grounding/page"
    mf["sources"][0]["notes"] = "Safe URL reference for research grounding."
    packet = make_source_pack_intake_packet(wf, mf)
    assert packet.source_pack_intake_available is True
    assert not packet.blockers
    assert packet.source_types == ["public_url_reference"]


def test_explicit_public_url_claim_in_notes_fails_closed():
    wf = _workflow()
    mf = _manifest()
    mf["sources"][0]["source_type"] = "public_url_reference"
    mf["sources"][0]["notes"] = "Here is the public_url of the published post."
    packet = make_source_pack_intake_packet(wf, mf)
    assert packet.source_pack_intake_available is False
    assert any("public_url" in blocker for blocker in packet.blockers)


def test_hard_claims_in_manifest_fail_closed():
    wf = _workflow()
    claims = [
        "publication_ready",
        "dispatch_allowed",
        "outbox_creation_allowed",
        "public_metrics",
        "approved",
        "canonical_public_url",
    ]
    for claim in claims:
        mf = _manifest()
        mf["sources"][0]["notes"] = f"notes claim: {claim}"
        packet = make_source_pack_intake_packet(wf, mf)
        assert packet.source_pack_intake_available is False
        assert any(claim in blocker for blocker in packet.blockers)


def test_secret_in_manifest_hardens_hashes():
    wf = _workflow()
    mf = _manifest()
    mf["sources"][0]["notes"] = "my password is secret-val"
    packet = make_source_pack_intake_packet(wf, mf)
    assert packet.source_pack_intake_available is False
    assert packet.source_pack_manifest_sha256 == ""


def test_secret_in_workflow_hardens_hashes():
    wf = _workflow()
    wf["edit_checklist"].append("my secret_marker password")
    mf = _manifest()
    packet = make_source_pack_intake_packet(wf, mf)
    assert packet.source_pack_intake_available is False
    assert packet.source_editorial_workflow_sha256 == ""