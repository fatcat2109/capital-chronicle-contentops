"""Remote operator inbox + intent parser + review challenge contract.

Tasks 0174TG (Telegram remote operator inbox), 0174TH (LLM intent parser
contract), and 0174TI (Telegram review challenge contract) -- one deterministic,
LOCAL authority batch on top of the accepted chain:

  * 0174EC: credential handle / redaction boundary.
  * 0174ED + R1: exact approval ledger + payload hash contract.
  * 0174EE + R1: dispatch outbox + idempotency + preflight contract, bound to a
    recomputed payload hash.

Product role of this batch (all LOCAL, all deterministic):
  1. 0174TG normalizes a Telegram-LIKE inbound operator message object into a
     symbolic, redacted inbox record. It NEVER touches Telegram: no bot polling,
     no getUpdates, no sendMessage, no webhook, no Telegram SDK, no network. No
     raw Telegram update object is persisted.
  2. 0174TH converts an inbox record's redacted text into a BOUNDED structured
     operator intent using a deterministic, rule-based parser. It simulates the
     boundary an LLM may later fill but NEVER calls an LLM. It fails closed on
     ambiguity and never treats vague agreement / emoji as approval.
  3. 0174TI consumes a valid 0174EE outbox entry/preflight result and generates a
     local review challenge that binds the EXACT outbox entry id, idempotency
     key, and payload hash, and requires an exact human approval phrase before
     any later dispatch gate. A valid approval can ONLY produce
     ``remote_review_approved_not_dispatched`` -- never dispatch.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Pure Python stdlib only. No requests/httpx/aiohttp, no urllib request
    clients, no socket/ssl/http server, no selenium/playwright, no
    dotenv/keyring/sqlite, no openai/anthropic/telegram/tweepy SDKs.
  * NO network call of any kind.
  * NO env / .env / keyring / browser-session / credential-file read.
  * NO OAuth, token exchange/refresh, credential hydration.
  * NO live posting, sendMessage, bot polling, webhook, getUpdates, scheduler,
    retry loop, autonomous replies/DMs, scraping, or OpenClaw runtime.
  * Raw chat id / username / phone / token / bot token / webhook url / raw
    provider update JSON are rejected or redacted by a fail-closed scanner and
    never persisted.
  * Remote approval is NOT dispatch; challenge approval is NOT platform posting;
    the review challenge NEVER hydrates credentials.
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

TASK_LABEL = (
    "TASK_CONTENTOPS_0174TG_TH_TI_REMOTE_INBOX_INTENT_AND_REVIEW_CHALLENGE_"
    "CONTRACT_BATCH_V0"
)
MODEL = "REMOTE_OPERATOR_INBOX_INTENT_REVIEW_CONTRACT_0174TG_TH_TI"
MODEL_VERSION = "0174TG_TH_TI_REMOTE_INBOX_INTENT_REVIEW_V1"

INBOX_SCHEMA = "contentops.remote_operator_inbox_record"
INBOX_SCHEMA_VERSION = "0174TG_INBOX_V1"
INTENT_SCHEMA = "contentops.operator_intent_parse_result"
INTENT_SCHEMA_VERSION = "0174TH_INTENT_V1"
CHALLENGE_SCHEMA = "contentops.remote_review_challenge"
CHALLENGE_SCHEMA_VERSION = "0174TI_REVIEW_CHALLENGE_V1"

SOURCE_BASELINE_COMMIT = "1f5f8642c6d54ce3ffc7c0c29c9a9f4427337a06"

# Output artifact locations (written ONLY by the explicit write helper).
DOC_REL_DIR = os.path.join("docs", "automation", "0174TG_TH_TI")
PACKET_FILENAME = "remote_operator_inbox_intent_review_contract_packet.json"
DOC_FILENAME = "remote_operator_inbox_intent_review_contract.md"

NEXT_REQUIRED_GATE = (
    "editorial agent + platform preview integration + supervised end-to-end "
    "dry run (still local, no live dispatch), then kill switch, rate/spend/"
    "retry policy, one-request/no-auto-retry supervised dispatch, and redacted "
    "immutable audit before any supervised live write; credential hydration and "
    "live platform/Telegram dispatch remain separate future operator-owned "
    "gates and are NOT enabled here"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174TJ_TK_TL_EDITORIAL_PREVIEW_AND_SUPERVISED_DRY_RUN_"
    "CONTRACT_BATCH_V0"
)


# --------------------------------------------------------------------------- #
# Status vocabularies (symbolic only)
# --------------------------------------------------------------------------- #
class InboxStatus:
    PASS = "pass"
    BLOCKED = "blocked"
    FAIL_CLOSED = "fail_closed"


# 0174TG inbound record status classes.
INBOX_NORMALIZED = "inbound_normalized_symbolic_record"
INBOX_BLOCKED = "inbound_blocked"
INBOX_FAIL_CLOSED = "inbound_fail_closed_forbidden_value"

# The only accepted inbound surface class.
SOURCE_SURFACE_CLASS = "telegram_remote_operator_surface"

# Operator identity classes.
IDENTITY_VERIFIED = "verified_remote_operator"
IDENTITY_UNVERIFIED = "unverified_operator"
IDENTITY_UNKNOWN = "unknown_operator"
_VERIFIED_IDENTITY_CLASSES = frozenset({IDENTITY_VERIFIED})

# 0174TG blocked-reason classes.
BLOCK_BAD_SURFACE = "inbound_surface_class_not_telegram_remote_operator"
BLOCK_OPERATOR_NOT_VERIFIED = "operator_identity_not_verified"
BLOCK_MISSING_CHAT_BINDING = "chat_binding_missing"
BLOCK_FORBIDDEN_VALUE = "forbidden_value_detected"
BLOCK_MISSING_INBOUND_FIELD = "required_inbound_field_missing"

# 0174TH intent classes.
INTENT_EXPLICIT_REVIEW_REQUEST = "explicit_review_request"
INTENT_EXPLICIT_APPROVE = "explicit_approve"
INTENT_EXPLICIT_REJECT = "explicit_reject"
INTENT_EXPLICIT_EDIT_REQUEST = "explicit_edit_request"
INTENT_STATUS_REQUEST = "status_request"
INTENT_CANCEL_REQUEST = "cancel_request"
INTENT_AMBIGUOUS = "ambiguous_or_unsupported"

SUPPORTED_INTENT_CLASSES = (
    INTENT_EXPLICIT_REVIEW_REQUEST,
    INTENT_EXPLICIT_APPROVE,
    INTENT_EXPLICIT_REJECT,
    INTENT_EXPLICIT_EDIT_REQUEST,
    INTENT_STATUS_REQUEST,
    INTENT_CANCEL_REQUEST,
    INTENT_AMBIGUOUS,
)

# 0174TI review challenge status classes.
CHALLENGE_PENDING = "pending"
CHALLENGE_APPROVED = "approved"
CHALLENGE_REJECTED = "rejected"
CHALLENGE_EXPIRED = "expired"
CHALLENGE_INVALIDATED = "invalidated"

# 0174TI validation outcome classes.
REVIEW_APPROVED_NOT_DISPATCHED = "remote_review_approved_not_dispatched"
REVIEW_NOT_APPROVED = "remote_review_not_approved"
REVIEW_FAIL_CLOSED = "remote_review_fail_closed_forbidden_value"

# 0174TI blocked-reason classes.
BLOCK_OPERATOR_MISMATCH = "challenge_operator_mismatch"
BLOCK_INTENT_NOT_APPROVE = "inbound_intent_not_explicit_approve"
BLOCK_CHALLENGE_NOT_PENDING = "challenge_not_pending"
BLOCK_CHALLENGE_EXPIRED = "challenge_expired"
BLOCK_CHALLENGE_ID_MISMATCH = "challenge_id_mismatch"
BLOCK_APPROVAL_PHRASE_MISMATCH = "approval_phrase_mismatch"
BLOCK_OUTBOX_ENTRY_MISMATCH = "outbox_entry_id_mismatch"
BLOCK_IDEMPOTENCY_KEY_MISMATCH = "idempotency_key_mismatch"
BLOCK_PAYLOAD_HASH_MISMATCH = "payload_hash_mismatch"
BLOCK_NONCE_MISMATCH = "one_time_nonce_mismatch"
BLOCK_CHALLENGE_FORBIDDEN_VALUE = "challenge_forbidden_value_detected"

# 0174TI R1: 0174EE outbox-authority gate block-reason classes. A review
# challenge may only be created from a genuine, eligible 0174EE local outbox
# record -- never a synthetic/outbox-like dict or a live/dispatch-flagged entry.
BLOCK_OUTBOX_NOT_0174EE_AUTHORITY = "outbox_entry_not_0174ee_authority"
BLOCK_OUTBOX_STATE_NOT_LOCAL_RECORD = (
    "outbox_entry_state_not_local_record_created")
BLOCK_OUTBOX_NOT_ELIGIBLE = "outbox_entry_not_eligible_for_review"
BLOCK_OUTBOX_LIVE_OR_DISPATCH_FLAG = "outbox_entry_live_or_dispatch_flag_set"
BLOCK_OUTBOX_REQUIRED_FIELD_MISSING = "outbox_entry_required_field_missing"
BLOCK_OUTBOX_FORBIDDEN_VALUE = "outbox_entry_forbidden_value_detected"

# Required (non-empty) fields on a normalized inbound envelope.
REQUIRED_INBOUND_FIELDS = (
    "inbound_message_id",
    "received_at_epoch",
    "operator_id",
    "operator_identity_class",
    "chat_binding_id",
    "message_text_redacted",
)

# Authority fields that must match between an outbox entry and a challenge.
_OUTBOX_BIND_FIELDS = (
    "outbox_entry_id",
    "idempotency_key",
    "payload_hash",
    "approval_ledger_entry_id",
    "platform",
    "destination_binding_id",
    "credential_handle_id",
    "visibility_class",
)

DEFAULT_APPROVAL_PHRASE = "APPROVE"


# --------------------------------------------------------------------------- #
# Redaction + deterministic serialization (reuse the 0174ED scanner family).
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


def compute_message_hash(message_text_redacted, inbound_message_id,
                         received_at_epoch, operator_id):
    """Deterministic provenance hash over symbolic, redacted message fields.

    The hash binds the REDACTED message text and symbolic envelope identifiers
    only. It is a non-secret content fingerprint, never derived from raw chat
    ids, usernames, phones, tokens, or raw provider update objects.
    """
    provenance = {
        "inbox_schema": INBOX_SCHEMA,
        "inbox_schema_version": INBOX_SCHEMA_VERSION,
        "message_text_redacted": message_text_redacted,
        "inbound_message_id": inbound_message_id,
        "received_at_epoch": int(received_at_epoch),
        "operator_id": operator_id,
    }
    return hashlib.sha256(serialize(provenance).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# 0174TG: Remote operator inbox contract
# --------------------------------------------------------------------------- #
def normalize_inbound_envelope(raw_message, *, expected_operator_id=None):
    """Normalize a Telegram-LIKE inbound message into a symbolic inbox record.

    ``raw_message`` is a plain dict of SYMBOLIC fields only (the caller is
    responsible for never handing us a raw Telegram update object; if one is
    handed in, the fail-closed scanner rejects it). Recognized symbolic fields:

      * ``source_surface_class`` (must be ``telegram_remote_operator_surface``)
      * ``inbound_message_id``
      * ``received_at_epoch``
      * ``operator_id``
      * ``operator_identity_class``
      * ``chat_binding_id`` (a symbolic 0174-style binding id, NOT a raw chat id)
      * ``chat_binding_hash`` (optional; symbolic)
      * ``message_text_redacted``
      * ``reply_to_challenge_id`` (optional)
      * ``linked_outbox_entry_id`` (optional)
      * ``linked_idempotency_key`` (optional; only the short form is persisted)
      * ``inbound_status`` (optional override; ignored for authority)

    Fail-closed rules:
      * forbidden/raw material (raw chat id, username, phone, token, bot token,
        webhook url, raw provider update JSON) => FAIL_CLOSED, nothing persisted;
      * wrong surface class => BLOCKED;
      * operator identity class not verified => BLOCKED;
      * missing chat binding => BLOCKED;
      * any required field missing => BLOCKED.

    NO Telegram behavior is performed: this only reshapes an in-memory dict.
    """
    raw = raw_message or {}
    blocked = []

    # 1. Fail-closed redaction scan of the ENTIRE caller-supplied object first.
    #    A raw Telegram update object (with chat ids, usernames, tokens, etc.)
    #    trips this and is rejected before anything is persisted.
    forbidden = scan_for_leaks(raw)
    forbidden_detected = bool(forbidden)
    if forbidden_detected:
        return {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": InboxStatus.FAIL_CLOSED,
            "inbound_status_class": INBOX_FAIL_CLOSED,
            "record": None,
            "blocked_reasons": [BLOCK_FORBIDDEN_VALUE],
            "forbidden_fields_detected": True,
            "redaction_verified": False,
            **_inbox_safety_flags(),
        }

    surface = raw.get("source_surface_class")
    operator_id = raw.get("operator_id")
    identity_class = raw.get("operator_identity_class")
    chat_binding_id = raw.get("chat_binding_id")

    # 2. Surface class must be exactly the telegram remote operator surface.
    if surface != SOURCE_SURFACE_CLASS:
        blocked.append(BLOCK_BAD_SURFACE)

    # 3. Operator identity must be a verified class.
    if identity_class not in _VERIFIED_IDENTITY_CLASSES:
        blocked.append(BLOCK_OPERATOR_NOT_VERIFIED)

    # 4. Chat binding must be present (symbolic binding id).
    if not chat_binding_id:
        blocked.append(BLOCK_MISSING_CHAT_BINDING)

    # 5. Required inbound fields must be present (non-empty).
    for field in REQUIRED_INBOUND_FIELDS:
        if not raw.get(field):
            reason = BLOCK_MISSING_INBOUND_FIELD + ":" + field
            if reason not in blocked:
                blocked.append(reason)

    # 6. Optional cross-check: declared operator must match an expected operator.
    if (expected_operator_id is not None
            and operator_id != expected_operator_id):
        blocked.append(BLOCK_OPERATOR_NOT_VERIFIED)

    if blocked:
        return {
            "task_label": TASK_LABEL,
            "model": MODEL,
            "model_version": MODEL_VERSION,
            "status": InboxStatus.BLOCKED,
            "inbound_status_class": INBOX_BLOCKED,
            "record": None,
            "blocked_reasons": sorted(set(blocked)),
            "forbidden_fields_detected": False,
            "redaction_verified": True,
            **_inbox_safety_flags(),
        }

    message_text_redacted = raw.get("message_text_redacted")
    message_hash = compute_message_hash(
        message_text_redacted, raw.get("inbound_message_id"),
        raw.get("received_at_epoch"), operator_id)

    linked_key = raw.get("linked_idempotency_key")
    record = {
        "inbox_schema": INBOX_SCHEMA,
        "inbox_schema_version": INBOX_SCHEMA_VERSION,
        "source_surface_class": SOURCE_SURFACE_CLASS,
        "inbound_message_id": raw.get("inbound_message_id"),
        "received_at_epoch": int(raw.get("received_at_epoch")),
        "operator_id": operator_id,
        "operator_identity_class": identity_class,
        "chat_binding_id": chat_binding_id,
        "chat_binding_hash": raw.get("chat_binding_hash"),
        "message_text_redacted": message_text_redacted,
        "message_provenance_hash": message_hash,
        "message_provenance_hash_short": _short(message_hash),
        "reply_to_challenge_id": raw.get("reply_to_challenge_id"),
        "linked_outbox_entry_id": raw.get("linked_outbox_entry_id"),
        "linked_idempotency_key_short": (
            _short(linked_key) if linked_key else None),
        "inbound_status_class": INBOX_NORMALIZED,
        # Hard safety invariants -- ALWAYS these values.
        **_inbox_safety_flags(),
    }
    record["record_checksum"] = compute_checksum(record)
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": InboxStatus.PASS,
        "inbound_status_class": INBOX_NORMALIZED,
        "record": record,
        "blocked_reasons": [],
        "forbidden_fields_detected": False,
        "redaction_verified": True,
        **_inbox_safety_flags(),
    }


def _inbox_safety_flags():
    """The hard-coded safety invariants attached to every 0174TG result."""
    return {
        "telegram_api_called": False,
        "bot_polling_performed": False,
        "get_updates_performed": False,
        "send_message_performed": False,
        "webhook_registered": False,
        "network_performed": False,
        "raw_telegram_update_persisted": False,
        "credential_hydrated": False,
        "llm_behavior": False,
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "scheduler_enabled": False,
        "auto_retry_allowed": False,
        "autonomous_reply_performed": False,
    }


class RemoteOperatorInboxRegistry:
    """An append-only, local-only registry of normalized inbox records.

    Nothing is mutated in place; only PASS records (symbolic, redacted) may be
    appended. A record carrying forbidden material can never be appended because
    ``normalize_inbound_envelope`` fails closed before producing a record.
    """

    def __init__(self):
        self._records = []
        self._by_message_id = {}

    def _copy(self, obj):
        return json.loads(json.dumps(obj))

    def append(self, normalize_result):
        """Append a PASS inbox record. Raises ValueError on a non-PASS result."""
        res = normalize_result or {}
        if res.get("status") != InboxStatus.PASS or not res.get("record"):
            raise ValueError("cannot append: inbound normalization did not pass")
        record = res["record"]
        # Defense-in-depth: never append anything that trips the scanner.
        violations = scan_for_leaks(record)
        if violations:
            raise ValueError(f"record failed redaction scan: {violations}")
        mid = record.get("inbound_message_id")
        self._records.append(self._copy(record))
        self._by_message_id[mid] = record.get("message_provenance_hash")
        return self._copy(record)

    @property
    def records(self):
        return self._copy(self._records)

    def record_count(self):
        return len(self._records)

    def find_by_message_id(self, inbound_message_id):
        for r in self._records:
            if r.get("inbound_message_id") == inbound_message_id:
                return self._copy(r)
        return None


# --------------------------------------------------------------------------- #
# 0174TH: Intent parser contract (deterministic, rule-based; NO LLM)
# --------------------------------------------------------------------------- #
def build_intent_policy_snapshot():
    """Return the deterministic IntentParserPolicySnapshot (pure value)."""
    return {
        "intent_schema": INTENT_SCHEMA,
        "intent_schema_version": INTENT_SCHEMA_VERSION,
        "parser_kind": "deterministic_rule_based_no_llm",
        "supported_intent_classes": list(SUPPORTED_INTENT_CLASSES),
        "approval_requires_exact_phrase_or_challenge_id": True,
        "fails_closed_on_ambiguity": True,
        "casual_agreement_is_not_approval": True,
        "llm_behavior": False,
        "creates_approval_or_dispatch_state": False,
    }


# Exact command tokens (case-insensitive, after normalization). Each maps a
# single explicit command word to a bounded intent. Approval is deliberately
# excluded here: approval requires the exact challenge phrase or challenge id.
_COMMAND_TOKENS = {
    "REVIEW": INTENT_EXPLICIT_REVIEW_REQUEST,
    "REJECT": INTENT_EXPLICIT_REJECT,
    "DENY": INTENT_EXPLICIT_REJECT,
    "EDIT": INTENT_EXPLICIT_EDIT_REQUEST,
    "REVISE": INTENT_EXPLICIT_EDIT_REQUEST,
    "STATUS": INTENT_STATUS_REQUEST,
    "CANCEL": INTENT_CANCEL_REQUEST,
    "ABORT": INTENT_CANCEL_REQUEST,
}

# Vague-agreement phrases that MUST NOT be treated as approval.
_VAGUE_AGREEMENT = frozenset({
    "looks good", "lgtm", "ok", "okay", "sure", "fine", "nice", "great",
    "good", "yes", "yep", "yeah", "cool", "perfect", "love it", "+1",
    "thumbs up", "go ahead", "sounds good", "approve?",
})

_WORD_RE = re.compile(r"[A-Za-z0-9_]+")


def _normalize_text(text):
    """Lowercase, collapse whitespace; used for casual-agreement detection."""
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def parse_operator_intent(inbox_record, *, expected_challenge_id=None,
                          required_approval_phrase=DEFAULT_APPROVAL_PHRASE,
                          policy_snapshot=None):
    """Deterministically classify an inbox record's redacted text into an intent.

    This is a rule-based parser ONLY -- it never calls an LLM. It preserves the
    source message provenance hash and never creates approval, outbox, dispatch,
    or live state. ``explicit_approve`` is produced ONLY when the message is the
    EXACT required approval phrase, or the exact expected challenge id is present
    alongside that phrase. Vague agreement, emoji, or partial matches fail closed
    to ``ambiguous_or_unsupported``.
    """
    policy = policy_snapshot or build_intent_policy_snapshot()
    rec = inbox_record or {}

    text_redacted = rec.get("message_text_redacted")
    provenance_hash = rec.get("message_provenance_hash")

    # Fail-closed scan: the parser must never ingest forbidden material.
    forbidden = scan_for_leaks({"message_text_redacted": text_redacted})
    if forbidden:
        return _intent_result(
            INTENT_AMBIGUOUS, rec, policy, confidence="fail_closed",
            matched_token=None, provenance_hash=provenance_hash,
            forbidden_detected=True)

    raw_text = str(text_redacted or "")
    normalized = _normalize_text(raw_text)
    phrase = str(required_approval_phrase or DEFAULT_APPROVAL_PHRASE)

    # 1. Exact explicit approval: the whole message is exactly the phrase, OR
    #    the phrase plus the exact expected challenge id (and nothing ambiguous).
    stripped = raw_text.strip()
    tokens = _WORD_RE.findall(stripped)
    token_set_upper = {t.upper() for t in tokens}

    if stripped == phrase:
        return _intent_result(
            INTENT_EXPLICIT_APPROVE, rec, policy, confidence="exact_phrase",
            matched_token=phrase, provenance_hash=provenance_hash)

    if (expected_challenge_id
            and phrase.upper() in token_set_upper
            and expected_challenge_id in tokens):
        # Exact phrase token + exact challenge id token, no conflicting command.
        conflicting = token_set_upper & set(_COMMAND_TOKENS.keys())
        if not conflicting:
            return _intent_result(
                INTENT_EXPLICIT_APPROVE, rec, policy,
                confidence="phrase_plus_challenge_id",
                matched_token=phrase, provenance_hash=provenance_hash)

    # 2. Casual / vague agreement must NEVER be approval -> ambiguous.
    if normalized in _VAGUE_AGREEMENT:
        return _intent_result(
            INTENT_AMBIGUOUS, rec, policy, confidence="vague_agreement",
            matched_token=None, provenance_hash=provenance_hash)

    # 3. Single explicit command token (REVIEW/REJECT/EDIT/STATUS/CANCEL...).
    command_hits = sorted(token_set_upper & set(_COMMAND_TOKENS.keys()))
    if len(command_hits) == 1:
        token = command_hits[0]
        return _intent_result(
            _COMMAND_TOKENS[token], rec, policy, confidence="explicit_command",
            matched_token=token, provenance_hash=provenance_hash)

    # 4. Anything else (no command, multiple conflicting commands, partial
    #    approval, emoji, free text) fails closed to ambiguous.
    return _intent_result(
        INTENT_AMBIGUOUS, rec, policy, confidence="no_exact_match",
        matched_token=None, provenance_hash=provenance_hash)


def _intent_result(intent_class, rec, policy, *, confidence, matched_token,
                   provenance_hash, forbidden_detected=False):
    """Build a deterministic OperatorIntentParseResult (pure value)."""
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "intent_schema": INTENT_SCHEMA,
        "intent_schema_version": INTENT_SCHEMA_VERSION,
        "intent_class": intent_class,
        "is_explicit_approve": intent_class == INTENT_EXPLICIT_APPROVE,
        "confidence_class": confidence,
        "matched_token": matched_token,
        "source_message_provenance_hash": provenance_hash,
        "source_message_provenance_hash_short": (
            _short(provenance_hash) if provenance_hash else None),
        "inbound_message_id": (rec or {}).get("inbound_message_id"),
        "operator_id": (rec or {}).get("operator_id"),
        "reply_to_challenge_id": (rec or {}).get("reply_to_challenge_id"),
        "policy_snapshot": policy,
        "forbidden_fields_detected": forbidden_detected,
        # Hard safety invariants -- a parse NEVER creates state.
        "creates_approval_state": False,
        "creates_outbox_state": False,
        "creates_dispatch_state": False,
        "llm_behavior": False,
        "network_performed": False,
        "credential_hydrated": False,
        "dispatch_performed": False,
        "live_request_performed": False,
    }


# --------------------------------------------------------------------------- #
# 0174TI: Telegram review challenge contract
# --------------------------------------------------------------------------- #
def _challenge_safety_flags():
    """Hard-coded safety invariants attached to every 0174TI object."""
    return {
        "dispatch_performed": False,
        "live_request_performed": False,
        "platform_api_called": False,
        "telegram_send_performed": False,
        "credential_hydrated": False,
        "llm_behavior": False,
        "network_performed": False,
        "scheduler_enabled": False,
        "auto_retry_allowed": False,
        "autonomous_reply_performed": False,
        "dispatch_ready": False,
        "live_ready": False,
    }


# --------------------------------------------------------------------------- #
# 0174TI R1: 0174EE outbox-entry authority gate.
# --------------------------------------------------------------------------- #
# Flags that MUST be present and True on a valid 0174EE outbox entry.
_OUTBOX_REQUIRED_TRUE_FLAGS = (
    "outbox_created",
    "eligible_for_local_outbox",
)

# Flags that MUST be present and False on a valid 0174EE outbox entry.
_OUTBOX_REQUIRED_FALSE_FLAGS = (
    "dispatch_performed",
    "live_request_performed",
    "platform_api_called",
    "credential_hydrated",
    "auto_retry_allowed",
    "scheduler_enabled",
    "telegram_behavior",
    "llm_behavior",
    "dispatch_ready",
    "live_ready",
)

# Authority fields that MUST be present (non-empty) on a valid 0174EE entry.
_OUTBOX_REQUIRED_AUTHORITY_FIELDS = (
    "outbox_entry_id",
    "idempotency_key",
    "payload_hash",
    "approval_ledger_entry_id",
    "platform",
    "destination_binding_id",
    "credential_handle_id",
    "visibility_class",
    "dispatch_intent_class",
)


def validate_0174ee_outbox_entry_for_review_challenge(outbox_entry):
    """Fail-closed proof that ``outbox_entry`` is a genuine 0174EE local outbox
    record eligible to back a remote review challenge.

    Returns a deterministic result dict::

        {"valid": bool,
         "blocked_reasons": [...],
         "forbidden_fields_detected": bool}

    Rejects (``valid`` False) an arbitrary outbox-like dict, a duplicate-
    suppressed registry result, a record missing the exact 0174EE model /
    model_version / state authority stamp, a record that is not explicitly
    created + eligible for local outbox, a record with ANY live / dispatch /
    platform / credential / scheduler / telegram / llm flag set true, a record
    missing a required authority field, or a record carrying forbidden raw
    credential / provider / Telegram material. Performs NO side effect, NEVER
    dispatches, and NEVER hydrates credentials.
    """
    entry = outbox_entry if isinstance(outbox_entry, dict) else {}
    blocked = []

    # 1. Fail-closed redaction scan FIRST: never reason about forbidden material.
    if scan_for_leaks(outbox_entry or {}):
        return {
            "valid": False,
            "blocked_reasons": [BLOCK_OUTBOX_FORBIDDEN_VALUE],
            "forbidden_fields_detected": True,
        }

    if not isinstance(outbox_entry, dict) or not entry:
        blocked.append(BLOCK_OUTBOX_NOT_0174EE_AUTHORITY)

    # 2. Exact 0174EE model + version authority stamp.
    if (entry.get("model") != outbox.MODEL
            or entry.get("model_version") != outbox.MODEL_VERSION):
        blocked.append(BLOCK_OUTBOX_NOT_0174EE_AUTHORITY)

    # 3. State must be the local-record-created class (rejects duplicate-
    #    suppressed results and any other state).
    if entry.get("state_class") != outbox.STATE_LOCAL_RECORD_CREATED:
        blocked.append(BLOCK_OUTBOX_STATE_NOT_LOCAL_RECORD)

    # 4. Must be explicitly created + eligible for local outbox.
    if any(entry.get(flag) is not True
           for flag in _OUTBOX_REQUIRED_TRUE_FLAGS):
        blocked.append(BLOCK_OUTBOX_NOT_ELIGIBLE)

    # 5. No live / dispatch / platform / credential / scheduler / telegram /
    #    llm flag may be set (each must be explicitly present and False).
    if any(entry.get(flag) is not False
           for flag in _OUTBOX_REQUIRED_FALSE_FLAGS):
        blocked.append(BLOCK_OUTBOX_LIVE_OR_DISPATCH_FLAG)

    # 6. Required authority fields present (non-empty).
    for field in _OUTBOX_REQUIRED_AUTHORITY_FIELDS:
        if not entry.get(field):
            blocked.append(BLOCK_OUTBOX_REQUIRED_FIELD_MISSING + ":" + field)

    return {
        "valid": not blocked,
        "blocked_reasons": sorted(set(blocked)),
        "forbidden_fields_detected": False,
    }


def create_review_challenge(outbox_entry, challenge_id, operator_id,
                            created_at_epoch, expires_at_epoch,
                            *, one_time_nonce=None,
                            required_approval_phrase=DEFAULT_APPROVAL_PHRASE,
                            preview_summary_redacted="redacted",
                            dispatch_intent_class=None):
    """Create a local RemoteReviewChallenge bound to an EXACT 0174EE outbox entry.

    Consumes a 0174EE outbox entry (the append-ready record produced by
    ``DispatchOutboxRegistry.submit(...)["entry"]`` or ``build_outbox_entry``).
    The challenge binds the exact outbox entry id, idempotency key, and payload
    hash, and requires an exact human approval phrase. It NEVER hydrates
    credentials and NEVER dispatches. Fail-closed: raises ValueError if the
    outbox entry carries forbidden material or is missing required binding
    fields.
    """
    entry = outbox_entry or {}

    violations = scan_for_leaks(entry)
    if violations:
        raise ValueError(f"outbox entry failed redaction scan: {violations}")

    # R1: prove the entry is a genuine, eligible 0174EE local outbox record
    # BEFORE binding a challenge to it. A synthetic/outbox-like dict, a
    # duplicate-suppressed result, or a live/dispatch-flagged entry fails here.
    authority = validate_0174ee_outbox_entry_for_review_challenge(entry)
    if not authority["valid"]:
        raise ValueError(
            "outbox entry is not a valid 0174EE authority for a review "
            f"challenge: {authority['blocked_reasons']}")

    for field in ("outbox_entry_id", "idempotency_key", "payload_hash"):
        if not entry.get(field):
            raise ValueError(f"outbox entry missing required field: {field}")

    challenge = {
        "challenge_schema": CHALLENGE_SCHEMA,
        "challenge_schema_version": CHALLENGE_SCHEMA_VERSION,
        "challenge_id": challenge_id,
        "outbox_entry_id": entry.get("outbox_entry_id"),
        "idempotency_key": entry.get("idempotency_key"),
        "idempotency_key_short": _short(entry.get("idempotency_key")),
        "payload_hash": entry.get("payload_hash"),
        "payload_hash_short": _short(entry.get("payload_hash")),
        "approval_ledger_entry_id": entry.get("approval_ledger_entry_id"),
        "platform": entry.get("platform"),
        "destination_binding_id": entry.get("destination_binding_id"),
        "credential_handle_id": entry.get("credential_handle_id"),
        "visibility_class": entry.get("visibility_class"),
        "dispatch_intent_class": (
            dispatch_intent_class or entry.get("dispatch_intent_class")),
        "operator_id": operator_id,
        "created_at_epoch": int(created_at_epoch),
        "expires_at_epoch": int(expires_at_epoch),
        "one_time_nonce": one_time_nonce or challenge_id,
        "required_approval_phrase": str(
            required_approval_phrase or DEFAULT_APPROVAL_PHRASE),
        "preview_summary_redacted": preview_summary_redacted,
        "challenge_status": CHALLENGE_PENDING,
        **_challenge_safety_flags(),
    }
    challenge["challenge_checksum"] = compute_checksum(challenge)
    return challenge


def validate_review_challenge_response(challenge, intent_result, outbox_entry,
                                       *, now_epoch, responding_operator_id,
                                       provided_nonce=None):
    """Re-derive whether a challenge response is a valid remote review approval.

    Fail-closed and non-side-effecting. A response validates as an approval ONLY
    if ALL hold:
      * neither the challenge, intent result, nor outbox entry carry forbidden
        material (else fail_closed);
      * the responding operator matches the challenge operator;
      * the inbound intent is ``explicit_approve``;
      * the challenge status is pending;
      * the challenge is not expired (now <= expires_at);
      * the intent's ``reply_to_challenge_id`` matches the challenge id;
      * the required approval phrase was matched (the parser produced
        ``explicit_approve`` against the same required phrase);
      * the outbox entry id, idempotency key, and payload hash still match the
        challenge binding;
      * the one-time nonce matches (when provided).
    Even when valid, the outcome is ``remote_review_approved_not_dispatched`` --
    NEVER dispatch. Reject/edit/status/cancel never validate as approval.
    """
    ch = challenge or {}
    ir = intent_result or {}
    entry = outbox_entry or {}
    blocked = []

    forbidden = scan_for_leaks([ch, ir, entry])
    if forbidden:
        return _review_result(
            REVIEW_FAIL_CLOSED, ch, blocked=[BLOCK_CHALLENGE_FORBIDDEN_VALUE],
            approved=False, forbidden_detected=True)

    # Operator identity must match the challenge operator.
    if responding_operator_id != ch.get("operator_id"):
        blocked.append(BLOCK_OPERATOR_MISMATCH)

    # Inbound intent must be an explicit approve.
    if ir.get("intent_class") != INTENT_EXPLICIT_APPROVE:
        blocked.append(BLOCK_INTENT_NOT_APPROVE)

    # Challenge must be pending.
    if ch.get("challenge_status") != CHALLENGE_PENDING:
        blocked.append(BLOCK_CHALLENGE_NOT_PENDING)

    # Challenge must not be expired.
    expires_at = ch.get("expires_at_epoch")
    if expires_at is None or int(now_epoch) > int(expires_at):
        blocked.append(BLOCK_CHALLENGE_EXPIRED)

    # Intent must reference the same challenge id.
    if ir.get("reply_to_challenge_id") != ch.get("challenge_id"):
        blocked.append(BLOCK_CHALLENGE_ID_MISMATCH)

    # The parser must have matched the exact required approval phrase.
    if ir.get("matched_token") != ch.get("required_approval_phrase"):
        blocked.append(BLOCK_APPROVAL_PHRASE_MISMATCH)

    # Outbox binding must still match (entry id / key / payload hash).
    if entry.get("outbox_entry_id") != ch.get("outbox_entry_id"):
        blocked.append(BLOCK_OUTBOX_ENTRY_MISMATCH)
    if entry.get("idempotency_key") != ch.get("idempotency_key"):
        blocked.append(BLOCK_IDEMPOTENCY_KEY_MISMATCH)
    if entry.get("payload_hash") != ch.get("payload_hash"):
        blocked.append(BLOCK_PAYLOAD_HASH_MISMATCH)

    # One-time nonce must match when supplied by the caller.
    if provided_nonce is not None and provided_nonce != ch.get("one_time_nonce"):
        blocked.append(BLOCK_NONCE_MISMATCH)

    if blocked:
        return _review_result(
            REVIEW_NOT_APPROVED, ch, blocked=sorted(set(blocked)),
            approved=False, forbidden_detected=False)

    return _review_result(
        REVIEW_APPROVED_NOT_DISPATCHED, ch, blocked=[], approved=True,
        forbidden_detected=False)


def _review_result(outcome_class, ch, *, blocked, approved, forbidden_detected):
    """Build a deterministic RemoteReviewChallengeValidation (pure value)."""
    status = (InboxStatus.PASS if approved
              else (InboxStatus.FAIL_CLOSED if forbidden_detected
                    else InboxStatus.BLOCKED))
    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": status,
        "review_outcome_class": outcome_class,
        "approved_not_dispatched": approved,
        "challenge_id": (ch or {}).get("challenge_id"),
        "outbox_entry_id": (ch or {}).get("outbox_entry_id"),
        "idempotency_key_short": _short((ch or {}).get("idempotency_key") or ""),
        "payload_hash_short": _short((ch or {}).get("payload_hash") or ""),
        "operator_id": (ch or {}).get("operator_id"),
        "blocked_reasons": blocked,
        "forbidden_fields_detected": forbidden_detected,
        # Hard invariants: remote approval is NEVER dispatch.
        **_challenge_safety_flags(),
        "remote_approval_is_dispatch": False,
        "challenge_approval_is_platform_posting": False,
    }


class RemoteReviewChallengeRegistry:
    """An append-only, local-only registry of review challenges.

    Enforces challenge-id uniqueness with deterministic duplicate suppression
    (never appends a second challenge for the same id). Supports revocation /
    invalidation as a NEW status-bearing copy; a revoked/invalidated challenge
    blocks later approval (validation sees a non-pending status).
    """

    def __init__(self):
        self._challenges = []
        self._by_id = {}

    def _copy(self, obj):
        return json.loads(json.dumps(obj))

    def has_challenge(self, challenge_id):
        return challenge_id in self._by_id

    def append(self, challenge):
        """Append a pending challenge, or suppress a duplicate id.

        Returns a deterministic result dict. Fresh id => appended True. Duplicate
        id => appended False, ``duplicate_suppressed`` True, nothing mutated.
        """
        ch = challenge or {}
        violations = scan_for_leaks(ch)
        if violations:
            raise ValueError(f"challenge failed redaction scan: {violations}")
        cid = ch.get("challenge_id")
        if not cid:
            raise ValueError("cannot append: missing challenge id")
        if cid in self._by_id:
            return {
                "status": InboxStatus.PASS,
                "appended": False,
                "duplicate_suppressed": True,
                "challenge_id": cid,
            }
        self._challenges.append(self._copy(ch))
        self._by_id[cid] = ch.get("challenge_status")
        return {
            "status": InboxStatus.PASS,
            "appended": True,
            "duplicate_suppressed": False,
            "challenge_id": cid,
        }

    def revoke(self, challenge_id, *, revoked_at_epoch, operator_id,
               reason_class="operator_revoked"):
        """Append a NEW invalidated copy of the challenge (never mutates).

        After revocation, ``current_status`` for the id is invalidated, so a
        later approval validation blocks on a non-pending challenge.
        """
        if challenge_id not in self._by_id:
            raise ValueError("cannot revoke: unknown challenge id")
        latest = self.current(challenge_id) or {}
        invalidated = self._copy(latest)
        invalidated["challenge_status"] = CHALLENGE_INVALIDATED
        invalidated["revoked_at_epoch"] = int(revoked_at_epoch)
        invalidated["revoked_by_operator_id"] = operator_id
        invalidated["revocation_reason_class"] = reason_class
        invalidated["challenge_checksum"] = compute_checksum(
            {k: v for k, v in invalidated.items()
             if k != "challenge_checksum"})
        self._challenges.append(invalidated)
        self._by_id[challenge_id] = CHALLENGE_INVALIDATED
        return self._copy(invalidated)

    def current(self, challenge_id):
        """Return the LATEST appended copy of a challenge id (or None)."""
        latest = None
        for c in self._challenges:
            if c.get("challenge_id") == challenge_id:
                latest = c
        return self._copy(latest) if latest is not None else None

    def current_status(self, challenge_id):
        return self._by_id.get(challenge_id)

    @property
    def challenges(self):
        return self._copy(self._challenges)

    def challenge_count(self):
        return len(self._challenges)


# --------------------------------------------------------------------------- #
# Redacted audit
# --------------------------------------------------------------------------- #
def build_redacted_review_audit(challenge, validation_result):
    """Build a redacted audit summary containing symbolic/redacted values only.

    Stores short hashes (non-secret content fingerprints) and symbolic classes,
    never raw Telegram/provider material, raw chat ids, usernames, phones,
    tokens, webhook urls, or any credential material.
    """
    ch = challenge or {}
    vr = validation_result or {}
    audit = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "audit_kind": "redacted_remote_review_audit",
        "challenge_id": ch.get("challenge_id"),
        "outbox_entry_id": ch.get("outbox_entry_id"),
        "idempotency_key_short": ch.get("idempotency_key_short"),
        "payload_hash_short": ch.get("payload_hash_short"),
        "approval_ledger_entry_id": ch.get("approval_ledger_entry_id"),
        "platform": ch.get("platform"),
        "operator_id": ch.get("operator_id"),
        "review_outcome_class": vr.get("review_outcome_class"),
        "approved_not_dispatched": vr.get("approved_not_dispatched", False),
        "blocked_reasons": vr.get("blocked_reasons", []),
        "no_raw_telegram_update_stored": True,
        "no_raw_chat_id_stored": True,
        "no_raw_username_or_phone_stored": True,
        "no_raw_token_or_webhook_stored": True,
        "no_raw_credential_stored": True,
        "no_credential_hash_or_fingerprint_created": True,
        **_challenge_safety_flags(),
    }
    audit["audit_checksum"] = compute_checksum(audit)
    return audit


# --------------------------------------------------------------------------- #
# Model packet + doc builders
# --------------------------------------------------------------------------- #
def build_packet():
    """Build the deterministic redacted 0174TG/TH/TI model packet."""
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inbox_schema": INBOX_SCHEMA,
        "inbox_schema_version": INBOX_SCHEMA_VERSION,
        "intent_schema": INTENT_SCHEMA,
        "intent_schema_version": INTENT_SCHEMA_VERSION,
        "challenge_schema": CHALLENGE_SCHEMA,
        "challenge_schema_version": CHALLENGE_SCHEMA_VERSION,
        "contract_status": "deterministic_local_remote_review_authority_ready",
        "source_surface_class": SOURCE_SURFACE_CLASS,
        "verified_identity_classes": [IDENTITY_VERIFIED],
        "supported_intent_classes": list(SUPPORTED_INTENT_CLASSES),
        "challenge_status_classes": [
            CHALLENGE_PENDING, CHALLENGE_APPROVED, CHALLENGE_REJECTED,
            CHALLENGE_EXPIRED, CHALLENGE_INVALIDATED,
        ],
        "review_outcome_classes": [
            REVIEW_APPROVED_NOT_DISPATCHED, REVIEW_NOT_APPROVED,
            REVIEW_FAIL_CLOSED,
        ],
        "inbox_blocked_reasons": [
            BLOCK_BAD_SURFACE, BLOCK_OPERATOR_NOT_VERIFIED,
            BLOCK_MISSING_CHAT_BINDING, BLOCK_FORBIDDEN_VALUE,
            BLOCK_MISSING_INBOUND_FIELD,
        ],
        "review_blocked_reasons": [
            BLOCK_OPERATOR_MISMATCH, BLOCK_INTENT_NOT_APPROVE,
            BLOCK_CHALLENGE_NOT_PENDING, BLOCK_CHALLENGE_EXPIRED,
            BLOCK_CHALLENGE_ID_MISMATCH, BLOCK_APPROVAL_PHRASE_MISMATCH,
            BLOCK_OUTBOX_ENTRY_MISMATCH, BLOCK_IDEMPOTENCY_KEY_MISMATCH,
            BLOCK_PAYLOAD_HASH_MISMATCH, BLOCK_NONCE_MISMATCH,
            BLOCK_CHALLENGE_FORBIDDEN_VALUE,
            BLOCK_OUTBOX_NOT_0174EE_AUTHORITY,
            BLOCK_OUTBOX_STATE_NOT_LOCAL_RECORD,
            BLOCK_OUTBOX_NOT_ELIGIBLE,
            BLOCK_OUTBOX_LIVE_OR_DISPATCH_FLAG,
            BLOCK_OUTBOX_REQUIRED_FIELD_MISSING,
            BLOCK_OUTBOX_FORBIDDEN_VALUE,
        ],
        "consumes_0174ee_outputs": [
            "outbox_entry_id", "idempotency_key", "payload_hash",
            "approval_ledger_entry_id",
        ],
        "invariants": [
            "inbound_blocked_unless_surface_is_telegram_remote_operator",
            "inbound_blocked_unless_operator_identity_verified",
            "inbound_blocked_unless_chat_binding_present",
            "raw_telegram_update_never_persisted",
            "raw_chat_id_username_phone_token_webhook_rejected_or_redacted",
            "message_provenance_hash_deterministic",
            "parser_is_deterministic_rule_based_no_llm",
            "parser_fails_closed_on_ambiguity",
            "casual_agreement_or_emoji_is_never_approval",
            "explicit_approve_requires_exact_phrase_or_challenge_id",
            "parser_never_creates_approval_outbox_or_dispatch_state",
            "review_challenge_binds_exact_outbox_entry_idempotency_and_hash",
            "review_challenge_requires_valid_0174ee_outbox_entry",
            "synthetic_outbox_like_dict_cannot_create_review_challenge",
            "duplicate_suppressed_result_cannot_create_review_challenge",
            "live_or_dispatched_outbox_entry_cannot_create_review_challenge",
            "review_blocked_on_outbox_or_payload_hash_substitution",
            "review_blocked_unless_intent_is_explicit_approve",
            "review_blocked_on_expired_or_non_pending_challenge",
            "review_blocked_on_wrong_operator_or_phrase_or_challenge_id",
            "revoked_challenge_blocks_later_approval",
            "duplicate_challenge_id_suppressed_not_appended",
            "remote_approval_is_not_dispatch",
            "challenge_approval_is_not_platform_posting",
            "review_challenge_never_hydrates_credentials",
            "audit_contains_redacted_values_only",
        ],
        "redaction_policy": {
            "fail_closed_on_forbidden_value": True,
            "credential_referenced_by_handle_id_only": True,
            "no_raw_telegram_update_stored": True,
            "no_raw_chat_id_username_phone_stored": True,
            "no_raw_token_or_webhook_url_stored": True,
            "scanner_source": "0174ED_approval_ledger_payload_hash_contract",
        },
        "safety_flags": {
            "telegram_api_called": False,
            "bot_polling_performed": False,
            "get_updates_performed": False,
            "send_message_performed": False,
            "webhook_registered": False,
            "llm_behavior": False,
            "dispatch_performed": False,
            "live_request_performed": False,
            "platform_api_called": False,
            "credential_hydrated": False,
            "scheduler_enabled": False,
            "auto_retry_allowed": False,
            "autonomous_reply_performed": False,
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
        "status": InboxStatus.PASS,
        "next_required_gate": NEXT_REQUIRED_GATE,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
    }
    packet["checksum_sha256"] = compute_checksum(packet)
    return packet


def build_doc():
    """Build the deterministic redacted 0174TG/TH/TI markdown documentation."""
    intents = "\n".join(f"- `{c}`" for c in SUPPORTED_INTENT_CLASSES)
    return f"""# Remote Operator Inbox + Intent + Review Challenge Contract (0174TG/TH/TI)

Task: {TASK_LABEL}
Model: {MODEL} ({MODEL_VERSION})
Source baseline commit: {SOURCE_BASELINE_COMMIT}
Mode: Implementation Mode. Deterministic, stdlib-only, local authority batch.

> [!IMPORTANT]
> This batch introduces NO Telegram behavior (no bot polling, no getUpdates, no
> sendMessage, no webhook, no Telegram SDK), NO LLM call, NO live dispatch, NO
> posting, NO platform API call, NO network call, NO credential read or
> hydration, NO environment or `.env` read, NO keyring or browser-session read,
> NO OAuth, NO scheduler, and NO auto retry. It is the deterministic local
> remote-operator inbox + intent parser + review challenge authority contract
> only.

## Strategic Posture
- Manual posting is the **fallback** path, not the strategic destination.
- **Automation is the main build path.**
- **Autonomous posting is forbidden.**
- **Supervised publishing is the final product.**

## What This Batch Proves
0174ED proved Jim approved an **exact payload hash**. 0174EE proved that exact,
validated approval becomes a **single local outbox candidate** without duplicate
dispatch risk. This batch proves the next three local authority steps WITHOUT
touching Telegram, an LLM, or any live surface:

- **0174TG Remote Operator Inbox** -- normalizes a Telegram-LIKE inbound message
  object into a symbolic, redacted `RemoteOperatorInboxRecord`. Only a verified
  operator class on the `{SOURCE_SURFACE_CLASS}` surface with a present chat
  binding continues. Raw chat id / username / phone / token / bot token /
  webhook url / raw provider update JSON are rejected or redacted; no raw
  Telegram update object is persisted.
- **0174TH Intent Parser** -- a deterministic, rule-based
  `parse_operator_intent` that simulates the boundary an LLM may later fill but
  NEVER calls an LLM. It fails closed on ambiguity and never treats vague
  agreement / emoji as approval. `explicit_approve` requires the exact challenge
  phrase (or the exact challenge id alongside the phrase).
- **0174TI Review Challenge** -- `create_review_challenge` consumes a valid
  0174EE outbox entry and binds the exact outbox entry id, idempotency key, and
  payload hash, requiring an exact human approval phrase.
  `validate_review_challenge_response` can only ever produce
  `{REVIEW_APPROVED_NOT_DISPATCHED}` -- never dispatch.

## Supported Intent Classes
{intents}

## Core Objects
- **RemoteOperatorInboundEnvelope / RemoteOperatorIdentityProof** -- the symbolic
  input shape consumed by `normalize_inbound_envelope`.
- **RemoteOperatorInboxRecord** -- the normalized, redacted record.
- **RemoteOperatorInboxRegistry** -- append-only local registry.
- **OperatorIntentCandidate / OperatorIntentParseResult /
  IntentParserPolicySnapshot** -- the deterministic parse boundary.
- **RemoteReviewChallenge / RemoteReviewChallengeValidation /
  RemoteReviewChallengeRegistry** -- the bound review-challenge authority.

## Hard Invariants
- Remote approval is **not** dispatch; challenge approval is **not** platform
  posting; the review challenge **never** hydrates credentials.
- No raw Telegram/provider update is stored; no raw token / api key / chat id /
  username / phone / webhook url is stored.
- The parser is deterministic and rule-based; it never calls an LLM and never
  creates approval, outbox, dispatch, or live state.
- A challenge binds the EXACT outbox entry id, idempotency key, and payload
  hash; changing any of them blocks validation.
- Reject / edit / status / cancel never validate as approval; a valid approval
  yields only `{REVIEW_APPROVED_NOT_DISPATCHED}`.
- A revoked/invalidated challenge blocks later approval; a duplicate challenge id
  is suppressed, not appended.
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
    """Write the deterministic 0174TG/TH/TI packet + doc under ``repo_root``.

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
