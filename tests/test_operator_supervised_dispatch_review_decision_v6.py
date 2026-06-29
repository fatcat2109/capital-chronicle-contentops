import json
from dataclasses import asdict
from pathlib import Path

from live_contentops.operator_supervised_dispatch_review_decision_v6 import (
    make_operator_supervised_dispatch_review_decision_packet,
    write_operator_supervised_dispatch_review_decision_packet,
    main,
    _normalize_path,
)


def _preflight():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_LOCAL_DESTINATION_BINDING_PREFLIGHT_FROM_DISPATCH_PAYLOADS_V0",
        "local_destination_binding_preflight_id": "local_destination_binding_preflight_abc123",
        "destination_binding_id": "destination_binding_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T01:00:00+07:00",
        "local_dispatch_payload_manifest_id": "local_dispatch_payload_manifest_abc123",
        "local_dispatch_payload_manifest_sha256": "manifest_sha256_xyz",
        "operator_dispatch_review_decision_packet_id": "operator_dispatch_review_decision_packet_abc123",
        "local_dispatch_preflight_id": "local_dispatch_preflight_abc123",
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
        "canonical_slug": "sample-title-grounding-analysis",
        "canonical_title": "Sample Title Grounding Analysis",
        "prepared_dispatch_payload_json_files": [
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json",
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json"
        ],
        "prepared_dispatch_payload_json_hashes": {
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": "j1",
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": "j2"
        },
        "prepared_dispatch_payload_markdown_files": [
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md",
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md"
        ],
        "prepared_dispatch_payload_markdown_hashes": {
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md": "m1",
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md": "m2"
        },
        "destinations": [
            {
                "platform": "substack",
                "destination_label": "Production Substack",
                "destination_type": "draft_console_target",
                "destination_binding_kind": "non_secret_label_only",
                "manual_operator_confirmed": True
            },
            {
                "platform": "discord",
                "destination_label": "Announcements Channel",
                "destination_type": "webhook_family_target",
                "destination_binding_kind": "non_secret_label_only",
                "manual_operator_confirmed": True
            }
        ],
        "combined_payload_hash": "29cf1251e60055d78001ba1617a2241b1ea407c08a90da308ba37f375001a182",
        "destination_binding_preflight_available": True,
        "eligible_for_supervised_dispatch_gate": True,
        "destination_binding_created": True,
        "dispatch_execution_payload_created": False,
        "live_send_request_created": False,
        "approval_for_live_dispatch": False,
        "approval_for_publication": False,
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


def _decision():
    return {
        "schema_version": "6.0.0",
        "operator_supervised_dispatch_decision_id": "operator_supervised_dispatch_decision_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T01:05:00+07:00",
        "local_destination_binding_preflight_id": "local_destination_binding_preflight_abc123",
        "local_dispatch_payload_manifest_id": "local_dispatch_payload_manifest_abc123",
        "destination_binding_id": "destination_binding_abc123",
        "combined_payload_hash": "29cf1251e60055d78001ba1617a2241b1ea407c08a90da308ba37f375001a182",
        "reviewed_prepared_dispatch_payload_json_files": [
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json",
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json"
        ],
        "reviewed_prepared_dispatch_payload_markdown_files": [
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md",
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md"
        ],
        "reviewed_destinations": [
            {
                "platform": "substack",
                "destination_label": "Production Substack",
                "destination_type": "draft_console_target",
                "destination_binding_kind": "non_secret_label_only",
                "manual_operator_confirmed": True
            },
            {
                "platform": "discord",
                "destination_label": "Announcements Channel",
                "destination_type": "webhook_family_target",
                "destination_binding_kind": "non_secret_label_only",
                "manual_operator_confirmed": True
            }
        ],
        "decision": "approve_dispatch_execution_preparation",
        "approval_phrase": "APPROVE_LOCAL_DISPATCH_EXECUTION_PREPARATION_ONLY_NOT_LIVE_SEND",
        "approval_scope": "dispatch_execution_preparation_only",
        "notes": "Destinations are valid non-secret labels."
    }


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


def test_valid_inputs_emits_review_decision_packet(tmp_path):
    p = _preflight()
    dec = _decision()

    packet = make_operator_supervised_dispatch_review_decision_packet(p, dec)
    assert packet.supervised_dispatch_review_decision_available is True
    assert packet.dispatch_execution_preparation_approved is True
    assert not packet.blockers

    # Check output writing
    packet_path = write_operator_supervised_dispatch_review_decision_packet(packet, tmp_path)
    assert packet_path.exists()

    # Re-read and check fields
    data = json.loads(packet_path.read_text(encoding="utf-8"))
    assert data["supervised_dispatch_review_decision_available"] is True
    assert data["dispatch_execution_preparation_approved"] is True
    assert "Destinations are valid non-secret labels." not in json.dumps(data)
    _assert_no_public_state(packet)


def test_wrong_preflight_task_label_fails_closed():
    p = _preflight()
    p["task_label"] = "wrong"
    packet = make_operator_supervised_dispatch_review_decision_packet(p, _decision())
    assert packet.supervised_dispatch_review_decision_available is False
    assert packet.dispatch_execution_preparation_approved is False
    assert "preflight_task_label_invalid" in packet.blockers


def test_preflight_not_eligible_fields_fail_closed():
    for fld, val in [
        ("destination_binding_preflight_available", False),
        ("eligible_for_supervised_dispatch_gate", False),
        ("destination_binding_created", False),
        ("dispatch_execution_payload_created", True),
        ("live_send_request_created", True),
        ("approval_for_live_dispatch", True),
        ("approval_for_publication", True),
        ("approved_canonical_article_available", True),
        ("publication_ready", True),
        ("dispatch_allowed", True),
        ("public_url", "https://example.invalid"),
        ("public_metrics", {"some": "metric"}),
        ("review_only", False),
        ("human_review_required", False),
        ("kill_switch_active", False),
        ("runtime_truth", True),
        ("blockers", ["some_blocker"]),
    ]:
        p = _preflight()
        p[fld] = val
        packet = make_operator_supervised_dispatch_review_decision_packet(p, _decision())
        assert packet.supervised_dispatch_review_decision_available is False
        assert packet.dispatch_execution_preparation_approved is False
        assert packet.blockers


def test_reject_and_defer_fail_closed_with_blockers():
    for decision in ["reject", "defer"]:
        dec = _decision()
        dec["decision"] = decision
        packet = make_operator_supervised_dispatch_review_decision_packet(_preflight(), dec)
        assert packet.supervised_dispatch_review_decision_available is False
        assert packet.dispatch_execution_preparation_approved is False
        assert any(decision in b for b in packet.blockers)


def test_reviewed_jsons_mismatch_fails_closed():
    dec = _decision()
    dec["reviewed_prepared_dispatch_payload_json_files"] = [
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json",
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json"
    ]
    packet = make_operator_supervised_dispatch_review_decision_packet(_preflight(), dec)
    assert packet.supervised_dispatch_review_decision_available is False
    assert "decision_reviewed_prepared_dispatch_payload_json_files_mismatch" in packet.blockers


def test_reviewed_markdown_mismatch_fails_closed():
    dec = _decision()
    dec["reviewed_prepared_dispatch_payload_markdown_files"] = [
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md",
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"
    ]
    packet = make_operator_supervised_dispatch_review_decision_packet(_preflight(), dec)
    assert packet.supervised_dispatch_review_decision_available is False
    assert "decision_reviewed_prepared_dispatch_payload_markdown_files_mismatch" in packet.blockers


def test_reviewed_destinations_mismatch():
    dec = _decision()
    dec["reviewed_destinations"][0]["destination_label"] = "Mismatched"
    packet = make_operator_supervised_dispatch_review_decision_packet(_preflight(), dec)
    assert packet.supervised_dispatch_review_decision_available is False
    assert "decision_reviewed_destinations_mismatch" in packet.blockers


def test_combined_payload_hash_mismatch():
    dec = _decision()
    dec["combined_payload_hash"] = "wrong"
    packet = make_operator_supervised_dispatch_review_decision_packet(_preflight(), dec)
    assert packet.supervised_dispatch_review_decision_available is False
    assert "decision_combined_payload_hash_mismatch" in packet.blockers


def test_invalid_approval_phrase_or_scope():
    for fld, val in [
        ("approval_phrase", "wrong"),
        ("approval_scope", "wrong"),
    ]:
        dec = _decision()
        dec[fld] = val
        packet = make_operator_supervised_dispatch_review_decision_packet(_preflight(), dec)
        assert packet.supervised_dispatch_review_decision_available is False
        assert any("decision_approval" in b for b in packet.blockers)


def test_secret_marker_in_preflight_or_decision_fails_closed():
    # Secret in preflight
    p = _preflight()
    p["canonical_title"] = "my api_key is secret"
    packet = make_operator_supervised_dispatch_review_decision_packet(p, _decision())
    assert packet.supervised_dispatch_review_decision_available is False
    assert "preflight_secret_marker_detected" in packet.blockers
    assert packet.canonical_title == "[REDACTED_SECRET_MARKER_DETECTED]"

    # Secret in decision
    dec = _decision()
    dec["notes"] = "private_key is secret-val"
    packet = make_operator_supervised_dispatch_review_decision_packet(_preflight(), dec)
    assert packet.supervised_dispatch_review_decision_available is False
    assert "decision_secret_marker_detected" in packet.blockers


def test_decision_containing_credentials_fails_closed():
    for fld, val in [
        ("channel_id", "12345"),
        ("account_id", "abc"),
        ("app_id", "xyz"),
        ("bot_token", "secret"),
        ("url", "https://discord.invalid/webhook"),
    ]:
        dec = _decision()
        dec[fld] = val
        packet = make_operator_supervised_dispatch_review_decision_packet(_preflight(), dec)
        assert packet.supervised_dispatch_review_decision_available is False
        assert any("identifier_detected" in b for b in packet.blockers)


def test_fake_claims_fail_closed():
    for claim in ["fake_url", "fake_metrics", "fake_comments", "fake_readiness", "fake_citation"]:
        dec = _decision()
        dec["notes"] = f"Some {claim} note."
        packet = make_operator_supervised_dispatch_review_decision_packet(_preflight(), dec)
        assert packet.supervised_dispatch_review_decision_available is False
        assert any(claim in b for b in packet.blockers)


def test_financial_advice_framing_fails_closed():
    for pattern in ["buy target", "exit strategy", "trading advice", "signal service", "guaranteed prediction"]:
        dec = _decision()
        dec["notes"] = f"Some {pattern} advice."
        packet = make_operator_supervised_dispatch_review_decision_packet(_preflight(), dec)
        assert packet.supervised_dispatch_review_decision_available is False
        assert "decision_financial_advice_or_signal_framing_detected" in packet.blockers


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/operator_supervised_dispatch_review_decision_v6.py").read_text(encoding="utf-8")
    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_cli_writes_deterministic_packet(tmp_path):
    p_path = tmp_path / "preflight.json"
    p_data = _preflight()
    p_path.write_text(json.dumps(p_data, sort_keys=True), encoding="utf-8")
    
    dec_path = tmp_path / "decision.json"
    dec_data = _decision()
    dec_path.write_text(json.dumps(dec_data, sort_keys=True), encoding="utf-8")
    
    output_dir = tmp_path / "out"
    assert main([
        str(p_path),
        str(dec_path),
        "--output-dir", str(output_dir)
    ]) == 0
    
    first = list(output_dir.glob("operator_supervised_dispatch_review_decision_packet_*.json"))[0]
    first_packet = json.loads(first.read_text(encoding="utf-8"))
    
    assert main([
        str(p_path),
        str(dec_path),
        "--output-dir", str(output_dir)
    ]) == 0
    
    second = list(output_dir.glob("operator_supervised_dispatch_review_decision_packet_*.json"))[0]
    second_packet = json.loads(second.read_text(encoding="utf-8"))
    
    assert first_packet["operator_supervised_dispatch_review_decision_packet_id"] == second_packet["operator_supervised_dispatch_review_decision_packet_id"]
    assert first_packet["supervised_dispatch_review_decision_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_OPERATOR_SUPERVISED_DISPATCH_REVIEW_DECISION_FROM_DESTINATION_PREFLIGHT")
    paths = [
        Path("live_contentops/operator_supervised_dispatch_review_decision_v6.py"),
        Path("tests/test_operator_supervised_dispatch_review_decision_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_operator_supervised_dispatch_review_decision_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False


def test_malformed_non_object_cli_blocked_test(tmp_path):
    p_path = tmp_path / "preflight.json"
    p_path.write_text("[]", encoding="utf-8")
    
    output_dir = tmp_path / "out"
    exit_code = main([
        str(p_path),
        "A:/decision.json",
        "--output-dir", str(output_dir)
    ])
    assert exit_code == 1
    
    packets = list(output_dir.glob("operator_supervised_dispatch_review_decision_packet_*.json"))
    assert len(packets) == 1
    written = json.loads(packets[0].read_text(encoding="utf-8"))
    assert written["supervised_dispatch_review_decision_available"] is False
    assert written["dispatch_execution_preparation_approved"] is False
    assert written["dispatch_execution_payload_created"] is False
    assert written["live_send_request_created"] is False
    assert written["approval_for_live_dispatch"] is False
    assert written["dispatch_allowed"] is False
