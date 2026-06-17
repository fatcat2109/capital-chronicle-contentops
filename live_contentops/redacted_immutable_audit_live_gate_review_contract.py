# 0174TP/TQ/TR local-only contract write-loop marker; no live/API behavior.
"""Redacted immutable audit ledger + operator live-gate readiness review.

Tasks 0174TP (redacted immutable audit ledger), 0174TQ (operator live-gate
readiness review), and 0174TR (live-gate decision packet) -- one deterministic,
LOCAL authority batch on top of the accepted chain:

  * 0174EC: credential handle / redaction boundary.
  * 0174ED + R1: exact approval ledger + payload hash contract.
  * 0174EE + R1: dispatch outbox + idempotency + preflight contract.
  * 0174TG/TH/TI + R1: remote operator inbox + intent parser + review
    challenge contract, terminating in ``remote_review_approved_not_dispatched``.
  * 0174TJ/TK/TL + R2: editorial clear + multi-surface preview set + supervised
    dry run, terminating in ``supervised_dry_run_complete_not_dispatched``.
  * 0174TM/TN/TO + R1: kill switch + rate/spend/retry policy + one-request
    dispatch authorization candidate, with upstream safety flags revalidated
    before candidate creation.

Product role of this batch (all LOCAL, all deterministic):
  1. 0174TP appends a one-request dispatch gate result + candidate + redacted
     immutable dispatch audit into an APPEND-ONLY, redacted, checksum-chained
     audit ledger. Each entry carries the previous entry checksum, its own
     checksum, and a rolling chain digest. Duplicate ledger ids, candidate
     checksums, and idempotency fingerprints are suppressed. A ledger append is
     NOT dispatch and NOT live readiness.
  2. 0174TQ consumes the latest ledger entry + an integrity report + the gate
     result + candidate and produces a human-readable OperatorLiveGateReadiness
     Review. Default is FAIL-CLOSED/blocked. The only non-blocked outcome is
     ``evidence_ready_not_live``, which explicitly separates proven-local from
     not-live / not-executable / future-operator-owned work. It NEVER claims
     live readiness.
  3. 0174TR consumes an evidence-ready review + latest ledger entry + candidate
     and produces a LiveGateDecisionPacket FOR FUTURE operator-owned live work.
     It is explicitly NOT execution, NOT a provider/Telegram request. A registry
     appends only local packets and suppresses duplicates deterministically.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Pure Python stdlib only. No requests/httpx/aiohttp, no urllib request
    clients, no socket/ssl/http server, no selenium/playwright, no
    dotenv/keyring/sqlite, no openai/anthropic/telegram/tweepy SDKs.
  * NO network call of any kind.
  * NO env / keyring / browser-session / credential-file read.
  * NO OAuth, token exchange/refresh, credential hydration.
  * NO live posting, sendMessage, platform API call, dispatch, scheduler,
    retry loop, autonomous replies/DMs, scraping, or OpenClaw runtime.
  * Raw chat id / username / phone / token / bot token / webhook url / raw
    provider response / profile url are rejected or redacted by a fail-closed
    scanner and never persisted.
  * NO financial advice: buy/sell/hold calls, position sizing, guaranteed
    predictions, or trade-signal framing in audit text fail closed.
  * The audit ledger is append-only and redacted; its chain digest is the
    authority, not chat memory. The readiness review is evidence-ready, NOT
    live-ready. The decision packet is NOT execution. The candidate remains
    not live-executable. The operator-owned live gate remains a separate
    future task. Missing/stale/unsafe/ambiguous authority blocks (fail closed).

Importing this module performs NO writes and NO side effects. Artifacts are
written ONLY when ``write_artifacts(...)`` is called explicitly.
"""

import hashlib
import json
import os.path

# Upstream authority layers. This batch CONSUMES their outputs; it never
# bypasses them. The redaction + financial-advice scanners are reused as the
# single source of truth.
from live_contentops import supervised_dispatch_safety_gate_contract as gate

TASK_LABEL = (
    "TASK_CONTENTOPS_0174TP_TQ_TR_REDACTED_IMMUTABLE_AUDIT_AND_OPERATOR_LIVE_"
    "GATE_READINESS_REVIEW_BATCH_V0"
)
MODEL = "REDACTED_IMMUTABLE_AUDIT_LIVE_GATE_REVIEW_CONTRACT_0174TP_TQ_TR"
MODEL_VERSION = "0174TP_TQ_TR_AUDIT_LEDGER_LIVE_GATE_REVIEW_V1"

LEDGER_ENTRY_SCHEMA = "contentops.redacted_audit_ledger_entry"
LEDGER_ENTRY_SCHEMA_VERSION = "0174TP_REDACTED_AUDIT_LEDGER_ENTRY_V1"
LEDGER_INTEGRITY_SCHEMA = "contentops.audit_ledger_integrity_report"
LEDGER_INTEGRITY_SCHEMA_VERSION = "0174TP_AUDIT_LEDGER_INTEGRITY_REPORT_V1"
READINESS_REVIEW_SCHEMA = "contentops.operator_live_gate_readiness_review"
READINESS_REVIEW_SCHEMA_VERSION = "0174TQ_OPERATOR_LIVE_GATE_READINESS_REVIEW_V1"
DECISION_PACKET_SCHEMA = "contentops.live_gate_decision_packet"
DECISION_PACKET_SCHEMA_VERSION = "0174TR_LIVE_GATE_DECISION_PACKET_V1"

SOURCE_BASELINE_COMMIT = "f6c47c4db51162a7ad04a188909ed124455bdb04"

# Output artifact locations (written ONLY by the explicit write helper).
DOC_REL_DIR = os.path.join("docs", "automation", "0174TP_TQ_TR")
PACKET_FILENAME = "redacted_immutable_audit_live_gate_review_contract_packet.json"
DOC_FILENAME = "redacted_immutable_audit_live_gate_review_contract.md"

NEXT_REQUIRED_GATE = (
    "an operator-owned live-gate policy dry run + doc sync that still performs "
    "NO live dispatch; credential hydration and live platform/Telegram "
    "dispatch remain separate future operator-owned gates and are NOT enabled "
    "here"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174TS_TT_TU_OPERATOR_LIVE_GATE_POLICY_DRY_RUN_AND_DOC_"
    "SYNC_BATCH_V0"
)

# Genesis sentinel for the first ledger entry's previous-checksum link.
GENESIS_PREVIOUS_CHECKSUM = "GENESIS"


# --------------------------------------------------------------------------- #
# Status vocabularies (symbolic only)
# --------------------------------------------------------------------------- #
class Status:
    PASS = "pass"
    BLOCKED = "blocked"
    FAIL_CLOSED = "fail_closed"


# 0174TP audit ledger append outcome classes.
LEDGER_APPENDED = "redacted_audit_ledger_entry_appended_not_dispatch"
LEDGER_APPEND_BLOCKED = "redacted_audit_ledger_append_blocked"
LEDGER_APPEND_FAIL_CLOSED = "redacted_audit_ledger_append_fail_closed_forbidden_value"
LEDGER_DUPLICATE_ENTRY_ID = "duplicate_ledger_entry_id_suppressed"
LEDGER_DUPLICATE_CANDIDATE_CHECKSUM = "duplicate_candidate_checksum_suppressed"
LEDGER_DUPLICATE_FINGERPRINT = "duplicate_idempotency_fingerprint_suppressed"

# 0174TP audit ledger append blocked-reason classes.
BLOCK_LEDGER_FORBIDDEN_VALUE = "ledger_forbidden_value_detected"
BLOCK_LEDGER_FINANCIAL_ADVICE = "ledger_financial_advice_detected"
BLOCK_LEDGER_GATE_NOT_CANDIDATE_CREATED = "ledger_gate_result_not_candidate_created"
BLOCK_LEDGER_CANDIDATE_MISSING = "ledger_dispatch_authorization_candidate_missing"
BLOCK_LEDGER_AUDIT_MISSING = "ledger_redacted_immutable_dispatch_audit_missing"
BLOCK_LEDGER_CANDIDATE_CHECKSUM_MISSING = "ledger_candidate_checksum_missing"
BLOCK_LEDGER_AUDIT_CHECKSUM_MISSING = "ledger_audit_checksum_missing"
BLOCK_LEDGER_CANDIDATE_LIVE_EXECUTABLE = "ledger_candidate_claims_live_executable"
BLOCK_LEDGER_UPSTREAM_UNSAFE_BEHAVIOR = "ledger_upstream_unsafe_behavior_claimed"
BLOCK_LEDGER_OPERATOR_ID_MISSING = "ledger_operator_id_missing"
BLOCK_LEDGER_OPERATOR_ID_MISMATCH = "ledger_operator_id_mismatch"
BLOCK_LEDGER_ENTRY_ID_MISSING = "ledger_entry_id_missing"
BLOCK_LEDGER_POLICY_SNAPSHOT_MISSING = "ledger_policy_snapshot_id_missing"
BLOCK_LEDGER_REQUEST_ID_MISSING = "ledger_supervised_request_id_missing"

# 0174TP integrity-report classes.
INTEGRITY_PASS = "audit_ledger_chain_intact"
INTEGRITY_BROKEN = "audit_ledger_chain_broken"
INTEGRITY_EMPTY = "audit_ledger_empty"
BLOCK_INTEGRITY_BROKEN_PREVIOUS_LINK = "integrity_broken_previous_checksum_link"
BLOCK_INTEGRITY_ENTRY_CHECKSUM_MISMATCH = "integrity_entry_checksum_mismatch"
BLOCK_INTEGRITY_CHAIN_DIGEST_MISMATCH = "integrity_chain_digest_mismatch"

# 0174TQ readiness review outcome classes.
REVIEW_BLOCKED = "operator_live_gate_review_blocked"
REVIEW_EVIDENCE_READY = "operator_live_gate_review_evidence_ready_not_live"
REVIEW_FAIL_CLOSED = "operator_live_gate_review_fail_closed_forbidden_value"

# 0174TQ readiness review blocked-reason classes.
BLOCK_REVIEW_FORBIDDEN_VALUE = "review_forbidden_value_detected"
BLOCK_REVIEW_LEDGER_ENTRY_MISSING = "review_latest_ledger_entry_missing"
BLOCK_REVIEW_INTEGRITY_FAILED = "review_audit_ledger_integrity_failed"
BLOCK_REVIEW_CANDIDATE_MISSING = "review_dispatch_authorization_candidate_missing"
BLOCK_REVIEW_GATE_NOT_CANDIDATE_CREATED = "review_gate_result_not_candidate_created"
BLOCK_REVIEW_CANDIDATE_CHECKSUM_MISMATCH = "review_candidate_checksum_mismatch"
BLOCK_REVIEW_AUDIT_CHECKSUM_MISMATCH = "review_audit_checksum_mismatch"
BLOCK_REVIEW_STALE_POLICY_SNAPSHOT = "review_stale_policy_snapshot"
BLOCK_REVIEW_UNSAFE_BEHAVIOR = "review_unsafe_behavior_claimed"
BLOCK_REVIEW_OPERATOR_ID_MISSING = "review_operator_id_missing"
BLOCK_REVIEW_OPERATOR_ID_MISMATCH = "review_operator_id_mismatch"
BLOCK_REVIEW_REVIEW_ID_MISSING = "review_explicit_operator_review_id_missing"
# R1: per-input unsafe-behavior revalidation. Clear status / pass / intact
# metadata on an input artifact must NEVER hide a tampered flag claiming
# live/network/credential/dispatch behavior; the review re-derives the truth.
BLOCK_REVIEW_LEDGER_ENTRY_UNSAFE = (
    "readiness_review_ledger_entry_unsafe_behavior_claimed")
BLOCK_REVIEW_INTEGRITY_REPORT_UNSAFE = (
    "readiness_review_integrity_report_unsafe_behavior_claimed")
BLOCK_REVIEW_GATE_RESULT_UNSAFE = (
    "readiness_review_gate_result_unsafe_behavior_claimed")
BLOCK_REVIEW_CANDIDATE_UNSAFE = (
    "readiness_review_candidate_unsafe_behavior_claimed")

# 0174TR decision packet outcome classes.
DECISION_CREATED = "live_gate_decision_packet_created_not_executable"
DECISION_BLOCKED = "live_gate_decision_packet_blocked"
DECISION_FAIL_CLOSED = "live_gate_decision_packet_fail_closed_forbidden_value"
DECISION_DUPLICATE_PACKET_ID = "duplicate_decision_packet_id_suppressed"
DECISION_DUPLICATE_CANDIDATE_CHECKSUM = (
    "duplicate_decision_candidate_checksum_suppressed")

# 0174TR decision packet blocked-reason classes.
BLOCK_DECISION_FORBIDDEN_VALUE = "decision_forbidden_value_detected"
BLOCK_DECISION_REVIEW_NOT_EVIDENCE_READY = "decision_review_not_evidence_ready"
BLOCK_DECISION_REVIEW_CLAIMS_LIVE = "decision_review_claims_live_readiness"
BLOCK_DECISION_LEDGER_ENTRY_MISSING = "decision_latest_ledger_entry_missing"
BLOCK_DECISION_LEDGER_CHECKSUM_MISMATCH = "decision_ledger_entry_checksum_mismatch"
BLOCK_DECISION_CANDIDATE_MISSING = "decision_dispatch_authorization_candidate_missing"
BLOCK_DECISION_CANDIDATE_CHECKSUM_MISMATCH = "decision_candidate_checksum_mismatch"
BLOCK_DECISION_OPERATOR_ID_MISSING = "decision_operator_id_missing"
BLOCK_DECISION_OPERATOR_ID_MISMATCH = "decision_operator_id_mismatch"
BLOCK_DECISION_PACKET_ID_MISSING = "decision_packet_id_missing"
# R1: per-input unsafe-behavior revalidation for the decision packet.
BLOCK_DECISION_REVIEW_UNSAFE = (
    "decision_packet_review_unsafe_behavior_claimed")
BLOCK_DECISION_LEDGER_ENTRY_UNSAFE = (
    "decision_packet_ledger_entry_unsafe_behavior_claimed")
BLOCK_DECISION_CANDIDATE_UNSAFE = (
    "decision_packet_candidate_unsafe_behavior_claimed")

# Symbolic manual-checklist item ids (0174TQ). These are NOT approval and NOT
# live readiness; they are operator-facing reminders only.
MANUAL_CHECKLIST_ITEMS = (
    "human_operator_identity_confirmed",
    "policy_snapshot_reviewed",
    "kill_switch_reviewed",
    "rate_retry_policy_reviewed",
    "candidate_checksum_reviewed",
    "audit_checksum_reviewed",
    "platform_account_credential_remains_unhydrated",
    "provider_rendering_remains_unverified",
    "live_dispatch_remains_disabled",
)

# Identity fields threaded through ledger entry, review, and decision packet.
_BIND_FIELDS = (
    "supervised_request_id",
    "operator_id",
    "outbox_entry_id",
    "idempotency_fingerprint",
    "idempotency_key_short",
    "payload_hash_short",
    "approval_ledger_entry_id",
    "review_challenge_id",
    "editorial_id",
    "preview_set_id",
)


# --------------------------------------------------------------------------- #
# Redaction + financial-advice scanning + deterministic serialization.
# --------------------------------------------------------------------------- #
def scan_for_leaks(obj):
    """Return a sorted list of redaction violations (delegates to 0174ED)."""
    return gate.scan_for_leaks(obj)


def scan_for_financial_advice(obj):
    """Return a sorted list of financial-advice violations (delegates 0174TL)."""
    return gate.scan_for_financial_advice(obj)


def serialize(obj):
    """Deterministic JSON: sorted keys, stable separators, trailing newline."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization."""
    return hashlib.sha256(serialize(obj).encode("utf-8")).hexdigest()


def _safety_flags():
    """Hard-coded safety invariants attached to every 0174TP/TQ/TR object."""
    return {
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "telegram_api_called": False,
        "credential_hydrated": False,
        "llm_behavior": False,
        "network_performed": False,
        "scheduler_enabled": False,
        "auto_retry_allowed": False,
        "autonomous_reply_performed": False,
        "dispatch_ready": False,
        "live_ready": False,
        "no_financial_advice_emitted": True,
    }


def _candidate_is_live_executable(candidate):
    """True if a candidate claims any live-executable / readiness behavior.

    Only a flag that is PRESENT and truthy counts as a live claim. An absent
    flag (``.get`` -> ``None``) is treated as safe, so a well-formed candidate
    that simply omits ``live_ready`` / ``dispatch_ready`` is not false-blocked.
    """
    c = candidate or {}
    return bool(
        c.get("valid_for_live_execution")
        or c.get("candidate_is_live_readiness")
        or c.get("candidate_is_provider_authorization")
        or c.get("live_ready")
        or c.get("dispatch_ready")
    )


# Universal unsafe-behavior flags that MUST be False on every input artifact.
_UNSAFE_BEHAVIOR_FLAGS = (
    "dispatch_performed",
    "live_request_performed",
    "platform_api_called",
    "telegram_api_called",
    "credential_hydrated",
    "llm_behavior",
    "network_performed",
    "scheduler_enabled",
    "auto_retry_allowed",
    "autonomous_reply_performed",
    "dispatch_ready",
    "live_ready",
)

# Artifact-specific live/readiness booleans that MUST be False where present.
_UNSAFE_ARTIFACT_FLAGS = (
    "valid_for_live_execution",
    "ledger_append_is_dispatch",
    "ledger_append_is_live_readiness",
    "review_is_approval",
    "review_is_live_readiness",
    "decision_packet_is_execution",
    "decision_packet_is_provider_authorization",
    "decision_packet_is_live_readiness",
    "checklist_is_approval",
    "checklist_is_live_readiness",
)

# Artifact-name labels supported by detect_unsafe_behavior_claims in this module.
ARTIFACT_LEDGER_ENTRY = "ledger_entry"
ARTIFACT_LEDGER_INTEGRITY_REPORT = "ledger_integrity_report"
ARTIFACT_GATE_RESULT = "gate_result"
ARTIFACT_CANDIDATE = "dispatch_authorization_candidate"
ARTIFACT_READINESS_REVIEW = "readiness_review"
ARTIFACT_DECISION_PACKET = "decision_packet"


def detect_unsafe_behavior_claims(obj, artifact_name):
    """Return the unsafe flag names an input artifact claims (present + truthy).

    R1 hardening: a previously-"clear" / "pass" / "intact" input artifact (a
    ledger entry, integrity report, gate result, candidate, readiness review,
    or decision packet) must NOT be able to carry a tampered flag claiming
    live / network / credential / dispatch / readiness behavior past the
    readiness review or decision packet just because its status / pass /
    checksum / chain_intact metadata still reads clear. This helper re-derives
    the truth directly from the flags, ignoring that metadata entirely.

    A flag "claims" unsafe behavior when it is PRESENT and not False. An absent
    flag (``.get`` -> ``None``) is treated as safe. Returns a sorted, de-duped
    list of the tripped flag names (empty when the artifact claims nothing).
    ``artifact_name`` selects the audit label the CALLER attaches; the set of
    checked flags is the same across all supported artifact names. It also
    delegates to ``gate.detect_unsafe_behavior_claims`` so any upstream-only
    readiness flag (gate_is_*, dry_run_is_*, kill_switch_*, rate_*) is caught.
    """
    o = obj or {}
    hits = []
    for flag in (_UNSAFE_BEHAVIOR_FLAGS + _UNSAFE_ARTIFACT_FLAGS):
        if flag in o and o.get(flag) is not False:
            hits.append(flag)
    # Defense-in-depth: also surface any upstream-only readiness flag.
    for reason in gate.detect_unsafe_behavior_claims(o, str(artifact_name)):
        if ":" in reason:
            hits.append(reason.rsplit(":", 1)[1])
    return sorted(set(hits))


# --------------------------------------------------------------------------- #
# 0174TP: Redacted immutable audit ledger
# --------------------------------------------------------------------------- #
def build_redacted_audit_ledger_entry(gate_result, candidate, dispatch_audit, *,
                                      operator_id, ledger_entry_id,
                                      created_at_epoch, policy_snapshot_id,
                                      previous_entry_checksum, sequence_index,
                                      previous_chain_digest=None):
    """Build a deterministic, redacted RedactedAuditLedgerEntry (pure value).

    Stores symbolic ids and short hashes ONLY. The entry carries the previous
    entry checksum, its own ``entry_checksum`` (computed over the entry sans the
    checksum + chain digest), and a rolling ``chain_digest`` derived from the
    PREVIOUS chain digest and this entry's checksum. The rolling chain link --
    not the prior entry checksum -- is what the integrity report re-derives, so
    the two must use the same previous link. ``previous_chain_digest`` defaults
    to ``previous_entry_checksum`` only for a genesis entry where they coincide.
    """
    if previous_chain_digest is None:
        previous_chain_digest = previous_entry_checksum
    gr = gate_result or {}
    cand = candidate or {}
    audit = dispatch_audit or {}
    entry = {
        "ledger_entry_schema": LEDGER_ENTRY_SCHEMA,
        "ledger_entry_schema_version": LEDGER_ENTRY_SCHEMA_VERSION,
        "ledger_entry_id": ledger_entry_id,
        "sequence_index": sequence_index,
        "created_at_epoch": created_at_epoch,
        "previous_entry_checksum": previous_entry_checksum,
        "operator_id": operator_id,
        "policy_snapshot_id": policy_snapshot_id,
        # Deep-binding identity (symbolic ids + short hashes only).
        "supervised_request_id": gr.get("supervised_request_id"),
        "outbox_entry_id": gr.get("outbox_entry_id"),
        "idempotency_fingerprint": gr.get("idempotency_fingerprint"),
        "idempotency_key_short": gr.get("idempotency_key_short"),
        "payload_hash_short": gr.get("payload_hash_short"),
        "approval_ledger_entry_id": gr.get("approval_ledger_entry_id"),
        "review_challenge_id": gr.get("review_challenge_id"),
        "editorial_id": gr.get("editorial_id"),
        "preview_set_id": gr.get("preview_set_id"),
        "kill_switch_policy_snapshot_id":
            audit.get("kill_switch_policy_snapshot_id"),
        "rate_policy_snapshot_id": audit.get("rate_policy_snapshot_id"),
        "candidate_checksum": cand.get("candidate_checksum"),
        "audit_checksum": audit.get("audit_checksum"),
        "dispatch_gate_outcome_class": gr.get("dispatch_gate_outcome_class"),
        # Hard invariants -- a ledger entry is NEVER dispatch / live readiness.
        **_safety_flags(),
        "ledger_append_is_dispatch": False,
        "ledger_append_is_live_readiness": False,
        "requires_operator_live_gate": True,
        "valid_for_live_execution": False,
        "no_raw_credential_stored": True,
        "no_raw_provider_or_platform_response_stored": True,
        "no_chat_id_or_username_stored": True,
        "no_webhook_url_stored": True,
        "no_request_headers_or_cookies_stored": True,
    }
    entry["entry_checksum"] = compute_checksum(entry)
    entry["chain_digest"] = _chain_digest(previous_chain_digest,
                                          entry["entry_checksum"])
    return entry


def _chain_digest(previous_chain_or_checksum, entry_checksum):
    """Rolling chain digest = sha256(previous_link || entry_checksum)."""
    keyed = {
        "previous": previous_chain_or_checksum,
        "entry_checksum": entry_checksum,
    }
    return hashlib.sha256(serialize(keyed).encode("utf-8")).hexdigest()


def _recompute_entry_checksum(entry):
    """Recompute the entry_checksum exactly as build_... did (sans tail keys)."""
    e = dict(entry or {})
    e.pop("entry_checksum", None)
    e.pop("chain_digest", None)
    return compute_checksum(e)


class RedactedAuditLedger:
    """Append-only, redacted, checksum-chained audit ledger (LOCAL only).

    Suppresses duplicate ledger ids, candidate checksums, and idempotency
    fingerprints deterministically. Prior entries are never mutated. The ledger
    NEVER dispatches and NEVER hydrates credentials. The chain digest -- not
    chat memory -- is the authority.
    """

    def __init__(self):
        self._entries = []                 # append-only ledger entries
        self._by_entry_id = {}             # ledger_entry_id -> index
        self._by_candidate_checksum = {}   # candidate_checksum -> index
        self._by_fingerprint = {}          # idempotency_fingerprint -> index

    def _copy(self, obj):
        return json.loads(json.dumps(obj))

    @property
    def entries(self):
        return self._copy(self._entries)

    def entry_count(self):
        return len(self._entries)

    def latest_entry(self):
        if not self._entries:
            return None
        return self._copy(self._entries[-1])

    def _last_chain_link(self):
        if not self._entries:
            return GENESIS_PREVIOUS_CHECKSUM
        return self._entries[-1]["chain_digest"]

    def _last_entry_checksum(self):
        if not self._entries:
            return GENESIS_PREVIOUS_CHECKSUM
        return self._entries[-1]["entry_checksum"]

    def append(self, gate_result, candidate, dispatch_audit, *, operator_id,
               ledger_entry_id, created_at_epoch, policy_snapshot_id):
        """Append a redacted ledger entry, or block / suppress a duplicate.

        FAIL-CLOSED. Returns an AuditLedgerAppendResult. The ledger is mutated
        ONLY on a clean, non-duplicate append.
        """
        gr = gate_result or {}
        cand = candidate or {}
        audit = dispatch_audit or {}
        blocked = []

        # 1. Fail-closed redaction scan FIRST across all inputs.
        if scan_for_leaks([gr, cand, audit, {
                "operator_id": operator_id,
                "ledger_entry_id": ledger_entry_id,
                "policy_snapshot_id": policy_snapshot_id,
        }]):
            return self._append_result(
                LEDGER_APPEND_FAIL_CLOSED, blocked=[BLOCK_LEDGER_FORBIDDEN_VALUE],
                appended=False, forbidden_detected=True, financial_advice=False,
                entry=None, ledger_entry_id=ledger_entry_id)
        # 2. Hard content-safety gate: no financial advice anywhere.
        if scan_for_financial_advice([gr, cand, audit]):
            return self._append_result(
                LEDGER_APPEND_FAIL_CLOSED,
                blocked=[BLOCK_LEDGER_FINANCIAL_ADVICE], appended=False,
                forbidden_detected=False, financial_advice=True, entry=None,
                ledger_entry_id=ledger_entry_id)

        # 3. The gate result must be an actual candidate-created outcome.
        if gr.get("dispatch_gate_outcome_class") != gate.GATE_CANDIDATE_CREATED:
            blocked.append(BLOCK_LEDGER_GATE_NOT_CANDIDATE_CREATED)
        # 4. Candidate + audit must be present with checksums.
        if not cand:
            blocked.append(BLOCK_LEDGER_CANDIDATE_MISSING)
        elif not cand.get("candidate_checksum"):
            blocked.append(BLOCK_LEDGER_CANDIDATE_CHECKSUM_MISSING)
        if not audit:
            blocked.append(BLOCK_LEDGER_AUDIT_MISSING)
        elif not audit.get("audit_checksum"):
            blocked.append(BLOCK_LEDGER_AUDIT_CHECKSUM_MISSING)

        # 5. The candidate must NOT claim live-executable behavior.
        if _candidate_is_live_executable(cand):
            blocked.append(BLOCK_LEDGER_CANDIDATE_LIVE_EXECUTABLE)
        # 6. No upstream artifact may claim unsafe behavior.
        for art_name, art in (("dry_run", gr), ("candidate", cand),
                              ("audit", audit)):
            if gate.detect_unsafe_behavior_claims(art, art_name):
                blocked.append(BLOCK_LEDGER_UPSTREAM_UNSAFE_BEHAVIOR
                               + ":" + art_name)

        # 7. Required identity fields.
        if not operator_id:
            blocked.append(BLOCK_LEDGER_OPERATOR_ID_MISSING)
        elif gr.get("operator_id") and gr.get("operator_id") != operator_id:
            blocked.append(BLOCK_LEDGER_OPERATOR_ID_MISMATCH)
        if not ledger_entry_id:
            blocked.append(BLOCK_LEDGER_ENTRY_ID_MISSING)
        if not policy_snapshot_id:
            blocked.append(BLOCK_LEDGER_POLICY_SNAPSHOT_MISSING)
        if not gr.get("supervised_request_id"):
            blocked.append(BLOCK_LEDGER_REQUEST_ID_MISSING)

        if blocked:
            return self._append_result(
                LEDGER_APPEND_BLOCKED, blocked=sorted(set(blocked)),
                appended=False, forbidden_detected=False,
                financial_advice=False, entry=None,
                ledger_entry_id=ledger_entry_id)

        # 8. Duplicate suppression (id, candidate checksum, fingerprint).
        if ledger_entry_id in self._by_entry_id:
            return self._duplicate_result(
                LEDGER_DUPLICATE_ENTRY_ID, ledger_entry_id,
                self._entries[self._by_entry_id[ledger_entry_id]])
        candidate_checksum = cand.get("candidate_checksum")
        if candidate_checksum in self._by_candidate_checksum:
            return self._duplicate_result(
                LEDGER_DUPLICATE_CANDIDATE_CHECKSUM, ledger_entry_id,
                self._entries[self._by_candidate_checksum[candidate_checksum]])
        fingerprint = gr.get("idempotency_fingerprint")
        if fingerprint and fingerprint in self._by_fingerprint:
            return self._duplicate_result(
                LEDGER_DUPLICATE_FINGERPRINT, ledger_entry_id,
                self._entries[self._by_fingerprint[fingerprint]])

        # 9. Build + append. Prior entries are never mutated.
        entry = build_redacted_audit_ledger_entry(
            gr, cand, audit, operator_id=operator_id,
            ledger_entry_id=ledger_entry_id, created_at_epoch=created_at_epoch,
            policy_snapshot_id=policy_snapshot_id,
            previous_entry_checksum=self._last_entry_checksum(),
            previous_chain_digest=self._last_chain_link(),
            sequence_index=len(self._entries))
        index = len(self._entries)
        self._entries.append(self._copy(entry))
        self._by_entry_id[ledger_entry_id] = index
        self._by_candidate_checksum[candidate_checksum] = index
        if fingerprint:
            self._by_fingerprint[fingerprint] = index
        return self._append_result(
            LEDGER_APPENDED, blocked=[], appended=True,
            forbidden_detected=False, financial_advice=False,
            entry=self._copy(entry), ledger_entry_id=ledger_entry_id)

    def _append_result(self, outcome_class, *, blocked, appended,
                       forbidden_detected, financial_advice, entry,
                       ledger_entry_id):
        status = (Status.PASS if appended
                  else (Status.FAIL_CLOSED
                        if (forbidden_detected or financial_advice)
                        else Status.BLOCKED))
        result = {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": status,
            "ledger_append_outcome_class": outcome_class,
            "appended": appended,
            "duplicate_suppressed": False,
            "ledger_entry_id": ledger_entry_id,
            "blocked_reasons": blocked,
            "forbidden_fields_detected": forbidden_detected,
            "financial_advice_detected": financial_advice,
            "ledger_entry": entry,
            "entry_checksum": (entry or {}).get("entry_checksum"),
            "chain_digest": (entry or {}).get("chain_digest"),
            "entry_count": len(self._entries),
            **_safety_flags(),
            "ledger_append_is_dispatch": False,
            "ledger_append_is_live_readiness": False,
        }
        result["append_result_checksum"] = compute_checksum(result)
        return result

    def _duplicate_result(self, outcome_class, ledger_entry_id, existing):
        result = {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": Status.PASS,
            "ledger_append_outcome_class": outcome_class,
            "appended": False,
            "duplicate_suppressed": True,
            "ledger_entry_id": ledger_entry_id,
            "blocked_reasons": [],
            "forbidden_fields_detected": False,
            "financial_advice_detected": False,
            "ledger_entry": None,
            "existing_entry_checksum": existing.get("entry_checksum"),
            "existing_chain_digest": existing.get("chain_digest"),
            "entry_count": len(self._entries),
            **_safety_flags(),
            "ledger_append_is_dispatch": False,
            "ledger_append_is_live_readiness": False,
        }
        result["append_result_checksum"] = compute_checksum(result)
        return result

    def build_integrity_report(self):
        """Verify the full chain and return an AuditLedgerIntegrityReport."""
        return build_audit_ledger_integrity_report(self._entries)


def build_audit_ledger_integrity_report(entries):
    """Re-derive every checksum + chain link and report chain integrity.

    Deterministic, pure value. Detects a broken previous-checksum link, a
    tampered entry checksum, and a chain-digest mismatch. An empty ledger is
    reported as ``audit_ledger_empty`` (intact=False).
    """
    entries = entries or []
    blocked = []
    if not entries:
        report = {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "ledger_integrity_schema": LEDGER_INTEGRITY_SCHEMA,
            "ledger_integrity_schema_version": LEDGER_INTEGRITY_SCHEMA_VERSION,
            "status": Status.BLOCKED,
            "integrity_outcome_class": INTEGRITY_EMPTY,
            "chain_intact": False,
            "entry_count": 0,
            "blocked_reasons": [],
            "latest_entry_checksum": None,
            "latest_chain_digest": None,
            **_safety_flags(),
        }
        report["integrity_report_checksum"] = compute_checksum(report)
        return report

    previous_entry_checksum = GENESIS_PREVIOUS_CHECKSUM
    previous_chain_link = GENESIS_PREVIOUS_CHECKSUM
    for idx, entry in enumerate(entries):
        # Previous-checksum link must match the prior entry's checksum.
        if entry.get("previous_entry_checksum") != previous_entry_checksum:
            blocked.append(BLOCK_INTEGRITY_BROKEN_PREVIOUS_LINK
                           + ":" + str(idx))
        # The stored entry_checksum must match a fresh recomputation.
        recomputed = _recompute_entry_checksum(entry)
        if entry.get("entry_checksum") != recomputed:
            blocked.append(BLOCK_INTEGRITY_ENTRY_CHECKSUM_MISMATCH
                           + ":" + str(idx))
        # The chain digest must match the rolling derivation.
        expected_digest = _chain_digest(previous_chain_link,
                                        entry.get("entry_checksum"))
        if entry.get("chain_digest") != expected_digest:
            blocked.append(BLOCK_INTEGRITY_CHAIN_DIGEST_MISMATCH
                           + ":" + str(idx))
        previous_entry_checksum = entry.get("entry_checksum")
        previous_chain_link = entry.get("chain_digest")

    intact = not blocked
    report = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "ledger_integrity_schema": LEDGER_INTEGRITY_SCHEMA,
        "ledger_integrity_schema_version": LEDGER_INTEGRITY_SCHEMA_VERSION,
        "status": Status.PASS if intact else Status.BLOCKED,
        "integrity_outcome_class": INTEGRITY_PASS if intact else INTEGRITY_BROKEN,
        "chain_intact": intact,
        "entry_count": len(entries),
        "blocked_reasons": sorted(set(blocked)),
        "latest_entry_checksum": entries[-1].get("entry_checksum"),
        "latest_chain_digest": entries[-1].get("chain_digest"),
        **_safety_flags(),
    }
    report["integrity_report_checksum"] = compute_checksum(report)
    return report


# --------------------------------------------------------------------------- #
# 0174TQ: Operator live-gate readiness review
# --------------------------------------------------------------------------- #
def build_live_gate_manual_checklist():
    """Build the symbolic LiveGateManualChecklist (NOT approval, NOT live)."""
    checklist = {
        "checklist_kind": "live_gate_manual_checklist",
        "items": [
            {"item_id": item, "item_state": "operator_action_required",
             "checked": False}
            for item in MANUAL_CHECKLIST_ITEMS
        ],
        "checklist_is_approval": False,
        "checklist_is_live_readiness": False,
    }
    checklist["checklist_checksum"] = compute_checksum(checklist)
    return checklist


def run_operator_live_gate_readiness_review(
        latest_ledger_entry, integrity_report, gate_result, candidate, *,
        operator_id, current_policy_snapshot_id, operator_review_id):
    """Produce a deterministic OperatorLiveGateReadinessReview. FAIL-CLOSED.

    Default is blocked. The ONLY non-blocked outcome is ``evidence_ready_not_
    live``, and only when ALL hold:

      * no forbidden / financial-advice material;
      * a latest ledger entry exists and the integrity report is intact;
      * the gate result is candidate-created and the candidate is present;
      * candidate + audit checksums agree with the ledger entry;
      * the policy snapshot is fresh (matches ``current_policy_snapshot_id``);
      * no upstream artifact claims unsafe behavior;
      * operator id agrees and an explicit operator review id is present.

    Even when evidence-ready, the review is NEVER live-ready: ``live_ready`` and
    ``valid_for_live_execution`` are always False.
    """
    entry = latest_ledger_entry or {}
    report = integrity_report or {}
    gr = gate_result or {}
    cand = candidate or {}
    blocked = []

    # 1. Fail-closed redaction scan FIRST.
    if scan_for_leaks([entry, report, gr, cand, {
            "operator_id": operator_id,
            "current_policy_snapshot_id": current_policy_snapshot_id,
            "operator_review_id": operator_review_id,
    }]):
        return _review_result(
            REVIEW_FAIL_CLOSED, blocked=[BLOCK_REVIEW_FORBIDDEN_VALUE],
            evidence_ready=False, forbidden_detected=True, entry=entry,
            candidate=cand, operator_review_id=operator_review_id,
            operator_id=operator_id)

    # 2. A latest ledger entry must exist.
    if not entry:
        blocked.append(BLOCK_REVIEW_LEDGER_ENTRY_MISSING)
    # 3. The integrity report must be intact.
    if report.get("chain_intact") is not True:
        blocked.append(BLOCK_REVIEW_INTEGRITY_FAILED)
    # 4. The gate result must be candidate-created; candidate must be present.
    if gr.get("dispatch_gate_outcome_class") != gate.GATE_CANDIDATE_CREATED:
        blocked.append(BLOCK_REVIEW_GATE_NOT_CANDIDATE_CREATED)
    if not cand:
        blocked.append(BLOCK_REVIEW_CANDIDATE_MISSING)

    # 5. Candidate + audit checksums must agree with the ledger entry.
    if entry and cand and (
            entry.get("candidate_checksum") != cand.get("candidate_checksum")):
        blocked.append(BLOCK_REVIEW_CANDIDATE_CHECKSUM_MISMATCH)
    if entry and gr and entry.get("audit_checksum") is not None and (
            gr.get("idempotency_fingerprint")
            != entry.get("idempotency_fingerprint")):
        # Fingerprint binds the gate result to the ledger entry's audit.
        blocked.append(BLOCK_REVIEW_AUDIT_CHECKSUM_MISMATCH)

    # 6. The policy snapshot must be fresh.
    if entry and current_policy_snapshot_id is not None and (
            entry.get("policy_snapshot_id") != current_policy_snapshot_id):
        blocked.append(BLOCK_REVIEW_STALE_POLICY_SNAPSHOT)

    # 7. No input artifact may claim unsafe behavior, even if its status /
    #    pass / intact / checksum metadata still reads clear. The truth is
    #    re-derived directly from the flags on each input.
    for base, art_name, art in (
            (BLOCK_REVIEW_LEDGER_ENTRY_UNSAFE, ARTIFACT_LEDGER_ENTRY, entry),
            (BLOCK_REVIEW_INTEGRITY_REPORT_UNSAFE,
             ARTIFACT_LEDGER_INTEGRITY_REPORT, report),
            (BLOCK_REVIEW_GATE_RESULT_UNSAFE, ARTIFACT_GATE_RESULT, gr),
            (BLOCK_REVIEW_CANDIDATE_UNSAFE, ARTIFACT_CANDIDATE, cand)):
        unsafe = detect_unsafe_behavior_claims(art, art_name)
        if unsafe:
            blocked.append(base)
            blocked.extend(base + ":" + flag for flag in unsafe)

    # 8. Operator id agreement + explicit review id.
    if not operator_id:
        blocked.append(BLOCK_REVIEW_OPERATOR_ID_MISSING)
    elif entry and entry.get("operator_id") and (
            entry.get("operator_id") != operator_id):
        blocked.append(BLOCK_REVIEW_OPERATOR_ID_MISMATCH)
    if not operator_review_id:
        blocked.append(BLOCK_REVIEW_REVIEW_ID_MISSING)

    evidence_ready = not blocked
    outcome = REVIEW_EVIDENCE_READY if evidence_ready else REVIEW_BLOCKED
    return _review_result(
        outcome, blocked=sorted(set(blocked)), evidence_ready=evidence_ready,
        forbidden_detected=False, entry=entry, candidate=cand,
        operator_review_id=operator_review_id, operator_id=operator_id)


def _review_result(outcome_class, *, blocked, evidence_ready,
                   forbidden_detected, entry, candidate, operator_review_id,
                   operator_id):
    """Build a deterministic OperatorLiveGateReadinessReview (pure value)."""
    status = (Status.PASS if evidence_ready
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    e = entry or {}
    cand = candidate or {}
    # The evidence map separates proven-local from future-operator-owned work.
    evidence_map = {
        "local_deterministic_evidence_complete": evidence_ready,
        "live_execution_authorized": False,
        "credential_hydration_authorized": False,
        "provider_or_api_call_authorized": False,
        "telegram_or_platform_dispatch_authorized": False,
        "future_live_or_api_operator_gate_required": True,
    }
    blocker_stack = {
        "blocker_kind": "live_gate_blocker_stack",
        "blockers": blocked,
        "blocker_count": len(blocked),
        "live_dispatch_blocked": True,
    }
    review = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "readiness_review_schema": READINESS_REVIEW_SCHEMA,
        "readiness_review_schema_version": READINESS_REVIEW_SCHEMA_VERSION,
        "status": status,
        "readiness_outcome_class": outcome_class,
        "evidence_ready_not_live": evidence_ready,
        "operator_review_id": operator_review_id,
        "operator_id": operator_id,
        # Deep-binding identity re-asserted from the ledger entry.
        "ledger_entry_id": e.get("ledger_entry_id"),
        "entry_checksum": e.get("entry_checksum"),
        "chain_digest": e.get("chain_digest"),
        "supervised_request_id": e.get("supervised_request_id"),
        "outbox_entry_id": e.get("outbox_entry_id"),
        "idempotency_fingerprint": e.get("idempotency_fingerprint"),
        "payload_hash_short": e.get("payload_hash_short"),
        "approval_ledger_entry_id": e.get("approval_ledger_entry_id"),
        "review_challenge_id": e.get("review_challenge_id"),
        "editorial_id": e.get("editorial_id"),
        "preview_set_id": e.get("preview_set_id"),
        "candidate_checksum": cand.get("candidate_checksum"),
        "audit_checksum": e.get("audit_checksum"),
        "policy_snapshot_id": e.get("policy_snapshot_id"),
        "evidence_map": evidence_map,
        "blocker_stack": blocker_stack,
        "manual_checklist": build_live_gate_manual_checklist(),
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        # Hard invariants -- evidence-ready is NEVER live-ready.
        **_safety_flags(),
        "requires_future_operator_live_gate": True,
        "valid_for_live_execution": False,
        "not_executable": True,
        "review_is_approval": False,
        "review_is_live_readiness": False,
    }
    review["readiness_review_checksum"] = compute_checksum(review)
    return review


# --------------------------------------------------------------------------- #
# 0174TR: Live-gate decision packet
# --------------------------------------------------------------------------- #
def build_live_gate_decision_packet(readiness_review, latest_ledger_entry,
                                    candidate, *, operator_id,
                                    decision_packet_id):
    """Produce a deterministic LiveGateDecisionPacket or block. FAIL-CLOSED.

    Creates ONLY a local decision packet for FUTURE operator-owned live work.
    The ONLY created outcome is ``..._created_not_executable``, and only when:

      * no forbidden material;
      * the readiness review is ``evidence_ready_not_live`` and does NOT claim
        live readiness;
      * a latest ledger entry exists and its checksum agrees with the review;
      * the candidate is present and its checksum agrees with the ledger entry;
      * operator id agrees and an explicit decision packet id is present.

    Even when created, the packet is NEVER executable.
    """
    review = readiness_review or {}
    entry = latest_ledger_entry or {}
    cand = candidate or {}
    blocked = []

    # 1. Fail-closed redaction scan FIRST.
    if scan_for_leaks([review, entry, cand, {
            "operator_id": operator_id,
            "decision_packet_id": decision_packet_id,
    }]):
        return _decision_result(
            DECISION_FAIL_CLOSED, blocked=[BLOCK_DECISION_FORBIDDEN_VALUE],
            created=False, forbidden_detected=True, review=review, entry=entry,
            candidate=cand, operator_id=operator_id,
            decision_packet_id=decision_packet_id)

    # 2. The review must be evidence-ready and not claim live readiness.
    if review.get("readiness_outcome_class") != REVIEW_EVIDENCE_READY:
        blocked.append(BLOCK_DECISION_REVIEW_NOT_EVIDENCE_READY)
    if (review.get("valid_for_live_execution") is not False
            or review.get("live_ready") is not False
            or review.get("dispatch_ready") is not False
            or review.get("review_is_live_readiness") is not False):
        blocked.append(BLOCK_DECISION_REVIEW_CLAIMS_LIVE)

    # 3. A latest ledger entry must exist and agree with the review.
    if not entry:
        blocked.append(BLOCK_DECISION_LEDGER_ENTRY_MISSING)
    elif review.get("entry_checksum") and (
            review.get("entry_checksum") != entry.get("entry_checksum")):
        blocked.append(BLOCK_DECISION_LEDGER_CHECKSUM_MISMATCH)

    # 4. The candidate must be present and agree with the ledger entry.
    if not cand:
        blocked.append(BLOCK_DECISION_CANDIDATE_MISSING)
    elif entry and entry.get("candidate_checksum") != cand.get(
            "candidate_checksum"):
        blocked.append(BLOCK_DECISION_CANDIDATE_CHECKSUM_MISMATCH)

    # 4b. No input artifact may claim unsafe behavior, even if its outcome /
    #     checksum metadata still reads clear. The truth is re-derived directly
    #     from the flags on the review, ledger entry, and candidate.
    for base, art_name, art in (
            (BLOCK_DECISION_REVIEW_UNSAFE, ARTIFACT_READINESS_REVIEW, review),
            (BLOCK_DECISION_LEDGER_ENTRY_UNSAFE, ARTIFACT_LEDGER_ENTRY, entry),
            (BLOCK_DECISION_CANDIDATE_UNSAFE, ARTIFACT_CANDIDATE, cand)):
        unsafe = detect_unsafe_behavior_claims(art, art_name)
        if unsafe:
            blocked.append(base)
            blocked.extend(base + ":" + flag for flag in unsafe)

    # 5. Operator id agreement + explicit decision packet id.
    if not operator_id:
        blocked.append(BLOCK_DECISION_OPERATOR_ID_MISSING)
    elif entry and entry.get("operator_id") and (
            entry.get("operator_id") != operator_id):
        blocked.append(BLOCK_DECISION_OPERATOR_ID_MISMATCH)
    if not decision_packet_id:
        blocked.append(BLOCK_DECISION_PACKET_ID_MISSING)

    created = not blocked
    outcome = DECISION_CREATED if created else DECISION_BLOCKED
    return _decision_result(
        outcome, blocked=sorted(set(blocked)), created=created,
        forbidden_detected=False, review=review, entry=entry, candidate=cand,
        operator_id=operator_id, decision_packet_id=decision_packet_id)


def _decision_result(outcome_class, *, blocked, created, forbidden_detected,
                     review, entry, candidate, operator_id, decision_packet_id):
    """Build a deterministic LiveGateDecisionPacket (pure value)."""
    status = (Status.PASS if created
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    e = entry or {}
    cand = candidate or {}
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "decision_packet_schema": DECISION_PACKET_SCHEMA,
        "decision_packet_schema_version": DECISION_PACKET_SCHEMA_VERSION,
        "status": status,
        "decision_outcome_class": outcome_class,
        "decision_packet_created_not_executable": created,
        "decision_packet_id": decision_packet_id,
        "operator_id": operator_id,
        # Exact binding to the ledger entry + candidate.
        "ledger_entry_id": e.get("ledger_entry_id"),
        "ledger_entry_checksum": e.get("entry_checksum"),
        "chain_digest": e.get("chain_digest"),
        "supervised_request_id": e.get("supervised_request_id"),
        "candidate_checksum": cand.get("candidate_checksum"),
        "audit_checksum": e.get("audit_checksum"),
        "idempotency_fingerprint": e.get("idempotency_fingerprint"),
        "outbox_entry_id": e.get("outbox_entry_id"),
        "payload_hash_short": e.get("payload_hash_short"),
        "approval_ledger_entry_id": e.get("approval_ledger_entry_id"),
        "review_challenge_id": e.get("review_challenge_id"),
        "editorial_id": e.get("editorial_id"),
        "preview_set_id": e.get("preview_set_id"),
        "readiness_review_checksum": (review or {}).get(
            "readiness_review_checksum"),
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        # Hard invariants -- a decision packet is NEVER execution.
        **_safety_flags(),
        "requires_future_operator_live_gate": True,
        "valid_for_live_execution": False,
        "decision_packet_is_execution": False,
        "decision_packet_is_provider_authorization": False,
        "decision_packet_is_live_readiness": False,
    }
    packet["decision_packet_checksum"] = compute_checksum(packet)
    return packet


class LiveGateDecisionPacketRegistry:
    """Append-only registry of LOCAL live-gate decision packets.

    Suppresses duplicate decision packet ids AND duplicate candidate checksums
    deterministically. Nothing is mutated in place, and the registry NEVER
    dispatches and NEVER executes.
    """

    def __init__(self):
        self._packets = []                 # append-only decision packets
        self._by_packet_id = {}            # decision_packet_id -> index
        self._by_candidate_checksum = {}   # candidate_checksum -> index

    def _copy(self, obj):
        return json.loads(json.dumps(obj))

    @property
    def packets(self):
        return self._copy(self._packets)

    def packet_count(self):
        return len(self._packets)

    def submit(self, decision_packet):
        """Append a created decision packet, or suppress a duplicate.

        Raises ValueError when the packet was not created (fail-closed). On a
        fresh id + candidate checksum, appends and reports appended. On a
        duplicate id or candidate checksum, appends NOTHING.
        """
        dp = decision_packet or {}
        if dp.get("decision_outcome_class") != DECISION_CREATED:
            raise ValueError(
                "cannot submit: decision packet was not created")
        packet_id = dp.get("decision_packet_id")
        candidate_checksum = dp.get("candidate_checksum")
        if not packet_id:
            raise ValueError("cannot submit: missing decision packet id")
        if not candidate_checksum:
            raise ValueError("cannot submit: missing candidate checksum")

        if packet_id in self._by_packet_id:
            existing = self._packets[self._by_packet_id[packet_id]]
            return self._registry_result(
                DECISION_DUPLICATE_PACKET_ID, appended=False, packet_id=packet_id,
                candidate_checksum=candidate_checksum, packet=None,
                existing=existing)
        if candidate_checksum in self._by_candidate_checksum:
            existing = self._packets[
                self._by_candidate_checksum[candidate_checksum]]
            return self._registry_result(
                DECISION_DUPLICATE_CANDIDATE_CHECKSUM, appended=False,
                packet_id=packet_id, candidate_checksum=candidate_checksum,
                packet=None, existing=existing)

        index = len(self._packets)
        self._packets.append(self._copy(dp))
        self._by_packet_id[packet_id] = index
        self._by_candidate_checksum[candidate_checksum] = index
        return self._registry_result(
            DECISION_CREATED, appended=True, packet_id=packet_id,
            candidate_checksum=candidate_checksum, packet=self._copy(dp),
            existing=None)

    def _registry_result(self, outcome_class, *, appended, packet_id,
                         candidate_checksum, packet, existing):
        result = {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": Status.PASS,
            "registry_outcome_class": outcome_class,
            "appended": appended,
            "duplicate_suppressed": not appended,
            "decision_packet_id": packet_id,
            "candidate_checksum": candidate_checksum,
            "decision_packet": packet,
            "existing_decision_packet_checksum":
                (existing or {}).get("decision_packet_checksum"),
            "packet_count": len(self._packets),
            **_safety_flags(),
            "valid_for_live_execution": False,
            "requires_future_operator_live_gate": True,
        }
        result["registry_result_checksum"] = compute_checksum(result)
        return result


class LiveGateDecisionPacketIntegrityReport:
    """Re-verify a decision packet's binding against a ledger entry + candidate."""

    @staticmethod
    def verify(decision_packet, latest_ledger_entry, candidate):
        dp = decision_packet or {}
        e = latest_ledger_entry or {}
        cand = candidate or {}
        mismatches = []
        if dp.get("ledger_entry_checksum") != e.get("entry_checksum"):
            mismatches.append("ledger_entry_checksum")
        if dp.get("chain_digest") != e.get("chain_digest"):
            mismatches.append("chain_digest")
        if dp.get("candidate_checksum") != cand.get("candidate_checksum"):
            mismatches.append("candidate_checksum")
        if dp.get("idempotency_fingerprint") != e.get("idempotency_fingerprint"):
            mismatches.append("idempotency_fingerprint")
        intact = not mismatches
        report = {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": Status.PASS if intact else Status.BLOCKED,
            "binding_intact": intact,
            "mismatched_fields": sorted(set(mismatches)),
            "decision_packet_id": dp.get("decision_packet_id"),
            **_safety_flags(),
            "valid_for_live_execution": False,
        }
        report["integrity_report_checksum"] = compute_checksum(report)
        return report


# --------------------------------------------------------------------------- #
# Deterministic packet + doc builders + explicit artifact writer
# --------------------------------------------------------------------------- #
def build_packet():
    """Return a deterministic, redaction-clean contract packet (pure value)."""
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": Status.PASS,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "ledger_entry_schema": LEDGER_ENTRY_SCHEMA,
        "ledger_entry_schema_version": LEDGER_ENTRY_SCHEMA_VERSION,
        "ledger_integrity_schema": LEDGER_INTEGRITY_SCHEMA,
        "ledger_integrity_schema_version": LEDGER_INTEGRITY_SCHEMA_VERSION,
        "readiness_review_schema": READINESS_REVIEW_SCHEMA,
        "readiness_review_schema_version": READINESS_REVIEW_SCHEMA_VERSION,
        "decision_packet_schema": DECISION_PACKET_SCHEMA,
        "decision_packet_schema_version": DECISION_PACKET_SCHEMA_VERSION,
        "ledger_append_outcome_classes": [
            LEDGER_APPENDED,
            LEDGER_APPEND_BLOCKED,
            LEDGER_APPEND_FAIL_CLOSED,
            LEDGER_DUPLICATE_ENTRY_ID,
            LEDGER_DUPLICATE_CANDIDATE_CHECKSUM,
            LEDGER_DUPLICATE_FINGERPRINT,
        ],
        "integrity_outcome_classes": [
            INTEGRITY_PASS,
            INTEGRITY_BROKEN,
            INTEGRITY_EMPTY,
        ],
        "readiness_outcome_classes": [
            REVIEW_EVIDENCE_READY,
            REVIEW_BLOCKED,
            REVIEW_FAIL_CLOSED,
        ],
        "decision_outcome_classes": [
            DECISION_CREATED,
            DECISION_BLOCKED,
            DECISION_FAIL_CLOSED,
            DECISION_DUPLICATE_PACKET_ID,
            DECISION_DUPLICATE_CANDIDATE_CHECKSUM,
        ],
        "r1_revalidation_blocked_reasons": [
            BLOCK_REVIEW_LEDGER_ENTRY_UNSAFE,
            BLOCK_REVIEW_INTEGRITY_REPORT_UNSAFE,
            BLOCK_REVIEW_GATE_RESULT_UNSAFE,
            BLOCK_REVIEW_CANDIDATE_UNSAFE,
            BLOCK_DECISION_REVIEW_UNSAFE,
            BLOCK_DECISION_LEDGER_ENTRY_UNSAFE,
            BLOCK_DECISION_CANDIDATE_UNSAFE,
        ],
        "r1_revalidated_unsafe_flags": list(
            _UNSAFE_BEHAVIOR_FLAGS + _UNSAFE_ARTIFACT_FLAGS),
        "required_ledger_entry_fields": [
            "ledger_entry_id",
            "previous_entry_checksum",
            "entry_checksum",
            "chain_digest",
            "operator_id",
            "supervised_request_id",
            "outbox_entry_id",
            "idempotency_fingerprint",
            "idempotency_key_short",
            "payload_hash_short",
            "approval_ledger_entry_id",
            "review_challenge_id",
            "editorial_id",
            "preview_set_id",
            "kill_switch_policy_snapshot_id",
            "rate_policy_snapshot_id",
            "candidate_checksum",
            "audit_checksum",
        ],
        "manual_checklist_items": list(MANUAL_CHECKLIST_ITEMS),
        "bind_fields": list(_BIND_FIELDS),
        "hard_invariants": [
            "audit_ledger_is_append_only_and_redacted",
            "ledger_chain_digest_is_authority_not_chat_memory",
            "ledger_stores_symbolic_ids_and_short_hashes_only",
            "ledger_append_is_not_dispatch",
            "ledger_append_is_not_live_readiness",
            "readiness_review_is_evidence_ready_not_live_ready",
            "readiness_review_never_sets_valid_for_live_execution_true",
            "decision_packet_is_not_execution",
            "candidate_remains_not_live_executable",
            "future_operator_owned_live_gate_remains_separate",
            "manual_checklist_is_not_approval",
            "no_credential_hydration",
            "no_provider_or_platform_or_telegram_behavior",
            "no_scheduler_queue_or_retry_loop",
            "no_autonomous_posting",
            "no_financial_advice_or_signal_framing",
            "missing_stale_unsafe_or_ambiguous_authority_blocks",
            "readiness_review_revalidates_all_input_safety_flags",
            "decision_packet_revalidates_all_input_safety_flags",
            "integrity_report_clear_metadata_cannot_hide_unsafe_behavior",
            "candidate_checksum_match_cannot_hide_unsafe_behavior",
            "ledger_entry_checksum_match_cannot_hide_unsafe_behavior",
            "unsafe_input_artifact_blocks_review_or_decision",
        ],
        "next_required_gate": NEXT_REQUIRED_GATE,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
        "safety_flags": _safety_flags(),
    }
    packet["checksum_sha256"] = compute_checksum(packet)
    return packet


def build_doc():
    """Return a deterministic, redaction-clean markdown contract document."""
    packet = build_packet()
    checklist = "\n".join(f"  * `{item}`" for item in MANUAL_CHECKLIST_ITEMS)
    hard = "\n".join(f"  * `{inv}`" for inv in packet["hard_invariants"])
    fields = "\n".join(
        f"  * `{f}`" for f in packet["required_ledger_entry_fields"])
    return (
        f"# 0174TP/TQ/TR Redacted Immutable Audit Ledger + Live-Gate Review\n\n"
        f"Task: `{TASK_LABEL}`\n\n"
        f"Model: `{MODEL}` version `{MODEL_VERSION}`\n\n"
        f"Baseline commit: `{SOURCE_BASELINE_COMMIT}`\n\n"
        f"## Role\n\n"
        f"This batch is LOCAL and deterministic. It performs NO live platform "
        f"API call, NO Telegram send, NO LLM/provider call, NO network, NO "
        f"env/credential read, NO credential hydration, NO scheduler, and NO "
        f"auto retry. It NEVER dispatches and NEVER executes.\n\n"
        f"## 0174TP Redacted immutable audit ledger\n\n"
        f"Append-only, redacted, checksum-chained. Each entry carries a "
        f"`previous_entry_checksum`, its own `entry_checksum`, and a rolling "
        f"`chain_digest`. Duplicate ledger ids, candidate checksums, and "
        f"idempotency fingerprints are suppressed. Required entry fields:\n\n"
        f"{fields}\n\n"
        f"The chain digest is the authority, not chat memory. A ledger append "
        f"is NOT dispatch and NOT live readiness.\n\n"
        f"## 0174TQ Operator live-gate readiness review\n\n"
        f"Fail-closed by default. The only non-blocked outcome is "
        f"`{REVIEW_EVIDENCE_READY}`, which separates proven-local evidence "
        f"from not-live / not-executable / future-operator-owned work. It "
        f"NEVER sets `valid_for_live_execution=True` or `live_ready=True`. "
        f"Symbolic manual checklist (NOT approval):\n\n{checklist}\n\n"
        f"## 0174TR Live-gate decision packet\n\n"
        f"Requires an `{REVIEW_EVIDENCE_READY}` review, an intact ledger "
        f"binding, and an explicit decision packet id. It produces a local "
        f"`{DECISION_CREATED}` packet for FUTURE operator-owned live work that "
        f"is NEVER executable and always `requires_future_operator_live_gate`. "
        f"A registry suppresses duplicate decision packet ids and candidate "
        f"checksums.\n\n"
        f"## R1 input safety revalidation\n\n"
        f"Both the readiness review (0174TQ) and the decision packet (0174TR) "
        f"re-derive unsafe behavior directly from the flags on EVERY input "
        f"artifact -- the ledger entry, the integrity report, the gate result, "
        f"the candidate, and the readiness review -- ignoring clear `status`, "
        f"`pass`, `chain_intact`, and matching checksum metadata. A tampered "
        f"input that keeps a valid checksum or an intact-chain report while "
        f"claiming `network_performed=True`, `platform_api_called=True`, "
        f"`live_ready=True`, `credential_hydrated=True`, or any readiness flag "
        f"is BLOCKED. Blocked reasons identify the artifact class and the "
        f"specific flag (`<artifact>_unsafe_behavior_claimed:<flag>`).\n\n"
        f"## Hard invariants\n\n{hard}\n\n"
        f"## Next required gate\n\n{NEXT_REQUIRED_GATE}\n\n"
        f"Exact next task: `{EXACT_NEXT_TASK_RECOMMENDATION}`\n\n"
        f"Packet checksum: `{packet['checksum_sha256']}`\n")


def write_artifacts(base_dir):
    """Write the packet JSON + markdown doc under ``base_dir``. Explicit only.

    Returns the list of written absolute paths. This is the ONLY function that
    performs filesystem writes; importing the module performs none.
    """
    out_dir = os.path.join(base_dir, DOC_REL_DIR)
    os.makedirs(out_dir, exist_ok=True)
    packet_path = os.path.join(out_dir, PACKET_FILENAME)
    doc_path = os.path.join(out_dir, DOC_FILENAME)
    with open(packet_path, "w", encoding="utf-8") as fh:
        fh.write(serialize(build_packet()))
    with open(doc_path, "w", encoding="utf-8") as fh:
        fh.write(build_doc())
    return [packet_path, doc_path]
