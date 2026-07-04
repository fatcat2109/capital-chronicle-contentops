"""X OAuth credential readiness POLICY gate (0174DB).

This module is STRICTLY LOCAL and POLICY-ONLY. It does NOT read, request,
validate, print, hash, inspect, load, persist, or infer any real credential,
token, Client ID, Client Secret, env var, .env file, browser session, account
id, handle, developer portal state, or X API state. It performs NO network of
any kind, opens NO browser, binds NO interface/port, creates NO socket, runs
NO subprocess, and reads NO env / credential / config / secret-store. It only
defines the FUTURE credential-readiness policy contract for supervised X OAuth
readiness.

HARD GUARANTEES (enforced by tests + leakage guards):
  * No network imports (no urllib / requests / httpx / aiohttp / socket /
    http / ssl / env-file loaders).
  * No server imports (no socketserver / http.server / wsgiref / asyncio).
  * No browser/subprocess imports (no webbrowser / subprocess).
  * No credential/secret-source imports (no config-parser / key-ring /
    get-pass / secret-store / browser-cookie tooling).
  * No process-environment or env-file read (no process-env / env-file /
    home-dir access).
  * Imports ONLY hashlib, json, os.path, re, sys.
  * Fail-closed: writes happen ONLY when the write flag is present AND the
    packet passes the redaction scan.
  * Deterministic JSON: sorted keys, compact separators, trailing newline.
  * Does NOT validate credential presence, check X app existence, check
    redirect URI registration, perform OAuth, open an authorize URL, start a
    callback server, exchange tokens, bind an account, or persist any raw
    secret / token value / token hash / token prefix or suffix / account id /
    user id / handle.
  * Stores only concise symbolic policy metadata: credential material
    classification, redacted presence proof rules, secret-source boundaries,
    rotation/revocation requirements, operator GO requirements, required future
    gates, blockers/caveats, and citation URLs (token/id/handle/query-free).

Future credential presence checks require a SEPARATE explicit task and operator
GO. All outputs here are local policy artifacts only.
"""

import hashlib
import json
import os.path
import re
import sys

TASK_LABEL = (
    "TASK_CONTENTOPS_0174DB_X_OAUTH_CREDENTIAL_READINESS_POLICY_GATE_"
    "NO_SECRET_NO_TOKEN_NO_NETWORK_NO_BROWSER_V0"
)

GATE = "X_OAUTH_CREDENTIAL_READINESS_POLICY_GATE_0174DB"
PLATFORM = "x"
SOURCE_BASELINE_COMMIT = "3a3b61f7ed2260d1c69543a2d31efbd23046c332"
INHERITED_0174DA_COMMIT = "3a3b61f7ed2260d1c69543a2d31efbd23046c332"

# Date the official docs were inspected for this task (UTC, no time-of-day).
DOCS_ACCESSED_DATE = "2026-06-16"

NEXT_TASK = (
    "TASK_CONTENTOPS_0174DC_X_OAUTH_REDACTED_CREDENTIAL_PRESENCE_CHECK_DESIGN_"
    "GATE_NO_SECRET_NO_TOKEN_NO_NETWORK_NO_BROWSER_V0"
)

# Output artifact locations.
PACKET_REL_DIR = os.path.join("docs", "credential_readiness", "0174DB")
PACKET_FILENAME = "x_oauth_credential_readiness_policy_packet.json"
README_FILENAME = "README.md"

FLAG_WRITE = "--write-x-oauth-credential-readiness-policy"

ACCEPTED_0174DA_REFERENCE = (
    "docs/credential_readiness/0174DA/"
    "x_oauth_callback_server_policy_packet.json "
    "(gate X_OAUTH_CALLBACK_SERVER_POLICY_GATE_0174DA)"
)

# Symbolic OAuth flow family (no flow initiated; no credential read).
OAUTH_FLOW_FAMILY_SYMBOLIC = (
    "x.oauth2.authorization_code_with_pkce.user_context.credential.readiness."
    "policy (POLICY ONLY; NO credential read, NO token, NO flow initiated)"
)

# Symbolic credential material classes (never real values).
CREDENTIAL_MATERIAL_CLASSES = [
    "client_id_class",
    "client_secret_class",
    "access_token_class",
    "refresh_token_class",
    "bearer_token_class",
    "authorization_code_class",
    "pkce_code_verifier_class",
    "pkce_code_challenge_class",
    "oauth_state_class",
]

# Symbolic redacted presence-proof classes a FUTURE task may emit (not now).
REDACTED_PRESENCE_PROOF_CLASSES = [
    "present_boolean_only_class",
    "absent_boolean_only_class",
    "source_configured_boolean_class",
    "source_missing_boolean_class",
    "no_value_exposed_class",
]


# --------------------------------------------------------------------------- #
# Redaction scanner (defense-in-depth). Extends the 0174DA pattern: blocks
# tokens / bearer strings / raw auth codes / raw state / raw code_verifier /
# raw code_challenge / Client-Secret-shaped values / callback URLs with query /
# raw query strings / raw env assignment patterns / .env-like lines / raw
# handles / long numeric ids / LinkedIn-style URNs / secret hash-fingerprint-
# prefix-suffix claims / forbidden raw keys. Official docs URLs are allowed
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
# Raw env assignment / .env-like line: KEY=VALUE with secret-ish key names.
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
# Secret hash / fingerprint / prefix / suffix EXPOSURE claims (a concrete
# value attached). We allow the policy WORDS in prose but block a value-bearing
# claim like "fingerprint: ab12cd" or "token prefix=AAAA".
_SECRET_FINGERPRINT_CLAIM = re.compile(
    r"(?i)(?:secret|token|client_secret|credential)\s*"
    r"(?:hash|fingerprint|prefix|suffix|sha256|md5)\s*[:=]\s*[A-Za-z0-9+/=_-]{4,}"
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
    "env_value", "dotenv_value",
)

# Safe symbolic placeholders allowed in policy text.
_SAFE_SYMBOLIC_PLACEHOLDERS = frozenset(
    CREDENTIAL_MATERIAL_CLASSES + REDACTED_PRESENCE_PROOF_CLASSES
)

# Keys whose list values are allowed to contain the declared field NAMES.
_SCHEMA_NAME_LIST_KEYS = frozenset({
    "credential_material_classes",
    "redacted_presence_proof_classes",
})


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, payload hashes)."""
    if s in (SOURCE_BASELINE_COMMIT, INHERITED_0174DA_COMMIT):
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
                "defines the future credential-readiness policy and never "
                "reads or validates any credential."
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
                "User access token / refresh token context: token storage, "
                "rotation, and revocation remain policy-only and blocked here."
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
                "this gate records only policy classes/blockers, no values."
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
# X OAuth credential readiness POLICY packet
# --------------------------------------------------------------------------- #
def build_packet():
    """Deep, policy-only X OAuth credential readiness policy packet."""
    packet = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "platform": PLATFORM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inherited_0174da_commit": INHERITED_0174DA_COMMIT,
        "accepted_0174da_reference": ACCEPTED_0174DA_REFERENCE,
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
        "credential_readiness_policy_status":
            "policy_only_no_secret_no_token",
        "client_type_resolution": "unresolved_public_vs_confidential",
        "credential_material_classification_policy": (
            "credential material is classified ONLY by symbolic class (Client "
            "ID, Client Secret, access token, refresh token, bearer token, "
            "authorization code, PKCE verifier/challenge, OAuth state); this "
            "gate never reads, stores, or infers any real value"
        ),
        "credential_material_classes": list(CREDENTIAL_MATERIAL_CLASSES),
        "forbidden_secret_material_policy": (
            "raw secret values, token values, Client Secret, authorization "
            "codes, refresh/bearer/access tokens, and any secret hash / "
            "fingerprint / prefix / suffix are FORBIDDEN in any artifact, log, "
            "commit, or output; only redacted boolean/class proofs are ever "
            "permitted (by a future task)"
        ),
        "redacted_presence_proof_policy": (
            "a FUTURE task may emit redacted presence proofs as boolean/class "
            "only (present/absent/source_configured); this gate emits NO "
            "presence proof and performs NO presence validation now"
        ),
        "redacted_presence_proof_classes": list(REDACTED_PRESENCE_PROOF_CLASSES),
        "future_credential_source_policy": (
            "any future credential source must be operator-controlled and "
            "local-only; this gate reads no source, no env, no .env, no config "
            "file, no keyring, no browser store, and no credential store"
        ),
        "env_dotenv_boundary_policy": (
            "no process-environment read and no .env/dotenv read by this gate "
            "or permitted before a separate explicit presence-check gate and "
            "operator GO"
        ),
        "token_storage_boundary_policy": (
            "no token is stored, cached, serialized, or persisted; future "
            "token storage requires an accepted storage/rotation/revocation "
            "design and operator GO"
        ),
        "token_exchange_boundary_policy": (
            "token exchange remains blocked; no token endpoint call is ever "
            "made by this gate or permitted before a separate token-exchange "
            "gate and operator GO"
        ),
        "client_id_secret_boundary_policy": (
            "no Client ID and no Client Secret is read, validated, printed, "
            "hashed, fingerprinted, or persisted by this gate"
        ),
        "account_binding_boundary_policy": (
            "no X account is bound and no user id / handle is persisted; "
            "account binding requires a separate explicit gate and operator GO"
        ),
        "secret_rotation_revocation_policy": (
            "before any live use, an accepted secret rotation and revocation "
            "plan is required, including revocation on suspected exposure and "
            "scheduled rotation; defined as policy only here"
        ),
        "no_raw_secret_logging_policy": (
            "no raw secret, token, Client Secret, or authorization code is "
            "ever logged, printed, or committed; redacted classes/booleans "
            "only"
        ),
        "no_secret_hashing_policy": (
            "this gate never hashes any real secret or token; no SHA/MD5 or "
            "other digest of credential material is computed or displayed"
        ),
        "no_secret_fingerprint_policy": (
            "this gate never derives or displays any fingerprint, prefix, or "
            "suffix of any real secret or token"
        ),
        "credential_packet_redaction_policy": (
            "the packet is scanned by a fail-closed redaction scanner that "
            "blocks token/bearer/secret-shaped values, env assignments, "
            ".env-like lines, callback URLs with query, raw queries, account/"
            "user/post ids, handles, long numeric ids, secret hash/fingerprint/"
            "prefix/suffix claims, and forbidden raw keys; the packet is "
            "written only if the scan is clean"
        ),
        "explicit_non_actions": [
            "this task does not read Client ID, Client Secret, access token, "
            "refresh token, bearer token, env, .env, config files, browser "
            "sessions, portal state, or credential stores",
            "this task does not validate credential presence",
            "this task does not check X app existence",
            "this task does not check redirect URI registration",
            "this task does not perform OAuth",
            "this task does not open an authorize URL",
            "this task does not start a callback server",
            "this task does not exchange authorization code for token",
            "this task does not bind an X account",
            "this task does not persist raw secret material, token values, "
            "token hashes, token prefixes/suffixes, account ids, user ids, or "
            "handles",
            "future credential presence checks require a separate explicit "
            "task and operator GO",
        ],
        "future_presence_proof_rules": [
            "no raw secret print",
            "no raw secret commit",
            "no secret hash/fingerprint/prefix/suffix exposure",
            "no token response dump",
            "no account identifier persistence",
            "operator-controlled credential source",
            "local-only execution",
            "one-command scoped check",
            "redacted boolean/class outputs only",
            "no platform API call unless a later explicit live-read-only gate "
            "permits it",
            "credential rotation/revocation plan before live",
            "kill switch and duplicate prevention before live",
            "request budget and no retry before live",
            "redacted audit ledger before live",
        ],
        "required_before_real_credential_presence_check": [
            "operator explicit GO for the presence-check gate",
            "operator-controlled local-only credential source defined",
            "redacted boolean/class-only output contract accepted",
            "no-raw-print / no-hash / no-fingerprint enforcement tests accepted",
            "one-command scoped check design accepted",
        ],
        "required_before_token_exchange": [
            "callback server policy accepted (0174DA)",
            "redacted credential presence check accepted (future)",
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
            "redacted credential presence check accepted (future)",
            "account-binding proof uses redacted booleans/classes only",
        ],
        "required_before_text_only_dry_run": [
            "credential readiness policy accepted (0174DB)",
            "redacted credential presence proof accepted (future)",
            "exact payload hash design accepted",
            "no-secret / no-token redaction enforced on dry-run output",
            "operator explicit GO",
        ],
        "required_before_live": [
            "credential-readiness gate accepted",
            "redacted credential presence proof accepted",
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
            "operator-controlled local credential source not yet defined",
            "redacted credential presence-check gate not yet accepted",
            "token response redaction ledger not yet designed",
            "secret rotation/revocation plan not yet accepted",
            "any X plan/access-tier ambiguity is a blocker, not an assumption",
        ])),
        "caveats": [
            "OAuth 2.0 Authorization Code Flow with PKCE (user context) is the "
            "expected family, but NO flow, authorize URL, callback, token, or "
            "credential read is exercised now",
            "this is a policy/spec gate only; no real credential is read, "
            "validated, hashed, fingerprinted, or persisted",
            "token exchange and credential presence validation are explicitly "
            "out of scope and blocked",
            "developer portal access tier and redirect URI registration "
            "remain unverified (no login)",
            "no readiness claim is made; blockers remain open",
        ],
        "recommended_next_task": NEXT_TASK,
        "no_live_call_performed": True,
        "no_network_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_dotenv_read": True,
        "no_client_id_read": True,
        "no_client_secret_read": True,
        "no_access_token_read": True,
        "no_refresh_token_read": True,
        "no_bearer_token_read": True,
        "no_token_exchange_performed": True,
        "no_token_persisted": True,
        "no_secret_material_persisted": True,
        "no_secret_hash_or_fingerprint_created": True,
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
    """Concise operator-facing README for the 0174DB policy packet."""
    return (
        "# 0174DB X OAuth Credential Readiness Policy Gate\n"
        "\n"
        "Strictly local, official-doc-grounded, POLICY-ONLY X OAuth credential "
        "readiness gate. It defines the FUTURE credential-readiness contract "
        "for supervised X OAuth readiness. It does NOT read, request, "
        "validate, print, hash, inspect, load, persist, or infer any real "
        "credential, token, Client ID, Client Secret, env var, .env file, "
        "browser session, account id, handle, developer portal state, or X "
        "API state. No network, no socket, no port bind, no browser, no "
        "authorize URL, no token exchange, no account binding.\n"
        "\n"
        "## Inherited posture\n"
        "\n"
        "- Inherits the conservative posture: live posting is "
        "`blocked_until_new_explicit_task_and_operator_go`.\n"
        "- This task only defines policy; it does not enable any live path, "
        "reads no credential, and makes no readiness claim while blockers "
        "remain.\n"
        "\n"
        "## OAuth flow (symbolic)\n"
        "\n"
        "- Flow family: OAuth 2.0 Authorization Code Flow with PKCE (user "
        "context) credential readiness policy. Not initiated now.\n"
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
        "## Credential material classification (symbolic)\n"
        "\n"
        "- Classes only: Client ID, Client Secret, access/refresh/bearer "
        "token, authorization code, PKCE verifier/challenge, OAuth state.\n"
        "- No real value is read, stored, hashed, fingerprinted, or inferred.\n"
        "\n"
        "## Key policies\n"
        "\n"
        "- Forbidden secret material: no raw value, no hash, no fingerprint, "
        "no prefix/suffix anywhere.\n"
        "- Redacted presence proofs: a FUTURE task may emit boolean/class-only "
        "proofs; this gate emits none and validates nothing.\n"
        "- Credential source: operator-controlled, local-only; no env/.env/"
        "config/keyring/browser store read.\n"
        "- Token storage / exchange / Client ID-Secret / account binding all "
        "remain blocked at this gate.\n"
        "- Secret rotation/revocation, kill switch, duplicate prevention, "
        "request budget, no retry, and redacted audit ledger are required "
        "before live.\n"
        "\n"
        "## What this did NOT do\n"
        "\n"
        "Did not read Client ID/Secret, access/refresh/bearer token, env, "
        ".env, config files, browser sessions, portal state, or credential "
        "stores. Did not validate credential presence. Did not check X app "
        "existence or redirect URI registration. Did not perform OAuth, open "
        "an authorize URL, start a callback server, or exchange a token. Did "
        "not bind an X account. Did not persist raw secret material, token "
        "values, token hashes, token prefixes/suffixes, account ids, user "
        "ids, or handles. Did not post/edit/delete/quote/repost/bookmark/like/"
        "reply/DM, fetch metrics, create a webhook, or scrape. The module "
        "never browses docs at runtime; docs reading was an Antigravity/"
        "operator activity before writing symbolic packet data.\n"
        "\n"
        "## Next\n"
        "\n"
        f"Recommended next task: `{NEXT_TASK}`.\n"
    )


# --------------------------------------------------------------------------- #
# Main gate
# --------------------------------------------------------------------------- #
def run_gate(*, write=False, repo_root=None):
    """Run the strictly-local 0174DB credential readiness policy gate.

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
        "inherited_0174da_commit": INHERITED_0174DA_COMMIT,
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
        "credential_readiness_policy_status":
            "policy_only_no_secret_no_token",
        "developer_portal_access_status":
            "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "credential_material_classes": list(CREDENTIAL_MATERIAL_CLASSES),
        "redacted_presence_proof_classes":
            list(REDACTED_PRESENCE_PROOF_CLASSES),
        "next_recommended_task": NEXT_TASK,
        "no_live_call_performed": True,
        "no_network_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_dotenv_read": True,
        "no_client_id_read": True,
        "no_client_secret_read": True,
        "no_access_token_read": True,
        "no_refresh_token_read": True,
        "no_bearer_token_read": True,
        "no_token_exchange_performed": True,
        "no_token_persisted": True,
        "no_secret_material_persisted": True,
        "no_secret_hash_or_fingerprint_created": True,
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
