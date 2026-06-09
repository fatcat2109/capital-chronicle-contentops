"""Tests for the local approval ledger, kill-switch, and audit contracts (0079).

No network/credential/platform access. Mock publish flow is NOT implemented
here; that is task 0080.
"""

import json
import os

import live_contentops.approval_audit_contracts as m

FIX = os.path.join(os.path.dirname(__file__), "..", "fixtures", "approval_audit")


def _load(name):
    with open(os.path.join(FIX, name), "r", encoding="utf-8") as f:
        return json.load(f)


# --- schemas load -----------------------------------------------------------

def test_schemas_load():
    assert m.load_approval_schema()["title"] == "ApprovalLedgerRecord"
    assert m.load_kill_switch_schema()["title"] == "PublishKillSwitchState"
    assert m.load_audit_schema()["title"] == "RedactedAuditEvent"


# --- approval ledger --------------------------------------------------------

def test_valid_approval_record_validates():
    rec = _load("valid_approval_for_mock_publish.json")
    assert m.validate_approval_record(rec)["valid"] is True


def test_missing_approval_fails_closed():
    rec = _load("invalid_missing_approval.json")
    res = m.validate_approval_record(rec)
    assert res["valid"] is False
    assert any("approval_id" in e for e in res["errors"])


def test_revoked_fails_mock_closed():
    rec = _load("invalid_revoked_approval.json")
    ks = m.default_kill_switch_state()
    ks["enabled"] = True
    ks["blocks_mock_publish"] = False
    out = m.can_proceed_to_mock_publish(rec, ks)
    assert out["allowed"] is False
    assert any("fail_closed" in r for r in out["reasons"])


def test_append_only_ledger_roundtrip(tmp_path):
    rec = _load("valid_approval_for_mock_publish.json")
    p = tmp_path / "ledger.jsonl"
    m.append_approval_record(str(p), rec)
    rec2 = dict(rec)
    rec2["approval_id"] = "appr_0002"
    m.append_approval_record(str(p), rec2)
    records = m.read_approval_ledger(str(p))
    assert len(records) == 2
    assert records[0]["approval_id"] == "appr_0001"
    assert records[1]["approval_id"] == "appr_0002"


def test_append_rejects_invalid_record(tmp_path):
    rec = _load("invalid_missing_approval.json")
    p = tmp_path / "ledger.jsonl"
    try:
        m.append_approval_record(str(p), rec)
        assert False, "expected ValueError"
    except ValueError:
        pass
    assert not p.exists()


# --- kill switch ------------------------------------------------------------

def test_kill_switch_default_blocks_both():
    ks = m.default_kill_switch_state()
    assert ks["enabled"] is False
    assert ks["blocks_mock_publish"] is True
    assert ks["blocks_live_publish"] is True
    assert ks["fail_closed"] is True
    assert m.validate_kill_switch_state(ks)["valid"] is True


def test_kill_switch_cannot_unblock_live():
    ks = m.default_kill_switch_state()
    ks["blocks_live_publish"] = False
    res = m.validate_kill_switch_state(ks)
    assert res["valid"] is False


# --- proceed checks (fail closed) ------------------------------------------

def test_mock_publish_allowed_only_with_approval_and_permissive_switch():
    rec = _load("valid_approval_for_mock_publish.json")
    ks = m.default_kill_switch_state()
    ks["enabled"] = True
    ks["blocks_mock_publish"] = False
    out = m.can_proceed_to_mock_publish(rec, ks)
    assert out["allowed"] is True
    assert out["reasons"] == []


def test_mock_publish_blocked_by_default_kill_switch():
    rec = _load("valid_approval_for_mock_publish.json")
    ks = m.default_kill_switch_state()
    out = m.can_proceed_to_mock_publish(rec, ks)
    assert out["allowed"] is False
    assert any("blocks_mock_publish" in r for r in out["reasons"])


def test_mock_publish_blocked_when_approval_missing():
    ks = m.default_kill_switch_state()
    ks["blocks_mock_publish"] = False
    out = m.can_proceed_to_mock_publish({}, ks)
    assert out["allowed"] is False


def test_mock_publish_blocked_for_review_only_state():
    rec = _load("valid_approval_for_mock_publish.json")
    rec["approval_state"] = "operator_review_required"
    ks = m.default_kill_switch_state()
    ks["blocks_mock_publish"] = False
    out = m.can_proceed_to_mock_publish(rec, ks)
    assert out["allowed"] is False
    assert any("not_mock_publish" in r for r in out["reasons"])


def test_live_publish_always_blocked_in_this_task():
    rec = _load("valid_approval_for_mock_publish.json")
    rec["approval_state"] = "operator_approved_for_live_publish_later"
    ks = m.default_kill_switch_state()
    ks["enabled"] = True
    ks["blocks_mock_publish"] = False
    out = m.can_proceed_to_live_publish_later(rec, ks)
    assert out["allowed"] is False
    assert "live_publish_not_implemented_or_enabled_in_this_task" in out["reasons"]


# --- redacted audit events --------------------------------------------------

def test_valid_audit_event_validates():
    ev = _load("valid_redacted_audit_event.json")
    assert m.validate_audit_event(ev)["valid"] is True


def test_audit_event_with_unredacted_secret_fails_closed():
    ev = _load("invalid_secret_in_audit_event.json")
    res = m.validate_audit_event(ev)
    assert res["valid"] is False
    assert any("unredacted_secret_in" in e for e in res["errors"])


def test_build_redacted_audit_event_redacts_fake_secret():
    ev = m.build_redacted_audit_event(
        audit_event_id="a1",
        event_type="would_post_dry_run",
        source_post_id="post_x",
        decision="blocked",
        request_payload="authorization: bearer sk-ABCD1234EFGH5678IJKL",
        response_payload="api_key=sk-ZZZZ9999YYYY8888",
    )
    assert "[REDACTED]" in ev["request_payload_redacted"]
    assert "sk-ABCD1234EFGH5678IJKL" not in ev["request_payload_redacted"]
    assert "sk-ZZZZ9999YYYY8888" not in ev["response_payload_redacted"]
    assert ev["redaction_status"] == "redacted"
    assert ev["contains_secret"] is False
    assert ev["live_posting_enabled"] is False
    assert m.validate_audit_event(ev)["valid"] is True


def test_build_audit_event_clean_when_no_secret():
    ev = m.build_redacted_audit_event(
        audit_event_id="a2",
        event_type="would_post_dry_run",
        source_post_id="post_y",
        decision="blocked",
        request_payload="hello world",
    )
    assert ev["redaction_status"] == "clean_no_secret_found"
    assert m.validate_audit_event(ev)["valid"] is True


# --- summary / posture ------------------------------------------------------

def test_summary_posture():
    s = m.summary()
    assert s["live_publish_possible_now"] is False
    assert s["mock_publish_flow_implemented"] is False
    assert s["kill_switch_default_blocks_mock"] is True
    assert s["kill_switch_default_blocks_live"] is True
    assert s["credential_read_allowed_now"] is False
    assert s["network_accessed"] is False
