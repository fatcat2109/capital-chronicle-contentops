import json
import hashlib
from dataclasses import asdict
from pathlib import Path

from live_contentops.live_dispatch_readiness_preflight_v6 import (
    make_live_dispatch_readiness_preflight_packet,
    main,
    _normalize_path,
    _canonical_json,
)


def _manifest():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_LOCAL_DISPATCH_EXECUTION_PAYLOAD_PREPARATION_FROM_SUPERVISED_DECISION_V0",
        "local_dispatch_execution_payload_manifest_id": "local_dispatch_execution_payload_manifest_abc123",
        "operator_supervised_dispatch_review_decision_packet_id": "operator_supervised_dispatch_review_decision_packet_abc123",
        "operator_supervised_dispatch_decision_sha256": "decision_sha256_abc123",
        "local_destination_binding_preflight_id": "local_destination_binding_preflight_abc123",
        "local_destination_binding_preflight_sha256": "preflight_sha256_abc123",
        "destination_binding_id": "destination_binding_abc123",
        "local_dispatch_payload_manifest_id": "local_dispatch_payload_manifest_abc123",
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
        "execution_preparation_dir": "A:/prepared_payloads/sample-title-grounding-analysis_xyz",
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
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md": "a659cc763b018861df43d4617a2241b1ea407c08a90da3084ba37f375001a182",
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md": "06b005118749e7a858e38d9dc100d0f7300c082729a6da304ba37f375001a182"
        },
        "execution_preparation_json_files": [
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json",
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json"
        ],
        "execution_preparation_markdown_files": [
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.md",
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.md"
        ],
        "execution_preparation_file_hashes": {
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": "ej1",
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": "ej2",
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.md": "em1",
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.md": "em2"
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
        "local_dispatch_execution_prepared": True,
        "dispatch_execution_payload_created": True,
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


def _execution_substack_json():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_LOCAL_DISPATCH_EXECUTION_PAYLOAD_PREPARATION_FROM_SUPERVISED_DECISION_V0",
        "execution_preparation_payload_id": "execution_preparation_payload_substack_abc123",
        "platform": "substack",
        "preparation_status": "local_dispatch_execution_payload_pending_live_gate",
        "destination": {
            "platform": "substack",
            "destination_label": "Production Substack",
            "destination_type": "draft_console_target",
            "destination_binding_kind": "non_secret_label_only",
            "manual_operator_confirmed": True
        },
        "markdown_snapshot_file": "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.md",
        "markdown_snapshot_sha256": "em1",
        "source_prepared_dispatch_payload_json_file": "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json",
        "source_prepared_dispatch_payload_json_sha256": "j1",
        "source_prepared_dispatch_payload_markdown_file": "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md",
        "source_prepared_dispatch_payload_markdown_sha256": "em1",
        "combined_payload_hash": "29cf1251e60055d78001ba1617a2241b1ea407c08a90da308ba37f375001a182",
        "operator_supervised_dispatch_review_decision_packet_id": "operator_supervised_dispatch_review_decision_packet_abc123",
        "local_destination_binding_preflight_id": "local_destination_binding_preflight_abc123",
        "local_dispatch_payload_manifest_id": "local_dispatch_payload_manifest_abc123",
        "canonical_slug": "sample-title-grounding-analysis",
        "canonical_title": "Sample Title Grounding Analysis",
        "local_dispatch_execution_prepared": True,
        "dispatch_execution_payload_created": True,
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


def _execution_discord_json():
    val = _execution_substack_json()
    val["platform"] = "discord"
    val["execution_preparation_payload_id"] = "execution_preparation_payload_discord_abc123"
    val["destination"] = {
        "platform": "discord",
        "destination_label": "Announcements Channel",
        "destination_type": "webhook_family_target",
        "destination_binding_kind": "non_secret_label_only",
        "manual_operator_confirmed": True
    }
    val["markdown_snapshot_file"] = "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.md"
    val["markdown_snapshot_sha256"] = "em2"
    val["source_prepared_dispatch_payload_json_file"] = "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json"
    val["source_prepared_dispatch_payload_json_sha256"] = "j2"
    val["source_prepared_dispatch_payload_markdown_file"] = "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md"
    val["source_prepared_dispatch_payload_markdown_sha256"] = "em2"
    return val


def _declaration():
    return {
        "schema_version": "6.0.0",
        "live_dispatch_readiness_declaration_id": "live_dispatch_readiness_declaration_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T01:10:00+07:00",
        "local_dispatch_execution_payload_manifest_id": "local_dispatch_execution_payload_manifest_abc123",
        "combined_payload_hash": "29cf1251e60055d78001ba1617a2241b1ea407c08a90da308ba37f375001a182",
        "platform_action_class": "supervised_dispatch_future_gate",
        "dispatch_family": "substack_discord_dispatch_family",
        "reviewed_execution_preparation_json_files": [
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json",
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json"
        ],
        "reviewed_execution_preparation_markdown_files": [
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.md",
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.md"
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
        "official_docs_required": True,
        "credentials_required_later": True,
        "credential_key_names_only": [
            "SUBSTACK_API_KEY_DRAFT_STAGE",
            "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"
        ],
        "destination_binding_required_later": True,
        "endpoint_allowlist_required_later": True,
        "payload_hash_required_later": True,
        "explicit_operator_approval_required_later": True,
        "kill_switch_required": True,
        "decision": "mark_ready_for_future_live_dispatch_gate",
        "approval_phrase": "MARK_READY_FOR_FUTURE_LIVE_DISPATCH_GATE_ONLY_NOT_SEND",
        "approval_scope": "future_live_dispatch_gate_preflight_only",
        "notes": "Verified local build files and key profiles."
    }


def _preview_texts():
    return {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.md": "# Sample Title\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nSafe body.",
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.md": "LOCAL PREVIEW ONLY - NOT APPROVED FOR DISCORD DISPATCH\nSafe discord body.",
    }


def _json_paths():
    return [
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json"),
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json"),
    ]


def _md_paths():
    return [
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.md"),
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.md"),
    ]


def _assert_no_public_state(packet):
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


def _align_hashes(m, dec, jpackets, texts):
    h1 = hashlib.sha256(texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.md"].encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.md"].encode("utf-8")).hexdigest()

    m["prepared_dispatch_payload_markdown_hashes"] = {
        "a:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md": h1,
        "a:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md": h2
    }

    # Align JSON inputs
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json"]["markdown_snapshot_sha256"] = h1
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json"]["source_prepared_dispatch_payload_markdown_sha256"] = h1
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json"]["markdown_snapshot_sha256"] = h2
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json"]["source_prepared_dispatch_payload_markdown_sha256"] = h2

    # Align manifest hashes of the JSON inputs
    comp_j1 = hashlib.sha256(_canonical_json(jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json"]).encode("utf-8")).hexdigest()
    comp_j2 = hashlib.sha256(_canonical_json(jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json"]).encode("utf-8")).hexdigest()

    m["execution_preparation_file_hashes"] = {
        "a:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": comp_j1,
        "a:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": comp_j2,
        "a:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.md": h1,
        "a:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.md": h2
    }

    dec["reviewed_execution_preparation_json_files"] = [
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json",
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json"
    ]
    dec["reviewed_execution_preparation_markdown_files"] = [
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.md",
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.md"
    ]


def test_valid_inputs_emits_readiness_preflight_packet():
    m = _manifest()
    dec = _declaration()
    jpaths = _json_paths()
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": _execution_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": _execution_discord_json()
    }
    mds = _md_paths()
    texts = _preview_texts()

    _align_hashes(m, dec, jpackets, texts)

    packet = make_live_dispatch_readiness_preflight_packet(m, jpaths, jpackets, mds, texts, dec)
    assert packet.live_dispatch_readiness_preflight_available is True
    assert packet.eligible_for_future_live_dispatch_gate is True
    assert packet.live_dispatch_readiness_preflight_approved is True
    assert not packet.blockers
    assert "Safe body." not in json.dumps(asdict(packet))

    _assert_no_public_state(packet)


def test_reject_or_defer_decision_disapproves():
    for val in ["reject", "defer"]:
        m = _manifest()
        dec = _declaration()
        dec["decision"] = val
        dec["approval_phrase"] = "NONE"
        dec["approval_scope"] = "NONE"
        
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": _execution_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": _execution_discord_json()
        }
        _align_hashes(m, dec, jpackets, _preview_texts())
        packet = make_live_dispatch_readiness_preflight_packet(m, _json_paths(), jpackets, _md_paths(), _preview_texts(), dec)
        assert packet.live_dispatch_readiness_preflight_available is True
        assert packet.eligible_for_future_live_dispatch_gate is True
        assert packet.live_dispatch_readiness_preflight_approved is False
        assert not packet.blockers


def test_wrong_manifest_task_label_fails_closed():
    m = _manifest()
    m["task_label"] = "wrong"
    
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": _execution_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": _execution_discord_json()
    }
    packet = make_live_dispatch_readiness_preflight_packet(m, _json_paths(), jpackets, _md_paths(), _preview_texts(), _declaration())
    assert packet.live_dispatch_readiness_preflight_available is False
    assert "manifest_task_label_invalid" in packet.blockers


def test_manifest_not_prepared_fails_closed():
    for fld, val in [
        ("local_dispatch_execution_prepared", False),
        ("dispatch_execution_payload_created", False),
        ("live_send_request_created", True),
        ("approval_for_live_dispatch", True),
        ("dispatch_allowed", True),
        ("publication_ready", True),
    ]:
        m = _manifest()
        m[fld] = val
        
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": _execution_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": _execution_discord_json()
        }
        packet = make_live_dispatch_readiness_preflight_packet(m, _json_paths(), jpackets, _md_paths(), _preview_texts(), _declaration())
        assert packet.live_dispatch_readiness_preflight_available is False
        assert packet.blockers


def test_execution_json_mismatches():
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": _execution_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": _execution_discord_json()
    }
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json"]["platform"] = "wrong"
    packet = make_live_dispatch_readiness_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), _preview_texts(), _declaration())
    assert packet.live_dispatch_readiness_preflight_available is False
    assert any("platform_invalid" in b for b in packet.blockers)


def test_markdown_hash_mismatch():
    texts = _preview_texts()
    texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.md"] = "# Different\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION"
    
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": _execution_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": _execution_discord_json()
    }
    packet = make_live_dispatch_readiness_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), texts, _declaration())
    assert packet.live_dispatch_readiness_preflight_available is False
    assert any("hash_mismatch" in b for b in packet.blockers)


def test_missing_local_only_warnings():
    texts = _preview_texts()
    texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.md"] = "Safe text but missing warning."
    
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": _execution_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": _execution_discord_json()
    }
    packet = make_live_dispatch_readiness_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), texts, _declaration())
    assert packet.live_dispatch_readiness_preflight_available is False
    assert "prepared_substack_warning_missing" in packet.blockers


def test_declaration_required_gates_disabled_fails_closed():
    for gate in [
        "official_docs_required",
        "credentials_required_later",
        "destination_binding_required_later",
        "endpoint_allowlist_required_later",
        "payload_hash_required_later",
        "explicit_operator_approval_required_later",
        "kill_switch_required"
    ]:
        dec = _declaration()
        dec[gate] = False
        
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": _execution_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": _execution_discord_json()
        }
        packet = make_live_dispatch_readiness_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), _preview_texts(), dec)
        assert packet.live_dispatch_readiness_preflight_available is False
        assert any(gate in b for b in packet.blockers)


def test_declaration_invalid_decision_or_phrases():
    for fld, val in [
        ("decision", "wrong"),
        ("approval_phrase", "MARK_READY_FOR_FUTURE_LIVE_DISPATCH_GATE_ONLY_NOT_SEND_WRONG"),
        ("approval_scope", "future_live_dispatch_gate_preflight_only_wrong"),
    ]:
        dec = _declaration()
        dec[fld] = val
        
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": _execution_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": _execution_discord_json()
        }
        packet = make_live_dispatch_readiness_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), _preview_texts(), dec)
        assert packet.live_dispatch_readiness_preflight_available is False
        assert packet.blockers


def test_credential_keys_character_and_type_rules():
    for invalid_keys in [
        ["DISCORD_TOKEN=xyz"],
        ["DISCORD_TOKEN:"],
        ["DISCORD_TOKEN "],
        ["DISCORD_TOKEN_abc1234567890abcdef1234567890abcdef"], # Hex values length >= 16
        ["DISCORD_TOKEN_" + "A" * 60], # Too long
    ]:
        dec = _declaration()
        dec["credential_key_names_only"] = invalid_keys
        
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": _execution_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": _execution_discord_json()
        }
        packet = make_live_dispatch_readiness_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), _preview_texts(), dec)
        assert packet.live_dispatch_readiness_preflight_available is False
        assert packet.blockers


def test_secret_marker_in_manifest_or_declaration_fails_closed():
    # Secret in manifest
    m = _manifest()
    m["notes"] = "private_key: 1234"
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": _execution_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": _execution_discord_json()
    }
    packet = make_live_dispatch_readiness_preflight_packet(m, _json_paths(), jpackets, _md_paths(), _preview_texts(), _declaration())
    assert packet.live_dispatch_readiness_preflight_available is False
    assert "manifest_secret_marker_detected" in packet.blockers


def test_fake_claims_fail_closed():
    for claim in ["fake_url", "fake_metrics", "fake_comments", "fake_readiness", "fake_citation"]:
        texts = _preview_texts()
        texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.md"] = f"LOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nSupport {claim}."
        
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": _execution_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": _execution_discord_json()
        }
        packet = make_live_dispatch_readiness_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), texts, _declaration())
        assert packet.live_dispatch_readiness_preflight_available is False
        assert any(claim in b for b in packet.blockers)


def test_financial_advice_framing_fails_closed():
    for advice in ["buy position", "exit target", "signal service", "trading advice", "guaranteed prediction"]:
        texts = _preview_texts()
        texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.md"] = f"LOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nUse {advice}."
        
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.json": _execution_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.json": _execution_discord_json()
        }
        packet = make_live_dispatch_readiness_preflight_packet(_manifest(), _json_paths(), jpackets, _md_paths(), texts, _declaration())
        assert packet.live_dispatch_readiness_preflight_available is False
        assert "prepared_substack_financial_advice_or_signal_framing_detected" in packet.blockers


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/live_dispatch_readiness_preflight_v6.py").read_text(encoding="utf-8")
    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_cli_writes_deterministic_packet(tmp_path):
    m_path = tmp_path / "manifest.json"
    dec_path = tmp_path / "declaration.json"
    
    substack_md = tmp_path / "substack_execution_preparation.md"
    substack_md.write_text(_preview_texts()["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_execution_preparation.md"], encoding="utf-8")
    
    discord_md = tmp_path / "discord_execution_preparation.md"
    discord_md.write_text(_preview_texts()["A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_execution_preparation.md"], encoding="utf-8")
    
    h1 = hashlib.sha256(substack_md.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(discord_md.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    
    substack_json = tmp_path / "substack_execution_preparation.json"
    substack_json_data = _execution_substack_json()
    substack_json_data["markdown_snapshot_file"] = _normalize_path(substack_md)
    substack_json_data["markdown_snapshot_sha256"] = h1
    substack_json_data["source_prepared_dispatch_payload_markdown_file"] = "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"
    substack_json_data["source_prepared_dispatch_payload_markdown_sha256"] = "a659cc763b018861df43d4617a2241b1ea407c08a90da3084ba37f375001a182"
    substack_json.write_text(json.dumps(substack_json_data, sort_keys=True), encoding="utf-8")
    
    discord_json = tmp_path / "discord_execution_preparation.json"
    discord_json_data = _execution_discord_json()
    discord_json_data["markdown_snapshot_file"] = _normalize_path(discord_md)
    discord_json_data["markdown_snapshot_sha256"] = h2
    discord_json_data["source_prepared_dispatch_payload_markdown_file"] = "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md"
    discord_json_data["source_prepared_dispatch_payload_markdown_sha256"] = "06b005118749e7a858e38d9dc100d0f7300c082729a6da304ba37f375001a182"
    discord_json.write_text(json.dumps(discord_json_data, sort_keys=True), encoding="utf-8")
    
    comp_j1 = hashlib.sha256(_canonical_json(substack_json_data).encode("utf-8")).hexdigest()
    comp_j2 = hashlib.sha256(_canonical_json(discord_json_data).encode("utf-8")).hexdigest()
    
    m_data = _manifest()
    m_data["execution_preparation_json_files"] = [
        _normalize_path(substack_json),
        _normalize_path(discord_json)
    ]
    m_data["execution_preparation_markdown_files"] = [
        _normalize_path(substack_md),
        _normalize_path(discord_md)
    ]
    m_data["execution_preparation_file_hashes"] = {
        _normalize_path(substack_json): comp_j1,
        _normalize_path(discord_json): comp_j2,
        _normalize_path(substack_md): h1,
        _normalize_path(discord_md): h2
    }
    m_path.write_text(json.dumps(m_data, sort_keys=True), encoding="utf-8")
    
    dec_data = _declaration()
    dec_data["reviewed_execution_preparation_json_files"] = [
        _normalize_path(substack_json),
        _normalize_path(discord_json)
    ]
    dec_data["reviewed_execution_preparation_markdown_files"] = [
        _normalize_path(substack_md),
        _normalize_path(discord_md)
    ]
    dec_path.write_text(json.dumps(dec_data, sort_keys=True), encoding="utf-8")
    
    output_file = tmp_path / "readiness_preflight.json"
    ret = main([
        str(m_path),
        str(dec_path),
        "--json-files", str(substack_json), str(discord_json),
        "--markdown-files", str(substack_md), str(discord_md),
        "--output-file", str(output_file)
    ])
    if ret != 0:
        first = json.loads(output_file.read_text(encoding="utf-8"))
        print("FIRST BLOCKERS:", first["blockers"])
    assert ret == 0
    
    first = json.loads(output_file.read_text(encoding="utf-8"))
    
    assert main([
        str(m_path),
        str(dec_path),
        "--json-files", str(substack_json), str(discord_json),
        "--markdown-files", str(substack_md), str(discord_md),
        "--output-file", str(output_file)
    ]) == 0
    
    second = json.loads(output_file.read_text(encoding="utf-8"))
    assert first["live_dispatch_readiness_preflight_id"] == second["live_dispatch_readiness_preflight_id"]
    assert first["live_dispatch_readiness_preflight_available"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_LIVE_DISPATCH_READINESS_PREFLIGHT_FROM_EXECUTION_PAYLOADS")
    paths = [
        Path("live_contentops/live_dispatch_readiness_preflight_v6.py"),
        Path("tests/test_live_dispatch_readiness_preflight_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_live_dispatch_readiness_preflight_packet.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False


def test_malformed_non_object_cli_blocked_test(tmp_path):
    m_path = tmp_path / "manifest.json"
    m_path.write_text("[]", encoding="utf-8")
    
    output_file = tmp_path / "blocked_readiness_preflight.json"
    exit_code = main([
        str(m_path),
        "A:/declaration.json",
        "--json-files", "A:/a.json", "A:/b.json",
        "--markdown-files", "A:/a.md", "A:/b.md",
        "--output-file", str(output_file)
    ])
    assert exit_code == 1
    
    written = json.loads(output_file.read_text(encoding="utf-8"))
    assert written["live_dispatch_readiness_preflight_available"] is False
    assert written["eligible_for_future_live_dispatch_gate"] is False
    assert written["live_dispatch_readiness_preflight_approved"] is False
    assert written["live_send_request_created"] is False
    assert written["approval_for_live_dispatch"] is False
