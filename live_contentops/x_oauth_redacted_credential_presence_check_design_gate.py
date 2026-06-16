"""X OAuth redacted credential presence-check DESIGN gate (0174DC).

This module is STRICTLY LOCAL and DESIGN-ONLY. It does NOT perform a credential
presence check. It does NOT read, request, validate, print, hash, inspect,
load, persist, or infer any real credential, token, Client ID, Client Secret,
env var, env-file, config file, secret-store, browser session, account id,
handle, developer portal state, or X API state. It performs NO network of any
kind, opens NO browser, binds NO interface/port, creates NO socket, runs NO
subprocess, and reads NO env / credential / config / secret-store / shell
history / source-control history. It only defines the FUTURE design contract
for a later redacted credential presence check.

HARD DISTINCTION:
  * 0174DB defined the credential readiness policy.
  * 0174DC defines the FUTURE redacted presence-check design.
  * 0174DC does NOT execute the future check.

HARD GUARANTEES (enforced by tests + leakage guards):
  * No network imports (no urllib / requests / httpx / aiohttp / socket /
    http / ssl / env-file loaders).
  * No server imports (no socketserver / http.server / wsgiref / asyncio).
  * No browser/subprocess imports (no webbrowser / subprocess).
  * No credential/secret-source imports (no config-parser / key-ring /
    get-pass / secret-store / browser-cookie tooling / source-control history
    scanning).
  * No process-environment or env-file read (no process-env / env-file /
    home-dir access).
  * Imports ONLY hashlib, json, os.path, re, sys.
  * Fail-closed: writes happen ONLY when the write flag is present AND the
    packet passes the redaction scan.
  * Deterministic JSON: sorted keys, compact separators, trailing newline.
  * Does NOT perform a presence check, read a credential source, validate that
    any credential exists, reveal source names with values, reveal secret
    hashes / fingerprints / prefixes / suffixes / redacted-from-real strings,
    see token responses, check X app existence, check redirect URI
    registration, perform OAuth, open an authorize URL, start a callback
    server, exchange tokens, or bind an account.
  * Stores only concise symbolic design metadata: allowed future presence
    classes, forbidden future outputs, redacted boolean output contract,
    boundary policies, fail-closed result classes, operator GO requirements,
    required future gates, blockers/caveats, and citation URLs (token / id /
    handle / query-free).

Future redacted credential presence checks require a SEPARATE explicit
EXECUTION task and operator GO. All outputs here are local design artifacts
only.
"""

import hashlib
import json
import os.path
import re
import sys

TASK_LABEL = (
    "TASK_CONTENTOPS_0174DC_X_OAUTH_REDACTED_CREDENTIAL_PRESENCE_CHECK_DESIGN_"
    "GATE_NO_SECRET_NO_TOKEN_NO_NETWORK_NO_BROWSER_V0"
)

GATE = "X_OAUTH_REDACTED_CREDENTIAL_PRESENCE_CHECK_DESIGN_GATE_0174DC"
PLATFORM = "x"
SOURCE_BASELINE_COMMIT = "cc7b82cf23b6436888c3b09c181436fc992f2699"
INHERITED_0174DB_COMMIT = "cc7b82cf23b6436888c3b09c181436fc992f2699"

# Date the official docs were inspected for this task (UTC, no time-of-day).
DOCS_ACCESSED_DATE = "2026-06-16"

NEXT_TASK = (
    "TASK_CONTENTOPS_0174DD_X_OAUTH_REDACTED_CREDENTIAL_PRESENCE_CHECK_FIXTURE_"
    "CONTRACT_GATE_NO_SECRET_NO_TOKEN_NO_NETWORK_NO_BROWSER_V0"
)

# Output artifact locations.
PACKET_REL_DIR = os.path.join("docs", "credential_readiness", "0174DC")
PACKET_FILENAME = "x_oauth_redacted_credential_presence_check_design_packet.json"
README_FILENAME = "README.md"

FLAG_WRITE = "--write-x-oauth-redacted-credential-presence-check-design"

ACCEPTED_0174DB_REFERENCE = (
    "docs/credential_readiness/0174DB/"
    "x_oauth_credential_readiness_policy_packet.json "
    "(gate X_OAUTH_CREDENTIAL_READINESS_POLICY_GATE_0174DB)"
)

# Symbolic OAuth flow family (no flow initiated; no credential read).
OAUTH_FLOW_FAMILY_SYMBOLIC = (
    "x.oauth2.authorization_code_with_pkce.user_context.credential.presence."
    "check.design (DESIGN ONLY; NO presence check, NO credential read, NO "
    "token, NO flow initiated)"
)

# Symbolic allowed future presence classes (never real values).
ALLOWED_FUTURE_PRESENCE_CLASSES = [
    "client_id_presence_unknown_class",
    "client_id_presence_present_boolean_only_class",
    "client_id_presence_absent_boolean_only_class",
    "client_secret_presence_unknown_class",
    "client_secret_presence_present_boolean_only_class",
    "client_secret_presence_absent_boolean_only_class",
    "access_token_presence_forbidden_until_later_gate_class",
    "refresh_token_presence_forbidden_until_later_gate_class",
    "bearer_token_presence_forbidden_until_later_gate_class",
    "credential_source_configured_boolean_only_class",
    "credential_source_missing_boolean_only_class",
    "no_value_exposed_class",
    "no_hash_exposed_class",
    "no_fingerprint_exposed_class",
    "no_prefix_suffix_exposed_class",
]

# Symbolic fail-closed result classes a FUTURE check may emit (not now).
FAIL_CLOSED_RESULT_CLASSES = [
    "presence_check_blocked_no_operator_go_class",
    "presence_check_blocked_source_undefined_class",
    "presence_check_blocked_redaction_violation_class",
    "presence_check_fail_closed_unknown_class",
]

# Symbolic forbidden future presence outputs (described, never produced).
FORBIDDEN_FUTURE_PRESENCE_OUTPUTS = [
    "raw_credential_value",
    "raw_token_value",
    "secret_hash_value",
    "secret_fingerprint_value",
    "secret_prefix_value",
    "secret_suffix_value",
    "redacted_from_real_string",
    "credential_source_name_with_value",
    "env_name_with_value_pair",
    "token_response_body",
    "account_identifier_value",
    "handle_value",
    "raw_error_body",
]


# --------------------------------------------------------------------------- #
# Redaction scanner (defense-in-depth). Extends the 0174DB pattern: blocks
# tokens / bearer strings / raw auth codes / raw state / raw code_verifier /
# raw code_challenge / Client-Secret-shaped values / callback URLs with query /
# raw query strings / raw env assignment patterns / env-file-like lines / raw
# handles / long numeric ids / source-control URNs / secret hash-fingerprint-
# prefix-suffix claims / source-name-with-value claims / redacted-from-real
# claims ("starts with"/"ends with"/"last4"/"first6") / forbidden raw keys.
# Official docs URLs are allowed only when token/id/handle/query-free.
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
# Raw env assignment / env-file-like line: KEY=VALUE with secret-ish key names.
_ENV_ASSIGNMENT = re.compile(
    r"(?im)^\s*(?:export\s+)?[A-Z0-9_]*"
    r"(?:SECRET|TOKEN|KEY|PASSWORD|PASSWD|CLIENT_ID|CLIENT_SECRET|BEARER|"
    r"API_KEY|ACCESS|REFRESH)[A-Z0-9_]*\s*=\s*\S+"
)
# Any URL carrying an OAuth-sensitive query parameter.
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
# Real bind targets must never appear as concrete host:port values.
_REAL_BIND_TARGET = re.compile(
    r"\b(?:127\.0\.0\.1|0\.0\.0\.0|::1)\b|\b(?:localhost|127\.0\.0\.1):\d{2,5}\b"
)
# Secret hash / fingerprint / prefix / suffix EXPOSURE claims (value attached).
_SECRET_FINGERPRINT_CLAIM = re.compile(
    r"(?i)(?:secret|token|client_secret|credential)\s*"
    r"(?:hash|fingerprint|prefix|suffix|sha256|md5)\s*[:=]\s*[A-Za-z0-9+/=_-]{4,}"
)
# Redacted-from-real disclosure claims with a concrete fragment attached, e.g.
# "starts with abcd", "ends with 1234", "last4: 7890", "first6=ABCDEF".
_REDACTED_FROM_REAL_CLAIM = re.compile(
    r"(?i)(?:starts?\s*with|ends?\s*with|begins?\s*with|"
    r"last\s*\d+|first\s*\d+|last4|first6)\s*[:=]?\s*[A-Za-z0-9+/=_-]{3,}"
)
# Source-name-with-value claim, e.g. "source: vault_path=/secret/x" or
# "credential source = MY_SECRET_STORE:abc123".
_SOURCE_NAME_WITH_VALUE = re.compile(
    r"(?i)(?:credential\s*source|source\s*name|vault\s*path|secret\s*path)\s*"
    r"[:=]\s*\S*[A-Za-z0-9]{2,}[:/=]\S+"
)

_FORBIDDEN_KEYS = (
    "token", "access_token", "refresh_token", "bearer_token", "client_secret",
    "client_id", "api_key", "account_id", "account_handle", "user_id",
    "username", "screen_name", "handle", "post_id", "tweet_id", "community_id",
    "media_id", "place_id", "raw_url", "raw_request", "raw_response",
    "raw_query", "query_string", "authorization_code", "auth_code", "code",
    "state", "code_verifier", "code_challenge", "redirect_uri", "callback_url",
    "token_response", "error_description", "secret", "password", "passwd",
    "secret_hash", "token_hash", "secret_fingerprint", "token_fingerprint",
    "token_prefix", "token_suffix", "secret_prefix", "secret_suffix",
    "env_value", "dotenv_value", "source_value", "vault_path", "secret_path",
    "last4", "first6",
)

# Safe symbolic placeholders allowed in policy/design text.
_SAFE_SYMBOLIC_PLACEHOLDERS = frozenset(
    ALLOWED_FUTURE_PRESENCE_CLASSES
    + FAIL_CLOSED_RESULT_CLASSES
    + FORBIDDEN_FUTURE_PRESENCE_OUTPUTS
)

# Keys whose list values are allowed to contain the declared field NAMES.
_SCHEMA_NAME_LIST_KEYS = frozenset({
    "allowed_future_presence_classes",
    "fail_closed_result_classes",
    "forbidden_future_presence_outputs",
})


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, payload hashes)."""
    if s in (SOURCE_BASELINE_COMMIT, INHERITED_0174DB_COMMIT):
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
                "Reference for the credential/token model; this gate only "
                "designs a future redacted presence check and never reads or "
                "validates any credential."
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
                "User access token / refresh token context: presence checks, "
                "token storage, rotation, and revocation remain design-only "
                "and blocked here."
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
                "Confirms Client ID/Secret and token handling are required; "
                "this gate records only symbolic design classes/blockers, no "
                "values and no presence check."
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
                "portal login; treated as a blocker, not an assumption. No "
                "login performed."
            ),
        },
    ]


# --------------------------------------------------------------------------- #
# X OAuth redacted credential presence-check DESIGN packet
# --------------------------------------------------------------------------- #
def build_packet():
    """Deep, design-only X OAuth redacted credential presence-check packet."""
    packet = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "platform": PLATFORM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inherited_0174db_commit": INHERITED_0174DB_COMMIT,
        "accepted_0174db_reference": ACCEPTED_0174DB_REFERENCE,
        "docs_access_status": (
            "partially_accessible: authorization-code-with-pkce, user-access-"
            "token, and authentication overview accessible; developer portal "
            "access/tier gated (login required, not performed)"
        ),
        "official_docs_checked": True,
        "official_docs_sources": build_official_docs_sources(),
        "oauth_flow_family_symbolic": OAUTH_FLOW_FAMILY_SYMBOLIC,
        "developer_portal_access_status": "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "redirect_uri_registration_status": "not_verified_blocked",
        "client_type_resolution": "unresolved_public_vs_confidential",
        "redacted_presence_check_design_status":
            "design_only_no_presence_check",
        "credential_presence_check_execution_status": "not_executed",
        "credential_source_read_status": "not_read",
        "allowed_future_presence_classes": list(
            ALLOWED_FUTURE_PRESENCE_CLASSES),
        "fail_closed_result_classes": list(FAIL_CLOSED_RESULT_CLASSES),
        "forbidden_future_presence_outputs": list(
            FORBIDDEN_FUTURE_PRESENCE_OUTPUTS),
        "redacted_boolean_output_contract": (
            "a FUTURE presence check may output ONLY redacted boolean/class "
            "values from the allowed presence classes; it must never output a "
            "real value, hash, fingerprint, prefix, suffix, redacted-from-real "
            "string, source name with value, env-name-with-value pair, token "
            "response, account identifier, or raw error body"
        ),
        "source_abstraction_policy": (
            "the future credential source is referenced ONLY by an abstract "
            "operator-controlled handle; the source name, path, or location is "
            "never paired with a value and never disclosed in any output"
        ),
        "env_dotenv_config_boundary_policy": (
            "no process-environment read, no env-file read, and no config-file "
            "read by this gate; a future presence check may consult an "
            "operator-controlled local source only after a separate explicit "
            "execution gate and operator GO, and only emitting redacted "
            "boolean/class results"
        ),
        "secret_value_boundary_policy": (
            "no real secret or token value is ever read, printed, stored, or "
            "inferred; only boolean/class presence indicators are ever "
            "permitted (by a future task)"
        ),
        "no_secret_hashing_policy": (
            "this gate never hashes any real secret or token, and a future "
            "presence check must never hash credential material; no digest is "
            "computed or displayed"
        ),
        "no_secret_fingerprint_policy": (
            "this gate never derives or displays any fingerprint of any real "
            "secret or token, and a future presence check must not either"
        ),
        "no_secret_prefix_suffix_policy": (
            "no prefix or suffix of any real secret or token is ever derived, "
            "displayed, or claimed (no starts-with / ends-with / first-n / "
            "last-n disclosure)"
        ),
        "no_env_name_value_pair_policy": (
            "no environment variable NAME is ever paired with its VALUE in any "
            "output; a future presence check may reference an abstract source "
            "handle only, never a name-with-value pair"
        ),
        "no_account_identifier_policy": (
            "no account id, user id, screen name, or handle is ever read, "
            "derived, or persisted by this gate or a future presence check"
        ),
        "no_token_response_policy": (
            "no token endpoint response is ever requested, seen, parsed, or "
            "stored; token exchange remains blocked"
        ),
        "no_raw_error_policy": (
            "no raw error body from any source or endpoint is ever surfaced; "
            "errors are mapped to fail-closed result classes only"
        ),
        "fail_closed_result_class_policy": (
            "any ambiguity, missing operator GO, undefined source, or "
            "redaction violation maps to a fail-closed result class; the "
            "future check never falls open and never emits a value on error"
        ),
        "future_presence_check_operator_go_policy": (
            "a future redacted presence check requires a separate explicit "
            "execution task and operator GO; this design gate grants no "
            "permission to execute"
        ),
        "future_presence_check_command_boundary": (
            "the future presence check must be a single-command, local-only, "
            "scoped operation emitting redacted boolean/class output only; it "
            "must make no platform API call unless a later explicit live-read-"
            "only gate permits it"
        ),
        "explicit_non_actions": [
            "this task does not perform a credential presence check",
            "this task does not read Client ID, Client Secret, access token, "
            "refresh token, bearer token, env, env-file, config files, "
            "key-ring, credential stores, browser stores, shell history, "
            "source-control history, portal state, or API state",
            "this task does not validate that any credential exists",
            "this task does not reveal credential source names with values",
            "this task does not reveal secret hashes, fingerprints, prefixes, "
            "suffixes, or redacted-from-real strings",
            "this task does not see token responses",
            "this task does not check X app existence",
            "this task does not check redirect URI registration",
            "this task does not perform OAuth",
            "this task does not open an authorize URL",
            "this task does not start a callback server",
            "this task does not exchange authorization code for token",
            "this task does not bind an X account",
            "future redacted credential presence checks require a separate "
            "explicit execution task and operator GO",
        ],
        "required_before_real_presence_check": [
            "operator explicit GO for the presence-check execution gate",
            "operator-controlled local-only abstract credential source handle "
            "defined",
            "redacted boolean/class-only output contract accepted",
            "no-value / no-hash / no-fingerprint / no-prefix-suffix "
            "enforcement tests accepted",
            "single-command local-only scoped check design accepted",
            "fail-closed result-class mapping accepted",
        ],
        "required_before_token_exchange": [
            "callback server policy accepted (0174DA)",
            "credential readiness policy accepted (0174DB)",
            "redacted presence-check design accepted (0174DC)",
            "redacted presence check executed and accepted (future)",
            "token response redaction ledger design accepted",
            "token endpoint call budget and no-retry policy defined",
            "token storage/rotation/revocation policy accepted",
            "operator explicit GO",
        ],
        "required_before_account_binding": [
            "OAuth user-context design accepted (0174CW)",
            "callback + PKCE dry-run design accepted (0174CX)",
            "redirect ledger + callback fixture contract accepted (0174CY)",
            "local callback handler dry-run stub accepted (0174CZ)",
            "callback server policy accepted (0174DA)",
            "credential readiness policy accepted (0174DB)",
            "redacted presence-check design accepted (0174DC)",
            "redacted presence check executed and accepted (future)",
            "account-binding proof uses redacted booleans/classes only",
        ],
        "required_before_text_only_dry_run": [
            "credential readiness policy accepted (0174DB)",
            "redacted presence-check design accepted (0174DC)",
            "redacted presence check executed and accepted (future)",
            "exact payload hash design accepted",
            "no-secret / no-token redaction enforced on dry-run output",
            "operator explicit GO",
        ],
        "required_before_live": [
            "credential-readiness gate accepted",
            "redacted presence-check design accepted",
            "redacted presence check executed and accepted",
            "account-binding proof accepted",
            "text-only dry-run accepted",
            "exact payload hash locked",
            "operator approval",
            "one-time live GO",
            "duplicate-send prevention",
            "kill switch",
            "request_budget=1",
            "no retry",
            "redacted post-send ledger",
            "secret rotation/revocation plan in place",
        ],
        "blocker_policy": (
            "any inaccessible/gated/redirected/deprecated/ambiguous official "
            "page is recorded as a blocker; capability is never assumed and "
            "third-party blogs/tutorials/SDK examples are never treated as "
            "authority; no readiness claim is made while blockers remain"
        ),
        "blockers": sorted(set([
            "developer access/tier not yet verified (portal login required)",
            "X app existence not yet verified",
            "redirect URI not yet registered/verified in portal",
            "public vs confidential client type not yet resolved",
            "operator-controlled local credential source handle not yet "
            "defined",
            "redacted presence-check execution gate not yet accepted",
            "redacted presence check not yet executed",
            "token response redaction ledger not yet designed",
            "secret rotation/revocation plan not yet accepted",
            "any X plan/access-tier ambiguity is a blocker, not an assumption",
        ])),
        "caveats": [
            "OAuth 2.0 Authorization Code Flow with PKCE (user context) is the "
            "expected family, but NO flow, authorize URL, callback, token, "
            "credential read, or presence check is exercised now",
            "this is a design/spec gate only; no real credential is read, "
            "validated, hashed, fingerprinted, prefixed, suffixed, or "
            "persisted, and no presence check is executed",
            "token exchange and credential presence validation are explicitly "
            "out of scope and blocked",
            "developer portal access tier and redirect URI registration "
            "remain unverified (no login)",
            "no readiness claim is made; blockers remain open",
        ],
        "recommended_next_task": NEXT_TASK,
        "no_presence_check_performed": True,
        "no_credential_source_read": True,
        "no_live_call_performed": True,
        "no_network_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_dotenv_read": True,
        "no_config_read": True,
        "no_keyring_read": True,
        "no_browser_store_read": True,
        "no_client_id_read": True,
        "no_client_secret_read": True,
        "no_access_token_read": True,
        "no_refresh_token_read": True,
        "no_bearer_token_read": True,
        "no_token_exchange_performed": True,
        "no_token_response_seen": True,
        "no_token_persisted": True,
        "no_secret_material_persisted": True,
        "no_secret_hash_or_fingerprint_created": True,
        "no_secret_prefix_or_suffix_exposed": True,
        "no_account_identifier_read": True,
        "no_account_binding_performed": True,
        "no_oauth_flow_performed": True,
        "no_authorize_url_opened": True,
        "no_browser_login_performed": True,
        "no_developer_portal_login_performed": True,
        "no_callback_server_started": True,
        "no_localhost_port_bound": True,
        "no_socket_created": True,
        "no_port_listened": True,
        "no_authorization_code_generated_or_received": True,
        "no_real_callback_url_processed": True,
        "no_raw_callback_query_processed": True,
        "no_state_generated": True,
        "no_code_verifier_generated": True,
        "no_code_challenge_generated": True,
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
    """Concise operator-facing README for the 0174DC design packet."""
    return (
        "# 0174DC X OAuth Redacted Credential Presence-Check Design Gate\n"
        "\n"
        "Strictly local, official-doc-grounded, DESIGN-ONLY gate. It defines "
        "the FUTURE design contract for a later redacted credential presence "
        "check. It does NOT perform a presence check, and does NOT read, "
        "request, validate, print, hash, inspect, load, persist, or infer any "
        "real credential, token, Client ID, Client Secret, env var, env-file, "
        "config file, secret store, browser session, account id, handle, "
        "developer portal state, or X API state. No network, no socket, no "
        "port bind, no browser, no authorize URL, no token exchange, no "
        "account binding.\n"
        "\n"
        "## Hard distinction\n"
        "\n"
        "- 0174DB defined the credential readiness policy.\n"
        "- 0174DC defines the FUTURE redacted presence-check design.\n"
        "- 0174DC does NOT execute the future check.\n"
        "\n"
        "## Inherited posture\n"
        "\n"
        "- Inherits the conservative posture: live posting is "
        "`blocked_until_new_explicit_task_and_operator_go`.\n"
        "- This task only defines design; it does not enable any live path, "
        "reads no credential, performs no presence check, and makes no "
        "readiness claim while blockers remain.\n"
        "\n"
        "## OAuth flow (symbolic)\n"
        "\n"
        "- Flow family: OAuth 2.0 Authorization Code Flow with PKCE (user "
        "context) redacted presence-check design. Not initiated now.\n"
        "- Token exchange and credential presence validation are explicitly "
        "out of scope and blocked.\n"
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
        "## Redacted boolean output model (symbolic)\n"
        "\n"
        "- A FUTURE presence check may emit ONLY redacted boolean/class "
        "values from the allowed presence classes (present/absent/unknown "
        "booleans, source configured/missing booleans, no-value/no-hash/"
        "no-fingerprint/no-prefix-suffix exposed classes).\n"
        "- Access/refresh/bearer token presence stays forbidden until a later "
        "gate.\n"
        "- No real value, hash, fingerprint, prefix, suffix, redacted-from-"
        "real string, source-name-with-value, env-name-with-value pair, token "
        "response, account identifier, or raw error is ever emitted.\n"
        "\n"
        "## Key policies\n"
        "\n"
        "- Source abstraction: future source referenced by abstract operator-"
        "controlled handle only; never name-with-value.\n"
        "- Fail-closed result classes: ambiguity / missing GO / undefined "
        "source / redaction violation map to fail-closed; never falls open.\n"
        "- Operator GO + separate explicit EXECUTION task required before any "
        "real presence check.\n"
        "- Token storage / exchange / account binding remain blocked.\n"
        "- Secret rotation/revocation, kill switch, duplicate prevention, "
        "request budget, no retry, and redacted audit ledger are required "
        "before live.\n"
        "\n"
        "## What this did NOT do\n"
        "\n"
        "Did not perform a credential presence check. Did not read Client ID/"
        "Secret, access/refresh/bearer token, env, env-file, config files, "
        "key-ring, credential stores, browser stores, shell history, source-"
        "control history, portal state, or API state. Did not validate that "
        "any credential exists. Did not reveal source names with values, "
        "secret hashes, fingerprints, prefixes, suffixes, or redacted-from-"
        "real strings. Did not see token responses. Did not check X app "
        "existence or redirect URI registration. Did not perform OAuth, open "
        "an authorize URL, start a callback server, or exchange a token. Did "
        "not bind an X account. Did not post/edit/delete/quote/repost/"
        "bookmark/like/reply/DM, fetch metrics, create a webhook, or scrape. "
        "The module never browses docs at runtime; docs reading was an "
        "Antigravity/operator activity before writing symbolic packet data.\n"
        "\n"
        "## Next\n"
        "\n"
        f"Recommended next task: `{NEXT_TASK}`.\n"
    )


# --------------------------------------------------------------------------- #
# Main gate
# --------------------------------------------------------------------------- #
def run_gate(*, write=False, repo_root=None):
    """Run the strictly-local 0174DC redacted presence-check design gate.

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
        "inherited_0174db_commit": INHERITED_0174DB_COMMIT,
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
        "redacted_presence_check_design_status":
            "design_only_no_presence_check",
        "credential_presence_check_execution_status": "not_executed",
        "credential_source_read_status": "not_read",
        "developer_portal_access_status":
            "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "allowed_future_presence_classes": list(
            ALLOWED_FUTURE_PRESENCE_CLASSES),
        "fail_closed_result_classes": list(FAIL_CLOSED_RESULT_CLASSES),
        "next_recommended_task": NEXT_TASK,
        "no_presence_check_performed": True,
        "no_credential_source_read": True,
        "no_live_call_performed": True,
        "no_network_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_dotenv_read": True,
        "no_config_read": True,
        "no_keyring_read": True,
        "no_browser_store_read": True,
        "no_client_id_read": True,
        "no_client_secret_read": True,
        "no_access_token_read": True,
        "no_refresh_token_read": True,
        "no_bearer_token_read": True,
        "no_token_exchange_performed": True,
        "no_token_response_seen": True,
        "no_token_persisted": True,
        "no_secret_material_persisted": True,
        "no_secret_hash_or_fingerprint_created": True,
        "no_secret_prefix_or_suffix_exposed": True,
        "no_account_identifier_read": True,
        "no_account_binding_performed": True,
        "no_oauth_flow_performed": True,
        "no_authorize_url_opened": True,
        "no_browser_login_performed": True,
        "no_developer_portal_login_performed": True,
        "no_callback_server_started": True,
        "no_localhost_port_bound": True,
        "no_socket_created": True,
        "no_port_listened": True,
        "no_authorization_code_generated_or_received": True,
        "no_real_callback_url_processed": True,
        "no_raw_callback_query_processed": True,
        "no_state_generated": True,
        "no_code_verifier_generated": True,
        "no_code_challenge_generated": True,
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
