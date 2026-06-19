"""Tests for 0174TI approval ledger candidate contract."""

import ast
import os

from live_contentops import telegram_approval_ledger_candidate_contract as model
from live_contentops import telegram_review_challenge_contract as review

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(
    REPO_ROOT, "live_contentops", "telegram_approval_ledger_candidate_contract.py")

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


def _bundle(reply_text="approve", **overrides):
    challenge_overrides = overrides.pop("challenge", {})
    reply_overrides = overrides.pop("reply", {})
    validation_seen_duplicate = overrides.pop("seen_duplicate", False)
    challenge_base = dict(
        review_challenge_id="review-chal-1",
        source_outbox_entry_id="outbox-1",
        source_approval_challenge_id="approval-chal-1",
        payload_hash="a" * 64,
        payload_hash_short="a" * 16,
        platform="telegram",
        destination_binding_id="dest:telegram:private-review",
        operator_identity_ref="operator:jim:stable-ref",
        nonce="nonce-0174ti-1",
        created_at_epoch=1000,
        expires_at_epoch=2000,
        prompt_text_redacted="Reply approve/reject/request edit with nonce nonce-0174ti-1 and hash aaaaaaaaaaaaaaaa.",
        evidence_refs=["evidence:0174ti:challenge"],
    )
    challenge_base.update(challenge_overrides)
    challenge = review.build_telegram_review_challenge(**challenge_base)
    reply_base = dict(
        reply_id="reply-1",
        source_inbox_message_id="inbox-1",
        review_challenge_id=challenge.get("review_challenge_id"),
        operator_identity_ref=challenge.get("operator_identity_ref"),
        reply_text_redacted=reply_text,
        referenced_payload_hash_short=challenge.get("payload_hash_short"),
        referenced_nonce=challenge.get("nonce"),
        received_at_epoch=1500,
        evidence_refs=["evidence:0174ti:reply"],
    )
    reply_base.update(reply_overrides)
    reply = review.build_telegram_review_reply(**reply_base)
    validation = review.validate_review_challenge_reply(
        challenge, reply, seen_duplicate=validation_seen_duplicate)
    candidate = model.build_approval_ledger_candidate(
        challenge, reply, validation, created_at_epoch=1600)
    return challenge, reply, validation, candidate


# --------------------------------------------------------------------------- #
# Static safety surface
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


def test_module_import_has_no_artifact_side_effects():
    out_dir = os.path.join(REPO_ROOT, "docs", "automation", "0174TI")
    pre_exists = os.path.isdir(out_dir)
    import importlib
    importlib.reload(model)
    post_exists = os.path.isdir(out_dir)
    assert pre_exists == post_exists


# --------------------------------------------------------------------------- #
# Candidate creation / hash rules
# --------------------------------------------------------------------------- #
def test_valid_approval_validation_creates_deterministic_candidate():
    _, _, validation, candidate = _bundle("approve")
    assert validation["validation_status"] == review.VALIDATION_LOCAL_PASS
    assert candidate["candidate_validity_class"] == model.VALIDITY_LOCAL_ONLY
    assert candidate["candidate_intent_class"] == model.INTENT_APPROVAL
    assert candidate["reply_class"] == review.REPLY_EXPLICIT_APPROVE
    assert len(candidate["candidate_hash"]) == 64
    assert len(candidate["approval_ledger_candidate_id"]) == 64
    assert candidate["approval_ledger_mutated"] is False
    assert candidate["outbox_mutated"] is False
    assert candidate["dispatch_ready"] is False
    assert candidate["live_ready"] is False
    assert candidate["public_postable"] is False
    assert model.BLOCK_LEDGER_MUTATION_DISABLED in candidate["blocked_reasons"]
    assert model.BLOCK_OUTBOX_MUTATION_DISABLED in candidate["blocked_reasons"]
    assert model.BLOCK_DISPATCH_DISABLED in candidate["blocked_reasons"]


def test_candidate_hash_stable_for_identical_inputs():
    first = _bundle("approve")[3]
    second = _bundle("approve")[3]
    assert first["candidate_hash"] == second["candidate_hash"]
    assert first["approval_ledger_candidate_id"] == second["approval_ledger_candidate_id"]


def test_candidate_hash_changes_when_payload_hash_changes():
    first = _bundle("approve")[3]
    second = _bundle("approve", challenge={
        "payload_hash": "b" * 64,
        "payload_hash_short": "b" * 16,
        "prompt_text_redacted": "Reply approve with nonce nonce-0174ti-1 and hash bbbbbbbbbbbbbbbb.",
    })[3]
    assert first["candidate_hash"] != second["candidate_hash"]


def test_candidate_hash_changes_when_outbox_id_changes():
    first = _bundle("approve")[3]
    second = _bundle("approve", challenge={"source_outbox_entry_id": "outbox-2"})[3]
    assert first["candidate_hash"] != second["candidate_hash"]


def test_candidate_hash_changes_when_operator_identity_changes():
    first = _bundle("approve")[3]
    second = _bundle("approve", challenge={
        "operator_identity_ref": "operator:jane:stable-ref"})[3]
    assert first["candidate_hash"] != second["candidate_hash"]


def test_candidate_hash_changes_when_reply_id_changes():
    first = _bundle("approve")[3]
    second = _bundle("approve", reply={"reply_id": "reply-2"})[3]
    assert first["candidate_hash"] != second["candidate_hash"]


# --------------------------------------------------------------------------- #
# Reply class handling
# --------------------------------------------------------------------------- #
def test_reject_reply_produces_reject_candidate_only():
    _, _, validation, candidate = _bundle("reject")
    assert validation["reply_class"] == review.REPLY_EXPLICIT_REJECT
    assert candidate["candidate_validity_class"] == model.VALIDITY_LOCAL_ONLY
    assert candidate["candidate_intent_class"] == model.INTENT_REJECT
    assert candidate["candidate_intent_class"] != model.INTENT_APPROVAL
    assert candidate["dispatch_ready"] is False


def test_edit_request_reply_produces_edit_request_candidate_only():
    _, _, validation, candidate = _bundle("request edit")
    assert validation["reply_class"] == review.REPLY_EXPLICIT_EDIT_REQUEST
    assert candidate["candidate_validity_class"] == model.VALIDITY_LOCAL_ONLY
    assert candidate["candidate_intent_class"] == model.INTENT_EDIT_REQUEST
    assert candidate["candidate_intent_class"] != model.INTENT_APPROVAL
    assert candidate["dispatch_ready"] is False


def test_ambiguous_reply_blocks_candidate():
    _, _, validation, candidate = _bundle("ok looks good ship it")
    assert validation["reply_class"] == review.REPLY_AMBIGUOUS
    assert candidate["candidate_validity_class"] == model.VALIDITY_BLOCKED
    assert candidate["candidate_intent_class"] == model.INTENT_BLOCKED
    assert model.BLOCK_REPLY_CLASS_AMBIGUOUS_OR_INVALID in candidate["blocked_reasons"]


def test_invalid_reply_blocks_candidate():
    _, _, validation, candidate = _bundle("nonsense")
    assert validation["reply_class"] == review.REPLY_INVALID
    assert candidate["candidate_validity_class"] == model.VALIDITY_BLOCKED
    assert candidate["candidate_intent_class"] == model.INTENT_BLOCKED
    assert model.BLOCK_REPLY_CLASS_AMBIGUOUS_OR_INVALID in candidate["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Fail-closed validation proofs
# --------------------------------------------------------------------------- #
def test_expired_validation_blocks_candidate():
    _, _, validation, candidate = _bundle(
        "approve", challenge={"expires_at_epoch": 1200}, reply={"received_at_epoch": 1500})
    assert validation["not_expired"] is False
    assert candidate["candidate_validity_class"] == model.VALIDITY_BLOCKED
    assert model.BLOCK_EXPIRED in candidate["blocked_reasons"]


def test_wrong_nonce_blocks_candidate():
    _, _, validation, candidate = _bundle(
        "approve", reply={"referenced_nonce": "wrong-nonce"})
    assert validation["nonce_match"] is False
    assert candidate["candidate_validity_class"] == model.VALIDITY_BLOCKED
    assert model.BLOCK_WRONG_NONCE in candidate["blocked_reasons"]


def test_wrong_hash_blocks_candidate():
    _, _, validation, candidate = _bundle(
        "approve", reply={"referenced_payload_hash_short": "b" * 16})
    assert validation["hash_match"] is False
    assert candidate["candidate_validity_class"] == model.VALIDITY_BLOCKED
    assert model.BLOCK_WRONG_HASH in candidate["blocked_reasons"]


def test_wrong_sender_blocks_candidate():
    _, _, validation, candidate = _bundle(
        "approve", reply={"operator_identity_ref": "operator:wrong:stable-ref"})
    assert validation["sender_match"] is False
    assert candidate["candidate_validity_class"] == model.VALIDITY_BLOCKED
    assert model.BLOCK_WRONG_SENDER in candidate["blocked_reasons"]


def test_missing_evidence_refs_blocks_candidate():
    _, _, validation, candidate = _bundle(
        "approve", challenge={"evidence_refs": []}, reply={"evidence_refs": []})
    assert validation["evidence_refs_present"] is False
    assert candidate["candidate_validity_class"] == model.VALIDITY_BLOCKED
    assert model.BLOCK_MISSING_EVIDENCE_REFS in candidate["blocked_reasons"]


def test_validation_result_id_mismatch_blocks_candidate():
    challenge, reply, validation, _ = _bundle("approve")
    validation = dict(validation)
    validation["validation_result_id"] = "0" * 64
    candidate = model.build_approval_ledger_candidate(
        challenge, reply, validation, created_at_epoch=1600)
    assert candidate["candidate_validity_class"] == model.VALIDITY_BLOCKED
    assert model.BLOCK_VALIDATION_ID_MISMATCH in candidate["blocked_reasons"]


def test_upstream_mutation_flag_blocks_candidate():
    challenge, reply, validation, _ = _bundle("approve")
    validation = dict(validation)
    validation["approval_ledger_mutated"] = True
    candidate = model.build_approval_ledger_candidate(
        challenge, reply, validation, created_at_epoch=1600)
    assert candidate["candidate_validity_class"] == model.VALIDITY_BLOCKED
    assert model.BLOCK_UPSTREAM_LEDGER_MUTATED in candidate["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Duplicate / safety / artifacts
# --------------------------------------------------------------------------- #
def test_duplicate_candidate_suppressed():
    candidate = _bundle("approve")[3]
    registry = model.ApprovalLedgerCandidateRegistry()
    first = registry.append(candidate)
    duplicate = registry.append(candidate)
    assert first["status"] == model.REGISTRY_APPENDED
    assert duplicate["status"] == model.REGISTRY_DUPLICATE_SUPPRESSED
    assert duplicate["duplicate_suppressed"] is True
    assert duplicate["candidate"]["candidate_validity_class"] == model.VALIDITY_DUPLICATE_SUPPRESSED
    assert model.BLOCK_DUPLICATE_CANDIDATE in duplicate["candidate"]["blocked_reasons"]
    assert len(registry.candidates()) == 1
    assert duplicate["approval_ledger_mutated"] is False
    assert duplicate["outbox_mutated"] is False
    assert duplicate["dispatch_ready"] is False


def test_candidate_never_sets_live_or_mutation_flags_true():
    candidate = _bundle("approve")[3]
    for key in (
        "approval_ledger_mutated", "outbox_mutated", "dispatch_ready",
        "live_ready", "public_postable"):
        assert candidate[key] is False
    for key, value in candidate["safety_flags"].items():
        assert value is False, key


def test_packet_is_deterministic_and_leak_free():
    a = model.build_packet()
    b = model.build_packet()
    assert a == b
    assert len(a["checksum_sha256"]) == 64
    assert model.scan_for_leaks(a) == []
    assert a["safety_flags"]["telegram_api_called"] is False
    assert a["safety_flags"]["llm_provider_called"] is False
    assert a["safety_flags"]["approval_ledger_mutated"] is False


def test_artifact_writer_touches_only_0174ti(tmp_path):
    out = model.write_artifacts(str(tmp_path))
    rel_packet = os.path.relpath(out["packet_path"], str(tmp_path))
    rel_doc = os.path.relpath(out["doc_path"], str(tmp_path))
    assert rel_packet == os.path.join(
        "docs", "automation", "0174TI",
        "telegram_approval_ledger_candidate_contract_packet.json")
    assert rel_doc == os.path.join(
        "docs", "automation", "0174TI",
        "telegram_approval_ledger_candidate_contract.md")
    assert os.path.exists(out["packet_path"])
    assert os.path.exists(out["doc_path"])
