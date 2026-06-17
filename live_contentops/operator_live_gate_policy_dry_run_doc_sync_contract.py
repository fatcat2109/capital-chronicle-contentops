# 0174TS/TT/TU local-only contract write-loop marker; no live/API behavior.
"""Operator live-gate policy dry-run + checklist packet + doc/state sync.

Tasks 0174TS (operator live-gate policy dry-run), 0174TT (live-gate operator
checklist packet), and 0174TU (documentation/state sync packet) -- one
deterministic, LOCAL authority batch on top of the accepted chain:

  * 0174EC: credential handle / redaction boundary.
  * 0174ED + R1: exact approval ledger + payload hash contract.
  * 0174EE + R1: dispatch outbox + idempotency + preflight contract.
  * 0174TG/TH/TI + R1: remote operator inbox + intent parser + review
    challenge contract, terminating in ``remote_review_approved_not_dispatched``.
  * 0174TJ/TK/TL + R2: editorial clear + multi-surface preview set + supervised
    dry run, terminating in ``supervised_dry_run_complete_not_dispatched``.
  * 0174TM/TN/TO + R1: kill switch + rate/spend/retry policy + one-request
    dispatch authorization candidate, with upstream safety flags revalidated.
  * 0174TP/TQ/TR + R1: redacted immutable audit ledger + evidence-ready-not-live
    review + not-executable decision packet, with readiness and decision input
    safety flags revalidated.

Product role of this batch (all LOCAL, all deterministic):
  1. 0174TS consumes a 0174TR live-gate decision packet + the latest redacted
     audit ledger entry and produces an OperatorLiveGatePolicyDryRun. Default is
     FAIL-CLOSED/blocked. The only non-blocked outcome is
     ``operator_live_gate_policy_dry_run_complete_not_live``. It proves the
     project remains not-live, enumerates every remaining future live gate as
     UNRESOLVED / not-run / not-authorized, and NEVER clears them. It NEVER sets
     ``live_ready`` or ``valid_for_live_execution`` true. It revalidates unsafe
     flags on all input artifacts.
  2. 0174TT consumes a complete policy dry-run + decision packet + ledger entry
     and produces an OperatorLiveGateChecklistPacket. The checklist is NOT
     approval and NOT live readiness; every item defaults to
     ``operator_action_required`` and ``checked=False`` and cannot be marked
     complete automatically. A registry appends only local packets and
     suppresses duplicate checklist packet ids and duplicate decision packet ids.
  3. 0174TU consumes a checklist packet + policy dry-run + decision packet +
     ledger entry and produces a LocalDocumentationStateSyncPacket plus a
     NextTaskHandoffPacket. It records what remains blocked, names the exact
     next recommended task, and states the accepted baseline candidate is for
     HUMAN audit only (never self-accepted). It modifies NO current-state docs.

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
    predictions, or trade-signal framing fail closed.
  * The policy dry-run is NOT live policy approval. The checklist packet is NOT
    operator approval. The documentation sync is NOT readiness. Future live/API
    work remains blocked. Missing/stale/unsafe/ambiguous authority blocks.

Importing this module performs NO writes and NO side effects. Artifacts are
written ONLY when ``write_artifacts(...)`` is called explicitly.
"""

import hashlib
import json
import os.path

# Upstream authority layers. This batch CONSUMES their outputs; it never
# bypasses them. The redaction + financial-advice scanners and the unsafe-flag
# revalidator are reused as the single source of truth.
from live_contentops import redacted_immutable_audit_live_gate_review_contract as al

TASK_LABEL = (
    "TASK_CONTENTOPS_0174TS_TT_TU_OPERATOR_LIVE_GATE_POLICY_DRY_RUN_AND_DOC_"
    "SYNC_BATCH_V0"
)
MODEL = "OPERATOR_LIVE_GATE_POLICY_DRY_RUN_DOC_SYNC_CONTRACT_0174TS_TT_TU"
MODEL_VERSION = "0174TS_TT_TU_POLICY_DRY_RUN_CHECKLIST_DOC_SYNC_V1"

POLICY_SNAPSHOT_SCHEMA = "contentops.operator_live_gate_policy_snapshot"
POLICY_SNAPSHOT_SCHEMA_VERSION = "0174TS_OPERATOR_LIVE_GATE_POLICY_SNAPSHOT_V1"
POLICY_DRY_RUN_SCHEMA = "contentops.operator_live_gate_policy_dry_run"
POLICY_DRY_RUN_SCHEMA_VERSION = "0174TS_OPERATOR_LIVE_GATE_POLICY_DRY_RUN_V1"
POLICY_DRY_RUN_INTEGRITY_SCHEMA = (
    "contentops.operator_live_gate_policy_dry_run_integrity_report")
POLICY_DRY_RUN_INTEGRITY_SCHEMA_VERSION = (
    "0174TS_OPERATOR_LIVE_GATE_POLICY_DRY_RUN_INTEGRITY_REPORT_V1")
CHECKLIST_PACKET_SCHEMA = "contentops.operator_live_gate_checklist_packet"
CHECKLIST_PACKET_SCHEMA_VERSION = "0174TT_OPERATOR_LIVE_GATE_CHECKLIST_PACKET_V1"
DOC_SYNC_PACKET_SCHEMA = "contentops.local_documentation_state_sync_packet"
DOC_SYNC_PACKET_SCHEMA_VERSION = "0174TU_LOCAL_DOCUMENTATION_STATE_SYNC_PACKET_V1"
DOC_SYNC_INTEGRITY_SCHEMA = "contentops.documentation_sync_integrity_report"
DOC_SYNC_INTEGRITY_SCHEMA_VERSION = (
    "0174TU_DOCUMENTATION_SYNC_INTEGRITY_REPORT_V1")
HANDOFF_PACKET_SCHEMA = "contentops.next_task_handoff_packet"
HANDOFF_PACKET_SCHEMA_VERSION = "0174TU_NEXT_TASK_HANDOFF_PACKET_V1"

SOURCE_BASELINE_COMMIT = "775b931e568fa8fe4b6a5834c714f15a8bf05cec"

# Output artifact locations (written ONLY by the explicit write helper).
DOC_REL_DIR = os.path.join("docs", "automation", "0174TS_TT_TU")
PACKET_FILENAME = "operator_live_gate_policy_dry_run_doc_sync_contract_packet.json"
DOC_FILENAME = "operator_live_gate_policy_dry_run_doc_sync_contract.md"

# The exact next recommended task. The live gate remains a FUTURE operator-owned
# task; this batch never authorizes it.
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174TV_TW_TX_OFFICIAL_PROVIDER_DOC_REVIEW_AND_LIVE_GATE_"
    "DESIGN_BATCH_V0"
)


# --------------------------------------------------------------------------- #
# Status vocabularies (symbolic only)
# --------------------------------------------------------------------------- #
class Status:
    PASS = "pass"
    BLOCKED = "blocked"
    FAIL_CLOSED = "fail_closed"


# 0174TS policy dry-run outcome classes.
POLICY_DRY_RUN_COMPLETE = "operator_live_gate_policy_dry_run_complete_not_live"
POLICY_DRY_RUN_BLOCKED = "operator_live_gate_policy_dry_run_blocked"
POLICY_DRY_RUN_FAIL_CLOSED = (
    "operator_live_gate_policy_dry_run_fail_closed_forbidden_value")

# 0174TS policy dry-run blocked-reason classes.
BLOCK_DRY_RUN_FORBIDDEN_VALUE = "policy_dry_run_forbidden_value_detected"
BLOCK_DRY_RUN_FINANCIAL_ADVICE = "policy_dry_run_financial_advice_detected"
BLOCK_DRY_RUN_DECISION_PACKET_MISSING = "policy_dry_run_decision_packet_missing"
BLOCK_DRY_RUN_DECISION_NOT_CREATED = "policy_dry_run_decision_packet_not_created"
BLOCK_DRY_RUN_DECISION_VALID_FOR_LIVE = (
    "policy_dry_run_decision_packet_valid_for_live_execution")
BLOCK_DRY_RUN_NO_FUTURE_GATE_REQUIRED = (
    "policy_dry_run_decision_packet_requires_future_operator_live_gate_false")
BLOCK_DRY_RUN_LEDGER_ENTRY_MISSING = "policy_dry_run_latest_ledger_entry_missing"
BLOCK_DRY_RUN_LEDGER_CHECKSUM_MISMATCH = "policy_dry_run_ledger_checksum_mismatch"
BLOCK_DRY_RUN_BINDING_MISMATCH = "policy_dry_run_binding_mismatch"
BLOCK_DRY_RUN_OPERATOR_ID_MISSING = "policy_dry_run_operator_id_missing"
BLOCK_DRY_RUN_OPERATOR_ID_MISMATCH = "policy_dry_run_operator_id_mismatch"
BLOCK_DRY_RUN_POLICY_SNAPSHOT_MISSING = "policy_dry_run_policy_snapshot_id_missing"
BLOCK_DRY_RUN_DRY_RUN_ID_MISSING = "policy_dry_run_dry_run_id_missing"
BLOCK_DRY_RUN_DECISION_PACKET_UNSAFE = (
    "policy_dry_run_decision_packet_unsafe_behavior_claimed")
BLOCK_DRY_RUN_LEDGER_ENTRY_UNSAFE = (
    "policy_dry_run_ledger_entry_unsafe_behavior_claimed")

# 0174TT checklist packet outcome classes.
CHECKLIST_PACKET_CREATED = (
    "operator_live_gate_checklist_packet_created_not_approval")
CHECKLIST_PACKET_BLOCKED = "operator_live_gate_checklist_packet_blocked"
CHECKLIST_PACKET_FAIL_CLOSED = (
    "operator_live_gate_checklist_packet_fail_closed_forbidden_value")

# 0174TT checklist packet blocked-reason classes.
BLOCK_CHECKLIST_FORBIDDEN_VALUE = "checklist_forbidden_value_detected"
BLOCK_CHECKLIST_DRY_RUN_MISSING = "checklist_policy_dry_run_missing"
BLOCK_CHECKLIST_DRY_RUN_NOT_COMPLETE = "checklist_policy_dry_run_not_complete"
BLOCK_CHECKLIST_DECISION_PACKET_MISSING = "checklist_decision_packet_missing"
BLOCK_CHECKLIST_LEDGER_ENTRY_MISSING = "checklist_latest_ledger_entry_missing"
BLOCK_CHECKLIST_OPERATOR_ID_MISSING = "checklist_operator_id_missing"
BLOCK_CHECKLIST_OPERATOR_ID_MISMATCH = "checklist_operator_id_mismatch"
BLOCK_CHECKLIST_PACKET_ID_MISSING = "checklist_packet_id_missing"
BLOCK_CHECKLIST_PREMARKED_ITEM = "checklist_premarked_item_supplied"
BLOCK_CHECKLIST_DRY_RUN_UNSAFE = "checklist_policy_dry_run_unsafe_behavior_claimed"

# 0174TT checklist registry suppression classes.
CHECKLIST_REGISTRY_APPENDED = "operator_checklist_packet_appended"
CHECKLIST_REGISTRY_DUPLICATE_PACKET_ID = "duplicate_checklist_packet_id_suppressed"
CHECKLIST_REGISTRY_DUPLICATE_DECISION_ID = (
    "duplicate_decision_packet_id_suppressed")

# 0174TU documentation/state sync outcome classes.
DOC_SYNC_CREATED = "local_documentation_state_sync_packet_created"
DOC_SYNC_BLOCKED = "local_documentation_state_sync_packet_blocked"
DOC_SYNC_FAIL_CLOSED = (
    "local_documentation_state_sync_packet_fail_closed_forbidden_value")

# 0174TU documentation/state sync blocked-reason classes.
BLOCK_SYNC_FORBIDDEN_VALUE = "doc_sync_forbidden_value_detected"
BLOCK_SYNC_FINANCIAL_ADVICE = "doc_sync_financial_advice_detected"
BLOCK_SYNC_CHECKLIST_MISSING = "doc_sync_checklist_packet_missing"
BLOCK_SYNC_CHECKLIST_NOT_CREATED = "doc_sync_checklist_packet_not_created"
BLOCK_SYNC_CHECKLIST_CLAIMS_APPROVAL = "doc_sync_checklist_claims_approval"
BLOCK_SYNC_DRY_RUN_MISSING = "doc_sync_policy_dry_run_missing"
BLOCK_SYNC_DRY_RUN_NOT_COMPLETE = "doc_sync_policy_dry_run_not_complete"
BLOCK_SYNC_DECISION_PACKET_MISSING = "doc_sync_decision_packet_missing"
BLOCK_SYNC_OPERATOR_ID_MISSING = "doc_sync_operator_id_missing"
BLOCK_SYNC_SYNC_PACKET_ID_MISSING = "doc_sync_sync_packet_id_missing"

# Remaining FUTURE live gates. Symbolic ids only. Each is UNRESOLVED here and is
# NEVER cleared by this local batch.
REMAINING_FUTURE_LIVE_GATES = (
    "credential_hydration_gate",
    "platform_or_telegram_provider_request_gate",
    "explicit_operator_final_approval_gate",
    "official_provider_documentation_review_gate",
    "one_request_execution_harness_gate",
    "post_request_immutable_audit_gate",
    "emergency_kill_switch_or_revoke_gate",
)
REMAINING_GATE_STATUS = "unresolved_not_run_not_authorized"

# Symbolic checklist sections (0174TT). NOT approval, NOT live readiness; these
# are operator-facing reminders only.
CHECKLIST_SECTIONS = (
    "identity_and_policy_review",
    "redacted_audit_ledger_review",
    "candidate_and_decision_packet_checksum_review",
    "kill_switch_and_rate_retry_policy_review",
    "credential_boundary_still_closed",
    "provider_or_api_docs_still_pending",
    "platform_account_still_unhydrated",
    "one_request_harness_still_not_live",
    "no_autonomous_posting",
    "emergency_revoke_or_kill_switch_procedure_pending",
)
CHECKLIST_ITEM_STATUS_DEFAULT = "operator_action_required"

# Blockers preserved by the documentation/state sync packet (0174TU). These are
# stated as still-true; nothing here clears them.
PRESERVED_BLOCKERS = (
    "no_credentials_hydrated",
    "no_provider_docs_reviewed_in_this_batch",
    "no_live_request_made",
    "no_platform_or_telegram_dispatch",
    "no_readiness_for_live_execution",
    "live_gate_remains_future_operator_owned_task",
)

# Exact binding fields re-asserted across decision packet <-> ledger entry. The
# ledger entry stores its own checksum under ``entry_checksum`` while the
# decision packet mirrors it as ``ledger_entry_checksum``; that pair is compared
# explicitly. Every other field below must match by identical key on both.
_BIND_FIELDS_SAME_KEY = (
    "ledger_entry_id",
    "chain_digest",
    "supervised_request_id",
    "candidate_checksum",
    "audit_checksum",
    "idempotency_fingerprint",
    "outbox_entry_id",
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
    return al.scan_for_leaks(obj)


def scan_for_financial_advice(obj):
    """Return a sorted list of financial-advice violations (delegates 0174TL)."""
    return al.scan_for_financial_advice(obj)


def serialize(obj):
    """Deterministic JSON: sorted keys, stable separators, trailing newline."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization."""
    return hashlib.sha256(serialize(obj).encode("utf-8")).hexdigest()


def _safety_flags():
    """Hard-coded safety invariants attached to every 0174TS/TT/TU object."""
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


def detect_unsafe_behavior_claims(obj, artifact_name):
    """Re-derive unsafe-behavior claims on an input artifact (delegates 0174TQ).

    A clear / pass / created status on an input artifact must NEVER hide a
    tampered flag claiming live / network / credential / dispatch / readiness
    behavior; the 0174TP/TQ/TR helper re-derives the truth directly from the
    flags. Returns a sorted list of tripped flag names (empty when clean).
    """
    return al.detect_unsafe_behavior_claims(obj, artifact_name)


# --------------------------------------------------------------------------- #
# 0174TS: Operator live-gate policy snapshot
# --------------------------------------------------------------------------- #
def build_operator_live_gate_policy_snapshot(policy_snapshot_id):
    """Build a deterministic OperatorLiveGatePolicySnapshot (pure value).

    Symbolic policy posture only: every future live gate is still required and
    nothing is authorized. NEVER live policy approval.
    """
    snapshot = {
        "policy_snapshot_schema": POLICY_SNAPSHOT_SCHEMA,
        "policy_snapshot_schema_version": POLICY_SNAPSHOT_SCHEMA_VERSION,
        "policy_snapshot_id": policy_snapshot_id,
        "remaining_future_live_gates": [
            {"gate_id": gate_id, "gate_status": REMAINING_GATE_STATUS}
            for gate_id in REMAINING_FUTURE_LIVE_GATES
        ],
        "all_future_live_gates_unresolved": True,
        "policy_snapshot_is_live_policy_approval": False,
        **_safety_flags(),
        "valid_for_live_execution": False,
        "requires_future_operator_live_gate": True,
    }
    snapshot["policy_snapshot_checksum"] = compute_checksum(snapshot)
    return snapshot


def _build_remaining_blocker_stack(blocked):
    """Build a LiveGateRemainingBlockerStack (symbolic; live always blocked)."""
    stack = {
        "blocker_kind": "live_gate_remaining_blocker_stack",
        "blockers": list(blocked),
        "blocker_count": len(blocked),
        "remaining_future_live_gates": [
            {"gate_id": gate_id, "gate_status": REMAINING_GATE_STATUS}
            for gate_id in REMAINING_FUTURE_LIVE_GATES
        ],
        "all_future_live_gates_unresolved": True,
        "live_dispatch_blocked": True,
    }
    return stack


def _binding_mismatches(decision_packet, entry):
    """Return the list of binding fields that disagree (empty when all agree)."""
    dp = decision_packet or {}
    e = entry or {}
    mismatches = []
    # The decision packet mirrors the entry's own checksum under a distinct key.
    if dp.get("ledger_entry_checksum") != e.get("entry_checksum"):
        mismatches.append("ledger_entry_checksum")
    for field in _BIND_FIELDS_SAME_KEY:
        if dp.get(field) != e.get(field):
            mismatches.append(field)
    return mismatches


def run_operator_live_gate_policy_dry_run(
        decision_packet, latest_ledger_entry, *, operator_id,
        policy_snapshot_id, dry_run_id, created_at_epoch):
    """Produce a deterministic OperatorLiveGatePolicyDryRun. FAIL-CLOSED.

    Default is blocked. The ONLY non-blocked outcome is ``..._complete_not_
    live``, and only when ALL hold:

      * no forbidden / financial-advice material;
      * the decision packet is ``live_gate_decision_packet_created_not_
        executable`` with ``valid_for_live_execution=False`` and
        ``requires_future_operator_live_gate=True``;
      * a latest ledger entry exists, its checksum agrees with the decision
        packet, and every deep-binding identity field agrees;
      * no input artifact claims unsafe behavior;
      * operator id agrees and explicit policy snapshot id + dry-run id present.

    Even when complete, the dry-run is NEVER live: ``live_ready`` and
    ``valid_for_live_execution`` are always False, and every remaining future
    live gate stays UNRESOLVED / not-run / not-authorized.
    """
    dp = decision_packet or {}
    entry = latest_ledger_entry or {}
    blocked = []

    # 1. Fail-closed redaction + financial-advice scan FIRST.
    forbidden = scan_for_leaks([dp, entry, {
        "operator_id": operator_id,
        "policy_snapshot_id": policy_snapshot_id,
        "dry_run_id": dry_run_id,
    }])
    advice = scan_for_financial_advice([dp, entry])
    if forbidden or advice:
        reasons = []
        if forbidden:
            reasons.append(BLOCK_DRY_RUN_FORBIDDEN_VALUE)
        if advice:
            reasons.append(BLOCK_DRY_RUN_FINANCIAL_ADVICE)
        return _dry_run_result(
            POLICY_DRY_RUN_FAIL_CLOSED, blocked=sorted(set(reasons)),
            complete=False, forbidden_detected=bool(forbidden),
            financial_advice=bool(advice), decision_packet=dp, entry=entry,
            operator_id=operator_id, policy_snapshot_id=policy_snapshot_id,
            dry_run_id=dry_run_id, created_at_epoch=created_at_epoch)

    # 2. The decision packet must be created-not-executable.
    if not dp:
        blocked.append(BLOCK_DRY_RUN_DECISION_PACKET_MISSING)
    elif dp.get("decision_outcome_class") != al.DECISION_CREATED:
        blocked.append(BLOCK_DRY_RUN_DECISION_NOT_CREATED)
    # 3. The decision packet must NOT claim live execution validity.
    if dp.get("valid_for_live_execution") is not False:
        blocked.append(BLOCK_DRY_RUN_DECISION_VALID_FOR_LIVE)
    # 4. The decision packet must still require a future operator live gate.
    if dp.get("requires_future_operator_live_gate") is not True:
        blocked.append(BLOCK_DRY_RUN_NO_FUTURE_GATE_REQUIRED)

    # 5. A latest ledger entry must exist and bind to the decision packet.
    if not entry:
        blocked.append(BLOCK_DRY_RUN_LEDGER_ENTRY_MISSING)
    elif dp:
        if dp.get("ledger_entry_checksum") != entry.get("entry_checksum"):
            blocked.append(BLOCK_DRY_RUN_LEDGER_CHECKSUM_MISMATCH)
        mismatches = _binding_mismatches(dp, entry)
        if mismatches:
            blocked.append(BLOCK_DRY_RUN_BINDING_MISMATCH)
            blocked.extend(BLOCK_DRY_RUN_BINDING_MISMATCH + ":" + field
                           for field in mismatches)

    # 6. No input artifact may claim unsafe behavior, even if its outcome /
    #    checksum metadata still reads clear.
    for base, art_name, art in (
            (BLOCK_DRY_RUN_DECISION_PACKET_UNSAFE,
             al.ARTIFACT_DECISION_PACKET, dp),
            (BLOCK_DRY_RUN_LEDGER_ENTRY_UNSAFE, al.ARTIFACT_LEDGER_ENTRY,
             entry)):
        unsafe = detect_unsafe_behavior_claims(art, art_name)
        if unsafe:
            blocked.append(base)
            blocked.extend(base + ":" + flag for flag in unsafe)

    # 7. Operator id agreement + explicit policy snapshot + dry-run ids.
    if not operator_id:
        blocked.append(BLOCK_DRY_RUN_OPERATOR_ID_MISSING)
    elif dp and dp.get("operator_id") and dp.get("operator_id") != operator_id:
        blocked.append(BLOCK_DRY_RUN_OPERATOR_ID_MISMATCH)
    if not policy_snapshot_id:
        blocked.append(BLOCK_DRY_RUN_POLICY_SNAPSHOT_MISSING)
    if not dry_run_id:
        blocked.append(BLOCK_DRY_RUN_DRY_RUN_ID_MISSING)

    complete = not blocked
    outcome = POLICY_DRY_RUN_COMPLETE if complete else POLICY_DRY_RUN_BLOCKED
    return _dry_run_result(
        outcome, blocked=sorted(set(blocked)), complete=complete,
        forbidden_detected=False, financial_advice=False, decision_packet=dp,
        entry=entry, operator_id=operator_id,
        policy_snapshot_id=policy_snapshot_id, dry_run_id=dry_run_id,
        created_at_epoch=created_at_epoch)


def _dry_run_result(outcome_class, *, blocked, complete, forbidden_detected,
                    financial_advice, decision_packet, entry, operator_id,
                    policy_snapshot_id, dry_run_id, created_at_epoch):
    """Build a deterministic OperatorLiveGatePolicyDryRun (pure value)."""
    status = (Status.PASS if complete
              else (Status.FAIL_CLOSED
                    if (forbidden_detected or financial_advice)
                    else Status.BLOCKED))
    dp = decision_packet or {}
    e = entry or {}
    dry_run = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "policy_dry_run_schema": POLICY_DRY_RUN_SCHEMA,
        "policy_dry_run_schema_version": POLICY_DRY_RUN_SCHEMA_VERSION,
        "status": status,
        "policy_dry_run_outcome_class": outcome_class,
        "policy_dry_run_complete_not_live": complete,
        "dry_run_id": dry_run_id,
        "created_at_epoch": created_at_epoch,
        "operator_id": operator_id,
        "policy_snapshot_id": policy_snapshot_id,
        "policy_snapshot": build_operator_live_gate_policy_snapshot(
            policy_snapshot_id),
        # Exact binding mirrored from the decision packet + ledger entry.
        "decision_packet_id": dp.get("decision_packet_id"),
        "ledger_entry_id": e.get("ledger_entry_id"),
        "ledger_entry_checksum": e.get("entry_checksum"),
        "chain_digest": e.get("chain_digest"),
        "supervised_request_id": e.get("supervised_request_id"),
        "candidate_checksum": e.get("candidate_checksum"),
        "audit_checksum": e.get("audit_checksum"),
        "idempotency_fingerprint": e.get("idempotency_fingerprint"),
        "outbox_entry_id": e.get("outbox_entry_id"),
        "payload_hash_short": e.get("payload_hash_short"),
        "approval_ledger_entry_id": e.get("approval_ledger_entry_id"),
        "review_challenge_id": e.get("review_challenge_id"),
        "editorial_id": e.get("editorial_id"),
        "preview_set_id": e.get("preview_set_id"),
        "decision_packet_checksum": dp.get("decision_packet_checksum"),
        "remaining_future_live_gates": [
            {"gate_id": gate_id, "gate_status": REMAINING_GATE_STATUS}
            for gate_id in REMAINING_FUTURE_LIVE_GATES
        ],
        "all_future_live_gates_unresolved": True,
        "remaining_blocker_stack": _build_remaining_blocker_stack(blocked),
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        "financial_advice_detected": financial_advice,
        # Hard invariants -- a policy dry-run is NEVER live.
        **_safety_flags(),
        "requires_future_operator_live_gate": True,
        "valid_for_live_execution": False,
        "policy_dry_run_is_live_policy_approval": False,
        "policy_dry_run_is_live_readiness": False,
    }
    dry_run["policy_dry_run_checksum"] = compute_checksum(dry_run)
    return dry_run


def build_operator_live_gate_policy_dry_run_integrity_report(dry_run):
    """Re-verify a policy dry-run's checksum + not-live invariants (pure value).

    Deterministic. A dry-run is intact when its stored checksum recomputes, it
    is complete-not-live, every remaining gate is unresolved, and it claims no
    unsafe behavior.
    """
    dr = dry_run or {}
    blocked = []
    recomputed = None
    if not dr:
        blocked.append("integrity_policy_dry_run_missing")
    else:
        stored = dr.get("policy_dry_run_checksum")
        clone = dict(dr)
        clone.pop("policy_dry_run_checksum", None)
        recomputed = compute_checksum(clone)
        if stored != recomputed:
            blocked.append("integrity_policy_dry_run_checksum_mismatch")
        if dr.get("policy_dry_run_outcome_class") != POLICY_DRY_RUN_COMPLETE:
            blocked.append("integrity_policy_dry_run_not_complete")
        if dr.get("valid_for_live_execution") is not False:
            blocked.append("integrity_policy_dry_run_valid_for_live_execution")
        if dr.get("all_future_live_gates_unresolved") is not True:
            blocked.append("integrity_policy_dry_run_future_gate_resolved")
        if detect_unsafe_behavior_claims(dr, al.ARTIFACT_DECISION_PACKET):
            blocked.append("integrity_policy_dry_run_unsafe_behavior_claimed")
    intact = not blocked
    report = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "policy_dry_run_integrity_schema": POLICY_DRY_RUN_INTEGRITY_SCHEMA,
        "policy_dry_run_integrity_schema_version":
            POLICY_DRY_RUN_INTEGRITY_SCHEMA_VERSION,
        "status": Status.PASS if intact else Status.BLOCKED,
        "policy_dry_run_intact_not_live": intact,
        "recomputed_policy_dry_run_checksum": recomputed,
        "blocked_reasons": sorted(set(blocked)),
        **_safety_flags(),
        "valid_for_live_execution": False,
        "requires_future_operator_live_gate": True,
    }
    report["integrity_report_checksum"] = compute_checksum(report)
    return report


# --------------------------------------------------------------------------- #
# 0174TT: Live-gate operator checklist packet
# --------------------------------------------------------------------------- #
def build_operator_checklist_items():
    """Build the symbolic OperatorChecklistItem list (NOT approval, NOT live).

    Every item defaults to ``operator_action_required`` + ``checked=False`` and
    cannot be marked complete automatically.
    """
    return [
        {
            "section_id": section,
            "item_status": CHECKLIST_ITEM_STATUS_DEFAULT,
            "checked": False,
            "item_is_approval": False,
            "item_is_live_readiness": False,
        }
        for section in CHECKLIST_SECTIONS
    ]


def _checklist_has_premarked_item(supplied_items):
    """True if a caller-supplied checklist item is checked / claims approval."""
    for item in (supplied_items or []):
        if not isinstance(item, dict):
            return True
        if item.get("checked") is not False:
            return True
        if item.get("item_status") not in (None, CHECKLIST_ITEM_STATUS_DEFAULT):
            return True
        if item.get("item_is_approval") is True:
            return True
        if item.get("item_is_live_readiness") is True:
            return True
    return False


def build_operator_live_gate_checklist_packet(
        policy_dry_run, decision_packet, latest_ledger_entry, *, operator_id,
        checklist_packet_id, supplied_items=None):
    """Produce a deterministic OperatorLiveGateChecklistPacket. FAIL-CLOSED.

    The ONLY created outcome is ``..._created_not_approval``, and only when:

      * no forbidden material;
      * the policy dry-run is ``..._complete_not_live``;
      * the decision packet and latest ledger entry are present;
      * no caller-supplied item is pre-checked or claims approval/readiness;
      * operator id agrees and an explicit checklist packet id is present.

    The checklist is NEVER approval and NEVER live readiness; every item stays
    ``operator_action_required`` + ``checked=False``.
    """
    dr = policy_dry_run or {}
    dp = decision_packet or {}
    entry = latest_ledger_entry or {}
    blocked = []

    # 1. Fail-closed redaction scan FIRST.
    if scan_for_leaks([dr, dp, entry, {
            "operator_id": operator_id,
            "checklist_packet_id": checklist_packet_id,
    }, supplied_items or []]):
        return _checklist_result(
            CHECKLIST_PACKET_FAIL_CLOSED,
            blocked=[BLOCK_CHECKLIST_FORBIDDEN_VALUE], created=False,
            forbidden_detected=True, dry_run=dr, decision_packet=dp,
            entry=entry, operator_id=operator_id,
            checklist_packet_id=checklist_packet_id)

    # 2. The policy dry-run must be present and complete-not-live.
    if not dr:
        blocked.append(BLOCK_CHECKLIST_DRY_RUN_MISSING)
    elif dr.get("policy_dry_run_outcome_class") != POLICY_DRY_RUN_COMPLETE:
        blocked.append(BLOCK_CHECKLIST_DRY_RUN_NOT_COMPLETE)

    # 3. Decision packet + ledger entry must be present.
    if not dp:
        blocked.append(BLOCK_CHECKLIST_DECISION_PACKET_MISSING)
    if not entry:
        blocked.append(BLOCK_CHECKLIST_LEDGER_ENTRY_MISSING)

    # 4. No caller-supplied item may be pre-checked or claim approval.
    if _checklist_has_premarked_item(supplied_items):
        blocked.append(BLOCK_CHECKLIST_PREMARKED_ITEM)

    # 5. The dry-run must not claim unsafe behavior.
    if detect_unsafe_behavior_claims(dr, al.ARTIFACT_DECISION_PACKET):
        blocked.append(BLOCK_CHECKLIST_DRY_RUN_UNSAFE)

    # 6. Operator id agreement + explicit checklist packet id.
    if not operator_id:
        blocked.append(BLOCK_CHECKLIST_OPERATOR_ID_MISSING)
    elif dr and dr.get("operator_id") and dr.get("operator_id") != operator_id:
        blocked.append(BLOCK_CHECKLIST_OPERATOR_ID_MISMATCH)
    if not checklist_packet_id:
        blocked.append(BLOCK_CHECKLIST_PACKET_ID_MISSING)

    created = not blocked
    outcome = (CHECKLIST_PACKET_CREATED if created
               else CHECKLIST_PACKET_BLOCKED)
    return _checklist_result(
        outcome, blocked=sorted(set(blocked)), created=created,
        forbidden_detected=False, dry_run=dr, decision_packet=dp, entry=entry,
        operator_id=operator_id, checklist_packet_id=checklist_packet_id)


def _checklist_result(outcome_class, *, blocked, created, forbidden_detected,
                      dry_run, decision_packet, entry, operator_id,
                      checklist_packet_id):
    """Build a deterministic OperatorLiveGateChecklistPacket (pure value)."""
    status = (Status.PASS if created
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    dr = dry_run or {}
    dp = decision_packet or {}
    e = entry or {}
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "checklist_packet_schema": CHECKLIST_PACKET_SCHEMA,
        "checklist_packet_schema_version": CHECKLIST_PACKET_SCHEMA_VERSION,
        "status": status,
        "checklist_outcome_class": outcome_class,
        "checklist_packet_created_not_approval": created,
        "checklist_packet_id": checklist_packet_id,
        "operator_id": operator_id,
        # Exact binding mirrored from the dry-run / decision packet / entry.
        "dry_run_id": dr.get("dry_run_id"),
        "policy_dry_run_checksum": dr.get("policy_dry_run_checksum"),
        "decision_packet_id": dp.get("decision_packet_id"),
        "decision_packet_checksum": dp.get("decision_packet_checksum"),
        "ledger_entry_id": e.get("ledger_entry_id"),
        "ledger_entry_checksum": e.get("entry_checksum"),
        "chain_digest": e.get("chain_digest"),
        "candidate_checksum": e.get("candidate_checksum"),
        "audit_checksum": e.get("audit_checksum"),
        "checklist_sections": list(CHECKLIST_SECTIONS),
        "items": build_operator_checklist_items(),
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        # Hard invariants -- a checklist packet is NEVER approval / live.
        **_safety_flags(),
        "requires_future_operator_live_gate": True,
        "valid_for_live_execution": False,
        "checklist_is_approval": False,
        "checklist_is_live_readiness": False,
        "checklist_auto_complete_allowed": False,
    }
    packet["checklist_packet_checksum"] = compute_checksum(packet)
    return packet


class OperatorChecklistRegistry:
    """Append-only registry of LOCAL operator checklist packets.

    Suppresses duplicate checklist packet ids AND duplicate decision packet ids
    deterministically. Nothing is mutated in place. NEVER dispatches, NEVER
    approves, NEVER executes.
    """

    def __init__(self):
        self._packets = []              # append-only checklist packets
        self._by_packet_id = {}         # checklist_packet_id -> index
        self._by_decision_id = {}       # decision_packet_id -> index

    def _copy(self, obj):
        return json.loads(json.dumps(obj))

    @property
    def packets(self):
        return self._copy(self._packets)

    def packet_count(self):
        return len(self._packets)

    def submit(self, checklist_packet):
        """Append a created checklist packet, or suppress a duplicate.

        Raises ValueError when the packet was not created (fail-closed). On a
        fresh checklist + decision id, appends and reports appended. On a
        duplicate checklist id or decision id, appends NOTHING.
        """
        cp = checklist_packet or {}
        if cp.get("checklist_outcome_class") != CHECKLIST_PACKET_CREATED:
            raise ValueError("cannot submit: checklist packet was not created")
        packet_id = cp.get("checklist_packet_id")
        decision_id = cp.get("decision_packet_id")
        if not packet_id:
            raise ValueError("cannot submit: missing checklist packet id")
        if not decision_id:
            raise ValueError("cannot submit: missing decision packet id")

        if packet_id in self._by_packet_id:
            existing = self._packets[self._by_packet_id[packet_id]]
            return self._registry_result(
                CHECKLIST_REGISTRY_DUPLICATE_PACKET_ID, appended=False,
                packet_id=packet_id, decision_id=decision_id, packet=None,
                existing=existing)
        if decision_id in self._by_decision_id:
            existing = self._packets[self._by_decision_id[decision_id]]
            return self._registry_result(
                CHECKLIST_REGISTRY_DUPLICATE_DECISION_ID, appended=False,
                packet_id=packet_id, decision_id=decision_id, packet=None,
                existing=existing)

        index = len(self._packets)
        self._packets.append(self._copy(cp))
        self._by_packet_id[packet_id] = index
        self._by_decision_id[decision_id] = index
        return self._registry_result(
            CHECKLIST_REGISTRY_APPENDED, appended=True, packet_id=packet_id,
            decision_id=decision_id, packet=self._copy(cp), existing=None)

    def _registry_result(self, outcome_class, *, appended, packet_id,
                         decision_id, packet, existing):
        result = {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": Status.PASS,
            "registry_outcome_class": outcome_class,
            "appended": appended,
            "duplicate_suppressed": not appended,
            "checklist_packet_id": packet_id,
            "decision_packet_id": decision_id,
            "checklist_packet": packet,
            "existing_checklist_packet_checksum":
                (existing or {}).get("checklist_packet_checksum"),
            "packet_count": len(self._packets),
            **_safety_flags(),
            "valid_for_live_execution": False,
            "requires_future_operator_live_gate": True,
            "checklist_is_approval": False,
        }
        result["registry_result_checksum"] = compute_checksum(result)
        return result


# --------------------------------------------------------------------------- #
# 0174TU: Documentation / state sync packet
# --------------------------------------------------------------------------- #
def build_next_task_handoff_packet():
    """Build a deterministic NextTaskHandoffPacket (pure value).

    Names the exact next recommended task and re-states that the accepted
    baseline candidate is for HUMAN audit only (never self-accepted).
    """
    packet = {
        "handoff_packet_schema": HANDOFF_PACKET_SCHEMA,
        "handoff_packet_schema_version": HANDOFF_PACKET_SCHEMA_VERSION,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
        "accepted_baseline_requires_human_audit": True,
        "baseline_self_accepted": False,
        "remaining_future_live_gates": [
            {"gate_id": gate_id, "gate_status": REMAINING_GATE_STATUS}
            for gate_id in REMAINING_FUTURE_LIVE_GATES
        ],
        "preserved_blockers": list(PRESERVED_BLOCKERS),
        **_safety_flags(),
        "valid_for_live_execution": False,
        "requires_future_operator_live_gate": True,
    }
    packet["handoff_packet_checksum"] = compute_checksum(packet)
    return packet


def build_local_state_sync_manifest(policy_dry_run, checklist_packet,
                                    decision_packet, latest_ledger_entry):
    """Build a deterministic LocalStateSyncManifest (pure value).

    Records the symbolic ids + checksums of the local artifacts this batch
    syncs. It modifies NO current-state docs and promotes NO authority.
    """
    dr = policy_dry_run or {}
    cp = checklist_packet or {}
    dp = decision_packet or {}
    e = latest_ledger_entry or {}
    manifest = {
        "manifest_kind": "local_state_sync_manifest",
        "dry_run_id": dr.get("dry_run_id"),
        "policy_dry_run_checksum": dr.get("policy_dry_run_checksum"),
        "checklist_packet_id": cp.get("checklist_packet_id"),
        "checklist_packet_checksum": cp.get("checklist_packet_checksum"),
        "decision_packet_id": dp.get("decision_packet_id"),
        "decision_packet_checksum": dp.get("decision_packet_checksum"),
        "ledger_entry_id": e.get("ledger_entry_id"),
        "ledger_entry_checksum": e.get("entry_checksum"),
        "chain_digest": e.get("chain_digest"),
        "modifies_current_state_docs": False,
        "promotes_authority": False,
    }
    return manifest


def build_local_documentation_state_sync_packet(
        policy_dry_run, checklist_packet, decision_packet, latest_ledger_entry,
        *, operator_id, sync_packet_id):
    """Produce a deterministic LocalDocumentationStateSyncPacket. FAIL-CLOSED.

    The ONLY created outcome is ``..._created``, and only when:

      * no forbidden / financial-advice material;
      * the checklist packet is created-not-approval and does NOT claim approval
        or live readiness;
      * the policy dry-run is complete-not-live and the decision packet present;
      * operator id present and an explicit sync packet id present.

    It records preserved blockers, the exact next task, and that the accepted
    baseline candidate is for HUMAN audit only. It modifies NO current-state
    docs and promotes NO authority.
    """
    dr = policy_dry_run or {}
    cp = checklist_packet or {}
    dp = decision_packet or {}
    entry = latest_ledger_entry or {}
    blocked = []

    # 1. Fail-closed redaction + financial-advice scan FIRST.
    forbidden = scan_for_leaks([dr, cp, dp, entry, {
        "operator_id": operator_id,
        "sync_packet_id": sync_packet_id,
    }])
    advice = scan_for_financial_advice([dr, cp, dp, entry])
    if forbidden or advice:
        reasons = []
        if forbidden:
            reasons.append(BLOCK_SYNC_FORBIDDEN_VALUE)
        if advice:
            reasons.append(BLOCK_SYNC_FINANCIAL_ADVICE)
        return _sync_result(
            DOC_SYNC_FAIL_CLOSED, blocked=sorted(set(reasons)), created=False,
            forbidden_detected=bool(forbidden), financial_advice=bool(advice),
            dry_run=dr, checklist_packet=cp, decision_packet=dp, entry=entry,
            operator_id=operator_id, sync_packet_id=sync_packet_id)

    # 2. The checklist packet must be present, created, and NOT approval.
    if not cp:
        blocked.append(BLOCK_SYNC_CHECKLIST_MISSING)
    elif cp.get("checklist_outcome_class") != CHECKLIST_PACKET_CREATED:
        blocked.append(BLOCK_SYNC_CHECKLIST_NOT_CREATED)
    if (cp.get("checklist_is_approval") is not False
            or cp.get("checklist_is_live_readiness") is not False):
        blocked.append(BLOCK_SYNC_CHECKLIST_CLAIMS_APPROVAL)

    # 3. The policy dry-run must be present and complete-not-live.
    if not dr:
        blocked.append(BLOCK_SYNC_DRY_RUN_MISSING)
    elif dr.get("policy_dry_run_outcome_class") != POLICY_DRY_RUN_COMPLETE:
        blocked.append(BLOCK_SYNC_DRY_RUN_NOT_COMPLETE)

    # 4. The decision packet must be present.
    if not dp:
        blocked.append(BLOCK_SYNC_DECISION_PACKET_MISSING)

    # 5. Operator id + explicit sync packet id.
    if not operator_id:
        blocked.append(BLOCK_SYNC_OPERATOR_ID_MISSING)
    if not sync_packet_id:
        blocked.append(BLOCK_SYNC_SYNC_PACKET_ID_MISSING)

    created = not blocked
    outcome = DOC_SYNC_CREATED if created else DOC_SYNC_BLOCKED
    return _sync_result(
        outcome, blocked=sorted(set(blocked)), created=created,
        forbidden_detected=False, financial_advice=False, dry_run=dr,
        checklist_packet=cp, decision_packet=dp, entry=entry,
        operator_id=operator_id, sync_packet_id=sync_packet_id)


def _sync_result(outcome_class, *, blocked, created, forbidden_detected,
                 financial_advice, dry_run, checklist_packet, decision_packet,
                 entry, operator_id, sync_packet_id):
    """Build a deterministic LocalDocumentationStateSyncPacket (pure value)."""
    status = (Status.PASS if created
              else (Status.FAIL_CLOSED
                    if (forbidden_detected or financial_advice)
                    else Status.BLOCKED))
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "doc_sync_packet_schema": DOC_SYNC_PACKET_SCHEMA,
        "doc_sync_packet_schema_version": DOC_SYNC_PACKET_SCHEMA_VERSION,
        "status": status,
        "doc_sync_outcome_class": outcome_class,
        "doc_sync_packet_created": created,
        "sync_packet_id": sync_packet_id,
        "operator_id": operator_id,
        "state_sync_manifest": build_local_state_sync_manifest(
            dry_run, checklist_packet, decision_packet, entry),
        "next_task_handoff_packet": build_next_task_handoff_packet(),
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
        "preserved_blockers": list(PRESERVED_BLOCKERS),
        "accepted_baseline_requires_human_audit": True,
        "baseline_self_accepted": False,
        "modifies_current_state_docs": False,
        "promotes_authority": False,
        "protected_paths_statement": (
            "Only this task's own docs/automation/0174TS_TT_TU artifacts are "
            "written, and ONLY by an explicit write_artifacts call; no "
            "current-state, handoff, or task-ledger doc is modified by this "
            "module."),
        "no_live_behavior_statement": (
            "No live request, no platform or telegram dispatch, no provider or "
            "api call, no credential hydration, no scheduler, no retry loop, "
            "and no autonomous posting are performed by this batch."),
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        "financial_advice_detected": financial_advice,
        # Hard invariants -- documentation sync is NEVER readiness.
        **_safety_flags(),
        "requires_future_operator_live_gate": True,
        "valid_for_live_execution": False,
        "doc_sync_is_readiness": False,
        "doc_sync_is_authority_promotion": False,
    }
    packet["doc_sync_packet_checksum"] = compute_checksum(packet)
    return packet


def build_documentation_sync_integrity_report(sync_packet):
    """Re-verify a doc/state sync packet's checksum + invariants (pure value)."""
    sp = sync_packet or {}
    blocked = []
    recomputed = None
    if not sp:
        blocked.append("integrity_doc_sync_packet_missing")
    else:
        stored = sp.get("doc_sync_packet_checksum")
        clone = dict(sp)
        clone.pop("doc_sync_packet_checksum", None)
        recomputed = compute_checksum(clone)
        if stored != recomputed:
            blocked.append("integrity_doc_sync_packet_checksum_mismatch")
        if sp.get("doc_sync_outcome_class") != DOC_SYNC_CREATED:
            blocked.append("integrity_doc_sync_packet_not_created")
        if sp.get("exact_next_task_recommendation") != (
                EXACT_NEXT_TASK_RECOMMENDATION):
            blocked.append("integrity_doc_sync_packet_wrong_next_task")
        if sp.get("baseline_self_accepted") is not False:
            blocked.append("integrity_doc_sync_packet_baseline_self_accepted")
        if sp.get("valid_for_live_execution") is not False:
            blocked.append("integrity_doc_sync_packet_valid_for_live_execution")
    intact = not blocked
    report = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "doc_sync_integrity_schema": DOC_SYNC_INTEGRITY_SCHEMA,
        "doc_sync_integrity_schema_version": DOC_SYNC_INTEGRITY_SCHEMA_VERSION,
        "status": Status.PASS if intact else Status.BLOCKED,
        "doc_sync_intact": intact,
        "recomputed_doc_sync_packet_checksum": recomputed,
        "blocked_reasons": sorted(set(blocked)),
        **_safety_flags(),
        "valid_for_live_execution": False,
        "requires_future_operator_live_gate": True,
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
        "policy_snapshot_schema": POLICY_SNAPSHOT_SCHEMA,
        "policy_snapshot_schema_version": POLICY_SNAPSHOT_SCHEMA_VERSION,
        "policy_dry_run_schema": POLICY_DRY_RUN_SCHEMA,
        "policy_dry_run_schema_version": POLICY_DRY_RUN_SCHEMA_VERSION,
        "checklist_packet_schema": CHECKLIST_PACKET_SCHEMA,
        "checklist_packet_schema_version": CHECKLIST_PACKET_SCHEMA_VERSION,
        "doc_sync_packet_schema": DOC_SYNC_PACKET_SCHEMA,
        "doc_sync_packet_schema_version": DOC_SYNC_PACKET_SCHEMA_VERSION,
        "policy_dry_run_outcome_classes": [
            POLICY_DRY_RUN_COMPLETE,
            POLICY_DRY_RUN_BLOCKED,
            POLICY_DRY_RUN_FAIL_CLOSED,
        ],
        "checklist_outcome_classes": [
            CHECKLIST_PACKET_CREATED,
            CHECKLIST_PACKET_BLOCKED,
            CHECKLIST_PACKET_FAIL_CLOSED,
            CHECKLIST_REGISTRY_APPENDED,
            CHECKLIST_REGISTRY_DUPLICATE_PACKET_ID,
            CHECKLIST_REGISTRY_DUPLICATE_DECISION_ID,
        ],
        "doc_sync_outcome_classes": [
            DOC_SYNC_CREATED,
            DOC_SYNC_BLOCKED,
            DOC_SYNC_FAIL_CLOSED,
        ],
        "remaining_future_live_gates": list(REMAINING_FUTURE_LIVE_GATES),
        "remaining_future_live_gate_status": REMAINING_GATE_STATUS,
        "checklist_sections": list(CHECKLIST_SECTIONS),
        "preserved_blockers": list(PRESERVED_BLOCKERS),
        "binding_fields": ["ledger_entry_checksum"] + list(
            _BIND_FIELDS_SAME_KEY),
        "hard_invariants": [
            "policy_dry_run_is_not_live_policy_approval",
            "checklist_packet_is_not_operator_approval",
            "documentation_sync_is_not_readiness",
            "future_live_or_api_work_remains_blocked",
            "all_remaining_future_live_gates_remain_unresolved",
            "policy_dry_run_revalidates_all_input_safety_flags",
            "no_credential_hydration",
            "no_provider_or_platform_or_telegram_behavior",
            "no_scheduler_queue_or_retry_loop",
            "no_autonomous_posting",
            "no_financial_advice_or_signal_framing",
            "missing_stale_unsafe_or_ambiguous_authority_blocks",
            "no_current_state_authority_promotion_inside_module",
            "accepted_baseline_requires_human_audit_not_self_accepted",
        ],
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
        "safety_flags": _safety_flags(),
    }
    packet["checksum_sha256"] = compute_checksum(packet)
    return packet


def build_doc():
    """Return a deterministic, redaction-clean markdown contract document."""
    packet = build_packet()
    gates = "\n".join(f"  * `{g}`" for g in REMAINING_FUTURE_LIVE_GATES)
    sections = "\n".join(f"  * `{s}`" for s in CHECKLIST_SECTIONS)
    blockers = "\n".join(f"  * `{b}`" for b in PRESERVED_BLOCKERS)
    hard = "\n".join(f"  * `{inv}`" for inv in packet["hard_invariants"])
    return (
        f"# 0174TS/TT/TU Operator Live-Gate Policy Dry-Run + Doc/State Sync\n\n"
        f"Task: `{TASK_LABEL}`\n\n"
        f"Model: `{MODEL}` version `{MODEL_VERSION}`\n\n"
        f"Baseline commit: `{SOURCE_BASELINE_COMMIT}`\n\n"
        f"## Role\n\n"
        f"This batch is LOCAL and deterministic. It performs NO live platform "
        f"API call, NO Telegram send, NO LLM/provider call, NO network, NO "
        f"env/credential read, NO credential hydration, NO scheduler, and NO "
        f"auto retry. It NEVER dispatches and NEVER executes.\n\n"
        f"## 0174TS Operator live-gate policy dry-run\n\n"
        f"Fail-closed by default. The only non-blocked outcome is "
        f"`{POLICY_DRY_RUN_COMPLETE}`, which requires a created-not-executable "
        f"decision packet (`valid_for_live_execution=False`, "
        f"`requires_future_operator_live_gate=True`) bound exactly to the "
        f"latest redacted audit ledger entry. It re-derives unsafe behavior "
        f"directly from the flags on every input artifact. It enumerates the "
        f"remaining FUTURE live gates, all `{REMAINING_GATE_STATUS}`:\n\n"
        f"{gates}\n\n"
        f"It NEVER sets `live_ready=True` or `valid_for_live_execution=True`, "
        f"and it NEVER clears those future gates.\n\n"
        f"## 0174TT Live-gate operator checklist packet\n\n"
        f"Fail-closed by default. The only created outcome is "
        f"`{CHECKLIST_PACKET_CREATED}`. The checklist is NOT approval and NOT "
        f"live readiness; every item defaults to "
        f"`{CHECKLIST_ITEM_STATUS_DEFAULT}` with `checked=False` and cannot be "
        f"marked complete automatically. Required sections:\n\n{sections}\n\n"
        f"A registry suppresses duplicate checklist packet ids and duplicate "
        f"decision packet ids.\n\n"
        f"## 0174TU Documentation / state sync packet\n\n"
        f"Fail-closed by default. The only created outcome is "
        f"`{DOC_SYNC_CREATED}`. It records a local state-sync manifest + a "
        f"next-task handoff packet, preserves the blockers, and states the "
        f"accepted baseline candidate is for HUMAN audit only (never "
        f"self-accepted). It modifies NO current-state docs and promotes NO "
        f"authority. Preserved blockers:\n\n{blockers}\n\n"
        f"## Hard invariants\n\n{hard}\n\n"
        f"## Next recommended task\n\n`{EXACT_NEXT_TASK_RECOMMENDATION}`\n\n"
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
