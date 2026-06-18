"""Tests for 0174TG Telegram remote operator inbox contract."""

import ast
import os

from live_contentops import telegram_remote_operator_inbox_contract as model

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(
    REPO_ROOT, "live_contentops",
    "telegram_remote_operator_inbox_contract.py")

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


def _message(**overrides):
    base = dict(
        inbox_message_id="msg-1",
        received_at_epoch=1800,
        operator_handle_redacted="operator_handle_redacted",
        operator_identity_ref="operator:jim:stable-ref",
        message_text_redacted="approve",
        reply_to_challenge_id="chal-remote-1",
        referenced_approval_ledger_entry_id="led-1",
        referenced_outbox_entry_id="outbox-1",
        referenced_payload_hash_short="a" * 16,
        attachment_manifest_hash="b" * 64,
        evidence_refs=["evidence:0174tg:fixture"],
    )
    base.update(overrides)
    return model.build_remote_operator_inbox_message(**base)


# --------------------------------------------------------------------------- #
# Import/static surface
# --------------------------------------------------------------------------- #
def test_import_allow_list_exact():
    roots = _module_imports()
    assert roots <= ALLOWED_IMPORT_ROOTS, (
        f"unexpected imports: {roots - ALLOWED_IMPORT_ROOTS}")


def test_no_forbidden_imports():
    roots = _module_imports()
    bad = roots & FORBIDDEN_IMPORT_ROOTS
    assert not bad, f"forbidden imports present: {bad}"


def test_no_network_telegram_env_credential_strings():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    for s in (
            "requests.", "httpx.", "aiohttp.", "urllib.", "socket.",
            "import requests", "import httpx", "import aiohttp",
            "urlopen", "http.client", "webbrowser", "getUpdates",
            "sendMessage", "setWebhook", "deleteWebhook", "os.environ",
            "os.getenv", "getenv(", "load_dotenv", "dotenv_values",
            "keyring.get", "keyring.set", "secretstorage.", "netrc(",
            "ConfigParser", "browser_cookie", "sqlite3.", "getpass"):
        assert s not in src, f"forbidden string present: {s}"


def test_module_import_has_no_side_effect_writes():
    out_dir = os.path.join(REPO_ROOT, "docs", "automation", "0174TG")
    pre_exists = os.path.isdir(out_dir)
    import importlib
    importlib.reload(model)
    post_exists = os.path.isdir(out_dir)
    assert pre_exists == post_exists


# --------------------------------------------------------------------------- #
# Hash / dedupe determinism
# --------------------------------------------------------------------------- #
def test_message_text_hash_is_stable():
    a = model.compute_message_text_hash("approve")
    b = model.compute_message_text_hash("approve")
    assert a == b
    assert len(a) == 64


def test_dedupe_key_is_stable_for_same_message():
    a = _message()
    b = _message()
    assert a["inbox_dedupe_key"] == b["inbox_dedupe_key"]
    assert len(a["inbox_dedupe_key"]) == 64


def test_duplicate_inbox_message_is_suppressed():
    registry = model.RemoteOperatorInboxRegistry()
    first = registry.append(_message())
    second = registry.append(_message())
    assert first["status"] == model.REGISTRY_APPENDED
    assert second["status"] == model.REGISTRY_DUPLICATE_SUPPRESSED
    assert second["duplicate_suppressed"] is True
    assert len(registry.messages()) == 1
    assert second["approval_created"] is False
    assert second["dispatch_created"] is False


def test_same_text_different_operator_changes_dedupe_key():
    a = _message(operator_identity_ref="operator:jim:stable-ref")
    b = _message(operator_identity_ref="operator:alt:stable-ref")
    assert a["message_text_hash"] == b["message_text_hash"]
    assert a["inbox_dedupe_key"] != b["inbox_dedupe_key"]


# --------------------------------------------------------------------------- #
# Intent candidates: local only, blocked
# --------------------------------------------------------------------------- #
def test_exact_approve_phrase_creates_intent_candidate_only_not_approval():
    msg = _message(message_text_redacted="approve")
    cand = model.parse_operator_intent_candidate(
        msg, expected_outbox_entry_id="outbox-1",
        expected_payload_hash_short="a" * 16)
    assert cand["intent_class"] == model.INTENT_APPROVE
    assert cand["confidence_class"] == model.CONFIDENCE_EXACT
    assert cand["valid_for_approval"] is False
    assert cand["valid_for_dispatch"] is False
    assert cand["approval_created"] is False
    assert cand["dispatch_created"] is False
    assert cand["ledger_mutated"] is False
    assert cand["outbox_mutated"] is False
    assert model.BLOCK_APPROVAL_DISABLED in cand["blocked_reasons"]
    assert model.BLOCK_DISPATCH_DISABLED in cand["blocked_reasons"]


def test_reject_edit_and_hold_parse_deterministically():
    cases = [
        ("reject", model.INTENT_REJECT),
        ("request edit", model.INTENT_EDIT_REQUEST),
        ("hold", model.INTENT_HOLD),
    ]
    for text, expected in cases:
        cand = model.parse_operator_intent_candidate(_message(message_text_redacted=text))
        assert cand["intent_class"] == expected
        assert cand["confidence_class"] == model.CONFIDENCE_EXACT
        assert cand["valid_for_approval"] is False
        assert cand["valid_for_dispatch"] is False


def test_unknown_or_ambiguous_text_is_blocked():
    unknown = model.parse_operator_intent_candidate(
        _message(message_text_redacted="sounds maybe okay"))
    ambiguous = model.parse_operator_intent_candidate(
        _message(message_text_redacted="ok send it"))
    assert unknown["intent_class"] == model.INTENT_UNKNOWN
    assert ambiguous["intent_class"] == model.INTENT_UNKNOWN
    assert model.BLOCK_AMBIGUOUS_TEXT in unknown["blocked_reasons"]
    assert model.BLOCK_AMBIGUOUS_TEXT in ambiguous["blocked_reasons"]
    assert ambiguous["valid_for_dispatch"] is False


def test_referenced_outbox_id_mismatch_blocks_candidate():
    cand = model.parse_operator_intent_candidate(
        _message(referenced_outbox_entry_id="outbox-actual"),
        expected_outbox_entry_id="outbox-expected")
    assert model.BLOCK_REFERENCE_OUTBOX_MISMATCH in cand["blocked_reasons"]
    assert cand["valid_for_dispatch"] is False


def test_referenced_payload_hash_mismatch_blocks_candidate():
    cand = model.parse_operator_intent_candidate(
        _message(referenced_payload_hash_short="a" * 16),
        expected_payload_hash_short="b" * 16)
    assert model.BLOCK_REFERENCE_PAYLOAD_HASH_MISMATCH in cand["blocked_reasons"]
    assert cand["valid_for_approval"] is False


def test_missing_evidence_refs_blocks_message_and_candidate():
    msg = _message(evidence_refs=[])
    cand = model.parse_operator_intent_candidate(msg)
    assert model.BLOCK_MISSING_EVIDENCE_REFS in msg["blocked_reasons"]
    assert model.BLOCK_MISSING_EVIDENCE_REFS in cand["blocked_reasons"]
    assert msg["accepted_for_local_registry"] is False
    assert cand["valid_for_approval"] is False


def test_replay_cannot_create_approval_or_dispatch():
    registry = model.RemoteOperatorInboxRegistry()
    msg = _message()
    first = registry.append(msg)
    replay = registry.append(msg)
    cand = model.parse_operator_intent_candidate(replay["message"])
    assert first["approval_created"] is False
    assert first["dispatch_created"] is False
    assert replay["approval_created"] is False
    assert replay["dispatch_created"] is False
    assert cand["approval_created"] is False
    assert cand["dispatch_created"] is False
    assert len(registry.messages()) == 1


def test_no_telegram_api_network_env_credential_behavior_flags_exist_false():
    msg = _message()
    cand = model.parse_operator_intent_candidate(msg)
    for obj in (msg, cand):
        flags = obj["safety_flags"]
        assert flags["telegram_api_called"] is False
        assert flags["telegram_send_performed"] is False
        assert flags["telegram_polling_performed"] is False
        assert flags["webhook_enabled"] is False
        assert flags["credential_hydrated"] is False
        assert flags["env_read"] is False
        assert flags["network_performed"] is False
        assert flags["dispatch_ready"] is False
        assert flags["live_ready"] is False
        assert flags["autonomous_posting_allowed"] is False
        assert flags["public_postable"] is False


def test_forbidden_raw_token_like_message_fails_closed():
    msg = _message(message_text_redacted="token=123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef")
    assert model.BLOCK_FORBIDDEN_VALUE in msg["blocked_reasons"]
    assert msg["accepted_for_local_registry"] is False


# --------------------------------------------------------------------------- #
# Packet / artifact writer
# --------------------------------------------------------------------------- #
def test_packet_is_deterministic_and_leak_free():
    a = model.build_packet()
    b = model.build_packet()
    assert a == b
    assert len(a["checksum_sha256"]) == 64
    assert model.scan_for_leaks(a) == []
    assert a["safety_flags"]["telegram_api_called"] is False
    assert a["safety_flags"]["dispatch_ready"] is False


def test_artifact_writer_touches_only_0174tg(tmp_path):
    root = tmp_path
    out = model.write_artifacts(str(root))
    rel_packet = os.path.relpath(out["packet_path"], str(root))
    rel_doc = os.path.relpath(out["doc_path"], str(root))
    assert rel_packet == os.path.join(
        "docs", "automation", "0174TG",
        "telegram_remote_operator_inbox_contract_packet.json")
    assert rel_doc == os.path.join(
        "docs", "automation", "0174TG",
        "telegram_remote_operator_inbox_contract.md")
    assert os.path.exists(out["packet_path"])
    assert os.path.exists(out["doc_path"])
