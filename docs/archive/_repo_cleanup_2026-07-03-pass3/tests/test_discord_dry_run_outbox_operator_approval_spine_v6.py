import json
from dataclasses import asdict
from pathlib import Path

import pytest

from live_contentops.discord_dry_run_outbox_operator_approval_spine_v6 import *
from live_contentops.unified_capability_env_readiness_v6 import make_unified_capability_env_readiness_packet


def _packet(key_present=True, article=None):
    env = {DISCORD_REQUIRED_KEY_NAME: "fake-secret-value-never-serialize"} if key_present else {}
    cap = asdict(make_unified_capability_env_readiness_packet(env=env, dotenv_path="missing.env", scan_mode="process_env_only"))
    return make_discord_dry_run_outbox_packet(article=article, capability_packet=cap)


def test_committed_sample_creates_dry_run_packet_with_no_live_send():
    data = asdict(sample_discord_dry_run_outbox_packet())
    assert data["task_label"] == TASK_LABEL
    assert data["outbox_dry_run_record"]["action_class"] == "dry_run_outbox"
    assert data["live_send_performed"] is False
    assert data["provider_call_made"] is False
    assert data["network_call_made"] is False
    assert data["browser_call_made"] is False


def test_discord_key_present_live_candidate_but_no_live_send():
    p = _packet(True)
    assert p.discord_key_present is True
    assert p.live_pilot_candidate is True
    assert p.outbox_dry_run_record["ready_for_live_pilot_candidate"] is True
    assert p.live_send_performed is False
    assert p.outbox_dry_run_record["live_send_performed"] is False


def test_discord_key_missing_dry_run_and_manual_fallback_remain_valid():
    p = _packet(False)
    assert p.discord_key_present is False
    assert p.live_pilot_candidate is False
    assert p.manual_fallback_record["available"] is True
    assert p.outbox_dry_run_record["credential_present"] is False
    assert any("discord_key_absent" in w for w in p.warnings)


def test_exact_rendered_preview_hash_is_stable():
    p1 = _packet(True)
    p2 = _packet(True)
    assert p1.discord_preview_text == p2.discord_preview_text
    assert p1.approved_payload_hash == p2.approved_payload_hash
    assert p1.approved_payload_hash == exact_payload_hash(p1.discord_preview_text, sample_article())
    assert p1.approved_payload_preview_id.endswith(p1.approved_payload_hash[:16])


def test_approval_record_pending_default_and_live_not_allowed():
    approval = asdict(_packet(True))["operator_approval_record"]
    assert approval["operator_approval_status"] == "pending"
    assert approval["approved_by"] is None
    assert approval["approved_at"] is None
    assert approval["live_send_allowed"] is False
    assert approval["preview_hash"] == approval["exact_payload_hash"]


def test_outbox_binds_exact_payload_hash():
    p = _packet(True)
    assert p.outbox_dry_run_record["exact_payload_hash"] == p.approved_payload_hash
    assert p.outbox_dry_run_record["credential_key_name"] == DISCORD_REQUIRED_KEY_NAME
    assert p.outbox_dry_run_record["destination_binding"].startswith("symbolic_")


def test_redacted_audit_has_no_raw_secret_or_env_values():
    data = asdict(_packet(True))
    audit = data["redacted_audit_record"]
    assert audit["raw_secret_values_serialized"] is False
    assert audit["env_lines_serialized"] is False
    assert audit["provider_call_made"] is False
    assert audit["network_call_made"] is False
    assert audit["live_send_performed"] is False
    text = json.dumps(data).lower()
    for bad in ["fake-secret-value-never-serialize", "discord_live_announcements_webhook=fake", "bearer "]:
        assert bad not in text


def test_injected_fake_secret_payload_value_is_rejected_or_not_serialized():
    article = asdict(sample_article())
    article["summary"] = "This contains never-serialize payload material."
    with pytest.raises(ValueError):
        _packet(True, article)


def test_no_financial_advice_language_allowed():
    article = asdict(sample_article())
    article["call_to_action"] = "Buy this now."
    with pytest.raises(ValueError, match="forbidden_financial_advice_language"):
        _packet(True, article)


def test_no_provider_network_browser_live_call_code():
    src = Path("live_contentops/discord_dry_run_outbox_operator_approval_spine_v6.py").read_text(encoding="utf-8-sig").lower()
    for bad in ["requests", "httpx", "urllib", "webbrowser", "selenium", "playwright", "discord.com/api", "api/webhooks", ".post(", "authorization", "content-type"]:
        assert bad not in src, bad


def test_bom_removed_from_scoped_docs():
    paths = [
        "docs/automation/V6_FAST_SHIP_RUNTIME_SPINE_CONSOLIDATION/runtime_spine_consolidation_report.md",
        "docs/automation/V6_FAST_SHIP_RUNTIME_SPINE_CONSOLIDATION/next_product_lane_pointer.md",
        "docs/automation/V6_UNIFIED_CAPABILITY_ENV_READINESS/capability_env_readiness_contract.md",
        "docs/automation/V6_UNIFIED_CAPABILITY_ENV_READINESS/sample_unified_capability_env_readiness_packet.json",
        "docs/runbooks/V6_UNIFIED_CAPABILITY_ENV_READINESS_OPERATOR_RUNBOOK.md",
    ]
    for path in paths:
        assert not Path(path).read_bytes().startswith(b"\xef\xbb\xbf")


def test_manual_fallback_includes_copyable_preview_and_hash():
    p = _packet(True)
    manual = p.manual_fallback_record
    assert manual["copyable_discord_message_preview"] == p.discord_preview_text
    assert manual["exact_payload_hash"] == p.approved_payload_hash
    assert "Jim/operator" in manual["operator_instructions"]
