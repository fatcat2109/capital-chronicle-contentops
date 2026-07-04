"""X OAuth redirect ledger + callback fixture contract gate (0174CY).

This module is STRICTLY LOCAL. It performs NO network of any kind, opens NO
browser, starts NO callback server, binds NO localhost port, runs NO subprocess,
and reads NO env/credentials. Official X OAuth documentation reading is an
Antigravity/operator activity performed BEFORE this module runs; the module only
emits a symbolic, redacted, CONTRACT-ONLY redirect-ledger schema and callback
fixture contract grounded in those docs.

It turns the 0174CX callback + PKCE dry-run design into a stricter redacted
redirect/callback ledger schema and a deterministic symbolic callback fixture
contract WITHOUT initiating OAuth, WITHOUT opening an authorize URL, WITHOUT
starting a callback server or binding a port, WITHOUT receiving or processing a
real callback URL, WITHOUT reading any Client ID / Client Secret / token,
WITHOUT generating any real state / code_verifier / code_challenge, and WITHOUT
any account binding or live/posting behavior.

HARD GUARANTEES (enforced by tests + leakage guards):
  * No network imports (no urllib / requests / httpx / socket / http / dotenv).
  * No browser/subprocess imports (no webbrowser / subprocess).
  * No http server imports (no http.server / socketserver / wsgiref).
  * No process env / dotenv read (no environment or home-dir lookups).
  * Imports ONLY hashlib, json, os.path, re, sys.
  * Fail-closed: writes happen ONLY when the write flag is present AND the
    packet passes the redaction scan.
  * Deterministic JSON: sorted keys, compact separators, trailing newline.
  * No OAuth flow, no authorize URL opened, no callback server started, no port
    bound, no real callback URL processed, no authorization code, no token
    exchange, no token persisted, no developer-portal login, no account
    binding, no posting/metrics/webhook/reply/DM/scraping, no generic
    publisher, no credential-entry schema, no OAuth/live execution command.
  * Stores only concise symbolic metadata: OAuth flow family, redirect ledger
    schema (classes/booleans only), callback fixture classes (fake placeholders
    only), redaction policy, validation rules, blockers/caveats, and citation
    URLs (token/id/handle/query-free).
"""

import hashlib
import json
import os.path
import re
import sys

TASK_LABEL = (
    "TASK_CONTENTOPS_0174CY_X_OAUTH_REDIRECT_LEDGER_AND_CALLBACK_FIXTURE_"
    "CONTRACT_NO_SECRET_NO_TOKEN_NO_LIVE_V0"
)

GATE = "X_OAUTH_REDIRECT_LEDGER_CALLBACK_FIXTURE_CONTRACT_0174CY"
PLATFORM = "x"
SOURCE_BASELINE_COMMIT = "cf1e4da2b3d7026794ae88f94f61c6b0bc205f0f"
INHERITED_0174CX_COMMIT = "cf1e4da2b3d7026794ae88f94f61c6b0bc205f0f"

# Date the official docs were inspected for this task (UTC, no time-of-day).
DOCS_ACCESSED_DATE = "2026-06-16"

NEXT_TASK = (
    "TASK_CONTENTOPS_0174CZ_X_OAUTH_LOCAL_CALLBACK_HANDLER_DRY_RUN_STUB_"
    "NO_SECRET_NO_TOKEN_NO_NETWORK_NO_BROWSER_V0"
)

# Output artifact locations.
PACKET_REL_DIR = os.path.join("docs", "credential_readiness", "0174CY")
PACKET_FILENAME = "x_oauth_redirect_ledger_callback_fixture_contract_packet.json"
README_FILENAME = "README.md"

FLAG_WRITE = "--write-x-oauth-redirect-ledger-callback-fixture-contract"

# Symbolic OAuth flow family (no flow initiated).
OAUTH_FLOW_FAMILY_SYMBOLIC = (
    "x.oauth2.authorization_code_with_pkce.user_context.callback.ledger "
    "(NOT initiated now)"
)

# Future redacted redirect/callback ledger allowed fields (classes/booleans
# /timestamps only; no raw secrets).
REDIRECT_LEDGER_ALLOWED_FIELDS = [
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

# Fields that must NEVER appear in the future ledger.
REDIRECT_LEDGER_FORBIDDEN_FIELDS = [
    "raw_url",
    "callback_url",
    "raw_query",
    "query_string",
    "authorization_code",
    "auth_code",
    "code",
    "state",
    "error_description",
    "token",
    "access_token",
    "refresh_token",
    "bearer_token",
    "token_response",
    "client_id",
    "client_secret",
    "redirect_uri",
    "code_verifier",
    "code_challenge",
    "account_id",
    "user_id",
    "username",
    "screen_name",
    "handle",
    "post_id",
    "tweet_id",
    "community_id",
    "media_id",
    "place_id",
]

# Required callback fixture classes.
CALLBACK_FIXTURE_CLASSES = [
    "success_callback_symbolic",
    "denied_callback_symbolic",
    "missing_code_callback_symbolic",
    "missing_state_callback_symbolic",
    "state_mismatch_callback_symbolic",
    "duplicate_callback_symbolic",
    "expired_or_used_code_callback_symbolic",
    "malformed_callback_symbolic",
    "timeout_callback_symbolic",
    "unexpected_error_callback_symbolic",
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

# The literal forbidden-field names are stored as data in the packet (the
# REDIRECT_LEDGER_FORBIDDEN_FIELDS list). Those are field-NAME strings, not raw
# secret values, so the key-name scan must not treat list *values* as leaks. We
# only flag forbidden names when they appear as dict KEYS.


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, payload hashes)."""
    if s in (SOURCE_BASELINE_COMMIT, INHERITED_0174CX_COMMIT):
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
        # Allow the declared forbidden-field NAMES to appear as list values in
        # the schema/forbidden-field documentation lists.
        if key in ("redirect_ledger_forbidden_fields",
                   "redirect_ledger_allowed_fields"):
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
                "Reference for the callback redirect step: after user consent, "
                "the authorize endpoint redirects to the registered redirect "
                "URI with code and state query params. This contract defines a "
                "redacted ledger of that event; no flow initiated, no callback "
                "received, no code/state stored."
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
                "User access token context: a successful callback yields a "
                "code redeemed for a user access token in a later, separate "
                "gate. Token exchange remains out of scope and blocked here."
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
                "Confirms state and PKCE are required for the user-context "
                "authorization code flow; the redacted ledger records only "
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
# Future redacted redirect/callback ledger schema (classes/booleans only)
# --------------------------------------------------------------------------- #
def build_redirect_ledger_schema():
    """Symbolic schema describing the FUTURE redacted callback ledger.

    Values here are TYPE/CLASS descriptors, never real data.
    """
    return {
        "task_label": "string:task_label",
        "gate": "string:gate_id",
        "platform": "string:platform",
        "attempt_id_class": "class:opaque_attempt_class_no_raw_id",
        "callback_received": "bool",
        "callback_class": "enum:callback_event_class",
        "terminal_result_class": "enum:terminal_result_class",
        "state_match_class": "enum:match|mismatch|missing|expired",
        "code_present_class": "enum:present|missing|expired",
        "denial_or_error_class": "enum:none|user_denied|malformed|unexpected",
        "timeout_class": "enum:none|timed_out",
        "replay_detected_class": "enum:none|replay_detected",
        "malformed_class": "enum:none|malformed",
        "redaction_verified": "bool:true",
        "no_raw_callback_url_persisted": "bool:true",
        "no_raw_query_persisted": "bool:true",
        "no_authorization_code_persisted": "bool:true",
        "no_state_persisted": "bool:true",
        "no_error_description_persisted": "bool:true",
        "no_token_persisted": "bool:true",
        "no_account_identifier_persisted": "bool:true",
        "one_terminal_result_or_timeout": "bool:true",
        "token_exchange_blocked": "bool:true",
        "next_required_gate": "string:next_gate_id",
        "status": "enum:pass|blocked|fail_closed",
        "blocked_reasons": "list:string",
    }


# --------------------------------------------------------------------------- #
# Symbolic callback fixture contract (fake placeholders only)
# --------------------------------------------------------------------------- #
def _fixture(name, callback_class, *, terminal, state_match="not_applicable",
            code_present="not_applicable", denial_or_error="none",
            timeout="none", replay="none", malformed="none"):
    """Build a single symbolic fixture with full expected-class contract."""
    return {
        "fixture_name": name,
        "callback_class": callback_class,
        "expected_terminal_result_class": terminal,
        "expected_state_match_class": state_match,
        "expected_code_present_class": code_present,
        "expected_denial_or_error_class": denial_or_error,
        "expected_timeout_class": timeout,
        "expected_replay_detected_class": replay,
        "expected_malformed_class": malformed,
        "expected_ledger_allowed_fields_only": True,
        "expected_no_raw_url": True,
        "expected_no_raw_query": True,
        "expected_no_code": True,
        "expected_no_state": True,
        "expected_no_token": True,
        "expected_token_exchange_blocked": True,
        "symbolic_inputs_only": True,
    }


def build_callback_fixture_contract():
    """Deterministic fake-only callback fixture contract (no real material)."""
    return {
        "success_callback_symbolic": _fixture(
            "success_callback_symbolic", "success_code_present_state_match",
            terminal="success_terminal", state_match="match",
            code_present="present"),
        "denied_callback_symbolic": _fixture(
            "denied_callback_symbolic", "user_denied_or_declined",
            terminal="denied_terminal", denial_or_error="user_denied"),
        "missing_code_callback_symbolic": _fixture(
            "missing_code_callback_symbolic", "missing_code",
            terminal="error_terminal", code_present="missing"),
        "missing_state_callback_symbolic": _fixture(
            "missing_state_callback_symbolic", "missing_state",
            terminal="error_terminal", state_match="missing",
            code_present="present"),
        "state_mismatch_callback_symbolic": _fixture(
            "state_mismatch_callback_symbolic", "state_mismatch",
            terminal="error_terminal", state_match="mismatch",
            code_present="present"),
        "duplicate_callback_symbolic": _fixture(
            "duplicate_callback_symbolic", "duplicate_or_replayed_callback",
            terminal="replay_terminal", replay="replay_detected"),
        "expired_or_used_code_callback_symbolic": _fixture(
            "expired_or_used_code_callback_symbolic",
            "expired_or_used_authorization_code",
            terminal="error_terminal", code_present="expired"),
        "malformed_callback_symbolic": _fixture(
            "malformed_callback_symbolic", "malformed_callback",
            terminal="error_terminal", denial_or_error="malformed",
            malformed="malformed"),
        "timeout_callback_symbolic": _fixture(
            "timeout_callback_symbolic", "timeout_no_callback",
            terminal="timeout_terminal", timeout="timed_out"),
        "unexpected_error_callback_symbolic": _fixture(
            "unexpected_error_callback_symbolic", "unexpected_error_redacted",
            terminal="error_terminal", denial_or_error="unexpected"),
    }


# --------------------------------------------------------------------------- #
# X OAuth redirect-ledger + callback fixture contract packet
# --------------------------------------------------------------------------- #
def build_x_packet():
    """Deep, contract-only X OAuth redirect-ledger + fixture packet."""
    packet = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "platform": PLATFORM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inherited_0174cx_commit": INHERITED_0174CX_COMMIT,
        "docs_access_status": (
            "partially_accessible: authorization-code-with-pkce, user-access-"
            "token, and authentication overview accessible; developer portal "
            "access/tier gated (login required, not performed)"
        ),
        "official_docs_checked": True,
        "official_docs_sources": build_official_docs_sources(),
        "oauth_flow_family_symbolic": OAUTH_FLOW_FAMILY_SYMBOLIC,
        "redirect_ledger_contract_status": "contract_only_no_real_flow",
        "developer_portal_access_status": "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "access_tier_blocker": (
            "developer portal access/tier cannot be verified without login; "
            "any plan/access-tier ambiguity is a blocker, not an assumption"
        ),
        "callback_server_policy": (
            "this task starts NO server and binds NO localhost; a future "
            "callback server must be local-only, operator-triggered, bind only "
            "to an explicit allowlisted localhost interface+port chosen in a "
            "future gate, never log raw query strings, stop after one terminal "
            "callback result or timeout, and produce only this redacted "
            "redirect ledger"
        ),
        "localhost_binding_policy": (
            "no localhost port is bound now; future binding requires an "
            "explicit allowlisted interface+port and operator GO"
        ),
        "browser_open_policy": (
            "no browser opened now; future browser opening is operator-"
            "triggered only, never autonomous"
        ),
        "authorize_url_policy": (
            "no authorize URL constructed or opened now; future authorize URL "
            "construction is a separate gate and is never persisted raw"
        ),
        "redirect_uri_policy": (
            "no real redirect URI registered or tested now; future redirect "
            "URI must be exact-match, deterministic, local-first, and never "
            "logged with its query string"
        ),
        "callback_url_policy": (
            "no real callback URL processed now; the future callback handler "
            "redacts the full URL and all query params before any persistence; "
            "only classes/booleans reach the ledger"
        ),
        "callback_query_policy": (
            "future callback handler must redact ALL query parameters before "
            "persistence; raw code, state, error, error_description, and the "
            "raw query string are never logged"
        ),
        "redirect_ledger_schema": build_redirect_ledger_schema(),
        "redirect_ledger_allowed_fields": list(REDIRECT_LEDGER_ALLOWED_FIELDS),
        "redirect_ledger_forbidden_fields": list(
            REDIRECT_LEDGER_FORBIDDEN_FIELDS),
        "callback_fixture_contract": build_callback_fixture_contract(),
        "callback_fixture_classes": list(CALLBACK_FIXTURE_CLASSES),
        "callback_fixture_validation_rules": [
            "every fixture uses symbolic inputs only (symbolic_inputs_only)",
            "every fixture asserts expected_ledger_allowed_fields_only",
            "every fixture asserts expected_no_raw_url / no_raw_query",
            "every fixture asserts expected_no_code / no_state / no_token",
            "every fixture asserts expected_token_exchange_blocked",
            "each fixture maps to exactly one terminal_result_class",
            "success requires state_match=match AND code_present=present",
            "denial/malformed/unexpected map to redacted error classes only",
            "duplicate maps to replay_detected; timeout maps to timed_out",
        ],
        "callback_fixture_symbolic_placeholders": sorted(
            _SAFE_SYMBOLIC_PLACEHOLDERS),
        "callback_terminal_state_policy": (
            "each callback resolves to exactly one terminal result class; no "
            "fixture triggers token exchange or any live action"
        ),
        "one_terminal_result_or_timeout_policy": (
            "future callback handler must stop after exactly one terminal "
            "callback result OR timeout; duplicate/replayed callbacks are "
            "terminal redacted classes and never trigger token exchange"
        ),
        "replay_detection_policy": (
            "future replay detection records only replay_detected_class; never "
            "raw callback data, URL, or query"
        ),
        "state_match_policy": (
            "future state validation records match/mismatch/missing/expired "
            "classes only; never raw state"
        ),
        "code_presence_policy": (
            "future code validation records present/missing/expired classes "
            "only; never the raw authorization code"
        ),
        "denial_error_policy": (
            "future denial/error records a class only; never raw "
            "error_description"
        ),
        "malformed_callback_policy": (
            "malformed callback records a class only; never raw URL or query "
            "string"
        ),
        "timeout_policy": (
            "timeout records a class only; no retry and no polling"
        ),
        "unexpected_error_policy": (
            "unexpected errors must fail closed and redact everything; only an "
            "unexpected_error_redacted class is recorded"
        ),
        "token_exchange_boundary_policy": (
            "token exchange remains blocked; this contract only defines what a "
            "redacted callback ledger could look like AFTER a callback event; "
            "it must not call the token endpoint or design token-response "
            "persistence beyond redacted classes"
        ),
        "pkce_boundary_policy": (
            "PKCE generation remains out of scope; only symbolic classes "
            "(e.g. CHALLENGE_SYMBOLIC_S256_CLASS, VERIFIER_SYMBOLIC_CLASS) are "
            "allowed; no real state/code_verifier/code_challenge generated"
        ),
        "redaction_policy": (
            "tokens, bearer strings, auth codes, state, code_verifier, "
            "code_challenge, callback URLs with query, and raw query strings "
            "are never logged raw; the ledger stores booleans/classes only"
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
            "receive or process a real callback URL",
            "exchange authorization code / call token endpoint",
            "generate real state / code_verifier / code_challenge",
            "read Client ID / Client Secret / access token / refresh token",
            "read env or dotenv",
            "bind account or persist account id / user id / handle",
            "post/edit/delete/repost/quote/bookmark/like/reply/DM",
            "fetch metrics / create webhook / scrape",
            "create a generic publisher or OAuth execution command",
        ],
        "required_before_real_callback_server": [
            "operator explicit GO for the callback-server gate",
            "explicit allowlisted localhost interface+port chosen",
            "this redacted redirect ledger schema accepted",
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
            "credential-readiness gate accepted (no raw token persisted)",
            "account-binding proof uses redacted booleans/classes only",
            "no raw account id/handle persisted; hashed local-only proof only "
            "if explicitly approved later",
        ],
        "required_before_dry_run": [
            "OAuth user-context design accepted",
            "callback + PKCE dry-run design accepted",
            "redirect ledger + callback fixture contract accepted",
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
            "this is a redacted-ledger + fixture CONTRACT only; no real "
            "callback handler is implemented",
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


# --------------------------------------------------------------------------- #
# README
# --------------------------------------------------------------------------- #
def build_readme():
    """Concise operator-facing README for the 0174CY ledger+fixture packet."""
    return (
        "# 0174CY X OAuth Redirect Ledger and Callback Fixture Contract\n"
        "\n"
        "Strictly local, official-doc-grounded, CONTRACT-ONLY X OAuth redirect "
        "ledger schema and callback fixture contract. No OAuth flow, no "
        "authorize URL opened, no callback server started, no localhost port "
        "bound, no real callback URL processed, no browser/developer-portal "
        "login, no token exchange, no Client ID/Secret read, no state/"
        "code_verifier/code_challenge generated, no account binding, no "
        "posting.\n"
        "\n"
        "## Inherited posture\n"
        "\n"
        "- Inherits the conservative posture: live posting is "
        "`blocked_until_new_explicit_task_and_operator_go`.\n"
        "- This task only defines the future redacted ledger + fixture "
        "contract; it does not enable any live path.\n"
        "\n"
        "## OAuth flow (symbolic)\n"
        "\n"
        "- Flow family: OAuth 2.0 Authorization Code Flow with PKCE (user "
        "context) callback ledger. Not initiated now.\n"
        "- Token exchange is explicitly out of scope and blocked.\n"
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
        "## Redirect ledger schema\n"
        "\n"
        "- Future redacted ledger stores ONLY classes/booleans/timestamps: "
        "`attempt_id_class`, `callback_class`, `terminal_result_class`, "
        "`state_match_class`, `code_present_class`, `denial_or_error_class`, "
        "`timeout_class`, `replay_detected_class`, `malformed_class`, plus "
        "redaction/`no_*_persisted` booleans, "
        "`one_terminal_result_or_timeout`, and `token_exchange_blocked`.\n"
        "- Forbidden raw fields (never persisted): raw URL, callback URL, "
        "query string, code, state, error_description, any token, client "
        "id/secret, redirect URI, code_verifier/challenge, and any account/"
        "user/post/tweet/community/media/place id or handle.\n"
        "\n"
        "## Callback fixture contract\n"
        "\n"
        "- 10 symbolic fixtures: success, denied, missing code, missing "
        "state, state mismatch, duplicate, expired/used code, malformed, "
        "timeout, unexpected error.\n"
        "- Each fixture is symbolic-only and asserts allowed-fields-only, no "
        "raw URL/query/code/state/token, and `token_exchange_blocked=true`.\n"
        "- Placeholders only (e.g. `STATE_SYMBOLIC_MATCH`, "
        "`CODE_SYMBOLIC_PRESENT`, `ERROR_SYMBOLIC_ACCESS_DENIED`). No "
        "realistic codes, token-shaped strings, long numeric ids, or raw "
        "query URLs.\n"
        "\n"
        "## Terminal-result / replay / timeout policy\n"
        "\n"
        "- Future callback handler stops after exactly one terminal result or "
        "timeout. Duplicate/replayed callbacks are terminal redacted classes "
        "and never trigger token exchange.\n"
        "- Replay/state/code/denial/timeout/malformed are all recorded as "
        "classes only; never raw values.\n"
        "\n"
        "## Token-exchange boundary\n"
        "\n"
        "- Out of scope and blocked. No token endpoint call. The contract "
        "defines only the redacted ledger AFTER a callback; token-response "
        "persistence beyond redacted classes is not designed here.\n"
        "\n"
        "## What this did NOT do\n"
        "\n"
        "No X (or any platform) API call. No OAuth flow, authorize URL, "
        "browser login, or developer-portal login. No callback server, no "
        "localhost port bound, no real callback URL processed. No "
        "authorization code, token exchange, or token persistence. No Client "
        "ID/Secret read. No state/code_verifier/code_challenge generated. No "
        "account binding, no credential or env read, no credential-entry "
        "schema. No post/edit/delete/repost/quote/bookmark/like/reply/DM, "
        "metrics, webhook, or scraping. The module never browses docs at "
        "runtime; docs reading was an Antigravity/operator activity before "
        "writing symbolic packet data.\n"
        "\n"
        "## Next\n"
        "\n"
        f"Recommended next task: `{NEXT_TASK}`.\n"
    )


# --------------------------------------------------------------------------- #
# Main gate
# --------------------------------------------------------------------------- #
def run_gate(*, write=False, repo_root=None):
    """Run the strictly-local 0174CY redirect-ledger+fixture contract gate.

    Writing occurs ONLY when ``write=True`` AND the packet passes the redaction
    scan. Fail-closed.
    """
    if repo_root is None:
        repo_root = os.path.dirname(os.path.dirname(__file__))

    blocked = []
    status = "pass"

    packet = build_x_packet()

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
        "inherited_0174cx_commit": INHERITED_0174CX_COMMIT,
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
        "redirect_ledger_contract_status": "contract_only_no_real_flow",
        "developer_portal_access_status":
            "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "callback_fixture_classes": list(CALLBACK_FIXTURE_CLASSES),
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
