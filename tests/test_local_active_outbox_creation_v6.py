import json
from dataclasses import asdict
from pathlib import Path

from live_contentops.local_active_outbox_creation_v6 import (
    make_local_active_outbox_manifest,
    write_local_active_outbox,
    load_json_packet,
    main,
    _normalize_path,
)


def _decision():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_OPERATOR_ACTIVE_OUTBOX_REVIEW_DECISION_FROM_ELIGIBILITY_GATE_V0",
        "operator_active_outbox_review_decision_id": "operator_active_outbox_review_decision_abc123",
        "operator_review_decision_id": "operator_review_decision_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T00:00:00+07:00",
        "active_outbox_eligibility_id": "active_outbox_eligibility_abc123",
        "active_outbox_eligibility_sha256": "eligibility_sha256_xyz",
        "outbox_package_staging_id": "outbox_package_staging_abc123",
        "payload_review_ledger_id": "payload_review_ledger_abc123",
        "approval_intent_id": "approval_intent_abc123",
        "variant_preview_staging_id": "local_platform_variant_preview_staging_abc123",
        "metadata_values_review_id": "operator_metadata_values_review_abc123",
        "metadata_values_id": "operator_metadata_values_abc123",
        "metadata_proposal_id": "seo_editorial_metadata_proposal_abc123",
        "source_pack_intake_id": "operator_source_pack_intake_abc123",
        "source_pack_id": "operator_source_pack_abc123",
        "editorial_workflow_id": "accepted_review_editorial_workflow_abc123",
        "canonical_title": "Sample Title Grounding Analysis",
        "canonical_slug": "sample-title-grounding-analysis",
        "reviewed_staged_payload_files": [
            "A:/outbox/sample-title-grounding-analysis_xyz/substack_preview.md",
            "A:/outbox/sample-title-grounding-analysis_xyz/discord_preview.md"
        ],
        "reviewed_staged_payload_file_hashes": {
            "a:/outbox/sample-title-grounding-analysis_xyz/substack_preview.md": "a659cc763b018861df43d4617a2241b1ea407c08a90da3084ba37f375001a182",
            "a:/outbox/sample-title-grounding-analysis_xyz/discord_preview.md": "06b005118749e7a858e38d9dc100d0f7300c082729a6da304ba37f375001a182",
        },
        "combined_payload_hash": "29cf1251e60055d78001ba1617a2241b1ea407c08a90da308ba37f375001a182",
        "decision": "approve_active_outbox_creation",
        "approval_phrase": "APPROVE_LOCAL_ACTIVE_OUTBOX_CREATION_ONLY_NOT_DISPATCH",
        "approval_scope": "active_outbox_creation_only",
        "active_outbox_creation_approved": True,
        "active_outbox_creation_decision_available": True,
        "approval_for_outbox_creation": True,
        "active_outbox_entry_created": False,
        "approval_for_dispatch": False,
        "approval_for_publication": False,
        "approved_canonical_article_available": False,
        "publication_ready": False,
        "dispatch_allowed": False,
        "platform_variant_generation_allowed": False,
        "outbox_creation_allowed": False,
        "generated_citations_allowed": False,
        "citations_verified": False,
        "public_url": None,
        "public_metrics": None,
        "review_only": True,
        "human_review_required": True,
        "kill_switch_active": True,
        "runtime_truth": False,
        "blockers": [],
        "warnings": [],
    }


def _preview_texts():
    return {
        "A:/outbox/sample-title-grounding-analysis_xyz/substack_preview.md": "# Sample Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nSafe body content.",
        "A:/outbox/sample-title-grounding-analysis_xyz/discord_preview.md": "LOCAL PREVIEW ONLY - NOT APPROVED FOR DISCORD DISPATCH\nSafe discord content.",
    }


def _paths():
    return [
        Path("A:/outbox/sample-title-grounding-analysis_xyz/substack_preview.md"),
        Path("A:/outbox/sample-title-grounding-analysis_xyz/discord_preview.md"),
    ]


def _assert_no_public_state(packet):
    assert packet.active_outbox_entry_created is True
    assert packet.dispatch_payload_created is False
    assert packet.approval_for_dispatch is False
    assert packet.approval_for_publication is False
    assert packet.approved_canonical_article_available is False
    assert packet.publication_ready is False
    assert packet.dispatch_allowed is False
    assert packet.platform_variant_generation_allowed is False
    assert packet.outbox_creation_allowed is False
    assert packet.generated_citations_allowed is False
    assert packet.citations_verified is False
    assert packet.public_url is None
    assert packet.public_metrics is None
    assert packet.review_only is True
    assert packet.human_review_required is True
    assert packet.kill_switch_active is True
    assert packet.runtime_truth is False


def test_valid_inputs_emits_active_outbox_manifest_and_files(tmp_path):
    dec = _decision()
    paths = _paths()
    texts = _preview_texts()
    
    import hashlib
    h1 = hashlib.sha256(texts["A:/outbox/sample-title-grounding-analysis_xyz/substack_preview.md"].encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(texts["A:/outbox/sample-title-grounding-analysis_xyz/discord_preview.md"].encode("utf-8")).hexdigest()
    
    dec["reviewed_staged_payload_file_hashes"] = {
        _normalize_path(paths[0]): h1,
        _normalize_path(paths[1]): h2
    }
    
    packet = make_local_active_outbox_manifest(dec, paths, texts, tmp_path)
    assert packet.local_active_outbox_created is True
    assert packet.active_outbox_entry_created is True
    assert not packet.blockers
    
    _assert_no_public_state(packet)
    
    manifest_path = write_local_active_outbox(packet, dec, paths, texts, tmp_path)
    assert manifest_path.exists()
    
    # Verify active outbox files are copied
    package_dir_path = Path(packet.active_outbox_dir)
    assert (package_dir_path / "substack_payload.md").exists()
    assert (package_dir_path / "discord_payload.md").exists()
    assert (package_dir_path / "substack_outbox_entry.json").exists()
    assert (package_dir_path / "discord_outbox_entry.json").exists()
    
    # Assert output does not leak raw markdown body
    dumped = manifest_path.read_text(encoding="utf-8")
    assert "Safe body content." not in dumped
    
    entry_dumped = (package_dir_path / "substack_outbox_entry.json").read_text(encoding="utf-8")
    assert "Safe body content." not in entry_dumped


def test_wrong_decision_task_label_fails_closed(tmp_path):
    dec = _decision()
    dec["task_label"] = "wrong"
    packet = make_local_active_outbox_manifest(dec, _paths(), _preview_texts(), tmp_path)
    assert packet.local_active_outbox_created is False
    assert "decision_task_label_invalid" in packet.blockers


def test_decision_packet_eligibility_failures(tmp_path):
    for fld, val in [
        ("active_outbox_creation_decision_available", False),
        ("active_outbox_creation_approved", False),
        ("approval_for_outbox_creation", False),
        ("blockers", ["some_blocker"]),
        ("publication_ready", True),
        ("public_url", "https://example.invalid"),
    ]:
        dec = _decision()
        dec[fld] = val
        packet = make_local_active_outbox_manifest(dec, _paths(), _preview_texts(), tmp_path)
        assert packet.local_active_outbox_created is False
        assert packet.blockers


def test_staged_payload_path_order_mismatch_fails_closed(tmp_path):
    paths = [
        Path("A:/outbox/sample-title-grounding-analysis_xyz/discord_preview.md"),
        Path("A:/outbox/sample-title-grounding-analysis_xyz/substack_preview.md"),
    ]
    packet = make_local_active_outbox_manifest(_decision(), paths, _preview_texts(), tmp_path)
    assert packet.local_active_outbox_created is False
    assert "preview_file_paths_order_mismatch" in packet.blockers


def test_duplicate_staged_payload_path_fails_closed(tmp_path):
    paths = [
        Path("A:/outbox/sample-title-grounding-analysis_xyz/substack_preview.md"),
        Path("A:/outbox/sample-title-grounding-analysis_xyz/substack_preview.md"),
    ]
    packet = make_local_active_outbox_manifest(_decision(), paths, _preview_texts(), tmp_path)
    assert packet.local_active_outbox_created is False
    assert "preview_file_paths_duplicate_detected" in packet.blockers


def test_extra_staged_payload_path_fails_closed(tmp_path):
    paths = _paths() + [Path("A:/outbox/sample-title-grounding-analysis_xyz/extra.md")]
    packet = make_local_active_outbox_manifest(_decision(), paths, _preview_texts(), tmp_path)
    assert packet.local_active_outbox_created is False
    assert "preview_file_paths_count_invalid" in packet.blockers


def test_staged_payload_file_hash_mismatch_fails_closed(tmp_path):
    texts = _preview_texts()
    texts["A:/outbox/sample-title-grounding-analysis_xyz/substack_preview.md"] = "# Sample Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nDifferent content to mismatch hash."
    packet = make_local_active_outbox_manifest(_decision(), _paths(), texts, tmp_path)
    assert packet.local_active_outbox_created is False
    assert any("hash_mismatch" in blocker for blocker in packet.blockers)


def test_preview_file_missing_local_only_warning_fails_closed(tmp_path):
    texts = _preview_texts()
    texts["A:/outbox/sample-title-grounding-analysis_xyz/substack_preview.md"] = "# Title\nSafe content but no warning."
    packet = make_local_active_outbox_manifest(_decision(), _paths(), texts, tmp_path)
    assert packet.local_active_outbox_created is False
    assert "staged_substack_warning_missing" in packet.blockers


def test_secret_marker_in_inputs_fails_closed_and_hashes_cleared(tmp_path):
    # Secret in decision
    dec = _decision()
    dec["canonical_title"] = "my api_key is secret-val"
    packet = make_local_active_outbox_manifest(dec, _paths(), _preview_texts(), tmp_path)
    assert packet.local_active_outbox_created is False
    assert "decision_secret_marker_detected" in packet.blockers
    assert packet.operator_review_decision_sha256 == ""
    assert packet.canonical_title == "[REDACTED_SECRET_MARKER_DETECTED]"

    # Secret in preview file
    texts = _preview_texts()
    texts["A:/outbox/sample-title-grounding-analysis_xyz/substack_preview.md"] = "# Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nbearer secret-token-val"
    packet = make_local_active_outbox_manifest(_decision(), _paths(), texts, tmp_path)
    assert packet.local_active_outbox_created is False
    assert "staged_substack_secret_marker_detected" in packet.blockers


def test_fake_claims_in_preview_fail_closed(tmp_path):
    for claim in ["fake_url", "fake_metrics", "fake_comments", "fake_readiness", "fake_citation"]:
        texts = _preview_texts()
        texts["A:/outbox/sample-title-grounding-analysis_xyz/substack_preview.md"] = f"# Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\n{claim} is supported."
        packet = make_local_active_outbox_manifest(_decision(), _paths(), texts, tmp_path)
        assert packet.local_active_outbox_created is False
        assert any(claim in blocker for blocker in packet.blockers)


def test_financial_advice_in_preview_fails_closed(tmp_path):
    for pattern in ["buy target", "exit strategy", "trading advice", "signal service", "guaranteed prediction"]:
        texts = _preview_texts()
        texts["A:/outbox/sample-title-grounding-analysis_xyz/substack_preview.md"] = f"# Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nsome {pattern} advice."
        packet = make_local_active_outbox_manifest(_decision(), _paths(), texts, tmp_path)
        assert packet.local_active_outbox_created is False
        assert "staged_substack_financial_advice_or_signal_framing_detected" in packet.blockers


def test_no_active_outbox_files_are_written_on_blocked_inputs(tmp_path):
    dec = _decision()
    dec["active_outbox_creation_approved"] = False
    packet = make_local_active_outbox_manifest(dec, _paths(), _preview_texts(), tmp_path)
    assert packet.local_active_outbox_created is False
    manifest_path = write_local_active_outbox(packet, dec, _paths(), _preview_texts(), tmp_path)
    assert manifest_path.exists()
    if packet.active_outbox_dir:
        assert not Path(packet.active_outbox_dir).exists()


def test_malformed_json_fails_closed(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{bad", encoding="utf-8")
    try:
        load_json_packet(bad, "malformed_operator_review_decision_json")
    except ValueError as exc:
        assert str(exc) == "malformed_operator_review_decision_json"
    else:
        raise AssertionError("expected malformed_operator_review_decision_json")


def test_non_object_json_fails_closed_without_exception_and_cli_returns_1(tmp_path):
    packet = make_local_active_outbox_manifest([], [], {}, tmp_path)
    assert "malformed_operator_review_decision_json" in packet.blockers
    assert packet.local_active_outbox_created is False
    
    dec_path = tmp_path / "decision.json"
    dec_path.write_text("[]", encoding="utf-8")
    
    output_dir = tmp_path / "out"
    exit_code = main([str(dec_path), "--staged-files", "A:/a.md", "A:/b.md", "--output-dir", str(output_dir)])
    assert exit_code == 1
    
    packets = list(output_dir.glob("local_active_outbox_manifest_*.json"))
    assert len(packets) == 1
    written = json.loads(packets[0].read_text(encoding="utf-8"))
    assert "malformed_operator_review_decision_json" in written["blockers"]
    assert written["local_active_outbox_created"] is False


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/local_active_outbox_creation_v6.py").read_text(encoding="utf-8")
    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_cli_writes_deterministic_packet(tmp_path):
    # Setup decision with correct hashes for test paths
    dec_path = tmp_path / "decision.json"
    
    substack_path = tmp_path / "substack_preview.md"
    substack_path.write_text(_preview_texts()["A:/outbox/sample-title-grounding-analysis_xyz/substack_preview.md"], encoding="utf-8")
    
    discord_path = tmp_path / "discord_preview.md"
    discord_path.write_text(_preview_texts()["A:/outbox/sample-title-grounding-analysis_xyz/discord_preview.md"], encoding="utf-8")
    
    import hashlib
    h1 = hashlib.sha256(substack_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(discord_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    
    dec_data = _decision()
    dec_data["reviewed_staged_payload_files"] = [
        _normalize_path(substack_path),
        _normalize_path(discord_path)
    ]
    dec_data["reviewed_staged_payload_file_hashes"] = {
        _normalize_path(substack_path): h1,
        _normalize_path(discord_path): h2
    }
    
    dec_path.write_text(json.dumps(dec_data, sort_keys=True), encoding="utf-8")
    
    output_dir = tmp_path / "out"
    assert main([
        str(dec_path),
        "--staged-files",
        str(substack_path),
        str(discord_path),
        "--output-dir",
        str(output_dir)
    ]) == 0
    
    first = list(output_dir.glob("local_active_outbox_manifest_*.json"))[0]
    first_packet = json.loads(first.read_text(encoding="utf-8"))
    
    assert main([
        str(dec_path),
        "--staged-files",
        str(substack_path),
        str(discord_path),
        "--output-dir",
        str(output_dir)
    ]) == 0
    
    second = list(output_dir.glob("local_active_outbox_manifest_*.json"))[0]
    second_packet = json.loads(second.read_text(encoding="utf-8"))
    
    assert first_packet["local_active_outbox_manifest_id"] == second_packet["local_active_outbox_manifest_id"]
    assert first_packet["local_active_outbox_created"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_LOCAL_ACTIVE_OUTBOX_CREATION_FROM_OPERATOR_REVIEW_DECISION")
    paths = [
        Path("live_contentops/local_active_outbox_creation_v6.py"),
        Path("tests/test_local_active_outbox_creation_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_local_active_outbox_manifest.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False
