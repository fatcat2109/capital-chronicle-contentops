import json
from dataclasses import asdict
from pathlib import Path

from live_contentops.local_platform_variant_preview_staging_v6 import (
    make_variant_preview_staging_packet,
    write_variant_preview_files,
    load_json_packet,
    load_markdown,
    main,
)


def _metadata():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_OPERATOR_METADATA_VALUES_INTAKE_FROM_METADATA_PROPOSAL_V0",
        "metadata_values_review_id": "operator_metadata_values_review_abc123",
        "metadata_values_id": "operator_metadata_values_abc123",
        "metadata_proposal_id": "seo_editorial_metadata_proposal_abc123",
        "metadata_proposal_sha256": "h" * 64,
        "source_pack_intake_id": "operator_source_pack_intake_abc123",
        "source_pack_id": "operator_source_pack_abc123",
        "editorial_workflow_id": "accepted_review_editorial_workflow_abc123",
        "canonical_title": "Sample Title Grounding Analysis",
        "canonical_slug": "sample-title-grounding-analysis",
        "meta_description": "Sample meta description that is long enough to pass validation rules.",
        "focus_keywords": ["testing"],
        "editorial_summary": "Sample editorial summary thirty character minimum check.",
        "intended_search_intent": "Intended search intent of the page.",
        "metadata_values_available_for_editorial_review": True,
        "metadata_values_finalized": False,
        "generated_by_llm": False,
        "operator_supplied": True,
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


def _markdown():
    return """# Canonical Title Grounding Analysis

Some safe markdown paragraph text.
"""


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
    assert packet.preview_only is True


def test_valid_input_emits_staging_packet_and_files(tmp_path):
    wf = _metadata()
    md = _markdown()
    packet = make_variant_preview_staging_packet(wf, md, tmp_path)
    assert packet.variant_preview_staging_available is True
    assert packet.variant_previews_generated is True
    assert not packet.blockers
    _assert_no_public_state(packet)

    written = write_variant_preview_files(packet, wf, md, tmp_path)
    assert len(written) == 2
    
    substack_preview = written[0].read_text(encoding="utf-8")
    assert "# Sample Title Grounding Analysis" in substack_preview
    assert "META_DESCRIPTION: Sample meta description" in substack_preview
    assert "Sample editorial summary thirty character minimum check." in substack_preview
    assert "LOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION" in substack_preview
    assert "Canonical Draft Preview" in substack_preview

    discord_preview = written[1].read_text(encoding="utf-8")
    assert "LOCAL PREVIEW ONLY - NOT APPROVED FOR DISCORD DISPATCH" in discord_preview
    assert "Sample Title Grounding Analysis" in discord_preview
    assert "operator_source_pack_abc123" in discord_preview


def test_wrong_metadata_task_label_fails_closed(tmp_path):
    wf = _metadata()
    wf["task_label"] = "wrong"
    packet = make_variant_preview_staging_packet(wf, _markdown(), tmp_path)
    assert packet.variant_preview_staging_available is False
    assert "metadata_task_label_invalid" in packet.blockers


def test_metadata_unavailable_finalized_fails_closed(tmp_path):
    for fld, val in [
        ("metadata_values_available_for_editorial_review", False),
        ("metadata_values_finalized", True),
        ("generated_by_llm", True),
        ("operator_supplied", False),
        ("blockers", ["some_blocker"]),
        ("approved_canonical_article_available", True),
        ("publication_ready", True),
        ("dispatch_allowed", True),
        ("platform_variant_generation_allowed", True),
        ("outbox_creation_allowed", True),
        ("public_url", "https://example.invalid/pub"),
        ("public_metrics", {"views": 1}),
    ]:
        wf = _metadata()
        wf[fld] = val
        packet = make_variant_preview_staging_packet(wf, _markdown(), tmp_path)
        assert packet.variant_preview_staging_available is False
        assert packet.blockers


def test_markdown_missing_or_empty_fails_closed(tmp_path):
    wf = _metadata()
    packet = make_variant_preview_staging_packet(wf, "", tmp_path)
    assert packet.variant_preview_staging_available is False
    assert "markdown_empty" in packet.blockers


def test_secret_marker_in_metadata_fails_closed_and_hash_cleared(tmp_path):
    wf = _metadata()
    wf["meta_description"] = "my api_key is secret-value"
    packet = make_variant_preview_staging_packet(wf, _markdown(), tmp_path)
    assert packet.variant_preview_staging_available is False
    assert "metadata_secret_marker_detected" in packet.blockers
    assert packet.metadata_values_review_sha256 == ""
    assert packet.canonical_title == "[REDACTED_SECRET_MARKER_DETECTED]"


def test_secret_marker_in_markdown_fails_closed_and_hash_cleared(tmp_path):
    wf = _metadata()
    md = "my token is secret-value"
    packet = make_variant_preview_staging_packet(wf, md, tmp_path)
    assert packet.variant_preview_staging_available is False
    assert "markdown_secret_marker_detected" in packet.blockers
    assert packet.metadata_values_review_sha256 == ""


def test_fake_claims_in_markdown_fail_closed(tmp_path):
    for claim in ["fake_url", "fake_metrics", "fake_comments", "fake_readiness", "fake_citation"]:
        wf = _metadata()
        md = f"Claiming {claim} support here."
        packet = make_variant_preview_staging_packet(wf, md, tmp_path)
        assert packet.variant_preview_staging_available is False
        assert any(claim in blocker for blocker in packet.blockers)


def test_financial_advice_in_markdown_fails_closed(tmp_path):
    for pattern in ["buy target", "exit strategy", "trading advice", "signal service", "guaranteed prediction"]:
        wf = _metadata()
        md = f"here is some {pattern} notes"
        packet = make_variant_preview_staging_packet(wf, md, tmp_path)
        assert packet.variant_preview_staging_available is False
        assert "markdown_financial_advice_or_signal_framing_detected" in packet.blockers


def test_live_dispatch_instructions_in_markdown_fail_closed(tmp_path):
    for pattern in ["dispatch_allowed: true", "publish: true", "supervised_dispatch"]:
        wf = _metadata()
        md = f"instructions: {pattern}"
        packet = make_variant_preview_staging_packet(wf, md, tmp_path)
        assert packet.variant_preview_staging_available is False
        assert "markdown_live_dispatch_instructions_detected" in packet.blockers


def test_preview_files_not_written_on_blocked_inputs(tmp_path):
    wf = _metadata()
    wf["metadata_values_available_for_editorial_review"] = False
    packet = make_variant_preview_staging_packet(wf, _markdown(), tmp_path)
    assert packet.variant_preview_staging_available is False
    written = write_variant_preview_files(packet, wf, _markdown(), tmp_path)
    assert len(written) == 0


def test_malformed_json_fails_closed(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{bad", encoding="utf-8")
    try:
        load_json_packet(bad, "malformed_metadata_values_review_json")
    except ValueError as exc:
        assert str(exc) == "malformed_metadata_values_review_json"
    else:
        raise AssertionError("expected malformed_metadata_values_review_json")


def test_non_object_json_fails_closed_without_exception_and_cli_returns_1(tmp_path):
    packet = make_variant_preview_staging_packet([], "", tmp_path)
    assert "malformed_metadata_values_review_json" in packet.blockers
    _assert_no_public_state(packet)
    
    wf_path = tmp_path / "metadata.json"
    wf_path.write_text("[]", encoding="utf-8")
    md_path = tmp_path / "article.md"
    md_path.write_text("# Title\n", encoding="utf-8")
    
    output_dir = tmp_path / "out"
    exit_code = main([str(wf_path), str(md_path), "--output-dir", str(output_dir)])
    assert exit_code == 1
    
    packets = list(output_dir.glob("local_platform_variant_preview_staging_*.json"))
    assert len(packets) == 1
    written = json.loads(packets[0].read_text(encoding="utf-8"))
    assert "malformed_metadata_values_review_json" in written["blockers"]
    assert written["variant_preview_staging_available"] is False


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/local_platform_variant_preview_staging_v6.py").read_text(encoding="utf-8")
    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_cli_writes_deterministic_packet(tmp_path):
    wf_path = tmp_path / "metadata.json"
    wf_path.write_text(json.dumps(_metadata(), sort_keys=True), encoding="utf-8")
    md_path = tmp_path / "article.md"
    md_path.write_text(_markdown(), encoding="utf-8")
    
    output_dir = tmp_path / "out"
    assert main([str(wf_path), str(md_path), "--output-dir", str(output_dir)]) == 0
    first = list(output_dir.glob("local_platform_variant_preview_staging_*.json"))[0]
    first_packet = json.loads(first.read_text(encoding="utf-8"))
    
    assert main([str(wf_path), str(md_path), "--output-dir", str(output_dir)]) == 0
    second = list(output_dir.glob("local_platform_variant_preview_staging_*.json"))[0]
    second_packet = json.loads(second.read_text(encoding="utf-8"))
    
    assert first_packet["variant_preview_staging_id"] == second_packet["variant_preview_staging_id"]
    assert first_packet["variant_preview_staging_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_LOCAL_PLATFORM_VARIANT_PREVIEW_STAGING_FROM_METADATA_VALUES")
    paths = [
        Path("live_contentops/local_platform_variant_preview_staging_v6.py"),
        Path("tests/test_local_platform_variant_preview_staging_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_variant_preview_staging_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False


def test_metadata_fake_claim_title_fails_closed(tmp_path):
    wf = _metadata()
    wf["canonical_title"] = "Fake Title with fake_metrics"
    packet = make_variant_preview_staging_packet(wf, _markdown(), tmp_path)
    assert packet.variant_preview_staging_available is False
    assert any("fake_metrics" in blocker for blocker in packet.blockers)
    
    written = write_variant_preview_files(packet, wf, _markdown(), tmp_path)
    assert len(written) == 0


def test_metadata_public_readiness_fails_closed(tmp_path):
    for fld, claim in [("meta_description", "publication_ready"), ("editorial_summary", "dispatch_allowed")]:
        wf = _metadata()
        wf[fld] = f"Some dummy text with {claim} marker in it."
        packet = make_variant_preview_staging_packet(wf, _markdown(), tmp_path)
        assert packet.variant_preview_staging_available is False
        assert any(claim in blocker for blocker in packet.blockers)


def test_metadata_citation_verification_fails_closed(tmp_path):
    wf = _metadata()
    wf["intended_search_intent"] = "intent with citations_verified indicator"
    packet = make_variant_preview_staging_packet(wf, _markdown(), tmp_path)
    assert packet.variant_preview_staging_available is False
    assert any("citations_verified" in blocker for blocker in packet.blockers)


def test_metadata_financial_advice_fails_closed(tmp_path):
    wf = _metadata()
    wf["focus_keywords"] = ["testing", "trading advice"]
    packet = make_variant_preview_staging_packet(wf, _markdown(), tmp_path)
    assert packet.variant_preview_staging_available is False
    assert "metadata_financial_advice_or_signal_framing_detected" in packet.blockers