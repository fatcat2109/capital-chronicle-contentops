"""Approval ledger + payload hash contract (0174ED).

This module is the platform-agnostic, deterministic, LOCAL authority layer that
proves Jim approved an EXACT payload -- not a vague idea -- BEFORE any future
dispatch outbox, Telegram review challenge, LLM intent parsing, or supervised
live publishing is even considered.

It binds:
  * an exact payload (platform, text, formatting, destination binding,
    credential handle, media manifest, visibility, disclosure, content lane,
    policy snapshot, adapter version) to a deterministic sha256 payload hash,
  * an expiring, one-time approval challenge to that exact hash,
  * an append-only approval ledger entry recording the approval fact,
  * an append-only revocation event,
  * a DERIVED validation result that re-checks the current payload against the
    approved hash, expiration, and revocation -- validity is never assumed.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Pure Python stdlib only. No requests/httpx/aiohttp, no urllib request
    clients, no socket/ssl/http server, no selenium/playwright, no
    dotenv/keyring/sqlite, no openai/anthropic/telegram/tweepy SDKs.
  * NO network call of any kind.
  * NO env / .env / keyring / browser-session / credential-file read.
  * NO OAuth, token exchange/refresh, credential hydration.
  * NO live posting, mutation, scheduling, scraping, or dispatch.
  * Approval NEVER authorizes dispatch by itself: every result reports
    ``dispatch_ready = False`` and ``live_ready = False``.
  * Append-only: revocation/invalidation are NEW facts or DERIVED status, never
    mutation of a prior approval entry.
  * The payload hash is computed over NON-SECRET, authority-bearing fields
    only. Raw credential/token/api-key/env values are rejected by a fail-closed
    redaction scanner and never hashed, prefixed, suffixed, fingerprinted, or
    logged.

Importing this module performs NO writes and NO side effects. Artifacts are
written ONLY when ``write_artifacts(...)`` is called explicitly.
"""

import hashlib
import json
import os.path
import re

TASK_LABEL = (
    "TASK_CONTENTOPS_0174ED_APPROVAL_LEDGER_AND_PAYLOAD_HASH_CONTRACT_V0"
)
MODEL = "APPROVAL_LEDGER_PAYLOAD_HASH_CONTRACT_0174ED"
MODEL_VERSION = "0174ED_APPROVAL_LEDGER_PAYLOAD_HASH_V1"
# Schema/version constants mixed into the deterministic payload hash.
PAYLOAD_SCHEMA = "contentops.platform_payload_for_approval"
PAYLOAD_SCHEMA_VERSION = "0174ED_PAYLOAD_HASH_V1"
SOURCE_BASELINE_COMMIT = "b0cff8f6ddb6819ba148512dadebdf5a025552ce"

# Output artifact locations (written ONLY by the explicit write helper).
DOC_REL_DIR = os.path.join("docs", "automation", "0174ED")
PACKET_FILENAME = "approval_ledger_payload_hash_contract_packet.json"
DOC_FILENAME = "approval_ledger_payload_hash_contract.md"

NEXT_REQUIRED_GATE = (
    "dispatch outbox + idempotency contract, then kill switch, rate/spend/"
    "retry policy, one-request/no-auto-retry supervised dispatch, and redacted "
    "immutable audit before any supervised live write; credential hydration "
    "remains a separate future operator-owned gate and is NOT enabled here"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174EE_DISPATCH_OUTBOX_AND_IDEMPOTENCY_CONTRACT_V0"
)


# --------------------------------------------------------------------------- #
# Status vocabularies (symbolic only)
# --------------------------------------------------------------------------- #
class ApprovalStatus:
    PASS = "pass"
    BLOCKED = "blocked"
    FAIL_CLOSED = "fail_closed"


# Challenge status classes.
CHALLENGE_PENDING = "pending"
CHALLENGE_APPROVED = "approved"
CHALLENGE_REJECTED = "rejected"
CHALLENGE_EXPIRED = "expired"
CHALLENGE_INVALIDATED = "invalidated"

# Approval validity (derived) classes.
APPROVAL_VALID_CANDIDATE = "approval_valid_for_payload_not_dispatch"
APPROVAL_NOT_VALID = "approval_not_valid"
APPROVAL_FAIL_CLOSED = "approval_fail_closed_forbidden_value"

# Ledger fact kinds (append-only).
FACT_APPROVAL = "approval"
FACT_REVOCATION = "revocation"

# Required response classes for a challenge.
RESPONSE_EXPLICIT_APPROVE = "explicit_approve"
RESPONSE_EXPLICIT_REJECT = "explicit_reject"
RESPONSE_EXPLICIT_EDIT_REQUEST = "explicit_edit_request"

REQUIRED_RESPONSE_CLASSES = (
    RESPONSE_EXPLICIT_APPROVE,
    RESPONSE_EXPLICIT_REJECT,
    RESPONSE_EXPLICIT_EDIT_REQUEST,
)

# The exact ordered list of authority-bearing inputs to the payload hash.
PAYLOAD_HASH_INPUTS = (
    "payload_schema",
    "payload_schema_version",
    "platform",
    "payload_text",
    "platform_formatting",
    "thread_split",
    "disclosure_class",
    "destination_binding_id",
    "credential_handle_id",
    "media_manifest_hash",
    "visibility_class",
    "content_lane",
    "policy_snapshot_id",
    "platform_adapter_version",
)

REQUIRED_APPROVAL_SCOPES = (
    "manual_export_only",
    "platform_preview_only",
    "dispatch_readiness_review_only",
)

MIN_EVIDENCE_REF_COUNT = 1

# Fields that MUST NEVER feed the payload hash or be persisted.
PAYLOAD_HASH_EXCLUDES = (
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
    "raw_sensitive_account_id",
    "local_absolute_path_if_sensitive",
)


# --------------------------------------------------------------------------- #
# Redaction scanner (same defense-in-depth family as 0174EB / 0174EC).
# --------------------------------------------------------------------------- #
_SECRET_LIKE = [
    re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}"),           # telegram-style token
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),   # PEM private key
    re.compile(r"AKIA[0-9A-Z]{16}"),                     # AWS access key id
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),                 # GitHub PAT
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),         # GitHub fine PAT
    re.compile(r"\bAAAA[A-Za-z0-9%]{20,}\b"),            # X/Twitter bearer body
    re.compile(r"xoxb-[A-Za-z0-9-]{10,}"),               # slack-style bot token
    re.compile(r"\bMTA[A-Za-z0-9._-]{20,}\b"),           # discord-style token
    re.compile(r"\bey[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}"),
]
_BEARER_TOKEN = re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-%]{10,}")
_TOKEN_KV = re.compile(
    r"(?i)\b(?:access_token|refresh_token|bearer_token|client_secret|"
    r"api_key|authorization_code|auth_code|code_verifier|code_challenge|"
    r"webhook_token|bot_token|app_secret|access_jwt|refresh_jwt|app_password)"
    r"\b\s*[:=]\s*[A-Za-z0-9._\-/+]{4,}"
)
_TELEGRAM_URL_WITH_BOT = re.compile(r"api\.telegram\.org/bot")
_DISCORD_WEBHOOK_URL = re.compile(
    r"(?i)discord(?:app)?\.com/api/webhooks/\d+")
_HANDLE_LIKE = re.compile(r"@[A-Za-z0-9_]{3,}")
_LONG_DIGITS = re.compile(r"(?<!\d)-?\d{7,}(?!\d)")
_LINKEDIN_URN = re.compile(r"urn:li:[A-Za-z]+:")
_ENV_ASSIGNMENT = re.compile(
    r"(?im)^\s*(?:export\s+)?[A-Z0-9_]*"
    r"(?:SECRET|TOKEN|KEY|PASSWORD|PASSWD|CLIENT_ID|CLIENT_SECRET|BEARER|"
    r"API_KEY|ACCESS|REFRESH|WEBHOOK)[A-Z0-9_]*\s*=\s*\S+"
)
_CALLBACK_URL_WITH_QUERY = re.compile(
    r"https?://[^\s\"']*[?&](?:code|state|access_token|token|bearer_token|"
    r"refresh_token|authorization_code|auth_code|code_verifier|code_challenge|"
    r"redirect_uri|callback_url|error|error_description)="
)
_RAW_QUERY_SENSITIVE = re.compile(
    r"(?:^|[?&])(?:code|state|access_token|token|bearer_token|refresh_token|"
    r"authorization_code|auth_code|code_verifier|code_challenge|error|"
    r"error_description)=[^&\s]+"
)
_SECRET_FINGERPRINT_CLAIM = re.compile(
    r"(?i)(?:secret|token|client_secret|credential|api_key)\s*"
    r"(?:hash|fingerprint|prefix|suffix|sha256|md5)\s*[:=]\s*[A-Za-z0-9+/=_-]{4,}"
)
_REDACTED_FROM_REAL_CLAIM = re.compile(
    r"(?i)(?:starts?\s*with|ends?\s*with|begins?\s*with|"
    r"last\s*\d+|first\s*\d+|last4|first6)\s*[:=]?\s*[A-Za-z0-9+/=_-]{3,}"
)
_PROFILE_URL = re.compile(
    r"(?i)https?://(?:www\.)?(?:twitter\.com|x\.com|facebook\.com|fb\.com|"
    r"instagram\.com|linkedin\.com|tiktok\.com|youtube\.com|youtu\.be|"
    r"t\.me|telegram\.me|reddit\.com|medium\.com|substack\.com|threads\.net|"
    r"bsky\.app|discord\.com|discordapp\.com)/\S+"
)
_SECRET_PATH_CLAIM = re.compile(
    r"(?i)(?:vault|secret|credential)\s*path\s*[:=]\s*\S*"
    r"(?:secret|token|key|password|credential)\S*"
)

_FORBIDDEN_KEYS = (
    "token", "access_token", "refresh_token", "bearer_token", "client_secret",
    "client_id", "api_key", "app_secret", "webhook_token", "webhook_url",
    "bot_token", "access_jwt", "refresh_jwt", "app_password", "account_id",
    "raw_account_id", "account_handle", "user_id", "username", "screen_name",
    "handle", "display_name", "post_id", "tweet_id", "message_id",
    "channel_id", "page_id", "community_id", "media_id", "subreddit_id",
    "place_id", "raw_url", "raw_request", "raw_response",
    "raw_provider_response", "raw_query", "query_string",
    "authorization_code", "auth_code", "code", "state", "code_verifier",
    "code_challenge", "redirect_uri", "callback_url", "token_response",
    "error_description", "secret", "password", "passwd", "secret_hash",
    "token_hash", "credential_hash", "secret_fingerprint", "token_fingerprint",
    "credential_fingerprint", "token_prefix", "token_suffix", "secret_prefix",
    "secret_suffix", "credential_prefix", "credential_suffix", "env_value",
    "dotenv_value", "source_value", "vault_path", "secret_path",
    "profile_url", "profile_image_url", "authorization", "cookie",
    "set_cookie", "response_headers", "raw_headers", "last4", "first6",
    "raw_credential", "raw_env_var",
)

# Keys whose string/list values are schema vocabularies (class NAMES), not
# secret material, and are therefore exempt from string scanning.
_SCHEMA_NAME_LIST_KEYS = frozenset({
    "payload_hash_inputs",
    "payload_hash_excludes",
    "required_response_classes",
    "required_response_class",
    "fact_kinds",
    "challenge_status_classes",
    "approval_validity_classes",
    "result_field_classes",
    "blocked_reasons",
    "invariants",
    "next_gate",
    "next_required_gate",
    "scanner_catches",
    "approval_scope",
    "required_approval_scopes",
})


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, sha256/short hashes).

    Hex digests are not leaks: full payload hashes are 64 hex chars, git SHAs
    are 40, and short hashes are 16. These are deterministic, non-secret
    content fingerprints, never credential material.
    """
    if s == SOURCE_BASELINE_COMMIT:
        return True
    if re.fullmatch(r"[0-9a-f]{16}", s):
        return True
    if re.fullmatch(r"[0-9a-f]{40}", s):
        return True
    if re.fullmatch(r"[0-9a-f]{64}", s):
        return True
    return False


def scan_for_leaks(obj):
    """Return a sorted list of redaction violations for an object."""
    violations = []

    def _walk(node, key=None):
        if isinstance(node, dict):
            for k, v in node.items():
                if str(k).lower() in _FORBIDDEN_KEYS:
                    violations.append(f"forbidden_key:{str(k).lower()}")
                _walk(v, k)
        elif isinstance(node, (list, tuple)):
            for v in node:
                _walk(v, key)
        elif isinstance(node, str):
            _scan_string(node, key)

    def _scan_string(s, key):
        if key in _SCHEMA_NAME_LIST_KEYS:
            return
        if _CALLBACK_URL_WITH_QUERY.search(s):
            violations.append(f"callback_url_with_query:{key or 'value'}")
        if _RAW_QUERY_SENSITIVE.search(s):
            violations.append(f"raw_query_sensitive:{key or 'value'}")
        if _ENV_ASSIGNMENT.search(s):
            violations.append(f"env_assignment:{key or 'value'}")
        if _TOKEN_KV.search(s):
            violations.append(f"token_kv:{key or 'value'}")
        if _SECRET_FINGERPRINT_CLAIM.search(s):
            violations.append(f"secret_fingerprint_claim:{key or 'value'}")
        if _REDACTED_FROM_REAL_CLAIM.search(s):
            violations.append(f"redacted_from_real_claim:{key or 'value'}")
        if _SECRET_PATH_CLAIM.search(s):
            violations.append(f"secret_path_claim:{key or 'value'}")
        if _PROFILE_URL.search(s):
            violations.append(f"profile_url:{key or 'value'}")
        if _DISCORD_WEBHOOK_URL.search(s):
            violations.append(f"discord_webhook_url:{key or 'value'}")
        for pat in _SECRET_LIKE:
            if pat.search(s):
                violations.append(f"secret_like_value:{key or 'value'}")
                break
        if _BEARER_TOKEN.search(s):
            violations.append(f"bearer_token:{key or 'value'}")
        if _TELEGRAM_URL_WITH_BOT.search(s):
            violations.append(f"telegram_url:{key or 'value'}")
        if _LINKEDIN_URN.search(s):
            violations.append(f"linkedin_urn:{key or 'value'}")
        if _HANDLE_LIKE.search(s):
            violations.append(f"raw_handle:{key or 'value'}")
        if _long_digit_id_present(s) and not _is_known_safe_identifier(s):
            violations.append(f"long_digits_possible_id:{key or 'value'}")

    _walk(obj)
    return sorted(set(violations))


_HEX_CHARS = set("0123456789abcdefABCDEF")


def _long_digit_id_present(s):
    """True if a 7+ digit run looks like a raw account/message/page id.

    A digit run that is merely a fragment of a 16-, 40-, or 64-character hex
    token (a short hash, git SHA, or sha256 embedded in prose) is NOT a leak
    and is skipped.
    """
    for m in _LONG_DIGITS.finditer(s):
        start, end = m.start(), m.end()
        left = start
        while left > 0 and s[left - 1] in _HEX_CHARS:
            left -= 1
        right = end
        while right < len(s) and s[right] in _HEX_CHARS:
            right += 1
        if (right - left) in (16, 40, 64):
            continue
        return True
    return False


# --------------------------------------------------------------------------- #
# Deterministic serialization + hashing
# --------------------------------------------------------------------------- #
def serialize(obj):
    """Deterministic JSON: sorted keys, stable separators, trailing newline."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization."""
    return hashlib.sha256(serialize(obj).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# PlatformPayloadForApproval + canonicalization + payload hash
# --------------------------------------------------------------------------- #
def canonical_payload_dict(platform, payload_text, destination_binding_id,
                           credential_handle_id, media_manifest_hash,
                           visibility_class, content_lane, policy_snapshot_id,
                           platform_adapter_version,
                           platform_formatting="default",
                           thread_split=None, disclosure_class="none"):
    """Build the canonical, authority-bearing PlatformPayloadForApproval dict.

    Only NON-SECRET, authority-bearing fields are included. A credential is
    represented ONLY by its symbolic ``credential_handle_id`` (a 0174EC
    handle id), never by a value. ``thread_split`` is normalized to a list of
    strings (empty list if None) so that thread structure changes the hash.
    """
    if thread_split is None:
        thread_split_norm = []
    else:
        thread_split_norm = [str(seg) for seg in thread_split]
    return {
        "payload_schema": PAYLOAD_SCHEMA,
        "payload_schema_version": PAYLOAD_SCHEMA_VERSION,
        "platform": platform,
        "payload_text": payload_text,
        "platform_formatting": platform_formatting,
        "thread_split": thread_split_norm,
        "disclosure_class": disclosure_class,
        "destination_binding_id": destination_binding_id,
        "credential_handle_id": credential_handle_id,
        "media_manifest_hash": media_manifest_hash,
        "visibility_class": visibility_class,
        "content_lane": content_lane,
        "policy_snapshot_id": policy_snapshot_id,
        "platform_adapter_version": platform_adapter_version,
    }


def assert_payload_redacted(payload):
    """Raise ValueError if the payload carries forbidden credential material.

    Fail-closed precondition for hashing/approval. The payload may reference a
    credential ONLY via ``credential_handle_id``; any raw token/secret/env
    value is rejected.
    """
    violations = scan_for_leaks(payload)
    if violations:
        raise ValueError(f"payload failed redaction scan: {violations}")


def compute_payload_hash(payload):
    """Deterministic sha256 over the canonical authority-bearing fields only.

    The hash is computed strictly over ``PAYLOAD_HASH_INPUTS`` extracted from
    the canonical payload, so ANY authority-bearing change (text, platform,
    binding, credential handle, media manifest, visibility, disclosure,
    formatting, thread split, content lane, policy snapshot, adapter version)
    changes the hash, while incidental extra keys do not.
    """
    assert_payload_redacted(payload)
    hashed = {k: payload.get(k) for k in PAYLOAD_HASH_INPUTS}
    return hashlib.sha256(serialize(hashed).encode("utf-8")).hexdigest()


def payload_hash_short(payload_hash):
    """Return the first 16 hex chars of a payload hash (display only)."""
    return str(payload_hash)[:16]


# --------------------------------------------------------------------------- #
# Approval challenge / ledger entry / revocation builders
# --------------------------------------------------------------------------- #
def create_approval_challenge(payload, challenge_id, operator_id,
                              created_at_epoch, expires_at_epoch,
                              channel="local_ui", one_time_nonce=None,
                              approval_phrase_required="APPROVE",
                              destination_summary_redacted="redacted",
                              approval_scope="manual_export_only",
                              evidence_refs=None):
    """Create an expiring, one-time ApprovalChallenge bound to an exact hash.

    The challenge stores only the payload hash (and short form), the platform,
    the symbolic destination binding id, the symbolic credential handle id, and
    redacted display fields -- never the raw payload secret material.
    """
    assert_payload_redacted(payload)
    payload_hash = compute_payload_hash(payload)
    if evidence_refs is None:
        evidence_refs = [f"generated_evidence_ref:{challenge_id}"]
    evidence_refs = list(evidence_refs)
    return {
        "fact_kind": "approval_challenge",
        "challenge_id": challenge_id,
        "operator_id": operator_id,
        "channel": channel,
        "created_at_epoch": int(created_at_epoch),
        "expires_at_epoch": int(expires_at_epoch),
        "platform": payload.get("platform"),
        "destination_binding_id": payload.get("destination_binding_id"),
        "credential_handle_id": payload.get("credential_handle_id"),
        "media_manifest_hash": payload.get("media_manifest_hash"),
        "visibility_class": payload.get("visibility_class"),
        "approval_scope": approval_scope,
        "evidence_refs": evidence_refs,
        "payload_hash": payload_hash,
        "payload_hash_short": payload_hash_short(payload_hash),
        "destination_summary_redacted": destination_summary_redacted,
        "one_time_nonce": one_time_nonce or challenge_id,
        "approval_phrase_required": approval_phrase_required,
        "required_response_classes": list(REQUIRED_RESPONSE_CLASSES),
        "status": CHALLENGE_PENDING,
        "public_postable": False,
    }


def record_approval(challenge, payload, ledger_entry_id, approved_at_epoch,
                    operator_id, response_class=RESPONSE_EXPLICIT_APPROVE,
                    approval_text_redacted="redacted",
                    approval_method="challenge_response",
                    prior_payload_hash=None, approval_scope=None,
                    evidence_refs=None):
    """Build an append-only ApprovalLedgerEntry recording an approval fact.

    The entry binds the operator, the challenge id, the exact payload hash, the
    platform/binding/credential-handle/media/visibility, and an expiration. It
    is a pure value: it does NOT authorize dispatch, does NOT hydrate
    credentials, and reports ``valid_for_dispatch = False``. Validity for a
    CURRENT payload is always re-derived by ``validate_approval_for_current_
    payload`` -- this fact only states that an approval happened.

    R1 HARDENING (fail-closed challenge<->payload binding): an approval entry is
    created ONLY when the supplied challenge still binds the EXACT same payload.
    A challenge created for payload A MUST NOT be usable to record an approval
    for a substituted payload B. Before any entry is built this raises
    ``ValueError`` with a stable reason string if:
      * the challenge payload hash is missing
        (``approval_challenge_payload_hash_missing``);
      * the challenge payload hash differs from ``compute_payload_hash(payload)``
        (``approval_challenge_payload_hash_mismatch``);
      * any binding field (platform, destination binding, credential handle,
        media manifest hash, visibility class) differs
        (``approval_challenge_binding_mismatch:<field>``);
      * the approval time is past the challenge expiry
        (``approval_challenge_expired``);
      * the response class is not an explicit approve
        (``approval_response_not_explicit_approve``);
      * the challenge status is present and not pending
        (``approval_challenge_not_pending``).
    No approval fact is produced in any failed case.
    """
    assert_payload_redacted(payload)
    payload_hash = compute_payload_hash(payload)

    # --- R1: prove the challenge still binds this exact payload ----------- #
    if response_class != RESPONSE_EXPLICIT_APPROVE:
        raise ValueError("approval_response_not_explicit_approve")

    challenge = challenge or {}

    challenge_status = challenge.get("status")
    if challenge_status is not None and challenge_status != CHALLENGE_PENDING:
        raise ValueError("approval_challenge_not_pending")

    challenge_hash = challenge.get("payload_hash")
    if not challenge_hash:
        raise ValueError("approval_challenge_payload_hash_missing")
    if challenge_hash != payload_hash:
        raise ValueError("approval_challenge_payload_hash_mismatch")

    for field in _BINDING_FIELDS:
        if challenge.get(field) != payload.get(field):
            raise ValueError(f"approval_challenge_binding_mismatch:{field}")

    challenge_expires = challenge.get("expires_at_epoch")
    if challenge_expires is None:
        raise ValueError("approval_challenge_expired")
    if int(approved_at_epoch) > int(challenge_expires):
        raise ValueError("approval_challenge_expired")

    resolved_scope = approval_scope or challenge.get("approval_scope")
    if resolved_scope not in REQUIRED_APPROVAL_SCOPES:
        raise ValueError("approval_scope_invalid")

    resolved_evidence_refs = list(evidence_refs or challenge.get("evidence_refs") or [])
    if len(resolved_evidence_refs) < MIN_EVIDENCE_REF_COUNT:
        raise ValueError("approval_evidence_refs_missing")

    entry = {
        "fact_kind": FACT_APPROVAL,
        "ledger_entry_id": ledger_entry_id,
        "approved_at_epoch": int(approved_at_epoch),
        "operator_id": operator_id,
        "approval_channel": challenge.get("channel"),
        "challenge_id": challenge.get("challenge_id"),
        "one_time_nonce": challenge.get("one_time_nonce"),
        "response_class": response_class,
        "platform": payload.get("platform"),
        "destination_binding_id": payload.get("destination_binding_id"),
        "credential_handle_id": payload.get("credential_handle_id"),
        "media_manifest_hash": payload.get("media_manifest_hash"),
        "visibility_class": payload.get("visibility_class"),
        "payload_hash": payload_hash,
        "payload_hash_short": payload_hash_short(payload_hash),
        "prior_payload_hash": prior_payload_hash,
        "approval_text_redacted": approval_text_redacted,
        "approval_method": approval_method,
        "approval_scope": resolved_scope,
        "evidence_refs": resolved_evidence_refs,
        "expires_at_epoch": int(challenge.get("expires_at_epoch")),
        # Hard invariant: an approval fact never authorizes dispatch by itself.
        "valid_for_dispatch": False,
        "dispatch_ready": False,
        "live_ready": False,
        "public_postable": False,
    }
    return entry


def record_revocation(revocation_id, revoked_at_epoch, operator_id,
                      challenge_id=None, ledger_entry_id=None,
                      payload_hash=None, reason_class="operator_revoked"):
    """Build an append-only revocation event.

    Revocation never mutates a prior approval entry. It is a new fact that the
    validator consults: any approval matching the revoked challenge id, ledger
    entry id, or payload hash is treated as not valid.
    """
    return {
        "fact_kind": FACT_REVOCATION,
        "revocation_id": revocation_id,
        "revoked_at_epoch": int(revoked_at_epoch),
        "operator_id": operator_id,
        "challenge_id": challenge_id,
        "ledger_entry_id": ledger_entry_id,
        "payload_hash": payload_hash,
        "reason_class": reason_class,
    }


# --------------------------------------------------------------------------- #
# ApprovalLedger (append-only)
# --------------------------------------------------------------------------- #
class ApprovalLedger:
    """An append-only collection of approval + revocation facts.

    Facts are only ever appended; nothing is mutated in place. Validity is
    always derived from the full fact set, never stored as authority.
    """

    def __init__(self):
        self._facts = []

    def append_approval(self, entry):
        if entry.get("fact_kind") != FACT_APPROVAL:
            raise ValueError("entry is not an approval fact")
        self._facts.append(json.loads(json.dumps(entry)))

    def append_revocation(self, event):
        if event.get("fact_kind") != FACT_REVOCATION:
            raise ValueError("event is not a revocation fact")
        self._facts.append(json.loads(json.dumps(event)))

    @property
    def facts(self):
        """Return a deep copy of all facts in append order."""
        return json.loads(json.dumps(self._facts))

    def approvals(self):
        return [f for f in self.facts if f.get("fact_kind") == FACT_APPROVAL]

    def revocations(self):
        return [f for f in self.facts if f.get("fact_kind") == FACT_REVOCATION]

    def find_approval(self, ledger_entry_id):
        for f in self._facts:
            if (f.get("fact_kind") == FACT_APPROVAL
                    and f.get("ledger_entry_id") == ledger_entry_id):
                return json.loads(json.dumps(f))
        return None

    def is_revoked(self, approval_entry):
        """True if any revocation event targets this approval fact."""
        cid = approval_entry.get("challenge_id")
        leid = approval_entry.get("ledger_entry_id")
        phash = approval_entry.get("payload_hash")
        for r in self._facts:
            if r.get("fact_kind") != FACT_REVOCATION:
                continue
            if r.get("ledger_entry_id") and r.get("ledger_entry_id") == leid:
                return True
            if r.get("challenge_id") and r.get("challenge_id") == cid:
                return True
            if r.get("payload_hash") and r.get("payload_hash") == phash:
                return True
        return False


# --------------------------------------------------------------------------- #
# Derived validation
# --------------------------------------------------------------------------- #
# Binding fields that must match between the approval and the current payload.
_BINDING_FIELDS = (
    "platform",
    "destination_binding_id",
    "credential_handle_id",
    "media_manifest_hash",
    "visibility_class",
)


def validate_approval_for_current_payload(ledger, approval_entry,
                                          current_payload, now_epoch):
    """Re-derive whether an approval is valid for the CURRENT payload.

    Fail-closed and non-side-effecting. Validity is DERIVED, never assumed.
    An approval is valid for the current payload ONLY if all hold:
      * neither the approval entry nor the current payload carry forbidden
        credential material (else fail_closed),
      * the current payload hash equals the approved payload hash,
      * each authority-bearing binding field matches,
      * the approval has not expired (now <= expires_at),
      * the approval has not been revoked.
    Even when valid, the result NEVER authorizes dispatch: ``dispatch_ready``
    and ``live_ready`` are always False.
    """
    blocked = []
    status = ApprovalStatus.PASS

    # Fail-closed redaction scan of all caller-supplied inputs.
    forbidden = scan_for_leaks([approval_entry, current_payload])
    forbidden_detected = bool(forbidden)

    approved_hash = (approval_entry or {}).get("payload_hash")
    expires_at = (approval_entry or {}).get("expires_at_epoch")

    current_hash = None
    validity = APPROVAL_NOT_VALID
    expired = False
    revoked = False
    hash_match = False
    binding_match = False

    if forbidden_detected:
        status = ApprovalStatus.FAIL_CLOSED
        validity = APPROVAL_FAIL_CLOSED
        blocked.append("forbidden_value_detected")
    else:
        current_hash = compute_payload_hash(current_payload)

        hash_match = (current_hash == approved_hash)
        if not hash_match:
            blocked.append("payload_hash_mismatch")

        mismatched = []
        for field in _BINDING_FIELDS:
            if (approval_entry or {}).get(field) != current_payload.get(field):
                mismatched.append(field)
        binding_match = not mismatched
        for field in mismatched:
            blocked.append(f"binding_mismatch:{field}")

        if expires_at is None or int(now_epoch) > int(expires_at):
            expired = True
            blocked.append("approval_expired")

        if ledger is not None and ledger.is_revoked(approval_entry or {}):
            revoked = True
            blocked.append("approval_revoked")

        if (approval_entry or {}).get("approval_scope") not in REQUIRED_APPROVAL_SCOPES:
            blocked.append("approval_scope_invalid")

        if len((approval_entry or {}).get("evidence_refs") or []) < MIN_EVIDENCE_REF_COUNT:
            blocked.append("approval_evidence_refs_missing")

        if blocked:
            status = ApprovalStatus.BLOCKED
            validity = APPROVAL_NOT_VALID
        else:
            status = ApprovalStatus.PASS
            validity = APPROVAL_VALID_CANDIDATE

    return {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": status,
        "approval_validity_class": validity,
        "platform": (approval_entry or {}).get("platform"),
        "ledger_entry_id": (approval_entry or {}).get("ledger_entry_id"),
        "challenge_id": (approval_entry or {}).get("challenge_id"),
        "approved_payload_hash": approved_hash,
        "current_payload_hash": current_hash,
        "payload_hash_match": hash_match,
        "binding_match": binding_match,
        "expired": expired,
        "revoked": revoked,
        "blocked_reasons": sorted(set(blocked)),
        "forbidden_fields_detected": forbidden_detected,
        "redaction_verified": not forbidden_detected,
        # Hard safety invariants -- ALWAYS these values in this task.
        "approval_authorizes_dispatch": False,
        "dispatch_ready": False,
        "live_ready": False,
        "outbox_entry_created": False,
        "credential_hydrated": False,
        "no_network_performed": True,
        "no_env_read_performed": True,
        "no_credential_read_performed": True,
        "no_credential_hydration_performed": True,
        "no_live_post_performed": True,
        "no_telegram_behavior": True,
        "no_llm_behavior": True,
        "public_postable": False,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }


# --------------------------------------------------------------------------- #
# Redacted audit summary
# --------------------------------------------------------------------------- #
def build_redacted_approval_audit(validation_result, approval_entry):
    """Build a redacted audit summary containing symbolic/redacted values only.

    Stores hashes (non-secret content fingerprints) and symbolic classes, never
    raw payload text, raw account ids, or any credential material.
    """
    audit = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "audit_kind": "redacted_approval_validation_audit",
        "status": validation_result.get("status"),
        "approval_validity_class": validation_result.get(
            "approval_validity_class"),
        "platform": validation_result.get("platform"),
        "ledger_entry_id": validation_result.get("ledger_entry_id"),
        "challenge_id": validation_result.get("challenge_id"),
        "approved_payload_hash_short": payload_hash_short(
            validation_result.get("approved_payload_hash") or ""),
        "current_payload_hash_short": payload_hash_short(
            validation_result.get("current_payload_hash") or ""),
        "payload_hash_match": validation_result.get("payload_hash_match"),
        "binding_match": validation_result.get("binding_match"),
        "expired": validation_result.get("expired"),
        "revoked": validation_result.get("revoked"),
        "approval_method": (approval_entry or {}).get("approval_method"),
        "approval_text_redacted": (approval_entry or {}).get(
            "approval_text_redacted", "redacted"),
        "blocked_reasons": validation_result.get("blocked_reasons", []),
        "dispatch_ready": False,
        "live_ready": False,
        "no_raw_credential_stored": True,
        "no_credential_hash_or_fingerprint_created": True,
        "no_credential_prefix_or_suffix_exposed": True,
    }
    audit["audit_hash"] = compute_checksum(audit)
    return audit


# --------------------------------------------------------------------------- #
# Ledger packet export
# --------------------------------------------------------------------------- #
def export_ledger_packet(ledger):
    """Export a deterministic redacted packet of all ledger facts + summary."""
    facts = ledger.facts if ledger is not None else []
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "ledger_export_kind": "append_only_approval_ledger",
        "fact_count": len(facts),
        "approval_count": sum(
            1 for f in facts if f.get("fact_kind") == FACT_APPROVAL),
        "revocation_count": sum(
            1 for f in facts if f.get("fact_kind") == FACT_REVOCATION),
        "facts": facts,
        "append_only": True,
        "dispatch_ready": False,
        "live_ready": False,
    }
    packet["packet_checksum"] = compute_checksum(packet)
    return packet


# --------------------------------------------------------------------------- #
# Model packet builder
# --------------------------------------------------------------------------- #
def build_packet():
    """Build the deterministic redacted 0174ED model packet."""
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "payload_schema": PAYLOAD_SCHEMA,
        "payload_schema_version": PAYLOAD_SCHEMA_VERSION,
        "approval_contract_status": "deterministic_local_authority_ready",
        "payload_hash_algorithm": "sha256",
        "payload_hash_inputs": list(PAYLOAD_HASH_INPUTS),
        "payload_hash_excludes": list(PAYLOAD_HASH_EXCLUDES),
        "challenge_status_classes": [
            CHALLENGE_PENDING, CHALLENGE_APPROVED, CHALLENGE_REJECTED,
            CHALLENGE_EXPIRED, CHALLENGE_INVALIDATED,
        ],
        "approval_validity_classes": [
            APPROVAL_VALID_CANDIDATE, APPROVAL_NOT_VALID, APPROVAL_FAIL_CLOSED,
        ],
        "fact_kinds": [FACT_APPROVAL, FACT_REVOCATION],
        "required_response_classes": list(REQUIRED_RESPONSE_CLASSES),
        "required_approval_scopes": list(REQUIRED_APPROVAL_SCOPES),
        "result_field_classes": [
            "status",
            "approval_validity_class",
            "payload_hash_match",
            "binding_match",
            "expired",
            "revoked",
            "blocked_reasons",
        ],
        "invariants": [
            "any_payload_text_change_changes_hash",
            "any_platform_change_changes_hash",
            "any_destination_binding_change_changes_hash",
            "any_credential_handle_change_changes_hash",
            "any_media_manifest_change_changes_hash",
            "any_visibility_disclosure_formatting_change_changes_hash",
            "approval_binds_exact_payload_hash",
            "approval_scope_is_explicit_and_limited",
            "approval_requires_evidence_packet_references",
            "approval_can_expire",
            "approval_can_be_revoked",
            "approval_invalid_if_current_hash_differs",
            "approval_invalid_if_challenge_expired",
            "approval_invalid_if_binding_differs",
            "approval_validity_is_derived_never_assumed",
            "approval_does_not_authorize_dispatch",
            "approval_does_not_create_outbox_entry",
            "approval_does_not_hydrate_credentials",
            "append_only_revocation_is_new_fact_not_mutation",
            "audit_contains_redacted_values_only",
            "record_approval_rejects_challenge_payload_substitution",
        ],
        "redaction_policy": {
            "fail_closed_on_forbidden_value": True,
            "credential_referenced_by_handle_id_only": True,
            "no_raw_credential_stored": True,
            "no_credential_hash_or_fingerprint_created": True,
            "no_credential_prefix_or_suffix_exposed": True,
            "scanner_catches": (
                "tokens, bearer strings, telegram/slack/discord-style tokens, "
                "GitHub PATs, AWS-like keys, JWT-like strings, OAuth code/"
                "state/verifier/challenge, refresh/access token KV strings, "
                "env assignments, callback URLs with query, raw sensitive "
                "query strings, social profile URLs, discord webhook URLs, "
                "raw handles, long raw numeric ids, secret hash/fingerprint/"
                "prefix/suffix claims, first6/last4 claims, secret vault "
                "paths, and forbidden dict keys"
            ),
        },
        "safety_flags": {
            "approval_authorizes_dispatch": False,
            "dispatch_ready": False,
            "live_ready": False,
            "outbox_entry_created": False,
            "credential_hydrated": False,
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
            "no_telegram_behavior": True,
            "no_llm_behavior": True,
            "no_openclaw_runtime": True,
            "no_scheduler_or_posting": True,
            "public_postable": False,
        },
        "strategic_posture": {
            "manual_posting": "fallback",
            "automation": "main_build_path",
            "autonomous_posting": "forbidden",
            "supervised_publishing": "final_product",
        },
        "status": ApprovalStatus.PASS,
        "next_required_gate": NEXT_REQUIRED_GATE,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
    }
    packet["checksum_sha256"] = compute_checksum(packet)
    return packet


# --------------------------------------------------------------------------- #
# Documentation builder
# --------------------------------------------------------------------------- #
def build_doc():
    """Build the deterministic redacted 0174ED markdown documentation."""
    hash_inputs = "\n".join(f"- `{f}`" for f in PAYLOAD_HASH_INPUTS)
    excludes = "\n".join(f"- `{f}`" for f in PAYLOAD_HASH_EXCLUDES)
    return f"""# Approval Ledger + Payload Hash Contract (0174ED)

Task: {TASK_LABEL}
Model: {MODEL} ({MODEL_VERSION})
Source baseline commit: {SOURCE_BASELINE_COMMIT}
Mode: Implementation Mode. Deterministic, stdlib-only, local authority layer.

> [!IMPORTANT]
> This module introduces NO live posting, NO dispatch, NO outbox creation, NO
> credential read or hydration, NO environment or `.env` read, NO keyring or
> browser-session read, NO OAuth, NO network call, NO Telegram behavior, NO
> LLM behavior, and NO scheduler. It is the deterministic approval/hash
> authority contract only.

## Strategic Posture
- Manual posting is the **fallback** path, not the strategic destination.
- **Automation is the main build path.**
- **Autonomous posting is forbidden.**
- **Supervised publishing is the final product.**

## What This Contract Proves
It proves that Jim approved an **exact payload**, not a vague idea. An approval
is bound to a deterministic sha256 **payload hash** computed over the exact
authority-bearing fields below. If any of those fields change, the hash
changes, and the prior approval is no longer valid for the new payload.

## Payload Hash Algorithm
- Algorithm: `sha256` over canonical JSON (sorted keys, compact separators).
- The hash includes explicit schema + version fields.
- The hash is computed over authority-bearing fields ONLY; incidental extra
  keys never affect it.

## Payload Hash Inputs (authority-bearing, non-secret)
{hash_inputs}

## Payload Hash Excludes (never hashed or stored)
{excludes}

A credential is represented ONLY by its symbolic `credential_handle_id` (a
0174EC handle id). No raw token, api key, env value, `.env` value, secret path,
raw provider response, raw sensitive account id, or sensitive local absolute
path is ever included in the hash or persisted.

## Core Objects
- **PlatformPayloadForApproval** -- the canonical authority-bearing payload
  dict (`canonical_payload_dict`).
- **ApprovalChallenge** -- an expiring, one-time challenge bound to an exact
  payload hash (`create_approval_challenge`).
- **ApprovalLedgerEntry** -- an append-only approval fact (`record_approval`).
- **ApprovalLedger** -- an append-only collection of approval + revocation
  facts; nothing is mutated in place.
- **Revocation event** -- an append-only revocation fact (`record_revocation`).
- **ApprovalValidationResult** -- the DERIVED validity result
  (`validate_approval_for_current_payload`).
- **Redacted audit summary** -- symbolic/redacted audit
  (`build_redacted_approval_audit`).

## Invariants
- Any change to payload text, platform, destination/account binding,
  credential handle id, media manifest hash, visibility, disclosure, or
  platform formatting changes the payload hash.
- Approval binds an exact payload hash.
- Approval can expire and can be revoked.
- Approval is invalid if the current payload hash differs from the approved
  hash, if the challenge is expired, or if any binding field differs.
- Approval validity is **derived, never assumed**.
- Approval does **not** authorize dispatch, does **not** create an outbox
  entry, and does **not** hydrate credentials in this task.
- Append-only: revocation and invalidation are new ledger facts or derived
  status, never mutation of a prior approval fact.
- Audit objects contain redacted values only; no raw credential/token/api-key
  is stored, hashed, prefixed, suffixed, fingerprinted, or logged.
- **R1 hardening:** `record_approval` fails closed BEFORE creating a ledger
  entry unless the supplied challenge still binds the exact same payload: the
  challenge payload hash must equal `compute_payload_hash(payload)`, every
  binding field (platform, destination binding, credential handle, media
  manifest hash, visibility class) must match, the response must be an explicit
  approve, the challenge must still be pending, and the approval time must not
  exceed the challenge expiry. A challenge created for payload A can never
  record an approval for a substituted payload B
  (`record_approval_rejects_challenge_payload_substitution`).

## Authority Boundary
Approval state never implies dispatch-ready or live-ready. Every validation
result and audit reports `dispatch_ready = False` and `live_ready = False`.
Future supervised dispatch remains blocked / future-gated.

## Next Task
Recommended next task after PASS:
`{EXACT_NEXT_TASK_RECOMMENDATION}`

Next required gate: {NEXT_REQUIRED_GATE}
"""


# --------------------------------------------------------------------------- #
# Explicit artifact writer (no writes happen on import)
# --------------------------------------------------------------------------- #
def write_artifacts(repo_root):
    """Write the deterministic 0174ED packet + doc under ``repo_root``.

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
