import json
from dataclasses import asdict
from pathlib import Path

from live_contentops.operator_metadata_values_intake_v6 import (
    make_metadata_values_review_packet,
    load_json_packet,
    main,
)


def _proposal():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_SEO_EDITORIAL_METADATA_PROPOSAL_PACKET_FROM_SOURCE_PACK_INTAKE_V0",
        "metadata_proposal_id": "seo_editorial_metadata_proposal_abc123",
        "source_pack_intake_id": "operator_source_pack_intake_abc123",
        "source_pack_intake_sha256": "h" * 64,
        "source_pack_id": "operator_source_pack_abc123",
        "editorial_workflow_id": "accepted_review_editorial_workflow_abc123",
        "metadata_proposal_available": True,
        "proposal_status": "METADATA_PROPOSAL_READY_FOR_OPERATOR_REVIEW",
        "seo_review_checklist": ["define_search_intent_later"],
        "editorial_metadata_checklist": ["confirm_canonical_article_title_later"],
        "source_grounding_checklist": ["source_pack_review_required"],
        "risk_review_checklist": ["no_fake_urls"],
        "required_operator_actions": ["review_source_pack_quality"],
        "proposed_slug_policy": "lowercase_hyphenated",
        "proposed_title_policy": "reflect_h1",
        "proposed_description_policy": "summarize",
        "proposed_keyword_policy": "align_sources",
        "generated_metadata_values": None,
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


def _values(proposal_id="seo_editorial_metadata_proposal_abc123"):
    return {
        "schema_version": "6.0.0",
        "metadata_values_id": "operator_metadata_values_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-29T23:00:00+07:00",
        "metadata_proposal_id": proposal_id,
        "canonical_title": "Valid Canonical Title with Long String",  # 36 chars
        "canonical_slug": "valid-canonical-slug-with-hyphens",
        "meta_description": "Valid meta description of exact length seventy characters minimum and one eighty maximum.",  # 90 chars
        "focus_keywords": ["testing", "grounding"],
        "editorial_summary": "Valid summary of exact editorial length thirty minimum.",  # 55 chars
        "intended_search_intent": "Understand local draft intake pipelines.",  # 40 chars
        "notes": "Safe notes.",
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
    assert packet.metadata_values_finalized is False
    assert packet.generated_by_llm is False


def test_valid_proposal_and_values_emits_review_packet():
    packet = make_metadata_values_review_packet(_proposal(), _values())
    assert packet.metadata_values_available_for_editorial_review is True
    assert packet.operator_supplied is True
    assert not packet.blockers
    assert packet.canonical_title == "Valid Canonical Title with Long String"
    assert packet.canonical_slug == "valid-canonical-slug-with-hyphens"
    assert packet.meta_description.startswith("Valid meta description")
    assert packet.focus_keywords == ["testing", "grounding"]
    assert packet.editorial_summary.startswith("Valid summary")
    assert packet.intended_search_intent == "Understand local draft intake pipelines."
    _assert_no_public_state(packet)


def test_wrong_proposal_task_label_fails_closed():
    prop = _proposal()
    prop["task_label"] = "wrong"
    packet = make_metadata_values_review_packet(prop, _values())
    assert packet.metadata_values_available_for_editorial_review is False
    assert "proposal_task_label_invalid" in packet.blockers


def test_proposal_not_available_or_blocked_fails_closed():
    for fld, val in [("metadata_proposal_available", False), ("proposal_status", "BLOCKED"), ("blockers", ["some_blocker"])]:
        prop = _proposal()
        prop[fld] = val
        packet = make_metadata_values_review_packet(prop, _values())
        assert packet.metadata_values_available_for_editorial_review is False
        assert packet.blockers


def test_proposal_generated_metadata_values_non_empty_fails_closed():
    prop = _proposal()
    prop["generated_metadata_values"] = {"title": "something"}
    packet = make_metadata_values_review_packet(prop, _values())
    assert packet.metadata_values_available_for_editorial_review is False
    assert "proposal_generated_metadata_values_not_empty" in packet.blockers


def test_metadata_proposal_id_mismatch_fails_closed():
    packet = make_metadata_values_review_packet(_proposal(), _values(proposal_id="mismatch"))
    assert packet.metadata_values_available_for_editorial_review is False
    assert "values_metadata_proposal_id_mismatch" in packet.blockers


def test_missing_required_metadata_values_field_fails_closed():
    for field in ["schema_version", "metadata_values_id", "operator_id", "created_at_manual", "metadata_proposal_id", "canonical_title", "canonical_slug", "meta_description", "focus_keywords", "editorial_summary", "intended_search_intent"]:
        vals = _values()
        del vals[field]
        packet = make_metadata_values_review_packet(_proposal(), vals)
        assert packet.metadata_values_available_for_editorial_review is False
        assert f"values_{field}_missing" in packet.blockers


def test_invalid_slug_format_fails_closed():
    for bad_slug in ["UPPER-CASE", "with spaces", "no_hyphens_allowed_underscore", "http://example.com/slug", "abc-"]:
        vals = _values()
        vals["canonical_slug"] = bad_slug
        packet = make_metadata_values_review_packet(_proposal(), vals)
        assert packet.metadata_values_available_for_editorial_review is False
        assert "values_canonical_slug_format_invalid" in packet.blockers


def test_length_violations_fail_closed():
    # Title too short/long
    v = _values()
    v["canonical_title"] = "Short"
    assert "values_canonical_title_length_invalid" in make_metadata_values_review_packet(_proposal(), v).blockers
    
    # Description too short/long
    v = _values()
    v["meta_description"] = "Short description"
    assert "values_meta_description_length_invalid" in make_metadata_values_review_packet(_proposal(), v).blockers

    # Summary too short/long
    v = _values()
    v["editorial_summary"] = "Short summary"
    assert "values_editorial_summary_length_invalid" in make_metadata_values_review_packet(_proposal(), v).blockers

    # Search intent too short/long
    v = _values()
    v["intended_search_intent"] = "Short"
    assert "values_intended_search_intent_length_invalid" in make_metadata_values_review_packet(_proposal(), v).blockers


def test_focus_keywords_violations_fail_closed():
    for bad_kws in [[], ["a"], ["a" * 70], ["ok"] * 11, "not_list"]:
        v = _values()
        v["focus_keywords"] = bad_kws
        packet = make_metadata_values_review_packet(_proposal(), v)
        assert packet.metadata_values_available_for_editorial_review is False
        assert packet.blockers


def test_malformed_json_fails_closed(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{bad", encoding="utf-8")
    try:
        load_json_packet(bad, "malformed_metadata_proposal_json")
    except ValueError as exc:
        assert str(exc) == "malformed_metadata_proposal_json"
    else:
        raise AssertionError("expected malformed_metadata_proposal_json")


def test_non_object_json_fails_closed_without_exception_and_cli_returns_1(tmp_path):
    packet = make_metadata_values_review_packet([], {})
    assert "malformed_metadata_proposal_json" in packet.blockers
    _assert_no_public_state(packet)
    
    prop_path = tmp_path / "proposal.json"
    prop_path.write_text("[]", encoding="utf-8")
    val_path = tmp_path / "values.json"
    val_path.write_text("{}", encoding="utf-8")
    
    output_dir = tmp_path / "out"
    exit_code = main([str(prop_path), str(val_path), "--output-dir", str(output_dir)])
    assert exit_code == 1
    
    packets = list(output_dir.glob("operator_metadata_values_review_*.json"))
    assert len(packets) == 1
    written = json.loads(packets[0].read_text(encoding="utf-8"))
    assert "malformed_metadata_proposal_json" in written["blockers"]
    assert written["metadata_values_available_for_editorial_review"] is False


def test_secret_marker_in_proposal_or_values_fails_closed_and_raw_value_not_persisted():
    raw = "my token is secret-val"
    prop = _proposal()
    prop["proposed_slug_policy"] = raw
    packet = make_metadata_values_review_packet(prop, _values())
    assert packet.metadata_values_available_for_editorial_review is False
    assert "proposal_secret_marker_detected" in packet.blockers
    assert packet.metadata_proposal_sha256 == ""
    
    v = _values()
    v["notes"] = "password is my-secret-val"
    packet = make_metadata_values_review_packet(_proposal(), v)
    assert packet.metadata_values_available_for_editorial_review is False
    assert "values_secret_marker_detected" in packet.blockers

    dumped = json.dumps(asdict(packet), sort_keys=True)
    assert "my-secret-val" not in dumped


def test_fake_claims_fail_closed():
    for claim in ["fake_url", "fake_metrics", "fake_comments", "fake_readiness", "fake_citation"]:
        v = _values()
        v["notes"] = f"notes: {claim}"
        packet = make_metadata_values_review_packet(_proposal(), v)
        assert packet.metadata_values_available_for_editorial_review is False
        assert any(claim in blocker for blocker in packet.blockers)


def test_financial_advice_or_signal_framing_fails_closed():
    for pattern in ["buy target", "exit strategy", "trading advice", "signal service", "guaranteed prediction"]:
        v = _values()
        v["notes"] = f"here is some {pattern} notes"
        packet = make_metadata_values_review_packet(_proposal(), v)
        assert packet.metadata_values_available_for_editorial_review is False
        assert "values_financial_advice_or_signal_framing_detected" in packet.blockers


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/operator_metadata_values_intake_v6.py").read_text(encoding="utf-8")
    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_cli_writes_deterministic_packet(tmp_path):
    prop_path = tmp_path / "proposal.json"
    prop_path.write_text(json.dumps(_proposal(), sort_keys=True), encoding="utf-8")
    val_path = tmp_path / "values.json"
    val_path.write_text(json.dumps(_values(), sort_keys=True), encoding="utf-8")
    
    output_dir = tmp_path / "out"
    assert main([str(prop_path), str(val_path), "--output-dir", str(output_dir)]) == 0
    first = list(output_dir.glob("operator_metadata_values_review_*.json"))[0]
    first_packet = json.loads(first.read_text(encoding="utf-8"))
    
    assert main([str(prop_path), str(val_path), "--output-dir", str(output_dir)]) == 0
    second = list(output_dir.glob("operator_metadata_values_review_*.json"))[0]
    second_packet = json.loads(second.read_text(encoding="utf-8"))
    
    assert first_packet["metadata_values_review_id"] == second_packet["metadata_values_review_id"]
    assert first_packet["metadata_values_available_for_editorial_review"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_OPERATOR_METADATA_VALUES_INTAKE_FROM_METADATA_PROPOSAL")
    paths = [
        Path("live_contentops/operator_metadata_values_intake_v6.py"),
        Path("tests/test_operator_metadata_values_intake_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_metadata_values_review_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False
