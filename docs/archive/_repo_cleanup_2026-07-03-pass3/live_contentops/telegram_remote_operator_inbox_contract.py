"""Telegram remote operator inbox contract (0174TG).

Deterministic, LOCAL-only intake model for future Telegram remote operator
review. This module models redacted inbound messages as local review-event
candidates. It never calls Telegram, polls Telegram, sends Telegram messages,
configures webhooks, hydrates credentials, reads env files, or performs network
behavior.

Telegram roles stay separate:
  * Remote Operator Inbox: future Jim review/approve/reject/edit decisions.
  * Channel Dispatch Destination: future public/channel dispatch destination.

0174TG implements only the Remote Operator Inbox local contract. A parsed
message can create an intent candidate, but it can never approve dispatch or
mutate the 0174ED approval ledger / 0174EE outbox.
"""

import hashlib
import json
import os.path
import re

from live_contentops import approval_ledger_payload_hash_contract as approval

TASK_LABEL = (
    "TASK_CONTENTOPS_0174TG_TELEGRAM_REMOTE_OPERATOR_INBOX_CONTRACT_V0"
)
MODEL = "TELEGRAM_REMOTE_OPERATOR_INBOX_CONTRACT_0174TG"
MODEL_VERSION = "0174TG_TELEGRAM_REMOTE_OPERATOR_INBOX_V1"
SOURCE_BASELINE_COMMIT = "f980880f7251a8038cb2d16b1d9c01a3f381d2bc"

DOC_REL_DIR = os.path.join("docs", "automation", "0174TG")
PACKET_FILENAME = "telegram_remote_operator_inbox_contract_packet.json"
DOC_FILENAME = "telegram_remote_operator_inbox_contract.md"

SOURCE_CHANNEL_CLASS = "telegram_remote_operator_inbox"
MESSAGE_SCHEMA = "contentops.telegram_remote_operator_inbox_message"
MESSAGE_SCHEMA_VERSION = "0174TG_INBOX_MESSAGE_V1"
INTENT_SCHEMA = "contentops.parsed_operator_intent_candidate"
INTENT_SCHEMA_VERSION = "0174TG_INTENT_CANDIDATE_V1"
DEDUPE_SCHEMA = "contentops.telegram_remote_operator_inbox_dedupe_key"
DEDUPE_SCHEMA_VERSION = "0174TG_INBOX_DEDUPE_V1"

INTENT_APPROVE = "approve"
INTENT_REJECT = "reject"
INTENT_EDIT_REQUEST = "edit_request"
INTENT_HOLD = "hold"
INTENT_UNKNOWN = "unknown"

CONFIDENCE_EXACT = "deterministic_exact_phrase"
CONFIDENCE_AMBIGUOUS = "ambiguous"
CONFIDENCE_INVALID = "invalid"

REGISTRY_APPENDED = "inbox_message_appended_blocked"
REGISTRY_DUPLICATE_SUPPRESSED = "inbox_message_duplicate_suppressed"

BLOCK_MISSING_EVIDENCE_REFS = "evidence_refs_missing"
BLOCK_FORBIDDEN_VALUE = "forbidden_value_detected"
BLOCK_REQUIRED_FIELD_MISSING = "required_field_missing"
BLOCK_AMBIGUOUS_TEXT = "operator_text_ambiguous_or_unknown"
BLOCK_REFERENCE_OUTBOX_MISMATCH = "referenced_outbox_entry_id_mismatch"
BLOCK_REFERENCE_PAYLOAD_HASH_MISMATCH = "referenced_payload_hash_short_mismatch"
BLOCK_APPROVAL_DISABLED = "remote_message_cannot_create_approval"
BLOCK_DISPATCH_DISABLED = "remote_message_cannot_create_dispatch"
BLOCK_FUTURE_GATES_MISSING = "future_review_challenge_intent_audit_kill_switch_gates_missing"
BLOCK_DUPLICATE_MESSAGE = "duplicate_inbox_message_suppressed"

DEDUPE_KEY_INPUTS = (
    "dedupe_schema",
    "dedupe_schema_version",
    "message_text_hash",
    "operator_identity_ref",
    "received_at_epoch_bucket",
    "inbox_message_id",
)

SAFETY_FLAGS = {
    "telegram_api_called": False,
    "telegram_send_performed": False,
    "telegram_polling_performed": False,
    "webhook_enabled": False,
    "credential_hydrated": False,
    "env_read": False,
    "network_performed": False,
    "dispatch_ready": False,
    "live_ready": False,
    "autonomous_posting_allowed": False,
    "public_postable": False,
    "approval_created": False,
    "dispatch_created": False,
    "ledger_mutated": False,
    "outbox_mutated": False,
    "autonomous_reply_performed": False,
    "dm_performed": False,
    "scheduler_enabled": False,
    "scraping_performed": False,
}

EXACT_PHRASES = {
    "approve": INTENT_APPROVE,
    "approved": INTENT_APPROVE,
    "reject": INTENT_REJECT,
    "rejected": INTENT_REJECT,
    "request edit": INTENT_EDIT_REQUEST,
    "edit request": INTENT_EDIT_REQUEST,
    "needs edit": INTENT_EDIT_REQUEST,
    "hold": INTENT_HOLD,
    "pause": INTENT_HOLD,
}

NEXT_REQUIRED_GATE = (
    "Telegram review challenge contract and deterministic exact intent parser "
    "gate, then audit, kill switch, supervised dispatch gates, and separate "
    "operator-owned credential/live platform gates before any live behavior"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174TH_TELEGRAM_REVIEW_CHALLENGE_CONTRACT_V0"
)


def serialize(obj):
    """Deterministic JSON: sorted keys, stable separators, trailing newline."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def compute_checksum(obj):
    """SHA-256 of deterministic serialization."""
    return hashlib.sha256(serialize(obj).encode("utf-8")).hexdigest()


def scan_for_leaks(obj):
    """Return sorted redaction violations using the 0174ED scanner."""
    return approval.scan_for_leaks(obj)


def _blocked(*reasons):
    return sorted(set(r for r in reasons if r))


def _require_no_leaks(obj):
    leaks = scan_for_leaks(obj)
    if leaks:
        return _blocked(BLOCK_FORBIDDEN_VALUE)
    return []


def _time_bucket(received_at_epoch, bucket_seconds=60):
    return int(received_at_epoch) // int(bucket_seconds)


def compute_message_text_hash(message_text_redacted):
    payload = {
        "message_schema": MESSAGE_SCHEMA,
        "message_schema_version": MESSAGE_SCHEMA_VERSION,
        "message_text_redacted": message_text_redacted,
    }
    return compute_checksum(payload)


def compute_inbox_dedupe_key(message, bucket_seconds=60):
    payload = {
        "dedupe_schema": DEDUPE_SCHEMA,
        "dedupe_schema_version": DEDUPE_SCHEMA_VERSION,
        "message_text_hash": message["message_text_hash"],
        "operator_identity_ref": message["operator_identity_ref"],
        "received_at_epoch_bucket": _time_bucket(
            message["received_at_epoch"], bucket_seconds=bucket_seconds),
        "inbox_message_id": message["inbox_message_id"],
    }
    return compute_checksum(payload)


def build_remote_operator_inbox_message(
        inbox_message_id,
        received_at_epoch,
        operator_handle_redacted,
        operator_identity_ref,
        message_text_redacted,
        reply_to_challenge_id=None,
        referenced_approval_ledger_entry_id=None,
        referenced_outbox_entry_id=None,
        referenced_payload_hash_short=None,
        attachment_manifest_hash=None,
        evidence_refs=None):
    """Build local redacted inbox message; fail closed via blocked reasons."""
    evidence_refs = list(evidence_refs or [])
    msg = {
        "inbox_message_id": inbox_message_id,
        "source_channel_class": SOURCE_CHANNEL_CLASS,
        "received_at_epoch": int(received_at_epoch),
        "operator_handle_redacted": operator_handle_redacted,
        "operator_identity_ref": operator_identity_ref,
        "message_text_redacted": message_text_redacted,
        "message_text_hash": compute_message_text_hash(message_text_redacted),
        "reply_to_challenge_id": reply_to_challenge_id,
        "referenced_approval_ledger_entry_id": referenced_approval_ledger_entry_id,
        "referenced_outbox_entry_id": referenced_outbox_entry_id,
        "referenced_payload_hash_short": referenced_payload_hash_short,
        "attachment_manifest_hash": attachment_manifest_hash,
        "evidence_refs": evidence_refs,
        "safety_flags": dict(SAFETY_FLAGS),
    }
    msg["inbox_dedupe_key"] = compute_inbox_dedupe_key(msg)
    reasons = []
    for field in ("inbox_message_id", "operator_identity_ref",
                  "message_text_redacted"):
        if not msg.get(field):
            reasons.append(BLOCK_REQUIRED_FIELD_MISSING)
    if not evidence_refs:
        reasons.append(BLOCK_MISSING_EVIDENCE_REFS)
    reasons.extend(_require_no_leaks(msg))
    msg["blocked_reasons"] = _blocked(*reasons)
    msg["accepted_for_local_registry"] = not bool(msg["blocked_reasons"])
    msg["valid_for_approval"] = False
    msg["valid_for_dispatch"] = False
    return msg


def _classify_text(text):
    normalized = " ".join(str(text).strip().lower().split())
    if normalized in EXACT_PHRASES:
        return EXACT_PHRASES[normalized], CONFIDENCE_EXACT, []
    # Words that look action-like but are not exact enough for authority.
    if any(w in normalized for w in ("approve", "ok", "yes", "ship", "send",
                                     "fine", "go", "looks good", "maybe")):
        return INTENT_UNKNOWN, CONFIDENCE_AMBIGUOUS, [BLOCK_AMBIGUOUS_TEXT]
    return INTENT_UNKNOWN, CONFIDENCE_INVALID, [BLOCK_AMBIGUOUS_TEXT]


def parse_operator_intent_candidate(
        inbox_message,
        expected_outbox_entry_id=None,
        expected_payload_hash_short=None):
    """Parse message into blocked intent candidate; never creates authority."""
    intent_class, confidence_class, reasons = _classify_text(
        inbox_message.get("message_text_redacted", ""))
    reasons.extend(inbox_message.get("blocked_reasons", []))
    referenced = {
        "reply_to_challenge_id": inbox_message.get("reply_to_challenge_id"),
        "referenced_approval_ledger_entry_id": inbox_message.get(
            "referenced_approval_ledger_entry_id"),
        "referenced_outbox_entry_id": inbox_message.get(
            "referenced_outbox_entry_id"),
        "referenced_payload_hash_short": inbox_message.get(
            "referenced_payload_hash_short"),
    }
    if (expected_outbox_entry_id is not None and
            referenced["referenced_outbox_entry_id"] != expected_outbox_entry_id):
        reasons.append(BLOCK_REFERENCE_OUTBOX_MISMATCH)
    if (expected_payload_hash_short is not None and
            referenced["referenced_payload_hash_short"] !=
            expected_payload_hash_short):
        reasons.append(BLOCK_REFERENCE_PAYLOAD_HASH_MISMATCH)
    reasons.extend([
        BLOCK_APPROVAL_DISABLED,
        BLOCK_DISPATCH_DISABLED,
        BLOCK_FUTURE_GATES_MISSING,
    ])
    payload = {
        "intent_schema": INTENT_SCHEMA,
        "intent_schema_version": INTENT_SCHEMA_VERSION,
        "source_inbox_message_id": inbox_message.get("inbox_message_id"),
        "source_inbox_dedupe_key": inbox_message.get("inbox_dedupe_key"),
        "intent_class": intent_class,
        "confidence_class": confidence_class,
        "referenced_ids": referenced,
    }
    candidate = dict(payload)
    candidate["intent_candidate_id"] = compute_checksum(payload)
    candidate["blocked_reasons"] = _blocked(*reasons)
    candidate["valid_for_approval"] = False
    candidate["valid_for_dispatch"] = False
    candidate["requires_future_llm_or_exact_parser_gate"] = True
    candidate["approval_created"] = False
    candidate["dispatch_created"] = False
    candidate["ledger_mutated"] = False
    candidate["outbox_mutated"] = False
    candidate["safety_flags"] = dict(SAFETY_FLAGS)
    return candidate


class RemoteOperatorInboxRegistry:
    """Append-only local registry with deterministic duplicate suppression."""

    def __init__(self):
        self._messages = []
        self._by_dedupe_key = {}

    def append(self, message):
        key = message["inbox_dedupe_key"]
        if key in self._by_dedupe_key:
            return {
                "status": REGISTRY_DUPLICATE_SUPPRESSED,
                "message": self._by_dedupe_key[key],
                "duplicate_suppressed": True,
                "approval_created": False,
                "dispatch_created": False,
                "blocked_reasons": [BLOCK_DUPLICATE_MESSAGE],
                "safety_flags": dict(SAFETY_FLAGS),
            }
        entry = dict(message)
        entry["registry_sequence"] = len(self._messages) + 1
        self._messages.append(entry)
        self._by_dedupe_key[key] = entry
        return {
            "status": REGISTRY_APPENDED,
            "message": entry,
            "duplicate_suppressed": False,
            "approval_created": False,
            "dispatch_created": False,
            "blocked_reasons": list(entry.get("blocked_reasons", [])),
            "safety_flags": dict(SAFETY_FLAGS),
        }

    def messages(self):
        return list(self._messages)


def build_packet():
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "status": "pass",
        "contract_status": "deterministic_local_remote_operator_inbox_ready",
        "message_schema": MESSAGE_SCHEMA,
        "message_schema_version": MESSAGE_SCHEMA_VERSION,
        "intent_schema": INTENT_SCHEMA,
        "intent_schema_version": INTENT_SCHEMA_VERSION,
        "source_channel_class": SOURCE_CHANNEL_CLASS,
        "intent_classes": [
            INTENT_APPROVE,
            INTENT_REJECT,
            INTENT_EDIT_REQUEST,
            INTENT_HOLD,
            INTENT_UNKNOWN,
        ],
        "confidence_classes": [
            CONFIDENCE_EXACT,
            CONFIDENCE_AMBIGUOUS,
            CONFIDENCE_INVALID,
        ],
        "dedupe_key_algorithm": "sha256",
        "dedupe_key_inputs": list(DEDUPE_KEY_INPUTS),
        "registry_status_classes": [
            REGISTRY_APPENDED,
            REGISTRY_DUPLICATE_SUPPRESSED,
        ],
        "blocked_reasons": [
            BLOCK_MISSING_EVIDENCE_REFS,
            BLOCK_FORBIDDEN_VALUE,
            BLOCK_REQUIRED_FIELD_MISSING,
            BLOCK_AMBIGUOUS_TEXT,
            BLOCK_REFERENCE_OUTBOX_MISMATCH,
            BLOCK_REFERENCE_PAYLOAD_HASH_MISMATCH,
            BLOCK_APPROVAL_DISABLED,
            BLOCK_DISPATCH_DISABLED,
            BLOCK_FUTURE_GATES_MISSING,
            BLOCK_DUPLICATE_MESSAGE,
        ],
        "invariants": [
            "message_text_hash_is_deterministic",
            "dedupe_key_changes_by_operator_identity",
            "duplicate_message_suppressed_not_appended",
            "exact_approve_phrase_creates_intent_candidate_only",
            "unknown_or_ambiguous_text_blocked",
            "outbox_reference_mismatch_blocks_candidate",
            "payload_hash_reference_mismatch_blocks_candidate",
            "missing_evidence_refs_blocks_message_and_candidate",
            "replay_cannot_create_approval_or_dispatch",
            "remote_inbox_never_mutates_approval_ledger_or_outbox",
            "telegram_channel_dispatch_destination_not_created_here",
            "artifact_writer_touches_only_docs_automation_0174TG",
        ],
        "safety_flags": dict(SAFETY_FLAGS),
        "next_required_gate": NEXT_REQUIRED_GATE,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
    }
    packet["checksum_sha256"] = compute_checksum(packet)
    return packet


def build_doc():
    packet = build_packet()
    flags = "\n".join(
        f"- `{k}` = `{str(v).lower()}`"
        for k, v in sorted(SAFETY_FLAGS.items()))
    return (
        "# 0174TG Telegram Remote Operator Inbox Contract\n\n"
        "This contract defines local redacted Telegram remote operator inbox "
        "messages. It does not define channel dispatch behavior.\n\n"
        "## Role Separation\n\n"
        "- Remote Operator Inbox: future operator review decisions.\n"
        "- Channel Dispatch Destination: future public/channel send target.\n\n"
        "0174TG implements only the first role.\n\n"
        "## Message Model\n\n"
        "`RemoteOperatorInboxMessage` binds redacted message text, operator "
        "identity ref, timestamp bucket, optional approval/outbox/payload refs, "
        "evidence refs, and safety flags. Raw Telegram updates are not stored.\n\n"
        "## Intent Candidate Model\n\n"
        "`ParsedOperatorIntentCandidate` maps exact local phrases to "
        "`approve`, `reject`, `edit_request`, `hold`, or `unknown`. Every "
        "candidate remains blocked and reports `valid_for_approval=false` and "
        "`valid_for_dispatch=false`.\n\n"
        "## Dedupe / Replay\n\n"
        "The registry is append-only. Dedupe uses message text hash, operator "
        "identity ref, timestamp bucket, and inbox message id. Duplicate replay "
        "is suppressed and creates no approval or dispatch.\n\n"
        "## Safety Flags\n\n"
        f"{flags}\n\n"
        "## Next Gate\n\n"
        f"{packet['exact_next_task_recommendation']}\n"
    )


def write_artifacts(repo_root):
    """Write deterministic packet and runbook only under docs/automation/0174TG."""
    out_dir = os.path.join(repo_root, DOC_REL_DIR)
    os.makedirs(out_dir, exist_ok=True)
    packet = build_packet()
    packet_path = os.path.join(out_dir, PACKET_FILENAME)
    doc_path = os.path.join(out_dir, DOC_FILENAME)
    with open(packet_path, "w", encoding="utf-8") as fh:
        fh.write(serialize(packet))
    with open(doc_path, "w", encoding="utf-8") as fh:
        fh.write(build_doc())
    return {"packet_path": packet_path, "doc_path": doc_path,
            "packet": packet}
