"""Tests for the 0174EE dispatch outbox + idempotency + preflight contract.

These tests prove the module is deterministic, stdlib-only, secret-free, and
fail-closed, and that:
  * the static import surface is an exact stdlib + 0174ED allow-list with no
    requests/httpx/aiohttp/socket/ssl/http server, no selenium/playwright, no
    dotenv/keyring/sqlite, no provider/platform SDKs,
  * importing the module performs NO network/env/credential read and NO write,
  * the idempotency key is deterministic and changes when ANY authority-bearing
    input changes (payload hash/platform/binding/credential handle/media/
    visibility/dispatch intent/policy snapshot),
  * a local outbox entry is created ONLY from a PASSED 0174ED approval
    validation and a symbolic-only credential handle, behind a present gate
    snapshot that allows local outbox candidacy,
  * invalid/expired/revoked approvals, hash/binding mismatches, missing
    validation, missing gate snapshot, blocking gate snapshot, and non-symbolic
    credentials all block,
  * duplicate idempotency keys are suppressed (not appended),
  * nothing is ever marked dispatched/live/platform-API/auto-retry/scheduler,
  * redacted audit objects contain no raw token/api-key/secret-like material,
  * the packet + doc are leak-free and deterministic, and
  * an approval valid for payload A cannot create an outbox for payload B.
"""

import ast
import os

import pytest

from live_contentops import approval_ledger_payload_hash_contract as approval
from live_contentops import dispatch_outbox_idempotency_contract as model


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(
    REPO_ROOT, "live_contentops",
    "dispatch_outbox_idempotency_contract.py")


ALLOWED_IMPORT_ROOTS = {"hashlib", "json", "os", "re", "live_contentops"}
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
# Import surface (tests 26-27)
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
    out_dir = os.path.join(REPO_ROOT, "docs", "automation", "0174EE")
    pre_exists = os.path.isdir(out_dir)
    import importlib
    importlib.reload(model)
    post_exists = os.path.isdir(out_dir)
    assert pre_exists == post_exists


# --------------------------------------------------------------------------- #
# Helpers: build a valid 0174ED approval + validation, then a 0174EE candidate
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
    return approval.canonical_payload_dict(**base)


def _approved(payload, created=1000, expires=2000, approved=1500):
    """Return (ledger, approval_entry) for an exact, valid approval of payload."""
    ledger = approval.ApprovalLedger()
    ch = approval.create_approval_challenge(
        payload, challenge_id="chal-1", operator_id="jim",
        created_at_epoch=created, expires_at_epoch=expires)
    entry = approval.record_approval(
        ch, payload, ledger_entry_id="led-1", approved_at_epoch=approved,
        operator_id="jim")
    ledger.append_approval(entry)
    return ledger, entry


def _valid_inputs(payload=None, now=1600):
    payload = payload or _payload()
    ledger, entry = _approved(payload)
    vres = approval.validate_approval_for_current_payload(
        ledger, entry, payload, now_epoch=now)
    return payload, entry, vres


def _candidate(payload=None, **overrides):
    payload, entry, vres = _valid_inputs(payload)
    kwargs = dict(
        dispatch_intent_class=model.INTENT_SUPERVISED_SINGLE,
        gate_snapshot_class=model.GATE_ALLOWS_LOCAL_OUTBOX,
        gate_snapshot_id="gate_v1", operator_id="jim")
    kwargs.update(overrides)
    return model.build_outbox_candidate(payload, entry, vres, **kwargs)


def _preflight(payload=None, **overrides):
    payload, entry, vres = _valid_inputs(payload)
    kwargs = dict(
        dispatch_intent_class=model.INTENT_SUPERVISED_SINGLE,
        gate_snapshot_class=model.GATE_ALLOWS_LOCAL_OUTBOX,
        gate_snapshot_id="gate_v1", operator_id="jim")
    kwargs.update(overrides)
    return model.run_dispatch_preflight(payload, entry, vres, **kwargs)


# --------------------------------------------------------------------------- #
# Idempotency key determinism + sensitivity (tests 1-9, 22)
# --------------------------------------------------------------------------- #
def test_idempotency_key_deterministic_for_identical_candidate():
    a = model.compute_idempotency_key(_candidate())
    b = model.compute_idempotency_key(_candidate())
    assert a == b
    assert len(a) == 64


def test_idempotency_key_changes_on_payload_hash_change():
    base = model.compute_idempotency_key(_candidate())
    other = model.compute_idempotency_key(
        _candidate(_payload(payload_text="Different body entirely.")))
    assert base != other


def test_idempotency_key_changes_on_platform_change():
    base = model.compute_idempotency_key(_candidate())
    other = model.compute_idempotency_key(_candidate(_payload(platform="x")))
    assert base != other


def test_idempotency_key_changes_on_destination_binding_change():
    base = model.compute_idempotency_key(_candidate())
    other = model.compute_idempotency_key(
        _candidate(_payload(destination_binding_id="d" * 64)))
    assert base != other


def test_idempotency_key_changes_on_credential_handle_change():
    base = model.compute_idempotency_key(_candidate())
    other = model.compute_idempotency_key(
        _candidate(_payload(credential_handle_id="e" * 64)))
    assert base != other


def test_idempotency_key_changes_on_media_manifest_change():
    base = model.compute_idempotency_key(_candidate())
    other = model.compute_idempotency_key(
        _candidate(_payload(media_manifest_hash="f" * 64)))
    assert base != other


def test_idempotency_key_changes_on_visibility_change():
    base = model.compute_idempotency_key(_candidate())
    other = model.compute_idempotency_key(
        _candidate(_payload(visibility_class="unlisted")))
    assert base != other


def test_idempotency_key_changes_on_dispatch_intent_change():
    base = model.compute_idempotency_key(_candidate())
    other = model.compute_idempotency_key(
        _candidate(dispatch_intent_class=model.INTENT_DRY_RUN))
    assert base != other


def test_idempotency_key_changes_on_gate_snapshot_change():
    base = model.compute_idempotency_key(_candidate())
    other = model.compute_idempotency_key(_candidate(gate_snapshot_id="gate_v2"))
    assert base != other


def test_idempotency_key_changes_on_different_payload():
    base = model.compute_idempotency_key(_candidate())
    other = model.compute_idempotency_key(
        _candidate(_payload(payload_text="A wholly separate post.")))
    assert base != other


def test_idempotency_key_ignores_incidental_extra_keys():
    cand = _candidate()
    base = model.compute_idempotency_key(cand)
    cand2 = dict(cand)
    cand2["incidental_display_note"] = "not authority bearing"
    assert model.compute_idempotency_key(cand2) == base


# --------------------------------------------------------------------------- #
# Preflight pass + blocking (tests 10-19)
# --------------------------------------------------------------------------- #
def test_valid_approval_creates_local_outbox_entry():
    pre = _preflight()
    assert pre["status"] == model.OutboxStatus.PASS
    assert pre["outbox_eligibility_class"] == model.OUTBOX_ELIGIBLE
    assert pre["blocked_reasons"] == []
    assert pre["idempotency_key"] and len(pre["idempotency_key"]) == 64
    reg = model.DispatchOutboxRegistry()
    res = reg.submit(pre, outbox_entry_id="ob-1", created_at_epoch=1700)
    assert res["appended"] is True
    assert res["state_class"] == model.STATE_LOCAL_RECORD_CREATED
    assert res["entry"]["outbox_created"] is True
    assert res["entry"]["eligible_for_local_outbox"] is True


def test_invalid_approval_blocks_outbox():
    p = _payload()
    ledger, entry = _approved(p)
    edited = _payload(payload_text="Edited after approval.")
    vres = approval.validate_approval_for_current_payload(
        ledger, entry, edited, now_epoch=1600)
    pre = model.run_dispatch_preflight(
        edited, entry, vres, gate_snapshot_id="gate_v1")
    assert pre["status"] == model.OutboxStatus.BLOCKED
    assert pre["candidate"] is None
    assert pre["idempotency_key"] is None


def test_expired_approval_blocks_outbox():
    p = _payload()
    ledger, entry = _approved(p, expires=2000)
    vres = approval.validate_approval_for_current_payload(
        ledger, entry, p, now_epoch=9999)
    pre = model.run_dispatch_preflight(
        p, entry, vres, gate_snapshot_id="gate_v1")
    assert pre["status"] == model.OutboxStatus.BLOCKED
    assert model.BLOCK_EXPIRED in pre["blocked_reasons"]


def test_revoked_approval_blocks_outbox():
    p = _payload()
    ledger, entry = _approved(p)
    rev = approval.record_revocation(
        "rev-1", revoked_at_epoch=1550, operator_id="jim",
        ledger_entry_id="led-1")
    ledger.append_revocation(rev)
    vres = approval.validate_approval_for_current_payload(
        ledger, entry, p, now_epoch=1600)
    pre = model.run_dispatch_preflight(
        p, entry, vres, gate_snapshot_id="gate_v1")
    assert pre["status"] == model.OutboxStatus.BLOCKED
    assert model.BLOCK_REVOKED in pre["blocked_reasons"]


def test_hash_mismatch_blocks_outbox():
    p = _payload()
    ledger, entry = _approved(p)
    other = _payload(payload_text="totally different payload")
    vres = approval.validate_approval_for_current_payload(
        ledger, entry, other, now_epoch=1600)
    pre = model.run_dispatch_preflight(
        other, entry, vres, gate_snapshot_id="gate_v1")
    assert pre["status"] == model.OutboxStatus.BLOCKED
    assert model.BLOCK_HASH_MISMATCH in pre["blocked_reasons"]


def test_binding_mismatch_blocks_outbox():
    p = _payload()
    ledger, entry = _approved(p)
    changed = _payload(destination_binding_id="9" * 64)
    vres = approval.validate_approval_for_current_payload(
        ledger, entry, changed, now_epoch=1600)
    pre = model.run_dispatch_preflight(
        changed, entry, vres, gate_snapshot_id="gate_v1")
    assert pre["status"] == model.OutboxStatus.BLOCKED
    assert any(r.startswith(model.BLOCK_BINDING_MISMATCH)
               for r in pre["blocked_reasons"])


def test_missing_approval_validation_blocks_outbox():
    p = _payload()
    _ledger, entry = _approved(p)
    pre = model.run_dispatch_preflight(
        p, entry, None, gate_snapshot_id="gate_v1")
    assert pre["status"] == model.OutboxStatus.BLOCKED
    assert model.BLOCK_MISSING_VALIDATION in pre["blocked_reasons"]


def test_missing_gate_snapshot_blocks_outbox():
    pre = _preflight(gate_snapshot_id=None)
    assert pre["status"] == model.OutboxStatus.BLOCKED
    assert model.BLOCK_GATE_SNAPSHOT_MISSING in pre["blocked_reasons"]


def test_gate_snapshot_blocking_blocks_outbox():
    pre = _preflight(gate_snapshot_class=model.GATE_BLOCKS_OUTBOX)
    assert pre["status"] == model.OutboxStatus.BLOCKED
    assert model.BLOCK_GATE_SNAPSHOT_BLOCKS in pre["blocked_reasons"]


def test_non_symbolic_credential_blocks_outbox():
    # A clean (non-secret-shaped) but non-symbolic credential handle: contains
    # spaces, so it is neither a hex digest nor a clean class label.
    p = _payload(credential_handle_id="not a symbolic handle")
    ledger, entry = _approved(p)
    vres = approval.validate_approval_for_current_payload(
        ledger, entry, p, now_epoch=1600)
    pre = model.run_dispatch_preflight(
        p, entry, vres, gate_snapshot_id="gate_v1")
    assert pre["status"] == model.OutboxStatus.BLOCKED
    assert model.BLOCK_CREDENTIAL_NOT_SYMBOLIC in pre["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Duplicate suppression (tests 20-21)
# --------------------------------------------------------------------------- #
def test_duplicate_idempotency_key_suppresses_duplicate_entry():
    pre = _preflight()
    reg = model.DispatchOutboxRegistry()
    first = reg.submit(pre, outbox_entry_id="ob-1", created_at_epoch=1700)
    second = reg.submit(pre, outbox_entry_id="ob-2", created_at_epoch=1800)
    assert first["appended"] is True
    assert second["appended"] is False
    assert second["duplicate_suppressed"] is True
    assert second["state_class"] == model.STATE_DUPLICATE_SUPPRESSED
    assert model.BLOCK_DUPLICATE_KEY in second["blocked_reasons"]


def test_duplicate_suppression_returns_existing_and_does_not_append():
    pre = _preflight()
    reg = model.DispatchOutboxRegistry()
    first = reg.submit(pre, outbox_entry_id="ob-1", created_at_epoch=1700)
    second = reg.submit(pre, outbox_entry_id="ob-2", created_at_epoch=1800)
    assert reg.entry_count() == 1
    assert second["outbox_entry_id"] == first["outbox_entry_id"] == "ob-1"
    assert second["idempotency_key"] == first["idempotency_key"]


def test_different_payload_creates_separate_idempotency_key_and_entry():
    pre_a = _preflight()
    pre_b = _preflight(_payload(payload_text="A different approved post."))
    assert pre_a["idempotency_key"] != pre_b["idempotency_key"]
    reg = model.DispatchOutboxRegistry()
    reg.submit(pre_a, outbox_entry_id="ob-a", created_at_epoch=1700)
    res_b = reg.submit(pre_b, outbox_entry_id="ob-b", created_at_epoch=1700)
    assert res_b["appended"] is True
    assert reg.entry_count() == 2


# --------------------------------------------------------------------------- #
# Safety invariants (tests 23-24)
# --------------------------------------------------------------------------- #
def test_outbox_entry_never_marks_dispatch_live_or_platform_api():
    pre = _preflight()
    reg = model.DispatchOutboxRegistry()
    res = reg.submit(pre, outbox_entry_id="ob-1", created_at_epoch=1700)
    entry = res["entry"]
    for obj in (pre, res, entry):
        assert obj["dispatch_performed"] is False
        assert obj["live_request_performed"] is False
        assert obj["platform_api_called"] is False
        assert obj["credential_hydrated"] is False


def test_outbox_entry_never_enables_auto_retry_or_scheduler():
    pre = _preflight()
    reg = model.DispatchOutboxRegistry()
    res = reg.submit(pre, outbox_entry_id="ob-1", created_at_epoch=1700)
    entry = res["entry"]
    for obj in (pre, res, entry):
        assert obj["auto_retry_allowed"] is False
        assert obj["scheduler_enabled"] is False
        assert obj["telegram_behavior"] is False
        assert obj["llm_behavior"] is False


def test_outbox_entry_contains_requested_contract_fields():
    pre = _preflight()
    reg = model.DispatchOutboxRegistry()
    res = reg.submit(pre, outbox_entry_id="ob-1", created_at_epoch=1700)
    entry = res["entry"]
    for field in (
            "outbox_entry_id", "source_approval_ledger_entry_id",
            "approval_challenge_id", "payload_hash", "payload_hash_short",
            "platform", "platform_payload_class", "destination_binding_id",
            "credential_handle_id", "media_manifest_hash", "approval_scope",
            "idempotency_key", "idempotency_basis", "created_at_epoch",
            "requested_by_operator_id", "status", "blocked_reasons",
            "evidence_refs", "redacted_audit_refs"):
        assert field in entry
    assert entry["status"] == model.STATE_ENTRY_CREATED_BLOCKED
    assert entry["blocked_reasons"] == [model.STATE_MISSING_FUTURE_GATE_BLOCKED]
    assert entry["evidence_refs"]


def test_outbox_entry_exact_safety_flags_false_or_blocked():
    pre = _preflight()
    reg = model.DispatchOutboxRegistry()
    res = reg.submit(pre, outbox_entry_id="ob-1", created_at_epoch=1700)
    entry = res["entry"]
    for obj in (pre, res, entry):
        assert obj["dispatch_ready"] is False
        assert obj["live_ready"] is False
        assert obj["platform_api_called"] is False
        assert obj["provider_api_called"] is False
        assert obj["credential_hydrated"] is False
        assert obj["scheduler_enabled"] is False
        assert obj["public_postable"] is False
        assert obj["autonomous_posting_allowed"] is False
        assert obj["outbox_only"] is True


def test_missing_evidence_refs_blocks_outbox_creation():
    p = _payload()
    ledger, entry = _approved(p)
    entry = dict(entry)
    entry["evidence_refs"] = []
    vres = approval.validate_approval_for_current_payload(
        ledger, entry, p, now_epoch=1600)
    pre = model.run_dispatch_preflight(
        p, entry, vres, gate_snapshot_id="gate_v1")
    assert pre["status"] == model.OutboxStatus.BLOCKED
    assert model.BLOCK_EVIDENCE_REFS_MISSING in pre["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Fail-closed redaction + redacted audit (tests 25, 19-family)
# --------------------------------------------------------------------------- #
def test_forbidden_value_fails_closed_in_preflight():
    p = _payload()
    ledger, entry = _approved(p)
    vres = approval.validate_approval_for_current_payload(
        ledger, entry, p, now_epoch=1600)
    leaky = dict(p)
    leaky["access_token"] = "AAAAabcdefghij1234567890klmno"
    pre = model.run_dispatch_preflight(
        leaky, entry, vres, gate_snapshot_id="gate_v1")
    assert pre["status"] == model.OutboxStatus.FAIL_CLOSED
    assert pre["forbidden_fields_detected"] is True
    assert pre["outbox_eligibility_class"] == model.OUTBOX_FAIL_CLOSED
    assert model.BLOCK_FORBIDDEN_VALUE in pre["blocked_reasons"]


def test_compute_idempotency_key_fails_closed_on_forbidden_value():
    cand = _candidate()
    cand["raw_token"] = "AAAAfakebearertokenvalue1234567890"
    with pytest.raises(ValueError):
        model.compute_idempotency_key(cand)


def test_redacted_audit_has_no_secret_material():
    pre = _preflight()
    reg = model.DispatchOutboxRegistry()
    res = reg.submit(pre, outbox_entry_id="ob-1", created_at_epoch=1700)
    audit = model.build_redacted_outbox_audit(pre, res["entry"])
    assert model.scan_for_leaks(audit) == []
    assert audit["no_raw_credential_stored"] is True
    assert audit["dispatch_performed"] is False
    assert audit["auto_retry_allowed"] is False
    assert len(audit["payload_hash_short"]) == 16


# --------------------------------------------------------------------------- #
# Integration + regression (tests 29-30)
# --------------------------------------------------------------------------- #
def test_integration_with_0174ed_valid_path():
    # Full chain: canonical payload -> challenge -> approval -> validation ->
    # preflight -> outbox entry, all via the real 0174ED module.
    p = _payload()
    ledger, entry = _approved(p)
    vres = approval.validate_approval_for_current_payload(
        ledger, entry, p, now_epoch=1600)
    assert vres["approval_validity_class"] == approval.APPROVAL_VALID_CANDIDATE
    pre = model.run_dispatch_preflight(
        p, entry, vres, gate_snapshot_id="gate_v1", operator_id="jim")
    assert pre["status"] == model.OutboxStatus.PASS
    reg = model.DispatchOutboxRegistry()
    res = reg.submit(pre, outbox_entry_id="ob-1", created_at_epoch=1700)
    assert res["appended"] is True


def test_regression_approval_for_a_cannot_create_outbox_for_b():
    a = _payload()
    b = _payload(payload_text="malicious substituted payload B")
    ledger, entry_a = _approved(a)
    # Validate the approval for A against substituted payload B.
    vres_b = approval.validate_approval_for_current_payload(
        ledger, entry_a, b, now_epoch=1600)
    pre = model.run_dispatch_preflight(
        b, entry_a, vres_b, gate_snapshot_id="gate_v1")
    assert pre["status"] != model.OutboxStatus.PASS
    assert pre["candidate"] is None
    assert pre["idempotency_key"] is None
    reg = model.DispatchOutboxRegistry()
    with pytest.raises(ValueError):
        reg.submit(pre, outbox_entry_id="ob-b", created_at_epoch=1700)
    assert reg.entry_count() == 0


# --------------------------------------------------------------------------- #
# Packet + doc (test 28)
# --------------------------------------------------------------------------- #
def test_packet_is_leak_free_and_deterministic():
    p1 = model.build_packet()
    p2 = model.build_packet()
    assert model.scan_for_leaks(p1) == []
    assert p1["checksum_sha256"] == p2["checksum_sha256"]
    assert p1["status"] == model.OutboxStatus.PASS


def test_packet_safety_flags_and_posture():
    pkt = model.build_packet()
    flags = pkt["safety_flags"]
    assert flags["dispatch_performed"] is False
    assert flags["live_request_performed"] is False
    assert flags["platform_api_called"] is False
    assert flags["credential_hydrated"] is False
    assert flags["auto_retry_allowed"] is False
    assert flags["scheduler_enabled"] is False
    assert flags["telegram_behavior"] is False
    assert flags["llm_behavior"] is False
    assert flags["no_openclaw_runtime"] is True
    posture = pkt["strategic_posture"]
    assert posture["automation"] == "main_build_path"
    assert posture["autonomous_posting"] == "forbidden"


def test_packet_next_task_recommendation():
    pkt = model.build_packet()
    assert pkt["exact_next_task_recommendation"] == (
        "TASK_CONTENTOPS_0174TG_TELEGRAM_REMOTE_OPERATOR_INBOX_CONTRACT_V0")


def test_packet_key_inputs_and_excludes():
    pkt = model.build_packet()
    for f in ("payload_hash", "platform", "platform_payload_class",
              "destination_binding_id", "credential_handle_id",
              "media_manifest_hash", "approval_scope",
              "dispatch_intent_class", "policy_snapshot_id",
              "platform_adapter_version", "source_approval_ledger_entry_id",
              "approval_challenge_id", "requested_by_operator_id"):
        assert f in pkt["idempotency_key_inputs"]
    for f in ("raw_token", "api_key", "raw_env_var", "request_headers",
              "cookies"):
        assert f in pkt["idempotency_key_excludes"]


def test_doc_is_leak_free():
    doc = model.build_doc()
    assert model.scan_for_leaks(doc) == []
    assert "0174EE" in doc


def test_write_artifacts_touches_only_0174ee_dir(tmp_path):
    paths = model.write_artifacts(repo_root=str(tmp_path))
    out_dir = tmp_path / "docs" / "automation" / "0174EE"
    written = sorted(p.name for p in out_dir.iterdir())
    assert written == sorted([
        "dispatch_outbox_idempotency_contract_packet.json",
        "dispatch_outbox_idempotency_contract.md",
    ])
    automation_dir = tmp_path / "docs" / "automation"
    assert sorted(p.name for p in automation_dir.iterdir()) == ["0174EE"]
    assert len(paths) == 2
    import json
    with open(out_dir / "dispatch_outbox_idempotency_contract_packet.json",
              "r", encoding="utf-8") as fh:
        packet = json.load(fh)
    assert model.scan_for_leaks(packet) == []


def test_source_baseline_commit_recorded():
    assert model.SOURCE_BASELINE_COMMIT == (
        "8cc0b87716d13c33352e9a3918bd35e1a685a75b")


# --------------------------------------------------------------------------- #
# R1 authority-chain hardening: preflight recomputes the current payload hash
# and fails closed on any stale/foreign validation-result pairing.
# --------------------------------------------------------------------------- #
def test_r1_valid_path_still_passes():
    pre = _preflight()
    assert pre["status"] == model.OutboxStatus.PASS
    assert pre["blocked_reasons"] == []
    assert pre["candidate"] is not None
    assert pre["idempotency_key"] and len(pre["idempotency_key"]) == 64


def _stale_validation_pairing(text_b="substituted body B only text changed"):
    """Build validation for payload A, then a payload B with only text changed
    so binding fields still match. Returns (payload_b, entry_a, vres_a)."""
    a = _payload()
    ledger, entry_a = _approved(a)
    vres_a = approval.validate_approval_for_current_payload(
        ledger, entry_a, a, now_epoch=1600)
    b = _payload(payload_text=text_b)
    return b, entry_a, vres_a


def test_r1_stale_validation_a_with_payload_b_blocks():
    b, entry_a, vres_a = _stale_validation_pairing()
    pre = model.run_dispatch_preflight(
        b, entry_a, vres_a, gate_snapshot_id="gate_v1")
    assert pre["status"] == model.OutboxStatus.BLOCKED
    assert model.BLOCK_VALIDATION_HASH_MISMATCH_CURRENT in pre["blocked_reasons"]


def test_r1_stale_validation_a_with_payload_b_no_candidate_or_key():
    b, entry_a, vres_a = _stale_validation_pairing()
    pre = model.run_dispatch_preflight(
        b, entry_a, vres_a, gate_snapshot_id="gate_v1")
    assert pre["candidate"] is None
    assert pre["idempotency_key"] is None


def test_r1_registry_submit_on_blocked_stale_pairing_raises_and_appends_none():
    b, entry_a, vres_a = _stale_validation_pairing()
    pre = model.run_dispatch_preflight(
        b, entry_a, vres_a, gate_snapshot_id="gate_v1")
    reg = model.DispatchOutboxRegistry()
    with pytest.raises(ValueError):
        reg.submit(pre, outbox_entry_id="ob-b", created_at_epoch=1700)
    assert reg.entry_count() == 0


def test_r1_stale_validation_hash_mismatch_reason_present():
    b, entry_a, vres_a = _stale_validation_pairing()
    pre = model.run_dispatch_preflight(
        b, entry_a, vres_a, gate_snapshot_id="gate_v1")
    assert (model.BLOCK_VALIDATION_HASH_MISMATCH_CURRENT
            in pre["blocked_reasons"])


def test_r1_validation_approved_hash_mismatch_against_entry_blocks():
    p = _payload()
    _ledger, entry = _approved(p)
    vres = approval.validate_approval_for_current_payload(
        _ledger, entry, p, now_epoch=1600)
    tampered = dict(vres)
    tampered["approved_payload_hash"] = "9" * 64
    pre = model.run_dispatch_preflight(
        p, entry, tampered, gate_snapshot_id="gate_v1")
    assert pre["status"] == model.OutboxStatus.BLOCKED
    assert (model.BLOCK_VALIDATION_APPROVED_HASH_MISMATCH_ENTRY
            in pre["blocked_reasons"])


def test_r1_validation_ledger_entry_id_mismatch_blocks():
    p = _payload()
    _ledger, entry = _approved(p)
    vres = approval.validate_approval_for_current_payload(
        _ledger, entry, p, now_epoch=1600)
    tampered = dict(vres)
    tampered["ledger_entry_id"] = "led-foreign"
    pre = model.run_dispatch_preflight(
        p, entry, tampered, gate_snapshot_id="gate_v1")
    assert pre["status"] == model.OutboxStatus.BLOCKED
    assert model.BLOCK_VALIDATION_ENTRY_MISMATCH in pre["blocked_reasons"]


def test_r1_validation_challenge_id_mismatch_blocks():
    p = _payload()
    _ledger, entry = _approved(p)
    vres = approval.validate_approval_for_current_payload(
        _ledger, entry, p, now_epoch=1600)
    tampered = dict(vres)
    tampered["challenge_id"] = "chal-foreign"
    pre = model.run_dispatch_preflight(
        p, entry, tampered, gate_snapshot_id="gate_v1")
    assert pre["status"] == model.OutboxStatus.BLOCKED
    assert model.BLOCK_VALIDATION_CHALLENGE_MISMATCH in pre["blocked_reasons"]


def test_r1_candidate_uses_recomputed_payload_hash_on_valid_path():
    p = _payload()
    _ledger, entry = _approved(p)
    vres = approval.validate_approval_for_current_payload(
        _ledger, entry, p, now_epoch=1600)
    expected = approval.compute_payload_hash(p)
    pre = model.run_dispatch_preflight(
        p, entry, vres, gate_snapshot_id="gate_v1")
    assert pre["status"] == model.OutboxStatus.PASS
    assert pre["candidate"]["payload_hash"] == expected
    assert pre["current_payload_hash"] == expected


def test_r1_invariants_present_in_packet():
    pkt = model.build_packet()
    assert (
        "preflight_recomputes_current_payload_hash_before_outbox"
        in pkt["invariants"])
    assert "stale_validation_result_cannot_create_outbox" in pkt["invariants"]
    for reason in (
            model.BLOCK_VALIDATION_HASH_MISMATCH_CURRENT,
            model.BLOCK_VALIDATION_APPROVED_HASH_MISMATCH_ENTRY,
            model.BLOCK_VALIDATION_ENTRY_MISMATCH,
            model.BLOCK_VALIDATION_CHALLENGE_MISMATCH):
        assert reason in pkt["blocked_reasons"]
