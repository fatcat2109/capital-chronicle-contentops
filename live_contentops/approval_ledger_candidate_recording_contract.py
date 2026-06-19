"""Approval ledger candidate -> ledger recording contract (0174TJ).

Deterministic LOCAL-only gate from 0174TI candidates to append-only ledger
recording facts. Recording a fact never authorizes dispatch, mutates outbox,
contacts Telegram, reads env, hydrates credentials, calls providers, or performs
network behavior.
"""

import hashlib
import json
import os.path

from live_contentops import approval_ledger_payload_hash_contract as approval
from live_contentops import telegram_approval_ledger_candidate_contract as candidate_model

TASK_LABEL = (
    "TASK_CONTENTOPS_0174TJ_APPROVAL_LEDGER_CANDIDATE_TO_LEDGER_RECORDING_CONTRACT_V0"
)
MODEL = "APPROVAL_LEDGER_CANDIDATE_RECORDING_CONTRACT_0174TJ"
MODEL_VERSION = "0174TJ_APPROVAL_LEDGER_RECORDING_V1"
SOURCE_BASELINE_COMMIT = "c80d440f919f1d01e22c47e5e9b57002539e388e"

DOC_REL_DIR = os.path.join("docs", "automation", "0174TJ")
PACKET_FILENAME = "approval_ledger_candidate_recording_contract_packet.json"
DOC_FILENAME = "approval_ledger_candidate_recording_contract.md"

RECORDING_SCHEMA = "contentops.approval_ledger_recording_fact"
RECORDING_SCHEMA_VERSION = "0174TJ_APPROVAL_LEDGER_RECORDING_FACT_V1"

FACT_APPROVAL_RECORDED = "remote_operator_approval_recorded"
FACT_REJECT_RECORDED = "remote_operator_reject_recorded"
FACT_EDIT_REQUEST_RECORDED = "remote_operator_edit_request_recorded"
FACT_RECORDING_BLOCKED = "candidate_recording_blocked"
FACT_DUPLICATE_SUPPRESSED = "duplicate_ledger_fact_suppressed"

STATUS_RECORDED_LOCAL_ONLY = "approval_ledger_fact_recorded_local_only"
STATUS_BLOCKED = "approval_ledger_fact_recording_blocked"
STATUS_DUPLICATE_SUPPRESSED = "approval_ledger_fact_duplicate_suppressed"

BLOCK_REQUIRED_FIELD_MISSING = "required_field_missing"
BLOCK_MISSING_EVIDENCE_REFS = "evidence_refs_missing"
BLOCK_FORBIDDEN_VALUE = "forbidden_value_detected"
BLOCK_CANDIDATE_HASH_MISMATCH = "candidate_hash_mismatch"
BLOCK_CANDIDATE_VALIDITY_MISMATCH = "candidate_validity_class_mismatch"
BLOCK_PAYLOAD_HASH_MISMATCH = "payload_hash_mismatch"
BLOCK_BLOCKED_CANDIDATE = "blocked_candidate_cannot_record_approval"
BLOCK_UNKNOWN_INTENT = "unknown_candidate_intent_class"
BLOCK_UPSTREAM_OUTBOX_MUTATED = "upstream_outbox_mutation_flag_set"
BLOCK_UPSTREAM_DISPATCH_OR_LIVE_FLAG_SET = "upstream_dispatch_live_or_public_flag_set"
BLOCK_DUPLICATE_FACT = "duplicate_ledger_recording_fact_suppressed"
BLOCK_DISPATCH_DISABLED = "dispatch_disabled_in_0174TJ"
BLOCK_OUTBOX_MUTATION_DISABLED = "outbox_mutation_disabled_in_0174TJ"

RECORDING_FACT_HASH_INPUTS = (
    "recording_schema", "recording_schema_version", "source_candidate_id",
    "source_candidate_hash", "source_review_challenge_id",
    "source_review_reply_id", "source_validation_result_id",
    "source_approval_challenge_id", "source_outbox_entry_id", "payload_hash",
    "payload_hash_short", "platform", "destination_binding_id",
    "operator_identity_ref", "recording_fact_class", "approval_scope",
    "expires_at_epoch", "inherited_expiration_proof", "evidence_refs",
)

RECORDING_HASH_EXCLUDES = (
    "raw_telegram_update", "raw_credential", "raw_token", "api_key",
    "access_token", "refresh_token", "bearer_token", "client_secret",
    "raw_env_var", "dotenv_value", "request_headers", "cookies",
    "raw_provider_response", "raw_platform_response", "telegram_url",
)

SAFETY_FLAGS = {
    "approval_ledger_recorded": False,
    "approval_authorizes_dispatch": False,
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
    "approval ledger revocation/expiration recording contract, then dispatch "
    "outbox revalidation gate, kill switch, supervised dispatch gates, and "
    "separate operator-owned credential/live platform gates before live behavior"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174TK_APPROVAL_LEDGER_REVOCATION_EXPIRATION_CONTRACT_V0"
)


def serialize(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def compute_checksum(obj):
    return hashlib.sha256(serialize(obj).encode("utf-8")).hexdigest()


def scan_for_leaks(obj):
    return approval.scan_for_leaks(obj)


def _blocked(*reasons):
    return sorted(set(reason for reason in reasons if reason))


def _leak_block(obj):
    return [BLOCK_FORBIDDEN_VALUE] if scan_for_leaks(obj) else []


def _required_block(obj, fields):
    return [BLOCK_REQUIRED_FIELD_MISSING for field in fields if not obj.get(field)]


def _candidate_hash_matches(candidate):
    if not candidate.get("candidate_hash"):
        return False
    return candidate_model.compute_candidate_hash(candidate) == candidate.get("candidate_hash")


def _candidate_validity_matches(candidate):
    return candidate.get("candidate_validity_class") == candidate_model.VALIDITY_LOCAL_ONLY


def _payload_hash_bound(candidate, current_payload_hash):
    if current_payload_hash is None:
        return True
    return candidate.get("payload_hash") == current_payload_hash


def _upstream_flag_block(candidate):
    reasons = []
    flags = candidate.get("safety_flags", {})
    if candidate.get("outbox_mutated") or flags.get("outbox_mutated"):
        reasons.append(BLOCK_UPSTREAM_OUTBOX_MUTATED)
    if (
            candidate.get("dispatch_ready") or candidate.get("live_ready") or
            candidate.get("public_postable") or flags.get("dispatch_ready") or
            flags.get("live_ready") or flags.get("public_postable")):
        reasons.append(BLOCK_UPSTREAM_DISPATCH_OR_LIVE_FLAG_SET)
    return reasons


def _fact_class_for_candidate(candidate):
    intent = candidate.get("candidate_intent_class")
    if intent == candidate_model.INTENT_APPROVAL:
        return FACT_APPROVAL_RECORDED
    if intent == candidate_model.INTENT_REJECT:
        return FACT_REJECT_RECORDED
    if intent == candidate_model.INTENT_EDIT_REQUEST:
        return FACT_EDIT_REQUEST_RECORDED
    return FACT_RECORDING_BLOCKED


def _approval_scope_for_fact(fact_class):
    if fact_class == FACT_APPROVAL_RECORDED:
        return "remote_operator_exact_payload_approval"
    if fact_class == FACT_REJECT_RECORDED:
        return "remote_operator_exact_payload_reject"
    if fact_class == FACT_EDIT_REQUEST_RECORDED:
        return "remote_operator_exact_payload_edit_request"
    return "candidate_recording_blocked"


def _recording_safety_flags(recorded):
    flags = dict(SAFETY_FLAGS)
    flags["approval_ledger_recorded"] = bool(recorded)
    return flags


def _redacted_remote_operator_refs(candidate):
    return {
        "operator_identity_ref": candidate.get("operator_identity_ref"),
        "source_review_reply_id": candidate.get("source_review_reply_id"),
        "source_review_challenge_id": candidate.get("source_review_challenge_id"),
    }


def _expiration_proof(candidate):
    return {
        "not_expired": bool(candidate.get("not_expired")),
        "challenge_active": bool(candidate.get("challenge_active")),
        "source_validation_result_id": candidate.get("source_validation_result_id"),
    }


def compute_recording_fact_hash(fact_fields):
    payload = {key: fact_fields.get(key) for key in RECORDING_FACT_HASH_INPUTS}
    return compute_checksum(payload)


def compute_ledger_recording_fact_id(fact_fields):
    return compute_checksum({
        "recording_schema": RECORDING_SCHEMA,
        "recording_schema_version": RECORDING_SCHEMA_VERSION,
        "recording_fact_hash": fact_fields.get("recording_fact_hash"),
        "source_candidate_id": fact_fields.get("source_candidate_id"),
    })


def _base_fact(candidate, created_at_epoch, fact_class):
    fact = {
        "recording_schema": RECORDING_SCHEMA,
        "recording_schema_version": RECORDING_SCHEMA_VERSION,
        "source_candidate_id": candidate.get("approval_ledger_candidate_id"),
        "source_candidate_hash": candidate.get("candidate_hash"),
        "source_review_challenge_id": candidate.get("source_review_challenge_id"),
        "source_review_reply_id": candidate.get("source_review_reply_id"),
        "source_validation_result_id": candidate.get("source_validation_result_id"),
        "source_approval_challenge_id": candidate.get("source_approval_challenge_id"),
        "source_outbox_entry_id": candidate.get("source_outbox_entry_id"),
        "payload_hash": candidate.get("payload_hash"),
        "payload_hash_short": candidate.get("payload_hash_short"),
        "platform": candidate.get("platform"),
        "destination_binding_id": candidate.get("destination_binding_id"),
        "operator_identity_ref": candidate.get("operator_identity_ref"),
        "recording_fact_class": fact_class,
        "approval_scope": _approval_scope_for_fact(fact_class),
        "created_at_epoch": int(created_at_epoch),
        "expires_at_epoch": candidate.get("expires_at_epoch"),
        "inherited_expiration_proof": _expiration_proof(candidate),
        "evidence_refs": list(candidate.get("evidence_refs", [])),
        "redacted_remote_operator_refs": _redacted_remote_operator_refs(candidate),
        "approval_authorizes_dispatch": False,
        "valid_for_dispatch": False,
        "outbox_mutated": False,
        "dispatch_ready": False,
        "live_ready": False,
        "public_postable": False,
        "safety_flags": _recording_safety_flags(fact_class == FACT_APPROVAL_RECORDED),
    }
    fact["recording_fact_hash"] = compute_recording_fact_hash(fact)
    fact["ledger_recording_fact_id"] = compute_ledger_recording_fact_id(fact)
    return fact


def _result(recording_status, ledger_fact_class, candidate, fact, reasons,
            current_payload_hash, duplicate=False):
    recorded = recording_status == STATUS_RECORDED_LOCAL_ONLY
    return {
        "recording_status": recording_status,
        "ledger_fact_class": ledger_fact_class,
        "candidate_hash_match": _candidate_hash_matches(candidate),
        "candidate_validity_match": _candidate_validity_matches(candidate),
        "payload_hash_bound": _payload_hash_bound(candidate, current_payload_hash),
        "duplicate_fact_suppressed": bool(duplicate),
        "blocked_reasons": _blocked(*reasons),
        "ledger_recording_fact": fact,
        "approval_ledger_recorded": bool(recorded and ledger_fact_class == FACT_APPROVAL_RECORDED),
        "approval_authorizes_dispatch": False,
        "valid_for_dispatch": False,
        "outbox_mutated": False,
        "dispatch_ready": False,
        "live_ready": False,
        "public_postable": False,
        "safety_flags": _recording_safety_flags(recorded),
    }


def _recording_block_reasons(candidate, current_payload_hash):
    fact_class = _fact_class_for_candidate(candidate)
    reasons = []
    reasons.extend(_required_block(candidate, (
        "approval_ledger_candidate_id", "candidate_hash",
        "source_review_challenge_id", "source_review_reply_id",
        "source_validation_result_id", "source_approval_challenge_id",
        "source_outbox_entry_id", "payload_hash", "payload_hash_short",
        "platform", "destination_binding_id", "operator_identity_ref",
        "candidate_intent_class")))
    if not candidate.get("evidence_refs"):
        reasons.append(BLOCK_MISSING_EVIDENCE_REFS)
    if not _candidate_hash_matches(candidate):
        reasons.append(BLOCK_CANDIDATE_HASH_MISMATCH)
    if not _candidate_validity_matches(candidate):
        reasons.append(BLOCK_CANDIDATE_VALIDITY_MISMATCH)
    if not _payload_hash_bound(candidate, current_payload_hash):
        reasons.append(BLOCK_PAYLOAD_HASH_MISMATCH)
    if candidate.get("candidate_intent_class") == candidate_model.INTENT_BLOCKED:
        reasons.append(BLOCK_BLOCKED_CANDIDATE)
    if fact_class == FACT_RECORDING_BLOCKED:
        reasons.append(BLOCK_UNKNOWN_INTENT)
    reasons.extend(_upstream_flag_block(candidate))
    reasons.extend(_leak_block(candidate))
    reasons.extend([BLOCK_DISPATCH_DISABLED, BLOCK_OUTBOX_MUTATION_DISABLED])
    return _blocked(*reasons)


def record_approval_ledger_candidate(candidate, created_at_epoch, current_payload_hash=None):
    fact_class = _fact_class_for_candidate(candidate)
    reasons = _recording_block_reasons(candidate, current_payload_hash)
    hard_blockers = set(reasons) - {BLOCK_DISPATCH_DISABLED, BLOCK_OUTBOX_MUTATION_DISABLED}
    if hard_blockers:
        fact = _base_fact(candidate, created_at_epoch, FACT_RECORDING_BLOCKED)
        return _result(
            STATUS_BLOCKED, FACT_RECORDING_BLOCKED, candidate, fact, reasons,
            current_payload_hash)
    fact = _base_fact(candidate, created_at_epoch, fact_class)
    return _result(
        STATUS_RECORDED_LOCAL_ONLY, fact_class, candidate, fact, reasons,
        current_payload_hash)


class ApprovalLedgerRecordingRegistry:
    def __init__(self):
        self._facts = []
        self._by_hash = {}

    def append(self, recording_result):
        fact = recording_result.get("ledger_recording_fact") or {}
        key = fact.get("recording_fact_hash")
        if key in self._by_hash:
            duplicate_fact = dict(self._by_hash[key])
            duplicate_fact["recording_fact_class"] = FACT_DUPLICATE_SUPPRESSED
            duplicate_result = dict(recording_result)
            duplicate_result.update({
                "recording_status": STATUS_DUPLICATE_SUPPRESSED,
                "ledger_fact_class": FACT_DUPLICATE_SUPPRESSED,
                "duplicate_fact_suppressed": True,
                "ledger_recording_fact": duplicate_fact,
                "approval_ledger_recorded": False,
                "valid_for_dispatch": False,
                "outbox_mutated": False,
                "dispatch_ready": False,
                "live_ready": False,
                "public_postable": False,
                "blocked_reasons": _blocked(
                    *recording_result.get("blocked_reasons", []), BLOCK_DUPLICATE_FACT),
                "safety_flags": _recording_safety_flags(False),
            })
            return duplicate_result
        entry = dict(fact)
        entry["registry_sequence"] = len(self._facts) + 1
        self._facts.append(entry)
        self._by_hash[key] = entry
        return dict(recording_result)

    def facts(self):
        return list(self._facts)


def build_packet():
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "status": "pass",
        "contract_status": "deterministic_local_approval_ledger_recording_ready",
        "recording_schema": RECORDING_SCHEMA,
        "recording_schema_version": RECORDING_SCHEMA_VERSION,
        "fact_classes": [
            FACT_APPROVAL_RECORDED, FACT_REJECT_RECORDED,
            FACT_EDIT_REQUEST_RECORDED, FACT_RECORDING_BLOCKED,
            FACT_DUPLICATE_SUPPRESSED],
        "recording_statuses": [
            STATUS_RECORDED_LOCAL_ONLY, STATUS_BLOCKED,
            STATUS_DUPLICATE_SUPPRESSED],
        "recording_fact_hash_algorithm": "sha256",
        "recording_fact_hash_inputs": list(RECORDING_FACT_HASH_INPUTS),
        "recording_hash_excludes": list(RECORDING_HASH_EXCLUDES),
        "blocked_reasons": [
            BLOCK_REQUIRED_FIELD_MISSING, BLOCK_MISSING_EVIDENCE_REFS,
            BLOCK_FORBIDDEN_VALUE, BLOCK_CANDIDATE_HASH_MISMATCH,
            BLOCK_CANDIDATE_VALIDITY_MISMATCH, BLOCK_PAYLOAD_HASH_MISMATCH,
            BLOCK_BLOCKED_CANDIDATE, BLOCK_UNKNOWN_INTENT,
            BLOCK_UPSTREAM_OUTBOX_MUTATED, BLOCK_UPSTREAM_DISPATCH_OR_LIVE_FLAG_SET,
            BLOCK_DUPLICATE_FACT, BLOCK_DISPATCH_DISABLED,
            BLOCK_OUTBOX_MUTATION_DISABLED],
        "invariants": [
            "only_valid_0174ti_approval_candidate_records_approval_fact",
            "reject_candidate_records_reject_fact_only",
            "edit_request_candidate_records_edit_request_fact_only",
            "blocked_candidate_cannot_record_approval",
            "candidate_hash_mismatch_blocks_recording",
            "payload_hash_mismatch_blocks_recording",
            "missing_evidence_refs_blocks_recording",
            "duplicate_recording_fact_hash_suppressed_not_appended",
            "recorded_approval_never_authorizes_dispatch",
            "outbox_never_mutated",
            "artifact_writer_touches_only_docs_automation_0174TJ"],
        "safety_flags": dict(SAFETY_FLAGS),
        "next_required_gate": NEXT_REQUIRED_GATE,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
    }
    packet["checksum_sha256"] = compute_checksum(packet)
    return packet


def build_doc():
    flags = "\n".join(
        f"- `{key}` = `{str(value).lower()}`"
        for key, value in sorted(SAFETY_FLAGS.items()))
    fact_classes = "\n".join(f"- `{value}`" for value in [
        FACT_APPROVAL_RECORDED, FACT_REJECT_RECORDED,
        FACT_EDIT_REQUEST_RECORDED, FACT_RECORDING_BLOCKED,
        FACT_DUPLICATE_SUPPRESSED])
    return (
        "# 0174TJ Approval Ledger Candidate Recording Contract\n\n"
        "Local deterministic gate from 0174TI candidate to append-only ledger "
        "recording fact. The fact is local evidence only and never authorizes "
        "dispatch, mutates outbox state, calls Telegram, reads env, hydrates "
        "credentials, calls providers, or performs network behavior.\n\n"
        "## Fact Classes\n\n"
        f"{fact_classes}\n\n"
        "## Hash Rules\n\n"
        "Recording fact hash is sha256 over candidate id/hash, source review "
        "ids, approval challenge id, outbox id, exact payload hash, platform, "
        "destination binding, operator ref, fact class, scope, expiration "
        "proof, and evidence refs.\n\n"
        "## Duplicate Rules\n\n"
        "Registry suppresses repeated recording fact hashes and returns "
        "`duplicate_ledger_fact_suppressed` without appending.\n\n"
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


