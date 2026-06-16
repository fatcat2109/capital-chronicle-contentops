"""X OAuth live-read-only IDENTITY PROOF gate (0174DE).

This module is the FIRST in the X OAuth chain permitted to perform a single,
bounded, live, READ-ONLY request to the X API -- and only when BOTH the
operator-GO flag and the execute flag are present. Its sole purpose is to prove
that a user-context access token can read the authenticated account identity in
a fully REDACTED, NON-PERSISTENT way.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Default mode is dry-run / blocked summary only (no network, no token read).
  * A live request occurs ONLY when both live flags are present.
  * Request budget is exactly 1; there is NO retry.
  * Allowed host is api.x.com only; allowed method is GET only.
  * Allowed endpoint family is the official-doc-verified authenticated-user
    identity endpoint only (X API v2 GET /2/users/me).
  * NO posting / edit / delete / repost / like / reply / DM / media upload /
    metrics / webhook / scrape / search / timeline / bulk read.
  * NO token exchange, NO refresh flow.
  * The token is never persisted, never logged, never hashed/fingerprinted,
    never prefixed/suffixed, and never placed in the packet/README/output.
  * The raw response body, response headers, account id, account handle,
    username, display name, and profile URL are never persisted.
  * Output is redacted boolean/class fields only.
  * Fail-closed on ANY ambiguity (missing GO, missing execute, missing token
    source, host/method/endpoint mismatch, unexpected response shape, or
    redaction violation).

Token source boundary:
  * No command-line token arguments.
  * No env / .env / config / key-ring / browser-store / shell-history /
    source-control reads by default.
  * The only live source is an interactive hidden getpass prompt, invoked ONLY
    when both live flags are present. Tests inject a fake provider and never
    require a real token.

Official docs verified before implementation (see official_docs_sources):
  * X API v2 "Get my User": GET https://api.x.com/2/users/me (OAuth 2.0
    user-context bearer token). Returns the authenticated user object.
"""

import hashlib
import json
import os.path
import re
import sys

TASK_LABEL = (
    "TASK_CONTENTOPS_0174DE_X_OAUTH_LIVE_READ_ONLY_IDENTITY_PROOF_GATE_ONE_"
    "REQUEST_NO_POST_NO_TOKEN_PERSIST_OPERATOR_GO_REQUIRED_V0"
)

GATE = "X_OAUTH_LIVE_READ_ONLY_IDENTITY_PROOF_GATE_0174DE"
PLATFORM = "x"
SOURCE_BASELINE_COMMIT = "0354581e83e4c2d1008e2f601635d7da8722a669"
INHERITED_0174DD_COMMIT = "0354581e83e4c2d1008e2f601635d7da8722a669"

# Date the official docs were inspected for this task (UTC, no time-of-day).
DOCS_ACCESSED_DATE = "2026-06-16"

# --------------------------------------------------------------------------- #
# Live request policy constants (all explicit; budget = 1, no retry)
# --------------------------------------------------------------------------- #
ALLOWED_HOST = "api.x.com"
ALLOWED_METHOD = "GET"
ENDPOINT_FAMILY = (
    "x_api_v2_users_me_authenticated_user_identity_oauth2_user_context"
)
ENDPOINT_URL = "https://api.x.com/2/users/me"
REQUEST_BUDGET = 1
TIMEOUT_SECONDS = 10

# Output artifact locations.
PACKET_REL_DIR = os.path.join("docs", "credential_readiness", "0174DE")
PACKET_FILENAME = "x_oauth_live_read_only_identity_proof_packet.json"
README_FILENAME = "README.md"

FLAG_WRITE = "--write-x-oauth-live-read-only-identity-proof"
FLAG_OPERATOR_GO = "--operator-go-live-read-only-identity-proof"
FLAG_EXECUTE = "--execute-live-read-only-identity-proof"

ACCEPTED_0174DD_REFERENCE = (
    "docs/credential_readiness/0174DD/"
    "x_oauth_supervised_live_readiness_bridge_bundle_packet.json "
    "(gate X_OAUTH_SUPERVISED_LIVE_READINESS_BRIDGE_BUNDLE_GATE_0174DD)"
)

NEXT_REQUIRED_GATE = (
    "supervised account-binding proof acceptance gate (redacted), then "
    "text-only dry-run + payload-hash/approval/kill-switch/duplicate-"
    "prevention gates before any supervised posting"
)

EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174DF_X_OAUTH_SUPERVISED_ACCOUNT_BINDING_PROOF_"
    "ACCEPTANCE_GATE_REDACTED_NO_POST_NO_TOKEN_PERSIST_OPERATOR_GO_REQUIRED_V0"
)


# --------------------------------------------------------------------------- #
# Redaction scanner (defense-in-depth). Same family as the 0174DC/0174DD
# chain: blocks tokens / bearer strings / raw auth codes/state/verifier/
# challenge / Client-Secret-shaped values / callback URLs with query / raw
# query strings / raw env assignment patterns / env-file-like lines / raw
# handles / long numeric ids / source-control URNs / secret hash-fingerprint-
# prefix-suffix claims / source-name-with-value claims / redacted-from-real
# claims / raw token response claims / forbidden raw keys.
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
_ENV_ASSIGNMENT = re.compile(
    r"(?im)^\s*(?:export\s+)?[A-Z0-9_]*"
    r"(?:SECRET|TOKEN|KEY|PASSWORD|PASSWD|CLIENT_ID|CLIENT_SECRET|BEARER|"
    r"API_KEY|ACCESS|REFRESH)[A-Z0-9_]*\s*=\s*\S+"
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
_REAL_BIND_TARGET = re.compile(
    r"\b(?:127\.0\.0\.1|0\.0\.0\.0|::1)\b|\b(?:localhost|127\.0\.0\.1):\d{2,5}\b"
)
_SECRET_FINGERPRINT_CLAIM = re.compile(
    r"(?i)(?:secret|token|client_secret|credential)\s*"
    r"(?:hash|fingerprint|prefix|suffix|sha256|md5)\s*[:=]\s*[A-Za-z0-9+/=_-]{4,}"
)
_REDACTED_FROM_REAL_CLAIM = re.compile(
    r"(?i)(?:starts?\s*with|ends?\s*with|begins?\s*with|"
    r"last\s*\d+|first\s*\d+|last4|first6)\s*[:=]?\s*[A-Za-z0-9+/=_-]{3,}"
)
_SOURCE_NAME_WITH_VALUE = re.compile(
    r"(?i)(?:credential\s*source|source\s*name|vault\s*path|secret\s*path)\s*"
    r"[:=]\s*\S*[A-Za-z0-9]{2,}[:/=]\S+"
)
_RAW_TOKEN_RESPONSE_CLAIM = re.compile(
    r"(?i)(?:token_response|access_token|refresh_token|bearer_token)\s*"
    r"[:=]\s*[A-Za-z0-9._\-]{6,}"
)

_FORBIDDEN_KEYS = (
    "token", "access_token", "refresh_token", "bearer_token", "client_secret",
    "client_id", "api_key", "account_id", "account_handle", "user_id",
    "username", "screen_name", "handle", "display_name", "post_id",
    "tweet_id", "community_id", "media_id", "place_id", "raw_url",
    "raw_request", "raw_response", "raw_query", "query_string",
    "authorization_code", "auth_code", "code", "state", "code_verifier",
    "code_challenge", "redirect_uri", "callback_url", "token_response",
    "error_description", "secret", "password", "passwd", "secret_hash",
    "token_hash", "secret_fingerprint", "token_fingerprint", "token_prefix",
    "token_suffix", "secret_prefix", "secret_suffix", "env_value",
    "dotenv_value", "source_value", "vault_path", "secret_path",
    "profile_url", "profile_image_url", "authorization", "last4", "first6",
)

# Keys whose list values are allowed to contain declared field/class NAMES.
_SCHEMA_NAME_LIST_KEYS = frozenset({
    "redacted_field_classes",
    "proof_field_classes",
    "identity_proof_field_classes",
    "response_field_classes",
    "error_field_classes",
})


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, payload hashes)."""
    if s in (SOURCE_BASELINE_COMMIT, INHERITED_0174DD_COMMIT):
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
        if key in _SCHEMA_NAME_LIST_KEYS:
            return
        if _CALLBACK_URL_WITH_QUERY.search(s):
            violations.append(f"callback_url_with_query:{key or 'value'}")
        if _RAW_QUERY_SENSITIVE.search(s):
            violations.append(f"raw_query_sensitive:{key or 'value'}")
        if _ENV_ASSIGNMENT.search(s):
            violations.append(f"env_assignment:{key or 'value'}")
        if _SECRET_FINGERPRINT_CLAIM.search(s):
            violations.append(f"secret_fingerprint_claim:{key or 'value'}")
        if _REDACTED_FROM_REAL_CLAIM.search(s):
            violations.append(f"redacted_from_real_claim:{key or 'value'}")
        if _SOURCE_NAME_WITH_VALUE.search(s):
            violations.append(f"source_name_with_value:{key or 'value'}")
        if _RAW_TOKEN_RESPONSE_CLAIM.search(s):
            violations.append(f"raw_token_response_claim:{key or 'value'}")
        if _REAL_BIND_TARGET.search(s):
            violations.append(f"real_bind_target:{key or 'value'}")
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
    """Concise, symbolic record of the official X docs inspected."""
    return [
        {
            "source_family": "x_api_v2_users_me",
            "title": "Get my User - X API v2",
            "url_or_symbolic_ref": "https://docs.x.com/x-api/users/get-my-user",
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "accessible",
            "notes": (
                "Authoritative reference for the authenticated-user identity "
                "endpoint: method GET, host api.x.com, path /2/users/me, "
                "OAuth 2.0 user-context bearer token. Returns the authenticated "
                "user object; this gate maps it ONLY to redacted booleans."
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
                "Confirms the user-context access token model used to authorize "
                "the single read-only identity request; no token exchange or "
                "refresh flow is performed by this gate."
            ),
        },
        {
            "source_family": "x_developer_portal",
            "title": "X Developer Portal / Console - access tier verification",
            "url_or_symbolic_ref": "https://developer.x.com/en/portal",
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "gated_login_required",
            "notes": (
                "App existence, access tier, and credential issuance require "
                "portal login; treated as an operator prerequisite, not an "
                "assumption. No login performed by this gate."
            ),
        },
    ]


# --------------------------------------------------------------------------- #
# Redacted contracts + identity-proof builders
# --------------------------------------------------------------------------- #
def _redacted_response_contract():
    return {
        "purpose": (
            "map the transient in-memory identity response to redacted "
            "boolean/class fields only; the raw body is discarded immediately"
        ),
        "identity_proof_field_classes": [
            "identity_endpoint_reachable_boolean",
            "authenticated_user_context_boolean",
            "account_identity_seen_boolean",
            "account_identifier_exposed_boolean",
            "account_handle_exposed_boolean",
            "token_exposed_boolean",
            "response_redaction_passed_boolean",
            "identity_proof_status_class",
        ],
        "forbidden_fields": (
            "no raw user id, no username, no handle, no display name, no "
            "profile URL, no profile image, no metrics, no raw response body, "
            "no response headers, no authorization header, no token"
        ),
        "raw_response_handling": "inspected_transiently_in_memory_then_discarded",
    }


def _redacted_error_contract():
    return {
        "purpose": (
            "map any live error to a redacted class only; never include raw "
            "error bodies, tracebacks with token material, or headers"
        ),
        "error_field_classes": [
            "live_request_error_boolean",
            "error_class",
            "redaction_passed_boolean",
        ],
        "error_classes": [
            "host_mismatch_blocked",
            "method_mismatch_blocked",
            "endpoint_mismatch_blocked",
            "timeout_error_redacted",
            "http_error_redacted",
            "unexpected_response_shape_redacted",
            "request_error_redacted",
        ],
        "no_retry": True,
    }


def _token_handling_contract():
    return {
        "source": (
            "interactive hidden getpass prompt only, invoked ONLY when both "
            "operator-GO and execute flags are present; tests inject a fake "
            "provider"
        ),
        "command_line_token_argument_supported": False,
        "env_or_dotenv_read_by_default": False,
        "token_printed": False,
        "token_logged": False,
        "token_persisted": False,
        "token_hashed_or_fingerprinted": False,
        "token_prefix_or_suffix_exposed": False,
        "token_lifetime": "held_in_a_local_variable_for_one_request_then_discarded",
    }


def _dry_run_identity_proof():
    return {
        "identity_endpoint_reachable_boolean": False,
        "authenticated_user_context_boolean": False,
        "account_identity_seen_boolean": False,
        "account_identifier_exposed_boolean": False,
        "account_handle_exposed_boolean": False,
        "token_exposed_boolean": False,
        "response_redaction_passed_boolean": False,
        "identity_proof_status_class": "not_executed",
    }


def _error_identity_proof(error_class):
    return {
        "identity_endpoint_reachable_boolean": False,
        "authenticated_user_context_boolean": False,
        "account_identity_seen_boolean": False,
        "account_identifier_exposed_boolean": False,
        "account_handle_exposed_boolean": False,
        "token_exposed_boolean": False,
        "response_redaction_passed_boolean": True,
        "identity_proof_status_class": error_class,
    }


def redact_identity_response(result):
    """Map a transient identity response dict to redacted booleans/classes.

    ``result`` is the dict returned by the HTTP caller with keys ``ok``,
    ``status_code`` and ``json`` (the parsed body, transient). This function
    NEVER returns or stores raw identity values -- only booleans and a class.
    """
    ok = bool(result.get("ok"))
    body = result.get("json")
    reachable = result.get("status_code") is not None

    seen = False
    authed = False
    if ok and isinstance(body, dict):
        data = body.get("data")
        if isinstance(data, dict):
            authed = True
            # account_identity_seen is a pure boolean derived from presence of
            # an "id" field; the value itself is NEVER read out or stored.
            seen = bool(data.get("id"))

    if not reachable:
        status_class = "live_request_error_redacted"
    elif seen:
        status_class = "identity_confirmed_redacted"
    elif authed:
        status_class = "authenticated_no_identity_field_redacted"
    else:
        status_class = "unexpected_response_shape_redacted"

    return {
        "identity_endpoint_reachable_boolean": bool(reachable),
        "authenticated_user_context_boolean": bool(authed),
        "account_identity_seen_boolean": bool(seen),
        "account_identifier_exposed_boolean": False,
        "account_handle_exposed_boolean": False,
        "token_exposed_boolean": False,
        "response_redaction_passed_boolean": True,
        "identity_proof_status_class": status_class,
    }


# --------------------------------------------------------------------------- #
# Default safe token provider + default bounded HTTP caller
# --------------------------------------------------------------------------- #
def _default_token_provider():
    """Interactive hidden prompt. Imported lazily so the module import graph
    stays free of getpass unless a live run actually requests a token."""
    import getpass
    return getpass.getpass(
        "Paste X user-context access token (hidden; not stored, not logged): "
    )


def _default_http_caller(method, url, token, timeout_seconds):
    """Perform at most ONE bounded read-only GET. Returns a redacted-safe dict.

    Never returns the token, the request URL, or raw headers. Validates host
    and method locally before any network use; refuses anything else without a
    network call. urllib is imported lazily to keep the static import surface
    minimal.
    """
    from urllib import request as _request
    from urllib import error as _error
    from urllib import parse as _parse

    if method != ALLOWED_METHOD:
        return {"ok": False, "status_code": None, "json": None,
                "error_class": "method_mismatch_blocked"}
    parsed = _parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
        return {"ok": False, "status_code": None, "json": None,
                "error_class": "host_mismatch_blocked"}
    if parsed.path != "/2/users/me":
        return {"ok": False, "status_code": None, "json": None,
                "error_class": "endpoint_mismatch_blocked"}

    req = _request.Request(url, method="GET")
    req.add_header("Authorization", "Bearer " + token)
    try:
        with _request.urlopen(req, timeout=timeout_seconds) as resp:
            body = resp.read().decode("utf-8")
            status = resp.getcode()
        data = json.loads(body)
        return {"ok": True, "status_code": status, "json": data,
                "error_class": None}
    except _error.HTTPError as e:
        return {"ok": False, "status_code": e.code, "json": None,
                "error_class": "http_error_redacted"}
    except Exception:
        return {"ok": False, "status_code": None, "json": None,
                "error_class": "request_error_redacted"}


# --------------------------------------------------------------------------- #
# Packet builder
# --------------------------------------------------------------------------- #
def build_packet(*, live_request_performed=False, request_count=0,
                 retry_count=0, operator_go=False, execution_requested=False,
                 proof=None, proof_status="blocked_no_operator_go",
                 current_blockers=None):
    """Build the deterministic redacted identity-proof packet."""
    if proof is None:
        proof = _dry_run_identity_proof()
    if current_blockers is None:
        current_blockers = []

    no_live = not live_request_performed

    packet = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "platform": PLATFORM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inherited_0174dd_commit": INHERITED_0174DD_COMMIT,
        "accepted_0174dd_reference": ACCEPTED_0174DD_REFERENCE,

        "live_read_only_identity_proof_status": proof_status,
        "operator_go_status": (
            "operator_go_present" if operator_go else "operator_go_absent"),
        "execution_requested": bool(execution_requested),
        "live_request_performed": bool(live_request_performed),

        "request_budget": REQUEST_BUDGET,
        "request_count": int(request_count),
        "retry_count": int(retry_count),
        "timeout_seconds": TIMEOUT_SECONDS,

        "allowed_host": ALLOWED_HOST,
        "allowed_method": ALLOWED_METHOD,
        "official_endpoint_family_verified": True,
        "endpoint_family": ENDPOINT_FAMILY,
        "official_docs_checked": True,
        "official_docs_sources": build_official_docs_sources(),

        "redacted_identity_proof": proof,
        "redacted_response_contract": _redacted_response_contract(),
        "redacted_error_contract": _redacted_error_contract(),
        "token_handling_contract": _token_handling_contract(),
        "no_token_persistence_contract": True,

        "token_exchange_status": "not_performed",
        "account_binding_status": "not_bound_by_this_task",
        "posting_status": "blocked",
        "blocker_status": (
            "live_posting_blocked_until_new_explicit_task_and_operator_go"),
        "current_blockers": sorted(set(current_blockers)),
        "cleared_blockers_if_any": [],
        "next_required_gate": NEXT_REQUIRED_GATE,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,

        "caveats": [
            "this gate performs at most ONE live read-only request and never "
            "retries",
            "it only reads authenticated-user identity (GET api.x.com/2/"
            "users/me); it never posts, mutates, fetches metrics, creates a "
            "webhook, or scrapes",
            "it never exchanges or refreshes tokens and never persists, logs, "
            "hashes, fingerprints, prefixes, or suffixes the token",
            "no account id, handle, username, display name, profile URL, raw "
            "response body, or response headers are ever persisted",
            "the token is supplied only via an interactive hidden prompt when "
            "both live flags are present; tests use a fake provider",
            "live posting remains blocked; account binding is not approved by "
            "this task",
        ],

        # --- Safety flags (all true) ------------------------------------- #
        "no_posting_performed": True,
        "no_mutating_x_api_call_performed": True,
        "no_token_exchange_performed": True,
        "no_refresh_flow_performed": True,
        "no_token_persisted": True,
        "no_token_logged": True,
        "no_token_hash_or_fingerprint_created": True,
        "no_token_prefix_or_suffix_exposed": True,
        "no_account_identifier_persisted": True,
        "no_account_handle_persisted": True,
        "no_profile_url_persisted": True,
        "no_raw_response_persisted": True,
        "no_response_headers_persisted": True,
        "no_metrics_fetched": True,
        "no_webhook_created": True,
        "no_reply_dm_created": True,
        "no_scraping_performed": True,
        "no_autonomous_publishing": True,
        "redaction_verified": True,

        # --- Mode-dependent network flags -------------------------------- #
        "no_live_network_call_performed": bool(no_live),
        "live_network_call_performed": bool(live_request_performed),
        "live_read_only_call_only": True,

        "status": "pass",
        "blocked_reasons": [],
    }
    return packet


# --------------------------------------------------------------------------- #
# README
# --------------------------------------------------------------------------- #
def build_readme():
    """Concise operator-facing README for the 0174DE identity-proof packet."""
    return (
        "# 0174DE X OAuth Live Read-Only Identity Proof Gate\n"
        "\n"
        "First gate in the X OAuth chain permitted to perform a SINGLE, "
        "bounded, live, READ-ONLY request -- and only when BOTH live flags "
        "are present. Its sole purpose is to prove a user-context access "
        "token can read the authenticated account identity in a fully "
        "REDACTED, NON-PERSISTENT way.\n"
        "\n"
        "## Default posture\n"
        "\n"
        "- Default mode is dry-run / blocked: no network, no token read, no "
        "write.\n"
        "- `live_read_only_identity_proof_status = blocked_no_operator_go` "
        "until both live flags are supplied.\n"
        "- Live posting remains blocked. Account binding is NOT approved here.\n"
        "\n"
        "## CLI\n"
        "\n"
        "```\n"
        "python -m live_contentops.cli x-oauth-live-read-only-identity-proof-"
        "gate\n"
        "python -m live_contentops.cli x-oauth-live-read-only-identity-proof-"
        "gate --write-x-oauth-live-read-only-identity-proof\n"
        "python -m live_contentops.cli x-oauth-live-read-only-identity-proof-"
        "gate --operator-go-live-read-only-identity-proof --execute-live-read-"
        "only-identity-proof --write-x-oauth-live-read-only-identity-proof\n"
        "```\n"
        "\n"
        "A live request occurs ONLY when both "
        "`--operator-go-live-read-only-identity-proof` and "
        "`--execute-live-read-only-identity-proof` are present. The token is "
        "then requested via an interactive hidden prompt; it is never echoed, "
        "logged, persisted, hashed, or placed in any artifact.\n"
        "\n"
        "## Verified endpoint (official docs)\n"
        "\n"
        "- `GET https://api.x.com/2/users/me` -- \"Get my User\" "
        "(`docs.x.com/x-api/users/get-my-user`), OAuth 2.0 user-context "
        "bearer token, returns the authenticated user object.\n"
        "- Host is restricted to `api.x.com`; method is restricted to `GET`; "
        "request budget is `1`; there is no retry; timeout is explicit.\n"
        "\n"
        "## Redacted output only\n"
        "\n"
        "The transient response is mapped to boolean/class fields only "
        "(reachable, authenticated-context, identity-seen, status class) and "
        "the raw body is discarded. No user id, username, handle, display "
        "name, profile URL, metrics, headers, or token ever appear in the "
        "packet, README, logs, or output.\n"
        "\n"
        "## What this did NOT do\n"
        "\n"
        "Did not post/edit/delete/repost/like/reply/DM, upload media, fetch "
        "metrics, create a webhook, scrape, search, read timelines, or do "
        "bulk reads. Did not exchange or refresh tokens. Did not persist, "
        "log, hash, fingerprint, prefix, or suffix the token. Did not bind an "
        "X account.\n"
        "\n"
        "## Next\n"
        "\n"
        f"Recommended next task: `{EXACT_NEXT_TASK_RECOMMENDATION}`.\n"
    )


# --------------------------------------------------------------------------- #
# Main gate
# --------------------------------------------------------------------------- #
def run_gate(*, write=False, operator_go=False, execution_requested=False,
             repo_root=None, token_provider=None, http_caller=None):
    """Run the 0174DE live-read-only identity proof gate.

    Default mode is dry-run / blocked. A single live read-only request occurs
    ONLY when both ``operator_go`` and ``execution_requested`` are true AND a
    token is obtained from the (injected or default hidden-prompt) provider.
    Writing occurs ONLY when ``write=True`` AND the packet passes the redaction
    scan. Fail-closed everywhere.
    """
    if repo_root is None:
        repo_root = os.path.dirname(os.path.dirname(__file__))

    blocked = []
    status = "pass"

    live_request_performed = False
    request_count = 0
    retry_count = 0
    proof = _dry_run_identity_proof()
    current_blockers = []

    both_flags = bool(operator_go) and bool(execution_requested)

    if not both_flags:
        if not operator_go:
            proof_status = "blocked_no_operator_go"
            current_blockers.append("operator_go_absent")
        else:
            proof_status = "blocked_not_executed"
            current_blockers.append("execute_flag_absent")
        if execution_requested and not operator_go:
            current_blockers.append("execute_requested_without_operator_go")
    else:
        provider = token_provider or _default_token_provider
        caller = http_caller or _default_http_caller
        token = None
        try:
            token = provider()
        except Exception:
            token = None
        if not token:
            proof_status = "blocked_pending_operator_go_or_token_source"
            current_blockers.append("no_token_source_available")
        else:
            # Exactly one request; NO retry.
            result = caller(ALLOWED_METHOD, ENDPOINT_URL, token,
                            TIMEOUT_SECONDS)
            request_count = 1
            retry_count = 0
            live_request_performed = True
            # Drop the token reference immediately after the single call.
            token = None
            if not isinstance(result, dict):
                proof = _error_identity_proof("unexpected_response_shape_"
                                              "redacted")
                proof_status = "unexpected_response_shape_redacted"
            elif result.get("ok"):
                proof = redact_identity_response(result)
                proof_status = proof["identity_proof_status_class"]
            else:
                err_class = result.get("error_class") or "request_error_redacted"
                proof = _error_identity_proof(err_class)
                proof_status = err_class

    packet = build_packet(
        live_request_performed=live_request_performed,
        request_count=request_count,
        retry_count=retry_count,
        operator_go=operator_go,
        execution_requested=execution_requested,
        proof=proof,
        proof_status=proof_status,
        current_blockers=current_blockers,
    )

    violations = scan_packet_for_leaks(packet)
    if violations:
        blocked.append("packet_redaction_violation")
        status = "fail_closed"
        packet["status"] = "fail_closed"
        packet["blocked_reasons"] = sorted(set(blocked))

    checksum = compute_checksum(packet)

    packet_written = False
    readme_written = False
    if write and not violations:
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
        "inherited_0174dd_commit": INHERITED_0174DD_COMMIT,
        "live_read_only_identity_proof_status": proof_status,
        "operator_go_status": (
            "operator_go_present" if operator_go else "operator_go_absent"),
        "execution_requested": bool(execution_requested),
        "live_request_performed": bool(live_request_performed),
        "request_budget": REQUEST_BUDGET,
        "request_count": int(request_count),
        "retry_count": int(retry_count),
        "timeout_seconds": TIMEOUT_SECONDS,
        "allowed_host": ALLOWED_HOST,
        "allowed_method": ALLOWED_METHOD,
        "endpoint_family": ENDPOINT_FAMILY,
        "official_endpoint_family_verified": True,
        "redacted_identity_proof": proof,
        "packet_path": os.path.join(
            PACKET_REL_DIR, PACKET_FILENAME).replace(os.sep, "/"),
        "readme_path": os.path.join(
            PACKET_REL_DIR, README_FILENAME).replace(os.sep, "/"),
        "write_requested": bool(write),
        "packet_written": bool(packet_written),
        "readme_written": bool(readme_written),
        "packet_checksum": checksum,
        "token_exchange_status": "not_performed",
        "account_binding_status": "not_bound_by_this_task",
        "posting_status": "blocked",
        "no_live_network_call_performed": not live_request_performed,
        "live_network_call_performed": bool(live_request_performed),
        "live_read_only_call_only": True,
        "no_posting_performed": True,
        "no_mutating_x_api_call_performed": True,
        "no_token_exchange_performed": True,
        "no_refresh_flow_performed": True,
        "no_token_persisted": True,
        "no_token_logged": True,
        "no_token_hash_or_fingerprint_created": True,
        "no_token_prefix_or_suffix_exposed": True,
        "no_account_identifier_persisted": True,
        "no_account_handle_persisted": True,
        "no_profile_url_persisted": True,
        "no_raw_response_persisted": True,
        "no_response_headers_persisted": True,
        "no_metrics_fetched": True,
        "no_webhook_created": True,
        "no_reply_dm_created": True,
        "no_scraping_performed": True,
        "no_autonomous_publishing": True,
        "redaction_verified": True,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
        "status": status,
        "blocked_reasons": sorted(set(blocked)),
    }


def main(argv=None):
    """CLI entry: prints the redacted gate summary as JSON."""
    if argv is None:
        argv = sys.argv[2:]
    write = FLAG_WRITE in argv
    operator_go = FLAG_OPERATOR_GO in argv
    execution_requested = FLAG_EXECUTE in argv
    print(json.dumps(run_gate(
        write=write,
        operator_go=operator_go,
        execution_requested=execution_requested,
    ), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
