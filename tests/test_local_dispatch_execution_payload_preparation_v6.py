import json
import hashlib
from dataclasses import asdict
from pathlib import Path

from live_contentops.local_dispatch_execution_payload_preparation_v6 import (
    make_local_dispatch_execution_payload_manifest,
    write_local_dispatch_execution_payloads,
    main,
    _normalize_path,
    _canonical_json,
)


def _decision():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_OPERATOR_SUPERVISED_DISPATCH_REVIEW_DECISION_FROM_DESTINATION_PREFLIGHT_V0",
        "operator_supervised_dispatch_review_decision_packet_id": "operator_supervised_dispatch_review_decision_packet_abc123",
        "operator_supervised_dispatch_decision_id": "operator_supervised_dispatch_decision_abc123",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T01:05:00+07:00",
        "local_destination_binding_preflight_id": "local_destination_binding_preflight_abc123",
        "local_destination_binding_preflight_sha256": "preflight_sha256_xyz",
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
        "reviewed_prepared_dispatch_payload_json_files": [
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json",
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json"
        ],
        "reviewed_prepared_dispatch_payload_json_hashes": {
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": "j1",
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": "j2"
        },
        "reviewed_prepared_dispatch_payload_markdown_files": [
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md",
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md"
        ],
        "reviewed_prepared_dispatch_payload_markdown_hashes": {
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md": "a659cc763b018861df43d4617a2241b1ea407c08a90da3084ba37f375001a182",
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md": "06b005118749e7a858e38d9dc100d0f7300c082729a6da304ba37f375001a182"
        },
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
        "combined_payload_hash": "29cf1251e60055d78001ba1617a2241b1ea407c08a90da308ba37f375001a182",
        "decision": "approve_dispatch_execution_preparation",
        "approval_phrase": "APPROVE_LOCAL_DISPATCH_EXECUTION_PREPARATION_ONLY_NOT_LIVE_SEND",
        "approval_scope": "dispatch_execution_preparation_only",
        "dispatch_execution_preparation_approved": True,
        "supervised_dispatch_review_decision_available": True,
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
        "source_pack_id": "operator_source_pack_sample123",
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
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md": "a659cc763b018861df43d4617a2241b1ea407c08a90da308ba37f375001a182",
            "a:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md": "06b005118749e7a858e38d9dc100d0f7300c082729a6da304ba37f375001a182"
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


def _prepared_substack_json():
    return {
        "schema_version": "6.0.0",
        "task_label": "TASK_CONTENTOPS_V6_LOCAL_DISPATCH_PAYLOAD_PREPARATION_FROM_OPERATOR_DECISION_V0",
        "prepared_dispatch_payload_id": "prepared_dispatch_payload_substack_abc123",
        "platform": "substack",
        "payload_markdown_file": "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md",
        "payload_markdown_sha256": "a659cc763b018861df43d4617a2241b1ea407c08a90da308ba37f375001a182",
        "source_active_outbox_entry_file": "a:/outbox/sample-title-grounding-analysis_xyz/substack_outbox_entry.json",
        "source_active_outbox_entry_sha256": "h1",
        "source_active_outbox_payload_file": "a:/outbox/sample-title-grounding-analysis_xyz/substack_payload.md",
        "source_active_outbox_payload_sha256": "a659cc763b018861df43d4617a2241b1ea407c08a90da308ba37f375001a182",
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


def test_valid_inputs_emits_dispatch_execution_payload_preparation_manifest(tmp_path):
    dec = _decision()
    p = _preflight()
    jpaths = _json_paths()
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    mds = _md_paths()
    texts = _preview_texts()

    # Align hash in decision/preflight and inputs
    import hashlib
    h1 = hashlib.sha256(texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"].encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md"].encode("utf-8")).hexdigest()

    dec["reviewed_prepared_dispatch_payload_markdown_hashes"] = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md": h1,
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md": h2
    }
    p["prepared_dispatch_payload_markdown_hashes"] = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md": h1,
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md": h2
    }
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json"]["payload_markdown_sha256"] = h1
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json"]["source_active_outbox_payload_sha256"] = h1
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json"]["payload_markdown_sha256"] = h2
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json"]["source_active_outbox_payload_sha256"] = h2

    comp_j1 = hashlib.sha256(_canonical_json(jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json"]).encode("utf-8")).hexdigest()
    comp_j2 = hashlib.sha256(_canonical_json(jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json"]).encode("utf-8")).hexdigest()

    dec["reviewed_prepared_dispatch_payload_json_hashes"] = {
        "a:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": comp_j1,
        "a:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": comp_j2
    }
    p["prepared_dispatch_payload_json_hashes"] = {
        "a:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": comp_j1,
        "a:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": comp_j2
    }

    # Recalculate preflight hash for decision
    computed_preflight_sha256 = hashlib.sha256(_canonical_json(p).encode("utf-8")).hexdigest()
    dec["local_destination_binding_preflight_sha256"] = computed_preflight_sha256

    manifest = make_local_dispatch_execution_payload_manifest(dec, p, jpaths, jpackets, mds, texts, tmp_path)
    assert manifest.local_dispatch_execution_prepared is True
    assert manifest.dispatch_execution_payload_created is True
    assert not manifest.blockers

    # Write execution-preparation payloads
    manifest_path = write_local_dispatch_execution_payloads(manifest, dec, jpaths, jpackets, mds, texts, tmp_path)
    assert manifest_path.exists()

    # Re-read and check fields
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["local_dispatch_execution_prepared"] is True
    assert data["dispatch_execution_payload_created"] is True
    assert "Safe body content." not in json.dumps(data)

    # Check that MD snapshots were written
    exec_dir = Path(manifest.execution_preparation_dir)
    substack_md = exec_dir / "substack_execution_preparation.md"
    assert substack_md.exists()
    assert hashlib.sha256(substack_md.read_bytes()).hexdigest() == h1
    assert "Safe body content." in substack_md.read_text(encoding="utf-8")

    # Check that JSON files were written and do not contain body content
    substack_json = exec_dir / "substack_execution_preparation.json"
    assert substack_json.exists()
    sub_data = json.loads(substack_json.read_text(encoding="utf-8"))
    assert sub_data["preparation_status"] == "local_dispatch_execution_payload_pending_live_gate"
    assert sub_data["dispatch_execution_payload_created"] is True
    assert "Safe body content." not in json.dumps(sub_data)

    _assert_no_public_state(manifest)


def test_wrong_decision_task_label_fails_closed():
    dec = _decision()
    dec["task_label"] = "wrong"
    
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    manifest = make_local_dispatch_execution_payload_manifest(dec, _preflight(), _json_paths(), jpackets, _md_paths(), _preview_texts(), Path("A:/"))
    assert manifest.local_dispatch_execution_prepared is False
    assert manifest.dispatch_execution_payload_created is False
    assert "decision_task_label_invalid" in manifest.blockers


def test_decision_packet_eligibility_failures():
    for fld, val in [
        ("supervised_dispatch_review_decision_available", False),
        ("dispatch_execution_preparation_approved", False),
        ("decision", "reject"),
        ("approval_phrase", "wrong"),
        ("approval_scope", "wrong"),
        ("dispatch_execution_payload_created", True),
        ("live_send_request_created", True),
        ("approval_for_live_dispatch", True),
        ("publication_ready", True),
        ("public_url", "https://example.invalid"),
    ]:
        dec = _decision()
        dec[fld] = val
        
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
        }
        manifest = make_local_dispatch_execution_payload_manifest(dec, _preflight(), _json_paths(), jpackets, _md_paths(), _preview_texts(), Path("A:/"))
        assert manifest.local_dispatch_execution_prepared is False
        assert manifest.dispatch_execution_payload_created is False
        assert manifest.blockers


def test_preflight_eligibility_failures():
    for fld, val in [
        ("task_label", "wrong"),
        ("destination_binding_preflight_available", False),
        ("eligible_for_supervised_dispatch_gate", False),
        ("destination_binding_created", False),
        ("dispatch_execution_payload_created", True),
        ("live_send_request_created", True),
        ("approval_for_live_dispatch", True),
        ("publication_ready", True),
    ]:
        p = _preflight()
        p[fld] = val
        
        # Align hash
        dec = _decision()
        dec["local_destination_binding_preflight_sha256"] = hashlib.sha256(_canonical_json(p).encode("utf-8")).hexdigest()

        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
        }
        manifest = make_local_dispatch_execution_payload_manifest(dec, p, _json_paths(), jpackets, _md_paths(), _preview_texts(), Path("A:/"))
        assert manifest.local_dispatch_execution_prepared is False
        assert manifest.dispatch_execution_payload_created is False
        assert manifest.blockers


def test_json_paths_matching_failures():
    jpaths = [
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json"),
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json")
    ]
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    manifest = make_local_dispatch_execution_payload_manifest(_decision(), _preflight(), jpaths, jpackets, _md_paths(), _preview_texts(), Path("A:/"))
    assert manifest.local_dispatch_execution_prepared is False
    assert "prepared_json_file_paths_order_mismatch" in manifest.blockers


def test_markdown_paths_matching_failures():
    mds = [
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md"),
        Path("A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md")
    ]
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    manifest = make_local_dispatch_execution_payload_manifest(_decision(), _preflight(), _json_paths(), jpackets, mds, _preview_texts(), Path("A:/"))
    assert manifest.local_dispatch_execution_prepared is False
    assert "prepared_markdown_file_paths_order_mismatch" in manifest.blockers


def test_prepared_json_mismatches():
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    jpackets["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json"]["platform"] = "wrong"
    manifest = make_local_dispatch_execution_payload_manifest(_decision(), _preflight(), _json_paths(), jpackets, _md_paths(), _preview_texts(), Path("A:/"))
    assert manifest.local_dispatch_execution_prepared is False
    assert any("platform_invalid" in b for b in manifest.blockers)


def test_markdown_hash_mismatches():
    texts = _preview_texts()
    texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"] = "# Different\nLOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION"
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    manifest = make_local_dispatch_execution_payload_manifest(_decision(), _preflight(), _json_paths(), jpackets, _md_paths(), texts, Path("A:/"))
    assert manifest.local_dispatch_execution_prepared is False
    assert any("hash_mismatch" in b for b in manifest.blockers)


def test_missing_local_only_warnings():
    texts = _preview_texts()
    texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"] = "# Title\nSafe content but no warning."
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    manifest = make_local_dispatch_execution_payload_manifest(_decision(), _preflight(), _json_paths(), jpackets, _md_paths(), texts, Path("A:/"))
    assert manifest.local_dispatch_execution_prepared is False
    assert "prepared_substack_warning_missing" in manifest.blockers


def test_secret_marker_in_inputs_fails_closed():
    # Secret in decision
    dec = _decision()
    dec["notes"] = "private_key is secret-val"
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    manifest = make_local_dispatch_execution_payload_manifest(dec, _preflight(), _json_paths(), jpackets, _md_paths(), _preview_texts(), Path("A:/"))
    assert manifest.local_dispatch_execution_prepared is False
    assert "decision_secret_marker_detected" in manifest.blockers


def test_fake_claims_fail_closed():
    for claim in ["fake_url", "fake_metrics", "fake_comments", "fake_readiness", "fake_citation"]:
        texts = _preview_texts()
        texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"] = f"LOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\n{claim} is supported."
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
        }
        manifest = make_local_dispatch_execution_payload_manifest(_decision(), _preflight(), _json_paths(), jpackets, _md_paths(), texts, Path("A:/"))
        assert manifest.local_dispatch_execution_prepared is False
        assert any(claim in b for b in manifest.blockers)


def test_financial_advice_framing_fails_closed():
    for pattern in ["buy target", "exit strategy", "trading advice", "signal service", "guaranteed prediction"]:
        texts = _preview_texts()
        texts["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"] = f"LOCAL PREVIEW ONLY - NOT APPROVED FOR PUBLICATION\nSome {pattern} advice."
        jpackets = {
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
            "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
        }
        manifest = make_local_dispatch_execution_payload_manifest(_decision(), _preflight(), _json_paths(), jpackets, _md_paths(), texts, Path("A:/"))
        assert manifest.local_dispatch_execution_prepared is False
        assert "prepared_substack_financial_advice_or_signal_framing_detected" in manifest.blockers


def test_no_execution_prep_files_are_written_on_blocked_inputs_except_blocked_manifest(tmp_path):
    dec = _decision()
    dec["task_label"] = "wrong"
    jpackets = {
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.json": _prepared_substack_json(),
        "A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.json": _prepared_discord_json()
    }
    manifest = make_local_dispatch_execution_payload_manifest(dec, _preflight(), _json_paths(), jpackets, _md_paths(), _preview_texts(), tmp_path)
    assert manifest.local_dispatch_execution_prepared is False
    assert manifest.dispatch_execution_payload_created is False

    manifest_path = write_local_dispatch_execution_payloads(manifest, dec, _json_paths(), jpackets, _md_paths(), _preview_texts(), tmp_path)
    assert manifest_path.exists()
    assert manifest.execution_preparation_dir == ""

    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written["local_dispatch_execution_prepared"] is False
    assert written["dispatch_execution_payload_created"] is False


def test_module_contains_no_getenv_environ_network_provider_browser_imports():
    source = Path("live_contentops/local_dispatch_execution_payload_preparation_v6.py").read_text(encoding="utf-8")
    forbidden = ["getenv", "environ", "requests", "urllib", "httpx", "provider_gateway", "browser", "webbrowser"]
    assert not any(marker in source for marker in forbidden)


def test_cli_writes_deterministic_manifest_and_package_names(tmp_path):
    dec_path = tmp_path / "decision.json"
    p_path = tmp_path / "preflight.json"
    
    substack_md = tmp_path / "substack_dispatch_payload.md"
    substack_md.write_text(_preview_texts()["A:/prepared_payloads/sample-title-grounding-analysis_xyz/substack_dispatch_payload.md"], encoding="utf-8")
    
    discord_md = tmp_path / "discord_dispatch_payload.md"
    discord_md.write_text(_preview_texts()["A:/prepared_payloads/sample-title-grounding-analysis_xyz/discord_dispatch_payload.md"], encoding="utf-8")
    
    import hashlib
    h1 = hashlib.sha256(substack_md.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    h2 = hashlib.sha256(discord_md.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    
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
    
    comp_j1 = hashlib.sha256(_canonical_json(substack_json_data).encode("utf-8")).hexdigest()
    comp_j2 = hashlib.sha256(_canonical_json(discord_json_data).encode("utf-8")).hexdigest()

    dec_data = _decision()
    dec_data["reviewed_prepared_dispatch_payload_json_files"] = [
        _normalize_path(substack_json),
        _normalize_path(discord_json)
    ]
    dec_data["reviewed_prepared_dispatch_payload_json_hashes"] = {
        _normalize_path(substack_json): comp_j1,
        _normalize_path(discord_json): comp_j2
    }
    dec_data["reviewed_prepared_dispatch_payload_markdown_files"] = [
        _normalize_path(substack_md),
        _normalize_path(discord_md)
    ]
    dec_data["reviewed_prepared_dispatch_payload_markdown_hashes"] = {
        _normalize_path(substack_md): h1,
        _normalize_path(discord_md): h2
    }
    
    p_data = _preflight()
    p_data["prepared_dispatch_payload_json_files"] = [
        _normalize_path(substack_json),
        _normalize_path(discord_json)
    ]
    p_data["prepared_dispatch_payload_json_hashes"] = {
        _normalize_path(substack_json): comp_j1,
        _normalize_path(discord_json): comp_j2
    }
    p_data["prepared_dispatch_payload_markdown_files"] = [
        _normalize_path(substack_md),
        _normalize_path(discord_md)
    ]
    p_data["prepared_dispatch_payload_markdown_hashes"] = {
        _normalize_path(substack_md): h1,
        _normalize_path(discord_md): h2
    }
    
    # Preflight sha256 alignment
    p_sha = hashlib.sha256(_canonical_json(p_data).encode("utf-8")).hexdigest()
    dec_data["local_destination_binding_preflight_sha256"] = p_sha
    
    p_path.write_text(json.dumps(p_data, sort_keys=True), encoding="utf-8")
    dec_path.write_text(json.dumps(dec_data, sort_keys=True), encoding="utf-8")
    
    output_dir = tmp_path / "out"
    assert main([
        str(dec_path),
        str(p_path),
        "--json-files", str(substack_json), str(discord_json),
        "--markdown-files", str(substack_md), str(discord_md),
        "--output-dir", str(output_dir)
    ]) == 0
    
    first = list(output_dir.glob("**/local_dispatch_execution_payload_manifest.json"))[0]
    first_packet = json.loads(first.read_text(encoding="utf-8"))
    
    assert main([
        str(dec_path),
        str(p_path),
        "--json-files", str(substack_json), str(discord_json),
        "--markdown-files", str(substack_md), str(discord_md),
        "--output-dir", str(output_dir)
    ]) == 0
    
    second = list(output_dir.glob("**/local_dispatch_execution_payload_manifest.json"))[0]
    second_packet = json.loads(second.read_text(encoding="utf-8"))
    
    assert first_packet["local_dispatch_execution_payload_manifest_id"] == second_packet["local_dispatch_execution_payload_manifest_id"]
    assert first_packet["local_dispatch_execution_prepared"] is True


def test_new_files_and_sample_json_are_utf8_without_bom():
    docs_dir = Path("docs/automation/V6_LOCAL_DISPATCH_EXECUTION_PAYLOAD_PREPARATION_FROM_SUPERVISED_DECISION")
    paths = [
        Path("live_contentops/local_dispatch_execution_payload_preparation_v6.py"),
        Path("tests/test_local_dispatch_execution_payload_preparation_v6.py"),
    ]
    paths.extend(path for path in docs_dir.glob("*") if path.is_file())
    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
    loaded = json.loads((docs_dir / "sample_local_dispatch_execution_payload_manifest.json").read_text(encoding="utf-8"))
    assert loaded["sample_packet_non_runtime"] is True
    assert loaded["runtime_truth"] is False


def test_malformed_non_object_cli_blocked_test(tmp_path):
    dec_path = tmp_path / "decision.json"
    dec_path.write_text("[]", encoding="utf-8")
    
    output_dir = tmp_path / "out"
    exit_code = main([
        str(dec_path),
        "A:/preflight.json",
        "--json-files", "A:/a.json", "A:/b.json",
        "--markdown-files", "A:/a.md", "A:/b.md",
        "--output-dir", str(output_dir)
    ])
    assert exit_code == 1
    
    packets = list(output_dir.glob("local_dispatch_execution_payload_manifest_*.json"))
    assert len(packets) == 1
    written = json.loads(packets[0].read_text(encoding="utf-8"))
    assert written["local_dispatch_execution_prepared"] is False
    assert written["dispatch_execution_payload_created"] is False
    assert written["live_send_request_created"] is False
    assert written["approval_for_live_dispatch"] is False
    assert written["dispatch_allowed"] is False
