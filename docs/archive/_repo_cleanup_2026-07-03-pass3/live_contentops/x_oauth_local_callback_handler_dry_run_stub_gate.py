"""X OAuth local callback handler dry-run stub gate (0174CZ).

This module is STRICTLY LOCAL. It performs NO network of any kind, opens NO
browser, starts NO callback server, binds NO localhost port, runs NO subprocess,
and reads NO env/credentials. Official X OAuth documentation reading is an
Antigravity/operator activity performed BEFORE this module runs; the module only
implements a deterministic, pure-function dry-run callback handler that consumes
SYMBOLIC fixture events and emits a redacted callback ledger matching the
accepted 0174CY contract.

It implements the 0174CZ local callback handler dry-run stub WITHOUT initiating
OAuth, WITHOUT opening an authorize URL, WITHOUT starting a callback server or
binding a port, WITHOUT receiving / parsing / processing a real callback URL or
raw query string, WITHOUT reading any Client ID / Client Secret / token, WITHOUT
generating any real state / code_verifier / code_challenge, and WITHOUT any
account binding or live/posting behavior.

HARD GUARANTEES (enforced by tests + leakage guards):
  * No network imports (no urllib / requests / httpx / socket / http / dotenv).
  * No browser/subprocess imports (no webbrowser / subprocess).
  * No http server imports (no http.server / socketserver / wsgiref).
  * No process env / dotenv read (no environment or home-dir lookups).
  * Imports ONLY hashlib, json, os.path, re, sys.
  * Fail-closed: writes happen ONLY when the write flag is present AND the
    packet passes the redaction scan.
  * Fail-closed handler: rejects any forbidden input field, missing/false
    symbolic_inputs_only, unknown callback_class, or any token/url/query/handle/
    long-id-looking value WITHOUT echoing the raw input.
  * Deterministic JSON: sorted keys, compact separators, trailing newline.
  * No OAuth flow, no authorize URL opened, no callback server started, no port
    bound, no real callback URL / raw query processed, no authorization code,
    no token exchange, no token persisted, no developer-portal login, no
    account binding, no posting/metrics/webhook/reply/DM/scraping, no generic
    publisher, no credential-entry schema, no OAuth/live execution command.
  * Stores only concise symbolic metadata: OAuth flow family, handler dry-run
    contract, fixture event classes, redacted ledger outputs (classes/booleans
    only), redaction policy, validation rules, blockers/caveats, and citation
    URLs (token/id/handle/query-free).
"""

import hashlib
import json
import os.path
import re
import sys

TASK_LABEL = (
    "TASK_CONTENTOPS_0174CZ_X_OAUTH_LOCAL_CALLBACK_HANDLER_DRY_RUN_STUB_"
    "NO_SECRET_NO_TOKEN_NO_NETWORK_NO_BROWSER_V0"
)

GATE = "X_OAUTH_LOCAL_CALLBACK_HANDLER_DRY_RUN_STUB_0174CZ"
PLATFORM = "x"
SOURCE_BASELINE_COMMIT = "fc54439e73029451bfa7d2fd29a4917c4e2d164e"
INHERITED_0174CY_COMMIT = "fc54439e73029451bfa7d2fd29a4917c4e2d164e"

# Date the official docs were inspected for this task (UTC, no time-of-day).
DOCS_ACCESSED_DATE = "2026-06-16"

NEXT_TASK = (
    "TASK_CONTENTOPS_0174DA_X_OAUTH_CALLBACK_SERVER_POLICY_GATE_"
    "NO_SECRET_NO_TOKEN_NO_NETWORK_NO_BROWSER_V0"
)

# Output artifact locations.
PACKET_REL_DIR = os.path.join("docs", "credential_readiness", "0174CZ")
PACKET_FILENAME = "x_oauth_local_callback_handler_dry_run_stub_packet.json"
README_FILENAME = "README.md"

FLAG_WRITE = "--write-x-oauth-local-callback-handler-dry-run-stub"

ACCEPTED_0174CY_CONTRACT_REFERENCE = (
    "docs/credential_readiness/0174CY/"
    "x_oauth_redirect_ledger_callback_fixture_contract_packet.json "
    "(gate X_OAUTH_REDIRECT_LEDGER_CALLBACK_FIXTURE_CONTRACT_0174CY)"
)

# Symbolic OAuth flow family (no flow initiated).
OAUTH_FLOW_FAMILY_SYMBOLIC = (
    "x.oauth2.authorization_code_with_pkce.user_context.callback.handler.stub "
    "(NOT initiated now)"
)

# Allowed symbolic handler input fields (no raw secrets).
ALLOWED_SYMBOLIC_INPUT_FIELDS = [
    "fixture_name",
    "callback_class",
    "state_match_class",
    "code_present_class",
    "denial_or_error_class",
    "timeout_class",
    "replay_detected_class",
    "malformed_class",
    "symbolic_inputs_only",
]

# Forbidden symbolic handler input fields (must never be accepted).
FORBIDDEN_SYMBOLIC_INPUT_FIELDS = [
    "raw_url", "callback_url", "raw_query", "query_string",
    "authorization_code", "auth_code", "code", "state", "error_description",
    "token", "access_token", "refresh_token", "bearer_token",
    "token_response", "client_id", "client_secret", "redirect_uri",
    "code_verifier", "code_challenge", "account_id", "user_id", "username",
    "screen_name", "handle", "post_id", "tweet_id", "community_id",
    "media_id", "place_id",
]

# Allowed redacted ledger output fields (exactly the accepted 0174CY allowed
# fields).
ALLOWED_LEDGER_OUTPUT_FIELDS = [
    "task_label",
    "gate",
    "platform",
    "attempt_id_class",
    "callback_received",
    "callback_class",
    "terminal_result_class",
    "state_match_class",
    "code_present_class",
    "denial_or_error_class",
    "timeout_class",
    "replay_detected_class",
    "malformed_class",
    "redaction_verified",
    "no_raw_callback_url_persisted",
    "no_raw_query_persisted",
    "no_authorization_code_persisted",
    "no_state_persisted",
    "no_error_description_persisted",
    "no_token_persisted",
    "no_account_identifier_persisted",
    "one_terminal_result_or_timeout",
    "token_exchange_blocked",
    "next_required_gate",
    "status",
    "blocked_reasons",
]

# Fields that must NEVER appear in the ledger output.
FORBIDDEN_LEDGER_OUTPUT_FIELDS = [
    "raw_url", "callback_url", "raw_query", "query_string",
    "authorization_code", "auth_code", "code", "state", "error_description",
    "token", "access_token", "refresh_token", "bearer_token",
    "token_response", "client_id", "client_secret", "redirect_uri",
    "code_verifier", "code_challenge", "account_id", "user_id", "username",
    "screen_name", "handle", "post_id", "tweet_id", "community_id",
    "media_id", "place_id",
]

# Accepted callback classes (mirrors the 0174CY callback event classes).
CALLBACK_CLASSES = [
    "success_code_present_state_match",
    "user_denied_or_declined",
    "missing_code",
    "missing_state",
    "state_mismatch",
    "duplicate_or_replayed_callback",
    "expired_or_used_authorization_code",
    "malformed_callback",
    "timeout_no_callback",
    "unexpected_error_redacted",
]


# --------------------------------------------------------------------------- #
# Redaction scanner (defense-in-depth). Blocks tokens / bearer strings / raw
# auth codes / raw state / raw code_verifier / raw code_challenge / callback
# URLs with query params / raw query strings with code|state|token|error / raw
# handles / raw account-user-post-tweet-community-media-place ids / long numeric
# ids / LinkedIn-style URNs / forbidden raw keys. Official docs URLs are allowed
# only when token/id/handle/query-free.
# --------------------------------------------------------------------------- #
_SECRET_LIKE = [
    re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}"),           # telegram-style token
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),   # PEM private key
    re.compile(r"AKIA[0-9A-Z]{16}"),                     # AWS access key id
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),                 # GitHub PAT
    re.compile(r"\bAAAA[A-Za-z0-9%]{20,}\b"),            # X/Twitter bearer body
]
_BEARER_TOKEN = re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-%]{10,}")
_TELEGRAM_URL_WITH_BOT = re.compile(r"api\.telegram\.org/bot")
_HANDLE_LIKE = re.compile(r"@[A-Za-z0-9_]{3,}")
_LONG_DIGITS = re.compile(r"(?<!\d)-?\d{7,}(?!\d)")
_LINKEDIN_URN = re.compile(r"urn:li:[A-Za-z]+:")
# Any URL carrying an OAuth-sensitive query parameter (code/state/token/verifier
# /challenge/redirect/error). This is the no-query-log callback guard.
_CALLBACK_URL_WITH_QUERY = re.compile(
    r"https?://[^\s\"']*[?&](?:code|state|access_token|token|bearer_token|"
    r"refresh_token|authorization_code|auth_code|code_verifier|code_challenge|"
    r"redirect_uri|callback_url|error|error_description)="
)
# A raw query-string fragment carrying sensitive params even without a scheme.
_RAW_QUERY_SENSITIVE = re.compile(
    r"(?:^|[?&])(?:code|state|access_token|token|bearer_token|refresh_token|"
    r"authorization_code|auth_code|code_verifier|code_challenge|error|"
    r"error_description)=[^&\s]+"
)

_FORBIDDEN_KEYS = (
    "token", "access_token", "refresh_token", "bearer_token", "client_secret",
    "client_id", "api_key", "account_id", "account_handle", "user_id",
    "username", "screen_name", "handle", "post_id", "tweet_id", "community_id",
    "media_id", "place_id", "raw_url", "raw_request", "raw_response",
    "raw_query", "query_string", "authorization_code", "auth_code", "code",
    "state", "code_verifier", "code_challenge", "redirect_uri", "callback_url",
    "token_response", "error_description",
)

# Safe symbolic placeholders allowed in fixtures (fake, non-token).
_SAFE_SYMBOLIC_PLACEHOLDERS = frozenset({
    "STATE_SYMBOLIC_MATCH",
    "STATE_SYMBOLIC_MISMATCH",
    "STATE_SYMBOLIC_MISSING",
    "CODE_SYMBOLIC_PRESENT",
    "CODE_SYMBOLIC_MISSING",
    "CODE_SYMBOLIC_EXPIRED",
    "ERROR_SYMBOLIC_ACCESS_DENIED",
    "ERROR_SYMBOLIC_MALFORMED",
    "ERROR_SYMBOLIC_UNEXPECTED",
    "CALLBACK_SYMBOLIC_DUPLICATE",
    "CALLBACK_SYMBOLIC_TIMEOUT",
    "CALLBACK_SYMBOLIC_REPLAY",
    "CALLBACK_SYMBOLIC_MALFORMED",
    "CHALLENGE_SYMBOLIC_S256_CLASS",
    "VERIFIER_SYMBOLIC_CLASS",
})


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, payload hashes)."""
    if s in (SOURCE_BASELINE_COMMIT, INHERITED_0174CY_COMMIT):
        return True
    if re.fullmatch(r"[0-9a-f]{40}", s) or re.fullmatch(r"[0-9a-f]{64}", s):
        return True
    return False


def scan_packet_for_leaks(obj):
    """Return a sorted list of redaction violations for an object."""
    violations = []

    def _walk(node, key=None):
        if isinstance(node, dict):
            for k, v in node.items():
                if str(k).lower() in _FORBIDDEN_KEYS:
                    violations.append(f"forbidden_key:{str(k).lower()}")
                _walk(v, k)
        elif isinstance(node, list):
            for v in node:
                _walk(v, key)
        elif isinstance(node, str):
            _scan_string(node, key)

    def _scan_string(s, key):
        if s in _SAFE_SYMBOLIC_PLACEHOLDERS:
            return
        # Allow the declared forbidden/allowed field NAMES to appear as list
        # values in the schema/contract documentation lists.
        if key in ("redirect_ledger_forbidden_fields",
                   "redirect_ledger_allowed_fields",
                   "allowed_symbolic_input_fields",
                   "forbidden_symbolic_input_fields",
                   "allowed_ledger_output_fields",
                   "forbidden_ledger_output_fields"):
            return
        if _CALLBACK_URL_WITH_QUERY.search(s):
            violations.append(f"callback_url_with_query:{key or 'value'}")
        if _RAW_QUERY_SENSITIVE.search(s):
            violations.append(f"raw_query_sensitive:{key or 'value'}")
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
        if key not in ("payload_hash",) and _LONG_DIGITS.search(s):
            if not _is_known_safe_identifier(s):
                violations.append(f"long_digits_possible_id:{key or 'value'}")

    _walk(obj)
    return sorted(set(violations))


# Back-compat alias used by some shared tests.
scan_ledger_for_leaks = scan_packet_for_leaks


# --------------------------------------------------------------------------- #
# Deterministic serialization
# --------------------------------------------------------------------------- #
def serialize(obj):
    """Deterministic JSON: sorted keys, stable separators, trailing newline."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization."""
    return hashlib.sha256(serialize(obj).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Official docs sources (symbolic, token/id/handle/query-free)
# --------------------------------------------------------------------------- #
def build_official_docs_sources():
    """Concise, symbolic record of the official X OAuth docs inspected."""
    return [
        {
            "source_family": "x_oauth2_authorization_code_pkce",
            "title": "OAuth 2.0 Authorization Code Flow with PKCE - X",
            "url_or_symbolic_ref": (
                "https://docs.x.com/fundamentals/authentication/oauth-2-0/"
                "authorization-code"
            ),
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "accessible",
            "notes": (
                "Reference for the callback redirect step; the dry-run stub "
                "consumes only symbolic event classes, never a real callback "
                "URL, code, or state. No flow initiated."
            ),
        },
        {
            "source_family": "x_oauth2_user_context",
            "title": "X OAuth 2.0 Making Requests on Behalf of Users",
            "url_or_symbolic_ref": (
                "https://docs.x.com/fundamentals/authentication/oauth-2-0/"
                "user-access-token"
            ),
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "accessible",
            "notes": (
                "User access token context: token exchange remains out of "
                "scope and blocked; the stub never redeems a code."
            ),
        },
        {
            "source_family": "x_authentication_overview",
            "title": "X API Authentication Overview (OAuth 2.0 user context)",
            "url_or_symbolic_ref": (
                "https://docs.x.com/fundamentals/authentication/overview"
            ),
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "accessible",
            "notes": (
                "Confirms state and PKCE are required; the stub records only "
                "match/presence classes, never raw values."
            ),
        },
        {
            "source_family": "x_developer_portal",
            "title": "X Developer Portal / Console - access tier verification",
            "url_or_symbolic_ref": "https://developer.x.com/en/portal",
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "gated_login_required",
            "notes": (
                "Access-tier, app existence, and redirect URI registration "
                "require portal login; treated as a blocker, not an "
                "assumption. No login performed."
            ),
        },
    ]


# --------------------------------------------------------------------------- #
# Symbolic callback events (fake placeholders only)
# --------------------------------------------------------------------------- #
def build_symbolic_callback_events():
    """Deterministic fake-only symbolic callback events (no real material).

    Each event is a symbolic input object accepted by the dry-run handler. It
    contains ONLY allowed symbolic input fields and class strings; never a raw
    URL, query, code, state, token, or account identifier.
    """
    return [
        {
            "fixture_name": "success_callback_symbolic",
            "callback_class": "success_code_present_state_match",
            "state_match_class": "match",
            "code_present_class": "present",
            "symbolic_inputs_only": True,
        },
        {
            "fixture_name": "denied_callback_symbolic",
            "callback_class": "user_denied_or_declined",
            "denial_or_error_class": "user_denied",
            "symbolic_inputs_only": True,
        },
        {
            "fixture_name": "missing_code_callback_symbolic",
            "callback_class": "missing_code",
            "code_present_class": "missing",
            "symbolic_inputs_only": True,
        },
        {
            "fixture_name": "missing_state_callback_symbolic",
            "callback_class": "missing_state",
            "state_match_class": "missing",
            "symbolic_inputs_only": True,
        },
        {
            "fixture_name": "state_mismatch_callback_symbolic",
            "callback_class": "state_mismatch",
            "state_match_class": "mismatch",
            "symbolic_inputs_only": True,
        },
        {
            "fixture_name": "duplicate_callback_symbolic",
            "callback_class": "duplicate_or_replayed_callback",
            "replay_detected_class": "replay_detected",
            "symbolic_inputs_only": True,
        },
        {
            "fixture_name": "expired_or_used_code_callback_symbolic",
            "callback_class": "expired_or_used_authorization_code",
            "code_present_class": "expired",
            "symbolic_inputs_only": True,
        },
        {
            "fixture_name": "malformed_callback_symbolic",
            "callback_class": "malformed_callback",
            "malformed_class": "malformed",
            "symbolic_inputs_only": True,
        },
        {
            "fixture_name": "timeout_callback_symbolic",
            "callback_class": "timeout_no_callback",
            "timeout_class": "timed_out",
            "symbolic_inputs_only": True,
        },
        {
            "fixture_name": "unexpected_error_callback_symbolic",
            "callback_class": "unexpected_error_redacted",
            "denial_or_error_class": "unexpected",
            "symbolic_inputs_only": True,
        },
    ]


# Mapping of callback_class -> output class overrides.
_CLASS_MAP = {
    "success_code_present_state_match": {
        "terminal_result_class": "success_terminal",
        "state_match_class": "match",
        "code_present_class": "present",
    },
    "user_denied_or_declined": {
        "terminal_result_class": "denied_terminal",
        "denial_or_error_class": "user_denied",
    },
    "missing_code": {
        "terminal_result_class": "error_terminal",
        "code_present_class": "missing",
    },
    "missing_state": {
        "terminal_result_class": "error_terminal",
        "state_match_class": "missing",
    },
    "state_mismatch": {
        "terminal_result_class": "error_terminal",
        "state_match_class": "mismatch",
    },
    "duplicate_or_replayed_callback": {
        "terminal_result_class": "replay_terminal",
        "replay_detected_class": "replay_detected",
    },
    "expired_or_used_authorization_code": {
        "terminal_result_class": "error_terminal",
        "code_present_class": "expired",
    },
    "malformed_callback": {
        "terminal_result_class": "error_terminal",
        "malformed_class": "malformed",
    },
    "timeout_no_callback": {
        "terminal_result_class": "timeout_terminal",
        "timeout_class": "timed_out",
        "callback_received": False,
    },
    "unexpected_error_redacted": {
        "terminal_result_class": "error_terminal",
        "denial_or_error_class": "unexpected",
    },
}


def _base_ledger_output():
    """Return a redacted ledger output with all defaults set (allowed fields)."""
    return {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "platform": PLATFORM,
        "attempt_id_class": "opaque_attempt_class_no_raw_id",
        "callback_received": True,
        "callback_class": None,
        "terminal_result_class": None,
        "state_match_class": "not_applicable",
        "code_present_class": "not_applicable",
        "denial_or_error_class": "none",
        "timeout_class": "none",
        "replay_detected_class": "none",
        "malformed_class": "none",
        "redaction_verified": True,
        "no_raw_callback_url_persisted": True,
        "no_raw_query_persisted": True,
        "no_authorization_code_persisted": True,
        "no_state_persisted": True,
        "no_error_description_persisted": True,
        "no_token_persisted": True,
        "no_account_identifier_persisted": True,
        "one_terminal_result_or_timeout": True,
        "token_exchange_blocked": True,
        "next_required_gate": NEXT_TASK,
        "status": "pass",
        "blocked_reasons": [],
    }


def _looks_unsafe(value):
    """True if a string value looks token/url/query/handle/long-id-like."""
    if not isinstance(value, str):
        return False
    if value in _SAFE_SYMBOLIC_PLACEHOLDERS:
        return False
    if _CALLBACK_URL_WITH_QUERY.search(value):
        return True
    if _RAW_QUERY_SENSITIVE.search(value):
        return True
    for pat in _SECRET_LIKE:
        if pat.search(value):
            return True
    if _BEARER_TOKEN.search(value):
        return True
    if _HANDLE_LIKE.search(value):
        return True
    if _LONG_DIGITS.search(value) and not _is_known_safe_identifier(value):
        return True
    return False


def handle_symbolic_callback_event(event):
    """Pure-function dry-run handler: symbolic event -> redacted ledger output.

    Fails closed WITHOUT echoing raw input if the event contains a forbidden
    field, is not symbolic-only, has an unknown callback_class, or contains any
    token/url/query/handle/long-id-looking value.
    """
    blocked = []

    if not isinstance(event, dict):
        out = _base_ledger_output()
        out["callback_class"] = "rejected_redacted"
        out["terminal_result_class"] = "rejected_terminal"
        out["denial_or_error_class"] = "rejected"
        out["status"] = "fail_closed"
        out["blocked_reasons"] = ["input_not_a_mapping"]
        return out

    # Forbidden input fields present?
    for k in event.keys():
        if str(k).lower() in set(FORBIDDEN_SYMBOLIC_INPUT_FIELDS):
            blocked.append(f"forbidden_input_field:{str(k).lower()}")
        elif str(k) not in ALLOWED_SYMBOLIC_INPUT_FIELDS:
            blocked.append(f"unexpected_input_field:{str(k)}")

    # symbolic_inputs_only must be present and true.
    if event.get("symbolic_inputs_only") is not True:
        blocked.append("symbolic_inputs_only_not_true")

    # Any unsafe-looking value? (never echo the value itself)
    for k, v in event.items():
        if _looks_unsafe(v):
            blocked.append(f"unsafe_input_value:{str(k).lower()}")

    callback_class = event.get("callback_class")
    if callback_class not in _CLASS_MAP:
        blocked.append("unknown_callback_class")

    if blocked:
        out = _base_ledger_output()
        out["callback_class"] = "rejected_redacted"
        out["terminal_result_class"] = "rejected_terminal"
        out["denial_or_error_class"] = "rejected"
        out["status"] = "fail_closed"
        out["blocked_reasons"] = sorted(set(blocked))
        return out

    out = _base_ledger_output()
    out["callback_class"] = callback_class
    out.update(_CLASS_MAP[callback_class])
    # Enforce the hard invariants regardless of the class map.
    out["redaction_verified"] = True
    out["no_raw_callback_url_persisted"] = True
    out["no_raw_query_persisted"] = True
    out["no_authorization_code_persisted"] = True
    out["no_state_persisted"] = True
    out["no_error_description_persisted"] = True
    out["no_token_persisted"] = True
    out["no_account_identifier_persisted"] = True
    out["one_terminal_result_or_timeout"] = True
    out["token_exchange_blocked"] = True
    out["next_required_gate"] = NEXT_TASK
    out["status"] = "pass"
    out["blocked_reasons"] = []
    return out


def validate_ledger_output(output):
    """Return a sorted list of contract violations for a ledger output."""
    violations = []
    if not isinstance(output, dict):
        return ["output_not_a_mapping"]
    allowed = set(ALLOWED_LEDGER_OUTPUT_FIELDS)
    forbidden = set(FORBIDDEN_LEDGER_OUTPUT_FIELDS)
    for k in output.keys():
        if k in forbidden:
            violations.append(f"forbidden_output_field:{k}")
        elif k not in allowed:
            violations.append(f"unexpected_output_field:{k}")
    # Required hard invariants.
    for flag in (
        "redaction_verified", "no_raw_callback_url_persisted",
        "no_raw_query_persisted", "no_authorization_code_persisted",
        "no_state_persisted", "no_error_description_persisted",
        "no_token_persisted", "no_account_identifier_persisted",
        "one_terminal_result_or_timeout", "token_exchange_blocked",
    ):
        if output.get(flag) is not True:
            violations.append(f"invariant_not_true:{flag}")
    return sorted(set(violations))


def build_symbolic_handler_outputs():
    """Run the handler over all symbolic events; return name -> output map."""
    outputs = {}
    for event in build_symbolic_callback_events():
        outputs[event["fixture_name"]] = handle_symbolic_callback_event(event)
    return outputs


# --------------------------------------------------------------------------- #
# X OAuth local callback handler dry-run stub packet
# --------------------------------------------------------------------------- #
def build_packet():
    """Deep, dry-run-stub-only X OAuth local callback handler packet."""
    packet = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "platform": PLATFORM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inherited_0174cy_commit": INHERITED_0174CY_COMMIT,
        "docs_access_status": (
            "partially_accessible: authorization-code-with-pkce, user-access-"
            "token, and authentication overview accessible; developer portal "
            "access/tier gated (login required, not performed)"
        ),
        "official_docs_checked": True,
        "official_docs_sources": build_official_docs_sources(),
        "oauth_flow_family_symbolic": OAUTH_FLOW_FAMILY_SYMBOLIC,
        "local_callback_handler_stub_status":
            "dry_run_stub_only_no_real_callback",
        "developer_portal_access_status": "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "access_tier_blocker": (
            "developer portal access/tier cannot be verified without login; "
            "any plan/access-tier ambiguity is a blocker, not an assumption"
        ),
        "accepted_0174cy_contract_reference":
            ACCEPTED_0174CY_CONTRACT_REFERENCE,
        "handler_input_contract": (
            "the dry-run handler accepts ONLY symbolic event dicts whose keys "
            "are within the allowed symbolic input fields and whose "
            "symbolic_inputs_only is true; it never accepts a raw URL, raw "
            "query string, code, state, token, or account identifier"
        ),
        "handler_output_contract": (
            "the dry-run handler emits ONLY a redacted ledger object using the "
            "accepted 0174CY allowed fields; every output sets redaction and "
            "no_*_persisted booleans true, one_terminal_result_or_timeout "
            "true, and token_exchange_blocked true"
        ),
        "handler_rejection_policy": (
            "the handler fails closed (status fail_closed) WITHOUT echoing raw "
            "input if any forbidden input field is present, symbolic_inputs_"
            "only is missing/false, the callback_class is unknown, or any "
            "value looks token-like / URL-with-query / raw-query / long-id / "
            "raw-handle; rejected output is still fully redacted"
        ),
        "allowed_symbolic_input_fields": list(ALLOWED_SYMBOLIC_INPUT_FIELDS),
        "forbidden_symbolic_input_fields": list(
            FORBIDDEN_SYMBOLIC_INPUT_FIELDS),
        "allowed_ledger_output_fields": list(ALLOWED_LEDGER_OUTPUT_FIELDS),
        "forbidden_ledger_output_fields": list(FORBIDDEN_LEDGER_OUTPUT_FIELDS),
        "symbolic_callback_events": build_symbolic_callback_events(),
        "symbolic_handler_outputs": build_symbolic_handler_outputs(),
        "one_terminal_result_or_timeout_policy": (
            "the dry-run handler resolves each symbolic event to exactly one "
            "terminal result OR timeout; duplicate/replayed callbacks are "
            "terminal redacted classes and never trigger token exchange"
        ),
        "replay_detection_policy": (
            "replay detection records only replay_detected_class; never raw "
            "callback data, URL, or query"
        ),
        "state_validation_policy": (
            "state validation records match/mismatch/missing/expired classes "
            "only; never raw state"
        ),
        "code_presence_policy": (
            "code validation records present/missing/expired classes only; "
            "never the raw authorization code"
        ),
        "denial_error_policy": (
            "denial/error records a class only; never raw error_description"
        ),
        "timeout_policy": (
            "timeout records a class only and sets callback_received false; no "
            "retry and no polling"
        ),
        "malformed_callback_policy": (
            "malformed callback records a class only; never raw URL or query "
            "string"
        ),
        "unexpected_error_policy": (
            "unexpected errors fail closed and redact everything; only an "
            "unexpected class is recorded"
        ),
        "token_exchange_boundary_policy": (
            "token exchange remains blocked; the stub never calls the token "
            "endpoint and sets token_exchange_blocked true for ALL classes "
            "including success"
        ),
        "pkce_boundary_policy": (
            "PKCE generation remains out of scope; only symbolic classes are "
            "allowed; no real state/code_verifier/code_challenge generated"
        ),
        "redaction_policy": (
            "tokens, bearer strings, auth codes, state, code_verifier, "
            "code_challenge, callback URLs with query, and raw query strings "
            "are never logged raw; outputs store booleans/classes only"
        ),
        "redaction_rules": [
            "block token-like values",
            "block bearer token strings",
            "block authorization-code-like values",
            "block raw state values",
            "block raw code_verifier values",
            "block raw code_challenge values",
            "block callback URLs with query params",
            "block raw query strings containing code/state/token/error",
            "block raw X/Twitter handles",
            "block raw account/user/post/tweet/community/media/place ids",
            "block long numeric IDs",
            "block forbidden raw keys",
            "allow safe official docs refs and safe symbolic placeholders",
        ],
        "forbidden_runtime_behaviors": [
            "call X or any platform API",
            "perform OAuth / open authorize URL",
            "open browser or developer portal login",
            "start a callback server or bind a localhost port",
            "listen on localhost",
            "receive / parse / process a real callback URL or raw query",
            "exchange authorization code / call token endpoint",
            "generate real state / code_verifier / code_challenge",
            "read Client ID / Client Secret / access token / refresh token",
            "read env or dotenv",
            "bind account or persist account id / user id / handle",
            "post/edit/delete/repost/quote/bookmark/like/reply/DM",
            "fetch metrics / create webhook / scrape",
            "create a generic publisher or OAuth execution command",
            "implement a real callback server",
        ],
        "required_before_real_callback_server": [
            "operator explicit GO for the callback-server gate",
            "explicit allowlisted localhost interface+port chosen",
            "redacted redirect ledger schema accepted",
            "one-terminal-result-or-timeout stop policy accepted",
            "no-raw-query-log policy accepted",
        ],
        "required_before_real_authorize_url": [
            "Client ID handling policy accepted",
            "redirect URI policy accepted",
            "state policy accepted",
            "PKCE policy accepted",
            "operator explicit GO",
        ],
        "required_before_real_pkce_generation": [
            "PKCE policy accepted",
            "state policy accepted",
            "single-use/per-attempt/no-raw-log enforcement tests accepted",
            "operator explicit GO",
        ],
        "required_before_token_exchange": [
            "callback success class achieved (code present)",
            "state match class confirmed",
            "token response redaction ledger design accepted",
            "token endpoint call budget and no-retry policy defined",
            "token storage/rotation/revocation policy accepted",
            "operator explicit GO",
        ],
        "required_before_account_binding": [
            "OAuth user-context design accepted",
            "callback + PKCE dry-run design accepted",
            "redirect ledger + callback fixture contract accepted",
            "local callback handler dry-run stub accepted",
            "credential-readiness gate accepted (no raw token persisted)",
            "account-binding proof uses redacted booleans/classes only",
            "no raw account id/handle persisted; hashed local-only proof only "
            "if explicitly approved later",
        ],
        "required_before_dry_run": [
            "OAuth user-context design accepted",
            "callback + PKCE dry-run design accepted",
            "redirect ledger + callback fixture contract accepted",
            "local callback handler dry-run stub accepted",
            "credential-readiness gate accepted",
            "account-binding proof accepted",
            "text-only payload field contract accepted",
        ],
        "required_before_live": [
            "credential-readiness gate accepted",
            "account-binding proof accepted",
            "text-only dry-run accepted",
            "exact payload hash locked",
            "operator approval",
            "one-time live GO",
            "duplicate-send prevention",
            "pre-attempt marker",
            "request_budget=1",
            "no retry",
            "redacted post-send ledger",
        ],
        "blocker_policy": (
            "any inaccessible/gated/redirected/deprecated/ambiguous official "
            "page is recorded as a blocker; capability is never assumed and "
            "third-party blogs/tutorials/SDK examples are never treated as "
            "authority"
        ),
        "blockers": sorted(set([
            "developer access/tier not yet verified (portal login required)",
            "redirect URI not yet registered/verified in portal",
            "public vs confidential client type not yet decided",
            "localhost callback interface+port not yet allowlisted",
            "callback server gate not yet accepted",
            "token response redaction ledger not yet designed",
            "any X plan/access-tier ambiguity is a blocker, not an assumption",
        ])),
        "caveats": [
            "OAuth 2.0 Authorization Code Flow with PKCE (user context) is the "
            "expected family, but NO flow, authorize URL, or callback is "
            "exercised now",
            "this is a dry-run stub over symbolic events only; no real "
            "callback handler / server is implemented",
            "token exchange is explicitly out of scope and blocked",
            "developer portal access tier and redirect URI registration remain "
            "unverified (no login)",
        ],
        "recommended_next_task": NEXT_TASK,
        "no_live_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_account_binding_performed": True,
        "no_oauth_flow_performed": True,
        "no_authorize_url_opened": True,
        "no_browser_login_performed": True,
        "no_developer_portal_login_performed": True,
        "no_callback_server_started": True,
        "no_localhost_port_bound": True,
        "no_authorization_code_generated_or_received": True,
        "no_real_callback_url_processed": True,
        "no_raw_callback_query_processed": True,
        "no_state_generated": True,
        "no_code_verifier_generated": True,
        "no_code_challenge_generated": True,
        "no_token_exchange_performed": True,
        "no_token_persisted": True,
        "no_client_id_read": True,
        "no_client_secret_read": True,
        "no_posting_performed": True,
        "no_metrics_fetched": True,
        "no_webhook_created": True,
        "no_reply_dm_created": True,
        "no_scraping_performed": True,
        "no_autonomous_publishing": True,
        "redaction_verified": True,
        "status": "pass",
        "blocked_reasons": [],
    }
    return packet


# Back-compat alias.
build_x_packet = build_packet


# --------------------------------------------------------------------------- #
# README
# --------------------------------------------------------------------------- #
def build_readme():
    """Concise operator-facing README for the 0174CZ dry-run stub packet."""
    return (
        "# 0174CZ X OAuth Local Callback Handler Dry-Run Stub\n"
        "\n"
        "Strictly local, official-doc-grounded, DRY-RUN-STUB-ONLY X OAuth "
        "local callback handler. It consumes ONLY symbolic callback event "
        "objects and emits a redacted callback ledger matching the accepted "
        "0174CY contract. No OAuth flow, no authorize URL opened, no callback "
        "server started, no localhost port bound, no real callback URL or raw "
        "query processed, no browser/developer-portal login, no token "
        "exchange, no Client ID/Secret read, no state/code_verifier/"
        "code_challenge generated, no account binding, no posting.\n"
        "\n"
        "## Inherited posture\n"
        "\n"
        "- Inherits the conservative posture: live posting is "
        "`blocked_until_new_explicit_task_and_operator_go`.\n"
        "- This task only implements a dry-run stub over symbolic events; it "
        "does not enable any live path and implements no real server.\n"
        "\n"
        "## OAuth flow (symbolic)\n"
        "\n"
        "- Flow family: OAuth 2.0 Authorization Code Flow with PKCE (user "
        "context) callback handler stub. Not initiated now.\n"
        "- Token exchange is explicitly out of scope and blocked for ALL "
        "classes, including success.\n"
        "\n"
        "## Official docs inspected\n"
        "\n"
        "- Authorization Code Flow with PKCE "
        "(`docs.x.com/fundamentals/authentication/oauth-2-0/"
        "authorization-code`) -- accessible.\n"
        "- User access token / requests on behalf of users "
        "(`docs.x.com/fundamentals/authentication/oauth-2-0/"
        "user-access-token`) -- accessible.\n"
        "- Authentication Overview "
        "(`docs.x.com/fundamentals/authentication/overview`) -- accessible.\n"
        "- Developer Portal access tiers (`developer.x.com/en/portal`) -- "
        "gated (login required, not performed) -> blocker.\n"
        "\n"
        "## Handler input contract\n"
        "\n"
        "- Accepts ONLY symbolic event dicts with allowed fields "
        "(`fixture_name`, `callback_class`, `*_class`, `symbolic_inputs_"
        "only`).\n"
        "- Rejects (fails closed, no raw echo) any forbidden input field, "
        "missing/false `symbolic_inputs_only`, unknown `callback_class`, or "
        "any token/URL-with-query/raw-query/long-id/raw-handle value.\n"
        "\n"
        "## Handler output contract\n"
        "\n"
        "- Emits ONLY the accepted 0174CY allowed ledger fields.\n"
        "- Every output sets `redaction_verified`, all `no_*_persisted`, "
        "`one_terminal_result_or_timeout`, and `token_exchange_blocked` to "
        "true.\n"
        "\n"
        "## Symbolic class mapping\n"
        "\n"
        "- success -> `success_terminal`, match, present.\n"
        "- denied -> `denied_terminal`, user_denied.\n"
        "- missing_code -> `error_terminal`, code missing.\n"
        "- missing_state -> `error_terminal`, state missing.\n"
        "- state_mismatch -> `error_terminal`, state mismatch.\n"
        "- duplicate/replay -> `replay_terminal`, replay_detected.\n"
        "- expired/used code -> `error_terminal`, code expired.\n"
        "- malformed -> `error_terminal`, malformed.\n"
        "- timeout -> `timeout_terminal`, timed_out, callback_received "
        "false.\n"
        "- unexpected error -> `error_terminal`, unexpected.\n"
        "\n"
        "## Token-exchange boundary\n"
        "\n"
        "- Out of scope and blocked. No token endpoint call. "
        "`token_exchange_blocked` is true for all classes including success.\n"
        "\n"
        "## What this did NOT do\n"
        "\n"
        "No X (or any platform) API call. No OAuth flow, authorize URL, "
        "browser login, or developer-portal login. No callback server, no "
        "localhost port bound, no real callback URL or raw query processed. "
        "No authorization code, token exchange, or token persistence. No "
        "Client ID/Secret read. No state/code_verifier/code_challenge "
        "generated. No account binding, no credential or env read, no "
        "credential-entry schema. No post/edit/delete/repost/quote/bookmark/"
        "like/reply/DM, metrics, webhook, or scraping. The module never "
        "browses docs at runtime; docs reading was an Antigravity/operator "
        "activity before writing symbolic packet data.\n"
        "\n"
        "## Next\n"
        "\n"
        f"Recommended next task: `{NEXT_TASK}`.\n"
    )


# --------------------------------------------------------------------------- #
# Main gate
# --------------------------------------------------------------------------- #
def run_gate(*, write=False, repo_root=None):
    """Run the strictly-local 0174CZ local callback handler dry-run stub gate.

    Writing occurs ONLY when ``write=True`` AND the packet passes the redaction
    scan. Fail-closed.
    """
    if repo_root is None:
        repo_root = os.path.dirname(os.path.dirname(__file__))

    blocked = []
    status = "pass"

    packet = build_packet()

    violations = scan_packet_for_leaks(packet)
    if violations:
        blocked.append(f"packet_redaction_violation:{PACKET_FILENAME}")
        status = "fail_closed"
        packet["status"] = "fail_closed"
        packet["blocked_reasons"] = sorted(set(blocked))

    checksum = compute_checksum(packet)

    packet_written = False
    readme_written = False

    if write and not blocked:
        out_dir = os.path.join(repo_root, PACKET_REL_DIR)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, PACKET_FILENAME), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(serialize(packet))
        packet_written = True
        with open(os.path.join(out_dir, README_FILENAME), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(build_readme())
        readme_written = True

    return {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "platform": PLATFORM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inherited_0174cy_commit": INHERITED_0174CY_COMMIT,
        "inherited_operator_posture": {
            "live_posting_state":
                "blocked_until_new_explicit_task_and_operator_go",
            "pause_additional_live_sends": True,
        },
        "packet_path": os.path.join(
            PACKET_REL_DIR, PACKET_FILENAME).replace(os.sep, "/"),
        "readme_path": os.path.join(
            PACKET_REL_DIR, README_FILENAME).replace(os.sep, "/"),
        "write_requested": bool(write),
        "packet_written": bool(packet_written),
        "readme_written": bool(readme_written),
        "packet_checksum": checksum,
        "oauth_flow_family_symbolic": OAUTH_FLOW_FAMILY_SYMBOLIC,
        "local_callback_handler_stub_status":
            "dry_run_stub_only_no_real_callback",
        "developer_portal_access_status":
            "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "callback_classes": list(CALLBACK_CLASSES),
        "next_recommended_task": NEXT_TASK,
        "no_live_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_account_binding_performed": True,
        "no_oauth_flow_performed": True,
        "no_authorize_url_opened": True,
        "no_browser_login_performed": True,
        "no_developer_portal_login_performed": True,
        "no_callback_server_started": True,
        "no_localhost_port_bound": True,
        "no_authorization_code_generated_or_received": True,
        "no_real_callback_url_processed": True,
        "no_raw_callback_query_processed": True,
        "no_state_generated": True,
        "no_code_verifier_generated": True,
        "no_code_challenge_generated": True,
        "no_token_exchange_performed": True,
        "no_token_persisted": True,
        "no_client_id_read": True,
        "no_client_secret_read": True,
        "no_posting_performed": True,
        "no_metrics_fetched": True,
        "no_webhook_created": True,
        "no_reply_dm_created": True,
        "no_scraping_performed": True,
        "no_autonomous_publishing": True,
        "redaction_verified": True,
        "status": status,
        "blocked_reasons": sorted(set(blocked)),
    }


def main(argv=None):
    """CLI entry: prints the redacted gate summary as JSON."""
    if argv is None:
        argv = sys.argv[2:]
    write = FLAG_WRITE in argv
    print(json.dumps(run_gate(write=write), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
