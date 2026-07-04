"""X OAuth callback + PKCE dry-run design gate (0174CX).

This module is STRICTLY LOCAL. It performs NO network of any kind, opens NO
browser, starts NO callback server, binds NO localhost port, runs NO subprocess,
and reads NO env/credentials. Official X OAuth documentation reading is an
Antigravity/operator activity performed BEFORE this module runs; the module only
emits a symbolic, redacted, DESIGN-ONLY callback + PKCE dry-run policy packet
grounded in those docs.

It designs the FUTURE X OAuth callback + PKCE dry-run mechanics (Authorization
Code Flow with PKCE) WITHOUT initiating OAuth, WITHOUT opening an authorize URL,
WITHOUT starting a callback server or binding a port, WITHOUT reading any Client
ID / Client Secret / token, WITHOUT generating any real state / code_verifier /
code_challenge, and WITHOUT any account binding or live/posting behavior.

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
    bound, no authorization code, no token exchange, no token persisted, no
    developer-portal login, no account binding, no posting/metrics/webhook/
    reply/DM/scraping, no generic publisher, no credential-entry schema, no
    OAuth/live execution command.
  * Stores only concise symbolic metadata: OAuth flow family, callback event
    classes, PKCE policy, redaction policy, symbolic dry-run fixtures (fake
    placeholders only), blockers/caveats, and citation URLs (token/id/handle/
    query-free).
"""

import hashlib
import json
import os.path
import re
import sys

TASK_LABEL = (
    "TASK_CONTENTOPS_0174CX_X_OAUTH_CALLBACK_AND_PKCE_DRY_RUN_DESIGN_"
    "NO_SECRET_NO_TOKEN_NO_LIVE_V0"
)

GATE = "X_OAUTH_CALLBACK_PKCE_DRY_RUN_DESIGN_0174CX"
PLATFORM = "x"
SOURCE_BASELINE_COMMIT = "5fabd269f01932e41cba42c0dc49208b963645d4"
INHERITED_0174CW_COMMIT = "5fabd269f01932e41cba42c0dc49208b963645d4"

# Date the official docs were inspected for this task (UTC, no time-of-day).
DOCS_ACCESSED_DATE = "2026-06-16"

NEXT_TASK = (
    "TASK_CONTENTOPS_0174CY_X_OAUTH_REDIRECT_LEDGER_AND_CALLBACK_FIXTURE_"
    "CONTRACT_NO_SECRET_NO_TOKEN_NO_LIVE_V0"
)

# Output artifact locations.
PACKET_REL_DIR = os.path.join("docs", "credential_readiness", "0174CX")
PACKET_FILENAME = "x_oauth_callback_pkce_dry_run_design_packet.json"
README_FILENAME = "README.md"

FLAG_WRITE = "--write-x-oauth-callback-pkce-dry-run-design"

# Symbolic OAuth flow family (no flow initiated).
OAUTH_FLOW_FAMILY_SYMBOLIC = (
    "x.oauth2.authorization_code_with_pkce.user_context.callback "
    "(NOT initiated now)"
)

# Required callback event classes.
CALLBACK_EVENT_CLASSES = [
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

# Redacted callback-log field allow-list (booleans / classes only).
CALLBACK_LOG_ALLOWED_FIELDS = [
    "callback_received",
    "callback_class",
    "state_match_class",
    "code_present_class",
    "denial_or_error_class",
    "timeout_class",
    "replay_detected_class",
    "redaction_verified",
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
    "CALLBACK_SYMBOLIC_DUPLICATE",
    "CALLBACK_SYMBOLIC_TIMEOUT",
    "CHALLENGE_SYMBOLIC_S256_CLASS",
    "VERIFIER_SYMBOLIC_CLASS",
})


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, payload hashes)."""
    if s in (SOURCE_BASELINE_COMMIT, INHERITED_0174CW_COMMIT):
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
                "Reference for the Authorization Code Flow with PKCE: authorize "
                "endpoint params (client_id, redirect_uri, scope, state, "
                "code_challenge, code_challenge_method), callback redirect, and "
                "token exchange. Symbolic only; no flow initiated, no authorize "
                "URL opened, no sample code/state/token stored."
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
                "User access token context: callback returns an authorization "
                "code redeemed for a user access token. No token requested or "
                "stored now; token exchange explicitly out of scope."
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
                "Scope-to-endpoint mapping is least-privilege; state and PKCE "
                "are required for the user-context authorization code flow. No "
                "flow performed."
            ),
        },
        {
            "source_family": "x_developer_portal",
            "title": "X Developer Portal / Console - access tier verification",
            "url_or_symbolic_ref": "https://developer.x.com/en/portal",
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "gated_login_required",
            "notes": (
                "Access-tier, app existence, redirect URI registration, and "
                "auth settings require portal login; treated as a blocker, not "
                "an assumption. No login performed."
            ),
        },
    ]


# --------------------------------------------------------------------------- #
# Symbolic dry-run fixtures (fake placeholders only, no realistic material)
# --------------------------------------------------------------------------- #
def build_symbolic_dry_run_fixtures():
    """Deterministic fake-only callback fixture classes (no real material)."""
    return {
        "success_callback_symbolic": {
            "callback_class": "success_code_present_state_match",
            "state_symbolic": "STATE_SYMBOLIC_MATCH",
            "code_symbolic": "CODE_SYMBOLIC_PRESENT",
            "expected_state_match_class": "match",
            "expected_code_present_class": "present",
            "expected_terminal": True,
        },
        "denied_callback_symbolic": {
            "callback_class": "user_denied_or_declined",
            "error_symbolic": "ERROR_SYMBOLIC_ACCESS_DENIED",
            "expected_denial_or_error_class": "user_denied",
            "expected_terminal": True,
        },
        "missing_state_callback_symbolic": {
            "callback_class": "missing_state",
            "state_symbolic": "STATE_SYMBOLIC_MISSING",
            "code_symbolic": "CODE_SYMBOLIC_PRESENT",
            "expected_state_match_class": "missing",
            "expected_terminal": True,
        },
        "state_mismatch_callback_symbolic": {
            "callback_class": "state_mismatch",
            "state_symbolic": "STATE_SYMBOLIC_MISMATCH",
            "code_symbolic": "CODE_SYMBOLIC_PRESENT",
            "expected_state_match_class": "mismatch",
            "expected_terminal": True,
        },
        "duplicate_callback_symbolic": {
            "callback_class": "duplicate_or_replayed_callback",
            "marker_symbolic": "CALLBACK_SYMBOLIC_DUPLICATE",
            "expected_replay_detected_class": "replay_detected",
            "expected_terminal": True,
        },
        "malformed_callback_symbolic": {
            "callback_class": "malformed_callback",
            "error_symbolic": "ERROR_SYMBOLIC_MALFORMED",
            "expected_denial_or_error_class": "malformed",
            "expected_terminal": True,
        },
        "timeout_callback_symbolic": {
            "callback_class": "timeout_no_callback",
            "marker_symbolic": "CALLBACK_SYMBOLIC_TIMEOUT",
            "expected_timeout_class": "timed_out",
            "expected_terminal": True,
        },
    }


# --------------------------------------------------------------------------- #
# X OAuth callback + PKCE dry-run design packet
# --------------------------------------------------------------------------- #
def build_x_packet():
    """Deep, design-only X OAuth callback + PKCE dry-run policy packet."""
    packet = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "platform": PLATFORM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inherited_0174cw_commit": INHERITED_0174CW_COMMIT,
        "docs_access_status": (
            "partially_accessible: authorization-code-with-pkce, user-access-"
            "token, and authentication overview accessible; developer portal "
            "access/tier gated (login required, not performed)"
        ),
        "official_docs_checked": True,
        "official_docs_sources": build_official_docs_sources(),
        "oauth_flow_family_symbolic": OAUTH_FLOW_FAMILY_SYMBOLIC,
        "callback_pkce_design_status": "design_only_no_real_flow",
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
            "callback result or timeout, and produce only a redacted callback "
            "ledger"
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
            "construction is a separate gate, allowed only after Client ID "
            "handling, redirect URI, state, and PKCE policies are accepted; the "
            "authorize URL is never persisted raw (it can include client_id, "
            "redirect_uri, state, code_challenge)"
        ),
        "redirect_uri_policy": (
            "no real redirect URI registered or tested now; future redirect "
            "URI must be exact-match, deterministic, local-first, and never "
            "logged with its query string"
        ),
        "callback_url_policy": (
            "no real callback URL processed now; future callback handler "
            "redacts the full URL and all query params before any persistence"
        ),
        "callback_query_policy": (
            "future callback handler must redact ALL query parameters before "
            "persistence; raw code, state, error, error_description, and the "
            "raw query string are never logged"
        ),
        "callback_log_policy": (
            "callback logs store only booleans/classes from the allow-list: "
            + ", ".join(CALLBACK_LOG_ALLOWED_FIELDS)
            + "; never raw callback URL, query string, authorization code, "
            "state, or error description"
        ),
        "callback_log_allowed_fields": list(CALLBACK_LOG_ALLOWED_FIELDS),
        "callback_event_classes": list(CALLBACK_EVENT_CLASSES),
        "callback_success_class_policy": (
            "success requires code present AND state match; still terminal and "
            "redacted; success does NOT trigger token exchange in this design"
        ),
        "callback_denial_class_policy": (
            "user denial/decline is a terminal, redacted class; error and "
            "error_description are never logged raw"
        ),
        "callback_error_class_policy": (
            "missing code, missing state, state mismatch, expired/used code, "
            "malformed callback, duplicate/replay, timeout, and unexpected "
            "error are terminal redacted classes; all fail closed"
        ),
        "state_parameter_policy": (
            "future real state must be high-entropy, per-attempt, single-use, "
            "short-lived, and never logged raw; this task generates NO state"
        ),
        "state_validation_policy": (
            "future validation fails closed on missing/mismatch/replay/expired "
            "state; only a state_match_class is recorded"
        ),
        "state_storage_policy": (
            "future state storage is local-only and ephemeral; never committed "
            "or placed in evidence"
        ),
        "pkce_policy": (
            "future PKCE is mandatory for the user-context flow; code_verifier "
            "is high-entropy, per-attempt, single-use, never logged raw; this "
            "task generates NO real PKCE material"
        ),
        "code_verifier_policy": (
            "future code_verifier is high-entropy, per-attempt, single-use, "
            "never logged or persisted raw; not generated now"
        ),
        "code_challenge_policy": (
            "future code_challenge may be recorded ONLY as a redacted/hash "
            "class if strictly necessary; never stored raw; not generated now"
        ),
        "code_challenge_method_policy": (
            "future code_challenge_method should be S256 unless official docs "
            "or future constraints require otherwise; plain is discouraged"
        ),
        "authorization_code_policy": (
            "no authorization code requested, received, or stored now; future "
            "code is single-use, short-lived, never logged raw"
        ),
        "token_exchange_boundary_policy": (
            "token exchange is explicitly OUT OF SCOPE and blocked; this task "
            "calls no token endpoint; future token exchange requires a "
            "separate gate with call budget, no retry, response redaction, "
            "token storage policy, revocation/rotation policy, and operator GO; "
            "no token request/response fixtures with realistic token-like "
            "content are created"
        ),
        "symbolic_dry_run_fixture_policy": (
            "fixtures are deterministic and use fake non-token placeholders "
            "only (e.g. STATE_SYMBOLIC_MATCH, CODE_SYMBOLIC_PRESENT, "
            "ERROR_SYMBOLIC_ACCESS_DENIED); no realistic auth codes, token-"
            "shaped strings, long numeric ids, or raw URLs with query strings"
        ),
        "symbolic_dry_run_fixtures": build_symbolic_dry_run_fixtures(),
        "redaction_policy": (
            "tokens, bearer strings, auth codes, state, code_verifier, "
            "code_challenge, callback URLs with query, and raw query strings "
            "are never logged raw; logs store booleans/classes only"
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
            "allow safe official docs refs (token/id/handle/query-free)",
        ],
        "forbidden_runtime_behaviors": [
            "call X or any platform API",
            "perform OAuth / open authorize URL",
            "open browser or developer portal login",
            "start a callback server or bind a localhost port",
            "listen on localhost",
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
            "redacted callback ledger design accepted",
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
            "credential-readiness gate accepted (no raw token persisted)",
            "account-binding proof uses redacted booleans/classes only",
            "no raw account id/handle persisted; hashed local-only proof only "
            "if explicitly approved later",
        ],
        "required_before_dry_run": [
            "OAuth user-context design accepted",
            "callback + PKCE dry-run design accepted",
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
            "state/PKCE generation+redaction enforcement tests not yet accepted",
            "token response redaction ledger not yet designed",
            "any X plan/access-tier ambiguity is a blocker, not an assumption",
        ])),
        "caveats": [
            "OAuth 2.0 Authorization Code Flow with PKCE (user context) is the "
            "expected family, but NO flow, authorize URL, or callback is "
            "exercised now",
            "token exchange is explicitly out of scope and blocked",
            "developer portal access tier and redirect URI registration remain "
            "unverified (no login)",
            "S256 is the expected code_challenge_method, pending docs/future "
            "constraints",
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
    """Concise operator-facing README for the 0174CX callback+PKCE packet."""
    return (
        "# 0174CX X OAuth Callback and PKCE Dry-Run Design\n"
        "\n"
        "Strictly local, official-doc-grounded, DESIGN-ONLY X OAuth callback + "
        "PKCE dry-run design packet. No OAuth flow, no authorize URL opened, no "
        "callback server started, no localhost port bound, no browser/"
        "developer-portal login, no token exchange, no Client ID/Secret read, "
        "no state/code_verifier/code_challenge generated, no account binding, "
        "no posting.\n"
        "\n"
        "## Inherited posture\n"
        "\n"
        "- Inherits the conservative posture: live posting is "
        "`blocked_until_new_explicit_task_and_operator_go`.\n"
        "- This task only designs the future callback + PKCE dry-run "
        "mechanics; it does not enable any live path.\n"
        "\n"
        "## OAuth flow (symbolic)\n"
        "\n"
        "- Flow family: OAuth 2.0 Authorization Code Flow with PKCE (user "
        "context) callback. Not initiated now.\n"
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
        "## Callback server / browser / authorize URL policy\n"
        "\n"
        "- No server started, no port bound, no browser opened, no authorize "
        "URL constructed now.\n"
        "- Future callback server is local-only, operator-triggered, binds "
        "only an allowlisted localhost interface+port, never logs raw query "
        "strings, and stops after one terminal result or timeout.\n"
        "- Future authorize URL construction is a separate gate (after Client "
        "ID, redirect URI, state, PKCE policies accepted) and is never "
        "persisted raw.\n"
        "\n"
        "## Callback event classes\n"
        "\n"
        "- `success_code_present_state_match`, `user_denied_or_declined`, "
        "`missing_code`, `missing_state`, `state_mismatch`, "
        "`duplicate_or_replayed_callback`, "
        "`expired_or_used_authorization_code`, `malformed_callback`, "
        "`timeout_no_callback`, `unexpected_error_redacted`.\n"
        "- Callback logs store only booleans/classes; never raw URL, query "
        "string, code, state, or error description.\n"
        "\n"
        "## State / PKCE policy\n"
        "\n"
        "- Future state and `code_verifier` must be high-entropy, "
        "per-attempt, single-use, short-lived, never logged raw.\n"
        "- Future `code_challenge` uses S256 and may be recorded only as a "
        "redacted/hash class if necessary.\n"
        "- This task generates NO real state, code_verifier, or "
        "code_challenge.\n"
        "\n"
        "## Symbolic dry-run fixtures\n"
        "\n"
        "- Deterministic fake-only fixtures: success, denied, missing state, "
        "state mismatch, duplicate, malformed, timeout.\n"
        "- Placeholders only (e.g. `STATE_SYMBOLIC_MATCH`, "
        "`CODE_SYMBOLIC_PRESENT`, `ERROR_SYMBOLIC_ACCESS_DENIED`). No "
        "realistic codes, token-shaped strings, long numeric ids, or raw "
        "query URLs.\n"
        "\n"
        "## Token-exchange boundary\n"
        "\n"
        "- Out of scope and blocked. No token endpoint call. Future token "
        "exchange requires a separate gate with call budget, no retry, "
        "response redaction, token storage + revocation/rotation policy, and "
        "operator GO.\n"
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
    """Run the strictly-local 0174CX callback+PKCE design gate. Fail-closed.

    Writing occurs ONLY when ``write=True`` AND the packet passes the redaction
    scan.
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
        "inherited_0174cw_commit": INHERITED_0174CW_COMMIT,
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
        "callback_pkce_design_status": "design_only_no_real_flow",
        "developer_portal_access_status":
            "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "callback_event_classes": list(CALLBACK_EVENT_CLASSES),
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
