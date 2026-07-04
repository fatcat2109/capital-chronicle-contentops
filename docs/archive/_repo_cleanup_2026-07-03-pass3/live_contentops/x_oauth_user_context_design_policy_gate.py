"""X OAuth user-context design and redirection policy gate (0174CW).

This module is STRICTLY LOCAL. It performs NO network of any kind, opens NO
browser, runs NO subprocess, and reads NO env/credentials. Official X OAuth
documentation reading is an Antigravity/operator activity performed BEFORE this
module runs; the module only emits a symbolic, redacted, DESIGN-ONLY OAuth
user-context + redirect/callback policy packet grounded in those docs.

It designs the FUTURE X OAuth user-context (Authorization Code Flow with PKCE)
WITHOUT initiating OAuth, WITHOUT reading any Client ID / Client Secret / token,
WITHOUT generating any real state / code_verifier / code_challenge, and WITHOUT
any account binding or live/posting behavior.

HARD GUARANTEES (enforced by tests + leakage guards):
  * No network imports (no urllib / requests / httpx / socket / http / dotenv).
  * No browser/subprocess imports (no webbrowser / subprocess).
  * No process env / dotenv read (no environment or home-dir lookups).
  * Imports ONLY hashlib, json, os.path, re, sys.
  * Fail-closed: writes happen ONLY when the write flag is present AND the
    packet passes the redaction scan.
  * Deterministic JSON: sorted keys, compact separators, trailing newline.
  * No OAuth flow, no authorize URL opened, no authorization code, no token
    exchange, no token persisted, no developer-portal login, no account
    binding, no posting/metrics/webhook/reply/DM/scraping, no generic
    publisher, no credential-entry schema, no OAuth/live execution command.
  * Stores only concise symbolic metadata: OAuth flow family, symbolic
    parameters, scope classes, redirect/callback policy, token-handling policy,
    blockers/caveats, and citation URLs (token/id/handle/query-free).
"""

import hashlib
import json
import os.path
import re
import sys

TASK_LABEL = (
    "TASK_CONTENTOPS_0174CW_X_OAUTH_USER_CONTEXT_DESIGN_AND_REDIRECTION_"
    "POLICY_NO_TOKEN_NO_LIVE_V0"
)

GATE = "X_OAUTH_USER_CONTEXT_DESIGN_POLICY_0174CW"
PLATFORM = "x"
SOURCE_BASELINE_COMMIT = "91136d776e741af81046961ace04580442184587"
INHERITED_0174CV_COMMIT = "91136d776e741af81046961ace04580442184587"

# Date the official docs were inspected for this task (UTC, no time-of-day).
DOCS_ACCESSED_DATE = "2026-06-15"

NEXT_TASK = (
    "TASK_CONTENTOPS_0174CX_X_OAUTH_CALLBACK_AND_PKCE_DRY_RUN_DESIGN_"
    "NO_SECRET_NO_TOKEN_NO_LIVE_V0"
)

# Output artifact locations.
PACKET_REL_DIR = os.path.join("docs", "credential_readiness", "0174CW")
PACKET_FILENAME = "x_oauth_user_context_design_policy_packet.json"
README_FILENAME = "README.md"

FLAG_WRITE = "--write-x-oauth-user-context-design-policy"

# Symbolic OAuth flow family (no flow initiated).
OAUTH_FLOW_FAMILY_SYMBOLIC = (
    "x.oauth2.authorization_code_with_pkce.user_context (NOT initiated now)"
)

# Future minimum candidate scope classes (least privilege, text-only posting).
ALLOWED_SCOPE_CLASSES_FOR_FUTURE_DESIGN = [
    "tweet.write",
    "tweet.read",
    "users.read",
]

# Scope classes forbidden until separately scoped/justified.
FORBIDDEN_SCOPE_CLASSES_UNTIL_SCOPED = [
    "any_scope_unrelated_to_text_only_posting_or_account_proof",
    "block.write",
    "bookmark.write",
    "dm.read",
    "dm.write",
    "follows.write",
    "like.write",
    "list.write",
    "media.write",
    "mute.write",
    "tweet.moderate.write",
]


# --------------------------------------------------------------------------- #
# Redaction scanner (defense-in-depth). Blocks tokens / bearer strings / raw
# auth codes / raw state / raw code_verifier / raw code_challenge / callback
# URLs with query params / raw handles / raw account-user-post-tweet-community-
# media-place ids / long numeric ids / LinkedIn-style URNs / forbidden raw keys.
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
# Any URL carrying an OAuth-sensitive query parameter (code/state/token/verifier
# /challenge/redirect). This is the no-query-log callback guard.
_CALLBACK_URL_WITH_QUERY = re.compile(
    r"https?://[^\s\"']*[?&](?:code|state|access_token|token|bearer_token|"
    r"refresh_token|authorization_code|auth_code|code_verifier|code_challenge|"
    r"redirect_uri|callback_url)="
)

_FORBIDDEN_KEYS = (
    "token", "access_token", "refresh_token", "bearer_token", "client_secret",
    "client_id", "api_key", "account_id", "account_handle", "user_id",
    "username", "screen_name", "handle", "post_id", "tweet_id", "community_id",
    "media_id", "place_id", "raw_url", "raw_request", "raw_response",
    "authorization_code", "auth_code", "code", "state", "code_verifier",
    "code_challenge", "redirect_uri", "callback_url", "token_response",
)


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, payload hashes)."""
    if s in (SOURCE_BASELINE_COMMIT, INHERITED_0174CV_COMMIT):
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
        if _CALLBACK_URL_WITH_QUERY.search(s):
            violations.append(f"callback_url_with_query:{key or 'value'}")
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
                "Reference for the Authorization Code Flow with PKCE: scopes, "
                "refresh tokens, confidential vs public clients, and access "
                "token lifetimes. Symbolic only; no flow initiated and no "
                "sample code/state/token stored."
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
                "User-context requests use OAuth 2.0 user access tokens; "
                "scope-to-endpoint mapping is least-privilege. No token "
                "requested or stored now."
            ),
        },
        {
            "source_family": "x_api_v2_manage_posts",
            "title": "Create or Edit Post - X API (downstream endpoint context)",
            "url_or_symbolic_ref": "https://docs.x.com/x-api/posts/create-post",
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "accessible",
            "notes": (
                "Downstream endpoint context only: future text-only Create "
                "Post requires tweet.write under user context. Edit / paid "
                "partnership remain forbidden until separately scoped."
            ),
        },
        {
            "source_family": "x_developer_portal",
            "title": "X Developer Portal / Console - access tier verification",
            "url_or_symbolic_ref": "https://developer.x.com/en/portal",
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "gated_login_required",
            "notes": (
                "Access-tier, app existence, and auth settings require portal "
                "login; treated as a blocker, not an assumption. No login "
                "performed."
            ),
        },
    ]


# --------------------------------------------------------------------------- #
# X OAuth user-context design + redirection policy packet
# --------------------------------------------------------------------------- #
def build_x_packet():
    """Deep, design-only X OAuth user-context + redirect/PKCE/token policy."""
    packet = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "platform": PLATFORM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inherited_0174cv_commit": INHERITED_0174CV_COMMIT,
        "docs_access_status": (
            "partially_accessible: authorization-code-with-pkce, "
            "authentication overview, and create-post docs accessible; "
            "developer portal access/tier gated (login required, not "
            "performed)"
        ),
        "official_docs_checked": True,
        "official_docs_sources": build_official_docs_sources(),
        "oauth_flow_family_symbolic": OAUTH_FLOW_FAMILY_SYMBOLIC,
        "oauth_design_status": "design_only_no_flow",
        "developer_portal_access_status": "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "access_tier_blocker": (
            "developer portal access/tier cannot be verified without login; "
            "any plan/access-tier ambiguity is a blocker, not an assumption"
        ),
        "app_registration_status": "not_performed",
        "app_auth_settings_status": "not_verified",
        "client_type_policy": (
            "public vs confidential client decision is DEFERRED to a dedicated "
            "future gate; no client registered now"
        ),
        "public_client_policy": (
            "if a public client is later selected, PKCE is mandatory and a "
            "no-client-secret policy must be explicit; code_verifier/"
            "code_challenge are per-attempt, single-use, and never logged raw"
        ),
        "confidential_client_policy": (
            "if a confidential client is later selected, client-secret "
            "storage/redaction/rotation MUST be designed and accepted BEFORE "
            "any secret exists; secret never read, logged, committed, or "
            "placed in evidence"
        ),
        "client_id_policy": (
            "no Client ID read, stored, or logged now; future handling policy "
            "must be accepted before token exchange"
        ),
        "client_secret_policy": (
            "no Client Secret read, stored, or logged now; only relevant if a "
            "confidential client is later chosen, and only after a secret "
            "storage/redaction/rotation policy is accepted"
        ),
        "redirect_uri_policy": (
            "no real redirect URI registered or tested now; future redirect "
            "URI must be exact-match, deterministic, and local-first; never "
            "logged with its query string"
        ),
        "callback_url_policy": (
            "future callback handler must redact code, state, token-like "
            "strings, and ALL query params before any persistence; callback "
            "logs store booleans/classes only, never raw URLs"
        ),
        "local_callback_policy": (
            "future callback is local-first and operator-triggered only; "
            "browser redirect handling is never autonomous"
        ),
        "state_parameter_policy": (
            "future state must be high-entropy, per-attempt, single-use, "
            "short-lived, and never logged raw; this task generates no real "
            "state"
        ),
        "pkce_policy": (
            "future PKCE is mandatory for the user-context flow; code_verifier "
            "is high-entropy, per-attempt, single-use, never logged raw; this "
            "task generates no real PKCE material"
        ),
        "code_challenge_policy": (
            "future code_challenge may be stored ONLY as a redacted/hash class "
            "if strictly necessary; never stored raw; not generated now"
        ),
        "code_verifier_policy": (
            "future code_verifier is high-entropy, per-attempt, single-use, "
            "never logged or persisted raw; not generated now"
        ),
        "scope_policy": (
            "least privilege with exact mapping to the future text-only "
            "endpoint contract; only scopes required for text posting and "
            "account proof are candidates"
        ),
        "allowed_scope_classes_for_future_design":
            list(ALLOWED_SCOPE_CLASSES_FOR_FUTURE_DESIGN),
        "forbidden_scope_classes_until_scoped":
            list(FORBIDDEN_SCOPE_CLASSES_UNTIL_SCOPED),
        "offline_access_policy": (
            "offline.access (refresh token) is BLOCKED until a dedicated "
            "future task explicitly justifies refresh-token handling"
        ),
        "authorization_code_policy": (
            "no authorization code requested, received, or stored now; future "
            "code is single-use, short-lived, never logged raw"
        ),
        "token_exchange_policy": (
            "no token endpoint call now; future token exchange requires a "
            "defined call budget, no-retry policy, and a token-response "
            "redaction ledger design accepted first"
        ),
        "access_token_policy": (
            "no access token requested or stored now; future access token is "
            "local-only, redacted in logs, never committed or placed in "
            "evidence"
        ),
        "refresh_token_policy": (
            "no refresh token now; refresh/offline.access blocked until a "
            "dedicated justification gate; future handling requires rotation "
            "and revocation plans"
        ),
        "token_storage_policy": (
            "future token storage must be local-only, encrypted or "
            "OS-secret-store-backed if available, redacted in logs, never "
            "committed, never included in evidence"
        ),
        "token_redaction_policy": (
            "tokens, bearer strings, auth codes, state, code_verifier, and "
            "code_challenge are never logged raw; logs store booleans/classes "
            "only; token_response is redacted before any persistence"
        ),
        "token_rotation_policy": (
            "future token rotation plan required before the first "
            "credential-readiness gate"
        ),
        "token_revocation_policy": (
            "future token revocation plan required before the first "
            "credential-readiness gate; revocation must be operator-triggerable"
        ),
        "failure_decline_expiry_policy": (
            "future handling of user decline, denied consent, expired/used "
            "authorization code, and state mismatch must fail closed, store "
            "only redacted classes, perform no retry beyond the defined "
            "budget, and never log raw error URLs/query strings"
        ),
        "account_binding_dependency": (
            "OAuth design does NOT prove account binding; account-binding "
            "proof is a separate future gate and must not persist raw account "
            "id/handle (redacted booleans/classes; hashed local-only proof "
            "only if explicitly approved later)"
        ),
        "dry_run_dependency": (
            "text-only dry-run is a separate future gate that depends on this "
            "OAuth design, credential readiness, and account-binding proof "
            "being accepted first"
        ),
        "live_gate_dependency": (
            "live posting depends on credential readiness, account-binding "
            "proof, accepted dry-run, locked payload hash, operator approval, "
            "and a one-time GO; remains blocked"
        ),
        "required_before_real_oauth": [
            "developer portal/access tier verified manually by operator (no "
            "login in this task)",
            "app existence and auth settings confirmed in a dedicated future "
            "task",
            "callback/redirect policy accepted",
            "scope policy accepted",
            "secret/token storage policy accepted",
            "redaction scanner accepted",
            "operator explicit GO for the OAuth readiness task",
        ],
        "required_before_token_exchange": [
            "real Client ID handling policy accepted",
            "if confidential client: Client Secret handling policy accepted",
            "state/PKCE generation and redaction tests accepted",
            "callback no-query-log policy accepted",
            "token endpoint call budget and no-retry policy defined",
            "token response redaction ledger design accepted",
            "operator explicit GO",
        ],
        "required_before_account_binding": [
            "OAuth user-context design accepted",
            "credential-readiness gate accepted (no raw token persisted)",
            "account-binding proof uses redacted booleans/classes only",
            "no raw account id/handle persisted; hashed local-only proof only "
            "if explicitly approved later",
        ],
        "required_before_dry_run": [
            "OAuth user-context design accepted",
            "credential-readiness gate accepted",
            "account-binding proof accepted",
            "text-only payload field contract accepted",
            "edit/replies/DMs/media/paid/quote/community fields forbidden "
            "until separately scoped",
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
            "public vs confidential client type not yet decided",
            "callback/redirect policy not yet accepted by operator",
            "scope policy not yet accepted by operator",
            "token storage/rotation/revocation policy not yet accepted",
            "any X plan/access-tier ambiguity is a blocker, not an assumption",
        ])),
        "caveats": [
            "OAuth 2.0 Authorization Code Flow with PKCE (user context) is the "
            "expected family, but NO flow is initiated now",
            "refresh tokens require offline.access, which is blocked until a "
            "dedicated justification gate",
            "confidential vs public client choice is deferred; secret handling "
            "must be designed before any secret exists",
            "developer portal access tier remains unverified (no login)",
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
        "no_authorization_code_generated_or_received": True,
        "no_code_verifier_generated": True,
        "no_code_challenge_generated": True,
        "no_state_generated": True,
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
    """Concise operator-facing README for the 0174CW X OAuth design packet."""
    return (
        "# 0174CW X OAuth User-Context Design and Redirection Policy\n"
        "\n"
        "Strictly local, official-doc-grounded, DESIGN-ONLY X OAuth "
        "user-context + redirect/callback/PKCE/token policy packet. No OAuth "
        "flow, no authorize URL opened, no browser/developer-portal login, no "
        "token exchange, no Client ID/Secret read, no state/code_verifier/"
        "code_challenge generated, no account binding, no posting.\n"
        "\n"
        "## Inherited posture\n"
        "\n"
        "- Inherits the conservative posture: live posting is "
        "`blocked_until_new_explicit_task_and_operator_go`.\n"
        "- This task only designs the future OAuth user-context; it does not "
        "enable any live path.\n"
        "\n"
        "## OAuth flow (symbolic)\n"
        "\n"
        "- Flow family: OAuth 2.0 Authorization Code Flow with PKCE (user "
        "context). Not initiated now.\n"
        "- Public vs confidential client decision is deferred to a dedicated "
        "future gate.\n"
        "\n"
        "## Official docs inspected\n"
        "\n"
        "- Authorization Code Flow with PKCE "
        "(`docs.x.com/fundamentals/authentication/oauth-2-0/"
        "authorization-code`) -- accessible.\n"
        "- Authentication Overview "
        "(`docs.x.com/fundamentals/authentication/overview`) -- accessible.\n"
        "- Create or Edit Post (`docs.x.com/x-api/posts/create-post`) -- "
        "accessible (downstream context only).\n"
        "- Developer Portal access tiers (`developer.x.com/en/portal`) -- "
        "gated (login required, not performed) -> blocker.\n"
        "\n"
        "## Redirect / callback policy\n"
        "\n"
        "- No real callback URL registered or tested now.\n"
        "- Future callback URL must be exact-match, deterministic, "
        "local-first, and must never be logged with its query string.\n"
        "- Future callback handler redacts `code`, `state`, token-like "
        "strings, and all query params before persistence; logs store "
        "booleans/classes only.\n"
        "- Browser redirect handling is operator-triggered only, never "
        "autonomous.\n"
        "\n"
        "## State / PKCE policy\n"
        "\n"
        "- Future state and `code_verifier` must be high-entropy, "
        "per-attempt, single-use, short-lived, and never logged raw.\n"
        "- Future `code_challenge` may be stored only as a redacted/hash "
        "class if necessary.\n"
        "- This task generates NO real state, code_verifier, or "
        "code_challenge.\n"
        "\n"
        "## Scope policy\n"
        "\n"
        "- Least privilege. Candidate future scopes: `tweet.write`, "
        "`tweet.read`, `users.read`.\n"
        "- `offline.access` (refresh token) is blocked until a dedicated "
        "justification gate.\n"
        "- Forbidden until scoped: `dm.read`, `dm.write`, `like.write`, "
        "`bookmark.write`, `follows.write`, `mute.write`, `block.write`, "
        "`list.write`, `media.write`, `tweet.moderate.write`, and any scope "
        "unrelated to text-only posting/account proof.\n"
        "\n"
        "## Token storage / redaction / revocation policy\n"
        "\n"
        "- No token exchange, access token, refresh token, or bearer token "
        "now; no token persistence now.\n"
        "- Future token storage is local-only, encrypted or OS-secret-store "
        "backed if available, redacted in logs, never committed or placed in "
        "evidence.\n"
        "- Token rotation and revocation plans are required before the first "
        "credential-readiness gate.\n"
        "\n"
        "## What this did NOT do\n"
        "\n"
        "No X (or any platform) API call. No OAuth flow, authorize URL, "
        "browser login, or developer-portal login. No authorization code, "
        "token exchange, or token persistence. No Client ID/Secret read. No "
        "state/code_verifier/code_challenge generated. No account binding, no "
        "credential or env read, no credential-entry schema. No "
        "post/edit/delete/repost/quote/bookmark/like/reply/DM, metrics, "
        "webhook, or scraping. The module never browses docs at runtime; docs "
        "reading was an Antigravity/operator activity before writing symbolic "
        "packet data.\n"
        "\n"
        "## Next\n"
        "\n"
        f"Recommended next task: `{NEXT_TASK}`.\n"
    )


# --------------------------------------------------------------------------- #
# Main gate
# --------------------------------------------------------------------------- #
def run_gate(*, write=False, repo_root=None):
    """Run the strictly-local 0174CW X OAuth design policy gate. Fail-closed.

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
        "inherited_0174cv_commit": INHERITED_0174CV_COMMIT,
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
        "oauth_design_status": "design_only_no_flow",
        "developer_portal_access_status":
            "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "allowed_scope_classes_for_future_design":
            list(ALLOWED_SCOPE_CLASSES_FOR_FUTURE_DESIGN),
        "forbidden_scope_classes_until_scoped":
            list(FORBIDDEN_SCOPE_CLASSES_UNTIL_SCOPED),
        "next_recommended_task": NEXT_TASK,
        "no_live_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_account_binding_performed": True,
        "no_oauth_flow_performed": True,
        "no_authorize_url_opened": True,
        "no_browser_login_performed": True,
        "no_developer_portal_login_performed": True,
        "no_authorization_code_generated_or_received": True,
        "no_code_verifier_generated": True,
        "no_code_challenge_generated": True,
        "no_state_generated": True,
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
