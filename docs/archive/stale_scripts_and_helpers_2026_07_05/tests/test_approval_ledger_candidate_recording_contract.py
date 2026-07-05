"""Tests for 0174TJ approval ledger candidate recording contract."""

import ast
import os

from live_contentops import approval_ledger_candidate_recording_contract as model
from live_contentops import telegram_approval_ledger_candidate_contract as candidate_model
from live_contentops import telegram_review_challenge_contract as review

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(
    REPO_ROOT, "live_contentops", "approval_ledger_candidate_recording_contract.py")

ALLOWED_IMPORT_ROOTS = {"hashlib", "json", "os", "live_contentops"}
FORBIDDEN_IMPORT_ROOTS = {
    "requests", "httpx", "aiohttp", "socket", "socketserver", "ssl",
    "asyncio", "selectors", "http", "urllib", "wsgiref", "webbrowser",
    "subprocess", "dotenv", "ftplib", "smtplib", "multiprocessing",
    "threading", "configparser", "keyring", "secretstorage", "netrc",
    "browser_cookie3", "sqlite3", "pickle", "shelve", "selenium",
    "playwright", "getpass", "openai", "anthropic", "telegram", "tweepy",
    "linkedin", "facebook",
}
FORBIDDEN_STRINGS = (
    "requests.", "httpx.", "aiohttp.", "urllib.", "socket.",
    "import requests", "import httpx", "import aiohttp", "urlopen",
    "http.client", "webbrowser", "getUpdates", "sendMessage",
    "setWebhook", "deleteWebhook", "os.environ", "os.getenv", "getenv(",
    "load_dotenv", "dotenv_values", "keyring.get", "keyring.set",
    "secretstorage.", "netrc(", "ConfigParser", "browser_cookie",
    "sqlite3.", "getpass", "openai.", "anthropic.")


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


def _candidate(reply_text="approve", **overrides):
    challenge_overrides = overrides.pop("challenge", {})
    reply_overrides = overrides.pop("reply", {})
    challenge_base = dict(
        review_challenge_id="review-chal-0174tj-1",
        source_outbox_entry_id="outbox-0174tj-1",
        source_approval_challenge_id="approval-chal-0174tj-1",
        payload_hash="c" * 64,
        payload_hash_short="c" * 16,
        platform="telegram",
        destination_binding_id="dest:telegram:remote-operator-review",
        operator_identity_ref="operator:jim:stable-ref",
        nonce="nonce-0174tj-1",
        created_at_epoch=1000,
        expires_at_epoch=2000,
        prompt_text_redacted="Reply approve/reject/request edit with nonce and hash.",
        evidence_refs=["evidence:0174tj:challenge"],
    )
    challenge_base.update(challenge_overrides)
    challenge = review.build_telegram_review_challenge(**challenge_base)
    reply_base = dict(
        reply_id="reply-0174tj-1",
        source_inbox_message_id="inbox-0174tj-1",
        review_challenge_id=challenge.get("review_challenge_id"),
        operator_identity_ref=challenge.get("operator_identity_ref"),
        reply_text_redacted=reply_text,
        referenced_payload_hash_short=challenge.get("payload_hash_short"),
        referenced_nonce=challenge.get("nonce"),
        received_at_epoch=1500,
        evidence_refs=["evidence:0174tj:reply"],
    )
    reply_base.update(reply_overrides)
    reply = review.build_telegram_review_reply(**reply_base)
    validation = review.validate_review_challenge_reply(challenge, reply)
    return candidate_model.build_approval_ledger_candidate(
        challenge, reply, validation, created_at_epoch=1600)

def test_import_allow_list_exact():
    roots = _module_imports()
    assert roots <= ALLOWED_IMPORT_ROOTS, f"unexpected imports: {roots - ALLOWED_IMPORT_ROOTS}"


def test_no_forbidden_imports():
    roots = _module_imports()
    bad = roots & FORBIDDEN_IMPORT_ROOTS
    assert not bad, f"forbidden imports present: {bad}"


def test_no_network_telegram_env_credential_provider_strings():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in src, f"forbidden string present: {forbidden}"


def test_valid_approval_candidate_records_deterministic_approval_fact():
    candidate = _candidate("approve")
    result = model.record_approval_ledger_candidate(
        candidate, created_at_epoch=1700,
        current_payload_hash=candidate["payload_hash"])
    fact = result["ledger_recording_fact"]
    assert result["recording_status"] == model.STATUS_RECORDED_LOCAL_ONLY
    assert result["ledger_fact_class"] == model.FACT_APPROVAL_RECORDED
    assert result["candidate_hash_match"] is True
    assert result["candidate_validity_match"] is True
    assert result["payload_hash_bound"] is True
    assert result["approval_ledger_recorded"] is True
    assert fact["recording_fact_class"] == model.FACT_APPROVAL_RECORDED
    assert fact["source_candidate_hash"] == candidate["candidate_hash"]
    assert fact["payload_hash"] == candidate["payload_hash"]
    assert len(fact["ledger_recording_fact_id"]) == 64
    assert len(fact["recording_fact_hash"]) == 64


def test_recording_fact_id_and_hash_stable_for_identical_inputs():
    candidate = _candidate("approve")
    first = model.record_approval_ledger_candidate(candidate, 1700)
    second = model.record_approval_ledger_candidate(candidate, 1700)
    assert first["ledger_recording_fact"]["recording_fact_hash"] == second[
        "ledger_recording_fact"]["recording_fact_hash"]
    assert first["ledger_recording_fact"]["ledger_recording_fact_id"] == second[
        "ledger_recording_fact"]["ledger_recording_fact_id"]


def test_candidate_hash_mismatch_blocks_recording():
    candidate = dict(_candidate("approve"))
    candidate["candidate_hash"] = "0" * 64
    result = model.record_approval_ledger_candidate(candidate, 1700)
    assert result["recording_status"] == model.STATUS_BLOCKED
    assert result["ledger_fact_class"] == model.FACT_RECORDING_BLOCKED
    assert result["candidate_hash_match"] is False
    assert model.BLOCK_CANDIDATE_HASH_MISMATCH in result["blocked_reasons"]
    assert result["approval_ledger_recorded"] is False


def test_payload_hash_mutation_blocks_recording():
    candidate = _candidate("approve")
    result = model.record_approval_ledger_candidate(
        candidate, 1700, current_payload_hash="d" * 64)
    assert result["recording_status"] == model.STATUS_BLOCKED
    assert result["payload_hash_bound"] is False
    assert model.BLOCK_PAYLOAD_HASH_MISMATCH in result["blocked_reasons"]
    assert result["ledger_fact_class"] == model.FACT_RECORDING_BLOCKED


def test_blocked_candidate_cannot_record_approval():
    candidate = _candidate("approve", reply={"referenced_nonce": "wrong"})
    result = model.record_approval_ledger_candidate(candidate, 1700)
    assert candidate["candidate_validity_class"] == candidate_model.VALIDITY_BLOCKED
    assert result["recording_status"] == model.STATUS_BLOCKED
    assert result["ledger_fact_class"] == model.FACT_RECORDING_BLOCKED
    assert result["approval_ledger_recorded"] is False
    assert model.BLOCK_CANDIDATE_VALIDITY_MISMATCH in result["blocked_reasons"]


def test_reject_candidate_records_reject_fact_only():
    candidate = _candidate("reject")
    result = model.record_approval_ledger_candidate(candidate, 1700)
    fact = result["ledger_recording_fact"]
    assert candidate["candidate_intent_class"] == candidate_model.INTENT_REJECT
    assert result["recording_status"] == model.STATUS_RECORDED_LOCAL_ONLY
    assert result["ledger_fact_class"] == model.FACT_REJECT_RECORDED
    assert fact["recording_fact_class"] == model.FACT_REJECT_RECORDED
    assert result["approval_ledger_recorded"] is False
    assert result["ledger_fact_class"] != model.FACT_APPROVAL_RECORDED


def test_edit_request_candidate_records_edit_request_fact_only():
    candidate = _candidate("request edit")
    result = model.record_approval_ledger_candidate(candidate, 1700)
    fact = result["ledger_recording_fact"]
    assert candidate["candidate_intent_class"] == candidate_model.INTENT_EDIT_REQUEST
    assert result["recording_status"] == model.STATUS_RECORDED_LOCAL_ONLY
    assert result["ledger_fact_class"] == model.FACT_EDIT_REQUEST_RECORDED
    assert fact["recording_fact_class"] == model.FACT_EDIT_REQUEST_RECORDED
    assert result["approval_ledger_recorded"] is False
    assert result["ledger_fact_class"] != model.FACT_APPROVAL_RECORDED


def test_duplicate_fact_is_suppressed():
    candidate = _candidate("approve")
    registry = model.ApprovalLedgerRecordingRegistry()
    first = model.record_approval_ledger_candidate(candidate, 1700)
    second = model.record_approval_ledger_candidate(candidate, 1700)
    first_append = registry.append(first)
    duplicate = registry.append(second)
    assert first_append["recording_status"] == model.STATUS_RECORDED_LOCAL_ONLY
    assert duplicate["recording_status"] == model.STATUS_DUPLICATE_SUPPRESSED
    assert duplicate["ledger_fact_class"] == model.FACT_DUPLICATE_SUPPRESSED
    assert duplicate["duplicate_fact_suppressed"] is True
    assert model.BLOCK_DUPLICATE_FACT in duplicate["blocked_reasons"]
    assert len(registry.facts()) == 1


def test_missing_evidence_refs_blocks_recording():
    candidate = dict(_candidate("approve"))
    candidate["evidence_refs"] = []
    candidate["candidate_hash"] = candidate_model.compute_candidate_hash(candidate)
    result = model.record_approval_ledger_candidate(candidate, 1700)
    assert result["recording_status"] == model.STATUS_BLOCKED
    assert model.BLOCK_MISSING_EVIDENCE_REFS in result["blocked_reasons"]
    assert result["approval_ledger_recorded"] is False


def test_recorded_approval_never_authorizes_dispatch_or_live():
    result = model.record_approval_ledger_candidate(_candidate("approve"), 1700)
    fact = result["ledger_recording_fact"]
    for obj in (result, fact):
        assert obj["approval_authorizes_dispatch"] is False
        assert obj["valid_for_dispatch"] is False
        assert obj["outbox_mutated"] is False
        assert obj["dispatch_ready"] is False
        assert obj["live_ready"] is False
        assert obj["public_postable"] is False


def test_safety_flags_prove_no_outbox_or_live_behavior():
    result = model.record_approval_ledger_candidate(_candidate("approve"), 1700)
    for key, value in result["safety_flags"].items():
        if key == "approval_ledger_recorded":
            assert value is True
        else:
            assert value is False, key
    fact = result["ledger_recording_fact"]
    assert fact["safety_flags"]["approval_ledger_recorded"] is True
    assert fact["safety_flags"]["telegram_api_called"] is False
    assert fact["safety_flags"]["network_performed"] is False
    assert fact["safety_flags"]["env_read"] is False
    assert fact["safety_flags"]["llm_provider_called"] is False


def test_packet_is_deterministic_and_leak_free():
    first = model.build_packet()
    second = model.build_packet()
    assert first == second
    assert len(first["checksum_sha256"]) == 64
    assert model.scan_for_leaks(first) == []
    assert first["safety_flags"]["telegram_api_called"] is False
    assert first["safety_flags"]["network_performed"] is False
    assert first["safety_flags"]["llm_provider_called"] is False


def test_artifact_writer_touches_only_0174tj(tmp_path):
    out = model.write_artifacts(str(tmp_path))
    rel_packet = os.path.relpath(out["packet_path"], str(tmp_path))
    rel_doc = os.path.relpath(out["doc_path"], str(tmp_path))
    assert rel_packet == os.path.join(
        "docs", "automation", "0174TJ",
        "approval_ledger_candidate_recording_contract_packet.json")
    assert rel_doc == os.path.join(
        "docs", "automation", "0174TJ",
        "approval_ledger_candidate_recording_contract.md")
    assert os.path.exists(out["packet_path"])
    assert os.path.exists(out["doc_path"])


def test_recording_does_not_mutate_candidate_or_imply_outbox_change():
    candidate = _candidate("approve")
    before = dict(candidate)
    result = model.record_approval_ledger_candidate(candidate, 1700)
    assert candidate == before
    assert result["outbox_mutated"] is False
    assert result["ledger_recording_fact"]["outbox_mutated"] is False
    assert result["ledger_recording_fact"]["source_outbox_entry_id"] == candidate[
        "source_outbox_entry_id"]

