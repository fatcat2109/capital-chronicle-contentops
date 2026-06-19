"""Tests for 0174TH Telegram review challenge contract."""

import ast
import os

from live_contentops import telegram_review_challenge_contract as model

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(REPO_ROOT, "live_contentops", "telegram_review_challenge_contract.py")

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


def _challenge(**overrides):
    base = dict(
        review_challenge_id="review-chal-1",
        source_outbox_entry_id="outbox-1",
        source_approval_challenge_id="approval-chal-1",
        payload_hash="a" * 64,
        payload_hash_short="a" * 16,
        platform="telegram",
        destination_binding_id="dest:telegram:private-review",
        operator_identity_ref="operator:jim:stable-ref",
        nonce="nonce-0174th-1",
        created_at_epoch=1000,
        expires_at_epoch=2000,
        prompt_text_redacted="Reply approve/reject/request edit with nonce nonce-0174th-1 and hash aaaaaaaaaaaaaaaa.",
        evidence_refs=["evidence:0174th:challenge"],
    )
    base.update(overrides)
    return model.build_telegram_review_challenge(**base)


def _reply(**overrides):
    base = dict(
        reply_id="reply-1",
        source_inbox_message_id="inbox-1",
        review_challenge_id="review-chal-1",
        operator_identity_ref="operator:jim:stable-ref",
        reply_text_redacted="approve",
        referenced_payload_hash_short="a" * 16,
        referenced_nonce="nonce-0174th-1",
        received_at_epoch=1500,
        evidence_refs=["evidence:0174th:reply"],
    )
    base.update(overrides)
    return model.build_telegram_review_reply(**base)


# --------------------------------------------------------------------------- #
# Import/static surface
# --------------------------------------------------------------------------- #
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


def test_module_import_has_no_side_effect_writes():
    out_dir = os.path.join(REPO_ROOT, "docs", "automation", "0174TH")
    pre_exists = os.path.isdir(out_dir)
    import importlib
    importlib.reload(model)
    post_exists = os.path.isdir(out_dir)
    assert pre_exists == post_exists


# --------------------------------------------------------------------------- #
# Hash determinism
# --------------------------------------------------------------------------- #
def test_challenge_hash_is_deterministic():
    a = model.compute_challenge_text_hash("prompt redacted")
    b = model.compute_challenge_text_hash("prompt redacted")
    assert a == b
    assert len(a) == 64


def test_reply_hash_is_deterministic():
    a = model.compute_reply_text_hash("approve")
    b = model.compute_reply_text_hash("approve")
    assert a == b
    assert len(a) == 64


# --------------------------------------------------------------------------- #
# Validation behavior
# --------------------------------------------------------------------------- #
def test_valid_explicit_approval_reply_validates_locally_but_no_mutation():
    result = model.validate_review_challenge_reply(_challenge(), _reply())
    assert result["validation_status"] == model.VALIDATION_LOCAL_PASS
    assert result["reply_class"] == model.REPLY_EXPLICIT_APPROVE
    assert result["sender_match"] is True
    assert result["nonce_match"] is True
    assert result["hash_match"] is True
    assert result["not_expired"] is True
    assert result["challenge_active"] is True
    assert result["evidence_refs_present"] is True
    assert result["valid_for_approval_ledger_entry"] is False
    assert result["valid_for_dispatch"] is False
    assert result["approval_ledger_mutated"] is False
    assert result["outbox_mutated"] is False
    assert result["dispatch_created"] is False
    assert model.BLOCK_APPROVAL_LEDGER_MUTATION_DISABLED in result["blocked_reasons"]
    assert model.BLOCK_OUTBOX_MUTATION_DISABLED in result["blocked_reasons"]
    assert model.BLOCK_DISPATCH_DISABLED in result["blocked_reasons"]


def test_ambiguous_approval_like_text_is_blocked():
    reply = _reply(reply_text_redacted="ok looks good ship it")
    result = model.validate_review_challenge_reply(_challenge(), reply)
    assert reply["parsed_reply_class"] == model.REPLY_AMBIGUOUS
    assert result["validation_status"] == model.VALIDATION_BLOCKED
    assert model.BLOCK_AMBIGUOUS_TEXT in result["blocked_reasons"]
    assert result["valid_for_approval_ledger_entry"] is False


def test_wrong_sender_blocks():
    result = model.validate_review_challenge_reply(
        _challenge(), _reply(operator_identity_ref="operator:wrong:stable-ref"))
    assert result["sender_match"] is False
    assert model.BLOCK_SENDER_MISMATCH in result["blocked_reasons"]


def test_wrong_nonce_blocks():
    result = model.validate_review_challenge_reply(
        _challenge(), _reply(referenced_nonce="wrong-nonce"))
    assert result["nonce_match"] is False
    assert model.BLOCK_NONCE_MISMATCH in result["blocked_reasons"]


def test_wrong_payload_hash_short_blocks():
    result = model.validate_review_challenge_reply(
        _challenge(), _reply(referenced_payload_hash_short="b" * 16))
    assert result["hash_match"] is False
    assert model.BLOCK_PAYLOAD_HASH_MISMATCH in result["blocked_reasons"]


def test_expired_challenge_blocks():
    result = model.validate_review_challenge_reply(
        _challenge(expires_at_epoch=1200), _reply(received_at_epoch=1500))
    assert result["not_expired"] is False
    assert model.BLOCK_EXPIRED in result["blocked_reasons"]


def test_inactive_challenge_blocks():
    result = model.validate_review_challenge_reply(
        _challenge(challenge_active=False), _reply())
    assert result["challenge_active"] is False
    assert model.BLOCK_CHALLENGE_INACTIVE in result["blocked_reasons"]


def test_missing_evidence_refs_blocks():
    result = model.validate_review_challenge_reply(
        _challenge(evidence_refs=[]), _reply(evidence_refs=[]))
    assert result["evidence_refs_present"] is False
    assert model.BLOCK_MISSING_EVIDENCE_REFS in result["blocked_reasons"]


def test_edit_request_returns_edit_request_class_and_cannot_approve():
    reply = _reply(reply_text_redacted="request edit")
    result = model.validate_review_challenge_reply(_challenge(), reply)
    assert reply["parsed_reply_class"] == model.REPLY_EXPLICIT_EDIT_REQUEST
    assert result["reply_class"] == model.REPLY_EXPLICIT_EDIT_REQUEST
    assert result["validation_status"] == model.VALIDATION_BLOCKED
    assert model.BLOCK_EDIT_REQUEST_REQUIRES_REVISION in result["blocked_reasons"]
    assert result["valid_for_approval_ledger_entry"] is False


def test_challenge_id_mismatch_blocks():
    result = model.validate_review_challenge_reply(
        _challenge(review_challenge_id="review-chal-a"),
        _reply(review_challenge_id="review-chal-b"))
    assert model.BLOCK_CHALLENGE_ID_MISMATCH in result["blocked_reasons"]


def test_duplicate_replay_reply_is_suppressed_and_blocks_validation():
    registry = model.TelegramReviewReplyRegistry()
    reply = _reply()
    first = registry.append(reply)
    replay = registry.append(reply)
    result = model.validate_review_challenge_reply(
        _challenge(), replay["reply"], seen_duplicate=replay["duplicate_suppressed"])
    assert first["status"] == model.REGISTRY_APPENDED
    assert replay["status"] == model.REGISTRY_DUPLICATE_SUPPRESSED
    assert replay["duplicate_suppressed"] is True
    assert len(registry.replies()) == 1
    assert result["validation_status"] == model.VALIDATION_DUPLICATE
    assert model.BLOCK_DUPLICATE_REPLY in result["blocked_reasons"]
    assert result["approval_ledger_mutated"] is False
    assert result["outbox_mutated"] is False
    assert result["dispatch_created"] is False


def test_forbidden_raw_token_like_reply_fails_closed():
    reply = _reply(reply_text_redacted="token=123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef")
    result = model.validate_review_challenge_reply(_challenge(), reply)
    assert model.BLOCK_FORBIDDEN_VALUE in reply["blocked_reasons"]
    assert model.BLOCK_FORBIDDEN_VALUE in result["blocked_reasons"]


def test_safety_flags_all_live_api_provider_behavior_false():
    challenge = _challenge()
    reply = _reply()
    result = model.validate_review_challenge_reply(challenge, reply)
    for obj in (challenge, reply, result):
        flags = obj["safety_flags"]
        assert flags["telegram_api_called"] is False
        assert flags["telegram_send_performed"] is False
        assert flags["telegram_polling_performed"] is False
        assert flags["webhook_enabled"] is False
        assert flags["credential_hydrated"] is False
        assert flags["env_read"] is False
        assert flags["network_performed"] is False
        assert flags["llm_provider_called"] is False
        assert flags["approval_ledger_mutated"] is False
        assert flags["outbox_mutated"] is False
        assert flags["dispatch_ready"] is False
        assert flags["live_ready"] is False
        assert flags["autonomous_posting_allowed"] is False
        assert flags["public_postable"] is False


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
    assert a["safety_flags"]["llm_provider_called"] is False
    assert a["safety_flags"]["dispatch_ready"] is False


def test_artifact_writer_touches_only_0174th(tmp_path):
    out = model.write_artifacts(str(tmp_path))
    rel_packet = os.path.relpath(out["packet_path"], str(tmp_path))
    rel_doc = os.path.relpath(out["doc_path"], str(tmp_path))
    assert rel_packet == os.path.join(
        "docs", "automation", "0174TH",
        "telegram_review_challenge_contract_packet.json")
    assert rel_doc == os.path.join(
        "docs", "automation", "0174TH",
        "telegram_review_challenge_contract.md")
    assert os.path.exists(out["packet_path"])
    assert os.path.exists(out["doc_path"])
