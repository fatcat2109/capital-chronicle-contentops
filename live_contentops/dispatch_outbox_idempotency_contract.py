"""Dispatch outbox + idempotency + preflight contract (0174EE).

This module is the platform-agnostic, deterministic, LOCAL authority layer that
turns an EXACT, validated 0174ED approval into a single local dispatch-outbox
candidate WITHOUT any risk of duplicate dispatch -- BEFORE any future Telegram
remote review, LLM intent parsing, platform preview integration, or supervised
live dispatch is even considered.

0174ED proved "Jim approved this exact payload hash."
0174EE proves "this exact approved payload can be represented as a single local
outbox candidate without duplicate dispatch risk."

This is NOT live-ready. It NEVER sends anything. It consumes 0174ED outputs
(it does not bypass them) and only creates LOCAL records.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Pure Python stdlib only. No requests/httpx/aiohttp, no urllib request
    clients, no socket/ssl/http server, no selenium/playwright, no
    dotenv/keyring/sqlite, no openai/anthropic/telegram/tweepy SDKs.
  * NO network call of any kind.
  * NO env / .env / keyring / browser-session / credential-file read.
  * NO OAuth, token exchange/refresh, credential hydration.
  * NO live posting, dispatch, mutation, scheduling, scraping, replies, DMs.
  * NO auto retry loop.
  * Every result reports ``dispatch_performed = False``,
    ``live_request_performed = False``, ``platform_api_called = False``,
    ``credential_hydrated = False``, ``auto_retry_allowed = False``,
    ``scheduler_enabled = False``, ``telegram_behavior = False``,
    ``llm_behavior = False``.
  * The idempotency key is computed over NON-SECRET, authority-bearing fields
    only. Raw credential/token/api-key/env values are rejected by a fail-closed
    redaction scanner and never hashed, prefixed, suffixed, fingerprinted, or
    logged.
  * Fail-closed: missing required gate input => blocked. Readiness is NEVER
    inferred from the mere absence of blockers.

Importing this module performs NO writes and NO side effects. Artifacts are
written ONLY when ``write_artifacts(...)`` is called explicitly.
"""

import hashlib
import json
import os.path
import re

# 0174ED is the upstream authority layer. 0174EE consumes its outputs.
from live_contentops import approval_ledger_payload_hash_contract as approval

TASK_LABEL = (
    "TASK_CONTENTOPS_0174EE_DISPATCH_OUTBOX_IDEMPOTENCY_AND_PREFLIGHT_"
    "CONTRACT_BATCH_V0"
)
MODEL = "DISPATCH_OUTBOX_IDEMPOTENCY_CONTRACT_0174EE"
MODEL_VERSION = "0174EE_DISPATCH_OUTBOX_IDEMPOTENCY_V1"
# Schema/version constants mixed into the deterministic idempotency key.
OUTBOX_SCHEMA = "contentops.dispatch_outbox_candidate"
OUTBOX_SCHEMA_VERSION = "0174EE_OUTBOX_IDEMPOTENCY_V1"
SOURCE_BASELINE_COMMIT = "b07848e61fef10917a38e344743f00a9de655cbb"

# Output artifact locations (written ONLY by the explicit write helper).
DOC_REL_DIR = os.path.join("docs", "automation", "0174EE")
PACKET_FILENAME = "dispatch_outbox_idempotency_contract_packet.json"
DOC_FILENAME = "dispatch_outbox_idempotency_contract.md"

NEXT_REQUIRED_GATE = (
    "Telegram remote operator inbox contract (deterministic local message "
    "intake model only; no bot polling, no getUpdates, no send, no webhook), "
    "then LLM intent parser contract, Telegram review challenge contract, "
    "editorial agent, platform preview integration, and end-to-end dry run "
    "before any supervised live dispatch gate; credential hydration and live "
    "platform dispatch remain separate future operator-owned gates and are NOT "
    "enabled here"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174TG_TELEGRAM_REMOTE_OPERATOR_INBOX_CONTRACT_V0"
)


# --------------------------------------------------------------------------- #
# Status vocabularies (symbolic only)
# --------------------------------------------------------------------------- #
class OutboxStatus:
    PASS = "pass"
    BLOCKED = "blocked"
    FAIL_CLOSED = "fail_closed"


# Outbox preflight / candidacy classes.
OUTBOX_ELIGIBLE = "eligible_for_local_outbox"
OUTBOX_NOT_ELIGIBLE = "not_eligible_for_local_outbox"
OUTBOX_FAIL_CLOSED = "outbox_fail_closed_forbidden_value"

# Outbox entry state classes.
STATE_LOCAL_RECORD_CREATED = "local_outbox_record_created_not_dispatched"
STATE_DUPLICATE_SUPPRESSED = "duplicate_idempotency_key_suppressed"

# Dispatch intent classes (symbolic only).
INTENT_SUPERVISED_SINGLE = "supervised_single_dispatch_candidate"
INTENT_DRY_RUN = "dry_run_candidate"

# Gate snapshot classes (symbolic only). Only an explicit "allows local outbox
# candidacy" class permits a local record; anything else (or missing) blocks.
GATE_ALLOWS_LOCAL_OUTBOX = "kill_switch_clear_allows_local_outbox_candidacy"
GATE_BLOCKS_OUTBOX = "kill_switch_engaged_blocks_outbox"

# The exact ordered list of authority-bearing inputs to the idempotency key.
IDEMPOTENCY_KEY_INPUTS = (
    "outbox_schema",
    "outbox_schema_version",
    "payload_hash",
    "platform",
    "destination_binding_id",
    "credential_handle_id",
    "media_manifest_hash",
    "visibility_class",
    "dispatch_intent_class",
    "content_lane",
    "policy_snapshot_id",
    "platform_adapter_version",
    "approval_ledger_entry_id",
    "challenge_id",
    "operator_id",
)

# Fields that MUST NEVER feed the idempotency key or be persisted.
IDEMPOTENCY_KEY_EXCLUDES = (
    "raw_credential",
    "raw_token",
    "api_key",
    "access_token",
    "refresh_token",
    "bearer_token",
    "client_secret",
    "raw_env_var",
    "dotenv_value",
    "secret_path",
    "raw_provider_response",
    "raw_platform_response",
    "raw_sensitive_account_id",
    "request_headers",
    "cookies",
    "browser_session_data",
    "local_absolute_path_if_sensitive",
)

# Symbolic preflight blocked-reason classes.
BLOCK_APPROVAL_NOT_PASS = "approval_validation_not_pass"
BLOCK_VALIDITY_NOT_CANDIDATE = "approval_validity_class_not_outbox_candidate"
BLOCK_HASH_MISMATCH = "payload_hash_mismatch"
BLOCK_BINDING_MISMATCH = "binding_mismatch"
BLOCK_EXPIRED = "approval_expired"
BLOCK_REVOKED = "approval_revoked"
BLOCK_CREDENTIAL_NOT_SYMBOLIC = "credential_not_symbolic"
BLOCK_GATE_SNAPSHOT_BLOCKS = "gate_snapshot_blocks_outbox"
BLOCK_GATE_SNAPSHOT_MISSING = "gate_snapshot_missing"
BLOCK_DUPLICATE_KEY = "duplicate_idempotency_key"
BLOCK_FORBIDDEN_VALUE = "forbidden_value_detected"
BLOCK_LIVE_NOT_ALLOWED = "live_dispatch_not_allowed_in_0174EE"
BLOCK_MISSING_VALIDATION = "approval_validation_missing"
BLOCK_MISSING_FIELD = "required_field_missing"
BLOCK_DISPATCH_FLAG_SET = "upstream_dispatch_or_live_flag_set"
# R1 authority-chain hardening: the preflight recomputes the current payload
# hash and proves the supplied validation result + approval entry all agree.
BLOCK_VALIDATION_HASH_MISMATCH_CURRENT = (
    "validation_payload_hash_mismatch_current_payload")
BLOCK_VALIDATION_APPROVED_HASH_MISMATCH_ENTRY = (
    "validation_approved_hash_mismatch_entry")
BLOCK_VALIDATION_ENTRY_MISMATCH = "validation_entry_mismatch"
BLOCK_VALIDATION_CHALLENGE_MISMATCH = "validation_challenge_mismatch"

# Required authority fields that must be present (non-empty) on a candidate.
REQUIRED_CANDIDATE_FIELDS = (
    "payload_hash",
    "platform",
    "destination_binding_id",
    "credential_handle_id",
    "media_manifest_hash",
    "visibility_class",
    "dispatch_intent_class",
    "policy_snapshot_id",
    "platform_adapter_version",
    "approval_ledger_entry_id",
)

# Binding fields that must match between approval entry, validation, and the
# candidate.
_BINDING_FIELDS = (
    "platform",
    "destination_binding_id",
    "credential_handle_id",
    "media_manifest_hash",
    "visibility_class",
)


# --------------------------------------------------------------------------- #
# Redaction: reuse the 0174ED scanner family (single source of truth).
# --------------------------------------------------------------------------- #
def scan_for_leaks(obj):
    """Return a sorted list of redaction violations (delegates to 0174ED)."""
    return approval.scan_for_leaks(obj)


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


# A symbolic credential handle id is a 0174EC-style sha256 hex digest (64 hex
# chars) or another clearly non-secret short class label. A value that trips the
# redaction scanner, or that is not a clean hex digest / safe label, is treated
# as "not symbolic" and blocks the outbox fail-closed.
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_HEX_ANY = re.compile(r"^[0-9a-f]{16,64}$")


def _is_symbolic_credential_handle(handle_id):
    """True if the credential handle id is symbolic (never a raw secret)."""
    if not isinstance(handle_id, str) or not handle_id:
        return False
    if scan_for_leaks(handle_id):
        return False
    if _HEX64.match(handle_id) or _HEX_ANY.match(handle_id):
        return True
    # Allow short, clearly-symbolic class labels (letters/digits/underscore),
    # but reject anything secret-shaped (caught above by the scanner).
    return bool(re.match(r"^[A-Za-z0-9_]{1,64}$", handle_id))


# --------------------------------------------------------------------------- #
# DispatchOutboxCandidate
# --------------------------------------------------------------------------- #
def build_outbox_candidate(current_payload, approval_entry, validation_result,
                           dispatch_intent_class=INTENT_SUPERVISED_SINGLE,
                           gate_snapshot_class=GATE_ALLOWS_LOCAL_OUTBOX,
                           gate_snapshot_id=None, operator_id=None,
                           payload_hash_override=None):
    """Build a deterministic DispatchOutboxCandidate from 0174ED outputs.

    Pulls authority-bearing fields from the CURRENT payload and the approval
    validation result. A credential is represented ONLY by its symbolic
    ``credential_handle_id``. No raw payload text, account id, handle, or
    secret material is copied into the candidate.

    R1: when ``payload_hash_override`` is supplied (the hash recomputed locally
    from the current payload by the preflight) it is the authoritative
    ``payload_hash`` -- the externally supplied validation result hash is never
    trusted on its own for the candidate or idempotency key.
    """
    payload = current_payload or {}
    entry = approval_entry or {}
    vres = validation_result or {}
    return {
        "outbox_schema": OUTBOX_SCHEMA,
        "outbox_schema_version": OUTBOX_SCHEMA_VERSION,
        "payload_hash": payload_hash_override or vres.get(
            "current_payload_hash"),
        "platform": payload.get("platform"),
        "destination_binding_id": payload.get("destination_binding_id"),
        "credential_handle_id": payload.get("credential_handle_id"),
        "media_manifest_hash": payload.get("media_manifest_hash"),
        "visibility_class": payload.get("visibility_class"),
        "content_lane": payload.get("content_lane"),
        "dispatch_intent_class": dispatch_intent_class,
        "policy_snapshot_id": gate_snapshot_id,
        "platform_adapter_version": payload.get("platform_adapter_version"),
        "approval_ledger_entry_id": entry.get("ledger_entry_id"),
        "challenge_id": entry.get("challenge_id"),
        "operator_id": operator_id or entry.get("operator_id"),
        "gate_snapshot_class": gate_snapshot_class,
    }


# --------------------------------------------------------------------------- #
# Idempotency key
# --------------------------------------------------------------------------- #
def compute_idempotency_key(candidate):
    """Deterministic sha256 over the non-secret authority-bearing fields only.

    Any authority-bearing change (payload hash, platform, destination binding,
    credential handle, media manifest hash, visibility, dispatch intent,
    content lane, policy/gate snapshot, adapter version, approval ledger entry,
    challenge id, operator id) changes the key; incidental extra keys do not.
    Fail-closed: refuses to key a candidate carrying forbidden material.
    """
    violations = scan_for_leaks(candidate)
    if violations:
        raise ValueError(f"candidate failed redaction scan: {violations}")
    keyed = {k: candidate.get(k) for k in IDEMPOTENCY_KEY_INPUTS}
    return hashlib.sha256(serialize(keyed).encode("utf-8")).hexdigest()


def idempotency_key_short(key):
    """Return the first 16 hex chars of an idempotency key (display only)."""
    return _short(key)


# --------------------------------------------------------------------------- #
# DispatchPreflightResult
# --------------------------------------------------------------------------- #
def run_dispatch_preflight(current_payload, approval_entry, validation_result,
                           dispatch_intent_class=INTENT_SUPERVISED_SINGLE,
                           gate_snapshot_class=GATE_ALLOWS_LOCAL_OUTBOX,
                           gate_snapshot_id=None, operator_id=None):
    """Deterministically decide whether a local outbox record may be created.

    Fail-closed and non-side-effecting. Readiness is NEVER inferred from the
    mere absence of blockers: every required field + gate input must be present
    and the 0174ED validation must explicitly PASS as an outbox candidate.
    NEVER authorizes dispatch: ``dispatch_performed`` etc. are always False.
    """
    blocked = []
    status = OutboxStatus.PASS

    payload = current_payload or {}
    entry = approval_entry or {}
    vres = validation_result

    # 1. Fail-closed redaction scan of all caller-supplied inputs FIRST.
    forbidden = scan_for_leaks([payload, entry, vres or {}, {
        "dispatch_intent_class": dispatch_intent_class,
        "gate_snapshot_class": gate_snapshot_class,
        "gate_snapshot_id": gate_snapshot_id,
        "operator_id": operator_id,
    }])
    forbidden_detected = bool(forbidden)

    candidate = None
    idempotency_key = None
    eligibility = OUTBOX_NOT_ELIGIBLE
    # R1: the trusted current payload hash is ALWAYS recomputed locally from the
    # supplied current_payload -- never read blindly from the validation result.
    computed_current_payload_hash = None

    if forbidden_detected:
        status = OutboxStatus.FAIL_CLOSED
        eligibility = OUTBOX_FAIL_CLOSED
        blocked.append(BLOCK_FORBIDDEN_VALUE)
    else:
        # R1: recompute the current payload hash from the CURRENT payload after
        # redaction passes. This is the single source of truth for the outbox
        # candidate + idempotency key; an externally supplied
        # validation_result["current_payload_hash"] is only cross-checked, never
        # trusted on its own.
        computed_current_payload_hash = approval.compute_payload_hash(payload)

        # 2. Approval validation must be present.
        if not vres:
            blocked.append(BLOCK_MISSING_VALIDATION)
        else:
            # 3. Approval validation must explicitly PASS.
            if vres.get("status") != approval.ApprovalStatus.PASS:
                blocked.append(BLOCK_APPROVAL_NOT_PASS)
            # 4. Validity class must be the outbox-candidate class.
            if (vres.get("approval_validity_class")
                    != approval.APPROVAL_VALID_CANDIDATE):
                blocked.append(BLOCK_VALIDITY_NOT_CANDIDATE)
            # 5. Hash match.
            if vres.get("payload_hash_match") is not True:
                blocked.append(BLOCK_HASH_MISMATCH)
            # 6. Binding match.
            if vres.get("binding_match") is not True:
                blocked.append(BLOCK_BINDING_MISMATCH)
            # 7. Not expired.
            if vres.get("expired") is not False:
                blocked.append(BLOCK_EXPIRED)
            # 8. Not revoked.
            if vres.get("revoked") is not False:
                blocked.append(BLOCK_REVOKED)
            # 9. Upstream must NOT claim dispatch/live readiness.
            if (vres.get("dispatch_ready") is not False
                    or vres.get("live_ready") is not False
                    or vres.get("approval_authorizes_dispatch") is not False):
                blocked.append(BLOCK_DISPATCH_FLAG_SET)

            # R1 AUTHORITY-CHAIN HARDENING: prove the supplied validation result
            # + approval entry all bind the SAME recomputed current payload.
            # A stale/foreign validation result for payload A must not be paired
            # with a substituted payload B.
            # (a) recomputed current hash must equal the validation's claimed
            #     current_payload_hash.
            if vres.get("current_payload_hash") != computed_current_payload_hash:
                blocked.append(BLOCK_VALIDATION_HASH_MISMATCH_CURRENT)
            # (b) recomputed current hash must equal the approval entry hash.
            if entry.get("payload_hash") != computed_current_payload_hash:
                blocked.append(BLOCK_VALIDATION_HASH_MISMATCH_CURRENT)
            # (c) validation approved hash must equal the approval entry hash.
            if vres.get("approved_payload_hash") != entry.get("payload_hash"):
                blocked.append(BLOCK_VALIDATION_APPROVED_HASH_MISMATCH_ENTRY)
            # (d) validation must reference the same ledger entry id.
            if vres.get("ledger_entry_id") != entry.get("ledger_entry_id"):
                blocked.append(BLOCK_VALIDATION_ENTRY_MISMATCH)
            # (e) validation must reference the same challenge id.
            if vres.get("challenge_id") != entry.get("challenge_id"):
                blocked.append(BLOCK_VALIDATION_CHALLENGE_MISMATCH)

        # 10. Required authority fields present (non-empty).
        for field in REQUIRED_CANDIDATE_FIELDS:
            if field == "payload_hash":
                present = bool((vres or {}).get("current_payload_hash"))
            elif field == "policy_snapshot_id":
                present = bool(gate_snapshot_id)
            elif field == "dispatch_intent_class":
                present = bool(dispatch_intent_class)
            elif field == "approval_ledger_entry_id":
                present = bool(entry.get("ledger_entry_id"))
            else:
                present = bool(payload.get(field))
            if not present:
                blocked.append(BLOCK_MISSING_FIELD + ":" + field)

        # 11. Gate snapshot must be present.
        if not gate_snapshot_id:
            blocked.append(BLOCK_GATE_SNAPSHOT_MISSING)
        # 12. Gate snapshot class must explicitly allow local outbox candidacy.
        if gate_snapshot_class != GATE_ALLOWS_LOCAL_OUTBOX:
            blocked.append(BLOCK_GATE_SNAPSHOT_BLOCKS)

        # 13. Credential handle must be symbolic only.
        if not _is_symbolic_credential_handle(payload.get(
                "credential_handle_id")):
            blocked.append(BLOCK_CREDENTIAL_NOT_SYMBOLIC)

        # 14. Cross-check binding fields between approval entry and payload.
        for field in _BINDING_FIELDS:
            if entry and entry.get(field) != payload.get(field):
                reason = BLOCK_BINDING_MISMATCH + ":" + field
                if reason not in blocked:
                    blocked.append(reason)

        if blocked:
            status = OutboxStatus.BLOCKED
            eligibility = OUTBOX_NOT_ELIGIBLE
        else:
            status = OutboxStatus.PASS
            eligibility = OUTBOX_ELIGIBLE
            candidate = build_outbox_candidate(
                payload, entry, vres,
                dispatch_intent_class=dispatch_intent_class,
                gate_snapshot_class=gate_snapshot_class,
                gate_snapshot_id=gate_snapshot_id, operator_id=operator_id,
                payload_hash_override=computed_current_payload_hash)
            idempotency_key = compute_idempotency_key(candidate)

    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": status,
        "outbox_eligibility_class": eligibility,
        "platform": payload.get("platform"),
        "approval_ledger_entry_id": entry.get("ledger_entry_id"),
        "challenge_id": entry.get("challenge_id"),
        "approved_payload_hash": (vres or {}).get("approved_payload_hash"),
        "current_payload_hash": (
            computed_current_payload_hash
            if computed_current_payload_hash is not None
            else (vres or {}).get("current_payload_hash")),
        "idempotency_key": idempotency_key,
        "idempotency_key_short": (
            idempotency_key_short(idempotency_key) if idempotency_key else None),
        "candidate": candidate,
        "blocked_reasons": sorted(set(blocked)),
        "forbidden_fields_detected": forbidden_detected,
        "redaction_verified": not forbidden_detected,
        # Hard safety invariants -- ALWAYS these values in 0174EE.
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
        "scheduler_enabled": False,
        "telegram_behavior": False,
        "llm_behavior": False,
        "dispatch_ready": False,
        "live_ready": False,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }


# --------------------------------------------------------------------------- #
# DispatchOutboxEntry
# --------------------------------------------------------------------------- #
def build_outbox_entry(preflight_result, outbox_entry_id, created_at_epoch):
    """Build an append-ready local outbox entry from a PASSED preflight result.

    Raises ValueError if the preflight did not pass (fail-closed). The entry
    carries only symbolic/hashed authority fields -- never raw payload text,
    account ids, handles, provider responses, headers, cookies, or secrets.
    """
    if (preflight_result or {}).get("status") != OutboxStatus.PASS:
        raise ValueError("cannot build outbox entry: preflight did not pass")
    cand = (preflight_result or {}).get("candidate") or {}
    idempotency_key = preflight_result.get("idempotency_key")
    payload_hash = preflight_result.get("current_payload_hash")
    entry = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "outbox_entry_id": outbox_entry_id,
        "idempotency_key": idempotency_key,
        "idempotency_key_short": idempotency_key_short(idempotency_key),
        "payload_hash": payload_hash,
        "payload_hash_short": _short(payload_hash),
        "approval_ledger_entry_id": cand.get("approval_ledger_entry_id"),
        "challenge_id": cand.get("challenge_id"),
        "operator_id": cand.get("operator_id"),
        "platform": cand.get("platform"),
        "destination_binding_id": cand.get("destination_binding_id"),
        "credential_handle_id": cand.get("credential_handle_id"),
        "media_manifest_hash": cand.get("media_manifest_hash"),
        "visibility_class": cand.get("visibility_class"),
        "content_lane": cand.get("content_lane"),
        "dispatch_intent_class": cand.get("dispatch_intent_class"),
        "policy_snapshot_id": cand.get("policy_snapshot_id"),
        "platform_adapter_version": cand.get("platform_adapter_version"),
        "gate_snapshot_class": cand.get("gate_snapshot_class"),
        "created_at_epoch": int(created_at_epoch),
        "state_class": STATE_LOCAL_RECORD_CREATED,
        # Hard safety invariants -- ALWAYS these values.
        "outbox_created": True,
        "eligible_for_local_outbox": True,
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
        "scheduler_enabled": False,
        "telegram_behavior": False,
        "llm_behavior": False,
        "dispatch_ready": False,
        "live_ready": False,
    }
    entry["audit_checksum"] = compute_checksum(entry)
    return entry


# --------------------------------------------------------------------------- #
# DispatchIdempotencyRecord + DispatchOutboxRegistry
# --------------------------------------------------------------------------- #
def build_idempotency_record(idempotency_key, outbox_entry_id,
                             created_at_epoch):
    """Build a pure-value idempotency record (key -> first outbox entry)."""
    return {
        "fact_kind": "dispatch_idempotency_record",
        "idempotency_key": idempotency_key,
        "idempotency_key_short": idempotency_key_short(idempotency_key),
        "outbox_entry_id": outbox_entry_id,
        "created_at_epoch": int(created_at_epoch),
    }


class DispatchOutboxRegistry:
    """An append-only registry that enforces idempotency-key uniqueness.

    A given idempotency key may have at most ONE active outbox entry. A repeat
    request with the same key returns a deterministic duplicate-suppressed
    result and does NOT append a second entry. Nothing is mutated in place.
    """

    def __init__(self):
        self._entries = []          # append-only outbox entries
        self._by_key = {}           # idempotency_key -> outbox_entry_id
        self._idempotency = []      # append-only idempotency records

    def _copy(self, obj):
        return json.loads(json.dumps(obj))

    def has_key(self, idempotency_key):
        return idempotency_key in self._by_key

    def submit(self, preflight_result, outbox_entry_id, created_at_epoch):
        """Create a local outbox entry, or suppress a duplicate.

        Returns a deterministic result dict. On a fresh key, appends a new
        outbox entry + idempotency record and reports
        ``local_outbox_record_created_not_dispatched``. On a duplicate key,
        appends NOTHING and reports ``duplicate_idempotency_key_suppressed``
        with the existing entry id.
        """
        if (preflight_result or {}).get("status") != OutboxStatus.PASS:
            raise ValueError("cannot submit: preflight did not pass")
        key = preflight_result.get("idempotency_key")
        if not key:
            raise ValueError("cannot submit: missing idempotency key")

        if key in self._by_key:
            existing_id = self._by_key[key]
            return {
                "task_label": TASK_LABEL,
                "model": MODEL,
                "model_version": MODEL_VERSION,
                "status": OutboxStatus.PASS,
                "state_class": STATE_DUPLICATE_SUPPRESSED,
                "duplicate_suppressed": True,
                "idempotency_key": key,
                "idempotency_key_short": idempotency_key_short(key),
                "outbox_entry_id": existing_id,
                "appended": False,
                "blocked_reasons": [BLOCK_DUPLICATE_KEY],
                "dispatch_performed": False,
                "live_request_performed": False,
                "platform_api_called": False,
                "credential_hydrated": False,
                "auto_retry_allowed": False,
                "scheduler_enabled": False,
                "telegram_behavior": False,
                "llm_behavior": False,
            }

        entry = build_outbox_entry(preflight_result, outbox_entry_id,
                                   created_at_epoch)
        self._entries.append(self._copy(entry))
        self._by_key[key] = outbox_entry_id
        self._idempotency.append(self._copy(build_idempotency_record(
            key, outbox_entry_id, created_at_epoch)))
        return {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": OutboxStatus.PASS,
            "state_class": STATE_LOCAL_RECORD_CREATED,
            "duplicate_suppressed": False,
            "idempotency_key": key,
            "idempotency_key_short": idempotency_key_short(key),
            "outbox_entry_id": outbox_entry_id,
            "appended": True,
            "entry": self._copy(entry),
            "blocked_reasons": [],
            "dispatch_performed": False,
            "live_request_performed": False,
            "platform_api_called": False,
            "credential_hydrated": False,
            "auto_retry_allowed": False,
            "scheduler_enabled": False,
            "telegram_behavior": False,
            "llm_behavior": False,
        }

    @property
    def entries(self):
        return self._copy(self._entries)

    @property
    def idempotency_records(self):
        return self._copy(self._idempotency)

    def entry_count(self):
        return len(self._entries)

    def find_by_key(self, idempotency_key):
        eid = self._by_key.get(idempotency_key)
        if eid is None:
            return None
        for e in self._entries:
            if e.get("outbox_entry_id") == eid:
                return self._copy(e)
        return None


# --------------------------------------------------------------------------- #
# RedactedOutboxAudit
# --------------------------------------------------------------------------- #
def build_redacted_outbox_audit(preflight_result, outbox_entry=None):
    """Build a redacted audit summary containing symbolic/redacted values only.

    Stores short hashes (non-secret content fingerprints) and symbolic classes,
    never raw payload text, raw account ids, headers, cookies, provider
    responses, or any credential material.
    """
    pr = preflight_result or {}
    oe = outbox_entry or {}
    audit = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "audit_kind": "redacted_dispatch_outbox_audit",
        "status": pr.get("status"),
        "outbox_eligibility_class": pr.get("outbox_eligibility_class"),
        "platform": pr.get("platform"),
        "approval_ledger_entry_id": pr.get("approval_ledger_entry_id"),
        "challenge_id": pr.get("challenge_id"),
        "idempotency_key_short": pr.get("idempotency_key_short"),
        "payload_hash_short": _short(pr.get("current_payload_hash") or ""),
        "outbox_entry_id": oe.get("outbox_entry_id"),
        "state_class": oe.get("state_class"),
        "blocked_reasons": pr.get("blocked_reasons", []),
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "credential_hydrated": False,
        "auto_retry_allowed": False,
        "scheduler_enabled": False,
        "no_raw_credential_stored": True,
        "no_credential_hash_or_fingerprint_created": True,
        "no_credential_prefix_or_suffix_exposed": True,
        "no_raw_provider_or_platform_response_stored": True,
    }
    audit["audit_checksum"] = compute_checksum(audit)
    return audit


# --------------------------------------------------------------------------- #
# Model packet + doc builders
# --------------------------------------------------------------------------- #
def build_packet():
    """Build the deterministic redacted 0174EE model packet."""
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "outbox_schema": OUTBOX_SCHEMA,
        "outbox_schema_version": OUTBOX_SCHEMA_VERSION,
        "contract_status": "deterministic_local_outbox_authority_ready",
        "idempotency_key_algorithm": "sha256",
        "idempotency_key_inputs": list(IDEMPOTENCY_KEY_INPUTS),
        "idempotency_key_excludes": list(IDEMPOTENCY_KEY_EXCLUDES),
        "outbox_eligibility_classes": [
            OUTBOX_ELIGIBLE, OUTBOX_NOT_ELIGIBLE, OUTBOX_FAIL_CLOSED,
        ],
        "outbox_state_classes": [
            STATE_LOCAL_RECORD_CREATED, STATE_DUPLICATE_SUPPRESSED,
        ],
        "dispatch_intent_classes": [INTENT_SUPERVISED_SINGLE, INTENT_DRY_RUN],
        "gate_snapshot_classes": [GATE_ALLOWS_LOCAL_OUTBOX, GATE_BLOCKS_OUTBOX],
        "blocked_reasons": [
            BLOCK_APPROVAL_NOT_PASS, BLOCK_VALIDITY_NOT_CANDIDATE,
            BLOCK_HASH_MISMATCH, BLOCK_BINDING_MISMATCH, BLOCK_EXPIRED,
            BLOCK_REVOKED, BLOCK_CREDENTIAL_NOT_SYMBOLIC,
            BLOCK_GATE_SNAPSHOT_BLOCKS, BLOCK_GATE_SNAPSHOT_MISSING,
            BLOCK_DUPLICATE_KEY, BLOCK_FORBIDDEN_VALUE, BLOCK_LIVE_NOT_ALLOWED,
            BLOCK_MISSING_VALIDATION, BLOCK_MISSING_FIELD,
            BLOCK_DISPATCH_FLAG_SET,
            BLOCK_VALIDATION_HASH_MISMATCH_CURRENT,
            BLOCK_VALIDATION_APPROVED_HASH_MISMATCH_ENTRY,
            BLOCK_VALIDATION_ENTRY_MISMATCH,
            BLOCK_VALIDATION_CHALLENGE_MISMATCH,
        ],
        "consumes_0174ed_outputs": [
            "current_payload",
            "approval_ledger_entry",
            "approval_validation_result",
            "payload_hash",
        ],
        "invariants": [
            "idempotency_key_deterministic_for_identical_candidate",
            "any_authority_field_change_changes_idempotency_key",
            "outbox_blocked_unless_approval_validation_pass",
            "outbox_blocked_unless_validity_is_outbox_candidate",
            "outbox_blocked_on_hash_or_binding_mismatch",
            "outbox_blocked_on_expired_or_revoked_approval",
            "outbox_blocked_on_missing_validation_or_gate_snapshot",
            "outbox_blocked_on_non_symbolic_credential",
            "duplicate_idempotency_key_suppressed_not_appended",
            "outbox_never_marks_dispatch_or_live_or_platform_api",
            "outbox_never_enables_auto_retry_or_scheduler",
            "readiness_never_inferred_from_absence_of_blockers",
            "approval_valid_for_payload_a_cannot_create_outbox_for_payload_b",
            "audit_contains_redacted_values_only",
            "preflight_recomputes_current_payload_hash_before_outbox",
            "stale_validation_result_cannot_create_outbox",
        ],
        "redaction_policy": {
            "fail_closed_on_forbidden_value": True,
            "credential_referenced_by_handle_id_only": True,
            "no_raw_credential_stored": True,
            "no_raw_provider_or_platform_response_stored": True,
            "no_request_headers_or_cookies_stored": True,
            "scanner_source": "0174ED_approval_ledger_payload_hash_contract",
        },
        "safety_flags": {
            "dispatch_performed": False,
            "live_request_performed": False,
            "platform_api_called": False,
            "credential_hydrated": False,
            "auto_retry_allowed": False,
            "scheduler_enabled": False,
            "telegram_behavior": False,
            "llm_behavior": False,
            "dispatch_ready": False,
            "live_ready": False,
            "autonomous_posting_allowed": False,
            "manual_fallback_available": True,
            "no_network_performed": True,
            "no_env_read_performed": True,
            "no_dotenv_read_performed": True,
            "no_keyring_read_performed": True,
            "no_browser_session_read_performed": True,
            "no_credential_file_read_performed": True,
            "no_oauth_performed": True,
            "no_credential_hydration_performed": True,
            "no_openclaw_runtime": True,
            "no_scheduler_or_posting": True,
        },
        "strategic_posture": {
            "manual_posting": "fallback",
            "automation": "main_build_path",
            "autonomous_posting": "forbidden",
            "supervised_publishing": "final_product",
        },
        "status": OutboxStatus.PASS,
        "next_required_gate": NEXT_REQUIRED_GATE,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
    }
    packet["checksum_sha256"] = compute_checksum(packet)
    return packet


def build_doc():
    """Build the deterministic redacted 0174EE markdown documentation."""
    key_inputs = "\n".join(f"- `{f}`" for f in IDEMPOTENCY_KEY_INPUTS)
    excludes = "\n".join(f"- `{f}`" for f in IDEMPOTENCY_KEY_EXCLUDES)
    return f"""# Dispatch Outbox + Idempotency + Preflight Contract (0174EE)

Task: {TASK_LABEL}
Model: {MODEL} ({MODEL_VERSION})
Source baseline commit: {SOURCE_BASELINE_COMMIT}
Mode: Implementation Mode. Deterministic, stdlib-only, local authority layer.

> [!IMPORTANT]
> This module introduces NO live dispatch, NO posting, NO platform API call, NO
> network call, NO credential read or hydration, NO environment or `.env` read,
> NO keyring or browser-session read, NO OAuth, NO Telegram behavior, NO LLM
> behavior, NO scheduler, and NO auto retry. It is the deterministic local
> dispatch-outbox + idempotency + preflight authority contract only.

## Strategic Posture
- Manual posting is the **fallback** path, not the strategic destination.
- **Automation is the main build path.**
- **Autonomous posting is forbidden.**
- **Supervised publishing is the final product.**

## What This Contract Proves
0174ED proved Jim approved an **exact payload hash**. 0174EE proves that exact,
validated approval can be represented as a **single local outbox candidate**
without duplicate dispatch risk. It consumes 0174ED outputs (current payload,
approval ledger entry, and the `validate_approval_for_current_payload` result);
it does not bypass them. It is still **not live-ready**.

## Idempotency Key Algorithm
- Algorithm: `sha256` over canonical JSON (sorted keys, compact separators).
- Computed over authority-bearing fields ONLY; incidental extra keys never
  affect it. Fail-closed: a candidate carrying forbidden material is refused.

## Idempotency Key Inputs (authority-bearing, non-secret)
{key_inputs}

## Idempotency Key Excludes (never keyed or stored)
{excludes}

A credential is represented ONLY by its symbolic `credential_handle_id` (a
0174EC handle id). No raw token, api key, env value, `.env` value, secret path,
raw provider/platform response, request headers, cookies, browser-session data,
raw sensitive account id, or sensitive local absolute path is ever keyed or
persisted.

## Core Objects
- **DispatchOutboxCandidate** -- canonical authority-bearing candidate built
  from 0174ED outputs (`build_outbox_candidate`).
- **DispatchPreflightResult** -- the fail-closed decision
  (`run_dispatch_preflight`).
- **DispatchOutboxEntry** -- an append-ready local outbox record
  (`build_outbox_entry`); state `{STATE_LOCAL_RECORD_CREATED}`.
- **DispatchIdempotencyRecord** -- key -> first entry record
  (`build_idempotency_record`).
- **DispatchOutboxRegistry** -- append-only registry enforcing idempotency-key
  uniqueness with deterministic duplicate suppression.
- **RedactedOutboxAudit** -- symbolic/redacted audit
  (`build_redacted_outbox_audit`).

## Outbox Creation Is Blocked Unless
1. approval validation status is PASS;
2. approval validity class is `approval_valid_for_payload_not_dispatch`;
3. current payload hash matches the approved hash;
4. binding match is true;
5. expired is false;
6. revoked is false;
7. upstream `dispatch_ready`/`live_ready`/`approval_authorizes_dispatch` are
   false;
8. all required authority fields are present (no inferred readiness);
9. a gate/kill-switch snapshot is present AND symbolically allows local outbox
   candidacy;
10. the credential handle is symbolic only;
11. no forbidden/raw credential-shaped value is present;
12. the idempotency key is not already active (else duplicate suppression
    returns the existing record).

## Invariants
- The idempotency key is deterministic for an identical candidate and changes
  if ANY authority field changes (payload hash, platform, destination binding,
  credential handle, media manifest hash, visibility, dispatch intent, content
  lane, policy/gate snapshot, adapter version, approval ledger entry, challenge
  id, operator id).
- A duplicate idempotency key is **suppressed**, not appended: the registry
  returns the existing entry id and appends nothing.
- Readiness is **never** inferred from the absence of blockers; missing
  validation, missing gate snapshot, or a non-symbolic credential blocks.
- An approval valid for payload A can **never** create an outbox entry for a
  substituted payload B.
- **R1 authority-chain hardening:** the preflight ALWAYS recomputes the current
  payload hash from the supplied current payload
  (`preflight_recomputes_current_payload_hash_before_outbox`) and uses it for
  the candidate + idempotency key. A stale/foreign validation result is rejected
  fail-closed (`stale_validation_result_cannot_create_outbox`) when its
  `current_payload_hash`, `approved_payload_hash`, `ledger_entry_id`, or
  `challenge_id` does not bind the same approval entry + recomputed payload.
- Audit objects contain redacted values only.

## Authority Boundary
Outbox state never implies dispatch-ready or live-ready. Every preflight
result, outbox entry, registry result, and audit reports
`dispatch_performed = False`, `live_request_performed = False`,
`platform_api_called = False`, `credential_hydrated = False`,
`auto_retry_allowed = False`, and `scheduler_enabled = False`.

## Next Task
Recommended next task after PASS:
`{EXACT_NEXT_TASK_RECOMMENDATION}`

Next required gate: {NEXT_REQUIRED_GATE}
"""


# --------------------------------------------------------------------------- #
# Explicit artifact writer (no writes happen on import)
# --------------------------------------------------------------------------- #
def write_artifacts(repo_root):
    """Write the deterministic 0174EE packet + doc under ``repo_root``.

    Returns the list of written file paths. Refuses to write if either artifact
    fails the redaction scan (fail closed). Performs NO other side effects.
    """
    packet = build_packet()
    doc = build_doc()

    packet_violations = scan_for_leaks(packet)
    if packet_violations:
        raise ValueError(f"packet failed redaction scan: {packet_violations}")
    doc_violations = scan_for_leaks(doc)
    if doc_violations:
        raise ValueError(f"doc failed redaction scan: {doc_violations}")

    out_dir = os.path.join(repo_root, DOC_REL_DIR)
    os.makedirs(out_dir, exist_ok=True)
    packet_path = os.path.join(out_dir, PACKET_FILENAME)
    doc_path = os.path.join(out_dir, DOC_FILENAME)

    with open(packet_path, "w", encoding="utf-8") as fh:
        fh.write(serialize(packet))
    with open(doc_path, "w", encoding="utf-8") as fh:
        fh.write(doc)

    return [packet_path, doc_path]


# Note: os.makedirs / open are used ONLY inside write_artifacts, invoked
# explicitly by an operator/test. Importing this module performs no writes.
# ``os`` is bound via the top-level ``import os.path``.
