"""Editorial agent + platform preview SET + supervised dry-run contract.

Tasks 0174TJ (editorial agent), 0174TK (platform preview integration), and
0174TL (supervised end-to-end dry run) -- one deterministic, LOCAL authority
batch on top of the accepted chain:

  * 0174EC: credential handle / redaction boundary.
  * 0174ED + R1: exact approval ledger + payload hash contract.
  * 0174EE + R1: dispatch outbox + idempotency + preflight contract, bound to a
    recomputed payload hash.
  * 0174TG/TH/TI + R1: remote operator inbox + intent parser + review challenge
    contract, terminating in ``remote_review_approved_not_dispatched``.

R1 HARDENING (this revision):
  * Bug 1 fix: 0174TK now builds a multi-surface ``PlatformPreviewSet`` (Telegram
    channel, X post, LinkedIn post, manual publish packet). A single
    ``PlatformPreviewRecord`` can NO LONGER satisfy supervised dry run.
  * Bug 2 fix: editorial / preview / dry-run cross-binding is deepened to bind
    and re-check review_challenge_id, operator_id, editorial_id, preview_set_id,
    outbox_entry_id, idempotency_key, payload_hash, and approval_ledger_entry_id
    across ALL artifacts (review result, outbox entry, editorial record, preview
    set, and EVERY preview artifact inside the set).

Product role of this batch (all LOCAL, all deterministic):
  1. 0174TJ takes a VALID 0174TI ``remote_review_approved_not_dispatched``
     result plus the EXACT 0174EE outbox entry it was bound to, and produces a
     symbolic, redacted ``EditorialDecisionRecord`` carrying the full authority
     binding. The editorial agent is a deterministic, rule-based gate (NEVER an
     LLM call). It fails closed on any financial-advice / buy-sell-hold / sizing
     / guaranteed-prediction / signal framing, and it NEVER dispatches.
  2. 0174TK consumes a valid editorial record + the same outbox entry and builds
     a LOCAL, redacted ``PlatformPreviewSet`` with one artifact per required
     surface. It NEVER renders against a live platform, calls a platform API, or
     hydrates credentials -- provider rendering remains UNVERIFIED. The manual
     publish packet is a local preview only, never live readiness.
  3. 0174TL consumes the review result, outbox entry, editorial record, and the
     preview SET, re-proves EVERY cross-binding, and requires all four surfaces.
     It emits ``supervised_dry_run_complete_not_dispatched``. A valid dry run can
     ONLY confirm readiness for a FUTURE supervised gate -- never dispatch.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Pure Python stdlib only. No requests/httpx/aiohttp, no urllib request
    clients, no socket/ssl/http server, no selenium/playwright, no
    dotenv/keyring/sqlite, no openai/anthropic/telegram/tweepy SDKs.
  * NO network call of any kind.
  * NO env / .env / keyring / browser-session / credential-file read.
  * NO OAuth, token exchange/refresh, credential hydration.
  * NO live posting, sendMessage, platform preview rendering against a live
    surface, platform API call, dispatch, scheduler, retry loop, autonomous
    replies/DMs, scraping, or OpenClaw runtime.
  * Raw chat id / username / phone / token / bot token / webhook url / raw
    provider response / profile url are rejected or redacted by a fail-closed
    scanner and never persisted.
  * NO financial advice: buy/sell/hold calls, position sizing, guaranteed
    predictions, or trade-signal framing in editorial/preview text fail closed.
  * Editorial approval is NOT dispatch; a preview SET is NOT a post; a dry run is
    NOT a live write; none of them hydrate credentials.
  * Provider rendering is UNVERIFIED and NEVER becomes live readiness.
  * Missing or ambiguous state blocks (fail closed).

Importing this module performs NO writes and NO side effects. Artifacts are
written ONLY when ``write_artifacts(...)`` is called explicitly.
"""

import hashlib
import json
import os.path
import re

# Upstream authority layers. This batch CONSUMES their outputs; it never
# bypasses them. The redaction scanner is reused as the single source of truth.
from live_contentops import approval_ledger_payload_hash_contract as approval
from live_contentops import dispatch_outbox_idempotency_contract as outbox
from live_contentops import remote_operator_inbox_intent_review_contract as review

TASK_LABEL = (
    "TASK_CONTENTOPS_0174TJ_TK_TL_EDITORIAL_PREVIEW_AND_SUPERVISED_DRY_RUN_"
    "CONTRACT_BATCH_V0"
)
MODEL = "EDITORIAL_PREVIEW_SUPERVISED_DRY_RUN_CONTRACT_0174TJ_TK_TL"
MODEL_VERSION = "0174TJ_TK_TL_EDITORIAL_PREVIEW_DRY_RUN_V2_R2"

EDITORIAL_SCHEMA = "contentops.editorial_decision_record"
EDITORIAL_SCHEMA_VERSION = "0174TJ_EDITORIAL_V2_R1"
PREVIEW_ARTIFACT_SCHEMA = "contentops.platform_preview_artifact"
PREVIEW_ARTIFACT_SCHEMA_VERSION = "0174TK_PREVIEW_ARTIFACT_V1_R1"
PREVIEW_SET_SCHEMA = "contentops.platform_preview_set"
PREVIEW_SET_SCHEMA_VERSION = "0174TK_PREVIEW_SET_V1_R1"
# Legacy single-record schema retained only for the compatibility wrapper.
PREVIEW_SCHEMA = "contentops.platform_preview_record"
PREVIEW_SCHEMA_VERSION = "0174TK_PREVIEW_V1"
DRY_RUN_SCHEMA = "contentops.supervised_dry_run_record"
DRY_RUN_SCHEMA_VERSION = "0174TL_DRY_RUN_V2_R2"

SOURCE_BASELINE_COMMIT = "9e06c325f64e3dd1d4aa95c44c8e5224b061be17"

# Output artifact locations (written ONLY by the explicit write helper).
DOC_REL_DIR = os.path.join("docs", "automation", "0174TJ_TK_TL")
PACKET_FILENAME = "editorial_preview_supervised_dry_run_contract_packet.json"
DOC_FILENAME = "editorial_preview_supervised_dry_run_contract.md"

NEXT_REQUIRED_GATE = (
    "kill switch contract, rate/spend policy contract, and a one-request/no-"
    "auto-retry supervised dispatch gate with redacted immutable audit, all "
    "still local until an explicit operator-owned live gate; credential "
    "hydration and live platform/Telegram dispatch remain separate future "
    "operator-owned gates and are NOT enabled here"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174TM_TN_TO_KILL_SWITCH_RATE_POLICY_AND_ONE_REQUEST_"
    "SUPERVISED_DISPATCH_GATE_BATCH_V0"
)


# --------------------------------------------------------------------------- #
# Status vocabularies (symbolic only)
# --------------------------------------------------------------------------- #
class Status:
    PASS = "pass"
    BLOCKED = "blocked"
    FAIL_CLOSED = "fail_closed"


# 0174TJ editorial outcome classes.
EDITORIAL_APPROVED_NOT_DISPATCHED = "editorial_approved_not_dispatched"
EDITORIAL_NOT_APPROVED = "editorial_not_approved"
EDITORIAL_FAIL_CLOSED = "editorial_fail_closed_forbidden_value"

# 0174TK preview-set outcome classes.
PREVIEW_SET_BUILT_NOT_DISPATCHED = "platform_preview_set_built_not_dispatched"
PREVIEW_SET_NOT_BUILT = "platform_preview_set_not_built"
PREVIEW_SET_FAIL_CLOSED = "platform_preview_set_fail_closed_forbidden_value"
# Legacy single-record outcome classes (compatibility wrapper only).
PREVIEW_BUILT_NOT_DISPATCHED = "platform_preview_built_not_dispatched"
PREVIEW_NOT_BUILT = "platform_preview_not_built"
PREVIEW_FAIL_CLOSED = "platform_preview_fail_closed_forbidden_value"

# 0174TL dry-run outcome classes.
DRY_RUN_COMPLETE_NOT_DISPATCHED = "supervised_dry_run_complete_not_dispatched"
DRY_RUN_NOT_COMPLETE = "supervised_dry_run_not_complete"
DRY_RUN_FAIL_CLOSED = "supervised_dry_run_fail_closed_forbidden_value"

# 0174TJ editorial blocked-reason classes.
BLOCK_REVIEW_NOT_APPROVED = "review_result_not_approved_not_dispatched"
BLOCK_REVIEW_FORBIDDEN_VALUE = "review_result_forbidden_value_detected"
BLOCK_OUTBOX_NOT_AUTHORITY = "outbox_entry_not_0174ee_authority"
BLOCK_REVIEW_OUTBOX_BINDING_MISMATCH = "review_outbox_binding_mismatch"
BLOCK_EDITORIAL_FORBIDDEN_VALUE = "editorial_forbidden_value_detected"
BLOCK_EDITORIAL_FINANCIAL_ADVICE = "editorial_financial_advice_detected"
BLOCK_EDITORIAL_MISSING_FIELD = "editorial_required_field_missing"
BLOCK_EDITORIAL_LANE_NOT_ALLOWED = "editorial_content_lane_not_allowed"
# R1 deep-binding editorial blocked reasons.
BLOCK_EDITORIAL_CHALLENGE_ID_MISMATCH = "editorial_challenge_id_mismatch"
BLOCK_EDITORIAL_OPERATOR_ID_MISMATCH = "editorial_operator_id_mismatch"
BLOCK_EDITORIAL_IDEMPOTENCY_KEY_MISMATCH = "editorial_idempotency_key_mismatch"
BLOCK_EDITORIAL_LEDGER_ENTRY_MISMATCH = (
    "editorial_approval_ledger_entry_id_mismatch")

# 0174TK preview blocked-reason classes.
BLOCK_EDITORIAL_NOT_APPROVED = "editorial_record_not_approved_not_dispatched"
BLOCK_EDITORIAL_FORBIDDEN_INPUT = "editorial_record_forbidden_value_detected"
BLOCK_PREVIEW_OUTBOX_MISMATCH = "preview_editorial_outbox_binding_mismatch"
BLOCK_PREVIEW_FORBIDDEN_VALUE = "preview_forbidden_value_detected"
BLOCK_PREVIEW_FINANCIAL_ADVICE = "preview_financial_advice_detected"
BLOCK_PREVIEW_MISSING_FIELD = "preview_required_field_missing"
BLOCK_PREVIEW_PLATFORM_MISMATCH = "preview_platform_mismatch"
BLOCK_PREVIEW_SET_MISSING_SURFACE = "preview_set_missing_required_surface"

# 0174TL dry-run blocked-reason classes.
BLOCK_DRY_RUN_FORBIDDEN_VALUE = "dry_run_forbidden_value_detected"
BLOCK_DRY_RUN_REVIEW_NOT_APPROVED = "dry_run_review_not_approved"
BLOCK_DRY_RUN_EDITORIAL_NOT_APPROVED = "dry_run_editorial_not_approved"
BLOCK_DRY_RUN_PREVIEW_NOT_BUILT = "dry_run_preview_set_not_built"
BLOCK_DRY_RUN_PAYLOAD_HASH_MISMATCH = "dry_run_payload_hash_mismatch"
BLOCK_DRY_RUN_IDEMPOTENCY_KEY_MISMATCH = "dry_run_idempotency_key_mismatch"
BLOCK_DRY_RUN_OUTBOX_ENTRY_MISMATCH = "dry_run_outbox_entry_id_mismatch"
BLOCK_DRY_RUN_LEDGER_ENTRY_MISMATCH = "dry_run_approval_ledger_entry_id_mismatch"
BLOCK_DRY_RUN_EDITORIAL_ID_MISMATCH = "dry_run_editorial_id_mismatch"
BLOCK_DRY_RUN_PREVIEW_ID_MISMATCH = "dry_run_preview_id_mismatch"
BLOCK_DRY_RUN_MISSING_FIELD = "dry_run_required_field_missing"
# R1 deep-binding dry-run blocked reasons.
BLOCK_DRY_RUN_CHALLENGE_ID_MISMATCH = "dry_run_challenge_id_mismatch"
BLOCK_DRY_RUN_OPERATOR_ID_MISMATCH = "dry_run_operator_id_mismatch"
BLOCK_DRY_RUN_PREVIEW_SET_ID_MISMATCH = "dry_run_preview_set_id_mismatch"
BLOCK_DRY_RUN_PREVIEW_SET_MISSING_SURFACE = (
    "dry_run_preview_set_missing_required_surface")
BLOCK_DRY_RUN_PREVIEW_ARTIFACT_BINDING_MISMATCH = (
    "dry_run_preview_artifact_binding_mismatch")
BLOCK_DRY_RUN_PREVIEW_ARTIFACT_HARD_BLOCKER = (
    "dry_run_preview_artifact_hard_blocker")
BLOCK_DRY_RUN_PREVIEW_SET_REQUIRED = "dry_run_preview_set_required"
BLOCK_DRY_RUN_LIVE_READINESS_CLAIMED = "dry_run_live_readiness_claimed"
# R2 coverage-recompute dry-run blocked reasons. Coverage is recomputed from
# the preview artifacts themselves; set-level metadata is never authority.
BLOCK_DRY_RUN_PREVIEW_ARTIFACT_DUPLICATE_SURFACE = (
    "dry_run_preview_artifact_duplicate_surface")
BLOCK_DRY_RUN_PREVIEW_ARTIFACT_UNKNOWN_SURFACE = (
    "dry_run_preview_artifact_unknown_surface")
BLOCK_DRY_RUN_PREVIEW_ARTIFACT_COUNT_MISMATCH = (
    "dry_run_preview_artifact_count_mismatch")
BLOCK_DRY_RUN_PREVIEW_SURFACE_COVERAGE_MISMATCH = (
    "dry_run_preview_surface_coverage_mismatch")

# R2 invariants surfaced in the packet + doc so the recompute guarantee is
# self-describing and auditable.
R2_INVARIANTS = (
    "dry_run_recomputes_preview_surface_coverage_from_artifacts",
    "preview_set_metadata_cannot_override_artifact_truth",
    "missing_preview_artifact_cannot_be_hidden_by_stale_metadata",
    "duplicate_preview_artifact_surface_blocks_dry_run",
    "unknown_preview_artifact_surface_blocks_dry_run",
    "artifact_count_mismatch_blocks_dry_run",
)

# The full set of dry-run blocked reasons that enforce preview coverage truth.
R2_COVERAGE_BLOCKED_REASONS = (
    BLOCK_DRY_RUN_PREVIEW_SET_MISSING_SURFACE,
    BLOCK_DRY_RUN_PREVIEW_ARTIFACT_BINDING_MISMATCH,
    BLOCK_DRY_RUN_PREVIEW_ARTIFACT_DUPLICATE_SURFACE,
    BLOCK_DRY_RUN_PREVIEW_ARTIFACT_UNKNOWN_SURFACE,
    BLOCK_DRY_RUN_PREVIEW_ARTIFACT_COUNT_MISMATCH,
    BLOCK_DRY_RUN_PREVIEW_SURFACE_COVERAGE_MISMATCH,
)

# Only these content lanes may carry an editorial decision in this batch. These
# are grounded/context lanes -- never a trade-signal or advice lane.
ALLOWED_CONTENT_LANES = frozenset({
    "grounded_news_context",
    "grounded_macro_context",
    "grounded_explainer",
    "market_structure_education",
    "neutral_market_recap",
})

DEFAULT_CONTENT_LANE = "grounded_news_context"

# The required preview surfaces. A preview set MUST contain exactly one artifact
# per surface; a missing surface blocks both the preview set and the dry run.
SURFACE_TELEGRAM_CHANNEL = "telegram_channel_preview"
SURFACE_X_POST = "x_post_preview"
SURFACE_LINKEDIN_POST = "linkedin_post_preview"
SURFACE_MANUAL_PUBLISH_PACKET = "manual_publish_packet_preview"

REQUIRED_PREVIEW_SURFACES = (
    SURFACE_TELEGRAM_CHANNEL,
    SURFACE_X_POST,
    SURFACE_LINKEDIN_POST,
    SURFACE_MANUAL_PUBLISH_PACKET,
)

# Each surface maps to the platform token recorded on its artifact.
_SURFACE_PLATFORM = {
    SURFACE_TELEGRAM_CHANNEL: "telegram",
    SURFACE_X_POST: "x",
    SURFACE_LINKEDIN_POST: "linkedin",
    SURFACE_MANUAL_PUBLISH_PACKET: "manual_publish_packet",
}

# Authority fields that must agree across the review result, outbox entry,
# editorial record, preview set, and every preview artifact.
_CHAIN_BIND_FIELDS = (
    "outbox_entry_id",
    "idempotency_key",
    "payload_hash",
    "approval_ledger_entry_id",
)

# Deep-binding identity fields threaded through every artifact (R1).
_DEEP_BIND_FIELDS = (
    "review_challenge_id",
    "operator_id",
    "editorial_id",
    "preview_set_id",
    "outbox_entry_id",
    "idempotency_key",
    "payload_hash",
    "approval_ledger_entry_id",
)


# --------------------------------------------------------------------------- #
# Redaction + financial-advice scanning + deterministic serialization.
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


# Financial-advice / trade-signal phrases that MUST fail closed. The editorial
# and preview surfaces are grounded context only; they NEVER tell anyone to
# buy/sell/hold, size a position, or frame a guaranteed prediction or signal.
_FINANCIAL_ADVICE_PATTERNS = [
    re.compile(r"(?i)\b(?:buy|sell|short|long|accumulate|dump|hold)\s+"
               r"(?:now|today|this|the|your|more|aggressively)\b"),
    re.compile(r"(?i)\b(?:strong\s+)?(?:buy|sell)\s+(?:signal|rating|call)\b"),
    re.compile(r"(?i)\b(?:price\s+target|target\s+price|pt)\b"),
    re.compile(r"(?i)\b(?:position|risk)\s*(?:size|sizing)\b"),
    re.compile(r"(?i)\ballocate\s+\d+\s*%"),
    re.compile(r"(?i)\b(?:guaranteed|guarantee[sd]?|surefire|risk-?free|"
               r"can'?t\s+lose|certain)\s+(?:return|profit|gain|win|upside)"),
    re.compile(r"(?i)\bwill\s+(?:definitely|certainly|surely)\s+"
               r"(?:rise|fall|moon|crash|double|triple|go\s+up|go\s+down)"),
    re.compile(r"(?i)\b(?:trade|entry|exit)\s+signal\b"),
    re.compile(r"(?i)\b(?:stop[\s-]?loss|take[\s-]?profit|leverage)\b"),
    re.compile(r"(?i)\bfinancial\s+advice\b"),
    re.compile(r"(?i)\b(?:should|must)\s+(?:buy|sell|short|invest\s+in)\b"),
]


def scan_for_financial_advice(obj):
    """Return a sorted list of financial-advice / trade-signal violations.

    Walks strings within ``obj`` (dict/list/str) and flags any buy/sell/hold
    call, position sizing, guaranteed prediction, or trade-signal framing. This
    is a hard content-safety gate, independent of the credential redaction
    scanner. Returns an empty list when the content is clean.
    """
    violations = []

    def _walk(node, key=None):
        if isinstance(node, dict):
            for k, v in node.items():
                _walk(v, k)
        elif isinstance(node, (list, tuple)):
            for v in node:
                _walk(v, key)
        elif isinstance(node, str):
            for pat in _FINANCIAL_ADVICE_PATTERNS:
                if pat.search(node):
                    violations.append(f"financial_advice:{key or 'value'}")
                    break

    _walk(obj)
    return sorted(set(violations))


# --------------------------------------------------------------------------- #
# Shared safety flags
# --------------------------------------------------------------------------- #
def _safety_flags():
    """Hard-coded safety invariants attached to every 0174TJ/TK/TL object."""
    return {
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "platform_preview_rendered_live": False,
        "telegram_send_performed": False,
        "credential_hydrated": False,
        "llm_behavior": False,
        "network_performed": False,
        "scheduler_enabled": False,
        "auto_retry_allowed": False,
        "autonomous_reply_performed": False,
        "dispatch_ready": False,
        "live_ready": False,
        "provider_rendering_unverified": True,
        "no_financial_advice_emitted": True,
    }


# --------------------------------------------------------------------------- #
# Deterministic derivation / normalization of review-result binding fields.
# --------------------------------------------------------------------------- #
def _review_binding(review_result):
    """Derive the canonical binding fields a 0174TI review result exposes.

    The 0174TI ``_review_result`` surface exposes ``challenge_id``,
    ``operator_id``, ``outbox_entry_id``, ``idempotency_key_short``, and
    ``payload_hash_short`` (short forms only). This normalizer maps them to the
    deep-binding field names without weakening fail-closed behavior: a missing
    field stays ``None`` and therefore cannot match a populated outbox field.
    """
    rr = review_result or {}
    return {
        "review_challenge_id": rr.get("challenge_id"),
        "operator_id": rr.get("operator_id"),
        "outbox_entry_id": rr.get("outbox_entry_id"),
        "idempotency_key_short": rr.get("idempotency_key_short"),
        "payload_hash_short": rr.get("payload_hash_short"),
    }


# --------------------------------------------------------------------------- #
# 0174TJ: Editorial agent contract
# --------------------------------------------------------------------------- #
def _review_is_approved(review_result):
    """True if a 0174TI validation result is an exact approved-not-dispatched."""
    rr = review_result or {}
    return (
        rr.get("review_outcome_class") == review.REVIEW_APPROVED_NOT_DISPATCHED
        and rr.get("approved_not_dispatched") is True
        and rr.get("status") == review.InboxStatus.PASS
    )


def run_editorial_agent(review_result, outbox_entry, *, editorial_id,
                        editor_operator_id, decided_at_epoch,
                        editorial_summary_redacted="redacted",
                        content_lane=DEFAULT_CONTENT_LANE,
                        editorial_notes_redacted="redacted"):
    """Deterministically decide whether an approved review may become editorial.

    Consumes a VALID 0174TI ``remote_review_approved_not_dispatched`` result and
    the EXACT 0174EE outbox entry it was bound to, and carries the full deep
    binding forward (review challenge id, operator id, outbox entry id,
    idempotency key, payload hash, approval ledger entry id). Fail-closed:

      * forbidden credential/provider material => ``fail_closed``;
      * financial-advice / signal framing in editorial text => ``fail_closed``;
      * the review must be an exact approved-not-dispatched outcome;
      * the outbox entry must be a genuine, eligible 0174EE local record;
      * the review<->outbox binding must match on outbox entry id, payload hash
        (short), operator id, and challenge id;
      * the editor operator must match the reviewing operator;
      * idempotency key and approval ledger entry id must be present and bind;
      * the content lane must be an allowed grounded/context lane.

    Even when approved, the outcome is ``editorial_approved_not_dispatched`` --
    NEVER dispatch. Produces a deterministic ``EditorialDecisionRecord``.
    """
    rr = review_result or {}
    entry = outbox_entry or {}
    bind = _review_binding(rr)
    blocked = []

    # 1. Fail-closed redaction scan FIRST (review + outbox + editorial text).
    editorial_payload = {
        "editorial_summary_redacted": editorial_summary_redacted,
        "editorial_notes_redacted": editorial_notes_redacted,
    }
    if scan_for_leaks([rr, entry, editorial_payload]):
        return _editorial_result(
            EDITORIAL_FAIL_CLOSED, entry, bind,
            blocked=[BLOCK_EDITORIAL_FORBIDDEN_VALUE], approved=False,
            forbidden_detected=True, financial_advice=False,
            editorial_id=editorial_id, editor_operator_id=editor_operator_id,
            decided_at_epoch=decided_at_epoch, content_lane=content_lane,
            editorial_summary_redacted=editorial_summary_redacted,
            editorial_notes_redacted=editorial_notes_redacted)

    # 2. Hard content-safety gate: no financial advice in editorial text.
    if scan_for_financial_advice(editorial_payload):
        return _editorial_result(
            EDITORIAL_FAIL_CLOSED, entry, bind,
            blocked=[BLOCK_EDITORIAL_FINANCIAL_ADVICE], approved=False,
            forbidden_detected=False, financial_advice=True,
            editorial_id=editorial_id, editor_operator_id=editor_operator_id,
            decided_at_epoch=decided_at_epoch, content_lane=content_lane,
            editorial_summary_redacted=editorial_summary_redacted,
            editorial_notes_redacted=editorial_notes_redacted)

    # 3. The outbox entry must be a genuine, eligible 0174EE local record.
    authority = review.validate_0174ee_outbox_entry_for_review_challenge(entry)
    if not authority["valid"]:
        blocked.append(BLOCK_OUTBOX_NOT_AUTHORITY)

    # 4. The review must be an exact approved-not-dispatched outcome.
    if not _review_is_approved(rr):
        blocked.append(BLOCK_REVIEW_NOT_APPROVED)

    # 5. The review<->outbox binding must still match (entry id + payload hash).
    if (bind["outbox_entry_id"] != entry.get("outbox_entry_id")
            or bind["payload_hash_short"] != _short(
                entry.get("payload_hash") or "")):
        blocked.append(BLOCK_REVIEW_OUTBOX_BINDING_MISMATCH)

    # 6. Challenge id must be present on the review binding.
    if not bind["review_challenge_id"]:
        blocked.append(BLOCK_EDITORIAL_CHALLENGE_ID_MISMATCH)

    # 7. The editor operator must match the reviewing operator.
    if not bind["operator_id"] or editor_operator_id != bind["operator_id"]:
        blocked.append(BLOCK_EDITORIAL_OPERATOR_ID_MISMATCH)

    # 8. Idempotency key must be present and bind (short form vs outbox).
    if (not entry.get("idempotency_key")
            or bind["idempotency_key_short"] != _short(
                entry.get("idempotency_key") or "")):
        blocked.append(BLOCK_EDITORIAL_IDEMPOTENCY_KEY_MISMATCH)

    # 9. Approval ledger entry id must be present on the outbox entry.
    if not entry.get("approval_ledger_entry_id"):
        blocked.append(BLOCK_EDITORIAL_LEDGER_ENTRY_MISMATCH)

    # 10. Content lane must be an allowed grounded/context lane.
    if content_lane not in ALLOWED_CONTENT_LANES:
        blocked.append(BLOCK_EDITORIAL_LANE_NOT_ALLOWED)

    # 11. Required identity fields present.
    if not editorial_id:
        blocked.append(BLOCK_EDITORIAL_MISSING_FIELD + ":editorial_id")
    if not editor_operator_id:
        blocked.append(BLOCK_EDITORIAL_MISSING_FIELD + ":editor_operator_id")

    approved = not blocked
    outcome = (EDITORIAL_APPROVED_NOT_DISPATCHED if approved
               else EDITORIAL_NOT_APPROVED)
    return _editorial_result(
        outcome, entry, bind, blocked=sorted(set(blocked)), approved=approved,
        forbidden_detected=False, financial_advice=False,
        editorial_id=editorial_id, editor_operator_id=editor_operator_id,
        decided_at_epoch=decided_at_epoch, content_lane=content_lane,
        editorial_summary_redacted=editorial_summary_redacted,
        editorial_notes_redacted=editorial_notes_redacted)


def _editorial_result(outcome_class, entry, bind, *, blocked, approved,
                      forbidden_detected, financial_advice, editorial_id,
                      editor_operator_id, decided_at_epoch, content_lane,
                      editorial_summary_redacted, editorial_notes_redacted):
    """Build a deterministic EditorialDecisionRecord (pure value).

    Carries the full deep binding forward: review challenge id and operator id
    from the review result, and the outbox entry id / idempotency key / payload
    hash / approval ledger entry id from the exact 0174EE outbox entry.
    """
    status = (Status.PASS if approved
              else (Status.FAIL_CLOSED
                    if (forbidden_detected or financial_advice)
                    else Status.BLOCKED))
    entry = entry or {}
    bind = bind or {}
    record = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "editorial_schema": EDITORIAL_SCHEMA,
        "editorial_schema_version": EDITORIAL_SCHEMA_VERSION,
        "status": status,
        "editorial_outcome_class": outcome_class,
        "editorial_approved_not_dispatched": approved,
        "editorial_id": editorial_id,
        "editor_operator_id": editor_operator_id,
        # Deep-binding identity fields (R1).
        "review_challenge_id": bind.get("review_challenge_id"),
        "operator_id": bind.get("operator_id"),
        "reviewing_operator_id": bind.get("operator_id"),
        "decided_at_epoch": (int(decided_at_epoch)
                             if decided_at_epoch is not None else None),
        "content_lane": content_lane,
        "editorial_summary_redacted": editorial_summary_redacted,
        "editorial_notes_redacted": editorial_notes_redacted,
        # Authority bindings carried forward from the outbox entry (symbolic).
        "outbox_entry_id": entry.get("outbox_entry_id"),
        "idempotency_key": entry.get("idempotency_key"),
        "idempotency_key_short": _short(entry.get("idempotency_key") or ""),
        "payload_hash": entry.get("payload_hash"),
        "payload_hash_short": _short(entry.get("payload_hash") or ""),
        "approval_ledger_entry_id": entry.get("approval_ledger_entry_id"),
        "platform": entry.get("platform"),
        "destination_binding_id": entry.get("destination_binding_id"),
        "credential_handle_id": entry.get("credential_handle_id"),
        "visibility_class": entry.get("visibility_class"),
        "dispatch_intent_class": entry.get("dispatch_intent_class"),
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        "financial_advice_detected": financial_advice,
        # Hard invariants -- editorial approval is NEVER dispatch.
        **_safety_flags(),
        "editorial_approval_is_dispatch": False,
        "editorial_approval_is_platform_posting": False,
    }
    record["record_checksum"] = compute_checksum(record)
    return record


# --------------------------------------------------------------------------- #
# 0174TK: Platform preview SET integration contract
# --------------------------------------------------------------------------- #
def _editorial_is_approved(editorial_record):
    """True if a 0174TJ editorial record is an exact approved-not-dispatched."""
    er = editorial_record or {}
    return (
        er.get("editorial_outcome_class") == EDITORIAL_APPROVED_NOT_DISPATCHED
        and er.get("editorial_approved_not_dispatched") is True
        and er.get("status") == Status.PASS
    )


def _text_length_class(text):
    """Bounded, symbolic length class -- never the raw text or its exact len."""
    n = len(str(text or ""))
    if n == 0:
        return "empty"
    if n <= 280:
        return "short_form"
    if n <= 1300:
        return "medium_form"
    return "long_form"


def _build_preview_artifact(surface, editorial_record, entry, *,
                            preview_set_id, built_at_epoch,
                            preview_body_redacted,
                            disclosure_class="none",
                            media_manifest_presence_class="none"):
    """Build a single deterministic PlatformPreviewArtifact for one surface.

    Every artifact carries the full deep binding (review challenge id, operator
    id, editorial id, preview set id, outbox entry id, idempotency key, payload
    hash, approval ledger entry id) and fails closed on forbidden material or
    financial-advice framing via ``hard_blocker_classes``. The artifact NEVER
    renders against a live platform and NEVER hydrates credentials.
    """
    er = editorial_record or {}
    entry = entry or {}
    hard_blockers = []
    warnings = []

    body_payload = {"preview_body_redacted": preview_body_redacted}
    if scan_for_leaks([body_payload]):
        hard_blockers.append(BLOCK_PREVIEW_FORBIDDEN_VALUE)
    if scan_for_financial_advice(body_payload):
        hard_blockers.append(BLOCK_PREVIEW_FINANCIAL_ADVICE)

    # Provider rendering is always unverified for a local symbolic preview.
    warnings.append("provider_rendering_unverified")
    if surface == SURFACE_MANUAL_PUBLISH_PACKET:
        warnings.append("manual_publish_packet_is_local_preview_only")

    artifact = {
        "preview_artifact_id": f"{preview_set_id}:{surface}",
        "preview_surface_class": surface,
        "preview_set_id": preview_set_id,
        "editorial_id": er.get("editorial_id"),
        "review_challenge_id": er.get("review_challenge_id"),
        "operator_id": er.get("operator_id"),
        "outbox_entry_id": entry.get("outbox_entry_id"),
        "idempotency_key": entry.get("idempotency_key"),
        "idempotency_key_short": _short(entry.get("idempotency_key") or ""),
        "payload_hash": entry.get("payload_hash"),
        "payload_hash_short": _short(entry.get("payload_hash") or ""),
        "approval_ledger_entry_id": entry.get("approval_ledger_entry_id"),
        "platform": entry.get("platform"),
        "source_platform": entry.get("platform"),
        "surface_platform": _SURFACE_PLATFORM.get(surface),
        "built_at_epoch": (int(built_at_epoch)
                           if built_at_epoch is not None else None),
        "text_length_class": _text_length_class(preview_body_redacted),
        "media_manifest_presence_class": media_manifest_presence_class,
        "disclosure_class": disclosure_class,
        "preview_body_redacted": preview_body_redacted,
        "manual_publish_required": True,
        "provider_rendering_unverified": True,
        "live_ready": False,
        "platform_api_called": False,
        "dispatch_performed": False,
        "credential_hydrated": False,
        "preview_warning_classes": sorted(set(warnings)),
        "hard_blocker_classes": sorted(set(hard_blockers)),
    }
    artifact["artifact_checksum"] = compute_checksum(artifact)
    return artifact


def build_platform_preview_set(editorial_record, outbox_entry, *,
                               preview_set_id, built_at_epoch,
                               surface_bodies_redacted=None,
                               disclosure_class="none",
                               media_manifest_presence_class="none"):
    """Build a deterministic PlatformPreviewSet across ALL required surfaces.

    Consumes an approved 0174TJ editorial record and the EXACT 0174EE outbox
    entry it bound, and produces one PlatformPreviewArtifact per required
    surface (telegram channel, X post, LinkedIn post, manual publish packet).
    A single record can NEVER satisfy this: a missing surface blocks the set.

    Fail-closed rules (the set is ``platform_preview_set_not_built`` unless ALL
    hold):
      * forbidden credential/provider material => ``fail_closed``;
      * financial-advice / signal framing in any body => ``fail_closed``;
      * the editorial record must be an exact approved-not-dispatched outcome;
      * the editorial<->outbox binding must match (entry id, payload hash short,
        idempotency key short, approval ledger entry id, operator id);
      * a body must be supplied for EVERY required surface;
      * no per-artifact hard blocker may be present.

    ``surface_bodies_redacted`` maps each required surface class to its redacted
    preview body string. Even when built, the set is built-not-dispatched --
    NEVER live, NEVER dispatched, provider rendering remains unverified.
    """
    er = editorial_record or {}
    entry = outbox_entry or {}
    bodies = dict(surface_bodies_redacted or {})
    blocked = []

    # 1. Fail-closed redaction + financial-advice scan across all bodies first.
    if scan_for_leaks([er, entry, bodies]):
        return _preview_set_result(
            PREVIEW_SET_FAIL_CLOSED, er, entry,
            blocked=[BLOCK_PREVIEW_FORBIDDEN_VALUE], built=False,
            forbidden_detected=True, financial_advice=False,
            preview_set_id=preview_set_id, built_at_epoch=built_at_epoch,
            artifacts=[])
    if scan_for_financial_advice(bodies):
        return _preview_set_result(
            PREVIEW_SET_FAIL_CLOSED, er, entry,
            blocked=[BLOCK_PREVIEW_FINANCIAL_ADVICE], built=False,
            forbidden_detected=False, financial_advice=True,
            preview_set_id=preview_set_id, built_at_epoch=built_at_epoch,
            artifacts=[])

    # 2. The editorial record must be an exact approved-not-dispatched outcome.
    if not _editorial_is_approved(er):
        blocked.append(BLOCK_EDITORIAL_NOT_APPROVED)

    # 3. The editorial<->outbox binding must still match.
    if (er.get("outbox_entry_id") != entry.get("outbox_entry_id")
            or er.get("payload_hash_short") != _short(
                entry.get("payload_hash") or "")
            or er.get("idempotency_key_short") != _short(
                entry.get("idempotency_key") or "")
            or er.get("approval_ledger_entry_id")
            != entry.get("approval_ledger_entry_id")
            or not er.get("operator_id")):
        blocked.append(BLOCK_PREVIEW_OUTBOX_MISMATCH)

    # 4. A body must be supplied for EVERY required surface.
    artifacts = []
    for surface in REQUIRED_PREVIEW_SURFACES:
        if surface not in bodies or bodies.get(surface) in (None, ""):
            blocked.append(BLOCK_PREVIEW_SET_MISSING_SURFACE + ":" + surface)
            continue
        artifact = _build_preview_artifact(
            surface, er, entry, preview_set_id=preview_set_id,
            built_at_epoch=built_at_epoch,
            preview_body_redacted=bodies.get(surface),
            disclosure_class=disclosure_class,
            media_manifest_presence_class=media_manifest_presence_class)
        if artifact["hard_blocker_classes"]:
            blocked.extend(artifact["hard_blocker_classes"])
        # Per-artifact platform must match its surface's platform token.
        if artifact["surface_platform"] != _SURFACE_PLATFORM.get(surface):
            blocked.append(BLOCK_PREVIEW_PLATFORM_MISMATCH + ":" + surface)
        artifacts.append(artifact)

    built = not blocked
    outcome = (PREVIEW_SET_BUILT_NOT_DISPATCHED if built
               else PREVIEW_SET_NOT_BUILT)
    return _preview_set_result(
        outcome, er, entry, blocked=sorted(set(blocked)), built=built,
        forbidden_detected=False, financial_advice=False,
        preview_set_id=preview_set_id, built_at_epoch=built_at_epoch,
        artifacts=artifacts)


def _preview_set_result(outcome_class, editorial_record, entry, *, blocked,
                        built, forbidden_detected, financial_advice,
                        preview_set_id, built_at_epoch, artifacts):
    """Build a deterministic PlatformPreviewSet result (pure value).

    Carries the full deep binding forward and embeds every per-surface preview
    artifact. ``present_surface_classes`` and ``missing_surface_classes`` make
    the surface-coverage proof explicit so a downstream dry run can re-verify
    that all required surfaces are present without re-deriving them.
    """
    status = (Status.PASS if built
              else (Status.FAIL_CLOSED
                    if (forbidden_detected or financial_advice)
                    else Status.BLOCKED))
    er = editorial_record or {}
    entry = entry or {}
    present = sorted({a.get("preview_surface_class") for a in artifacts})
    missing = sorted(set(REQUIRED_PREVIEW_SURFACES) - set(present))
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "preview_schema": PREVIEW_SCHEMA,
        "preview_schema_version": PREVIEW_SCHEMA_VERSION,
        "status": status,
        "preview_outcome_class": outcome_class,
        "preview_set_built_not_dispatched": built,
        "preview_set_id": preview_set_id,
        "built_at_epoch": (int(built_at_epoch)
                           if built_at_epoch is not None else None),
        # Deep-binding identity fields carried forward.
        "editorial_id": er.get("editorial_id"),
        "review_challenge_id": er.get("review_challenge_id"),
        "operator_id": er.get("operator_id"),
        "outbox_entry_id": entry.get("outbox_entry_id"),
        "idempotency_key": entry.get("idempotency_key"),
        "idempotency_key_short": _short(entry.get("idempotency_key") or ""),
        "payload_hash": entry.get("payload_hash"),
        "payload_hash_short": _short(entry.get("payload_hash") or ""),
        "approval_ledger_entry_id": entry.get("approval_ledger_entry_id"),
        "platform": entry.get("platform"),
        "required_surface_classes": list(REQUIRED_PREVIEW_SURFACES),
        "present_surface_classes": present,
        "missing_surface_classes": missing,
        "preview_artifacts": artifacts,
        "preview_artifact_count": len(artifacts),
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        "financial_advice_detected": financial_advice,
        # Hard invariants -- a preview set is NEVER dispatch / live.
        **_safety_flags(),
        "preview_is_dispatch": False,
        "preview_is_platform_posting": False,
    }
    result["preview_set_checksum"] = compute_checksum(result)
    return result


def build_platform_preview(editorial_record, outbox_entry, *, preview_set_id,
                           built_at_epoch, surface_bodies_redacted=None,
                           disclosure_class="none",
                           media_manifest_presence_class="none"):
    """Legacy single-call wrapper that returns a full PlatformPreviewSet.

    Retained for backward compatibility with callers that expected a single
    ``build_platform_preview`` entry point. A single preview RECORD can never
    satisfy the dry run -- this wrapper always builds the full required-surface
    SET and returns its result, so the hard surface-coverage invariant holds.
    """
    return build_platform_preview_set(
        editorial_record, outbox_entry, preview_set_id=preview_set_id,
        built_at_epoch=built_at_epoch,
        surface_bodies_redacted=surface_bodies_redacted,
        disclosure_class=disclosure_class,
        media_manifest_presence_class=media_manifest_presence_class)


# --------------------------------------------------------------------------- #
# 0174TL: Supervised end-to-end dry-run contract
# --------------------------------------------------------------------------- #
def _preview_set_is_built(preview_set_result):
    """True if a 0174TK preview-set result is an exact built-not-dispatched."""
    ps = preview_set_result or {}
    return (
        ps.get("preview_outcome_class") == PREVIEW_SET_BUILT_NOT_DISPATCHED
        and ps.get("preview_set_built_not_dispatched") is True
        and ps.get("status") == Status.PASS
        and not ps.get("missing_surface_classes")
    )


def _recompute_surface_coverage(artifacts):
    """Recompute preview-surface coverage STRICTLY from artifact contents (R2).

    Set-level ``present_surface_classes`` / ``missing_surface_classes`` are
    self-reported metadata and are NEVER trusted as authority. This reads each
    artifact's own ``preview_surface_class`` and returns the authoritative,
    deterministically-sorted coverage, so a tampered/stale preview set that
    drops one artifact while leaving clean metadata cannot pass the dry run.
    """
    artifacts = artifacts or []
    required = set(REQUIRED_PREVIEW_SURFACES)
    surfaces = [a.get("preview_surface_class") for a in artifacts]
    counts = {}
    for surface in surfaces:
        counts[surface] = counts.get(surface, 0) + 1
    present = sorted({str(s) for s in surfaces})
    missing = sorted(required - set(surfaces))
    duplicate = sorted({str(s) for s, c in counts.items() if c > 1})
    unknown = sorted({str(s) for s in surfaces if s not in required})
    return {
        "artifact_count": len(artifacts),
        "recomputed_present_surface_classes": present,
        "recomputed_missing_surface_classes": missing,
        "recomputed_duplicate_surface_classes": duplicate,
        "recomputed_unknown_surface_classes": unknown,
    }


def run_supervised_dry_run(review_result, outbox_entry, editorial_record,
                           preview_set_result, *, dry_run_id, operator_id,
                           run_at_epoch):
    """Re-verify the FULL local authority hierarchy as a supervised dry run.

    Consumes the review result (0174TI), the exact 0174EE outbox entry, the
    approved 0174TJ editorial record, and the built 0174TK preview SET, and
    re-derives every cross-binding from scratch. A single preview record can
    NEVER satisfy this: the preview set must carry an artifact for every
    required surface. Fail-closed (the run is ``supervised_dry_run_not_complete``
    unless ALL hold):

      * no forbidden credential/provider material and no financial advice;
      * the review is an exact approved-not-dispatched outcome;
      * the editorial is an exact approved-not-dispatched outcome;
      * the preview set is an exact built-not-dispatched outcome with no missing
        required surface;
      * the deep identity binding agrees across all four artifacts
        (review challenge id, operator id, editorial id, preview set id);
      * the authority binding agrees across all four artifacts
        (outbox entry id, idempotency key, payload hash, approval ledger id);
      * every preview artifact re-binds to the same authority and carries no
        hard blocker and no claimed live readiness.

    Even when complete, the outcome is ``supervised_dry_run_complete_not_
    dispatched`` -- NEVER dispatch, NEVER live, provider rendering unverified.
    """
    rr = review_result or {}
    entry = outbox_entry or {}
    er = editorial_record or {}
    ps = preview_set_result or {}
    blocked = []

    # 1. Fail-closed redaction + financial-advice scan across all inputs first.
    if scan_for_leaks([rr, entry, er, ps]):
        return _dry_run_result(
            DRY_RUN_FAIL_CLOSED, blocked=[BLOCK_DRY_RUN_FORBIDDEN_VALUE],
            complete=False, forbidden_detected=True, financial_advice=False,
            dry_run_id=dry_run_id, operator_id=operator_id,
            run_at_epoch=run_at_epoch, entry=entry, editorial_record=er,
            preview_set_result=ps)
    if scan_for_financial_advice([er, ps]):
        return _dry_run_result(
            DRY_RUN_FAIL_CLOSED, blocked=[BLOCK_PREVIEW_FINANCIAL_ADVICE],
            complete=False, forbidden_detected=False, financial_advice=True,
            dry_run_id=dry_run_id, operator_id=operator_id,
            run_at_epoch=run_at_epoch, entry=entry, editorial_record=er,
            preview_set_result=ps)

    # 2. Each upstream stage must be an exact accepted outcome.
    if not _review_is_approved(rr):
        blocked.append(BLOCK_DRY_RUN_REVIEW_NOT_APPROVED)
    if not _editorial_is_approved(er):
        blocked.append(BLOCK_DRY_RUN_EDITORIAL_NOT_APPROVED)
    if not _preview_set_is_built(ps):
        blocked.append(BLOCK_DRY_RUN_PREVIEW_NOT_BUILT)

    # 3. Preview-set coverage is RECOMPUTED from the artifacts themselves (R2).
    #    Set-level present/missing metadata is self-reported ONLY and can NEVER
    #    override artifact truth: a tampered set that drops one artifact while
    #    leaving clean metadata is caught here. The required surfaces must be
    #    present EXACTLY once, with no duplicate / unknown surface and an
    #    artifact count equal to the required count.
    artifacts = ps.get("preview_artifacts") or []
    coverage = _recompute_surface_coverage(artifacts)
    if not artifacts:
        blocked.append(BLOCK_DRY_RUN_PREVIEW_SET_REQUIRED)
    for surface in coverage["recomputed_missing_surface_classes"]:
        blocked.append(
            BLOCK_DRY_RUN_PREVIEW_SET_MISSING_SURFACE + ":" + surface)
    for surface in coverage["recomputed_duplicate_surface_classes"]:
        blocked.append(
            BLOCK_DRY_RUN_PREVIEW_ARTIFACT_DUPLICATE_SURFACE + ":" + surface)
    for surface in coverage["recomputed_unknown_surface_classes"]:
        blocked.append(
            BLOCK_DRY_RUN_PREVIEW_ARTIFACT_UNKNOWN_SURFACE + ":" + surface)
    if coverage["artifact_count"] != len(REQUIRED_PREVIEW_SURFACES):
        blocked.append(BLOCK_DRY_RUN_PREVIEW_ARTIFACT_COUNT_MISMATCH)
    # Self-reported set metadata must match the recomputed truth EXACTLY; any
    # divergence means the metadata was tampered or is stale -> block.
    if ((ps.get("present_surface_classes") or [])
            != coverage["recomputed_present_surface_classes"]):
        blocked.append(BLOCK_DRY_RUN_PREVIEW_SURFACE_COVERAGE_MISMATCH)
    if ((ps.get("missing_surface_classes") or [])
            != coverage["recomputed_missing_surface_classes"]):
        blocked.append(BLOCK_DRY_RUN_PREVIEW_SURFACE_COVERAGE_MISMATCH)
    if (ps.get("preview_artifact_count") or 0) != coverage["artifact_count"]:
        blocked.append(BLOCK_DRY_RUN_PREVIEW_SURFACE_COVERAGE_MISMATCH)

    # 4. Authority binding must agree across all four artifacts.
    rbind = _review_binding(rr)
    if not (entry.get("outbox_entry_id")
            == rbind["outbox_entry_id"]
            == er.get("outbox_entry_id")
            == ps.get("outbox_entry_id")):
        blocked.append(BLOCK_DRY_RUN_OUTBOX_ENTRY_MISMATCH)
    if not (entry.get("payload_hash")
            and er.get("payload_hash") == entry.get("payload_hash")
            and ps.get("payload_hash") == entry.get("payload_hash")
            and rbind["payload_hash_short"] == _short(
                entry.get("payload_hash") or "")):
        blocked.append(BLOCK_DRY_RUN_PAYLOAD_HASH_MISMATCH)
    if not (entry.get("idempotency_key")
            and er.get("idempotency_key") == entry.get("idempotency_key")
            and ps.get("idempotency_key") == entry.get("idempotency_key")):
        blocked.append(BLOCK_DRY_RUN_IDEMPOTENCY_KEY_MISMATCH)
    if not (entry.get("approval_ledger_entry_id")
            and er.get("approval_ledger_entry_id")
            == entry.get("approval_ledger_entry_id")
            and ps.get("approval_ledger_entry_id")
            == entry.get("approval_ledger_entry_id")):
        blocked.append(BLOCK_DRY_RUN_LEDGER_ENTRY_MISMATCH)

    # 5. Deep identity binding must agree across all four artifacts.
    if not (rbind["review_challenge_id"]
            and er.get("review_challenge_id") == rbind["review_challenge_id"]
            and ps.get("review_challenge_id") == rbind["review_challenge_id"]):
        blocked.append(BLOCK_DRY_RUN_CHALLENGE_ID_MISMATCH)
    if not (operator_id
            and rbind["operator_id"] == operator_id
            and er.get("operator_id") == operator_id
            and ps.get("operator_id") == operator_id):
        blocked.append(BLOCK_DRY_RUN_OPERATOR_ID_MISMATCH)
    if not (er.get("editorial_id")
            and ps.get("editorial_id") == er.get("editorial_id")):
        blocked.append(BLOCK_DRY_RUN_EDITORIAL_ID_MISMATCH)
    if not ps.get("preview_set_id"):
        blocked.append(BLOCK_DRY_RUN_PREVIEW_SET_ID_MISMATCH)

    # 6. Every preview artifact must re-bind to the same authority and carry no
    #    hard blocker and no claimed live readiness.
    for artifact in ps.get("preview_artifacts") or []:
        if (artifact.get("outbox_entry_id") != entry.get("outbox_entry_id")
                or artifact.get("payload_hash") != entry.get("payload_hash")
                or artifact.get("idempotency_key")
                != entry.get("idempotency_key")
                or artifact.get("approval_ledger_entry_id")
                != entry.get("approval_ledger_entry_id")
                or artifact.get("editorial_id") != er.get("editorial_id")
                or artifact.get("preview_set_id") != ps.get("preview_set_id")
                or artifact.get("review_challenge_id")
                != rbind["review_challenge_id"]
                or artifact.get("operator_id") != operator_id):
            blocked.append(BLOCK_DRY_RUN_PREVIEW_ARTIFACT_BINDING_MISMATCH
                           + ":" + str(artifact.get("preview_surface_class")))
        if artifact.get("hard_blocker_classes"):
            blocked.append(BLOCK_DRY_RUN_PREVIEW_ARTIFACT_HARD_BLOCKER
                           + ":" + str(artifact.get("preview_surface_class")))
        if (artifact.get("live_ready") is not False
                or artifact.get("platform_api_called") is not False
                or artifact.get("dispatch_performed") is not False
                or artifact.get("credential_hydrated") is not False):
            blocked.append(BLOCK_DRY_RUN_LIVE_READINESS_CLAIMED
                           + ":" + str(artifact.get("preview_surface_class")))

    # 7. Required identity fields present.
    if not dry_run_id:
        blocked.append(BLOCK_DRY_RUN_MISSING_FIELD + ":dry_run_id")
    if not operator_id:
        blocked.append(BLOCK_DRY_RUN_MISSING_FIELD + ":operator_id")

    complete = not blocked
    outcome = (DRY_RUN_COMPLETE_NOT_DISPATCHED if complete
               else DRY_RUN_NOT_COMPLETE)
    return _dry_run_result(
        outcome, blocked=sorted(set(blocked)), complete=complete,
        forbidden_detected=False, financial_advice=False,
        dry_run_id=dry_run_id, operator_id=operator_id,
        run_at_epoch=run_at_epoch, entry=entry, editorial_record=er,
        preview_set_result=ps)


def _dry_run_result(outcome_class, *, blocked, complete, forbidden_detected,
                    financial_advice, dry_run_id, operator_id, run_at_epoch,
                    entry, editorial_record, preview_set_result):
    """Build a deterministic SupervisedDryRunResult (pure value).

    Carries the full deep binding forward (review challenge id, operator id,
    editorial id, preview set id, outbox entry id, idempotency key, payload
    hash, approval ledger entry id) and embeds the present/missing surface
    coverage proof so the dry-run outcome is self-describing and re-verifiable.
    Even when complete, the outcome is complete-not-dispatched: NEVER live,
    NEVER dispatched, provider rendering remains unverified.
    """
    status = (Status.PASS if complete
              else (Status.FAIL_CLOSED
                    if (forbidden_detected or financial_advice)
                    else Status.BLOCKED))
    entry = entry or {}
    er = editorial_record or {}
    ps = preview_set_result or {}
    _coverage = _recompute_surface_coverage(ps.get("preview_artifacts") or [])
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "dry_run_schema": DRY_RUN_SCHEMA,
        "dry_run_schema_version": DRY_RUN_SCHEMA_VERSION,
        "status": status,
        "dry_run_outcome_class": outcome_class,
        "dry_run_complete_not_dispatched": complete,
        "dry_run_id": dry_run_id,
        "operator_id": operator_id,
        "run_at_epoch": (int(run_at_epoch)
                         if run_at_epoch is not None else None),
        # Deep-binding identity fields re-asserted from the verified chain.
        "review_challenge_id": ps.get("review_challenge_id"),
        "editorial_id": er.get("editorial_id"),
        "preview_set_id": ps.get("preview_set_id"),
        "outbox_entry_id": entry.get("outbox_entry_id"),
        "idempotency_key_short": _short(entry.get("idempotency_key") or ""),
        "payload_hash_short": _short(entry.get("payload_hash") or ""),
        "approval_ledger_entry_id": entry.get("approval_ledger_entry_id"),
        "platform": entry.get("platform"),
        # Surface-coverage proof carried forward from the preview set.
        "required_surface_classes": list(REQUIRED_PREVIEW_SURFACES),
        "present_surface_classes": ps.get("present_surface_classes") or [],
        "missing_surface_classes": ps.get("missing_surface_classes") or [],
        # R2 recomputed-from-artifacts coverage evidence (authoritative).
        "recomputed_present_surface_classes":
            _coverage["recomputed_present_surface_classes"],
        "recomputed_missing_surface_classes":
            _coverage["recomputed_missing_surface_classes"],
        "recomputed_duplicate_surface_classes":
            _coverage["recomputed_duplicate_surface_classes"],
        "recomputed_unknown_surface_classes":
            _coverage["recomputed_unknown_surface_classes"],
        "preview_artifact_count": _coverage["artifact_count"],
        "required_preview_artifact_count": len(REQUIRED_PREVIEW_SURFACES),
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        "financial_advice_detected": financial_advice,
        # Hard invariants -- a dry run is NEVER dispatch / live.
        **_safety_flags(),
        "dry_run_is_dispatch": False,
        "dry_run_is_platform_posting": False,
        "dry_run_is_live_readiness_claim": False,
    }
    result["dry_run_checksum"] = compute_checksum(result)
    return result


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
        "editorial_schema": EDITORIAL_SCHEMA,
        "editorial_schema_version": EDITORIAL_SCHEMA_VERSION,
        "preview_schema": PREVIEW_SCHEMA,
        "preview_schema_version": PREVIEW_SCHEMA_VERSION,
        "dry_run_schema": DRY_RUN_SCHEMA,
        "dry_run_schema_version": DRY_RUN_SCHEMA_VERSION,
        "allowed_content_lanes": sorted(ALLOWED_CONTENT_LANES),
        "required_preview_surfaces": list(REQUIRED_PREVIEW_SURFACES),
        "editorial_outcome_classes": [
            EDITORIAL_APPROVED_NOT_DISPATCHED,
            EDITORIAL_NOT_APPROVED,
            EDITORIAL_FAIL_CLOSED,
        ],
        "preview_set_outcome_classes": [
            PREVIEW_SET_BUILT_NOT_DISPATCHED,
            PREVIEW_SET_NOT_BUILT,
            PREVIEW_SET_FAIL_CLOSED,
        ],
        "dry_run_outcome_classes": [
            DRY_RUN_COMPLETE_NOT_DISPATCHED,
            DRY_RUN_NOT_COMPLETE,
            DRY_RUN_FAIL_CLOSED,
        ],
        "deep_bind_fields": list(_DEEP_BIND_FIELDS),
        "chain_bind_fields": list(_CHAIN_BIND_FIELDS),
        "next_required_gate": NEXT_REQUIRED_GATE,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
        "r2_invariants": list(R2_INVARIANTS),
        "dry_run_preview_coverage_blocked_reasons":
            list(R2_COVERAGE_BLOCKED_REASONS),
        "required_preview_artifact_count": len(REQUIRED_PREVIEW_SURFACES),
        **_safety_flags(),
    }
    packet["checksum_sha256"] = compute_checksum(packet)
    return packet


def build_doc():
    """Return a deterministic, redaction-clean markdown contract document."""
    packet = build_packet()
    lanes = "\n".join(f"  * `{lane}`" for lane in sorted(ALLOWED_CONTENT_LANES))
    surfaces = "\n".join(
        f"  * `{s}` -> `{_SURFACE_PLATFORM[s]}`"
        for s in REQUIRED_PREVIEW_SURFACES)
    r2_invariants = "\n".join(f"  * `{inv}`" for inv in R2_INVARIANTS)
    r2_reasons = "\n".join(
        f"  * `{reason}`" for reason in R2_COVERAGE_BLOCKED_REASONS)
    return (
        f"# 0174TJ/TK/TL Editorial + Preview Set + Supervised Dry-Run Contract\n\n"
        f"Task: `{TASK_LABEL}`\n\n"
        f"Model: `{MODEL}` version `{MODEL_VERSION}`\n\n"
        f"Baseline commit: `{SOURCE_BASELINE_COMMIT}`\n\n"
        f"## Role\n\n"
        f"This batch is LOCAL and deterministic. It performs NO live platform "
        f"API call, NO Telegram send, NO LLM/provider call, NO network, NO "
        f"env/credential read, NO credential hydration, NO scheduler, and NO "
        f"auto retry. Provider rendering remains UNVERIFIED.\n\n"
        f"## 0174TJ Editorial agent\n\n"
        f"Consumes a genuine `remote_review_approved_not_dispatched` result and "
        f"the exact 0174EE outbox entry. Fails closed on forbidden material or "
        f"financial-advice framing. Allowed content lanes:\n\n{lanes}\n\n"
        f"## 0174TK Platform preview SET\n\n"
        f"Builds one preview artifact per required surface; a single record "
        f"can NEVER satisfy the dry run. Required surfaces:\n\n{surfaces}\n\n"
        f"## 0174TL Supervised dry run\n\n"
        f"Re-verifies the full review -> outbox -> editorial -> preview-set "
        f"hierarchy and every deep binding. Even when complete, the outcome is "
        f"`{DRY_RUN_COMPLETE_NOT_DISPATCHED}` -- never dispatch.\n\n"
        f"## R2 preview-artifact coverage recompute\n\n"
        f"The supervised dry run RECOMPUTES preview-surface coverage directly "
        f"from `preview_artifacts` and treats set-level `present_surface_"
        f"classes` / `missing_surface_classes` as self-reported metadata only. "
        f"Stale or tampered set metadata can NEVER hide a missing, duplicated, "
        f"or unknown artifact. Invariants:\n\n{r2_invariants}\n\n"
        f"Coverage blocked reasons:\n\n{r2_reasons}\n\n"
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
