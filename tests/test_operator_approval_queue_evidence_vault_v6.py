from dataclasses import asdict
import json
from pathlib import Path

import pytest

from live_contentops.operator_approval_queue_evidence_vault_v6 import *


def packet_dict():
    return asdict(sample_operator_approval_queue_evidence_vault_packet())


def test_view_model_builds_queue_items_from_variant_bridge_packet():
    data = packet_dict()
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["task_label"] == TASK_LABEL
    assert len(data["approval_queue_items"]) == 3
    assert {i["platform"] for i in data["approval_queue_items"]} == {"discord", "telegram_operator", "substack"}
    assert data["redacted_audit_summary"]["queue_item_count"] == 3


def test_approval_records_remain_pending_and_live_dispatch_false():
    for item in packet_dict()["approval_queue_items"]:
        assert item["approval_status"] == "pending_operator_review"
        assert item["approved_by"] is None
        assert item["approved_at"] is None
        assert item["live_dispatch_allowed"] is False


def test_evidence_vault_includes_required_sources():
    data = packet_dict()
    types = {i["evidence_type"] for i in data["evidence_vault_items"]}
    assert {"canonical_article_packet", "variant_preview_hash_approval_packet", "discord_dry_run_outbox", "discord_live_pilot_blocked_result"} <= types
    assert data["redacted_audit_summary"]["evidence_vault_item_count"] == 4


def test_no_raw_secret_env_webhook_provider_values_serialized():
    text = json.dumps(packet_dict()).lower()
    forbidden = ["bearer", "sk-", "xoxb-", "never-serialize", "https://discord.com/api/webhooks"]
    for term in forbidden:
        assert term not in text
    data = packet_dict()
    assert data["raw_secret_values_serialized"] is False
    assert data["env_lines_serialized"] is False


def test_sample_key_presence_is_fixture_only_not_runtime_proof():
    sample = packet_dict()["discord_outbox_card"]["sample_key_presence"]
    assert sample["evidence_scope"] == "sample_fixture_only"
    assert sample["runtime_proof"] is False
    assert packet_dict()["redacted_audit_summary"]["sample_key_presence_scope"] == "sample_fixture_only"


def test_safety_flags_false():
    data = packet_dict()
    assert data["provider_call_made"] is False
    assert data["network_call_made"] is False
    assert data["live_send_performed"] is False
    assert data["browser_session_used"] is False
    assert data["live_pilot_status_card"]["live_send_attempted"] is False


def test_missing_source_packet_fields_fail_closed():
    article = load_json(ARTICLE_SAMPLE)
    variant = load_json(VARIANT_SAMPLE)
    live = load_json(LIVE_PILOT_BLOCKED_SAMPLE)
    del variant["approval_records"]
    with pytest.raises(ValueError, match="missing_required_field:variant_packet.approval_records"):
        build_packet(article, variant, live)


def test_canonical_dashboard_contains_required_queue_evidence_labels_and_no_enabled_controls():
    dashboard_dir = Path("ui/contentops_v5/src")
    app = (dashboard_dir / "App.tsx").read_text(encoding="utf-8-sig").lower()
    fixtures = (dashboard_dir / "fixtures.ts").read_text(encoding="utf-8-sig").lower()
    approval = (dashboard_dir / "views" / "ApprovalQueue.tsx").read_text(encoding="utf-8-sig").lower()
    evidence = (dashboard_dir / "views" / "EvidenceVault.tsx").read_text(encoding="utf-8-sig").lower()
    combined = "\n".join([app, fixtures, approval, evidence])
    assert "operator approval queue" in combined
    assert "evidence vault" in combined
    assert "sample_fixture_only" in combined
    assert "d4a5afd3ecf03b1b93caf5b9dbd204d93eb80237eb8d368c9eea24680fabe44e" in combined
    assert "1cd58fd896f19c77638e62c52f34700c8166bd9644a8d830071d174924ca9172" in combined
    assert "974e8509d7999acad8cdf4855dc874d2d7182e766a51d4d1b4a6d6749126eb32" in combined
    assert "c19e65c51abb0967d25dde12e8c1b5ff2a3fa32ccac3b9e14eb7d73aa30b1b59" in combined
    assert "discord_dry_run_outbox_e59579adf7eb8db3" in combined
    assert "e59579adf7eb8db3839080f3b1b6f6744012d064f1fa58a96abb02bdff73bb80" in combined
    assert "live pilot blocked" in combined
    assert "live blocked" in combined
    assert "dispatch to platform" in combined
    assert "<button>send" not in combined
    assert "<button>dispatch" not in combined
    assert "<button>approve" not in combined


def test_standalone_ui_removed_and_not_canonical():
    assert not Path("ui/operator_approval_queue_evidence_vault/index.html").exists()
    runbook = Path("docs/runbooks/V6_OPERATOR_APPROVAL_QUEUE_EVIDENCE_VAULT_UI_RUNBOOK.md").read_text(encoding="utf-8-sig")
    assert "ui/contentops_v5/" in runbook
    assert "ui/institutional_operator_cockpit_v4/index.html" not in runbook
    assert "ui/operator_approval_queue_evidence_vault/index.html" not in runbook


def test_next_task_pointer():
    assert packet_dict()["recommended_next_task"] == RECOMMENDED_NEXT_TASK
    assert "SUBSTACK_MANUAL_EXPORT" in RECOMMENDED_NEXT_TASK
