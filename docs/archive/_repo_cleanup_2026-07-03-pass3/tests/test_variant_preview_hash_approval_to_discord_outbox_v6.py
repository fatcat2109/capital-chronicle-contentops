from dataclasses import asdict

import pytest

from live_contentops.ai_research_canonical_article_engine_v6 import sample_article_packet
from live_contentops.variant_preview_hash_approval_to_discord_outbox_v6 import *


def test_sample_bridge_packet_builds_variants_previews_and_pending_approvals():
    packet = sample_variant_approval_bridge_packet()
    data = asdict(packet)
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["task_label"] == TASK_LABEL
    assert data["provider_call_made"] is False
    assert data["network_call_made"] is False
    assert data["browser_call_made"] is False
    assert data["live_send_performed"] is False
    assert len(data["variants"]) == 3
    assert len(data["preview_hash_records"]) == 3
    assert len(data["approval_records"]) == 3
    assert {v["platform"] for v in data["variants"]} == {"discord", "telegram_operator", "substack"}
    assert all(a["approval_status"] == "pending_operator_review" for a in data["approval_records"])
    assert all(a["live_dispatch_allowed"] is False for a in data["approval_records"])


def test_preview_hashes_are_stable_and_exact():
    p1 = sample_variant_approval_bridge_packet()
    p2 = sample_variant_approval_bridge_packet()
    h1 = [r["exact_preview_hash"] for r in asdict(p1)["preview_hash_records"]]
    h2 = [r["exact_preview_hash"] for r in asdict(p2)["preview_hash_records"]]
    assert h1 == h2
    assert all(len(h) == 64 and h.isalnum() for h in h1)
    assert all(r["executable_request_artifact_created"] is False for r in asdict(p1)["preview_hash_records"])


def test_discord_seed_is_compatible_with_existing_outbox_spine():
    packet = sample_variant_approval_bridge_packet()
    data = asdict(packet)
    outbox = data["discord_dry_run_outbox_packet"]
    assert data["discord_outbox_compatibility"]["discord_seed_accepted_by_outbox_spine"] is True
    assert data["discord_outbox_compatibility"]["discord_dry_run_only"] is True
    assert outbox["canonical_content_id"] == data["discord_summary_seed"]["source_article_id"]
    assert outbox["operator_approval_record"]["operator_approval_status"] == "pending"
    assert outbox["outbox_dry_run_record"]["action_class"] == "dry_run_outbox"
    assert outbox["live_send_performed"] is False


def test_redacted_audit_packet_has_no_secret_or_live_behavior_flags():
    packet = sample_variant_approval_bridge_packet()
    audit = asdict(packet)["redacted_audit_packet"]
    assert audit["provider_call_made"] is False
    assert audit["network_call_made"] is False
    assert audit["browser_call_made"] is False
    assert audit["live_send_performed"] is False
    assert audit["raw_secret_values_serialized"] is False
    assert audit["env_lines_serialized"] is False
    assert audit["executable_request_artifacts_created"] is False
    def walk_values(obj):
        if isinstance(obj, str):
            yield obj.lower()
        elif isinstance(obj, dict):
            for value in obj.values():
                yield from walk_values(value)
        elif isinstance(obj, list):
            for value in obj:
                yield from walk_values(value)

    text = "\n".join(walk_values(asdict(packet)))
    for bad in ("secret", "token", "bearer", "sk-", "xoxb-", "never-serialize"):
        assert bad not in text


def test_forbidden_financial_terms_are_blocked_from_input_packet():
    packet = sample_article_packet()
    packet["discord_summary_seed"]["summary"] = "This is a buy alert."
    with pytest.raises(ValueError, match="forbidden_financial_advice_language"):
        run_variant_approval_bridge(packet)


def test_missing_discord_summary_seed_fields_are_rejected():
    packet = sample_article_packet()
    packet["discord_summary_seed"].pop("source_article_id")
    with pytest.raises(ValueError, match="discord_summary_seed_missing_fields"):
        run_variant_approval_bridge(packet)


def test_next_task_pointer_is_operator_queue_and_evidence_vault_ui():
    packet = sample_variant_approval_bridge_packet()
    assert packet.recommended_next_task == RECOMMENDED_NEXT_TASK
    assert "OPERATOR_APPROVAL_QUEUE_AND_EVIDENCE_VAULT_UI" in packet.recommended_next_task
