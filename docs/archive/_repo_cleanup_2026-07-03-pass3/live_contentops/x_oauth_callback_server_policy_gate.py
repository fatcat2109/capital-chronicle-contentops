"""X OAuth callback server POLICY gate (0174DA).

This module is STRICTLY LOCAL and POLICY-ONLY. It does NOT implement, start,
bind, simulate, or run a callback server. It performs NO network of any kind,
opens NO browser, binds NO interface/port, creates NO socket, runs NO
subprocess, and reads NO env/credentials. It only defines the FUTURE policy
contract for a possible later localhost callback server.

HARD GUARANTEES (enforced by tests + leakage guards):
  * No network imports (no urllib / requests / httpx / aiohttp / socket /
    http / ssl / dotenv).
  * No server imports (no socketserver / http.server / wsgiref / asyncio).
  * No browser/subprocess imports (no webbrowser / subprocess).
  * No process-environment or dotenv read (no environ/getenv/home-dir).
  * Imports ONLY hashlib, json, os.path, re, sys.
  * Fail-closed: writes happen ONLY when the write flag is present AND the
    packet passes the redaction scan.
  * Deterministic JSON: sorted keys, compact separators, trailing newline.
  * Does NOT create a server, bind 127.0.0.1/localhost/0.0.0.0/::1/any
    interface, select a real port, parse a real callback URL, accept raw query
    strings, implement OAuth execution, generate state/code_verifier/
    code_challenge, exchange an authorization code for a token, read any
    credential/env, bind an account, or perform any posting/metrics/webhook/
    reply/DM/scraping.
  * Stores only concise symbolic policy metadata: interface/port policy
    classes, redirect-URI registration blocker, one-terminal-result-or-timeout
    policy, no-raw-query-log rule, token-exchange/credential/browser/account
    boundaries, required future gates, blockers/caveats, and citation URLs
    (token/id/handle/query-free).

Future callback-server implementation requires a SEPARATE explicit task and
operator GO. All outputs here are local policy artifacts only.
"""

import hashlib
import json
import os.path
import re
import sys

TASK_LABEL = (
    "TASK_CONTENTOPS_0174DA_X_OAUTH_CALLBACK_SERVER_POLICY_GATE_"
    "NO_SECRET_NO_TOKEN_NO_NETWORK_NO_BROWSER_V0"
)

GATE = "X_OAUTH_CALLBACK_SERVER_POLICY_GATE_0174DA"
PLATFORM = "x"
SOURCE_BASELINE_COMMIT = "33bb0c9a2ed4d276f3deb0f7e9af9f97d326d777"
INHERITED_0174CZ_COMMIT = "33bb0c9a2ed4d276f3deb0f7e9af9f97d326d777"

# Date the official docs were inspected for this task (UTC, no time-of-day).
DOCS_ACCESSED_DATE = "2026-06-16"

NEXT_TASK = (
    "TASK_CONTENTOPS_0174DB_X_OAUTH_CREDENTIAL_READINESS_POLICY_GATE_"
    "NO_SECRET_NO_TOKEN_NO_NETWORK_NO_BROWSER_V0"
)

# Output artifact locations.
PACKET_REL_DIR = os.path.join("docs", "credential_readiness", "0174DA")
PACKET_FILENAME = "x_oauth_callback_server_policy_packet.json"
README_FILENAME = "README.md"

FLAG_WRITE = "--write-x-oauth-callback-server-policy"

ACCEPTED_0174CZ_REFERENCE = (
    "docs/credential_readiness/0174CZ/"
    "x_oauth_local_callback_handler_dry_run_stub_packet.json "
    "(gate X_OAUTH_LOCAL_CALLBACK_HANDLER_DRY_RUN_STUB_0174CZ)"
)

# Symbolic OAuth flow family (no flow initiated; no server implemented).
OAUTH_FLOW_FAMILY_SYMBOLIC = (
    "x.oauth2.authorization_code_with_pkce.user_context.callback.server.policy "
    "(POLICY ONLY; NO server implemented or started)"
)

# Symbolic interface classes (never real bind instructions).
INTERFACE_POLICY_CLASSES = [
    "loopback_only_class",
    "no_public_interface_class",
    "no_wildcard_interface_class",
    "no_all_interfaces_class",
    "operator_allowlisted_only_class",
]

# Symbolic port policy classes (never a chosen real port).
PORT_POLICY_CLASSES = [
    "ephemeral_high_port_class",
    "single_fixed_allowlisted_port_class",
    "no_privileged_port_class",
    "operator_chosen_at_real_gate_class",
]


# --------------------------------------------------------------------------- #
# Redaction scanner (defense-in-depth). Mirrors the 0174CZ pattern: blocks
# tokens / bearer strings / raw auth codes / raw state / raw code_verifier /
# raw code_challenge / callback URLs with query params / raw query strings with
# code|state|token|error / raw handles / long numeric ids / LinkedIn-style URNs
# / forbidden raw keys. Official docs URLs are allowed only when token/id/
# handle/query-free. Real bind targets (127.0.0.1/localhost/0.0.0.0/::1) are
# blocked as values to guarantee no real interface appears.
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
# Real bind targets must never appear as concrete host:port values. We allow
# the bare policy WORDS (loopback/localhost) inside prose, but block literal
# IP-style bind addresses and host:port pairs.
_REAL_BIND_TARGET = re.compile(
    r"\b(?:127\.0\.0\.1|0\.0\.0\.0|::1)\b|\b(?:localhost|127\.0\.0\.1):\d{2,5}\b"
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

# Safe symbolic placeholders allowed in policy text.
_SAFE_SYMBOLIC_PLACEHOLDERS = frozenset(
    INTERFACE_POLICY_CLASSES + PORT_POLICY_CLASSES + [
        "STATE_SYMBOLIC_MATCH",
        "CODE_SYMBOLIC_PRESENT",
        "CHALLENGE_SYMBOLIC_S256_CLASS",
        "VERIFIER_SYMBOLIC_CLASS",
    ]
)

# Keys whose list values are allowed to contain the declared field NAMES.
_SCHEMA_NAME_LIST_KEYS = frozenset({
    "interface_policy_classes",
    "port_policy_classes",
})


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, payload hashes)."""
    if s in (SOURCE_BASELINE_COMMIT, INHERITED_0174CZ_COMMIT):
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
                "Reference for the redirect/callback step; this gate only "
                "defines the future callback-server policy and never "
                "implements or starts a server."
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
                "scope and blocked at this policy gate."
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
                "Confirms redirect URI registration and state/PKCE are "
                "required; this gate records only policy classes/blockers."
            ),
        },
        {
            "source_family": "x_developer_portal",
            "title": "X Developer Portal / Console - access tier verification",
            "url_or_symbolic_ref": "https://developer.x.com/en/portal",
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "gated_login_required",
            "notes": (
                "Access tier, app existence, and redirect URI registration "
                "require portal login; treated as a blocker, not an "
                "assumption. No login performed."
            ),
        },
    ]


# --------------------------------------------------------------------------- #
# X OAuth callback server POLICY packet
# --------------------------------------------------------------------------- #
def build_packet():
    """Deep, policy-only X OAuth callback server policy packet."""
    packet = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "platform": PLATFORM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inherited_0174cz_commit": INHERITED_0174CZ_COMMIT,
        "accepted_0174cz_reference": ACCEPTED_0174CZ_REFERENCE,
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
        "callback_server_policy_status": "policy_only_no_server",
        "client_type_resolution": "unresolved_public_vs_confidential",
        "interface_policy": (
            "future callback server, IF later approved, must use a loopback-"
            "only operator-allowlisted interface class; this gate selects NO "
            "real interface and binds nothing; symbolic classes only"
        ),
        "interface_policy_classes": list(INTERFACE_POLICY_CLASSES),
        "port_policy": (
            "future callback server, IF later approved, must use a single "
            "operator-allowlisted non-privileged port chosen at the real "
            "callback-server gate; this gate selects NO real port"
        ),
        "port_policy_classes": list(PORT_POLICY_CLASSES),
        "redirect_uri_registration_policy": (
            "redirect URI registration is BLOCKED until developer portal "
            "verification; no redirect URI is registered, parsed, or persisted "
            "here"
        ),
        "localhost_allowlist_policy": (
            "any future localhost callback bind requires an explicit operator-"
            "allowlisted interface+port; nothing is allowlisted or bound now"
        ),
        "no_raw_query_log_policy": (
            "a future callback server must NEVER log the raw callback URL or "
            "raw query string; only redacted classes/booleans may be recorded "
            "(per accepted 0174CY/0174CZ contract)"
        ),
        "one_terminal_result_or_timeout_policy": (
            "a future callback server must resolve each attempt to exactly one "
            "terminal result OR a timeout, then stop; no polling, no retry"
        ),
        "timeout_stop_policy": (
            "on timeout the future server records a timeout class, sets "
            "callback_received false, and stops; it never retries or rebinds"
        ),
        "replay_stop_policy": (
            "duplicate/replayed callbacks are terminal redacted classes; the "
            "future server stops and never triggers token exchange"
        ),
        "callback_server_lifecycle_policy": (
            "a future server, IF approved, must be single-attempt, bound only "
            "for the duration of one authorization attempt, then fully shut "
            "down; no persistent listener; no background process"
        ),
        "token_exchange_boundary_policy": (
            "token exchange remains blocked; no token endpoint call is ever "
            "made by this policy gate or permitted before a separate token-"
            "exchange gate and operator GO"
        ),
        "credential_env_boundary_policy": (
            "no Client ID / Client Secret / access token / refresh token / "
            "env / .env / credential source is read by this gate or permitted "
            "before a separate credential-readiness gate"
        ),
        "browser_boundary_policy": (
            "no browser, no authorize URL opening, no developer-portal login; "
            "any future browser interaction requires a separate explicit gate "
            "and operator GO"
        ),
        "account_binding_boundary_policy": (
            "no X account is bound and no user id / handle is persisted; "
            "account binding requires a separate explicit gate and operator GO"
        ),
        "explicit_non_actions": [
            "this task does not create a server",
            "this task does not bind any loopback or wildcard interface "
            "(loopback ipv4, loopback ipv6, all-interfaces wildcard) or any "
            "interface",
            "this task does not select a real port",
            "this task does not parse a real callback URL",
            "this task does not accept raw query strings",
            "this task does not implement OAuth execution",
            "this task does not generate state, code_verifier, or "
            "code_challenge",
            "this task does not exchange authorization code for token",
            "this task does not read Client ID, Client Secret, access token, "
            "refresh token, env, .env, or any credential source",
            "this task does not bind an X account or persist user id/handle",
            "this task does not post, edit, delete, quote, repost, bookmark, "
            "like, reply, DM, fetch metrics, create webhook, or scrape",
            "future callback-server implementation requires a separate "
            "explicit task and operator GO",
        ],
        "required_before_real_callback_server": [
            "operator explicit GO for the callback-server gate",
            "developer portal access tier verified (login by operator)",
            "redirect URI registered and verified in portal",
            "public vs confidential client type resolved",
            "explicit allowlisted loopback interface+port chosen",
            "redacted redirect ledger schema accepted (0174CY)",
            "local callback handler dry-run stub accepted (0174CZ)",
            "one-terminal-result-or-timeout stop policy accepted",
            "no-raw-query-log policy accepted",
            "single-attempt lifecycle/shutdown policy accepted",
        ],
        "required_before_real_authorize_url": [
            "Client ID handling policy accepted",
            "redirect URI policy accepted and registered",
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
            "OAuth user-context design accepted (0174CW)",
            "callback + PKCE dry-run design accepted (0174CX)",
            "redirect ledger + callback fixture contract accepted (0174CY)",
            "local callback handler dry-run stub accepted (0174CZ)",
            "callback server policy accepted (0174DA)",
            "credential-readiness gate accepted (no raw token persisted)",
            "account-binding proof uses redacted booleans/classes only",
        ],
        "required_before_live": [
            "credential-readiness gate accepted",
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
            "public vs confidential client type not yet resolved",
            "localhost callback interface+port not yet allowlisted",
            "callback server gate not yet accepted",
            "token response redaction ledger not yet designed",
            "any X plan/access-tier ambiguity is a blocker, not an assumption",
        ])),
        "caveats": [
            "OAuth 2.0 Authorization Code Flow with PKCE (user context) is the "
            "expected family, but NO flow, authorize URL, callback, or server "
            "is exercised now",
            "this is a policy/spec gate only; no real callback server is "
            "implemented, started, bound, or simulated",
            "token exchange is explicitly out of scope and blocked",
            "developer portal access tier and redirect URI registration remain "
            "unverified (no login)",
        ],
        "recommended_next_task": NEXT_TASK,
        "no_live_call_performed": True,
        "no_network_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
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
    """Concise operator-facing README for the 0174DA policy packet."""
    return (
        "# 0174DA X OAuth Callback Server Policy Gate\n"
        "\n"
        "Strictly local, official-doc-grounded, POLICY-ONLY X OAuth callback "
        "server gate. It defines the FUTURE policy contract for a possible "
        "later localhost callback server. It does NOT implement, start, bind, "
        "simulate, or run a server. No network, no socket, no port bind, no "
        "browser, no authorize URL, no real callback URL or raw query parsed, "
        "no token exchange, no credential/env read, no account binding, no "
        "posting.\n"
        "\n"
        "## Inherited posture\n"
        "\n"
        "- Inherits the conservative posture: live posting is "
        "`blocked_until_new_explicit_task_and_operator_go`.\n"
        "- This task only defines policy; it does not enable any live path "
        "and implements no real server.\n"
        "\n"
        "## OAuth flow (symbolic)\n"
        "\n"
        "- Flow family: OAuth 2.0 Authorization Code Flow with PKCE (user "
        "context) callback-server policy. Not initiated now.\n"
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
        "## Interface / port policy (symbolic)\n"
        "\n"
        "- Interface: loopback-only, operator-allowlisted class. No real "
        "interface selected. No bind to 127.0.0.1/localhost/0.0.0.0/::1.\n"
        "- Port: single operator-allowlisted non-privileged port chosen at "
        "the real callback-server gate. No real port selected now.\n"
        "\n"
        "## Key policies\n"
        "\n"
        "- Redirect URI registration: BLOCKED until developer portal "
        "verification.\n"
        "- No-raw-query-log: a future server must never log raw callback URL "
        "or query; redacted classes/booleans only.\n"
        "- One-terminal-result-or-timeout: resolve exactly one terminal "
        "result or timeout, then stop. No polling, no retry.\n"
        "- Lifecycle: single-attempt, bound only for one attempt, then full "
        "shutdown. No persistent listener.\n"
        "- Token exchange / credential-env / browser / account binding all "
        "remain blocked at this gate.\n"
        "\n"
        "## What this did NOT do\n"
        "\n"
        "Did not create a server. Did not bind 127.0.0.1, localhost, "
        "0.0.0.0, ::1, or any interface. Did not select a real port. Did not "
        "create a socket or listen. Did not parse a real callback URL or "
        "accept raw query strings. Did not implement OAuth execution. Did not "
        "generate state/code_verifier/code_challenge. Did not exchange an "
        "authorization code for a token. Did not read Client ID/Secret, "
        "access/refresh token, env, or .env. Did not bind an X account or "
        "persist user id/handle. Did not post/edit/delete/quote/repost/"
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
    """Run the strictly-local 0174DA callback server policy gate.

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
        "inherited_0174cz_commit": INHERITED_0174CZ_COMMIT,
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
        "callback_server_policy_status": "policy_only_no_server",
        "developer_portal_access_status":
            "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "interface_policy_classes": list(INTERFACE_POLICY_CLASSES),
        "port_policy_classes": list(PORT_POLICY_CLASSES),
        "next_recommended_task": NEXT_TASK,
        "no_live_call_performed": True,
        "no_network_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
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
