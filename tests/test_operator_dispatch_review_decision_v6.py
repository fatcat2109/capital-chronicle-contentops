import json
from dataclasses import asdict
from pathlib import Path

from live_contentops.operator_dispatch_review_decision_v6 import (
    make_operator_dispatch_review_decision_packet,
    write_operator_dispatch_review_decision_packet,
    load_json_packet,
    main,
    _normalize_path,
)


def _preflight():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_LOCAL_DISPATCH_PREFLIGHT_FROM_ACTIVE_OUTBOX_V0",
        "local_dispatch_preflight_id": "local_dispatch_preflight_abc123",
        "local_active_outbox_manifest_id": "local_active_outbox_manifest_abc123",
        "local_active_outbox_manifest_sha256": "manifest_sha256_xyz",
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
        "active_outbox_entries": [
            "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json",
            "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json"
        ],
        "active_outbox_entry_hashes": {
            "a:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": "h1",
            "a:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": "h2"
        },
        "active_outbox_payload_files": [
            "A:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md",
            "A:/outbox/sample-title-grounding-analysis_xyz/discord_payload.md"
        ],
        "active_outbox_payload_file_hashes": {
            "a:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md": "a659cc763b018861df43d4617a2241b1ea407c08a90da3084ba37f375001a182",
            "a:/outbox/sample-title-grounding-analysis_xyz/discord_payload.md": "06b005118749e7a858e38d9dc100d0f7300c082729a6da304ba37f375001a182",
        },
        "combined_payload_hash": "29cf1251e60055d78001ba1617a2241b1ea407c08a90da308ba37f375001a182",
        "dispatch_preflight_available": True,
        "eligible_for_operator_dispatch_review": True,
        "dispatch_payload_created": False,
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


def _decision():
    return {
        "schema_version": "6.0.0",
        "operator_dispatch_decision_id": "operator_dispatch_decision_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T00:00:00+07:00",
        "local_dispatch_preflight_id": "local_dispatch_preflight_abc123",
        "local_active_outbox_manifest_id": "local_active_outbox_manifest_abc123",
        "combined_payload_hash": "29cf1251e60055d78001ba1617a2241b1ea407c08a90da308ba37f375001a182",
        "reviewed_active_outbox_entries": [
            "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json",
            "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json"
        ],
        "reviewed_active_outbox_payload_files": [
            "A:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md",
            "A:/outbox/sample-title-grounding-analysis_xyz/discord_payload.md"
        ],
        "decision": "approve_dispatch_payload_preparation",
        "approval_phrase": "APPROVE_LOCAL_DISPATCH_PAYLOAD_PREPARATION_ONLY_NOT_SEND",
        "approval_scope": "dispatch_payload_preparation_only",
        "notes": "Checks passed.",
    }


def _assert_no_public_state(packet):
    assert packet.dispatch_payload_created is False
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


def test_valid_inputs_emits_dispatch_approval_intent(tmp_path):
    pf = _preflight()
    dec = _decision()
    
    packet = make_operator_dispatch_review_decision_packet(pf, dec)
    assert packet.dispatch_review_decision_available is True
    assert packet.dispatch_payload_preparation_approved is True
    assert packet.approval_for_dispatch is True
    assert not packet.blockers
    
    _assert_no_public_state(packet)
    
    # Assert output does not leak operator notes or raw markdown body
    dumped = json.dumps(asdict(packet))
    assert "Checks passed." not in dumped


def test_invalid_phrase_or_scope_fails_closed():
    for fld, val in [
        ("approval_phrase", "wrong"),
        ("approval_scope", "wrong"),
    ]:
        pf = _preflight()
        dec = _decision()
        dec[fld] = val
        packet = make_operator_dispatch_review_decision_packet(pf, dec)
        assert packet.dispatch_review_decision_available is False
        assert packet.dispatch_payload_preparation_approved is False
        assert any("phrase_or_scope_invalid" in b for b in packet.blockers)


def test_reject_and_defer_fail_closed_with_blockers():
    for dec_val in ["reject", "defer"]:
        pf = _preflight()
        dec = _decision()
        dec["decision"] = dec_val
        packet = make_operator_dispatch_review_decision_packet(pf, dec)
        assert packet.dispatch_review_decision_available is False
        assert packet.dispatch_payload_preparation_approved is False
        assert any(dec_val in blocker for blocker in packet.blockers)


def test_wrong_preflight_task_label_fails_closed():
    pf = _preflight()
    pf["task_label"] = "wrong"
    packet = make_operator_dispatch_review_decision_packet(pf, _decision())
    assert packet.dispatch_review_decision_available is False
    assert "preflight_task_label_invalid" in packet.blockers


def test_preflight_gate_preflight_failures():
    for fld, val in [
        ("dispatch_preflight_available", False),
        ("eligible_for_operator_dispatch_review", False),
        ("blockers", ["some_blocker"]),
        ("publication_ready", True),
        ("public_url", "https://example.invalid"),
    ]:
        pf = _preflight()
        pf[fld] = val
        packet = make_operator_dispatch_review_decision_packet(pf, _decision())
        assert packet.dispatch_review_decision_available is False
        assert packet.blockers


def test_reviewed_entry_file_path_mismatch_fails_closed():
    dec = _decision()
    dec["reviewed_active_outbox_entries"] = [
        "A:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json",
        "A:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json"
    ]
    packet = make_operator_dispatch_review_decision_packet(_preflight(), dec)
    assert packet.dispatch_review_decision_available is False
    assert "decision_reviewed_active_outbox_entries_mismatch" in packet.blockers


def test_reviewed_payload_file_path_mismatch_fails_closed():
    dec = _decision()
    dec["reviewed_active_outbox_payload_files"] = [
        "A:/outbox/sample-title-grounding-analysis_xyz/discord_payload.md",
        "A:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md"
    ]
    packet = make_operator_dispatch_review_decision_packet(_preflight(), dec)
    assert packet.dispatch_review_decision_available is False
    assert "decision_reviewed_active_outbox_payload_files_mismatch" in packet.blockers


def test_combined_payload_hash_mismatch_fails_closed():
    dec = _decision()
    dec["combined_payload_hash"] = "wrong"
    packet = make_operator_dispatch_review_decision_packet(_preflight(), dec)
    assert packet.dispatch_review_decision_available is False
    assert "decision_combined_payload_hash_mismatch" in packet.blockers


def test_secret_marker_in_inputs_fails_closed_and_hashes_cleared():
    # Secret in preflight
    pf = _preflight()
    pf["canonical_title"] = "my api_key is secret-val"
    packet = make_operator_dispatch_review_decision_packet(pf, _decision())
    assert packet.dispatch_review_decision_available is False
    assert "preflight_secret_marker_detected" in packet.blockers
    assert packet.local_dispatch_preflight_sha256 == ""
    assert packet.canonical_title == "[REDACTED_SECRET_MARKER_DETECTED]"

    # Secret in decision
    dec = _decision()
    dec["notes"] = "some bearer secret value"
    packet = make_operator_dispatch_review_decision_packet(_preflight(), dec)
    assert packet.dispatch_review_decision_available is False
    assert "decision_secret_marker_detected" in packet.blockers


def test_fake_claims_in_decision_fail_closed():
    for claim in ["fake_url", "fake_metrics", "fake_comments", "fake_readiness", "fake_citation"]:
        dec = _decision()
        dec["notes"] = f"some {claim} check done."
        packet = make_operator_dispatch_review_decision_packet(_preflight(), dec)
        assert packet.dispatch_review_decision_available is False
        assert any(claim in blocker for blocker in packet.blockers)


def test_financial_advice_in_decision_fails_closed():
    for pattern in ["buy target", "exit strategy", "trading advice", "signal service", "guaranteed prediction"]:
        dec = _decision()
        dec["notes"] = f"some {pattern} framing."
        packet = make_operator_dispatch_review_decision_packet(_preflight(), dec)
        assert packet.dispatch_review_decision_available is False
        assert "decision_financial_advice_or_signal_framing_detected" in packet.blockers


def test_malformed_json_fails_closed(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{bad", encoding="utf-8")
    try:
        load_json_packet(bad, "malformed_operator_dispatch_decision_json")
    except ValueError as exc:
        assert str(exc) == "malformed_operator_dispatch_decision_json"
    else:
        raise AssertionError("expected malformed_operator_dispatch_decision_json")


def test_non_object_json_fails_closed_without_exception_and_cli_returns_1(tmp_path):
    packet = make_operator_dispatch_review_decision_packet([], [])
    assert "malformed_local_dispatch_preflight_json" in packet.blockers
    assert packet.dispatch_review_decision_available is False
    
    pf_path = tmp_path / "preflight.json"
    pf_path.write_text("[]", encoding="utf-8")
    
    dec_path = tmp_path / "decision.json"
    dec_path.write_text("[]", encoding="utf-8")
    
    output_dir = tmp_path / "out"
    exit_code = main([str(pf_path), str(dec_path), "--output-dir", str(output_dir)])
    assert exit_code == 1
    
    packets = list(output_dir.glob("operator_dispatch_review_decision_*.json"))
    assert len(packets) == 1
    written = json.loads(packets[0].read_text(encoding="utf-8"))
    assert "malformed_local_dispatch_preflight_json" in written["blockers"]
    assert written["dispatch_review_decision_available"] is False


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/operator_dispatch_review_decision_v6.py").read_text(encoding="utf-8")
    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_cli_writes_deterministic_packet(tmp_path):
    pf_path = tmp_path / "preflight.json"
    pf_data = _preflight()
    pf_path.write_text(json.dumps(pf_data, sort_keys=True), encoding="utf-8")
    
    dec_path = tmp_path / "decision.json"
    dec_data = _decision()
    dec_path.write_text(json.dumps(dec_data, sort_keys=True), encoding="utf-8")
    
    output_dir = tmp_path / "out"
    assert main([
        str(pf_path),
        str(dec_path),
        "--output-dir",
        str(output_dir)
    ]) == 0
    
    first = list(output_dir.glob("operator_dispatch_review_decision_*.json"))[0]
    first_packet = json.loads(first.read_text(encoding="utf-8"))
    
    assert main([
        str(pf_path),
        str(dec_path),
        "--output-dir",
        str(output_dir)
    ]) == 0
    
    second = list(output_dir.glob("operator_dispatch_review_decision_*.json"))[0]
    second_packet = json.loads(second.read_text(encoding="utf-8"))
    
    assert first_packet["operator_dispatch_review_decision_packet_id"] == second_packet["operator_dispatch_review_decision_packet_id"]
    assert first_packet["dispatch_review_decision_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_OPERATOR_DISPATCH_REVIEW_DECISION_FROM_PREFLIGHT")
    paths = [
        Path("live_contentops/operator_dispatch_review_decision_v6.py"),
        Path("tests/test_operator_dispatch_review_decision_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_operator_dispatch_review_decision_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False
