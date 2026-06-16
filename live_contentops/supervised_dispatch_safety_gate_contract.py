"""Kill switch + rate/spend/retry policy + one-request supervised dispatch gate.

Tasks 0174TM (kill switch), 0174TN (rate/spend/retry policy), and 0174TO
(one-request/no-auto-retry supervised dispatch gate) -- one deterministic,
LOCAL authority batch on top of the accepted chain:

  * 0174EC: credential handle / redaction boundary.
  * 0174ED + R1: exact approval ledger + payload hash contract.
  * 0174EE + R1: dispatch outbox + idempotency + preflight contract.
  * 0174TG/TH/TI + R1: remote operator inbox + intent parser + review
    challenge contract, terminating in ``remote_review_approved_not_dispatched``.
  * 0174TJ/TK/TL + R2: editorial clear + multi-surface preview set + supervised
    dry run with artifact coverage recomputed from artifact truth, terminating
    in ``supervised_dry_run_complete_not_dispatched``.

Product role of this batch (all LOCAL, all deterministic):
  1. 0174TM evaluates a kill switch policy. Default is FAIL-CLOSED: only an
     explicit ``kill_switch_clear`` state with a fresh policy snapshot permits
     anything downstream. Any disabled scope (global, platform, credential,
     destination, operator, dispatch window) blocks. Kill switch evaluation is
     NOT dispatch and NOT live readiness.
  2. 0174TN evaluates a rate/spend/retry policy. It forbids loops, retries,
     budgets, queues, schedulers, and accidental automation. The only clear
     outcome permits EXACTLY one request through a future gate and requires
     operator re-approval after any failure. It NEVER reads spend/budget from a
     provider and NEVER hydrates credentials.
  3. 0174TO consumes a complete dry run, a clear kill switch evaluation, a clear
     rate/spend/retry evaluation, and the full deep cross-binding, and produces
     a LOCAL ``DispatchAuthorizationCandidate``. The candidate is explicitly
     NOT a dispatch, NOT live-executable, and requires a future operator-owned
     live gate. A registry appends only local candidates and suppresses
     duplicate request ids / idempotency fingerprints deterministically.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Pure Python stdlib only. No requests/httpx/aiohttp, no urllib request
    clients, no socket/ssl/http server, no selenium/playwright, no
    dotenv/keyring/sqlite, no openai/anthropic/telegram/tweepy SDKs.
  * NO network call of any kind.
  * NO env / .env / keyring / browser-session / credential-file read.
  * NO OAuth, token exchange/refresh, credential hydration.
  * NO live posting, sendMessage, platform API call, dispatch, scheduler,
    retry loop, autonomous replies/DMs, scraping, or OpenClaw runtime.
  * Raw chat id / username / phone / token / bot token / webhook url / raw
    provider response / profile url are rejected or redacted by a fail-closed
    scanner and never persisted.
  * NO financial advice: buy/sell/hold calls, position sizing, guaranteed
    predictions, or trade-signal framing in audit text fail closed.
  * Kill switch clear is required but NOT sufficient; rate/spend/retry clear is
    required but NOT sufficient; dry run complete is required but NOT
    sufficient. A one-request candidate is NEVER dispatch and NEVER live
    readiness; the operator-owned live gate remains a separate future task.
  * Missing or ambiguous or stale authority blocks (fail closed).

Importing this module performs NO writes and NO side effects. Artifacts are
written ONLY when ``write_artifacts(...)`` is called explicitly.
"""

import hashlib
import json
import os.path

# Upstream authority layers. This batch CONSUMES their outputs; it never
# bypasses them. The redaction + financial-advice scanners are reused as the
# single source of truth.
from live_contentops import approval_ledger_payload_hash_contract as approval
from live_contentops import editorial_preview_supervised_dry_run_contract as editorial

TASK_LABEL = (
    "TASK_CONTENTOPS_0174TM_TN_TO_KILL_SWITCH_RATE_POLICY_AND_ONE_REQUEST_"
    "SUPERVISED_DISPATCH_GATE_BATCH_V0"
)
MODEL = "SUPERVISED_DISPATCH_SAFETY_GATE_CONTRACT_0174TM_TN_TO"
MODEL_VERSION = "0174TM_TN_TO_SAFETY_GATE_V1"

KILL_SWITCH_SCHEMA = "contentops.kill_switch_evaluation"
KILL_SWITCH_SCHEMA_VERSION = "0174TM_KILL_SWITCH_V1"
RATE_POLICY_SCHEMA = "contentops.rate_spend_retry_evaluation"
RATE_POLICY_SCHEMA_VERSION = "0174TN_RATE_SPEND_RETRY_V1"
DISPATCH_GATE_SCHEMA = "contentops.one_request_dispatch_gate_result"
DISPATCH_GATE_SCHEMA_VERSION = "0174TO_ONE_REQUEST_DISPATCH_GATE_V1"
CANDIDATE_SCHEMA = "contentops.dispatch_authorization_candidate"
CANDIDATE_SCHEMA_VERSION = "0174TO_DISPATCH_AUTHORIZATION_CANDIDATE_V1"
AUDIT_SCHEMA = "contentops.redacted_immutable_dispatch_audit"
AUDIT_SCHEMA_VERSION = "0174TO_REDACTED_IMMUTABLE_DISPATCH_AUDIT_V1"

SOURCE_BASELINE_COMMIT = "905161770623e3dab9347fead84ae20f41ab7e4e"

# Output artifact locations (written ONLY by the explicit write helper).
DOC_REL_DIR = os.path.join("docs", "automation", "0174TM_TN_TO")
PACKET_FILENAME = "supervised_dispatch_safety_gate_contract_packet.json"
DOC_FILENAME = "supervised_dispatch_safety_gate_contract.md"

NEXT_REQUIRED_GATE = (
    "a redacted immutable audit ledger + an operator-owned live gate readiness "
    "review that still performs NO live dispatch; credential hydration and "
    "live platform/Telegram dispatch remain separate future operator-owned "
    "gates and are NOT enabled here"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174TP_TQ_TR_REDACTED_IMMUTABLE_AUDIT_AND_OPERATOR_LIVE_"
    "GATE_READINESS_REVIEW_BATCH_V0"
)


# --------------------------------------------------------------------------- #
# Status vocabularies (symbolic only)
# --------------------------------------------------------------------------- #
class Status:
    PASS = "pass"
    BLOCKED = "blocked"
    FAIL_CLOSED = "fail_closed"


# 0174TM kill switch states.
KILL_SWITCH_GLOBAL_DISABLED = "global_dispatch_disabled"
KILL_SWITCH_PLATFORM_DISABLED = "platform_dispatch_disabled"
KILL_SWITCH_CREDENTIAL_DISABLED = "credential_handle_disabled"
KILL_SWITCH_DESTINATION_DISABLED = "destination_binding_disabled"
KILL_SWITCH_OPERATOR_DISABLED = "operator_dispatch_disabled"
KILL_SWITCH_WINDOW_CLOSED = "dispatch_window_closed"
KILL_SWITCH_CLEAR = "kill_switch_clear"

# The full set of recognised kill switch states. Any state NOT in this set is
# an unknown state and blocks fail-closed.
KNOWN_KILL_SWITCH_STATES = frozenset({
    KILL_SWITCH_GLOBAL_DISABLED,
    KILL_SWITCH_PLATFORM_DISABLED,
    KILL_SWITCH_CREDENTIAL_DISABLED,
    KILL_SWITCH_DESTINATION_DISABLED,
    KILL_SWITCH_OPERATOR_DISABLED,
    KILL_SWITCH_WINDOW_CLOSED,
    KILL_SWITCH_CLEAR,
})

# Every recognised state EXCEPT clear is a disabled/blocking scope.
DISABLED_KILL_SWITCH_STATES = frozenset(
    KNOWN_KILL_SWITCH_STATES - {KILL_SWITCH_CLEAR})

# 0174TM kill switch outcome classes.
KILL_SWITCH_CLEAR_NOT_DISPATCH = "kill_switch_clear_not_dispatch"
KILL_SWITCH_ENGAGED_BLOCKS = "kill_switch_engaged_blocks_dispatch"
KILL_SWITCH_FAIL_CLOSED = "kill_switch_fail_closed_forbidden_value"

# 0174TM kill switch blocked-reason classes.
BLOCK_KILL_SWITCH_FORBIDDEN_VALUE = "kill_switch_forbidden_value_detected"
BLOCK_KILL_SWITCH_STATE_MISSING = "kill_switch_state_missing"
BLOCK_KILL_SWITCH_STATE_UNKNOWN = "kill_switch_state_unknown"
BLOCK_KILL_SWITCH_DISABLED = "kill_switch_scope_disabled"
BLOCK_KILL_SWITCH_POLICY_SNAPSHOT_MISSING = "kill_switch_policy_snapshot_missing"
BLOCK_KILL_SWITCH_POLICY_SNAPSHOT_STALE = "kill_switch_policy_snapshot_stale"
BLOCK_KILL_SWITCH_OPERATOR_MISSING = "kill_switch_operator_id_missing"
BLOCK_KILL_SWITCH_DRY_RUN_NOT_COMPLETE = "kill_switch_dry_run_not_complete"

# 0174TN rate/spend/retry outcome classes.
RATE_POLICY_CLEAR = "rate_spend_retry_policy_clear_for_one_request_gate"
RATE_POLICY_BLOCKED = "rate_spend_retry_policy_blocked"
RATE_POLICY_FAIL_CLOSED = "rate_spend_retry_policy_fail_closed_forbidden_value"

# 0174TN rate/spend/retry blocked-reason classes.
BLOCK_RATE_FORBIDDEN_VALUE = "rate_policy_forbidden_value_detected"
BLOCK_RATE_POLICY_MISSING = "rate_policy_missing"
BLOCK_RATE_AUTO_RETRY_ALLOWED = "rate_policy_auto_retry_allowed"
BLOCK_RATE_MAX_REQUESTS_GT_ONE = "rate_policy_max_requests_greater_than_one"
BLOCK_RATE_SCHEDULER_ENABLED = "rate_policy_scheduler_enabled"
BLOCK_RATE_QUEUE_WORKER_ENABLED = "rate_policy_queue_worker_enabled"
BLOCK_RATE_BACKOFF_LOOP_ENABLED = "rate_policy_backoff_loop_enabled"
BLOCK_RATE_SCHEDULED_RETRY_ENABLED = "rate_policy_scheduled_retry_enabled"
BLOCK_RATE_PROVIDER_BUDGET_HYDRATED = "rate_policy_provider_budget_hydrated"
BLOCK_RATE_SPEND_NOT_SYMBOLIC = "rate_policy_spend_limit_not_symbolic_only"
BLOCK_RATE_RATE_WINDOW_NOT_SYMBOLIC = "rate_policy_rate_window_not_symbolic_only"
BLOCK_RATE_CREDENTIAL_HYDRATED = "rate_policy_credential_hydrated"
BLOCK_RATE_REAPPROVAL_NOT_REQUIRED = (
    "rate_policy_operator_reapproval_not_required_after_failure")
BLOCK_RATE_MISSING_FIELD = "rate_policy_required_field_missing"

# 0174TO one-request dispatch gate outcome classes.
GATE_CANDIDATE_CREATED = (
    "one_request_dispatch_gate_candidate_created_not_dispatched")
GATE_BLOCKED = "one_request_dispatch_gate_blocked"
GATE_FAIL_CLOSED = "one_request_dispatch_gate_fail_closed_forbidden_value"

# 0174TO one-request dispatch gate blocked-reason classes.
BLOCK_GATE_FORBIDDEN_VALUE = "gate_forbidden_value_detected"
BLOCK_GATE_FINANCIAL_ADVICE = "gate_financial_advice_detected"
BLOCK_GATE_DRY_RUN_NOT_COMPLETE = "gate_dry_run_not_complete"
BLOCK_GATE_DRY_RUN_LIVE_FLAG_SET = "gate_dry_run_live_or_platform_flag_set"
BLOCK_GATE_KILL_SWITCH_NOT_CLEAR = "gate_kill_switch_not_clear"
BLOCK_GATE_RATE_POLICY_NOT_CLEAR = "gate_rate_spend_retry_policy_not_clear"
BLOCK_GATE_OPERATOR_ID_MISMATCH = "gate_operator_id_mismatch"
BLOCK_GATE_OUTBOX_ENTRY_MISMATCH = "gate_outbox_entry_id_mismatch"
BLOCK_GATE_PAYLOAD_HASH_MISMATCH = "gate_payload_hash_mismatch"
BLOCK_GATE_LEDGER_ENTRY_MISMATCH = "gate_approval_ledger_entry_id_mismatch"
BLOCK_GATE_CHALLENGE_ID_MISMATCH = "gate_review_challenge_id_mismatch"
BLOCK_GATE_EDITORIAL_ID_MISMATCH = "gate_editorial_id_mismatch"
BLOCK_GATE_PREVIEW_SET_ID_MISMATCH = "gate_preview_set_id_mismatch"
BLOCK_GATE_IDEMPOTENCY_KEY_MISMATCH = "gate_idempotency_key_mismatch"
BLOCK_GATE_REQUEST_ID_MISSING = "gate_explicit_supervised_request_id_missing"
BLOCK_GATE_MISSING_FIELD = "gate_required_field_missing"

# R1 upstream safety-flag revalidation blocked-reason classes. Clear status /
# pass / clear metadata on an upstream artifact must NEVER be able to hide a
# claim of unsafe behavior; the gate re-derives the truth from the flags.
BLOCK_GATE_DRY_RUN_UNSAFE_BEHAVIOR = (
    "dispatch_gate_dry_run_unsafe_behavior_claimed")
BLOCK_GATE_KILL_SWITCH_UNSAFE_BEHAVIOR = (
    "dispatch_gate_kill_switch_unsafe_behavior_claimed")
BLOCK_GATE_RATE_POLICY_UNSAFE_BEHAVIOR = (
    "dispatch_gate_rate_policy_unsafe_behavior_claimed")

# Artifact-name labels passed to detect_unsafe_behavior_claims.
ARTIFACT_DRY_RUN = "dry_run"
ARTIFACT_KILL_SWITCH = "kill_switch"
ARTIFACT_RATE_POLICY = "rate_policy"

_ARTIFACT_UNSAFE_BASE = {
    ARTIFACT_DRY_RUN: BLOCK_GATE_DRY_RUN_UNSAFE_BEHAVIOR,
    ARTIFACT_KILL_SWITCH: BLOCK_GATE_KILL_SWITCH_UNSAFE_BEHAVIOR,
    ARTIFACT_RATE_POLICY: BLOCK_GATE_RATE_POLICY_UNSAFE_BEHAVIOR,
}

# Universal unsafe-behavior flags that MUST be False on every upstream artifact.
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
_UNSAFE_READINESS_FLAGS = (
    "dry_run_is_dispatch",
    "dry_run_is_live_readiness_claim",
    "kill_switch_evaluation_is_dispatch",
    "kill_switch_evaluation_is_live_readiness",
    "rate_spend_retry_evaluation_is_dispatch",
    "gate_is_dispatch",
    "gate_is_provider_authorization",
    "gate_is_live_readiness",
    "valid_for_live_execution",
)

# 0174TO registry suppression classes.
GATE_REGISTRY_APPENDED = "dispatch_authorization_candidate_appended"
GATE_REGISTRY_DUPLICATE_REQUEST_ID = "duplicate_request_id_suppressed"
GATE_REGISTRY_DUPLICATE_FINGERPRINT = "duplicate_idempotency_fingerprint_suppressed"

# Deep-binding identity fields threaded through every artifact.
_DEEP_BIND_FIELDS = (
    "review_challenge_id",
    "operator_id",
    "editorial_id",
    "preview_set_id",
    "outbox_entry_id",
    "idempotency_key_short",
    "payload_hash_short",
    "approval_ledger_entry_id",
)


# --------------------------------------------------------------------------- #
# Redaction + financial-advice scanning + deterministic serialization.
# --------------------------------------------------------------------------- #
def scan_for_leaks(obj):
    """Return a sorted list of redaction violations (delegates to 0174ED)."""
    return approval.scan_for_leaks(obj)


def scan_for_financial_advice(obj):
    """Return a sorted list of financial-advice violations (delegates 0174TL)."""
    return editorial.scan_for_financial_advice(obj)


def serialize(obj):
    """Deterministic JSON: sorted keys, stable separators, trailing newline."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization."""
    return hashlib.sha256(serialize(obj).encode("utf-8")).hexdigest()


def _short(h):
    """Return the first 16 hex chars of a hash/key (display only)."""
    return str(h)[:16]


# --------------------------------------------------------------------------- #
# Shared safety flags
# --------------------------------------------------------------------------- #
def _safety_flags():
    """Hard-coded safety invariants attached to every 0174TM/TN/TO object."""
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


# --------------------------------------------------------------------------- #
# 0174TL dry-run acceptance helper
# --------------------------------------------------------------------------- #
def _dry_run_is_complete(dry_run_result):
    """True if a 0174TL dry-run result is an exact complete-not-dispatched."""
    dr = dry_run_result or {}
    return (
        dr.get("dry_run_outcome_class")
        == editorial.DRY_RUN_COMPLETE_NOT_DISPATCHED
        and dr.get("dry_run_complete_not_dispatched") is True
        and dr.get("status") == editorial.Status.PASS
    )


def _dry_run_claims_live(dry_run_result):
    """True if a dry-run result claims any live/platform/credential behavior."""
    dr = dry_run_result or {}
    return (
        dr.get("dispatch_performed") is not False
        or dr.get("live_request_performed") is not False
        or dr.get("platform_api_called") is not False
        or dr.get("credential_hydrated") is not False
        or dr.get("live_ready") is not False
        or dr.get("dry_run_is_dispatch") is not False
        or dr.get("dry_run_is_live_readiness_claim") is not False
    )


def detect_unsafe_behavior_claims(obj, artifact_name):
    """Return deterministic blocked reasons for any unsafe flag an artifact claims.

    R1 hardening: a previously-"clear"/"pass" upstream artifact (dry run, kill
    switch evaluation, or rate/spend/retry evaluation) must NOT be able to carry
    a tampered flag claiming live/network/credential/scheduler/retry/dispatch
    behavior past the gate just because its status metadata still reads clear.
    This helper re-derives the truth directly from the flags.

    A universal flag "claims" unsafe behavior when it is present and not False.
    An artifact-specific readiness boolean likewise blocks when present and not
    False. Returns a sorted, de-duplicated list whose first element (when any
    flag trips) is the artifact's bare unsafe-behavior-claimed class, followed
    by ``<base>:<flag>`` entries for audit precision. An empty list means the
    artifact claims no unsafe behavior.
    """
    o = obj or {}
    base = _ARTIFACT_UNSAFE_BASE.get(
        artifact_name,
        "dispatch_gate_" + str(artifact_name) + "_unsafe_behavior_claimed")
    hits = []
    for flag in (_UNSAFE_BEHAVIOR_FLAGS + _UNSAFE_READINESS_FLAGS):
        if flag in o and o.get(flag) is not False:
            hits.append(flag)
    if not hits:
        return []
    reasons = [base]
    reasons.extend(base + ":" + flag for flag in hits)
    return sorted(set(reasons))


# --------------------------------------------------------------------------- #
# 0174TM: Kill switch contract
# --------------------------------------------------------------------------- #
def evaluate_kill_switch(dry_run_result, *, operator_id, policy_snapshot_id,
                         kill_switch_state, current_policy_snapshot_id=None):
    """Deterministically evaluate the kill switch. FAIL-CLOSED by default.

    Consumes a 0174TL dry-run result plus an operator id, a policy snapshot id,
    and an explicit kill switch state. Only an explicit ``kill_switch_clear``
    state with a fresh policy snapshot returns clear; everything else blocks.

      * forbidden credential/provider material => ``fail_closed``;
      * a missing kill switch state blocks;
      * an unknown kill switch state blocks;
      * any disabled scope (global/platform/credential/destination/operator/
        window) blocks;
      * a missing policy snapshot blocks;
      * a stale policy snapshot (mismatch vs ``current_policy_snapshot_id``,
        when supplied) blocks;
      * a missing operator id blocks;
      * a dry run that is not complete-not-dispatched blocks.

    Kill switch evaluation is NEVER dispatch and NEVER live readiness.
    """
    dr = dry_run_result or {}
    blocked = []

    # 1. Fail-closed redaction scan FIRST.
    scan_payload = {
        "operator_id": operator_id,
        "policy_snapshot_id": policy_snapshot_id,
        "kill_switch_state": kill_switch_state,
        "current_policy_snapshot_id": current_policy_snapshot_id,
    }
    if scan_for_leaks([dr, scan_payload]):
        return _kill_switch_result(
            KILL_SWITCH_FAIL_CLOSED, blocked=[BLOCK_KILL_SWITCH_FORBIDDEN_VALUE],
            clear=False, forbidden_detected=True, operator_id=operator_id,
            policy_snapshot_id=policy_snapshot_id,
            kill_switch_state=kill_switch_state, dry_run_result=dr)

    # 2. A kill switch state must be present.
    if not kill_switch_state:
        blocked.append(BLOCK_KILL_SWITCH_STATE_MISSING)
    # 3. The kill switch state must be recognised.
    elif kill_switch_state not in KNOWN_KILL_SWITCH_STATES:
        blocked.append(BLOCK_KILL_SWITCH_STATE_UNKNOWN)
    # 4. Any recognised disabled scope blocks.
    elif kill_switch_state in DISABLED_KILL_SWITCH_STATES:
        blocked.append(BLOCK_KILL_SWITCH_DISABLED + ":" + kill_switch_state)

    # 5. A policy snapshot id must be present.
    if not policy_snapshot_id:
        blocked.append(BLOCK_KILL_SWITCH_POLICY_SNAPSHOT_MISSING)
    # 6. A stale policy snapshot (mismatch vs current) blocks.
    elif (current_policy_snapshot_id is not None
            and policy_snapshot_id != current_policy_snapshot_id):
        blocked.append(BLOCK_KILL_SWITCH_POLICY_SNAPSHOT_STALE)

    # 7. An operator id must be present.
    if not operator_id:
        blocked.append(BLOCK_KILL_SWITCH_OPERATOR_MISSING)

    # 8. The dry run must be complete-not-dispatched.
    if not _dry_run_is_complete(dr):
        blocked.append(BLOCK_KILL_SWITCH_DRY_RUN_NOT_COMPLETE)

    clear = not blocked
    outcome = (KILL_SWITCH_CLEAR_NOT_DISPATCH if clear
               else KILL_SWITCH_ENGAGED_BLOCKS)
    return _kill_switch_result(
        outcome, blocked=sorted(set(blocked)), clear=clear,
        forbidden_detected=False, operator_id=operator_id,
        policy_snapshot_id=policy_snapshot_id,
        kill_switch_state=kill_switch_state, dry_run_result=dr)


def _kill_switch_result(outcome_class, *, blocked, clear, forbidden_detected,
                        operator_id, policy_snapshot_id, kill_switch_state,
                        dry_run_result):
    """Build a deterministic KillSwitchEvaluation (pure value)."""
    status = (Status.PASS if clear
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    dr = dry_run_result or {}
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "kill_switch_schema": KILL_SWITCH_SCHEMA,
        "kill_switch_schema_version": KILL_SWITCH_SCHEMA_VERSION,
        "status": status,
        "kill_switch_outcome_class": outcome_class,
        "kill_switch_clear": clear,
        "kill_switch_state": kill_switch_state,
        "policy_snapshot_id": policy_snapshot_id,
        "operator_id": operator_id,
        # Deep-binding identity fields carried forward from the dry run.
        "review_challenge_id": dr.get("review_challenge_id"),
        "editorial_id": dr.get("editorial_id"),
        "preview_set_id": dr.get("preview_set_id"),
        "outbox_entry_id": dr.get("outbox_entry_id"),
        "idempotency_key_short": dr.get("idempotency_key_short"),
        "payload_hash_short": dr.get("payload_hash_short"),
        "approval_ledger_entry_id": dr.get("approval_ledger_entry_id"),
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        "known_kill_switch_states": sorted(KNOWN_KILL_SWITCH_STATES),
        # Hard invariants -- a kill switch evaluation is NEVER dispatch / live.
        **_safety_flags(),
        "kill_switch_evaluation_is_dispatch": False,
        "kill_switch_evaluation_is_live_readiness": False,
    }
    result["kill_switch_checksum"] = compute_checksum(result)
    return result


def build_kill_switch_audit(kill_switch_evaluation):
    """Build a redacted, deterministic KillSwitchAudit (symbolic values only)."""
    ks = kill_switch_evaluation or {}
    audit = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "audit_kind": "kill_switch_audit",
        "status": ks.get("status"),
        "kill_switch_outcome_class": ks.get("kill_switch_outcome_class"),
        "kill_switch_state": ks.get("kill_switch_state"),
        "policy_snapshot_id": ks.get("policy_snapshot_id"),
        "operator_id": ks.get("operator_id"),
        "outbox_entry_id": ks.get("outbox_entry_id"),
        "idempotency_key_short": ks.get("idempotency_key_short"),
        "payload_hash_short": ks.get("payload_hash_short"),
        "approval_ledger_entry_id": ks.get("approval_ledger_entry_id"),
        "blocked_reasons": ks.get("blocked_reasons", []),
        **_safety_flags(),
    }
    audit["audit_checksum"] = compute_checksum(audit)
    return audit


# --------------------------------------------------------------------------- #
# 0174TN: Rate / spend / retry policy contract
# --------------------------------------------------------------------------- #
def build_rate_spend_retry_policy_snapshot(*, policy_snapshot_id,
                                           rate_limit_window_class="symbolic_only",
                                           spend_limit_class="symbolic_only"):
    """Build a canonical, conservative RateSpendRetryPolicySnapshot.

    The returned snapshot encodes the ONLY policy shape this contract accepts:
    one request per gate, no auto retry, no scheduler/queue/backoff/scheduled
    retry, provider budget NOT hydrated, credential NOT hydrated, symbolic-only
    rate and spend limits, and operator re-approval required after a failure.
    Callers may tamper with it to exercise the blocking rules.
    """
    return {
        "policy_snapshot_id": policy_snapshot_id,
        "max_requests_per_gate": 1,
        "auto_retry_allowed": False,
        "scheduler_enabled": False,
        "queue_worker_enabled": False,
        "backoff_loop_enabled": False,
        "scheduled_retry_enabled": False,
        "provider_budget_hydrated": False,
        "credential_hydrated": False,
        "rate_limit_window_class": rate_limit_window_class,
        "spend_limit_class": spend_limit_class,
        "operator_reapproval_required_after_failure": True,
    }


def evaluate_rate_spend_retry_policy(policy_snapshot, *, operator_id=None):
    """Deterministically evaluate a rate/spend/retry policy. FAIL-CLOSED.

    The ONLY clear outcome is ``rate_spend_retry_policy_clear_for_one_request_
    gate``, and only when EVERY invariant holds:

      * forbidden credential/provider material => ``fail_closed``;
      * a missing policy blocks;
      * ``max_requests_per_gate`` must equal 1 (more than one blocks);
      * ``auto_retry_allowed`` must be False;
      * ``scheduler_enabled`` / ``queue_worker_enabled`` /
        ``backoff_loop_enabled`` / ``scheduled_retry_enabled`` must be False;
      * ``provider_budget_hydrated`` must be False (no provider spend claim);
      * ``credential_hydrated`` must be False;
      * ``rate_limit_window_class`` and ``spend_limit_class`` must be
        symbolic-only;
      * ``operator_reapproval_required_after_failure`` must be True.

    The policy NEVER reads env/credentials and NEVER calls a provider API.
    """
    policy = policy_snapshot
    blocked = []

    # 1. Fail-closed redaction scan FIRST.
    if scan_for_leaks([policy or {}, {"operator_id": operator_id}]):
        return _rate_policy_result(
            RATE_POLICY_FAIL_CLOSED, blocked=[BLOCK_RATE_FORBIDDEN_VALUE],
            clear=False, forbidden_detected=True, policy_snapshot=policy or {},
            operator_id=operator_id)

    # 2. A policy must be present.
    if not policy:
        return _rate_policy_result(
            RATE_POLICY_BLOCKED, blocked=[BLOCK_RATE_POLICY_MISSING],
            clear=False, forbidden_detected=False, policy_snapshot={},
            operator_id=operator_id)

    # 3. Required identity field.
    if not policy.get("policy_snapshot_id"):
        blocked.append(BLOCK_RATE_MISSING_FIELD + ":policy_snapshot_id")

    # 4. Exactly one request per gate.
    if policy.get("max_requests_per_gate") != 1:
        blocked.append(BLOCK_RATE_MAX_REQUESTS_GT_ONE)

    # 5. No auto retry.
    if policy.get("auto_retry_allowed") is not False:
        blocked.append(BLOCK_RATE_AUTO_RETRY_ALLOWED)

    # 6. No scheduler / queue / backoff / scheduled retry.
    if policy.get("scheduler_enabled") is not False:
        blocked.append(BLOCK_RATE_SCHEDULER_ENABLED)
    if policy.get("queue_worker_enabled") is not False:
        blocked.append(BLOCK_RATE_QUEUE_WORKER_ENABLED)
    if policy.get("backoff_loop_enabled") is not False:
        blocked.append(BLOCK_RATE_BACKOFF_LOOP_ENABLED)
    if policy.get("scheduled_retry_enabled") is not False:
        blocked.append(BLOCK_RATE_SCHEDULED_RETRY_ENABLED)

    # 7. No provider budget / spend claim, no credential hydration.
    if policy.get("provider_budget_hydrated") is not False:
        blocked.append(BLOCK_RATE_PROVIDER_BUDGET_HYDRATED)
    if policy.get("credential_hydrated") is not False:
        blocked.append(BLOCK_RATE_CREDENTIAL_HYDRATED)

    # 8. Rate window + spend limit must be symbolic-only.
    if policy.get("rate_limit_window_class") != "symbolic_only":
        blocked.append(BLOCK_RATE_RATE_WINDOW_NOT_SYMBOLIC)
    if policy.get("spend_limit_class") != "symbolic_only":
        blocked.append(BLOCK_RATE_SPEND_NOT_SYMBOLIC)

    # 9. Operator re-approval required after a failure.
    if policy.get("operator_reapproval_required_after_failure") is not True:
        blocked.append(BLOCK_RATE_REAPPROVAL_NOT_REQUIRED)

    clear = not blocked
    outcome = RATE_POLICY_CLEAR if clear else RATE_POLICY_BLOCKED
    return _rate_policy_result(
        outcome, blocked=sorted(set(blocked)), clear=clear,
        forbidden_detected=False, policy_snapshot=policy,
        operator_id=operator_id)


def _rate_policy_result(outcome_class, *, blocked, clear, forbidden_detected,
                        policy_snapshot, operator_id):
    """Build a deterministic RateSpendRetryEvaluation (pure value).

    Embeds the AttemptBudget, ProviderSpendBoundary, and RetryPolicyBoundary
    sub-objects so the evaluation is self-describing and re-verifiable.
    """
    status = (Status.PASS if clear
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    policy = policy_snapshot or {}
    attempt_budget = {
        "max_requests_per_gate": policy.get("max_requests_per_gate"),
        "max_requests_authorized": 1 if clear else 0,
        "auto_retry_allowed": False,
    }
    provider_spend_boundary = {
        "provider_budget_hydrated": policy.get("provider_budget_hydrated"),
        "spend_limit_class": policy.get("spend_limit_class"),
        "spend_limit_symbolic_only":
            policy.get("spend_limit_class") == "symbolic_only",
        "provider_api_called": False,
        "credential_hydrated": False,
    }
    retry_policy_boundary = {
        "auto_retry_allowed": policy.get("auto_retry_allowed"),
        "scheduler_enabled": policy.get("scheduler_enabled"),
        "queue_worker_enabled": policy.get("queue_worker_enabled"),
        "backoff_loop_enabled": policy.get("backoff_loop_enabled"),
        "scheduled_retry_enabled": policy.get("scheduled_retry_enabled"),
        "operator_reapproval_required_after_failure":
            policy.get("operator_reapproval_required_after_failure"),
        "no_backoff_loop": policy.get("backoff_loop_enabled") is False,
        "no_queue_worker": policy.get("queue_worker_enabled") is False,
        "no_scheduled_retry": policy.get("scheduled_retry_enabled") is False,
    }
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "rate_policy_schema": RATE_POLICY_SCHEMA,
        "rate_policy_schema_version": RATE_POLICY_SCHEMA_VERSION,
        "status": status,
        "rate_spend_retry_outcome_class": outcome_class,
        "rate_spend_retry_policy_clear": clear,
        "policy_snapshot_id": policy.get("policy_snapshot_id"),
        "operator_id": operator_id,
        "attempt_budget": attempt_budget,
        "provider_spend_boundary": provider_spend_boundary,
        "retry_policy_boundary": retry_policy_boundary,
        "max_requests_authorized": 1 if clear else 0,
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        # Hard invariants -- a policy evaluation is NEVER dispatch / live.
        **_safety_flags(),
        "rate_spend_retry_evaluation_is_dispatch": False,
        "provider_budget_not_hydrated": True,
        "credential_not_hydrated": True,
    }
    result["rate_policy_checksum"] = compute_checksum(result)
    return result


# --------------------------------------------------------------------------- #
# 0174TO: One-request supervised dispatch gate contract
# --------------------------------------------------------------------------- #
def build_one_request_dispatch_gate_input_bundle(
        dry_run_result, kill_switch_evaluation, rate_spend_retry_evaluation, *,
        operator_id, supervised_request_id, outbox_entry_id, payload_hash_short,
        approval_ledger_entry_id, review_challenge_id, editorial_id,
        preview_set_id, idempotency_key_short=None, payload_hash=None,
        idempotency_key=None):
    """Build a pure-value OneRequestDispatchGateInputBundle.

    Gathers every input the gate cross-binds. Short hashes are required; full
    hashes/keys are optional (``as available``) and are only cross-checked when
    present. No raw payload text or credential material is carried.
    """
    return {
        "dry_run_result": dry_run_result,
        "kill_switch_evaluation": kill_switch_evaluation,
        "rate_spend_retry_evaluation": rate_spend_retry_evaluation,
        "operator_id": operator_id,
        "supervised_request_id": supervised_request_id,
        "outbox_entry_id": outbox_entry_id,
        "idempotency_key_short": idempotency_key_short,
        "idempotency_key": idempotency_key,
        "payload_hash_short": payload_hash_short,
        "payload_hash": payload_hash,
        "approval_ledger_entry_id": approval_ledger_entry_id,
        "review_challenge_id": review_challenge_id,
        "editorial_id": editorial_id,
        "preview_set_id": preview_set_id,
    }


def _kill_switch_is_clear(kill_switch_evaluation):
    ks = kill_switch_evaluation or {}
    return (
        ks.get("kill_switch_outcome_class") == KILL_SWITCH_CLEAR_NOT_DISPATCH
        and ks.get("kill_switch_clear") is True
        and ks.get("status") == Status.PASS
    )


def _rate_policy_is_clear(rate_spend_retry_evaluation):
    rp = rate_spend_retry_evaluation or {}
    return (
        rp.get("rate_spend_retry_outcome_class") == RATE_POLICY_CLEAR
        and rp.get("rate_spend_retry_policy_clear") is True
        and rp.get("status") == Status.PASS
    )


def _idempotency_fingerprint(bundle):
    """Deterministic non-secret fingerprint of the authority-bearing binding.

    Built ONLY from symbolic ids and short hashes -- never from raw secrets.
    Two requests with the same authority binding share a fingerprint, so the
    registry can suppress a duplicate even under a different request id.
    """
    b = bundle or {}
    keyed = {
        "outbox_entry_id": b.get("outbox_entry_id"),
        "idempotency_key_short": b.get("idempotency_key_short"),
        "payload_hash_short": b.get("payload_hash_short"),
        "approval_ledger_entry_id": b.get("approval_ledger_entry_id"),
        "review_challenge_id": b.get("review_challenge_id"),
        "editorial_id": b.get("editorial_id"),
        "preview_set_id": b.get("preview_set_id"),
    }
    return hashlib.sha256(serialize(keyed).encode("utf-8")).hexdigest()


def run_one_request_dispatch_gate(input_bundle):
    """Deterministically produce a DispatchAuthorizationCandidate or block.

    Consumes a OneRequestDispatchGateInputBundle and re-proves the FULL local
    authority hierarchy. Fail-closed (the result is ``one_request_dispatch_
    gate_blocked`` unless ALL hold):

      * no forbidden credential/provider material and no financial advice;
      * the dry run is an exact complete-not-dispatched outcome carrying no
        live/platform/credential flag;
      * the kill switch evaluation is clear;
      * the rate/spend/retry evaluation is clear;
      * the deep cross-binding agrees across the dry run, kill switch, rate
        policy, and the bundle (operator id, outbox entry id, payload hash
        short, approval ledger id, review challenge id, editorial id, preview
        set id, and idempotency/payload full hashes when supplied);
      * an explicit supervised request id is present.

    Even when all hold, the outcome is ``..._candidate_created_not_dispatched``
    and the candidate is explicitly NOT live-executable.
    """
    bundle = input_bundle or {}
    dr = bundle.get("dry_run_result") or {}
    ks = bundle.get("kill_switch_evaluation") or {}
    rp = bundle.get("rate_spend_retry_evaluation") or {}
    blocked = []

    # 1. Fail-closed redaction scan across all inputs first.
    if scan_for_leaks([dr, ks, rp, {
            "operator_id": bundle.get("operator_id"),
            "supervised_request_id": bundle.get("supervised_request_id"),
            "outbox_entry_id": bundle.get("outbox_entry_id"),
            "review_challenge_id": bundle.get("review_challenge_id"),
            "editorial_id": bundle.get("editorial_id"),
            "preview_set_id": bundle.get("preview_set_id"),
            "approval_ledger_entry_id": bundle.get("approval_ledger_entry_id"),
    }]):
        return _gate_result(
            GATE_FAIL_CLOSED, blocked=[BLOCK_GATE_FORBIDDEN_VALUE],
            created=False, forbidden_detected=True, financial_advice=False,
            bundle=bundle)
    # 2. Hard content-safety gate: no financial advice anywhere in the chain.
    if scan_for_financial_advice([dr, ks, rp]):
        return _gate_result(
            GATE_FAIL_CLOSED, blocked=[BLOCK_GATE_FINANCIAL_ADVICE],
            created=False, forbidden_detected=False, financial_advice=True,
            bundle=bundle)

    # 3. Dry run must be complete-not-dispatched and carry no live flag.
    if not _dry_run_is_complete(dr):
        blocked.append(BLOCK_GATE_DRY_RUN_NOT_COMPLETE)
    if _dry_run_claims_live(dr):
        blocked.append(BLOCK_GATE_DRY_RUN_LIVE_FLAG_SET)

    # 3b. R1: re-validate the upstream safety flags on EVERY artifact. Clear
    #     status/pass/clear metadata on the dry run, kill switch, or rate policy
    #     must NOT be able to hide a claim of unsafe behavior (network,
    #     platform/telegram api, credential hydration, llm, scheduler, auto
    #     retry, dispatch, live readiness, autonomous reply).
    blocked.extend(detect_unsafe_behavior_claims(dr, ARTIFACT_DRY_RUN))
    blocked.extend(detect_unsafe_behavior_claims(ks, ARTIFACT_KILL_SWITCH))
    blocked.extend(detect_unsafe_behavior_claims(rp, ARTIFACT_RATE_POLICY))

    # 4. Kill switch + rate policy must both be clear.
    if not _kill_switch_is_clear(ks):
        blocked.append(BLOCK_GATE_KILL_SWITCH_NOT_CLEAR)
    if not _rate_policy_is_clear(rp):
        blocked.append(BLOCK_GATE_RATE_POLICY_NOT_CLEAR)

    operator_id = bundle.get("operator_id")

    # 5. Operator id must agree across the dry run, kill switch, rate policy.
    if not (operator_id
            and dr.get("operator_id") == operator_id
            and ks.get("operator_id") == operator_id
            and rp.get("operator_id") == operator_id):
        blocked.append(BLOCK_GATE_OPERATOR_ID_MISMATCH)

    # 6. Authority binding must agree across the dry run, kill switch + bundle.
    if not (bundle.get("outbox_entry_id")
            and dr.get("outbox_entry_id") == bundle.get("outbox_entry_id")
            and ks.get("outbox_entry_id") == bundle.get("outbox_entry_id")):
        blocked.append(BLOCK_GATE_OUTBOX_ENTRY_MISMATCH)
    if not (bundle.get("payload_hash_short")
            and dr.get("payload_hash_short") == bundle.get("payload_hash_short")
            and ks.get("payload_hash_short")
            == bundle.get("payload_hash_short")):
        blocked.append(BLOCK_GATE_PAYLOAD_HASH_MISMATCH)
    # Full payload hash, when supplied, must agree with its short form.
    if (bundle.get("payload_hash")
            and _short(bundle.get("payload_hash"))
            != bundle.get("payload_hash_short")):
        blocked.append(BLOCK_GATE_PAYLOAD_HASH_MISMATCH)
    if not (bundle.get("approval_ledger_entry_id")
            and dr.get("approval_ledger_entry_id")
            == bundle.get("approval_ledger_entry_id")
            and ks.get("approval_ledger_entry_id")
            == bundle.get("approval_ledger_entry_id")):
        blocked.append(BLOCK_GATE_LEDGER_ENTRY_MISMATCH)
    if not (bundle.get("review_challenge_id")
            and dr.get("review_challenge_id")
            == bundle.get("review_challenge_id")
            and ks.get("review_challenge_id")
            == bundle.get("review_challenge_id")):
        blocked.append(BLOCK_GATE_CHALLENGE_ID_MISMATCH)
    if not (bundle.get("editorial_id")
            and dr.get("editorial_id") == bundle.get("editorial_id")
            and ks.get("editorial_id") == bundle.get("editorial_id")):
        blocked.append(BLOCK_GATE_EDITORIAL_ID_MISMATCH)
    if not (bundle.get("preview_set_id")
            and dr.get("preview_set_id") == bundle.get("preview_set_id")
            and ks.get("preview_set_id") == bundle.get("preview_set_id")):
        blocked.append(BLOCK_GATE_PREVIEW_SET_ID_MISMATCH)
    # Idempotency key short, when present on the dry run, must agree; a supplied
    # full key must match its short form.
    if (bundle.get("idempotency_key_short")
            and dr.get("idempotency_key_short")
            and dr.get("idempotency_key_short")
            != bundle.get("idempotency_key_short")):
        blocked.append(BLOCK_GATE_IDEMPOTENCY_KEY_MISMATCH)
    if (bundle.get("idempotency_key")
            and _short(bundle.get("idempotency_key"))
            != bundle.get("idempotency_key_short")):
        blocked.append(BLOCK_GATE_IDEMPOTENCY_KEY_MISMATCH)

    # 7. An explicit supervised request id must be present.
    if not bundle.get("supervised_request_id"):
        blocked.append(BLOCK_GATE_REQUEST_ID_MISSING)

    created = not blocked
    outcome = GATE_CANDIDATE_CREATED if created else GATE_BLOCKED
    return _gate_result(
        outcome, blocked=sorted(set(blocked)), created=created,
        forbidden_detected=False, financial_advice=False, bundle=bundle)


def _build_dispatch_authorization_candidate(bundle):
    """Build the local DispatchAuthorizationCandidate (NEVER a dispatch)."""
    b = bundle or {}
    candidate = {
        "candidate_schema": CANDIDATE_SCHEMA,
        "candidate_schema_version": CANDIDATE_SCHEMA_VERSION,
        "supervised_request_id": b.get("supervised_request_id"),
        "operator_id": b.get("operator_id"),
        "outbox_entry_id": b.get("outbox_entry_id"),
        "idempotency_key_short": b.get("idempotency_key_short"),
        "payload_hash_short": b.get("payload_hash_short"),
        "approval_ledger_entry_id": b.get("approval_ledger_entry_id"),
        "review_challenge_id": b.get("review_challenge_id"),
        "editorial_id": b.get("editorial_id"),
        "preview_set_id": b.get("preview_set_id"),
        "idempotency_fingerprint": _idempotency_fingerprint(b),
        # Required hard invariants on the candidate itself.
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "telegram_api_called": False,
        "credential_hydrated": False,
        "llm_behavior": False,
        "scheduler_enabled": False,
        "auto_retry_allowed": False,
        "max_requests_authorized": 1,
        "requires_operator_live_gate": True,
        "valid_for_live_execution": False,
        "candidate_is_provider_authorization": False,
        "candidate_is_live_readiness": False,
    }
    candidate["candidate_checksum"] = compute_checksum(candidate)
    return candidate


def _gate_result(outcome_class, *, blocked, created, forbidden_detected,
                 financial_advice, bundle):
    """Build a deterministic OneRequestDispatchGateResult (pure value)."""
    status = (Status.PASS if created
              else (Status.FAIL_CLOSED
                    if (forbidden_detected or financial_advice)
                    else Status.BLOCKED))
    b = bundle or {}
    candidate = _build_dispatch_authorization_candidate(b) if created else None
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "dispatch_gate_schema": DISPATCH_GATE_SCHEMA,
        "dispatch_gate_schema_version": DISPATCH_GATE_SCHEMA_VERSION,
        "status": status,
        "dispatch_gate_outcome_class": outcome_class,
        "candidate_created_not_dispatched": created,
        "supervised_request_id": b.get("supervised_request_id"),
        "operator_id": b.get("operator_id"),
        # Deep-binding identity fields re-asserted from the bundle.
        "outbox_entry_id": b.get("outbox_entry_id"),
        "idempotency_key_short": b.get("idempotency_key_short"),
        "payload_hash_short": b.get("payload_hash_short"),
        "approval_ledger_entry_id": b.get("approval_ledger_entry_id"),
        "review_challenge_id": b.get("review_challenge_id"),
        "editorial_id": b.get("editorial_id"),
        "preview_set_id": b.get("preview_set_id"),
        "idempotency_fingerprint": _idempotency_fingerprint(b),
        "dispatch_authorization_candidate": candidate,
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        "financial_advice_detected": financial_advice,
        # Hard invariants -- the gate is NEVER dispatch / live.
        **_safety_flags(),
        "max_requests_authorized": 1 if created else 0,
        "requires_operator_live_gate": True,
        "valid_for_live_execution": False,
        "gate_is_dispatch": False,
        "gate_is_provider_authorization": False,
        "gate_is_live_readiness": False,
    }
    result["dispatch_gate_checksum"] = compute_checksum(result)
    return result


# --------------------------------------------------------------------------- #
# RedactedImmutableDispatchAudit
# --------------------------------------------------------------------------- #
def build_redacted_immutable_dispatch_audit(gate_result,
                                            kill_switch_evaluation=None,
                                            rate_spend_retry_evaluation=None):
    """Build a redacted, immutable, checksum-bound dispatch audit.

    Contains symbolic ids, short hashes, policy snapshot ids, blocked reasons,
    and safety flags ONLY -- never raw content, credentials, chat ids,
    usernames, tokens, webhook urls, provider responses, account ids, cookies,
    headers, or browser material. Append-only registry compatible.
    """
    gr = gate_result or {}
    ks = kill_switch_evaluation or {}
    rp = rate_spend_retry_evaluation or {}
    audit = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "audit_schema": AUDIT_SCHEMA,
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "audit_kind": "redacted_immutable_dispatch_audit",
        "status": gr.get("status"),
        "dispatch_gate_outcome_class": gr.get("dispatch_gate_outcome_class"),
        "candidate_created_not_dispatched":
            gr.get("candidate_created_not_dispatched"),
        "supervised_request_id": gr.get("supervised_request_id"),
        "operator_id": gr.get("operator_id"),
        "outbox_entry_id": gr.get("outbox_entry_id"),
        "idempotency_key_short": gr.get("idempotency_key_short"),
        "payload_hash_short": gr.get("payload_hash_short"),
        "approval_ledger_entry_id": gr.get("approval_ledger_entry_id"),
        "review_challenge_id": gr.get("review_challenge_id"),
        "editorial_id": gr.get("editorial_id"),
        "preview_set_id": gr.get("preview_set_id"),
        "idempotency_fingerprint": gr.get("idempotency_fingerprint"),
        "kill_switch_outcome_class": ks.get("kill_switch_outcome_class"),
        "kill_switch_state": ks.get("kill_switch_state"),
        "kill_switch_policy_snapshot_id": ks.get("policy_snapshot_id"),
        "rate_spend_retry_outcome_class":
            rp.get("rate_spend_retry_outcome_class"),
        "rate_policy_snapshot_id": rp.get("policy_snapshot_id"),
        "blocked_reasons": gr.get("blocked_reasons", []),
        "max_requests_authorized": gr.get("max_requests_authorized", 0),
        "requires_operator_live_gate": True,
        "valid_for_live_execution": False,
        **_safety_flags(),
        "no_raw_credential_stored": True,
        "no_raw_provider_or_platform_response_stored": True,
        "no_chat_id_or_username_stored": True,
        "no_webhook_url_stored": True,
        "no_request_headers_or_cookies_stored": True,
    }
    audit["audit_checksum"] = compute_checksum(audit)
    return audit


# --------------------------------------------------------------------------- #
# DispatchGateRegistry
# --------------------------------------------------------------------------- #
class DispatchGateRegistry:
    """Append-only registry of LOCAL dispatch authorization candidates.

    Suppresses duplicate supervised request ids AND duplicate idempotency
    fingerprints deterministically. A given request id or fingerprint yields at
    most ONE appended candidate; a repeat submission appends NOTHING and returns
    a deterministic duplicate-suppressed result. Nothing is mutated in place,
    and the registry NEVER dispatches.
    """

    def __init__(self):
        self._candidates = []          # append-only candidate audits
        self._by_request_id = {}       # supervised_request_id -> index
        self._by_fingerprint = {}      # idempotency_fingerprint -> index

    def _copy(self, obj):
        return json.loads(json.dumps(obj))

    def has_request_id(self, request_id):
        return request_id in self._by_request_id

    def has_fingerprint(self, fingerprint):
        return fingerprint in self._by_fingerprint

    def submit(self, gate_result, kill_switch_evaluation=None,
               rate_spend_retry_evaluation=None):
        """Append a local candidate audit, or suppress a duplicate.

        Raises ValueError when the gate result did not create a candidate
        (fail-closed). On a fresh request id + fingerprint, appends a redacted
        immutable audit and reports appended. On a duplicate request id or
        fingerprint, appends NOTHING and reports the suppression class.
        """
        gr = gate_result or {}
        if gr.get("dispatch_gate_outcome_class") != GATE_CANDIDATE_CREATED:
            raise ValueError(
                "cannot submit: gate result did not create a candidate")
        request_id = gr.get("supervised_request_id")
        fingerprint = gr.get("idempotency_fingerprint")
        if not request_id:
            raise ValueError("cannot submit: missing supervised request id")
        if not fingerprint:
            raise ValueError("cannot submit: missing idempotency fingerprint")

        if request_id in self._by_request_id:
            existing = self._candidates[self._by_request_id[request_id]]
            return {
                "task_label": TASK_LABEL,
                "model": MODEL,
                "model_version": MODEL_VERSION,
                "status": Status.PASS,
                "registry_outcome_class": GATE_REGISTRY_DUPLICATE_REQUEST_ID,
                "duplicate_suppressed": True,
                "appended": False,
                "supervised_request_id": request_id,
                "idempotency_fingerprint": fingerprint,
                "existing_audit_checksum": existing.get("audit_checksum"),
                **_safety_flags(),
            }
        if fingerprint in self._by_fingerprint:
            existing = self._candidates[self._by_fingerprint[fingerprint]]
            return {
                "task_label": TASK_LABEL,
                "model": MODEL,
                "model_version": MODEL_VERSION,
                "status": Status.PASS,
                "registry_outcome_class": GATE_REGISTRY_DUPLICATE_FINGERPRINT,
                "duplicate_suppressed": True,
                "appended": False,
                "supervised_request_id": request_id,
                "idempotency_fingerprint": fingerprint,
                "existing_audit_checksum": existing.get("audit_checksum"),
                **_safety_flags(),
            }

        audit = build_redacted_immutable_dispatch_audit(
            gr, kill_switch_evaluation, rate_spend_retry_evaluation)
        index = len(self._candidates)
        self._candidates.append(self._copy(audit))
        self._by_request_id[request_id] = index
        self._by_fingerprint[fingerprint] = index
        return {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": Status.PASS,
            "registry_outcome_class": GATE_REGISTRY_APPENDED,
            "duplicate_suppressed": False,
            "appended": True,
            "supervised_request_id": request_id,
            "idempotency_fingerprint": fingerprint,
            "audit": self._copy(audit),
            "audit_checksum": audit.get("audit_checksum"),
            **_safety_flags(),
        }

    @property
    def candidates(self):
        return self._copy(self._candidates)

    def candidate_count(self):
        return len(self._candidates)


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
        "kill_switch_schema": KILL_SWITCH_SCHEMA,
        "kill_switch_schema_version": KILL_SWITCH_SCHEMA_VERSION,
        "rate_policy_schema": RATE_POLICY_SCHEMA,
        "rate_policy_schema_version": RATE_POLICY_SCHEMA_VERSION,
        "dispatch_gate_schema": DISPATCH_GATE_SCHEMA,
        "dispatch_gate_schema_version": DISPATCH_GATE_SCHEMA_VERSION,
        "candidate_schema": CANDIDATE_SCHEMA,
        "candidate_schema_version": CANDIDATE_SCHEMA_VERSION,
        "audit_schema": AUDIT_SCHEMA,
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "known_kill_switch_states": sorted(KNOWN_KILL_SWITCH_STATES),
        "disabled_kill_switch_states": sorted(DISABLED_KILL_SWITCH_STATES),
        "kill_switch_outcome_classes": [
            KILL_SWITCH_CLEAR_NOT_DISPATCH,
            KILL_SWITCH_ENGAGED_BLOCKS,
            KILL_SWITCH_FAIL_CLOSED,
        ],
        "rate_spend_retry_outcome_classes": [
            RATE_POLICY_CLEAR,
            RATE_POLICY_BLOCKED,
            RATE_POLICY_FAIL_CLOSED,
        ],
        "dispatch_gate_outcome_classes": [
            GATE_CANDIDATE_CREATED,
            GATE_BLOCKED,
            GATE_FAIL_CLOSED,
        ],
        "registry_outcome_classes": [
            GATE_REGISTRY_APPENDED,
            GATE_REGISTRY_DUPLICATE_REQUEST_ID,
            GATE_REGISTRY_DUPLICATE_FINGERPRINT,
        ],
        "r1_upstream_revalidation_blocked_reasons": [
            BLOCK_GATE_DRY_RUN_UNSAFE_BEHAVIOR,
            BLOCK_GATE_KILL_SWITCH_UNSAFE_BEHAVIOR,
            BLOCK_GATE_RATE_POLICY_UNSAFE_BEHAVIOR,
        ],
        "r1_revalidated_unsafe_flags": list(
            _UNSAFE_BEHAVIOR_FLAGS + _UNSAFE_READINESS_FLAGS),
        "rate_spend_retry_policy_invariants": [
            "max_requests_per_gate_equals_1",
            "auto_retry_allowed_false",
            "scheduler_enabled_false",
            "rate_limit_window_symbolic_only",
            "spend_limit_symbolic_only",
            "provider_budget_not_hydrated",
            "credential_not_hydrated",
            "no_backoff_loop",
            "no_queue_worker",
            "no_scheduled_retry",
            "operator_reapproval_required_after_failure",
        ],
        "deep_bind_fields": list(_DEEP_BIND_FIELDS),
        "hard_invariants": [
            "kill_switch_clear_required_but_not_sufficient",
            "rate_spend_retry_clear_required_but_not_sufficient",
            "dry_run_complete_required_but_not_sufficient",
            "one_request_candidate_is_not_dispatch",
            "candidate_cannot_be_live_executable",
            "operator_owned_live_gate_remains_future_separate_task",
            "registry_suppresses_duplicate_request_id_and_fingerprint",
            # R1 upstream safety-flag revalidation invariants.
            "dispatch_gate_revalidates_upstream_safety_flags",
            "kill_switch_clear_metadata_cannot_hide_unsafe_behavior",
            "rate_policy_clear_metadata_cannot_hide_retry_or_scheduler_behavior",
            "dry_run_complete_metadata_cannot_hide_network_or_live_behavior",
            "unsafe_upstream_behavior_claim_blocks_candidate",
            "no_credential_hydration",
            "no_platform_api",
            "no_telegram_send",
            "no_network",
            "no_scheduler",
            "no_retries",
            "no_autonomous_posting",
            "no_financial_advice_or_signal_framing",
            "missing_ambiguous_or_stale_authority_blocks",
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
    states = "\n".join(
        f"  * `{s}`" for s in sorted(KNOWN_KILL_SWITCH_STATES))
    invariants = "\n".join(
        f"  * `{inv}`"
        for inv in packet["rate_spend_retry_policy_invariants"])
    hard = "\n".join(f"  * `{inv}`" for inv in packet["hard_invariants"])
    r1_reasons = "\n".join(
        f"  * `{r}`"
        for r in packet["r1_upstream_revalidation_blocked_reasons"])
    return (
        f"# 0174TM/TN/TO Kill Switch + Rate Policy + One-Request Dispatch Gate\n\n"
        f"Task: `{TASK_LABEL}`\n\n"
        f"Model: `{MODEL}` version `{MODEL_VERSION}`\n\n"
        f"Baseline commit: `{SOURCE_BASELINE_COMMIT}`\n\n"
        f"## Role\n\n"
        f"This batch is LOCAL and deterministic. It performs NO live platform "
        f"API call, NO Telegram send, NO LLM/provider call, NO network, NO "
        f"env/credential read, NO credential hydration, NO scheduler, and NO "
        f"auto retry. It NEVER dispatches.\n\n"
        f"## 0174TM Kill switch\n\n"
        f"Fail-closed by default: only an explicit `kill_switch_clear` state "
        f"with a fresh policy snapshot is clear. Recognised states:\n\n"
        f"{states}\n\n"
        f"## 0174TN Rate / spend / retry policy\n\n"
        f"The only clear outcome is "
        f"`{RATE_POLICY_CLEAR}`. Required invariants:\n\n{invariants}\n\n"
        f"## 0174TO One-request supervised dispatch gate\n\n"
        f"Requires a complete dry run, a clear kill switch, a clear rate "
        f"policy, the full deep cross-binding, and an explicit supervised "
        f"request id. It produces a local "
        f"`DispatchAuthorizationCandidate` (`{GATE_CANDIDATE_CREATED}`) that "
        f"is NEVER live-executable and always `requires_operator_live_gate`. "
        f"A registry suppresses duplicate request ids and idempotency "
        f"fingerprints.\n\n"
        f"## R1 upstream safety-flag revalidation\n\n"
        f"The gate re-derives upstream safety truth directly from the flags on "
        f"the dry run, kill switch evaluation, and rate/spend/retry evaluation. "
        f"A `pass`/`clear` status can NOT hide a tampered claim of "
        f"network/platform/Telegram/credential/LLM/scheduler/retry/dispatch or "
        f"live-readiness behavior; any such claim blocks the candidate:\n\n"
        f"{r1_reasons}\n\n"
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
