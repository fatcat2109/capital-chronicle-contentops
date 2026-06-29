import json
from dataclasses import asdict
from pathlib import Path

from live_contentops.local_destination_binding_preflight_v6 import (
    make_local_destination_binding_preflight_packet,
    write_local_destination_binding_preflight_packet,
    main,
    _normalize_path,
)


def _manifest():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_LOCAL_DISPATCH_PAYLOAD_PREPARATION_FROM_OPERATOR_DECISION_V0",
        "local_dispatch_payload_manifest_id": "local_dispatch_payload_manifest_abc123",
        "operator_dispatch_review_decision_packet_id": "operator_dispatch_review_decision_packet_abc123",
        "operator_dispatch_decision_sha256": "operator_dispatch_decision_sha256_xyz",
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
        "canonical_title": "Sample Title Grounding Analysis",
        "canonical_slug": "sample-title-grounding-analysis",
        "dispatch_payload_dir": "A:/prepared_payloads/sample-title-grounding-analysis_xyz",
        "prepared_dispatch_payload_json_files": [
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json",
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json"
        ],
        "prepared_dispatch_payload_markdown_files": [
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md",
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md"
        ],
        "prepared_dispatch_payload_hashes": {
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md": "a659cc763b018861df43d4617a2241b1ea407c08a90da3084ba37f375001a182",
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md": "06b005118749e7a858e38d9dc100d0f7300c082729a6da304ba37f375001a182"
        },
        "source_active_outbox_entry_hashes": {
            "a:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json": "h1",
            "a:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json": "h2"
        },
        "source_active_outbox_payload_hashes": {
            "a:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md": "p1",
            "a:/outbox/sample-title-grounding-analysis_xyz/discord_payload.md": "p2"
        },
        "combined_payload_hash": "29cf1251e60055d78001ba1617a2241b1ea407c08a90da308ba37f375001a182",
        "local_dispatch_payload_prepared": True,
        "dispatch_payload_created": True,
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


def _prepared_substack_json():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_LOCAL_DISPATCH_PAYLOAD_PREPARATION_FROM_OPERATOR_DECISION_V0",
        "prepared_dispatch_payload_id": "prepared_dispatch_payload_substack_abc123",
        "platform": "substack",
        "payload_markdown_file": "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md",
        "payload_markdown_sha256": "a659cc763b018861df43d4617a2241b1ea407c08a90da3084ba37f375001a182",
        "source_active_outbox_entry_file": "a:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json",
        "source_active_outbox_entry_sha256": "h1",
        "source_active_outbox_payload_file": "a:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md",
        "source_active_outbox_payload_sha256": "a659cc763b018861df43d4617a2241b1ea407c08a90da3084ba37f375001a182",
        "combined_payload_hash": "29cf1251e60055d78001ba1617a2241b1ea407c08a90da308ba37f375001a182",
        "operator_dispatch_review_decision_packet_id": "operator_dispatch_review_decision_packet_abc123",
        "local_dispatch_preflight_id": "local_dispatch_preflight_abc123",
        "local_active_outbox_manifest_id": "local_active_outbox_manifest_abc123",
        "canonical_slug": "sample-title-grounding-analysis",
        "canonical_title": "Sample Title Grounding Analysis",
        "preparation_status": "local_dispatch_payload_pending_supervised_dispatch_gate",
        "dispatch_payload_created": True,
        "dispatch_execution_payload_created": False,
        "live_send_request_created": False,
        "approval_for_live_dispatch": False,
        "dispatch_allowed": False,
        "approval_for_publication": False,
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


def _prepared_discord_json():
    val = _prepared_substack_json()
    val["platform"] = "discord"
    val["prepared_dispatch_payload_id"] = "prepared_dispatch_payload_discord_abc123"
    val["payload_markdown_file"] = "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md"
    val["payload_markdown_sha256"] = "06b005118749e7a858e38d9dc100d0f7300c082729a6da304ba37f375001a182"
    val["source_active_outbox_entry_file"] = "a:/outbox/sample-title-grounding-analysis_xyz/discord_outbox_entry.json"
    val["source_active_outbox_entry_sha256"] = "h2"
    val["source_active_outbox_payload_file"] = "a:/outbox/sample-title-grounding-analysis_xyz/discord_payload.md"
    val["source_active_outbox_payload_sha256"] = "06b005118749e7a858e38d9dc100d0f7300c082729a6da304ba37f375001a182"
    return val


def _preview_texts():
    return {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md": "# Sample Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nSafe body content.",
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md": "LOCAL PREVIEW ONLY - NOT APPROVED FOR DISCORD DISPATCH\nSafe discord content.",
    }


def _binding():
    return {
        "schema_version": "6.0.0",
        "destination_binding_id": "destination_binding_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T01:00:00+07:00",
        "local_dispatch_payload_manifest_id": "local_dispatch_payload_manifest_abc123",
        "combined_payload_hash": "29cf1251e60055d78001ba1617a2241b1ea407c08a90da308ba37f375001a182",
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
        "approval_phrase": "BIND_NON_SECRET_DESTINATION_LABELS_ONLY_NOT_LIVE_DISPATCH",
        "approval_scope": "destination_label_preflight_only",
        "notes": "Verified no secrets bound."
    }


def _json_paths():
    return [
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json"),
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json"),
    ]


def _md_paths():
    return [
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"),
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md"),
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


def test_valid_inputs_emits_destination_binding_preflight_packet(tmp_path):
    m = _manifest()
    binding = _binding()
    jpaths = _json_paths()
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    mds = _md_paths()
    texts = _preview_texts()

    # Align hash in manifest and inputs
    import hashlib
    h1 = hashlib.sha256(texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"].encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md"].encode("utf-8")).hexdigest()

    m["prepared_dispatch_payload_hashes"] = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md": h1,
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md": h2
    }
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json"]["payload_markdown_sha256"] = h1
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json"]["source_active_outbox_payload_sha256"] = h1
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json"]["payload_markdown_sha256"] = h2
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json"]["source_active_outbox_payload_sha256"] = h2

    packet = make_local_destination_binding_preflight_packet(m, jpaths, jpackets, mds, texts, binding)
    assert packet.destination_binding_preflight_available is True
    assert packet.eligible_for_supervised_dispatch_gate is True
    assert packet.destination_binding_created is True
    assert not packet.blockers

    # Check output folder writing
    packet_path = write_local_destination_binding_preflight_packet(packet, tmp_path)
    assert packet_path.exists()

    # Re-read and check fields
    data = json.loads(packet_path.read_text(encoding="utf-8"))
    assert data["destination_binding_preflight_available"] is True
    assert data["eligible_for_supervised_dispatch_gate"] is True
    assert data["destination_binding_created"] is True
    assert "Safe body content." not in json.dumps(data)
    _assert_no_public_state(packet)


def test_wrong_manifest_task_label_fails_closed():
    m = _manifest()
    m["task_label"] = "wrong"
    
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    packet = make_local_destination_binding_preflight_packet(m, _json_paths(), jpackets, _md_paths(), _preview_texts(), _binding())
    assert packet.destination_binding_preflight_available is False
    assert packet.destination_binding_created is False
    assert "manifest_task_label_invalid" in packet.blockers


def test_manifest_not_eligible_fields_fail_closed():
    for fld, val in [
        ("local_dispatch_payload_prepared", False),
        ("dispatch_payload_created", False),
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
        m = _manifest()
        m[fld] = val
        
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
        }
        packet = make_local_destination_binding_preflight_packet(m, _json_paths(), jpackets, _md_paths(), _preview_texts(), _binding())
        assert packet.destination_binding_preflight_available is False
        assert packet.destination_binding_created is False
        assert packet.blockers


def test_json_paths_matching_failures():
    # Order mismatch
    jpaths = [
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json"),
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json"),
    ]
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    packet = make_local_destination_binding_preflight_packet(_manifest(), jpaths, jpackets, _md_paths(), _preview_texts(), _binding())
    assert packet.destination_binding_preflight_available is False
    assert "prepared_json_file_paths_order_mismatch" in packet.blockers


def test_markdown_paths_matching_failures():
    # Order mismatch
    mds = [
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md"),
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"),
    ]
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    packet = make_local_destination_binding_preflight_packet(_manifest(), _json_paths(), jpackets, mds, _preview_texts(), _binding())
    assert packet.destination_binding_preflight_available is False
    assert "prepared_markdown_file_paths_order_mismatch" in packet.blockers


def test_prepared_json_mismatches():
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    # Platform mismatch
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json"]["platform"] = "wrong"
    
    packet = make_local_destination_binding_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), _preview_texts(), _binding())
    assert packet.destination_binding_preflight_available is False
    assert any("platform_invalid" in b for b in packet.blockers)


def test_markdown_hash_mismatch():
    texts = _preview_texts()
    texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"] = "# Different\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION"
    
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    packet = make_local_destination_binding_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), texts, _binding())
    assert packet.destination_binding_preflight_available is False
    assert any("hash_mismatch" in b for b in packet.blockers)


def test_missing_local_only_warnings():
    texts = _preview_texts()
    texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"] = "# Title\nSafe content but no warning."
    
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    packet = make_local_destination_binding_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), texts, _binding())
    assert packet.destination_binding_preflight_available is False
    assert "prepared_substack_warning_missing" in packet.blockers


def test_destination_list_mismatches():
    b = _binding()
    # Duplicate platform
    b["destinations"] = [
        {
            "platform": "substack",
            "destination_label": "Production Substack",
            "destination_type": "draft_console_target",
            "destination_binding_kind": "non_secret_label_only",
            "manual_operator_confirmed": True
        },
        {
            "platform": "substack",
            "destination_label": "Another Substack",
            "destination_type": "draft_console_target",
            "destination_binding_kind": "non_secret_label_only",
            "manual_operator_confirmed": True
        }
    ]
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    packet = make_local_destination_binding_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), _preview_texts(), b)
    assert packet.destination_binding_preflight_available is False
    assert "binding_destinations_platforms_mismatch" in packet.blockers


def test_destination_includes_credentials_fails_closed():
    for fld, val in [
        ("channel_id", "12345"),
        ("account_id", "abc"),
        ("app_id", "xyz"),
        ("bot_token", "secret"),
        ("url", "https://discord.invalid/webhook"),
    ]:
        b = _binding()
        b["destinations"][1][fld] = val
        
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
        }
        packet = make_local_destination_binding_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), _preview_texts(), b)
        assert packet.destination_binding_preflight_available is False
        assert any("identifier_detected" in b for b in packet.blockers)


def test_invalid_destination_approval_scope_or_phrase():
    for fld, val in [
        ("approval_phrase", "wrong"),
        ("approval_scope", "wrong"),
    ]:
        b = _binding()
        b[fld] = val
        
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
        }
        packet = make_local_destination_binding_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), _preview_texts(), b)
        assert packet.destination_binding_preflight_available is False
        assert any("binding_approval" in b for b in packet.blockers)


def test_secret_marker_in_manifest_prepared_json_markdown_or_binding_fails_closed():
    # Secret in manifest
    m = _manifest()
    m["canonical_title"] = "my api_key is secret-val"
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    packet = make_local_destination_binding_preflight_packet(m, _json_paths(), jpackets, _md_paths(), _preview_texts(), _binding())
    assert packet.destination_binding_preflight_available is False
    assert "manifest_secret_marker_detected" in packet.blockers
    assert packet.canonical_title == "[REDACTED_SECRET_MARKER_DETECTED]"

    # Secret in prepared JSON
    m = _manifest()
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json"]["canonical_title"] = "some private_key check done."
    packet = make_local_destination_binding_preflight_packet(m, _json_paths(), jpackets, _md_paths(), _preview_texts(), _binding())
    assert packet.destination_binding_preflight_available is False
    assert "prepared_json_secret_marker_detected" in packet.blockers

    # Secret in markdown
    texts = _preview_texts()
    texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"] = "LOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\ntoken is abc"
    packet = make_local_destination_binding_preflight_packet(m, _json_paths(), jpackets, _md_paths(), texts, _binding())
    assert packet.destination_binding_preflight_available is False
    assert "prepared_substack_secret_marker_detected" in packet.blockers


def test_fake_claims_fail_closed():
    for claim in ["fake_url", "fake_metrics", "fake_comments", "fake_readiness", "fake_citation"]:
        texts = _preview_texts()
        texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"] = f"LOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\n{claim} is supported."
        
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
        }
        packet = make_local_destination_binding_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), texts, _binding())
        assert packet.destination_binding_preflight_available is False
        assert any(claim in b for b in packet.blockers)


def test_financial_advice_framing_fails_closed():
    for pattern in ["buy target", "exit strategy", "trading advice", "signal service", "guaranteed prediction"]:
        texts = _preview_texts()
        texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"] = f"LOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nSome {pattern} advice."
        
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
        }
        packet = make_local_destination_binding_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), texts, _binding())
        assert packet.destination_binding_preflight_available is False
        assert "prepared_substack_financial_advice_or_signal_framing_detected" in packet.blockers


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/local_destination_binding_preflight_v6.py").read_text(encoding="utf-8")
    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_cli_writes_deterministic_packet(tmp_path):
    m_path = tmp_path / "manifest.json"
    m_data = _manifest()
    
    substack_md = tmp_path / "substack_dispatch_payload.md"
    substack_md.write_text(_preview_texts()["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"], encoding="utf-8")
    
    discord_md = tmp_path / "discord_dispatch_payload.md"
    discord_md.write_text(_preview_texts()["A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md"], encoding="utf-8")
    
    import hashlib
    h1 = hashlib.sha256(substack_md.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(discord_md.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    
    m_data["prepared_dispatch_payload_markdown_files"] = [
        _normalize_path(substack_md),
        _normalize_path(discord_md)
    ]
    m_data["prepared_dispatch_payload_hashes"] = {
        _normalize_path(substack_md): h1,
        _normalize_path(discord_md): h2
    }
    
    substack_json = tmp_path / "substack_dispatch_payload.json"
    substack_json_data = _prepared_substack_json()
    substack_json_data["payload_markdown_file"] = _normalize_path(substack_md)
    substack_json_data["payload_markdown_sha256"] = h1
    substack_json_data["source_active_outbox_payload_sha256"] = h1
    substack_json.write_text(json.dumps(substack_json_data, sort_keys=True), encoding="utf-8")
    
    discord_json = tmp_path / "discord_dispatch_payload.json"
    discord_json_data = _prepared_discord_json()
    discord_json_data["payload_markdown_file"] = _normalize_path(discord_md)
    discord_json_data["payload_markdown_sha256"] = h2
    discord_json_data["source_active_outbox_payload_sha256"] = h2
    discord_json.write_text(json.dumps(discord_json_data, sort_keys=True), encoding="utf-8")
    
    m_data["prepared_dispatch_payload_json_files"] = [
        _normalize_path(substack_json),
        _normalize_path(discord_json)
    ]
    
    m_path.write_text(json.dumps(m_data, sort_keys=True), encoding="utf-8")
    
    binding_path = tmp_path / "binding.json"
    binding_data = _binding()
    binding_path.write_text(json.dumps(binding_data, sort_keys=True), encoding="utf-8")
    
    output_dir = tmp_path / "out"
    assert main([
        str(m_path),
        "--json-files", str(substack_json), str(discord_json),
        "--markdown-files", str(substack_md), str(discord_md),
        "--destination-binding", str(binding_path),
        "--output-dir", str(output_dir)
    ]) == 0
    
    first = list(output_dir.glob("local_destination_binding_preflight_*.json"))[0]
    first_packet = json.loads(first.read_text(encoding="utf-8"))
    
    assert main([
        str(m_path),
        "--json-files", str(substack_json), str(discord_json),
        "--markdown-files", str(substack_md), str(discord_md),
        "--destination-binding", str(binding_path),
        "--output-dir", str(output_dir)
    ]) == 0
    
    second = list(output_dir.glob("local_destination_binding_preflight_*.json"))[0]
    second_packet = json.loads(second.read_text(encoding="utf-8"))
    
    assert first_packet["local_destination_binding_preflight_id"] == second_packet["local_destination_binding_preflight_id"]
    assert first_packet["destination_binding_preflight_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_LOCAL_DESTINATION_BINDING_PREFLIGHT_FROM_DISPATCH_PAYLOADS")
    paths = [
        Path("live_contentops/local_destination_binding_preflight_v6.py"),
        Path("tests/test_local_destination_binding_preflight_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_local_destination_binding_preflight_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False


def test_malformed_non_object_cli_blocked_test(tmp_path):
    m_path = tmp_path / "manifest.json"
    m_path.write_text("[]", encoding="utf-8")
    
    output_dir = tmp_path / "out"
    exit_code = main([
        str(m_path),
        "--json-files", "A:/a.json", "A:/b.json",
        "--markdown-files", "A:/a.md", "A:/b.md",
        "--destination-binding", "A:/binding.json",
        "--output-dir", str(output_dir)
    ])
    assert exit_code == 1
    
    packets = list(output_dir.glob("local_destination_binding_preflight_*.json"))
    assert len(packets) == 1
    written = json.loads(packets[0].read_text(encoding="utf-8"))
    assert written["destination_binding_preflight_available"] is False
    assert written["eligible_for_supervised_dispatch_gate"] is False
    assert written["destination_binding_created"] is False
    assert written["dispatch_execution_payload_created"] is False
    assert written["live_send_request_created"] is False
    assert written["approval_for_live_dispatch"] is False
    assert written["dispatch_allowed"] is False
