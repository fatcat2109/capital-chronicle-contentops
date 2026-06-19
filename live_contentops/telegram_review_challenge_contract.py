"""Telegram review challenge contract (0174TH).

Deterministic LOCAL-only challenge/reply binding layer. It never calls Telegram,
polls Telegram, sends Telegram messages, configures webhooks, hydrates
credentials, reads env files, calls LLM providers, or performs network behavior.
A valid reply can become only a local validation candidate for a future approval
ledger task; this module never mutates 0174ED approval ledger or 0174EE outbox.
"""

import hashlib
import json
import os.path

from live_contentops import approval_ledger_payload_hash_contract as approval

TASK_LABEL = "TASK_CONTENTOPS_0174TH_TELEGRAM_REVIEW_CHALLENGE_CONTRACT_V0"
MODEL = "TELEGRAM_REVIEW_CHALLENGE_CONTRACT_0174TH"
MODEL_VERSION = "0174TH_TELEGRAM_REVIEW_CHALLENGE_V1"
SOURCE_BASELINE_COMMIT = "5bd7154806fbac18d749fe26660dfe9906e6dbdc"

DOC_REL_DIR = os.path.join("docs", "automation", "0174TH")
PACKET_FILENAME = "telegram_review_challenge_contract_packet.json"
DOC_FILENAME = "telegram_review_challenge_contract.md"

CHALLENGE_SCHEMA = "contentops.telegram_review_challenge"
CHALLENGE_SCHEMA_VERSION = "0174TH_REVIEW_CHALLENGE_V1"
REPLY_SCHEMA = "contentops.telegram_review_reply"
REPLY_SCHEMA_VERSION = "0174TH_REVIEW_REPLY_V1"
VALIDATION_SCHEMA = "contentops.telegram_review_challenge_validation_result"
VALIDATION_SCHEMA_VERSION = "0174TH_REVIEW_VALIDATION_V1"
DEDUPE_SCHEMA = "contentops.telegram_review_reply_dedupe_key"
DEDUPE_SCHEMA_VERSION = "0174TH_REVIEW_REPLY_DEDUPE_V1"

REPLY_EXPLICIT_APPROVE = "explicit_approve"
REPLY_EXPLICIT_REJECT = "explicit_reject"
REPLY_EXPLICIT_EDIT_REQUEST = "explicit_edit_request"
REPLY_AMBIGUOUS = "ambiguous"
REPLY_INVALID = "invalid"

VALIDATION_LOCAL_PASS = "local_challenge_reply_valid_candidate_not_approval"
VALIDATION_BLOCKED = "local_challenge_reply_blocked"
VALIDATION_DUPLICATE = "local_challenge_reply_duplicate_suppressed"

REGISTRY_APPENDED = "review_reply_appended_blocked"
REGISTRY_DUPLICATE_SUPPRESSED = "review_reply_duplicate_suppressed"

BLOCK_REQUIRED_FIELD_MISSING = "required_field_missing"
BLOCK_MISSING_EVIDENCE_REFS = "evidence_refs_missing"
BLOCK_FORBIDDEN_VALUE = "forbidden_value_detected"
BLOCK_AMBIGUOUS_TEXT = "reply_text_ambiguous_or_invalid"
BLOCK_SENDER_MISMATCH = "operator_identity_ref_mismatch"
BLOCK_NONCE_MISMATCH = "nonce_mismatch"
BLOCK_PAYLOAD_HASH_MISMATCH = "payload_hash_short_mismatch"
BLOCK_EXPIRED = "review_challenge_expired"
BLOCK_CHALLENGE_INACTIVE = "review_challenge_not_active"
BLOCK_CHALLENGE_ID_MISMATCH = "review_challenge_id_mismatch"
BLOCK_EDIT_REQUEST_REQUIRES_REVISION = "edit_request_requires_revision_not_approval"
BLOCK_APPROVAL_LEDGER_MUTATION_DISABLED = "approval_ledger_mutation_disabled_in_0174TH"
BLOCK_OUTBOX_MUTATION_DISABLED = "outbox_mutation_disabled_in_0174TH"
BLOCK_DISPATCH_DISABLED = "dispatch_disabled_in_0174TH"
BLOCK_DUPLICATE_REPLY = "duplicate_review_reply_suppressed"

SAFETY_FLAGS = {
    "telegram_api_called": False,
    "telegram_send_performed": False,
    "telegram_polling_performed": False,
    "webhook_enabled": False,
    "credential_hydrated": False,
    "env_read": False,
    "network_performed": False,
    "llm_provider_called": False,
    "approval_ledger_mutated": False,
    "outbox_mutated": False,
    "dispatch_ready": False,
    "live_ready": False,
    "autonomous_posting_allowed": False,
    "public_postable": False,
}

EXACT_REPLY_PHRASES = {
    "approve": REPLY_EXPLICIT_APPROVE,
    "approved": REPLY_EXPLICIT_APPROVE,
    "reject": REPLY_EXPLICIT_REJECT,
    "rejected": REPLY_EXPLICIT_REJECT,
    "request edit": REPLY_EXPLICIT_EDIT_REQUEST,
    "edit request": REPLY_EXPLICIT_EDIT_REQUEST,
    "needs edit": REPLY_EXPLICIT_EDIT_REQUEST,
}

AMBIGUOUS_MARKERS = ("ok", "looks good", "ship", "send", "yes", "fine", "go", "maybe")

NEXT_REQUIRED_GATE = (
    "approval ledger candidate recording gate consuming 0174TH validation, then "
    "audit, kill switch, supervised dispatch gates, and separate operator-owned "
    "credential/live platform gates before any live behavior"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174TI_TELEGRAM_CHALLENGE_VALIDATION_TO_APPROVAL_LEDGER_CANDIDATE_CONTRACT_V0"
)


def serialize(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def compute_checksum(obj):
    return hashlib.sha256(serialize(obj).encode("utf-8")).hexdigest()


def scan_for_leaks(obj):
    return approval.scan_for_leaks(obj)


def _blocked(*reasons):
    return sorted(set(r for r in reasons if r))


def _leak_block(obj):
    return [BLOCK_FORBIDDEN_VALUE] if scan_for_leaks(obj) else []


def _required_block(obj, fields):
    return [BLOCK_REQUIRED_FIELD_MISSING for f in fields if not obj.get(f)]


def compute_challenge_text_hash(prompt_text_redacted):
    return compute_checksum({
        "challenge_schema": CHALLENGE_SCHEMA,
        "challenge_schema_version": CHALLENGE_SCHEMA_VERSION,
        "prompt_text_redacted": prompt_text_redacted,
    })


def compute_reply_text_hash(reply_text_redacted):
    return compute_checksum({
        "reply_schema": REPLY_SCHEMA,
        "reply_schema_version": REPLY_SCHEMA_VERSION,
        "reply_text_redacted": reply_text_redacted,
    })


def build_telegram_review_challenge(
        review_challenge_id,
        source_outbox_entry_id,
        source_approval_challenge_id,
        payload_hash,
        payload_hash_short,
        platform,
        destination_binding_id,
        operator_identity_ref,
        nonce,
        created_at_epoch,
        expires_at_epoch,
        prompt_text_redacted,
        evidence_refs=None,
        challenge_active=True):
    evidence_refs = list(evidence_refs or [])
    challenge = {
        "challenge_schema": CHALLENGE_SCHEMA,
        "challenge_schema_version": CHALLENGE_SCHEMA_VERSION,
        "review_challenge_id": review_challenge_id,
        "source_outbox_entry_id": source_outbox_entry_id,
        "source_approval_challenge_id": source_approval_challenge_id,
        "payload_hash": payload_hash,
        "payload_hash_short": payload_hash_short,
        "platform": platform,
        "destination_binding_id": destination_binding_id,
        "operator_identity_ref": operator_identity_ref,
        "nonce": nonce,
        "created_at_epoch": int(created_at_epoch),
        "expires_at_epoch": int(expires_at_epoch),
        "prompt_text_redacted": prompt_text_redacted,
        "challenge_text_hash": compute_challenge_text_hash(prompt_text_redacted),
        "evidence_refs": evidence_refs,
        "challenge_active": bool(challenge_active),
        "safety_flags": dict(SAFETY_FLAGS),
    }
    reasons = []
    reasons.extend(_required_block(challenge, (
        "review_challenge_id", "source_outbox_entry_id",
        "source_approval_challenge_id", "payload_hash", "payload_hash_short",
        "platform", "destination_binding_id", "operator_identity_ref",
        "nonce", "prompt_text_redacted")))
    if not evidence_refs:
        reasons.append(BLOCK_MISSING_EVIDENCE_REFS)
    reasons.extend(_leak_block(challenge))
    challenge["blocked_reasons"] = _blocked(*reasons)
    return challenge


def classify_reply_text(reply_text_redacted):
    normalized = " ".join(str(reply_text_redacted).strip().lower().split())
    if normalized in EXACT_REPLY_PHRASES:
        return EXACT_REPLY_PHRASES[normalized]
    if any(marker in normalized for marker in AMBIGUOUS_MARKERS):
        return REPLY_AMBIGUOUS
    return REPLY_INVALID


def build_telegram_review_reply(
        reply_id,
        source_inbox_message_id,
        review_challenge_id,
        operator_identity_ref,
        reply_text_redacted,
        referenced_payload_hash_short,
        referenced_nonce,
        received_at_epoch,
        evidence_refs=None):
    evidence_refs = list(evidence_refs or [])
    reply = {
        "reply_schema": REPLY_SCHEMA,
        "reply_schema_version": REPLY_SCHEMA_VERSION,
        "reply_id": reply_id,
        "source_inbox_message_id": source_inbox_message_id,
        "review_challenge_id": review_challenge_id,
        "operator_identity_ref": operator_identity_ref,
        "reply_text_redacted": reply_text_redacted,
        "reply_text_hash": compute_reply_text_hash(reply_text_redacted),
        "parsed_reply_class": classify_reply_text(reply_text_redacted),
        "referenced_payload_hash_short": referenced_payload_hash_short,
        "referenced_nonce": referenced_nonce,
        "received_at_epoch": int(received_at_epoch),
        "evidence_refs": evidence_refs,
        "safety_flags": dict(SAFETY_FLAGS),
    }
    reply["reply_dedupe_key"] = compute_reply_dedupe_key(reply)
    reasons = []
    reasons.extend(_required_block(reply, (
        "reply_id", "source_inbox_message_id", "review_challenge_id",
        "operator_identity_ref", "reply_text_redacted",
        "referenced_payload_hash_short", "referenced_nonce")))
    if not evidence_refs:
        reasons.append(BLOCK_MISSING_EVIDENCE_REFS)
    if reply["parsed_reply_class"] in (REPLY_AMBIGUOUS, REPLY_INVALID):
        reasons.append(BLOCK_AMBIGUOUS_TEXT)
    reasons.extend(_leak_block(reply))
    reply["blocked_reasons"] = _blocked(*reasons)
    return reply


def compute_reply_dedupe_key(reply):
    payload = {
        "dedupe_schema": DEDUPE_SCHEMA,
        "dedupe_schema_version": DEDUPE_SCHEMA_VERSION,
        "reply_text_hash": reply["reply_text_hash"],
        "operator_identity_ref": reply["operator_identity_ref"],
        "review_challenge_id": reply["review_challenge_id"],
        "referenced_nonce": reply["referenced_nonce"],
        "referenced_payload_hash_short": reply["referenced_payload_hash_short"],
        "reply_id": reply["reply_id"],
    }
    return compute_checksum(payload)


def validate_review_challenge_reply(challenge, reply, seen_duplicate=False):
    sender_match = reply.get("operator_identity_ref") == challenge.get("operator_identity_ref")
    nonce_match = reply.get("referenced_nonce") == challenge.get("nonce")
    hash_match = reply.get("referenced_payload_hash_short") == challenge.get("payload_hash_short")
    not_expired = int(reply.get("received_at_epoch", 0)) <= int(challenge.get("expires_at_epoch", -1))
    challenge_active = bool(challenge.get("challenge_active"))
    evidence_refs_present = bool(challenge.get("evidence_refs")) and bool(reply.get("evidence_refs"))
    challenge_id_match = reply.get("review_challenge_id") == challenge.get("review_challenge_id")
    reply_class = reply.get("parsed_reply_class", REPLY_INVALID)

    reasons = []
    reasons.extend(challenge.get("blocked_reasons", []))
    reasons.extend(reply.get("blocked_reasons", []))
    if not sender_match:
        reasons.append(BLOCK_SENDER_MISMATCH)
    if not nonce_match:
        reasons.append(BLOCK_NONCE_MISMATCH)
    if not hash_match:
        reasons.append(BLOCK_PAYLOAD_HASH_MISMATCH)
    if not not_expired:
        reasons.append(BLOCK_EXPIRED)
    if not challenge_active:
        reasons.append(BLOCK_CHALLENGE_INACTIVE)
    if not challenge_id_match:
        reasons.append(BLOCK_CHALLENGE_ID_MISMATCH)
    if not evidence_refs_present:
        reasons.append(BLOCK_MISSING_EVIDENCE_REFS)
    if reply_class in (REPLY_AMBIGUOUS, REPLY_INVALID):
        reasons.append(BLOCK_AMBIGUOUS_TEXT)
    if reply_class == REPLY_EXPLICIT_EDIT_REQUEST:
        reasons.append(BLOCK_EDIT_REQUEST_REQUIRES_REVISION)
    if seen_duplicate:
        reasons.append(BLOCK_DUPLICATE_REPLY)
    reasons.extend([
        BLOCK_APPROVAL_LEDGER_MUTATION_DISABLED,
        BLOCK_OUTBOX_MUTATION_DISABLED,
        BLOCK_DISPATCH_DISABLED,
    ])

    local_reply_valid = (
        reply_class == REPLY_EXPLICIT_APPROVE and sender_match and nonce_match and
        hash_match and not_expired and challenge_active and evidence_refs_present and
        challenge_id_match and not seen_duplicate and not challenge.get("blocked_reasons") and
        not reply.get("blocked_reasons")
    )
    status = VALIDATION_LOCAL_PASS if local_reply_valid else VALIDATION_BLOCKED
    if seen_duplicate:
        status = VALIDATION_DUPLICATE
    result = {
        "validation_schema": VALIDATION_SCHEMA,
        "validation_schema_version": VALIDATION_SCHEMA_VERSION,
        "validation_status": status,
        "review_challenge_id": challenge.get("review_challenge_id"),
        "reply_id": reply.get("reply_id"),
        "reply_class": reply_class,
        "sender_match": sender_match,
        "nonce_match": nonce_match,
        "hash_match": hash_match,
        "not_expired": not_expired,
        "challenge_active": challenge_active,
        "evidence_refs_present": evidence_refs_present,
        "valid_for_approval_ledger_entry": False,
        "valid_for_dispatch": False,
        "approval_ledger_mutated": False,
        "outbox_mutated": False,
        "dispatch_created": False,
        "safety_flags": dict(SAFETY_FLAGS),
        "blocked_reasons": _blocked(*reasons),
    }
    result["validation_result_id"] = compute_checksum({
        "validation_schema": VALIDATION_SCHEMA,
        "validation_schema_version": VALIDATION_SCHEMA_VERSION,
        "review_challenge_id": result["review_challenge_id"],
        "reply_id": result["reply_id"],
        "reply_class": result["reply_class"],
        "validation_status": result["validation_status"],
        "blocked_reasons": result["blocked_reasons"],
    })
    return result


class TelegramReviewReplyRegistry:
    def __init__(self):
        self._replies = []
        self._by_key = {}

    def append(self, reply):
        key = reply["reply_dedupe_key"]
        if key in self._by_key:
            return {
                "status": REGISTRY_DUPLICATE_SUPPRESSED,
                "reply": self._by_key[key],
                "duplicate_suppressed": True,
                "blocked_reasons": [BLOCK_DUPLICATE_REPLY],
                "approval_ledger_mutated": False,
                "outbox_mutated": False,
                "dispatch_created": False,
                "safety_flags": dict(SAFETY_FLAGS),
            }
        entry = dict(reply)
        entry["registry_sequence"] = len(self._replies) + 1
        self._replies.append(entry)
        self._by_key[key] = entry
        return {
            "status": REGISTRY_APPENDED,
            "reply": entry,
            "duplicate_suppressed": False,
            "blocked_reasons": list(entry.get("blocked_reasons", [])),
            "approval_ledger_mutated": False,
            "outbox_mutated": False,
            "dispatch_created": False,
            "safety_flags": dict(SAFETY_FLAGS),
        }

    def replies(self):
        return list(self._replies)


def build_packet():
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "status": "pass",
        "contract_status": "deterministic_local_review_challenge_ready",
        "challenge_schema": CHALLENGE_SCHEMA,
        "challenge_schema_version": CHALLENGE_SCHEMA_VERSION,
        "reply_schema": REPLY_SCHEMA,
        "reply_schema_version": REPLY_SCHEMA_VERSION,
        "validation_schema": VALIDATION_SCHEMA,
        "validation_schema_version": VALIDATION_SCHEMA_VERSION,
        "reply_classes": [
            REPLY_EXPLICIT_APPROVE, REPLY_EXPLICIT_REJECT,
            REPLY_EXPLICIT_EDIT_REQUEST, REPLY_AMBIGUOUS, REPLY_INVALID],
        "validation_statuses": [VALIDATION_LOCAL_PASS, VALIDATION_BLOCKED, VALIDATION_DUPLICATE],
        "blocked_reasons": [
            BLOCK_REQUIRED_FIELD_MISSING, BLOCK_MISSING_EVIDENCE_REFS,
            BLOCK_FORBIDDEN_VALUE, BLOCK_AMBIGUOUS_TEXT, BLOCK_SENDER_MISMATCH,
            BLOCK_NONCE_MISMATCH, BLOCK_PAYLOAD_HASH_MISMATCH, BLOCK_EXPIRED,
            BLOCK_CHALLENGE_INACTIVE, BLOCK_CHALLENGE_ID_MISMATCH,
            BLOCK_EDIT_REQUEST_REQUIRES_REVISION,
            BLOCK_APPROVAL_LEDGER_MUTATION_DISABLED,
            BLOCK_OUTBOX_MUTATION_DISABLED, BLOCK_DISPATCH_DISABLED,
            BLOCK_DUPLICATE_REPLY],
        "invariants": [
            "challenge_text_hash_is_deterministic",
            "reply_text_hash_is_deterministic",
            "valid_reply_binds_sender_nonce_payload_hash_and_expiration",
            "valid_reply_does_not_create_approval_ledger_entry",
            "valid_reply_does_not_create_outbox_or_dispatch",
            "ambiguous_approval_like_text_is_blocked",
            "wrong_sender_nonce_or_payload_hash_blocks",
            "expired_or_inactive_challenge_blocks",
            "missing_evidence_refs_blocks",
            "edit_request_requires_revision_not_approval",
            "duplicate_reply_suppressed",
            "artifact_writer_touches_only_docs_automation_0174TH"],
        "safety_flags": dict(SAFETY_FLAGS),
        "next_required_gate": NEXT_REQUIRED_GATE,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
    }
    packet["checksum_sha256"] = compute_checksum(packet)
    return packet


def build_doc():
    flags = "\n".join(f"- `{k}` = `{str(v).lower()}`" for k, v in sorted(SAFETY_FLAGS.items()))
    return (
        "# 0174TH Telegram Review Challenge Contract\n\n"
        "Local-only challenge/reply binding layer. No Telegram, network, env, "
        "credential, provider, approval ledger mutation, outbox mutation, or "
        "dispatch behavior exists here.\n\n"
        "## Challenge Binding\n\n"
        "Challenge binds review challenge id, outbox entry id, approval challenge "
        "id, payload hash, payload hash short, platform, destination binding, "
        "operator identity ref, nonce, expiration, prompt hash, and evidence refs.\n\n"
        "## Reply Binding\n\n"
        "Reply binds inbox message id, challenge id, operator identity ref, reply "
        "text hash, parsed reply class, referenced nonce, payload hash short, "
        "received time, and evidence refs.\n\n"
        "## Validation\n\n"
        "Valid explicit approval replies can pass local challenge validation only. "
        "They cannot create approval ledger entries, outbox entries, or dispatch.\n\n"
        "## Safety Flags\n\n"
        f"{flags}\n\n"
        "## Next Gate\n\n"
        f"{EXACT_NEXT_TASK_RECOMMENDATION}\n")


def write_artifacts(repo_root):
    out_dir = os.path.join(repo_root, DOC_REL_DIR)
    os.makedirs(out_dir, exist_ok=True)
    packet = build_packet()
    packet_path = os.path.join(out_dir, PACKET_FILENAME)
    doc_path = os.path.join(out_dir, DOC_FILENAME)
    with open(packet_path, "w", encoding="utf-8") as fh:
        fh.write(serialize(packet))
    with open(doc_path, "w", encoding="utf-8") as fh:
        fh.write(build_doc())
    return {"packet_path": packet_path, "doc_path": doc_path, "packet": packet}
