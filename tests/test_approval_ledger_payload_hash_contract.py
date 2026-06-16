"""Tests for the 0174ED approval ledger + payload hash contract.

These tests prove the module is deterministic, stdlib-only, secret-free, and
fail-closed, and that:
  * the static import surface is an exact stdlib allow-list (hashlib, json, os,
    re) with no requests/httpx/aiohttp/socket/ssl/http server, no
    selenium/playwright, no dotenv/keyring/sqlite, no provider/platform SDKs,
  * importing the module performs NO network/env/credential read and NO write,
  * the payload hash is deterministic and changes when ANY authority-bearing
    input changes (text/platform/binding/credential handle/media/visibility/
    disclosure/platform formatting),
  * approval binds an exact payload hash and is valid only before expiration,
    without revocation, and against the exact same payload + bindings,
  * approval is invalidated by edits, expiration, revocation, and binding
    changes,
  * append-only semantics hold (revocation never mutates the approval entry),
  * redacted audit objects contain no raw token/api-key/secret-like material,
  * approval never implies dispatch-ready / live-ready, and
  * the packet + doc are leak-free and writing touches only the 0174ED dir.
"""

import ast
import os

import pytest

from live_contentops import approval_ledger_payload_hash_contract as model


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(
    REPO_ROOT, "live_contentops",
    "approval_ledger_payload_hash_contract.py")


ALLOWED_IMPORT_ROOTS = {"hashlib", "json", "os", "re"}
FORBIDDEN_IMPORT_ROOTS = {
    "requests", "httpx", "aiohttp", "socket", "socketserver", "ssl",
    "asyncio", "selectors", "http", "urllib", "wsgiref", "webbrowser",
    "subprocess", "dotenv", "ftplib", "smtplib", "multiprocessing",
    "threading", "configparser", "keyring", "secretstorage", "netrc",
    "browser_cookie3", "sqlite3", "pickle", "shelve", "selenium",
    "playwright", "getpass", "openai", "anthropic", "telegram", "tweepy",
    "linkedin", "facebook",
}


def _module_imports():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                roots.add(node.module.split(".")[0])
    return roots


# --------------------------------------------------------------------------- #
# Import surface (tests 18-20)
# --------------------------------------------------------------------------- #
def test_import_allow_list_exact():
    roots = _module_imports()
    assert roots <= ALLOWED_IMPORT_ROOTS, (
        f"unexpected imports: {roots - ALLOWED_IMPORT_ROOTS}")


def test_no_forbidden_imports():
    roots = _module_imports()
    bad = roots & FORBIDDEN_IMPORT_ROOTS
    assert not bad, f"forbidden imports present: {bad}"


def test_no_network_or_http_client_strings():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    for s in ("requests.", "httpx.", "aiohttp.", "urllib.", "socket.",
              "import requests", "import httpx", "import aiohttp",
              "urlopen", "http.client", "webbrowser"):
        assert s not in src, f"forbidden network string present: {s}"


def test_no_env_credential_access_strings():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    for s in ("os.environ", "os.getenv", "getenv(", "load_dotenv",
              "dotenv_values", "keyring.get", "keyring.set", "secretstorage.",
              "netrc(", "configparser.", "ConfigParser", "browser_cookie",
              "sqlite3.", "getpass", "open(\".env", ".env.local"):
        assert s not in src, f"forbidden credential/env access string: {s}"


def test_module_import_has_no_side_effect_writes():
    # The 0174ED docs dir must not be created merely by importing the module.
    out_dir = os.path.join(REPO_ROOT, "docs", "automation", "0174ED")
    pre_exists = os.path.isdir(out_dir)
    import importlib
    importlib.reload(model)
    post_exists = os.path.isdir(out_dir)
    # Import must not change whether the dir exists.
    assert pre_exists == post_exists


# --------------------------------------------------------------------------- #
# Canonical payload helper
# --------------------------------------------------------------------------- #
def _payload(**overrides):
    base = dict(
        platform="telegram",
        payload_text="One CPI print is not a regime shift.",
        destination_binding_id="a" * 64,
        credential_handle_id="b" * 64,
        media_manifest_hash="c" * 64,
        visibility_class="public_default",
        content_lane="grounded_news_context",
        policy_snapshot_id="policy_v1",
        platform_adapter_version="telegram_adapter_v1",
        platform_formatting="default",
        thread_split=None,
        disclosure_class="none",
    )
    base.update(overrides)
    return model.canonical_payload_dict(**base)


# --------------------------------------------------------------------------- #
# Hash determinism + sensitivity (tests 1-7)
# --------------------------------------------------------------------------- #
def test_hash_deterministic_for_identical_payloads():
    a = model.compute_payload_hash(_payload())
    b = model.compute_payload_hash(_payload())
    assert a == b
    assert len(a) == 64


def test_hash_changes_on_payload_text_edit():
    base = model.compute_payload_hash(_payload())
    edited = model.compute_payload_hash(_payload(payload_text="Different."))
    assert base != edited


def test_hash_changes_on_platform_edit():
    base = model.compute_payload_hash(_payload())
    edited = model.compute_payload_hash(_payload(platform="x"))
    assert base != edited


def test_hash_changes_on_destination_binding_edit():
    base = model.compute_payload_hash(_payload())
    edited = model.compute_payload_hash(
        _payload(destination_binding_id="d" * 64))
    assert base != edited


def test_hash_changes_on_credential_handle_edit():
    base = model.compute_payload_hash(_payload())
    edited = model.compute_payload_hash(
        _payload(credential_handle_id="e" * 64))
    assert base != edited


def test_hash_changes_on_media_manifest_edit():
    base = model.compute_payload_hash(_payload())
    edited = model.compute_payload_hash(_payload(media_manifest_hash="f" * 64))
    assert base != edited


def test_hash_changes_on_visibility_disclosure_formatting_edit():
    base = model.compute_payload_hash(_payload())
    vis = model.compute_payload_hash(_payload(visibility_class="unlisted"))
    disc = model.compute_payload_hash(_payload(disclosure_class="ad"))
    fmt = model.compute_payload_hash(_payload(platform_formatting="thread"))
    thread = model.compute_payload_hash(_payload(thread_split=["a", "b"]))
    assert len({base, vis, disc, fmt, thread}) == 5


def test_hash_ignores_incidental_extra_keys():
    p = _payload()
    base = model.compute_payload_hash(p)
    p2 = dict(p)
    p2["incidental_display_note"] = "not authority bearing"
    assert model.compute_payload_hash(p2) == base


def test_payload_hash_short_is_16_hex():
    h = model.compute_payload_hash(_payload())
    assert model.payload_hash_short(h) == h[:16]
    assert len(model.payload_hash_short(h)) == 16


# --------------------------------------------------------------------------- #
# Approval lifecycle helpers
# --------------------------------------------------------------------------- #
def _challenge(payload, created=1000, expires=2000):
    return model.create_approval_challenge(
        payload, challenge_id="chal-1", operator_id="jim",
        created_at_epoch=created, expires_at_epoch=expires)


def _approval(payload, challenge, entry_id="led-1", approved=1500):
    return model.record_approval(
        challenge, payload, ledger_entry_id=entry_id,
        approved_at_epoch=approved, operator_id="jim")


# --------------------------------------------------------------------------- #
# Approval validity (tests 8-15)
# --------------------------------------------------------------------------- #
def test_approval_valid_for_same_payload_before_expiry_no_revocation():
    p = _payload()
    ledger = model.ApprovalLedger()
    ch = _challenge(p)
    entry = _approval(p, ch)
    ledger.append_approval(entry)
    res = model.validate_approval_for_current_payload(
        ledger, entry, p, now_epoch=1600)
    assert res["status"] == model.ApprovalStatus.PASS
    assert res["approval_validity_class"] == model.APPROVAL_VALID_CANDIDATE
    assert res["payload_hash_match"] is True
    assert res["binding_match"] is True
    assert res["expired"] is False
    assert res["revoked"] is False
    assert res["blocked_reasons"] == []
    # Even valid, never dispatch/live ready.
    assert res["dispatch_ready"] is False
    assert res["live_ready"] is False
    assert res["approval_authorizes_dispatch"] is False


def test_approval_invalid_after_expiration():
    p = _payload()
    ledger = model.ApprovalLedger()
    ch = _challenge(p, expires=2000)
    entry = _approval(p, ch)
    ledger.append_approval(entry)
    res = model.validate_approval_for_current_payload(
        ledger, entry, p, now_epoch=9999)
    assert res["status"] == model.ApprovalStatus.BLOCKED
    assert res["expired"] is True
    assert "approval_expired" in res["blocked_reasons"]
    assert res["approval_validity_class"] == model.APPROVAL_NOT_VALID


def test_approval_invalid_after_revocation():
    p = _payload()
    ledger = model.ApprovalLedger()
    ch = _challenge(p)
    entry = _approval(p, ch)
    ledger.append_approval(entry)
    rev = model.record_revocation(
        "rev-1", revoked_at_epoch=1550, operator_id="jim",
        ledger_entry_id="led-1")
    ledger.append_revocation(rev)
    res = model.validate_approval_for_current_payload(
        ledger, entry, p, now_epoch=1600)
    assert res["revoked"] is True
    assert "approval_revoked" in res["blocked_reasons"]
    assert res["status"] == model.ApprovalStatus.BLOCKED


def test_approval_invalidated_by_edited_content():
    p = _payload()
    ledger = model.ApprovalLedger()
    ch = _challenge(p)
    entry = _approval(p, ch)
    ledger.append_approval(entry)
    edited = _payload(payload_text="Rewritten calmer hook.")
    res = model.validate_approval_for_current_payload(
        ledger, entry, edited, now_epoch=1600)
    assert res["payload_hash_match"] is False
    assert "payload_hash_mismatch" in res["blocked_reasons"]
    assert res["status"] == model.ApprovalStatus.BLOCKED


def test_approval_invalidated_by_changed_destination_binding():
    p = _payload()
    ledger = model.ApprovalLedger()
    ch = _challenge(p)
    entry = _approval(p, ch)
    ledger.append_approval(entry)
    changed = _payload(destination_binding_id="9" * 64)
    res = model.validate_approval_for_current_payload(
        ledger, entry, changed, now_epoch=1600)
    assert res["binding_match"] is False
    assert "binding_mismatch:destination_binding_id" in res["blocked_reasons"]


def test_approval_invalidated_by_changed_credential_handle():
    p = _payload()
    ledger = model.ApprovalLedger()
    ch = _challenge(p)
    entry = _approval(p, ch)
    ledger.append_approval(entry)
    changed = _payload(credential_handle_id="9" * 64)
    res = model.validate_approval_for_current_payload(
        ledger, entry, changed, now_epoch=1600)
    assert "binding_mismatch:credential_handle_id" in res["blocked_reasons"]


def test_approval_invalidated_by_changed_media_manifest():
    p = _payload()
    ledger = model.ApprovalLedger()
    ch = _challenge(p)
    entry = _approval(p, ch)
    ledger.append_approval(entry)
    changed = _payload(media_manifest_hash="9" * 64)
    res = model.validate_approval_for_current_payload(
        ledger, entry, changed, now_epoch=1600)
    assert "binding_mismatch:media_manifest_hash" in res["blocked_reasons"]


def test_challenge_with_mismatched_hash_cannot_validate():
    # An approval entry whose approved hash does not match the current payload
    # (e.g. a stale/ambiguous challenge) cannot validate.
    p = _payload()
    ledger = model.ApprovalLedger()
    ch = _challenge(p)
    entry = _approval(p, ch)
    ledger.append_approval(entry)
    other = _payload(payload_text="totally different payload")
    res = model.validate_approval_for_current_payload(
        ledger, entry, other, now_epoch=1600)
    assert res["status"] != model.ApprovalStatus.PASS
    assert res["payload_hash_match"] is False


# --------------------------------------------------------------------------- #
# Append-only semantics (test 16)
# --------------------------------------------------------------------------- #
def test_append_only_approval_not_mutated_by_revocation():
    p = _payload()
    ledger = model.ApprovalLedger()
    ch = _challenge(p)
    entry = _approval(p, ch)
    ledger.append_approval(entry)
    snapshot = ledger.find_approval("led-1")
    rev = model.record_revocation(
        "rev-1", revoked_at_epoch=1550, operator_id="jim",
        ledger_entry_id="led-1")
    ledger.append_revocation(rev)
    after = ledger.find_approval("led-1")
    # The approval fact is unchanged; revocation is a separate appended fact.
    assert after == snapshot
    assert len(ledger.approvals()) == 1
    assert len(ledger.revocations()) == 1
    assert ledger.facts[0]["fact_kind"] == model.FACT_APPROVAL
    assert ledger.facts[1]["fact_kind"] == model.FACT_REVOCATION


# --------------------------------------------------------------------------- #
# Redacted audit (test 17)
# --------------------------------------------------------------------------- #
def test_redacted_audit_has_no_secret_material():
    p = _payload()
    ledger = model.ApprovalLedger()
    ch = _challenge(p)
    entry = _approval(p, ch)
    ledger.append_approval(entry)
    res = model.validate_approval_for_current_payload(
        ledger, entry, p, now_epoch=1600)
    audit = model.build_redacted_approval_audit(res, entry)
    assert model.scan_for_leaks(audit) == []
    assert audit["no_raw_credential_stored"] is True
    assert audit["dispatch_ready"] is False
    assert audit["live_ready"] is False
    # Audit carries short hashes only, never full raw payload text.
    assert audit["approval_text_redacted"] == "redacted"
    assert len(audit["approved_payload_hash_short"]) == 16


# --------------------------------------------------------------------------- #
# Fail-closed redaction
# --------------------------------------------------------------------------- #
def test_compute_payload_hash_fails_closed_on_forbidden_value():
    bad = _payload()
    bad["payload_text"] = "bearer AAAAfakebearertokenvalue1234567890"
    with pytest.raises(ValueError):
        model.compute_payload_hash(bad)


def test_validate_fails_closed_on_forbidden_value():
    p = _payload()
    ledger = model.ApprovalLedger()
    ch = _challenge(p)
    entry = _approval(p, ch)
    ledger.append_approval(entry)
    leaky = dict(p)
    leaky["access_token"] = "AAAAabcdefghij1234567890klmno"
    res = model.validate_approval_for_current_payload(
        ledger, entry, leaky, now_epoch=1600)
    assert res["status"] == model.ApprovalStatus.FAIL_CLOSED
    assert res["forbidden_fields_detected"] is True
    assert res["redaction_verified"] is False
    assert res["approval_validity_class"] == model.APPROVAL_FAIL_CLOSED


# --------------------------------------------------------------------------- #
# Dispatch / live-ready never implied (tests 21-22)
# --------------------------------------------------------------------------- #
def test_approval_state_never_implies_dispatch_ready():
    p = _payload()
    ledger = model.ApprovalLedger()
    ch = _challenge(p)
    entry = _approval(p, ch)
    ledger.append_approval(entry)
    # The approval fact itself.
    assert entry["valid_for_dispatch"] is False
    assert entry["dispatch_ready"] is False
    assert entry["live_ready"] is False
    # The validation result.
    res = model.validate_approval_for_current_payload(
        ledger, entry, p, now_epoch=1600)
    assert res["dispatch_ready"] is False
    assert res["live_ready"] is False
    assert res["outbox_entry_created"] is False
    assert res["credential_hydrated"] is False


def test_future_dispatch_state_remains_blocked_in_packet():
    pkt = model.build_packet()
    flags = pkt["safety_flags"]
    assert flags["approval_authorizes_dispatch"] is False
    assert flags["dispatch_ready"] is False
    assert flags["live_ready"] is False
    assert flags["outbox_entry_created"] is False
    assert flags["credential_hydrated"] is False
    assert flags["no_telegram_behavior"] is True
    assert flags["no_llm_behavior"] is True
    assert flags["no_openclaw_runtime"] is True


# --------------------------------------------------------------------------- #
# Ledger packet export
# --------------------------------------------------------------------------- #
def test_export_ledger_packet_is_leak_free_and_counts_facts():
    p = _payload()
    ledger = model.ApprovalLedger()
    ch = _challenge(p)
    entry = _approval(p, ch)
    ledger.append_approval(entry)
    rev = model.record_revocation(
        "rev-1", revoked_at_epoch=1550, operator_id="jim",
        ledger_entry_id="led-1")
    ledger.append_revocation(rev)
    pkt = model.export_ledger_packet(ledger)
    assert pkt["fact_count"] == 2
    assert pkt["approval_count"] == 1
    assert pkt["revocation_count"] == 1
    assert pkt["append_only"] is True
    assert model.scan_for_leaks(pkt) == []


def test_append_wrong_fact_kind_raises():
    ledger = model.ApprovalLedger()
    with pytest.raises(ValueError):
        ledger.append_approval({"fact_kind": model.FACT_REVOCATION})
    with pytest.raises(ValueError):
        ledger.append_revocation({"fact_kind": model.FACT_APPROVAL})


# --------------------------------------------------------------------------- #
# Packet + doc
# --------------------------------------------------------------------------- #
def test_packet_is_leak_free_and_deterministic():
    p1 = model.build_packet()
    p2 = model.build_packet()
    assert model.scan_for_leaks(p1) == []
    assert p1["checksum_sha256"] == p2["checksum_sha256"]
    assert p1["status"] == model.ApprovalStatus.PASS


def test_packet_strategic_posture():
    posture = model.build_packet()["strategic_posture"]
    assert posture["manual_posting"] == "fallback"
    assert posture["automation"] == "main_build_path"
    assert posture["autonomous_posting"] == "forbidden"
    assert posture["supervised_publishing"] == "final_product"


def test_packet_next_task_recommendation():
    pkt = model.build_packet()
    assert pkt["exact_next_task_recommendation"] == (
        "TASK_CONTENTOPS_0174EE_DISPATCH_OUTBOX_AND_IDEMPOTENCY_CONTRACT_V0")


def test_packet_hash_inputs_and_excludes():
    pkt = model.build_packet()
    for f in ("payload_text", "platform", "destination_binding_id",
              "credential_handle_id", "media_manifest_hash",
              "visibility_class", "content_lane", "policy_snapshot_id",
              "platform_adapter_version"):
        assert f in pkt["payload_hash_inputs"]
    for f in ("raw_token", "api_key", "raw_env_var"):
        assert f in pkt["payload_hash_excludes"]


def test_doc_is_leak_free():
    doc = model.build_doc()
    assert model.scan_for_leaks(doc) == []
    assert "0174ED" in doc


def test_write_artifacts_touches_only_0174ed_dir(tmp_path):
    paths = model.write_artifacts(repo_root=str(tmp_path))
    out_dir = tmp_path / "docs" / "automation" / "0174ED"
    written = sorted(p.name for p in out_dir.iterdir())
    assert written == sorted([
        "approval_ledger_payload_hash_contract_packet.json",
        "approval_ledger_payload_hash_contract.md",
    ])
    automation_dir = tmp_path / "docs" / "automation"
    assert sorted(p.name for p in automation_dir.iterdir()) == ["0174ED"]
    assert len(paths) == 2
    # Round-trip the written packet and re-scan it.
    import json
    with open(out_dir / "approval_ledger_payload_hash_contract_packet.json",
              "r", encoding="utf-8") as fh:
        packet = json.load(fh)
    assert model.scan_for_leaks(packet) == []


def test_source_baseline_commit_recorded():
    assert model.SOURCE_BASELINE_COMMIT == (
        "b07e220e4d5fdebeb47368dbc08a10f28c9c4bbd")


# --------------------------------------------------------------------------- #
# R1 hardening: record_approval rejects challenge<->payload substitution
# --------------------------------------------------------------------------- #
def test_r1_record_approval_rejects_edited_text_substitution():
    a = _payload()
    ch = _challenge(a)
    b = _payload(payload_text="substituted body B")
    with pytest.raises(ValueError) as exc:
        _approval(b, ch)
    assert "approval_challenge_payload_hash_mismatch" in str(exc.value)


def test_r1_record_approval_rejects_changed_platform():
    a = _payload()
    ch = _challenge(a)
    b = _payload(platform="x")
    with pytest.raises(ValueError):
        _approval(b, ch)


def test_r1_record_approval_rejects_changed_destination_binding():
    a = _payload()
    ch = _challenge(a)
    b = _payload(destination_binding_id="9" * 64)
    with pytest.raises(ValueError):
        _approval(b, ch)


def test_r1_record_approval_rejects_changed_credential_handle():
    a = _payload()
    ch = _challenge(a)
    b = _payload(credential_handle_id="9" * 64)
    with pytest.raises(ValueError):
        _approval(b, ch)


def test_r1_record_approval_rejects_changed_media_manifest():
    a = _payload()
    ch = _challenge(a)
    b = _payload(media_manifest_hash="9" * 64)
    with pytest.raises(ValueError):
        _approval(b, ch)


def test_r1_record_approval_rejects_changed_visibility():
    a = _payload()
    ch = _challenge(a)
    b = _payload(visibility_class="unlisted")
    with pytest.raises(ValueError):
        _approval(b, ch)


def test_r1_record_approval_rejects_expired_challenge_even_if_hash_matches():
    a = _payload()
    ch = _challenge(a, expires=2000)
    with pytest.raises(ValueError) as exc:
        model.record_approval(
            ch, a, ledger_entry_id="led-1", approved_at_epoch=9999,
            operator_id="jim")
    assert "approval_challenge_expired" in str(exc.value)


def test_r1_record_approval_rejects_non_explicit_response():
    a = _payload()
    ch = _challenge(a)
    with pytest.raises(ValueError) as exc:
        model.record_approval(
            ch, a, ledger_entry_id="led-1", approved_at_epoch=1500,
            operator_id="jim",
            response_class=model.RESPONSE_EXPLICIT_EDIT_REQUEST)
    assert "approval_response_not_explicit_approve" in str(exc.value)


def test_r1_record_approval_rejects_non_pending_challenge():
    a = _payload()
    ch = _challenge(a)
    ch["status"] = model.CHALLENGE_APPROVED
    with pytest.raises(ValueError) as exc:
        _approval(a, ch)
    assert "approval_challenge_not_pending" in str(exc.value)


def test_r1_valid_path_still_records_and_validates():
    a = _payload()
    ledger = model.ApprovalLedger()
    ch = _challenge(a)
    entry = _approval(a, ch)
    ledger.append_approval(entry)
    res = model.validate_approval_for_current_payload(
        ledger, entry, a, now_epoch=1600)
    assert res["approval_validity_class"] == model.APPROVAL_VALID_CANDIDATE
    assert res["status"] == model.ApprovalStatus.PASS


def test_r1_audit_exploit_regression_challenge_a_cannot_approve_payload_b():
    # Exact audit exploit: challenge for A must not approve substituted B.
    a = _payload()
    b = _payload(payload_text="malicious substituted payload B")
    ledger = model.ApprovalLedger()
    ch_a = _challenge(a)
    # 1. record_approval(challenge_A, payload_B) must fail closed.
    with pytest.raises(ValueError):
        model.record_approval(
            ch_a, b, ledger_entry_id="led-b", approved_at_epoch=1500,
            operator_id="jim")
    # 2. No approval fact was appended (nothing was returned to append).
    assert len(ledger.approvals()) == 0
    assert len(ledger.facts) == 0
    # 3. Even the legitimately recorded approval for A cannot validate B.
    entry_a = _approval(a, ch_a)
    ledger.append_approval(entry_a)
    res = model.validate_approval_for_current_payload(
        ledger, entry_a, b, now_epoch=1600)
    assert res["status"] != model.ApprovalStatus.PASS
    assert res["payload_hash_match"] is False


def test_r1_invariant_present_in_packet():
    pkt = model.build_packet()
    assert (
        "record_approval_rejects_challenge_payload_substitution"
        in pkt["invariants"])
