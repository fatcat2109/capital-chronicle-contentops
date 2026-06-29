import json
from dataclasses import asdict
from pathlib import Path

from live_contentops.local_outbox_package_staging_v6 import (
    make_local_outbox_package_staging_manifest,
    write_local_outbox_package,
    load_json_packet,
    main,
    _normalize_path,
)


def _ledger():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_LOCAL_PAYLOAD_REVIEW_HASH_AND_APPROVAL_LEDGER_STRENGTHENING_V0",
        "payload_review_ledger_id": "payload_review_ledger_abc123",
        "approval_intent_id": "approval_intent_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-29T23:00:00+07:00",
        "variant_preview_staging_id": "local_platform_variant_preview_staging_abc123",
        "variant_preview_staging_sha256": "staging_sha256_xyz",
        "metadata_values_review_id": "operator_metadata_values_review_abc123",
        "metadata_values_id": "operator_metadata_values_abc123",
        "metadata_proposal_id": "seo_editorial_metadata_proposal_abc123",
        "source_pack_intake_id": "operator_source_pack_intake_abc123",
        "source_pack_id": "operator_source_pack_abc123",
        "editorial_workflow_id": "accepted_review_editorial_workflow_abc123",
        "canonical_title": "Sample Title Grounding Analysis",
        "canonical_slug": "sample-title-grounding-analysis",
        "reviewed_preview_files": [
            "A:/staging/sample-title-grounding-analysis_substack_preview.md",
            "A:/staging/sample-title-grounding-analysis_discord_preview.md"
        ],
        "preview_file_hashes": {
            "a:/staging/sample-title-grounding-analysis_substack_preview.md": "a659cc763b018861df43d4617a2241b1ea407c08a90da3084ba37f375001a182",
            "a:/staging/sample-title-grounding-analysis_discord_preview.md": "06b005118749e7a858e38d9dc100d0f7300c082729a6da304ba37f375001a182",
        },
        "combined_payload_hash": "29cf1251e60055d78001ba1617a2241b1ea407c08a90da308ba37f375001a182",
        "approval_phrase": "REVIEWED_LOCAL_PREVIEWS_ONLY_NOT_APPROVED_FOR_DISPATCH",
        "approval_scope": "payload_review_hash_only",
        "payload_review_hash_available": True,
        "approval_intent_recorded": True,
        "approval_for_dispatch": False,
        "approval_for_outbox_creation": False,
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
        "A:/staging/sample-title-grounding-analysis_substack_preview.md": "# Sample Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nSafe body content.",
        "A:/staging/sample-title-grounding-analysis_discord_preview.md": "LOCAL PREVIEW ONLY - NOT APPROVED FOR DISCORD DISPATCH\nSafe discord content.",
    }


def _paths():
    return [
        Path("A:/staging/sample-title-grounding-analysis_substack_preview.md"),
        Path("A:/staging/sample-title-grounding-analysis_discord_preview.md"),
    ]


def _assert_no_public_state(packet):
    assert packet.active_outbox_entry_created is False
    assert packet.approval_for_dispatch is False
    assert packet.approval_for_outbox_creation is False
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


def test_valid_inputs_emits_staging_manifest_and_files(tmp_path):
    ld = _ledger()
    paths = _paths()
    texts = _preview_texts()
    
    # Overwrite the ledger combined_payload_hash to match the recalculated hash in test execution
    # To do so, we temporarily run it, see the computed hash, and then check it
    import hashlib
    sorted_preview_paths = sorted(["a:/staging/sample-title-grounding-analysis_discord_preview.md", "a:/staging/sample-title-grounding-analysis_substack_preview.md"])
    ordered_hashes = [
        hashlib.sha256(texts["A:/staging/sample-title-grounding-analysis_discord_preview.md"].encode("utf-8")).hexdigest(),
        hashlib.sha256(texts["A:/staging/sample-title-grounding-analysis_substack_preview.md"].encode("utf-8")).hexdigest()
    ]
    # Set matching hashes in ledger
    ld["preview_file_hashes"] = {
        "a:/staging/sample-title-grounding-analysis_discord_preview.md": ordered_hashes[0],
        "a:/staging/sample-title-grounding-analysis_substack_preview.md": ordered_hashes[1]
    }
    
    combined_payload_material = {
        "variant_preview_staging_id": ld["variant_preview_staging_id"],
        "ordered_preview_file_paths": sorted_preview_paths,
        "ordered_preview_file_hashes": ordered_hashes,
        "approval_intent_id": ld["approval_intent_id"],
        "approval_phrase": ld["approval_phrase"],
        "approval_scope": ld["approval_scope"],
    }
    ld["combined_payload_hash"] = hashlib.sha256(json.dumps(combined_payload_material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    packet = make_local_outbox_package_staging_manifest(ld, paths, texts, tmp_path)
    assert packet.outbox_package_staged is True
    assert packet.outbox_package_preview_only is True
    assert not packet.blockers
    
    _assert_no_public_state(packet)
    
    manifest_path = write_local_outbox_package(packet, paths, texts, tmp_path)
    assert manifest_path.exists()
    
    # Verify staged files are copied
    package_dir_path = Path(packet.package_dir)
    assert (package_dir_path / "substack_preview.md").exists()
    assert (package_dir_path / "discord_preview.md").exists()
    
    # Assert output does not leak raw markdown body
    dumped = manifest_path.read_text(encoding="utf-8")
    assert "Safe body content." not in dumped


def test_wrong_ledger_task_label_fails_closed(tmp_path):
    ld = _ledger()
    ld["task_label"] = "wrong"
    packet = make_local_outbox_package_staging_manifest(ld, _paths(), _preview_texts(), tmp_path)
    assert packet.outbox_package_staged is False
    assert "ledger_task_label_invalid" in packet.blockers


def test_ledger_packet_eligibility_failures(tmp_path):
    for fld, val in [
        ("payload_review_hash_available", False),
        ("approval_intent_recorded", False),
        ("blockers", ["some_blocker"]),
        ("publication_ready", True),
        ("public_url", "https://example.invalid"),
    ]:
        ld = _ledger()
        ld[fld] = val
        packet = make_local_outbox_package_staging_manifest(ld, _paths(), _preview_texts(), tmp_path)
        assert packet.outbox_package_staged is False
        assert packet.blockers


def test_preview_file_order_mismatch_fails_closed(tmp_path):
    # Swap order in supplied paths
    paths = [
        Path("A:/staging/sample-title-grounding-analysis_discord_preview.md"),
        Path("A:/staging/sample-title-grounding-analysis_substack_preview.md"),
    ]
    packet = make_local_outbox_package_staging_manifest(_ledger(), paths, _preview_texts(), tmp_path)
    assert packet.outbox_package_staged is False
    assert "preview_file_paths_order_mismatch" in packet.blockers


def test_duplicate_preview_file_path_fails_closed(tmp_path):
    paths = [
        Path("A:/staging/sample-title-grounding-analysis_substack_preview.md"),
        Path("A:/staging/sample-title-grounding-analysis_substack_preview.md"),
    ]
    packet = make_local_outbox_package_staging_manifest(_ledger(), paths, _preview_texts(), tmp_path)
    assert packet.outbox_package_staged is False
    assert "preview_file_paths_duplicate_detected" in packet.blockers


def test_extra_preview_file_path_fails_closed(tmp_path):
    paths = _paths() + [Path("A:/staging/extra.md")]
    packet = make_local_outbox_package_staging_manifest(_ledger(), paths, _preview_texts(), tmp_path)
    assert packet.outbox_package_staged is False
    assert "preview_file_paths_count_invalid" in packet.blockers


def test_preview_file_hash_mismatch_fails_closed(tmp_path):
    texts = _preview_texts()
    texts["A:/staging/sample-title-grounding-analysis_substack_preview.md"] = "# Sample Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nDifferent content to mismatch hash."
    packet = make_local_outbox_package_staging_manifest(_ledger(), _paths(), texts, tmp_path)
    assert packet.outbox_package_staged is False
    assert any("hash_mismatch" in blocker for blocker in packet.blockers)


def test_preview_file_missing_local_only_warning_fails_closed(tmp_path):
    texts = _preview_texts()
    texts["A:/staging/sample-title-grounding-analysis_substack_preview.md"] = "# Title\nSafe content but no warning."
    packet = make_local_outbox_package_staging_manifest(_ledger(), _paths(), texts, tmp_path)
    assert packet.outbox_package_staged is False
    assert "preview_substack_warning_missing" in packet.blockers


def test_secret_marker_in_inputs_fails_closed_and_hashes_cleared(tmp_path):
    # Secret in ledger
    ld = _ledger()
    ld["canonical_title"] = "my api_key is secret-val"
    packet = make_local_outbox_package_staging_manifest(ld, _paths(), _preview_texts(), tmp_path)
    assert packet.outbox_package_staged is False
    assert "ledger_secret_marker_detected" in packet.blockers
    assert packet.payload_review_ledger_sha256 == ""
    assert packet.combined_payload_hash == ""
    assert packet.canonical_title == "[REDACTED_SECRET_MARKER_DETECTED]"

    # Secret in preview file
    texts = _preview_texts()
    texts["A:/staging/sample-title-grounding-analysis_substack_preview.md"] = "# Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nbearer secret-token-val"
    packet = make_local_outbox_package_staging_manifest(_ledger(), _paths(), texts, tmp_path)
    assert packet.outbox_package_staged is False
    assert "preview_substack_secret_marker_detected" in packet.blockers
    assert packet.combined_payload_hash == ""


def test_fake_claims_in_preview_fail_closed(tmp_path):
    for claim in ["fake_url", "fake_metrics", "fake_comments", "fake_readiness", "fake_citation"]:
        texts = _preview_texts()
        texts["A:/staging/sample-title-grounding-analysis_substack_preview.md"] = f"# Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\n{claim} is supported."
        packet = make_local_outbox_package_staging_manifest(_ledger(), _paths(), texts, tmp_path)
        assert packet.outbox_package_staged is False
        assert any(claim in blocker for blocker in packet.blockers)


def test_financial_advice_in_preview_fails_closed(tmp_path):
    for pattern in ["buy target", "exit strategy", "trading advice", "signal service", "guaranteed prediction"]:
        texts = _preview_texts()
        texts["A:/staging/sample-title-grounding-analysis_substack_preview.md"] = f"# Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nsome {pattern} advice."
        packet = make_local_outbox_package_staging_manifest(_ledger(), _paths(), texts, tmp_path)
        assert packet.outbox_package_staged is False
        assert "preview_substack_financial_advice_or_signal_framing_detected" in packet.blockers


def test_no_staged_preview_files_are_written_on_blocked_inputs(tmp_path):
    ld = _ledger()
    ld["payload_review_hash_available"] = False
    packet = make_local_outbox_package_staging_manifest(ld, _paths(), _preview_texts(), tmp_path)
    assert packet.outbox_package_staged is False
    manifest_path = write_local_outbox_package(packet, _paths(), _preview_texts(), tmp_path)
    assert manifest_path.exists()
    if packet.package_dir:
        assert not Path(packet.package_dir).exists()


def test_malformed_json_fails_closed(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{bad", encoding="utf-8")
    try:
        load_json_packet(bad, "malformed_payload_review_ledger_json")
    except ValueError as exc:
        assert str(exc) == "malformed_payload_review_ledger_json"
    else:
        raise AssertionError("expected malformed_payload_review_ledger_json")


def test_non_object_json_fails_closed_without_exception_and_cli_returns_1(tmp_path):
    packet = make_local_outbox_package_staging_manifest([], [], {}, tmp_path)
    assert "malformed_payload_review_ledger_json" in packet.blockers
    _assert_no_public_state(packet)
    
    ld_path = tmp_path / "ledger.json"
    ld_path.write_text("[]", encoding="utf-8")
    
    output_dir = tmp_path / "out"
    exit_code = main([str(ld_path), "--preview-files", "A:/a.md", "A:/b.md", "--output-dir", str(output_dir)])
    assert exit_code == 1
    
    packets = list(output_dir.glob("outbox_package_staging_*.json"))
    assert len(packets) == 1
    written = json.loads(packets[0].read_text(encoding="utf-8"))
    assert "malformed_payload_review_ledger_json" in written["blockers"]
    assert written["outbox_package_staged"] is False


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/local_outbox_package_staging_v6.py").read_text(encoding="utf-8")
    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_cli_writes_deterministic_packet(tmp_path):
    # Setup ledger with correct hashes for test paths
    ld_path = tmp_path / "ledger.json"
    
    substack_path = tmp_path / "sample-title-grounding-analysis_substack_preview.md"
    substack_path.write_text(_preview_texts()["A:/staging/sample-title-grounding-analysis_substack_preview.md"], encoding="utf-8")
    
    discord_path = tmp_path / "sample-title-grounding-analysis_discord_preview.md"
    discord_path.write_text(_preview_texts()["A:/staging/sample-title-grounding-analysis_discord_preview.md"], encoding="utf-8")
    
    import hashlib
    sorted_preview_paths = sorted([_normalize_path(discord_path), _normalize_path(substack_path)])
    ordered_hashes = [
        hashlib.sha256(discord_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest(),
        hashlib.sha256(substack_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    ]
    
    ld_data = _ledger()
    ld_data["preview_file_hashes"] = {
        sorted_preview_paths[0]: ordered_hashes[0],
        sorted_preview_paths[1]: ordered_hashes[1]
    }
    ld_data["reviewed_preview_files"] = [
        _normalize_path(substack_path),
        _normalize_path(discord_path)
    ]
    
    combined_payload_material = {
        "variant_preview_staging_id": ld_data["variant_preview_staging_id"],
        "ordered_preview_file_paths": sorted_preview_paths,
        "ordered_preview_file_hashes": ordered_hashes,
        "approval_intent_id": ld_data["approval_intent_id"],
        "approval_phrase": ld_data["approval_phrase"],
        "approval_scope": ld_data["approval_scope"],
    }
    ld_data["combined_payload_hash"] = hashlib.sha256(json.dumps(combined_payload_material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    
    ld_path.write_text(json.dumps(ld_data, sort_keys=True), encoding="utf-8")
    
    output_dir = tmp_path / "out"
    assert main([
        str(ld_path),
        "--preview-files",
        str(substack_path),
        str(discord_path),
        "--output-dir",
        str(output_dir)
    ]) == 0
    
    first = list(output_dir.glob("outbox_package_staging_*.json"))[0]
    first_packet = json.loads(first.read_text(encoding="utf-8"))
    
    assert main([
        str(ld_path),
        "--preview-files",
        str(substack_path),
        str(discord_path),
        "--output-dir",
        str(output_dir)
    ]) == 0
    
    second = list(output_dir.glob("outbox_package_staging_*.json"))[0]
    second_packet = json.loads(second.read_text(encoding="utf-8"))
    
    assert first_packet["outbox_package_staging_id"] == second_packet["outbox_package_staging_id"]
    assert first_packet["outbox_package_staged"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_LOCAL_OUTBOX_PACKAGE_STAGING_FROM_PAYLOAD_REVIEW_LEDGER")
    paths = [
        Path("live_contentops/local_outbox_package_staging_v6.py"),
        Path("tests/test_local_outbox_package_staging_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_outbox_package_staging_manifest.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False
