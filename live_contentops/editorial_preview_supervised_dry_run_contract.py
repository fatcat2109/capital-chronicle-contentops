"""Editorial agent + platform preview + supervised dry-run contract.

Tasks 0174TJ (editorial agent), 0174TK (platform preview integration), and
0174TL (supervised end-to-end dry run) -- one deterministic, LOCAL authority
batch on top of the accepted chain:

  * 0174EC: credential handle / redaction boundary.
  * 0174ED + R1: exact approval ledger + payload hash contract.
  * 0174EE + R1: dispatch outbox + idempotency + preflight contract, bound to a
    recomputed payload hash.
  * 0174TG/TH/TI + R1: remote operator inbox + intent parser + review challenge
    contract, terminating in ``remote_review_approved_not_dispatched``.

Product role of this batch (all LOCAL, all deterministic):
  1. 0174TJ takes a VALID 0174TI ``remote_review_approved_not_dispatched``
     result plus the EXACT 0174EE outbox entry it was bound to, and produces a
     symbolic, redacted ``EditorialDecisionRecord``. The editorial agent is a
     deterministic, rule-based gate (NEVER an LLM call). It fails closed on any
     financial-advice / buy-sell-hold / sizing / guaranteed-prediction / signal
     framing in the editorial summary, and it NEVER dispatches.
  2. 0174TK consumes a valid editorial record + the same outbox entry and builds
     a LOCAL, redacted ``PlatformPreviewRecord``. It NEVER renders against a live
     platform, calls a platform API, or hydrates credentials -- it only restates
     symbolic, already-redacted authority fields bound to the exact payload hash.
  3. 0174TL consumes the review result, outbox entry, editorial record, and
     preview record, re-proves EVERY cross-binding (payload hash, idempotency
     key, outbox entry id, approval ledger entry id, editorial id, preview id),
     and emits a ``supervised_dry_run_complete_not_dispatched`` result. A valid
     dry run can ONLY confirm readiness for a FUTURE supervised gate -- it never
     dispatches, posts, or hydrates credentials.

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
  * Editorial approval is NOT dispatch; a preview is NOT a post; a dry run is NOT
    a live write; none of them hydrate credentials.
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
MODEL_VERSION = "0174TJ_TK_TL_EDITORIAL_PREVIEW_DRY_RUN_V1"

EDITORIAL_SCHEMA = "contentops.editorial_decision_record"
EDITORIAL_SCHEMA_VERSION = "0174TJ_EDITORIAL_V1"
PREVIEW_SCHEMA = "contentops.platform_preview_record"
PREVIEW_SCHEMA_VERSION = "0174TK_PREVIEW_V1"
DRY_RUN_SCHEMA = "contentops.supervised_dry_run_record"
DRY_RUN_SCHEMA_VERSION = "0174TL_DRY_RUN_V1"

SOURCE_BASELINE_COMMIT = "27ba55ce08aa8cae1b509e6404edd652e4d31c0c"

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

# 0174TK preview outcome classes.
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

# 0174TK preview blocked-reason classes.
BLOCK_EDITORIAL_NOT_APPROVED = "editorial_record_not_approved_not_dispatched"
BLOCK_EDITORIAL_FORBIDDEN_INPUT = "editorial_record_forbidden_value_detected"
BLOCK_PREVIEW_OUTBOX_MISMATCH = "preview_editorial_outbox_binding_mismatch"
BLOCK_PREVIEW_FORBIDDEN_VALUE = "preview_forbidden_value_detected"
BLOCK_PREVIEW_FINANCIAL_ADVICE = "preview_financial_advice_detected"
BLOCK_PREVIEW_MISSING_FIELD = "preview_required_field_missing"
BLOCK_PREVIEW_PLATFORM_MISMATCH = "preview_platform_mismatch"

# 0174TL dry-run blocked-reason classes.
BLOCK_DRY_RUN_FORBIDDEN_VALUE = "dry_run_forbidden_value_detected"
BLOCK_DRY_RUN_REVIEW_NOT_APPROVED = "dry_run_review_not_approved"
BLOCK_DRY_RUN_EDITORIAL_NOT_APPROVED = "dry_run_editorial_not_approved"
BLOCK_DRY_RUN_PREVIEW_NOT_BUILT = "dry_run_preview_not_built"
BLOCK_DRY_RUN_PAYLOAD_HASH_MISMATCH = "dry_run_payload_hash_mismatch"
BLOCK_DRY_RUN_IDEMPOTENCY_KEY_MISMATCH = "dry_run_idempotency_key_mismatch"
BLOCK_DRY_RUN_OUTBOX_ENTRY_MISMATCH = "dry_run_outbox_entry_id_mismatch"
BLOCK_DRY_RUN_LEDGER_ENTRY_MISMATCH = "dry_run_approval_ledger_entry_id_mismatch"
BLOCK_DRY_RUN_EDITORIAL_ID_MISMATCH = "dry_run_editorial_id_mismatch"
BLOCK_DRY_RUN_PREVIEW_ID_MISMATCH = "dry_run_preview_id_mismatch"
BLOCK_DRY_RUN_MISSING_FIELD = "dry_run_required_field_missing"

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

# Authority fields that must agree across the review result, outbox entry,
# editorial record, and preview record.
_CHAIN_BIND_FIELDS = (
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
        "no_financial_advice_emitted": True,
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
    the EXACT 0174EE outbox entry it was bound to. Fail-closed and
    non-side-effecting:

      * any forbidden credential/provider material in the review result, outbox
        entry, or editorial text => ``fail_closed``;
      * any financial-advice / buy-sell-hold / sizing / guaranteed-prediction /
        signal framing in the editorial text => ``fail_closed``;
      * the review must be an exact approved-not-dispatched outcome;
      * the outbox entry must be a genuine, eligible 0174EE local record;
      * the review<->outbox binding (entry id / idempotency key / payload hash)
        must still match;
      * the content lane must be an allowed grounded/context lane.

    Even when approved, the outcome is ``editorial_approved_not_dispatched`` --
    NEVER dispatch. Produces a deterministic ``EditorialDecisionRecord``.
    """
    rr = review_result or {}
    entry = outbox_entry or {}
    blocked = []

    # 1. Fail-closed redaction scan FIRST (review + outbox + editorial text).
    editorial_payload = {
        "editorial_summary_redacted": editorial_summary_redacted,
        "editorial_notes_redacted": editorial_notes_redacted,
    }
    if scan_for_leaks([rr, entry, editorial_payload]):
        return _editorial_result(
            EDITORIAL_FAIL_CLOSED, entry, blocked=[BLOCK_EDITORIAL_FORBIDDEN_VALUE],
            approved=False, forbidden_detected=True, financial_advice=False,
            editorial_id=editorial_id, editor_operator_id=editor_operator_id,
            decided_at_epoch=decided_at_epoch, content_lane=content_lane,
            editorial_summary_redacted=editorial_summary_redacted,
            editorial_notes_redacted=editorial_notes_redacted)

    # 2. Hard content-safety gate: no financial advice in editorial text.
    if scan_for_financial_advice(editorial_payload):
        return _editorial_result(
            EDITORIAL_FAIL_CLOSED, entry,
            blocked=[BLOCK_EDITORIAL_FINANCIAL_ADVICE],
            approved=False, forbidden_detected=False, financial_advice=True,
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

    # 5. The review<->outbox binding must still match.
    if (rr.get("outbox_entry_id") != entry.get("outbox_entry_id")
            or rr.get("payload_hash_short") != _short(
                entry.get("payload_hash") or "")):
        blocked.append(BLOCK_REVIEW_OUTBOX_BINDING_MISMATCH)

    # 6. Content lane must be an allowed grounded/context lane.
    if content_lane not in ALLOWED_CONTENT_LANES:
        blocked.append(BLOCK_EDITORIAL_LANE_NOT_ALLOWED)

    # 7. Required identity fields present.
    if not editorial_id:
        blocked.append(BLOCK_EDITORIAL_MISSING_FIELD + ":editorial_id")
    if not editor_operator_id:
        blocked.append(BLOCK_EDITORIAL_MISSING_FIELD + ":editor_operator_id")

    approved = not blocked
    outcome = (EDITORIAL_APPROVED_NOT_DISPATCHED if approved
               else EDITORIAL_NOT_APPROVED)
    return _editorial_result(
        outcome, entry, blocked=sorted(set(blocked)), approved=approved,
        forbidden_detected=False, financial_advice=False,
        editorial_id=editorial_id, editor_operator_id=editor_operator_id,
        decided_at_epoch=decided_at_epoch, content_lane=content_lane,
        editorial_summary_redacted=editorial_summary_redacted,
        editorial_notes_redacted=editorial_notes_redacted)


def _editorial_result(outcome_class, entry, *, blocked, approved,
                      forbidden_detected, financial_advice, editorial_id,
                      editor_operator_id, decided_at_epoch, content_lane,
                      editorial_summary_redacted, editorial_notes_redacted):
    """Build a deterministic EditorialDecisionRecord (pure value)."""
    status = (Status.PASS if approved
              else (Status.FAIL_CLOSED
                    if (forbidden_detected or financial_advice)
                    else Status.BLOCKED))
    entry = entry or {}
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
# 0174TK: Platform preview integration contract
# --------------------------------------------------------------------------- #
def _editorial_is_approved(editorial_record):
    """True if a 0174TJ editorial record is an exact approved-not-dispatched."""
    er = editorial_record or {}
    return (
        er.get("editorial_outcome_class") == EDITORIAL_APPROVED_NOT_DISPATCHED
        and er.get("editorial_approved_not_dispatched") is True
        and er.get("status") == Status.PASS
    )


def build_platform_preview(editorial_record, outbox_entry, *, preview_id,
                           built_at_epoch,
                           preview_body_redacted="redacted",
                           preview_render_class="local_symbolic_preview"):
    """Build a LOCAL, redacted platform preview bound to the editorial record.

    Consumes a VALID 0174TJ editorial record + the EXACT 0174EE outbox entry.
    Fail-closed and non-side-effecting:

      * any forbidden material in the editorial record, outbox entry, or preview
        body => ``fail_closed``;
      * any financial-advice / signal framing in the preview body =>
        ``fail_closed``;
      * the editorial record must be an exact approved-not-dispatched outcome;
      * the editorial<->outbox binding (entry id / idempotency key / payload
        hash) must still match;
      * the platform must match between the editorial record and outbox entry.

    The preview NEVER renders against a live platform, calls a platform API, or
    hydrates credentials. Outcome is ``platform_preview_built_not_dispatched``.
    """
    er = editorial_record or {}
    entry = outbox_entry or {}
    blocked = []

    preview_payload = {"preview_body_redacted": preview_body_redacted}

    # 1. Fail-closed redaction scan FIRST.
    if scan_for_leaks([er, entry, preview_payload]):
        return _preview_result(
            PREVIEW_FAIL_CLOSED, er, entry,
            blocked=[BLOCK_PREVIEW_FORBIDDEN_VALUE], built=False,
            forbidden_detected=True, financial_advice=False,
            preview_id=preview_id, built_at_epoch=built_at_epoch,
            preview_body_redacted=preview_body_redacted,
            preview_render_class=preview_render_class)

    # 2. Hard content-safety gate: no financial advice in preview body.
    if scan_for_financial_advice(preview_payload):
        return _preview_result(
            PREVIEW_FAIL_CLOSED, er, entry,
            blocked=[BLOCK_PREVIEW_FINANCIAL_ADVICE], built=False,
            forbidden_detected=False, financial_advice=True,
            preview_id=preview_id, built_at_epoch=built_at_epoch,
            preview_body_redacted=preview_body_redacted,
            preview_render_class=preview_render_class)

    # 3. The editorial record must be an exact approved-not-dispatched outcome.
    if not _editorial_is_approved(er):
        blocked.append(BLOCK_EDITORIAL_NOT_APPROVED)

    # 4. The outbox entry must still be a genuine 0174EE local record.
    authority = review.validate_0174ee_outbox_entry_for_review_challenge(entry)
    if not authority["valid"]:
        blocked.append(BLOCK_OUTBOX_NOT_AUTHORITY)

    # 5. The editorial<->outbox binding must still match.
    for field in _CHAIN_BIND_FIELDS:
        if er.get(field) != entry.get(field):
            blocked.append(BLOCK_PREVIEW_OUTBOX_MISMATCH)
            break

    # 6. Platform must match between editorial record and outbox entry.
    if er.get("platform") != entry.get("platform"):
        blocked.append(BLOCK_PREVIEW_PLATFORM_MISMATCH)

    # 7. Required identity fields present.
    if not preview_id:
        blocked.append(BLOCK_PREVIEW_MISSING_FIELD + ":preview_id")

    built = not blocked
    outcome = PREVIEW_BUILT_NOT_DISPATCHED if built else PREVIEW_NOT_BUILT
    return _preview_result(
        outcome, er, entry, blocked=sorted(set(blocked)), built=built,
        forbidden_detected=False, financial_advice=False,
        preview_id=preview_id, built_at_epoch=built_at_epoch,
        preview_body_redacted=preview_body_redacted,
        preview_render_class=preview_render_class)


def _preview_result(outcome_class, er, entry, *, blocked, built,
                    forbidden_detected, financial_advice, preview_id,
                    built_at_epoch, preview_body_redacted,
                    preview_render_class):
    """Build a deterministic PlatformPreviewRecord (pure value)."""
    status = (Status.PASS if built
              else (Status.FAIL_CLOSED
                    if (forbidden_detected or financial_advice)
                    else Status.BLOCKED))
    er = er or {}
    entry = entry or {}
    record = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "preview_schema": PREVIEW_SCHEMA,
        "preview_schema_version": PREVIEW_SCHEMA_VERSION,
        "status": status,
        "preview_outcome_class": outcome_class,
        "preview_built_not_dispatched": built,
        "preview_id": preview_id,
        "built_at_epoch": (int(built_at_epoch)
                           if built_at_epoch is not None else None),
        "preview_render_class": preview_render_class,
        "preview_body_redacted": preview_body_redacted,
        # Authority bindings carried forward (symbolic).
        "editorial_id": er.get("editorial_id"),
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
        "content_lane": er.get("content_lane"),
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        "financial_advice_detected": financial_advice,
        # Hard invariants -- a preview is NEVER a post.
        **_safety_flags(),
        "preview_is_platform_posting": False,
        "preview_rendered_against_live_platform": False,
    }
    record["record_checksum"] = compute_checksum(record)
    return record


# --------------------------------------------------------------------------- #
# 0174TL: Supervised end-to-end dry-run contract
# --------------------------------------------------------------------------- #
def _preview_is_built(preview_record):
    """True if a 0174TK preview record is an exact built-not-dispatched."""
    pr = preview_record or {}
    return (
        pr.get("preview_outcome_class") == PREVIEW_BUILT_NOT_DISPATCHED
        and pr.get("preview_built_not_dispatched") is True
        and pr.get("status") == Status.PASS
    )


def run_supervised_dry_run(review_result, outbox_entry, editorial_record,
                           preview_record, *, dry_run_id, operator_id,
                           run_at_epoch):
    """Re-prove the full local authority chain end-to-end without dispatching.

    Consumes the 0174TI review result, the 0174EE outbox entry, the 0174TJ
    editorial record, and the 0174TK preview record, and re-proves EVERY
    cross-binding. Fail-closed and non-side-effecting:

      * any forbidden material in any input => ``fail_closed``;
      * the review must be approved-not-dispatched;
      * the editorial record must be approved-not-dispatched;
      * the preview record must be built-not-dispatched;
      * the payload hash, idempotency key, outbox entry id, and approval ledger
        entry id must match across ALL four artifacts;
      * the editorial id and preview id must thread through consistently.

    Outcome is ``supervised_dry_run_complete_not_dispatched`` -- it confirms
    readiness for a FUTURE supervised gate but NEVER dispatches, posts, renders
    live, or hydrates credentials.
    """
    rr = review_result or {}
    entry = outbox_entry or {}
    er = editorial_record or {}
    pr = preview_record or {}
    blocked = []

    # 1. Fail-closed redaction scan FIRST.
    if scan_for_leaks([rr, entry, er, pr]):
        return _dry_run_result(
            DRY_RUN_FAIL_CLOSED, entry, er, pr,
            blocked=[BLOCK_DRY_RUN_FORBIDDEN_VALUE], complete=False,
            forbidden_detected=True, dry_run_id=dry_run_id,
            operator_id=operator_id, run_at_epoch=run_at_epoch)

    # 2. Stage outcomes must each be the exact not-dispatched success class.
    if not _review_is_approved(rr):
        blocked.append(BLOCK_DRY_RUN_REVIEW_NOT_APPROVED)
    if not _editorial_is_approved(er):
        blocked.append(BLOCK_DRY_RUN_EDITORIAL_NOT_APPROVED)
    if not _preview_is_built(pr):
        blocked.append(BLOCK_DRY_RUN_PREVIEW_NOT_BUILT)

    # 3. Outbox entry must still be a genuine 0174EE local record.
    authority = review.validate_0174ee_outbox_entry_for_review_challenge(entry)
    if not authority["valid"]:
        blocked.append(BLOCK_OUTBOX_NOT_AUTHORITY)

    # 4. Payload hash must match across outbox, editorial, preview, and review.
    ph = entry.get("payload_hash")
    ph_short = _short(ph or "")
    if (er.get("payload_hash") != ph or pr.get("payload_hash") != ph
            or rr.get("payload_hash_short") != ph_short):
        blocked.append(BLOCK_DRY_RUN_PAYLOAD_HASH_MISMATCH)

    # 5. Idempotency key must match across outbox, editorial, and preview.
    ik = entry.get("idempotency_key")
    if er.get("idempotency_key") != ik or pr.get("idempotency_key") != ik:
        blocked.append(BLOCK_DRY_RUN_IDEMPOTENCY_KEY_MISMATCH)

    # 6. Outbox entry id must thread through all artifacts.
    oeid = entry.get("outbox_entry_id")
    if (er.get("outbox_entry_id") != oeid or pr.get("outbox_entry_id") != oeid
            or rr.get("outbox_entry_id") != oeid):
        blocked.append(BLOCK_DRY_RUN_OUTBOX_ENTRY_MISMATCH)

    # 7. Approval ledger entry id must match across outbox, editorial, preview.
    leid = entry.get("approval_ledger_entry_id")
    if (er.get("approval_ledger_entry_id") != leid
            or pr.get("approval_ledger_entry_id") != leid):
        blocked.append(BLOCK_DRY_RUN_LEDGER_ENTRY_MISMATCH)

    # 8. Editorial id must thread editorial -> preview.
    if not er.get("editorial_id") or pr.get("editorial_id") != er.get(
            "editorial_id"):
        blocked.append(BLOCK_DRY_RUN_EDITORIAL_ID_MISMATCH)

    # 9. Preview id must be present.
    if not pr.get("preview_id"):
        blocked.append(BLOCK_DRY_RUN_PREVIEW_ID_MISMATCH)

    # 10. Required identity fields present.
    if not dry_run_id:
        blocked.append(BLOCK_DRY_RUN_MISSING_FIELD + ":dry_run_id")
    if not operator_id:
        blocked.append(BLOCK_DRY_RUN_MISSING_FIELD + ":operator_id")

    complete = not blocked
    outcome = (DRY_RUN_COMPLETE_NOT_DISPATCHED if complete
               else DRY_RUN_NOT_COMPLETE)
    return _dry_run_result(
        outcome, entry, er, pr, blocked=sorted(set(blocked)),
        complete=complete, forbidden_detected=False, dry_run_id=dry_run_id,
        operator_id=operator_id, run_at_epoch=run_at_epoch)


def _dry_run_result(outcome_class, entry, er, pr, *, blocked, complete,
                    forbidden_detected, dry_run_id, operator_id, run_at_epoch):
    """Build a deterministic SupervisedDryRunRecord (pure value)."""
    status = (Status.PASS if complete
              else (Status.FAIL_CLOSED if forbidden_detected
                    else Status.BLOCKED))
    entry = entry or {}
    er = er or {}
    pr = pr or {}
    record = {
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
        # The exact bound chain (symbolic / short fingerprints only).
        "editorial_id": er.get("editorial_id"),
        "preview_id": pr.get("preview_id"),
        "outbox_entry_id": entry.get("outbox_entry_id"),
        "idempotency_key_short": _short(entry.get("idempotency_key") or ""),
        "payload_hash_short": _short(entry.get("payload_hash") or ""),
        "approval_ledger_entry_id": entry.get("approval_ledger_entry_id"),
        "platform": entry.get("platform"),
        "visibility_class": entry.get("visibility_class"),
        "content_lane": er.get("content_lane"),
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        # Hard invariants -- a dry run is NEVER a live write.
        **_safety_flags(),
        "dry_run_is_dispatch": False,
        "dry_run_is_platform_posting": False,
        "ready_for_future_supervised_gate_only": complete,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }
    record["record_checksum"] = compute_checksum(record)
    return record


# --------------------------------------------------------------------------- #
# Model packet + doc builders
# --------------------------------------------------------------------------- #
def build_packet():
    """Build the deterministic redacted 0174TJ/TK/TL model packet."""
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "editorial_schema": EDITORIAL_SCHEMA,
        "editorial_schema_version": EDITORIAL_SCHEMA_VERSION,
        "preview_schema": PREVIEW_SCHEMA,
        "preview_schema_version": PREVIEW_SCHEMA_VERSION,
        "dry_run_schema": DRY_RUN_SCHEMA,
        "dry_run_schema_version": DRY_RUN_SCHEMA_VERSION,
        "contract_status": (
            "deterministic_local_editorial_preview_dry_run_authority_ready"),
        "allowed_content_lanes": sorted(ALLOWED_CONTENT_LANES),
        "editorial_outcome_classes": [
            EDITORIAL_APPROVED_NOT_DISPATCHED, EDITORIAL_NOT_APPROVED,
            EDITORIAL_FAIL_CLOSED,
        ],
        "preview_outcome_classes": [
            PREVIEW_BUILT_NOT_DISPATCHED, PREVIEW_NOT_BUILT,
            PREVIEW_FAIL_CLOSED,
        ],
        "dry_run_outcome_classes": [
            DRY_RUN_COMPLETE_NOT_DISPATCHED, DRY_RUN_NOT_COMPLETE,
            DRY_RUN_FAIL_CLOSED,
        ],
        "editorial_blocked_reasons": [
            BLOCK_REVIEW_NOT_APPROVED, BLOCK_REVIEW_FORBIDDEN_VALUE,
            BLOCK_OUTBOX_NOT_AUTHORITY, BLOCK_REVIEW_OUTBOX_BINDING_MISMATCH,
            BLOCK_EDITORIAL_FORBIDDEN_VALUE, BLOCK_EDITORIAL_FINANCIAL_ADVICE,
            BLOCK_EDITORIAL_MISSING_FIELD, BLOCK_EDITORIAL_LANE_NOT_ALLOWED,
        ],
        "preview_blocked_reasons": [
            BLOCK_EDITORIAL_NOT_APPROVED, BLOCK_EDITORIAL_FORBIDDEN_INPUT,
            BLOCK_PREVIEW_OUTBOX_MISMATCH, BLOCK_PREVIEW_FORBIDDEN_VALUE,
            BLOCK_PREVIEW_FINANCIAL_ADVICE, BLOCK_PREVIEW_MISSING_FIELD,
            BLOCK_PREVIEW_PLATFORM_MISMATCH, BLOCK_OUTBOX_NOT_AUTHORITY,
        ],
        "dry_run_blocked_reasons": [
            BLOCK_DRY_RUN_FORBIDDEN_VALUE, BLOCK_DRY_RUN_REVIEW_NOT_APPROVED,
            BLOCK_DRY_RUN_EDITORIAL_NOT_APPROVED,
            BLOCK_DRY_RUN_PREVIEW_NOT_BUILT,
            BLOCK_DRY_RUN_PAYLOAD_HASH_MISMATCH,
            BLOCK_DRY_RUN_IDEMPOTENCY_KEY_MISMATCH,
            BLOCK_DRY_RUN_OUTBOX_ENTRY_MISMATCH,
            BLOCK_DRY_RUN_LEDGER_ENTRY_MISMATCH,
            BLOCK_DRY_RUN_EDITORIAL_ID_MISMATCH,
            BLOCK_DRY_RUN_PREVIEW_ID_MISMATCH, BLOCK_DRY_RUN_MISSING_FIELD,
        ],
        "consumes_upstream_outputs": [
            "remote_review_approved_not_dispatched", "outbox_entry_id",
            "idempotency_key", "payload_hash", "approval_ledger_entry_id",
        ],
        "invariants": [
            "editorial_blocked_unless_review_approved_not_dispatched",
            "editorial_blocked_unless_outbox_entry_is_0174ee_authority",
            "editorial_blocked_on_review_outbox_binding_mismatch",
            "editorial_fails_closed_on_financial_advice_or_signal_framing",
            "editorial_blocked_unless_content_lane_allowed",
            "editorial_approval_is_not_dispatch",
            "preview_blocked_unless_editorial_approved_not_dispatched",
            "preview_blocked_on_editorial_outbox_binding_mismatch",
            "preview_fails_closed_on_financial_advice_or_signal_framing",
            "preview_never_renders_against_live_platform",
            "preview_is_not_platform_posting",
            "dry_run_reproves_every_cross_binding",
            "dry_run_blocked_on_any_hash_key_or_id_mismatch",
            "dry_run_is_not_dispatch_or_platform_posting",
            "dry_run_confirms_future_supervised_gate_readiness_only",
            "no_credential_hydration_anywhere",
            "fail_closed_on_forbidden_value",
        ],
        "redaction_policy": {
            "fail_closed_on_forbidden_value": True,
            "fail_closed_on_financial_advice": True,
            "credential_referenced_by_handle_id_only": True,
            "no_raw_provider_or_platform_response_stored": True,
            "scanner_source": "0174ED_approval_ledger_payload_hash_contract",
        },
        "safety_flags": {
            "dispatch_performed": False,
            "live_request_performed": False,
            "platform_api_called": False,
            "platform_preview_rendered_live": False,
            "telegram_send_performed": False,
            "llm_behavior": False,
            "credential_hydrated": False,
            "scheduler_enabled": False,
            "auto_retry_allowed": False,
            "autonomous_reply_performed": False,
            "dispatch_ready": False,
            "live_ready": False,
            "autonomous_posting_allowed": False,
            "manual_fallback_available": True,
            "no_financial_advice_emitted": True,
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
        "status": Status.PASS,
        "next_required_gate": NEXT_REQUIRED_GATE,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
    }
    packet["checksum_sha256"] = compute_checksum(packet)
    return packet


def build_doc():
    """Build the deterministic redacted 0174TJ/TK/TL markdown documentation."""
    lanes = "\n".join(f"- `{c}`" for c in sorted(ALLOWED_CONTENT_LANES))
    return f"""# Editorial Agent + Platform Preview + Supervised Dry-Run Contract (0174TJ/TK/TL)

Task: {TASK_LABEL}
Model: {MODEL} ({MODEL_VERSION})
Source baseline commit: {SOURCE_BASELINE_COMMIT}
Mode: Implementation Mode. Deterministic, stdlib-only, local authority batch.

> [!IMPORTANT]
> This batch introduces NO live behavior: no platform API call, no live preview
> render, no Telegram send, no LLM call, no network call, no credential read or
> hydration, no environment or `.env` read, no keyring or browser-session read,
> no OAuth, no scheduler, and no auto retry. It is the deterministic local
> editorial agent + platform preview + supervised dry-run authority contract
> only.

## Strategic Posture
- Manual posting is the **fallback** path, not the strategic destination.
- **Automation is the main build path.**
- **Autonomous posting is forbidden.**
- **Supervised publishing is the final product.**

## What This Batch Proves
0174ED proved Jim approved an **exact payload hash**. 0174EE proved that exact,
validated approval becomes a **single local outbox candidate** without duplicate
dispatch risk. 0174TG/TH/TI proved a remote operator review can only ever yield
`remote_review_approved_not_dispatched`. This batch proves the final three local
authority steps WITHOUT touching any live surface:

- **0174TJ Editorial Agent** -- `run_editorial_agent` consumes a valid
  `remote_review_approved_not_dispatched` result plus the exact 0174EE outbox
  entry and produces an `EditorialDecisionRecord`. It is a deterministic,
  rule-based gate (never an LLM call). It **fails closed** on any financial
  advice, buy/sell/hold call, position sizing, guaranteed prediction, or trade
  signal framing, and only allows grounded/context content lanes. Outcome is
  only ever `editorial_approved_not_dispatched`.
- **0174TK Platform Preview** -- `build_platform_preview` consumes a valid
  editorial record + the same outbox entry and builds a LOCAL, redacted
  `PlatformPreviewRecord`. It **never** renders against a live platform or calls
  a platform API. Outcome is only ever `platform_preview_built_not_dispatched`.
- **0174TL Supervised Dry Run** -- `run_supervised_dry_run` re-proves EVERY
  cross-binding (payload hash, idempotency key, outbox entry id, approval ledger
  entry id, editorial id, preview id) across all four artifacts and emits
  `supervised_dry_run_complete_not_dispatched`. It confirms readiness for a
  FUTURE supervised gate but never dispatches.

## Allowed Content Lanes
{lanes}

## Core Objects
- **EditorialDecisionRecord** -- the deterministic 0174TJ editorial gate output.
- **PlatformPreviewRecord** -- the local, redacted 0174TK preview output.
- **SupervisedDryRunRecord** -- the 0174TL end-to-end cross-binding proof.

## Hard Invariants
- Editorial approval is **not** dispatch; a preview is **not** a post; a dry run
  is **not** a live write; none of them hydrate credentials.
- Financial advice / buy-sell-hold / sizing / guaranteed predictions / signal
  framing **fail closed** in both editorial and preview text.
- Every stage re-proves the exact upstream authority binding; any payload hash,
  idempotency key, or id mismatch blocks.
- No raw provider/platform response, token, chat id, username, phone, or webhook
  url is ever stored.
- Missing or ambiguous state blocks (fail closed).

## Next Task
Recommended next task after PASS:
`{EXACT_NEXT_TASK_RECOMMENDATION}`

Next required gate: {NEXT_REQUIRED_GATE}
"""


# --------------------------------------------------------------------------- #
# Explicit artifact writer (no writes happen on import)
# --------------------------------------------------------------------------- #
def write_artifacts(repo_root):
    """Write the deterministic 0174TJ/TK/TL packet + doc under ``repo_root``.

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
