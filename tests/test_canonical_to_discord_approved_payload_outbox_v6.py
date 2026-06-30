import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.canonical_to_discord_approved_payload_outbox_v6 import *


def _readiness():
    data = {
        "schema_version": "6.0.0",
        "task_label": UPSTREAM_TASK_LABEL,
        "discord_final_pre_live_release_readiness_id": "discord_final_ready_abc",
        "eligible_for_future_explicit_live_send_task": True,
        "future_live_send_task_required": True,
        "future_live_send_task_requirements": {key: True for key in READINESS_REQUIREMENTS},
        "blockers": [],
    }
    for flag in SAFETY_FALSE_FLAGS:
        data[flag] = False
    return data


def _decl():
    data = {
        "schema_version": "6.0.0",
        "approved_payload_declaration_id": "payload_decl_abc",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T08:29:00+07:00",
        "discord_final_pre_live_release_readiness_id": _readiness()["discord_final_pre_live_release_readiness_id"],
        "platform": "discord",
        "content_lane": CONTENT_LANE,
        "payload_mode": PAYLOAD_MODE,
        "payload_kind": PAYLOAD_KIND,
        "canonical_content_reference_id": "canonical_content_001",
        "canonical_content_source_type": "operator_approved_canonical_payload_reference",
        "payload_preview_hash": "a4d3b5b6307374eeaa27f6cfb08c903823790e668b5a1532822a16d8cfb08cb0",
        "destination_binding_present_now": False,
        "credential_key_name": CREDENTIAL_KEY_NAME,
        "max_request_count": 1,
        "max_retries": 0,
        "hidden_retry_allowed": False,
        "operator_payload_decision": "approve_payload_hash_binding_for_future_explicit_live_send_task_only",
        "declaration_decision": "mark_canonical_to_discord_payload_outbox_ready",
        "approval_phrase": APPROVAL_PHRASE,
        "approval_scope": APPROVAL_SCOPE,
        "notes": "",
    }
    for flag in DECL_TRUE_FLAGS:
        data[flag] = True
    for flag in CONTENT_RISK_FALSE_FLAGS + SAFETY_FALSE_FLAGS:
        data[flag] = False
    return data


def _packet(readiness=None, declaration=None):
    return make_canonical_to_discord_approved_payload_outbox_packet(readiness or _readiness(), declaration or _decl())


def test_valid_outbox_packet_future_only_and_deterministic():
    p = _packet(); data = asdict(p)
    assert p.local_outbox_packet_created is True
    assert p.local_outbox_packet_non_executable is True
    assert p.eligible_for_future_explicit_live_send_task is True
    assert p.payload_hash_binding_ready is True
    assert p.eligible_for_live_send_now is False
    assert p.live_send_now is False
    assert p.dispatch_allowed is False
    assert p.publication_ready is False
    assert p.runtime_truth is False
    assert p.executable_request_artifact_created_now is False
    assert all(data["future_live_send_task_requirements"].values())
    assert p.packet_sha256 == _packet().packet_sha256


def test_final_readiness_unavailable_or_safety_flag_true_fails_closed():
    r = _readiness(); r["eligible_for_future_explicit_live_send_task"] = False
    assert "readiness_future_task_not_true" in _packet(r).blockers
    r = _readiness(); r["blockers"] = ["x"]
    assert "readiness_blockers_not_empty" in _packet(r).blockers
    for flag in SAFETY_FALSE_FLAGS:
        r = _readiness(); r[flag] = True
        p = _packet(r)
        assert p.eligible_for_future_explicit_live_send_task is False
        assert f"readiness_{flag}_not_false" in p.blockers


def test_missing_future_live_send_requirement_fails_closed():
    for req in READINESS_REQUIREMENTS:
        r = _readiness(); r["future_live_send_task_requirements"][req] = False
        assert f"readiness_{req}_not_true" in _packet(r).blockers

def test_payload_approval_public_postable_and_content_risks_fail_closed():
    d = _decl(); d["canonical_content_operator_approved"] = False
    assert "declaration_canonical_content_operator_approved_not_true" in _packet(declaration=d).blockers
    d = _decl(); d["payload_text_operator_supplied"] = False
    assert "declaration_payload_text_operator_supplied_not_true" in _packet(declaration=d).blockers
    for flag in CONTENT_RISK_FALSE_FLAGS:
        d = _decl(); d[flag] = True
        p = _packet(declaration=d)
        assert p.eligible_for_future_explicit_live_send_task is False
        assert f"declaration_{flag}_not_false" in p.blockers


def test_payload_hash_missing_secret_like_or_url_like_fails_closed():
    d = _decl(); d["payload_preview_hash"] = ""
    assert "payload_preview_hash_missing" in _packet(declaration=d).blockers
    d = _decl(); d["payload_preview_hash"] = "https://discord.com/api/webhooks/x/y"
    try:
        _packet(declaration=d)
    except ValueError as exc:
        assert "forbidden_value" in str(exc) and "discord.com" not in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_destination_credential_budget_retry_flags_fail_closed():
    d = _decl(); d["destination_binding_present_now"] = True
    assert "declaration_destination_binding_present_now_not_false" in _packet(declaration=d).blockers
    for flag in ("destination_binding_required_later", "credential_presence_membership_only_required_later", "exact_operator_go_required_later", "kill_switch_required", "redacted_audit_required", "manual_fallback_required"):
        d = _decl(); d[flag] = False
        assert f"declaration_{flag}_not_true" in _packet(declaration=d).blockers
    d = _decl(); d["credential_key_name"] = "OTHER"
    assert "declaration_credential_key_name_invalid" in _packet(declaration=d).blockers
    for key, value, blocker in (("max_request_count", 2, "declaration_max_request_count_not_one"), ("max_retries", 1, "declaration_max_retries_not_zero"), ("hidden_retry_allowed", True, "declaration_hidden_retry_allowed_not_false")):
        d = _decl(); d[key] = value
        assert blocker in _packet(declaration=d).blockers


def test_declaration_safety_flags_reject_defer_extra_fail_closed():
    for flag in SAFETY_FALSE_FLAGS:
        d = _decl(); d[flag] = True
        p = _packet(declaration=d)
        assert p.eligible_for_future_explicit_live_send_task is False
        assert f"declaration_{flag}_not_false" in p.blockers
    for key in ("operator_payload_decision", "declaration_decision"):
        for val in ("reject", "defer"):
            d = _decl(); d[key] = val
            assert _packet(declaration=d).eligible_for_future_explicit_live_send_task is False
    d = _decl(); d["extra"] = "x"
    assert "declaration_extra_fields" in _packet(declaration=d).blockers

def test_forbidden_live_secret_financial_fake_text_fail_closed_without_echo():
    bad = ("send now", "financial advice", "signal service", "fake readiness", "buy", "sell", "hold", "entries", "exits", "targets", "position sizing", "guaranteed prediction", "public URL", "curl something")
    for txt in bad:
        d = _decl(); d["notes"] = txt
        try:
            _packet(declaration=d)
        except ValueError as exc:
            assert "forbidden_text" in str(exc)
        else:
            raise AssertionError(txt)
    d = _decl(); d["notes"] = "https://discord.com/api/webhooks/x/y"
    try:
        _packet(declaration=d)
    except ValueError as exc:
        assert "forbidden_value" in str(exc) and "discord.com" not in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_static_no_env_network_browser_request_patterns():
    src = Path("live_contentops/canonical_to_discord_approved_payload_outbox_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


def test_docs_runbook_sample_utf8_no_bom_no_literal_backtick_n():
    paths = [
        "docs/runbooks/V6_CANONICAL_TO_DISCORD_APPROVED_PAYLOAD_OUTBOX_OPERATOR_RUNBOOK_NO_SEND.md",
        "docs/automation/V6_CANONICAL_TO_DISCORD_APPROVED_PAYLOAD_OUTBOX_HEAVY_BATCH_NO_SEND/implementation_report.md",
        "docs/automation/V6_CANONICAL_TO_DISCORD_APPROVED_PAYLOAD_OUTBOX_HEAVY_BATCH_NO_SEND/canonical_to_discord_approved_payload_outbox_contract.md",
        "docs/automation/V6_CANONICAL_TO_DISCORD_APPROVED_PAYLOAD_OUTBOX_HEAVY_BATCH_NO_SEND/sample_canonical_to_discord_approved_payload_outbox_packet.json",
    ]
    for path in paths:
        raw = Path(path).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert "`n" not in raw.decode("utf-8"), path
    text = Path(paths[0]).read_text(encoding="utf-8").lower()
    assert "no live send" in text and "future separate explicit live task required" in text
    assert "curl " not in text and "fetch(" not in text and "http method" not in text


def test_cli_deterministic_output(tmp_path):
    r = tmp_path / "readiness.json"; d = tmp_path / "decl.json"
    out1 = tmp_path / "out1.json"; out2 = tmp_path / "out2.json"
    r.write_text(json.dumps(_readiness()), encoding="utf-8")
    d.write_text(json.dumps(_decl()), encoding="utf-8")
    assert main(["--input-final-readiness-packet", str(r), "--operator-approved-payload-declaration", str(d), "--output", str(out1)]) == 0
    assert main(["--input-final-readiness-packet", str(r), "--operator-approved-payload-declaration", str(d), "--output", str(out2)]) == 0
    a = json.loads(out1.read_text(encoding="utf-8")); b = json.loads(out2.read_text(encoding="utf-8"))
    assert a == b
    assert a["eligible_for_future_explicit_live_send_task"] is True
    assert a["eligible_for_live_send_now"] is False
    assert a["local_outbox_packet_non_executable"] is True
