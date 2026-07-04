"""Tests for no-API platform publication identity registry."""
from __future__ import annotations

import json

import pytest

from live_contentops import platform_publication_identity_registry_v6 as registry


PAYLOAD_HASH = "sha256:" + "a" * 64
EXECUTION_PAYLOAD_HASH = "a" * 64
PUBLIC_X_URL = "https://x.com/CapitalChron/status/1234567890123456789"


def _execution_packet(**overrides):
    packet = {
        "packet_kind": registry.EXACT_LIVE_EXECUTION_PACKET_KIND,
        "execution_status": registry.EXACT_LIVE_EXECUTED_STATUS,
        "registry_append_ready": True,
        "publication_registry_record_appended": False,
        "live_click_performed": True,
        "public_url_capture_performed": True,
        "payload_hash": EXECUTION_PAYLOAD_HASH,
        "operator_confirmed_payload_hash": EXECUTION_PAYLOAD_HASH,
        "captured_public_x_url": PUBLIC_X_URL,
        "blocked_reasons": [],
        "x_api_used": False,
        "browser_or_cdp_probe_performed": False,
        "public_url_fetch_made": False,
        "exact_live_execution_id": "x_exact_live_exec_test",
        "exact_live_authorization_id": "x_exact_live_auth_test",
    }
    packet.update(overrides)
    return packet


def test_extract_x_status_identity_accepts_x_url():
    got = registry.extract_x_status_identity("https://x.com/CapitalChron/status/123456789")
    assert got["handle"] == "CapitalChron"
    assert got["platform_publication_id"] == "123456789"
    assert got["public_url"] == "https://x.com/CapitalChron/status/123456789"


def test_extract_x_status_identity_accepts_twitter_url():
    got = registry.extract_x_status_identity("https://twitter.com/CapitalChron/status/42?s=20")
    assert got["platform_publication_id"] == "42"
    assert got["public_url"] == "https://x.com/CapitalChron/status/42"


def test_make_registry_record_valid_x_no_api():
    record = registry.make_registry_record(platform="x", payload_hash=PAYLOAD_HASH, public_url="https://x.com/CapitalChron/status/123")
    assert record["platform_publication_id"] == "123"
    assert record["thread_root_url"] == "https://x.com/CapitalChron/status/123"
    assert record["no_paid_api_used"] is True
    assert record["registry_record_id"].startswith("pubid_x_")


def test_missing_payload_hash_rejected():
    with pytest.raises(ValueError, match="payload_hash_required"):
        registry.make_registry_record(platform="x", payload_hash="", public_url="https://x.com/CapitalChron/status/123")


def test_secret_like_field_rejected():
    record = registry.make_registry_record(platform="x", payload_hash=PAYLOAD_HASH, public_url="https://x.com/CapitalChron/status/123")
    record["cookie_dump"] = "blocked"
    with pytest.raises(ValueError, match="secret_like_registry_field_blocked"):
        registry.validate_registry_record(record)


def test_paid_api_flag_rejected_for_x():
    with pytest.raises(ValueError, match="x_paid_api_flag_blocked"):
        registry.make_registry_record(platform="x", payload_hash=PAYLOAD_HASH, public_url="https://x.com/CapitalChron/status/123", no_paid_api_used=False)


def test_child_reply_requires_parent_url():
    parent = "https://x.com/CapitalChron/status/123"
    child = registry.make_registry_record(platform="x", payload_hash=PAYLOAD_HASH, public_url="https://x.com/CapitalChron/status/124", parent_public_url=parent)
    assert registry.child_reply_requires_parent(child) is True
    assert child["thread_root_url"] == parent


def test_append_registry_record_jsonl(tmp_path):
    record = registry.make_registry_record(platform="x", payload_hash=PAYLOAD_HASH, public_url="https://x.com/CapitalChron/status/123")
    path = registry.append_registry_record(record, tmp_path / "registry.jsonl")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["platform_publication_id"] == "123"


def test_make_registry_record_from_exact_live_click_execution_reconciles_payload_and_url():
    record = registry.make_registry_record_from_exact_live_click_execution(_execution_packet())
    assert record["payload_hash"] == EXECUTION_PAYLOAD_HASH
    assert record["public_url"] == PUBLIC_X_URL
    assert record["platform_publication_id"] == "1234567890123456789"
    assert record["capture_method"] == registry.EXACT_LIVE_CLICK_CAPTURE_METHOD
    assert record["approval_id"] == "x_exact_live_auth_test"
    assert record["exact_live_execution_id"] == "x_exact_live_exec_test"


def test_exact_live_click_execution_reconciliation_blocks_payload_mismatch():
    with pytest.raises(ValueError, match="operator_payload_hash_match"):
        registry.make_registry_record_from_exact_live_click_execution(_execution_packet(operator_confirmed_payload_hash="0" * 64))


def test_append_reconciled_exact_live_click_execution_record_jsonl(tmp_path):
    path = registry.append_reconciled_exact_live_click_execution_record(_execution_packet(), tmp_path / "registry.jsonl")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["source_execution_packet_kind"] == registry.EXACT_LIVE_EXECUTION_PACKET_KIND


def test_append_reconciled_exact_live_click_execution_record_is_idempotent(tmp_path):
    target = tmp_path / "registry.jsonl"
    registry.append_reconciled_exact_live_click_execution_record(_execution_packet(), target)
    registry.append_reconciled_exact_live_click_execution_record(_execution_packet(), target)
    rows = registry.read_registry_records(target)
    assert len(rows) == 1
    assert registry.audit_registry_records(target)["duplicate_natural_key_count"] == 0


def test_registry_audit_reports_duplicate_existing_rows_without_fetch(tmp_path):
    target = tmp_path / "registry.jsonl"
    record = registry.make_registry_record_from_exact_live_click_execution(_execution_packet())
    target.write_text("\n".join(json.dumps(record, sort_keys=True) for _ in range(2)), encoding="utf-8")
    audit = registry.audit_registry_records(target)
    assert audit["row_count"] == 2
    assert audit["duplicate_natural_key_count"] == 1
    assert audit["public_url_fetch_made"] is False
    assert audit["browser_or_cdp_probe_performed"] is False
    assert audit["x_api_used"] is False
