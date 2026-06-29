import json
from dataclasses import asdict
from pathlib import Path

from live_contentops.seo_editorial_metadata_proposal_v6 import (
    make_metadata_proposal_packet,
    load_source_pack_intake_packet,
    main,
)


def _intake():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_OPERATOR_SOURCE_PACK_INTAKE_FOR_EDITORIAL_WORKFLOW_V0",
        "source_pack_intake_id": "operator_source_pack_intake_abc123",
        "source_pack_id": "operator_source_pack_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-29T23:00:00+07:00",
        "source_pack_purpose": "Safe testing grounding.",
        "editorial_workflow_id": "accepted_review_editorial_workflow_abc123",
        "source_editorial_workflow_sha256": "h" * 64,
        "source_pack_manifest_sha256": "m" * 64,
        "sources_count": 1,
        "source_ids": ["source_1"],
        "source_types": ["operator_note"],
        "evidence_roles": ["thesis_support"],
        "source_pack_intake_available": True,
        "source_grounding_available_for_editorial_review": True,
        "generated_citations_allowed": False,
        "citations_verified": False,
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
        "blockers": [],
        "warnings": [],
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


def test_valid_source_pack_intake_emits_proposal_packet():
    packet = make_metadata_proposal_packet(_intake())
    assert packet.metadata_proposal_available is True
    assert not packet.blockers
    assert packet.proposal_status == "METADATA_PROPOSAL_READY_FOR_OPERATOR_REVIEW"
    assert "define_search_intent_later" in packet.seo_review_checklist
    assert "confirm_canonical_article_title_later" in packet.editorial_metadata_checklist
    assert "verify_claims_before_metadata_finalization" in packet.source_grounding_checklist
    assert "no_trading_signal_or_advice_framing" in packet.risk_review_checklist
    assert "review_source_pack_quality" in packet.required_operator_actions
    assert packet.proposed_slug_policy
    assert packet.proposed_title_policy
    assert packet.proposed_description_policy
    assert packet.proposed_keyword_policy
    assert packet.generated_metadata_values is None
    _assert_no_public_state(packet)


def test_wrong_task_label_fails_closed():
    intake = _intake()
    intake["task_label"] = "wrong"
    packet = make_metadata_proposal_packet(intake)
    assert packet.metadata_proposal_available is False
    assert "intake_task_label_invalid" in packet.blockers


def test_source_pack_intake_available_false_fails_closed():
    intake = _intake()
    intake["source_pack_intake_available"] = False
    packet = make_metadata_proposal_packet(intake)
    assert packet.metadata_proposal_available is False
    assert "intake_not_available" in packet.blockers


def test_source_grounding_available_false_fails_closed():
    intake = _intake()
    intake["source_grounding_available_for_editorial_review"] = False
    packet = make_metadata_proposal_packet(intake)
    assert packet.metadata_proposal_available is False
    assert "intake_grounding_not_available" in packet.blockers


def test_blockers_present_fails_closed():
    intake = _intake()
    intake["blockers"] = ["manifest_operator_id_missing"]
    packet = make_metadata_proposal_packet(intake)
    assert packet.metadata_proposal_available is False
    assert "intake_has_blockers" in packet.blockers


def test_citations_verified_true_fails_closed():
    intake = _intake()
    intake["citations_verified"] = True
    packet = make_metadata_proposal_packet(intake)
    assert packet.metadata_proposal_available is False
    assert "intake_citations_verified_not_false" in packet.blockers


def test_generated_citations_allowed_true_fails_closed():
    intake = _intake()
    intake["generated_citations_allowed"] = True
    packet = make_metadata_proposal_packet(intake)
    assert packet.metadata_proposal_available is False
    assert "intake_generated_citations_allowed_not_false" in packet.blockers


def test_public_live_state_true_or_non_null_fails_closed():
    for field, val in [
        ("approved_canonical_article_available", True),
        ("publication_ready", True),
        ("dispatch_allowed", True),
        ("platform_variant_generation_allowed", True),
        ("outbox_creation_allowed", True),
        ("public_url", "https://example.invalid/pub"),
        ("public_metrics", {"views": 1}),
    ]:
        intake = _intake()
        intake[field] = val
        packet = make_metadata_proposal_packet(intake)
        assert packet.metadata_proposal_available is False
        assert packet.blockers


def test_malformed_json_fails_closed(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{bad", encoding="utf-8")
    try:
        load_source_pack_intake_packet(bad)
    except ValueError as exc:
        assert str(exc) == "malformed_source_pack_intake_json"
    else:
        raise AssertionError("expected malformed_source_pack_intake_json")


def test_non_object_json_fails_closed_without_exception_and_cli_returns_1(tmp_path):
    packet = make_metadata_proposal_packet([])
    assert "malformed_source_pack_intake_json" in packet.blockers
    _assert_no_public_state(packet)
    
    intake_path = tmp_path / "intake.json"
    intake_path.write_text("[]", encoding="utf-8")
    output_dir = tmp_path / "out"
    exit_code = main([str(intake_path), "--output-dir", str(output_dir)])
    assert exit_code == 1
    
    packets = list(output_dir.glob("seo_editorial_metadata_proposal_*.json"))
    assert len(packets) == 1
    written = json.loads(packets[0].read_text(encoding="utf-8"))
    assert "malformed_source_pack_intake_json" in written["blockers"]
    assert written["metadata_proposal_available"] is False


def test_missing_ids_or_hashes_fail_closed():
    for key in ["source_pack_id", "editorial_workflow_id", "source_editorial_workflow_sha256", "source_pack_manifest_sha256"]:
        intake = _intake()
        intake[key] = ""
        packet = make_metadata_proposal_packet(intake)
        assert packet.metadata_proposal_available is False
        assert f"intake_{key}_missing" in packet.blockers


def test_sources_count_invalid_fails_closed():
    for val in [0, -1, None, "1"]:
        intake = _intake()
        intake["sources_count"] = val
        packet = make_metadata_proposal_packet(intake)
        assert packet.metadata_proposal_available is False
        assert "intake_sources_count_invalid" in packet.blockers


def test_missing_or_empty_source_arrays_fail_closed():
    for key in ["source_ids", "source_types", "evidence_roles"]:
        for val in [[], None, "not_list"]:
            intake = _intake()
            intake[key] = val
            packet = make_metadata_proposal_packet(intake)
            assert packet.metadata_proposal_available is False
            assert f"intake_{key}_missing_or_empty" in packet.blockers


def test_secret_marker_in_intake_packet_fails_closed_and_raw_value_not_persisted():
    raw = "my token is secret-val"
    intake = _intake()
    intake["source_pack_purpose"] = raw
    packet = make_metadata_proposal_packet(intake)
    assert packet.metadata_proposal_available is False
    assert "intake_secret_marker_detected" in packet.blockers
    
    dumped = json.dumps(asdict(packet), sort_keys=True)
    assert "secret-val" not in dumped
    assert packet.source_pack_intake_sha256 == ""


def test_fake_claims_fail_closed():
    for claim in ["fake_url", "fake_metrics", "fake_comments", "fake_readiness", "fake_citation"]:
        intake = _intake()
        intake["source_pack_purpose"] = f"notes: {claim}"
        packet = make_metadata_proposal_packet(intake)
        assert packet.metadata_proposal_available is False
        assert "intake_secret_marker_detected" in packet.blockers or packet.blockers


def test_output_packet_does_not_copy_raw_source_body_content_or_locator():
    intake = _intake()
    intake["source_pack_purpose"] = "LONG RAW PURPOSE CONTENT TEXT"
    packet = make_metadata_proposal_packet(intake)
    dumped = json.dumps(asdict(packet), sort_keys=True)
    assert "LONG RAW PURPOSE CONTENT TEXT" not in dumped


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/seo_editorial_metadata_proposal_v6.py").read_text(encoding="utf-8")
    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_cli_writes_deterministic_packet(tmp_path):
    intake_path = tmp_path / "intake.json"
    intake_path.write_text(json.dumps(_intake(), sort_keys=True), encoding="utf-8")
    
    output_dir = tmp_path / "out"
    assert main([str(intake_path), "--output-dir", str(output_dir)]) == 0
    first = list(output_dir.glob("seo_editorial_metadata_proposal_*.json"))[0]
    first_packet = json.loads(first.read_text(encoding="utf-8"))
    
    assert main([str(intake_path), "--output-dir", str(output_dir)]) == 0
    second = list(output_dir.glob("seo_editorial_metadata_proposal_*.json"))[0]
    second_packet = json.loads(second.read_text(encoding="utf-8"))
    
    assert first_packet["metadata_proposal_id"] == second_packet["metadata_proposal_id"]
    assert first_packet["metadata_proposal_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_SEO_EDITORIAL_METADATA_PROPOSAL_PACKET_FROM_SOURCE_PACK_INTAKE")
    paths = [
        Path("live_contentops/seo_editorial_metadata_proposal_v6.py"),
        Path("tests/test_seo_editorial_metadata_proposal_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_metadata_proposal_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False
