"""Telegram challenge validation to approval-ledger candidate contract (0174TI).

Deterministic LOCAL-only bridge from 0174TH validation results to approval
ledger candidates. A candidate is evidence only: it never records approval facts,
mutates the approval ledger, mutates outbox state, dispatches, calls Telegram,
configures webhooks, reads env files, hydrates credentials, calls providers, or
performs network behavior.
"""

import hashlib
import json
import os.path

from live_contentops import approval_ledger_payload_hash_contract as approval
from live_contentops import telegram_review_challenge_contract as review

TASK_LABEL = (
    "TASK_CONTENTOPS_0174TI_TELEGRAM_CHALLENGE_VALIDATION_TO_APPROVAL_LEDGER_CANDIDATE_CONTRACT_V0"
)
MODEL = "TELEGRAM_APPROVAL_LEDGER_CANDIDATE_CONTRACT_0174TI"
MODEL_VERSION = "0174TI_TELEGRAM_APPROVAL_LEDGER_CANDIDATE_V1"
SOURCE_BASELINE_COMMIT = "3bd24cb5dc2af7cd0ef55df92aaa228931d4f00e"

DOC_REL_DIR = os.path.join("docs", "automation", "0174TI")
PACKET_FILENAME = "telegram_approval_ledger_candidate_contract_packet.json"
DOC_FILENAME = "telegram_approval_ledger_candidate_contract.md"

CANDIDATE_SCHEMA = "contentops.telegram_approval_ledger_candidate"
CANDIDATE_SCHEMA_VERSION = "0174TI_APPROVAL_LEDGER_CANDIDATE_V1"
DEDUPE_SCHEMA = "contentops.telegram_approval_ledger_candidate_dedupe_key"
DEDUPE_SCHEMA_VERSION = "0174TI_APPROVAL_LEDGER_CANDIDATE_DEDUPE_V1"

VALIDITY_LOCAL_ONLY = "approval_ledger_candidate_valid_local_only"
VALIDITY_BLOCKED = "approval_ledger_candidate_blocked"
VALIDITY_DUPLICATE_SUPPRESSED = "approval_ledger_candidate_duplicate_suppressed"

INTENT_APPROVAL = "approval_candidate"
INTENT_REJECT = "reject_candidate"
INTENT_EDIT_REQUEST = "edit_request_candidate"
INTENT_BLOCKED = "blocked_candidate"

REGISTRY_APPENDED = "approval_ledger_candidate_appended_local_only"
REGISTRY_DUPLICATE_SUPPRESSED = "approval_ledger_candidate_duplicate_suppressed"

BLOCK_REQUIRED_FIELD_MISSING = "required_field_missing"
BLOCK_MISSING_EVIDENCE_REFS = "evidence_refs_missing"
BLOCK_FORBIDDEN_VALUE = "forbidden_value_detected"
BLOCK_VALIDATION_ID_MISMATCH = "validation_result_id_mismatch"
BLOCK_REVIEW_CHALLENGE_ID_MISMATCH = "review_challenge_id_mismatch"
BLOCK_REVIEW_REPLY_ID_MISMATCH = "review_reply_id_mismatch"
BLOCK_VALIDATION_NOT_STRUCTURALLY_PASSING = "validation_not_structurally_passing"
BLOCK_REPLY_CLASS_AMBIGUOUS_OR_INVALID = "reply_class_ambiguous_or_invalid"
BLOCK_WRONG_SENDER = "operator_identity_ref_mismatch"
BLOCK_WRONG_NONCE = "nonce_mismatch"
BLOCK_WRONG_HASH = "payload_hash_short_mismatch"
BLOCK_EXPIRED = "review_challenge_expired"
BLOCK_CHALLENGE_INACTIVE = "review_challenge_not_active"
BLOCK_UPSTREAM_LEDGER_MUTATED = "upstream_approval_ledger_mutation_flag_set"
BLOCK_UPSTREAM_OUTBOX_MUTATED = "upstream_outbox_mutation_flag_set"
BLOCK_UPSTREAM_DISPATCH_OR_LIVE_FLAG_SET = "upstream_dispatch_live_or_public_flag_set"
BLOCK_DUPLICATE_CANDIDATE = "duplicate_candidate_hash_suppressed"
BLOCK_LEDGER_MUTATION_DISABLED = "approval_ledger_mutation_disabled_in_0174TI"
BLOCK_OUTBOX_MUTATION_DISABLED = "outbox_mutation_disabled_in_0174TI"
BLOCK_DISPATCH_DISABLED = "dispatch_disabled_in_0174TI"

CANDIDATE_HASH_INPUTS = (
    "candidate_schema",
    "candidate_schema_version",
    "source_review_challenge_id",
    "source_review_reply_id",
    "source_validation_result_id",
    "source_approval_challenge_id",
    "source_outbox_entry_id",
    "payload_hash",
    "payload_hash_short",
    "platform",
    "destination_binding_id",
    "operator_identity_ref",
    "reply_class",
    "nonce_match",
    "hash_match",
    "sender_match",
    "not_expired",
    "challenge_active",
)

CANDIDATE_HASH_EXCLUDES = (
    "raw_telegram_update", "raw_credential", "raw_token", "api_key",
    "access_token", "refresh_token", "bearer_token", "client_secret",
    "raw_env_var", "dotenv_value", "request_headers", "cookies",
    "raw_provider_response", "raw_platform_response", "telegram_url",
)

SAFETY_FLAGS = {
    "approval_ledger_mutated": False,
    "outbox_mutated": False,
    "dispatch_ready": False,
    "live_ready": False,
    "telegram_api_called": False,
    "telegram_polling_performed": False,
    "telegram_send_performed": False,
    "webhook_enabled": False,
    "credential_hydrated": False,
    "env_read": False,
    "network_performed": False,
    "llm_provider_called": False,
    "autonomous_posting_allowed": False,
    "public_postable": False,
}

NEXT_REQUIRED_GATE = (
    "approval ledger fact recording gate consuming 0174TI candidates, then "
    "audited revocation/expiration handling, dispatch outbox revalidation, kill "
    "switch, supervised dispatch gates, and separate operator-owned credential "
    "and live platform gates before any live behavior"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174TJ_APPROVAL_LEDGER_CANDIDATE_TO_LEDGER_RECORDING_CONTRACT_V0"
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
    return [BLOCK_REQUIRED_FIELD_MISSING for field in fields if not obj.get(field)]


def _upstream_flag_block(validation):
    reasons = []
    flags = validation.get("safety_flags", {})
    if validation.get("approval_ledger_mutated") or flags.get("approval_ledger_mutated"):
        reasons.append(BLOCK_UPSTREAM_LEDGER_MUTATED)
    if validation.get("outbox_mutated") or flags.get("outbox_mutated"):
        reasons.append(BLOCK_UPSTREAM_OUTBOX_MUTATED)
    if (validation.get("dispatch_created") or validation.get("valid_for_dispatch") or
            flags.get("dispatch_ready") or flags.get("live_ready") or
            flags.get("public_postable")):
        reasons.append(BLOCK_UPSTREAM_DISPATCH_OR_LIVE_FLAG_SET)
    return reasons


def _validation_result_id_matches(validation):
    if not validation.get("validation_result_id"):
        return False
    expected = review.compute_checksum({
        "validation_schema": validation.get("validation_schema"),
        "validation_schema_version": validation.get("validation_schema_version"),
        "review_challenge_id": validation.get("review_challenge_id"),
        "reply_id": validation.get("reply_id"),
        "reply_class": validation.get("reply_class"),
        "validation_status": validation.get("validation_status"),
        "blocked_reasons": validation.get("blocked_reasons", []),
    })
    return expected == validation.get("validation_result_id")


def _candidate_intent(reply_class):
    if reply_class == review.REPLY_EXPLICIT_APPROVE:
        return INTENT_APPROVAL
    if reply_class == review.REPLY_EXPLICIT_REJECT:
        return INTENT_REJECT
    if reply_class == review.REPLY_EXPLICIT_EDIT_REQUEST:
        return INTENT_EDIT_REQUEST
    return INTENT_BLOCKED


def _structural_validation_passes(validation):
    return (
        validation.get("sender_match") is True and
        validation.get("nonce_match") is True and
        validation.get("hash_match") is True and
        validation.get("not_expired") is True and
        validation.get("challenge_active") is True and
        validation.get("evidence_refs_present") is True
    )


def compute_candidate_hash(candidate_fields):
    payload = {key: candidate_fields.get(key) for key in CANDIDATE_HASH_INPUTS}
    return compute_checksum(payload)


def build_approval_ledger_candidate(challenge, reply, validation, created_at_epoch):
    reply_class = validation.get("reply_class", reply.get("parsed_reply_class"))
    evidence_refs = []
    evidence_refs.extend(challenge.get("evidence_refs", []))
    evidence_refs.extend(reply.get("evidence_refs", []))
    candidate = {
        "candidate_schema": CANDIDATE_SCHEMA,
        "candidate_schema_version": CANDIDATE_SCHEMA_VERSION,
        "source_review_challenge_id": challenge.get("review_challenge_id"),
        "source_review_reply_id": reply.get("reply_id"),
        "source_validation_result_id": validation.get("validation_result_id"),
        "source_approval_challenge_id": challenge.get("source_approval_challenge_id"),
        "source_outbox_entry_id": challenge.get("source_outbox_entry_id"),
        "payload_hash": challenge.get("payload_hash"),
        "payload_hash_short": challenge.get("payload_hash_short"),
        "platform": challenge.get("platform"),
        "destination_binding_id": challenge.get("destination_binding_id"),
        "operator_identity_ref": challenge.get("operator_identity_ref"),
        "reply_class": reply_class,
        "candidate_intent_class": _candidate_intent(reply_class),
        "nonce_match": bool(validation.get("nonce_match")),
        "hash_match": bool(validation.get("hash_match")),
        "sender_match": bool(validation.get("sender_match")),
        "not_expired": bool(validation.get("not_expired")),
        "challenge_active": bool(validation.get("challenge_active")),
        "created_at_epoch": int(created_at_epoch),
        "evidence_refs": evidence_refs,
        "approval_ledger_mutated": False,
        "outbox_mutated": False,
        "dispatch_ready": False,
        "live_ready": False,
        "public_postable": False,
        "safety_flags": dict(SAFETY_FLAGS),
    }
    candidate["candidate_hash"] = compute_candidate_hash(candidate)
    candidate["approval_ledger_candidate_id"] = compute_checksum({
        "candidate_schema": CANDIDATE_SCHEMA,
        "candidate_schema_version": CANDIDATE_SCHEMA_VERSION,
        "candidate_hash": candidate["candidate_hash"],
        "source_validation_result_id": candidate["source_validation_result_id"],
    })

    reasons = []
    reasons.extend(_required_block(candidate, (
        "approval_ledger_candidate_id", "source_review_challenge_id",
        "source_review_reply_id", "source_validation_result_id",
        "source_approval_challenge_id", "source_outbox_entry_id",
        "payload_hash", "payload_hash_short", "platform",
        "destination_binding_id", "operator_identity_ref", "reply_class",
        "candidate_hash")))
    if not evidence_refs:
        reasons.append(BLOCK_MISSING_EVIDENCE_REFS)
    if not _validation_result_id_matches(validation):
        reasons.append(BLOCK_VALIDATION_ID_MISMATCH)
    if validation.get("review_challenge_id") != challenge.get("review_challenge_id"):
        reasons.append(BLOCK_REVIEW_CHALLENGE_ID_MISMATCH)
    if validation.get("reply_id") != reply.get("reply_id"):
        reasons.append(BLOCK_REVIEW_REPLY_ID_MISMATCH)
    if reply.get("review_challenge_id") != challenge.get("review_challenge_id"):
        reasons.append(BLOCK_REVIEW_CHALLENGE_ID_MISMATCH)
    if reply_class in (review.REPLY_AMBIGUOUS, review.REPLY_INVALID):
        reasons.append(BLOCK_REPLY_CLASS_AMBIGUOUS_OR_INVALID)
    if not validation.get("sender_match"):
        reasons.append(BLOCK_WRONG_SENDER)
    if not validation.get("nonce_match"):
        reasons.append(BLOCK_WRONG_NONCE)
    if not validation.get("hash_match"):
        reasons.append(BLOCK_WRONG_HASH)
    if not validation.get("not_expired"):
        reasons.append(BLOCK_EXPIRED)
    if not validation.get("challenge_active"):
        reasons.append(BLOCK_CHALLENGE_INACTIVE)
    if not _structural_validation_passes(validation):
        reasons.append(BLOCK_VALIDATION_NOT_STRUCTURALLY_PASSING)
    reasons.extend(_upstream_flag_block(validation))
    reasons.extend(_leak_block(candidate))
    reasons.extend([
        BLOCK_LEDGER_MUTATION_DISABLED,
        BLOCK_OUTBOX_MUTATION_DISABLED,
        BLOCK_DISPATCH_DISABLED,
    ])
    candidate["blocked_reasons"] = _blocked(*reasons)

    allowed_candidate = (
        _structural_validation_passes(validation) and
        _validation_result_id_matches(validation) and
        validation.get("review_challenge_id") == challenge.get("review_challenge_id") and
        validation.get("reply_id") == reply.get("reply_id") and
        reply.get("review_challenge_id") == challenge.get("review_challenge_id") and
        reply_class in (
            review.REPLY_EXPLICIT_APPROVE,
            review.REPLY_EXPLICIT_REJECT,
            review.REPLY_EXPLICIT_EDIT_REQUEST,
        ) and
        bool(evidence_refs) and
        not _upstream_flag_block(validation) and
        not _leak_block(candidate)
    )
    candidate["candidate_validity_class"] = (
        VALIDITY_LOCAL_ONLY if allowed_candidate else VALIDITY_BLOCKED
    )
    if not allowed_candidate:
        candidate["candidate_intent_class"] = (
            INTENT_BLOCKED if reply_class in (review.REPLY_AMBIGUOUS, review.REPLY_INVALID)
            else candidate["candidate_intent_class"]
        )
    return candidate


class ApprovalLedgerCandidateRegistry:
    def __init__(self):
        self._candidates = []
        self._by_hash = {}

    def append(self, candidate):
        key = candidate["candidate_hash"]
        if key in self._by_hash:
            duplicate = dict(self._by_hash[key])
            duplicate["candidate_validity_class"] = VALIDITY_DUPLICATE_SUPPRESSED
            duplicate["blocked_reasons"] = _blocked(
                *duplicate.get("blocked_reasons", []), BLOCK_DUPLICATE_CANDIDATE)
            return {
                "status": REGISTRY_DUPLICATE_SUPPRESSED,
                "candidate": duplicate,
                "duplicate_suppressed": True,
                "blocked_reasons": [BLOCK_DUPLICATE_CANDIDATE],
                "approval_ledger_mutated": False,
                "outbox_mutated": False,
                "dispatch_ready": False,
                "live_ready": False,
                "public_postable": False,
                "safety_flags": dict(SAFETY_FLAGS),
            }
        entry = dict(candidate)
        entry["registry_sequence"] = len(self._candidates) + 1
        self._candidates.append(entry)
        self._by_hash[key] = entry
        return {
            "status": REGISTRY_APPENDED,
            "candidate": entry,
            "duplicate_suppressed": False,
            "blocked_reasons": list(entry.get("blocked_reasons", [])),
            "approval_ledger_mutated": False,
            "outbox_mutated": False,
            "dispatch_ready": False,
            "live_ready": False,
            "public_postable": False,
            "safety_flags": dict(SAFETY_FLAGS),
        }

    def candidates(self):
        return list(self._candidates)


def build_packet():
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "status": "pass",
        "contract_status": "deterministic_local_approval_ledger_candidate_ready",
        "candidate_schema": CANDIDATE_SCHEMA,
        "candidate_schema_version": CANDIDATE_SCHEMA_VERSION,
        "candidate_hash_algorithm": "sha256",
        "candidate_hash_inputs": list(CANDIDATE_HASH_INPUTS),
        "candidate_hash_excludes": list(CANDIDATE_HASH_EXCLUDES),
        "candidate_validity_classes": [
            VALIDITY_LOCAL_ONLY, VALIDITY_BLOCKED, VALIDITY_DUPLICATE_SUPPRESSED],
        "candidate_intent_classes": [
            INTENT_APPROVAL, INTENT_REJECT, INTENT_EDIT_REQUEST, INTENT_BLOCKED],
        "blocked_reasons": [
            BLOCK_REQUIRED_FIELD_MISSING, BLOCK_MISSING_EVIDENCE_REFS,
            BLOCK_FORBIDDEN_VALUE, BLOCK_VALIDATION_ID_MISMATCH,
            BLOCK_REVIEW_CHALLENGE_ID_MISMATCH, BLOCK_REVIEW_REPLY_ID_MISMATCH,
            BLOCK_VALIDATION_NOT_STRUCTURALLY_PASSING,
            BLOCK_REPLY_CLASS_AMBIGUOUS_OR_INVALID, BLOCK_WRONG_SENDER,
            BLOCK_WRONG_NONCE, BLOCK_WRONG_HASH, BLOCK_EXPIRED,
            BLOCK_CHALLENGE_INACTIVE, BLOCK_UPSTREAM_LEDGER_MUTATED,
            BLOCK_UPSTREAM_OUTBOX_MUTATED, BLOCK_UPSTREAM_DISPATCH_OR_LIVE_FLAG_SET,
            BLOCK_DUPLICATE_CANDIDATE, BLOCK_LEDGER_MUTATION_DISABLED,
            BLOCK_OUTBOX_MUTATION_DISABLED, BLOCK_DISPATCH_DISABLED],
        "invariants": [
            "valid_0174th_approve_validation_creates_local_candidate_only",
            "reject_reply_creates_reject_candidate_only",
            "edit_request_reply_creates_edit_request_candidate_only",
            "ambiguous_or_invalid_reply_blocks_candidate",
            "wrong_sender_nonce_hash_or_expiration_blocks",
            "missing_evidence_refs_blocks_candidate",
            "candidate_hash_deterministic_for_identical_inputs",
            "candidate_hash_changes_when_authority_fields_change",
            "duplicate_candidate_hash_suppressed_not_appended",
            "candidate_never_mutates_approval_ledger_or_outbox",
            "candidate_never_dispatches_or_marks_live_ready",
            "artifact_writer_touches_only_docs_automation_0174TI"],
        "safety_flags": dict(SAFETY_FLAGS),
        "next_required_gate": NEXT_REQUIRED_GATE,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
    }
    packet["checksum_sha256"] = compute_checksum(packet)
    return packet


def build_doc():
    flags = "\n".join(f"- `{k}` = `{str(v).lower()}`" for k, v in sorted(SAFETY_FLAGS.items()))
    return (
        "# 0174TI Telegram Approval Ledger Candidate Contract\n\n"
        "Local-only bridge from 0174TH validation to approval-ledger candidate. "
        "Candidates are evidence only and cannot record ledger facts, mutate "
        "outbox state, dispatch, call Telegram, read env, hydrate credentials, "
        "call providers, or perform network behavior.\n\n"
        "## Candidate Validity Classes\n\n"
        f"- `{VALIDITY_LOCAL_ONLY}`\n"
        f"- `{VALIDITY_BLOCKED}`\n"
        f"- `{VALIDITY_DUPLICATE_SUPPRESSED}`\n\n"
        "## Candidate Intent Classes\n\n"
        f"- `{INTENT_APPROVAL}`\n"
        f"- `{INTENT_REJECT}`\n"
        f"- `{INTENT_EDIT_REQUEST}`\n"
        f"- `{INTENT_BLOCKED}`\n\n"
        "## Hash Rules\n\n"
        "Candidate hash is sha256 over exact authority fields: validation id, "
        "challenge id, reply id, approval challenge id, outbox id, payload hash, "
        "platform binding, destination binding, operator identity, reply class, "
        "nonce/hash/sender/expiration/activity proofs.\n\n"
        "## Non-Mutation Rules\n\n"
        "Every candidate remains local-only. It cannot mutate approval ledger, "
        "outbox, dispatch state, live state, or public-postable state.\n\n"
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
