import json
from dataclasses import asdict
from pathlib import Path

from live_contentops.local_dispatch_payload_preparation_v6 import (
    make_local_dispatch_payload_manifest,
    write_local_dispatch_payloads,
    load_json_packet,
    main,
    _normalize_path,
)


def _decision():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_OPERATOR_DISPATCH_REVIEW_DECISION_FROM_PREFLIGHT_V0",
        "operator_dispatch_review_decision_packet_id": "operator_dispatch_review_decision_packet_abc123",
        "operator_dispatch_decision_id": "operator_dispatch_decision_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T00:00:00+07:00",
        "local_dispatch_preflight_id": "local_dispatch_preflight_abc123",
        "local_dispatch_preflight_sha256": "preflight_sha256_xyz",
        "local_active_outbox_manifest_id": "local_active_outbox_manifest_abc123",
        "operator_active_outbox_review_decision_id": "operator_active_outbox_review_decision_abc123",
        "active_outbox_eligibility_id": "active_outbox_eligibility_abc123",
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
        "reviewed_active_outbox_entries": [
            "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json",
            "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json"
        ],
        "reviewed_active_outbox_entry_hashes": {
            "a:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": "h1",
            "a:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": "h2"
        },
        "reviewed_active_outbox_payload_files": [
            "A:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md",
            "A:/outbox/sample-title-grounding-analysis_xyz/discord_payload.md"
        ],
        "reviewed_active_outbox_payload_file_hashes": {
            "a:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md": "a659cc763b018861df43d4617a2241b1ea407c08a90da3084ba37f375001a182",
            "a:/outbox/sample-title-grounding-analysis_xyz/discord_payload.md": "06b005118749e7a858e38d9dc100d0f7300c082729a6da304ba37f375001a182",
        },
        "combined_payload_hash": "29cf1251e60055d78001ba1617a2241b1ea407c08a90da308ba37f375001a182",
        "decision": "approve_dispatch_payload_preparation",
        "approval_phrase": "APPROVE_LOCAL_DISPATCH_PAYLOAD_PREPARATION_ONLY_NOT_SEND",
        "approval_scope": "dispatch_payload_preparation_only",
        "dispatch_payload_preparation_approved": True,
        "dispatch_review_decision_available": True,
        "dispatch_payload_created": False,
        "approval_for_dispatch": True,
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


def _substack_entry():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_LOCAL_ACTIVE_OUTBOX_CREATION_FROM_OPERATOR_REVIEW_DECISION_V0",
        "active_outbox_entry_id": "active_outbox_entry_substack_abc123",
        "platform": "substack",
        "payload_file": "A:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md",
        "payload_sha256": "a659cc763b018861df43d4617a2241b1ea407c08a90da3084ba37f375001a182",
        "source_staged_payload_file": "a:/staging/sample-title-grounding-analysis_substack_preview.md",
        "source_staged_payload_sha256": "a659cc763b018861df43d4617a2241b1ea407c08a90da3084ba37f375001a182",
        "combined_payload_hash": "29cf1251e60055d78001ba1617a2241b1ea407c08a90da308ba37f375001a182",
        "operator_active_outbox_review_decision_id": "operator_active_outbox_review_decision_abc123",
        "active_outbox_eligibility_id": "active_outbox_eligibility_abc123",
        "outbox_package_staging_id": "outbox_package_staging_abc123",
        "canonical_slug": "sample-title-grounding-analysis",
        "canonical_title": "Sample Title Grounding Analysis",
        "entry_status": "local_active_outbox_pending_dispatch_review",
        "dispatch_payload_created": False,
        "dispatch_allowed": False,
        "approval_for_dispatch": False,
        "publication_ready": False,
        "public_url": None,
        "public_metrics": None,
        "review_only": True,
        "human_review_required": True,
        "kill_switch_active": True,
        "runtime_truth": False,
        "blockers": [],
        "warnings": [],
    }


def _discord_entry():
    val = _substack_entry()
    val["platform"] = "discord"
    val["payload_file"] = "A:/outbox/sample-title-grounding-analysis_xyz/discord_payload.md"
    val["payload_sha256"] = "06b005118749e7a858e38d9dc100d0f7300c082729a6da304ba37f375001a182"
    val["source_staged_payload_file"] = "a:/staging/sample-title-grounding-analysis_discord_preview.md"
    val["source_staged_payload_sha256"] = "06b005118749e7a858e38d9dc100d0f7300c082729a6da304ba37f375001a182"
    return val


def _preview_texts():
    return {
        "A:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md": "# Sample Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nSafe body content.",
        "A:/outbox/sample-title-grounding-analysis_xyz/discord_payload.md": "LOCAL PREVIEW ONLY - NOT APPROVED FOR DISCORD DISPATCH\nSafe discord content.",
    }


def _entry_paths():
    return [
        Path("A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json"),
        Path("A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json"),
    ]


def _payload_paths():
    return [
        Path("A:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md"),
        Path("A:/outbox/sample-title-grounding-analysis_xyz/discord_payload.md"),
    ]


def _assert_no_public_state(packet):
    assert packet.dispatch_execution_payload_created is False
    assert packet.live_send_request_created is False
    assert packet.approval_for_live_dispatch is False
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


def test_valid_inputs_emits_payload_preparation_manifest_and_files(tmp_path):
    dec = _decision()
    epaths = _entry_paths()
    epackets = {
        "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": _substack_entry(),
        "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": _discord_entry()
    }
    ppaths = _payload_paths()
    texts = _preview_texts()
    
    # Overwrite decision file hashes
    import hashlib
    h1 = hashlib.sha256(texts["A:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md"].encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(texts["A:/outbox/sample-title-grounding-analysis_xyz/discord_payload.md"].encode("utf-8")).hexdigest()
    
    dec["reviewed_active_outbox_payload_file_hashes"] = {
        _normalize_path(ppaths[0]): h1,
        _normalize_path(ppaths[1]): h2
    }
    
    epackets["A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json"]["payload_sha256"] = h1
    epackets["A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json"]["payload_sha256"] = h2
    
    manifest = make_local_dispatch_payload_manifest(dec, epaths, epackets, ppaths, texts, tmp_path)
    assert manifest.local_dispatch_payload_prepared is True
    assert not manifest.blockers
    
    # Write and check files
    manifest_path = write_local_dispatch_payloads(manifest, dec, epaths, epackets, ppaths, texts, tmp_path)
    assert manifest_path.exists()
    
    # Verify file existence and contents
    payload_dir = Path(manifest.dispatch_payload_dir)
    assert (payload_dir / "substack_dispatch_payload.md").exists()
    assert (payload_dir / "discord_dispatch_payload.md").exists()
    
    substack_json_file = payload_dir / "substack_dispatch_payload.json"
    assert substack_json_file.exists()
    discord_json_file = payload_dir / "discord_dispatch_payload.json"
    assert discord_json_file.exists()
    
    # Recomputed hashes comparison
    h_sub = hashlib.sha256((payload_dir / "substack_dispatch_payload.md").read_bytes()).hexdigest()
    assert h_sub == h1
    
    # Ensure JSON files do not leak raw markdown body
    sub_json = json.loads(substack_json_file.read_text(encoding="utf-8"))
    assert sub_json["preparation_status"] == "local_dispatch_payload_pending_supervised_dispatch_gate"
    assert sub_json["dispatch_payload_created"] is True
    assert "Safe body content." not in json.dumps(sub_json)
    
    # Ensure manifest does not leak raw markdown body
    manifest_json = json.loads((payload_dir / "local_dispatch_payload_manifest.json").read_text(encoding="utf-8"))
    assert "Safe body content." not in json.dumps(manifest_json)
    
    _assert_no_public_state(manifest)


def test_wrong_decision_task_label_fails_closed():
    dec = _decision()
    dec["task_label"] = "wrong"
    
    epackets = {
        "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": _substack_entry(),
        "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": _discord_entry()
    }
    manifest = make_local_dispatch_payload_manifest(dec, _entry_paths(), epackets, _payload_paths(), _preview_texts(), Path("A:/"))
    assert manifest.local_dispatch_payload_prepared is False
    assert "decision_task_label_invalid" in manifest.blockers


def test_decision_packet_eligibility_failures():
    for fld, val in [
        ("dispatch_review_decision_available", False),
        ("dispatch_payload_preparation_approved", False),
        ("approval_for_dispatch", False),
        ("dispatch_payload_created", True),
        ("blockers", ["some_blocker"]),
        ("publication_ready", True),
        ("public_url", "https://example.invalid"),
    ]:
        dec = _decision()
        dec[fld] = val
        
        epackets = {
            "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": _substack_entry(),
            "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": _discord_entry()
        }
        manifest = make_local_dispatch_payload_manifest(dec, _entry_paths(), epackets, _payload_paths(), _preview_texts(), Path("A:/"))
        assert manifest.local_dispatch_payload_prepared is False
        assert manifest.blockers


def test_entry_path_matching_failures():
    # Order mismatch
    epaths = [
        Path("A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json"),
        Path("A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json"),
    ]
    epackets = {
        "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": _substack_entry(),
        "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": _discord_entry()
    }
    manifest = make_local_dispatch_payload_manifest(_decision(), epaths, epackets, _payload_paths(), _preview_texts(), Path("A:/"))
    assert manifest.local_dispatch_payload_prepared is False
    assert "entry_file_paths_order_mismatch" in manifest.blockers


def test_payload_path_matching_failures():
    # Order mismatch
    ppaths = [
        Path("A:/outbox/sample-title-grounding-analysis_xyz/discord_payload.md"),
        Path("A:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md"),
    ]
    epackets = {
        "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": _substack_entry(),
        "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": _discord_entry()
    }
    manifest = make_local_dispatch_payload_manifest(_decision(), _entry_paths(), epackets, ppaths, _preview_texts(), Path("A:/"))
    assert manifest.local_dispatch_payload_prepared is False
    assert "payload_file_paths_order_mismatch" in manifest.blockers


def test_entry_json_mismatch_failures():
    epackets = {
        "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": _substack_entry(),
        "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": _discord_entry()
    }
    epackets["A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json"]["combined_payload_hash"] = "wrong"
    
    manifest = make_local_dispatch_payload_manifest(_decision(), _entry_paths(), epackets, _payload_paths(), _preview_texts(), Path("A:/"))
    assert manifest.local_dispatch_payload_prepared is False
    assert "entry_substack_combined_payload_hash_mismatch" in manifest.blockers


def test_payload_file_hash_mismatch_fails_closed():
    texts = _preview_texts()
    texts["A:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md"] = "# Sample Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nDifferent content to mismatch hash."
    
    epackets = {
        "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": _substack_entry(),
        "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": _discord_entry()
    }
    manifest = make_local_dispatch_payload_manifest(_decision(), _entry_paths(), epackets, _payload_paths(), texts, Path("A:/"))
    assert manifest.local_dispatch_payload_prepared is False
    assert any("hash_mismatch" in blocker for blocker in manifest.blockers)


def test_preview_file_missing_local_only_warning_fails_closed():
    texts = _preview_texts()
    texts["A:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md"] = "# Title\nSafe content but no warning."
    
    epackets = {
        "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": _substack_entry(),
        "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": _discord_entry()
    }
    manifest = make_local_dispatch_payload_manifest(_decision(), _entry_paths(), epackets, _payload_paths(), texts, Path("A:/"))
    assert manifest.local_dispatch_payload_prepared is False
    assert "staged_substack_warning_missing" in manifest.blockers


def test_secret_marker_in_inputs_fails_closed_and_hashes_cleared():
    # Secret in decision
    dec = _decision()
    dec["canonical_title"] = "my api_key is secret-val"
    epackets = {
        "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": _substack_entry(),
        "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": _discord_entry()
    }
    manifest = make_local_dispatch_payload_manifest(dec, _entry_paths(), epackets, _payload_paths(), _preview_texts(), Path("A:/"))
    assert manifest.local_dispatch_payload_prepared is False
    assert "decision_secret_marker_detected" in manifest.blockers
    assert manifest.operator_dispatch_decision_sha256 == ""
    assert manifest.canonical_title == "[REDACTED_SECRET_MARKER_DETECTED]"

    # Secret in entry JSON
    epackets = {
        "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": _substack_entry(),
        "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": _discord_entry()
    }
    epackets["A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json"]["notes"] = "some private_key check done."
    manifest = make_local_dispatch_payload_manifest(_decision(), _entry_paths(), epackets, _payload_paths(), _preview_texts(), Path("A:/"))
    assert manifest.local_dispatch_payload_prepared is False
    assert "entry_secret_marker_detected" in manifest.blockers


def test_fake_claims_in_preview_fail_closed():
    for claim in ["fake_url", "fake_metrics", "fake_comments", "fake_readiness", "fake_citation"]:
        texts = _preview_texts()
        texts["A:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md"] = f"# Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\n{claim} is supported."
        
        epackets = {
            "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": _substack_entry(),
            "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": _discord_entry()
        }
        manifest = make_local_dispatch_payload_manifest(_decision(), _entry_paths(), epackets, _payload_paths(), texts, Path("A:/"))
        assert manifest.local_dispatch_payload_prepared is False
        assert any(claim in blocker for blocker in manifest.blockers)


def test_financial_advice_in_preview_fails_closed():
    for pattern in ["buy target", "exit strategy", "trading advice", "signal service", "guaranteed prediction"]:
        texts = _preview_texts()
        texts["A:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md"] = f"# Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nsome {pattern} advice."
        
        epackets = {
            "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": _substack_entry(),
            "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": _discord_entry()
        }
        manifest = make_local_dispatch_payload_manifest(_decision(), _entry_paths(), epackets, _payload_paths(), texts, Path("A:/"))
        assert manifest.local_dispatch_payload_prepared is False
        assert "staged_substack_financial_advice_or_signal_framing_detected" in manifest.blockers


def test_no_dispatch_payload_files_are_written_on_blocked_inputs_except_blocked_manifest(tmp_path):
    dec = _decision()
    dec["task_label"] = "wrong"
    
    epackets = {
        "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": _substack_entry(),
        "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": _discord_entry()
    }
    
    manifest = make_local_dispatch_payload_manifest(dec, _entry_paths(), epackets, _payload_paths(), _preview_texts(), tmp_path)
    assert manifest.local_dispatch_payload_prepared is False
    
    manifest_path = write_local_dispatch_payloads(manifest, dec, _entry_paths(), epackets, _payload_paths(), _preview_texts(), tmp_path)
    assert manifest_path.exists()
    
    # Directory for prepared files must not exist because it was blocked
    assert manifest.dispatch_payload_dir == ""


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/local_dispatch_payload_preparation_v6.py").read_text(encoding="utf-8")
    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_cli_writes_deterministic_manifest_and_package_names(tmp_path):
    dec_path = tmp_path / "decision.json"
    
    substack_payload_path = tmp_path / "substack_payload.md"
    substack_payload_path.write_text(_preview_texts()["A:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md"], encoding="utf-8")
    
    discord_payload_path = tmp_path / "discord_payload.md"
    discord_payload_path.write_text(_preview_texts()["A:/outbox/sample-title-grounding-analysis_xyz/discord_payload.md"], encoding="utf-8")
    
    import hashlib
    h1 = hashlib.sha256(substack_payload_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(discord_payload_path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    
    substack_entry_path = tmp_path / "substack_outbox_entry.json"
    substack_entry_data = _substack_entry()
    substack_entry_data["payload_file"] = _normalize_path(substack_payload_path)
    substack_entry_data["payload_sha256"] = h1
    substack_entry_path.write_text(json.dumps(substack_entry_data, sort_keys=True), encoding="utf-8")
    
    discord_entry_path = tmp_path / "discord_outbox_entry.json"
    discord_entry_data = _discord_entry()
    discord_entry_data["payload_file"] = _normalize_path(discord_payload_path)
    discord_entry_data["payload_sha256"] = h2
    discord_entry_path.write_text(json.dumps(discord_entry_data, sort_keys=True), encoding="utf-8")
    
    dec_data = _decision()
    dec_data["reviewed_active_outbox_entries"] = [
        _normalize_path(substack_entry_path),
        _normalize_path(discord_entry_path)
    ]
    dec_data["reviewed_active_outbox_payload_files"] = [
        _normalize_path(substack_payload_path),
        _normalize_path(discord_payload_path)
    ]
    dec_data["reviewed_active_outbox_payload_file_hashes"] = {
        _normalize_path(substack_payload_path): h1,
        _normalize_path(discord_payload_path): h2
    }
    
    dec_path.write_text(json.dumps(dec_data, sort_keys=True), encoding="utf-8")
    
    output_dir = tmp_path / "out"
    assert main([
        str(dec_path),
        "--entry-files", str(substack_entry_path), str(discord_entry_path),
        "--payload-files", str(substack_payload_path), str(discord_payload_path),
        "--output-dir", str(output_dir)
    ]) == 0
    
    first = list(output_dir.glob("**/local_dispatch_payload_manifest.json"))[0]
    first_packet = json.loads(first.read_text(encoding="utf-8"))
    
    assert main([
        str(dec_path),
        "--entry-files", str(substack_entry_path), str(discord_entry_path),
        "--payload-files", str(substack_payload_path), str(discord_payload_path),
        "--output-dir", str(output_dir)
    ]) == 0
    
    second = list(output_dir.glob("**/local_dispatch_payload_manifest.json"))[0]
    second_packet = json.loads(second.read_text(encoding="utf-8"))
    
    assert first_packet["local_dispatch_payload_manifest_id"] == second_packet["local_dispatch_payload_manifest_id"]
    assert first_packet["local_dispatch_payload_prepared"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_LOCAL_DISPATCH_PAYLOAD_PREPARATION_FROM_OPERATOR_DECISION")
    paths = [
        Path("live_contentops/local_dispatch_payload_preparation_v6.py"),
        Path("tests/test_local_dispatch_payload_preparation_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_local_dispatch_payload_manifest.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False
