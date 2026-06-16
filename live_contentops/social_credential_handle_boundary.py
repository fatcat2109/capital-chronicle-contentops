"""Social credential handle + redaction boundary (0174EC).

This module is the platform-agnostic, deterministic, LOCAL credential-handle
boundary that future supervised social publishing adapters MUST use WITHOUT
ever storing, printing, hashing, fingerprinting, prefixing, suffixing, or
exposing a credential value. It answers -- symbolically only --

  * which platform credential is required,
  * what symbolic credential handle represents it,
  * what presence class is known (unknown by default),
  * what source class is allowed in the FUTURE (declared, never used now),
  * what source class is forbidden NOW,
  * what proof is still missing before any live use,
  * what redaction guarantees apply, and
  * how fake providers simulate configured / not_configured / unknown /
    expired / revoked / insufficient_scope / wrong_account / source_policy_
    blocked / forbidden_value / live_hydration_attempt WITHOUT secrets.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Pure Python stdlib only. No requests/httpx/aiohttp, no socket/ssl/http
    server, no selenium/playwright, no dotenv/keyring/sqlite, and no
    hidden-input prompt module.
  * NO network call of any kind.
  * NO env / .env / keyring / browser-session / credential-file read.
  * NO OAuth, NO token exchange, NO token refresh, NO live hydration.
  * NO live posting, mutation, scheduling, scraping, or dispatch.
  * Only symbolic classes / booleans / operator-supplied non-secret labels are
    ever stored. Forbidden credential material (tokens, OAuth codes, refresh /
    bearer tokens, client secrets, api keys, webhook URLs, raw provider
    responses, response headers, sensitive raw account ids, profile URLs,
    callback URLs with query strings, env values, credential fingerprints /
    prefixes / suffixes / hashes) is rejected by a fail-closed scanner.
  * The deterministic credential handle id is computed over NON-SECRET fields
    only.
  * ``live_hydration_allowed`` is ALWAYS False; operator GO cannot change it --
    this task can never hydrate a secret.

Importing this module performs NO writes and NO side effects. Artifacts are
written ONLY when ``write_artifacts(...)`` is called explicitly.
"""

import hashlib
import json
import os.path
import re

TASK_LABEL = "TASK_CONTENTOPS_0174EC_CREDENTIAL_HANDLE_AND_REDACTION_BOUNDARY_V0"
MODEL = "SOCIAL_CREDENTIAL_HANDLE_BOUNDARY_0174EC"
MODEL_VERSION = "0174EC_CREDENTIAL_HANDLE_BOUNDARY_V1"
# Salt/version constant mixed into the deterministic credential handle id.
HANDLE_ID_SALT = "0174EC_CREDENTIAL_HANDLE_BOUNDARY_V1"
SOURCE_BASELINE_COMMIT = "c5763167bee79f41381465af517039498c219f63"

# Output artifact locations (written ONLY by the explicit write helper).
DOC_REL_DIR = os.path.join("docs", "automation", "0174EC")
PACKET_FILENAME = "social_credential_handle_boundary_packet.json"
DOC_FILENAME = "social_credential_handle_and_redaction_boundary.md"

NEXT_REQUIRED_GATE = (
    "approval ledger + payload hash contract, then outbox + idempotency, "
    "rate/spend/retry policy, and redacted dispatch audit before any "
    "supervised live write; live credential hydration remains a separate "
    "future operator-owned gate and is NOT enabled here"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174ED_APPROVAL_LEDGER_AND_PAYLOAD_HASH_CONTRACT_V0"
)


# --------------------------------------------------------------------------- #
# Status / class vocabularies (symbolic only)
# --------------------------------------------------------------------------- #
class CredentialStatus:
    PASS = "pass"
    BLOCKED = "blocked"
    FAIL_CLOSED = "fail_closed"


# credential_readiness_status classes
READINESS_SYMBOLIC_CANDIDATE = "credential_symbolic_readiness_candidate"
READINESS_NOT_READY = "credential_not_ready"
READINESS_FAIL_CLOSED = "credential_fail_closed_forbidden_value"

# Symbolic presence classes (NEVER reveal a value or account identifier).
PRESENCE_UNKNOWN = "unknown"
PRESENCE_NOT_CONFIGURED = "not_configured"
PRESENCE_CONFIGURED_SYMBOLIC = "configured_symbolic"
PRESENCE_UNAVAILABLE = "unavailable"
PRESENCE_EXPIRED_SYMBOLIC = "expired_symbolic"
PRESENCE_REVOKED_SYMBOLIC = "revoked_symbolic"
PRESENCE_INSUFFICIENT_SCOPE_SYMBOLIC = "insufficient_scope_symbolic"
PRESENCE_WRONG_ACCOUNT_SYMBOLIC = "wrong_account_symbolic"
PRESENCE_SOURCE_POLICY_BLOCKED = "source_policy_blocked"
PRESENCE_FORBIDDEN_VALUE_DETECTED = "forbidden_value_detected"
PRESENCE_LIVE_HYDRATION_NOT_ALLOWED = "live_hydration_not_allowed"

PRESENCE_CLASSES = (
    PRESENCE_UNKNOWN,
    PRESENCE_NOT_CONFIGURED,
    PRESENCE_CONFIGURED_SYMBOLIC,
    PRESENCE_UNAVAILABLE,
    PRESENCE_EXPIRED_SYMBOLIC,
    PRESENCE_REVOKED_SYMBOLIC,
    PRESENCE_INSUFFICIENT_SCOPE_SYMBOLIC,
    PRESENCE_WRONG_ACCOUNT_SYMBOLIC,
    PRESENCE_SOURCE_POLICY_BLOCKED,
    PRESENCE_FORBIDDEN_VALUE_DETECTED,
    PRESENCE_LIVE_HYDRATION_NOT_ALLOWED,
)

# Credential families (symbolic).
FAM_BOT_TOKEN = "bot_token"
FAM_WEBHOOK_URL_SECRET = "webhook_url_secret"
FAM_OAUTH2_USER_CONTEXT = "oauth2_user_context_token"
FAM_OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"
FAM_OAUTH1A_USER_PAIR = "oauth1a_user_context_token_pair"
FAM_APP_PASSWORD_OR_SESSION = "app_password_or_session_token"
FAM_INSTANCE_OAUTH = "instance_oauth_token"
FAM_API_KEY_DELEGATED = "api_key_delegated_provider"
FAM_UNSUPPORTED = "unsupported_or_manual_only"

CREDENTIAL_FAMILIES = (
    FAM_BOT_TOKEN,
    FAM_WEBHOOK_URL_SECRET,
    FAM_OAUTH2_USER_CONTEXT,
    FAM_OAUTH2_CLIENT_CREDENTIALS,
    FAM_OAUTH1A_USER_PAIR,
    FAM_APP_PASSWORD_OR_SESSION,
    FAM_INSTANCE_OAUTH,
    FAM_API_KEY_DELEGATED,
    FAM_UNSUPPORTED,
)

# Future source classes (declared symbolically; NEVER used by this task).
FUTURE_SOURCE_INTERACTIVE_PROMPT = "interactive_hidden_prompt_future_gate"
FUTURE_SOURCE_EXTERNAL_SECRET_MANAGER = "external_secret_manager_future_gate"
FUTURE_SOURCE_OPERATOR_SESSION_MEMORY = "operator_session_memory_future_gate"
FUTURE_SOURCE_PLATFORM_OAUTH_CALLBACK = "platform_oauth_callback_future_gate"

FUTURE_SOURCE_CLASSES = (
    FUTURE_SOURCE_INTERACTIVE_PROMPT,
    FUTURE_SOURCE_EXTERNAL_SECRET_MANAGER,
    FUTURE_SOURCE_OPERATOR_SESSION_MEMORY,
    FUTURE_SOURCE_PLATFORM_OAUTH_CALLBACK,
)

# Source classes that are FORBIDDEN now (must never be exercised).
FORBIDDEN_CURRENT_SOURCE_CLASSES = (
    "os_environ_read",
    "dotenv_file_read",
    "keyring_read",
    "browser_session_read",
    "credential_file_read",
    "oauth_callback_server_execution",
    "token_exchange_or_refresh",
    "api_token_validation_call",
)

# Source classes allowed for THIS task (symbolic, no secret material).
ALLOWED_CURRENT_SOURCE_CLASSES = (
    "fake_provider_result",
    "operator_declared_symbolic_presence",
    "docs_declared_requirement",
)

# Fake-provider result classes (the simulated scenarios this task must cover).
FCP_CONFIGURED_SYMBOLIC = "configured_symbolic"
FCP_NOT_CONFIGURED = "not_configured"
FCP_UNKNOWN = "unknown"
FCP_EXPIRED_SYMBOLIC = "expired_symbolic"
FCP_REVOKED_SYMBOLIC = "revoked_symbolic"
FCP_INSUFFICIENT_SCOPE_SYMBOLIC = "insufficient_scope_symbolic"
FCP_WRONG_ACCOUNT_SYMBOLIC = "wrong_account_symbolic"
FCP_SOURCE_POLICY_BLOCKED = "source_policy_blocked"
FCP_FORBIDDEN_VALUE_DETECTED = "forbidden_value_detected"
FCP_LIVE_HYDRATION_ATTEMPT_BLOCKED = "live_hydration_attempt_blocked"

FAKE_CREDENTIAL_PROVIDER_RESULT_CLASSES = (
    FCP_CONFIGURED_SYMBOLIC,
    FCP_NOT_CONFIGURED,
    FCP_UNKNOWN,
    FCP_EXPIRED_SYMBOLIC,
    FCP_REVOKED_SYMBOLIC,
    FCP_INSUFFICIENT_SCOPE_SYMBOLIC,
    FCP_WRONG_ACCOUNT_SYMBOLIC,
    FCP_SOURCE_POLICY_BLOCKED,
    FCP_FORBIDDEN_VALUE_DETECTED,
    FCP_LIVE_HYDRATION_ATTEMPT_BLOCKED,
)

# Symbolic identifier classes that MAY be stored.
ALLOWED_IDENTIFIER_CLASSES_BASE = (
    "platform_id",
    "credential_family",
    "credential_use_class",
    "stable_handle_label",
    "symbolic_credential_handle_id",
    "presence_class",
    "source_class",
    "readiness_status_class",
    "redaction_status_class",
    "future_source_class",
)

# Identifier classes that MUST NEVER be stored.
FORBIDDEN_IDENTIFIER_CLASSES_BASE = (
    "raw_token",
    "oauth_code",
    "refresh_token",
    "bearer_token",
    "client_secret",
    "client_id",
    "api_key",
    "webhook_url",
    "raw_provider_response",
    "response_headers",
    "raw_account_id",
    "profile_url",
    "callback_url_with_query",
    "env_value",
    "credential_fingerprint",
    "credential_prefix",
    "credential_suffix",
    "credential_hash",
)


# --------------------------------------------------------------------------- #
# Redaction scanner (defense-in-depth; same family as the 0174DC..0174EB
# chain). Catches tokens / bearer strings / OAuth code/query / callback URLs
# with query / env assignments / secret fingerprint-prefix-suffix-hash claims /
# raw social profile URLs / raw response headers / raw handles / long raw ids,
# plus any forbidden key.
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
# Raw social profile / destination URLs that must never be persisted.
_PROFILE_URL = re.compile(
    r"(?i)https?://(?:www\.)?(?:twitter\.com|x\.com|facebook\.com|fb\.com|"
    r"instagram\.com|linkedin\.com|tiktok\.com|youtube\.com|youtu\.be|"
    r"t\.me|telegram\.me|reddit\.com|medium\.com|substack\.com|threads\.net|"
    r"bsky\.app|discord\.com|discordapp\.com)/\S+"
)
# Vault/secret path that looks like it reveals a sensitive value path.
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
)

# Keys whose list/string values are allowed to contain declared field/class
# NAMES (these are schema vocabularies, not secret material).
_SCHEMA_NAME_LIST_KEYS = frozenset({
    "allowed_identifier_classes",
    "forbidden_identifier_classes",
    "credential_families",
    "credential_family",
    "allowed_future_source_classes",
    "forbidden_current_source_classes",
    "allowed_current_source_classes",
    "future_source_classes",
    "fake_provider_result_classes",
    "fake_credential_provider_result_classes",
    "presence_classes",
    "result_field_classes",
    "blocked_reasons",
    "platform_list",
    "may_store_classes",
    "must_not_store_classes",
    "scanner_catches",
    "credential_use_class",
    "required_for_future_gate",
    "next_gate",
    "next_required_gate",
})


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, sha256 handle ids)."""
    if s == SOURCE_BASELINE_COMMIT:
        return True
    if re.fullmatch(r"[0-9a-f]{40}", s) or re.fullmatch(r"[0-9a-f]{64}", s):
        return True
    return False


_HEX_CHARS = set("0123456789abcdefABCDEF")


def _long_digit_id_present(s):
    """True if a 7+ digit run looks like a raw account/message/page id.

    A digit run that is merely a fragment of a 40- or 64-character hex token
    (e.g. a git SHA or sha256 embedded in prose) is NOT a leak and is skipped.
    """
    for m in _LONG_DIGITS.finditer(s):
        start, end = m.start(), m.end()
        left = start
        while left > 0 and s[left - 1] in _HEX_CHARS:
            left -= 1
        right = end
        while right < len(s) and s[right] in _HEX_CHARS:
            right += 1
        if (right - left) in (40, 64):
            continue
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


# --------------------------------------------------------------------------- #
# Deterministic serialization + credential handle id
# --------------------------------------------------------------------------- #
def serialize(obj):
    """Deterministic JSON: sorted keys, stable separators, trailing newline."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization."""
    return hashlib.sha256(serialize(obj).encode("utf-8")).hexdigest()


def compute_handle_id(platform_id, credential_family, credential_use_class,
                      operator_supplied_handle_label, future_source_class):
    """Deterministic symbolic credential handle id over NON-SECRET fields only.

    Inputs are restricted to: the model salt/version, platform id, credential
    family, credential use class, the operator-supplied non-secret handle
    label, and a declared future/environment source class. It MUST NOT include
    any token value, refresh/bearer token, client secret, api key, webhook URL,
    profile URL, account id, username/handle, secret hash/fingerprint/prefix/
    suffix, env var value, or callback/query string.
    """
    parts = [
        HANDLE_ID_SALT,
        str(platform_id or ""),
        str(credential_family or ""),
        str(credential_use_class or ""),
        str(operator_supplied_handle_label or ""),
        str(future_source_class or ""),
    ]
    payload = "\x1f".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Credential handle profiles
# --------------------------------------------------------------------------- #
def _profile(platform_id, platform_label, credential_family,
             credential_use_class, required_for_future_gate,
             allowed_future_source_classes, next_gate,
             forbidden_extra=()):
    """Build a deterministic CredentialHandleProfile dict."""
    forbidden = list(FORBIDDEN_IDENTIFIER_CLASSES_BASE) + list(forbidden_extra)
    return {
        "platform_id": platform_id,
        "platform_label": platform_label,
        "credential_family": credential_family,
        "credential_use_class": credential_use_class,
        "required_for_future_gate": required_for_future_gate,
        "allowed_future_source_classes": list(allowed_future_source_classes),
        "forbidden_current_source_classes": list(
            FORBIDDEN_CURRENT_SOURCE_CLASSES),
        "allowed_identifier_classes": list(ALLOWED_IDENTIFIER_CLASSES_BASE),
        "forbidden_identifier_classes": sorted(set(forbidden)),
        "presence_class_default": PRESENCE_UNKNOWN,
        "credential_value_allowed_in_artifacts": False,
        "credential_hash_allowed": False,
        "credential_fingerprint_allowed": False,
        "credential_prefix_suffix_allowed": False,
        "env_read_allowed_by_default": False,
        "dotenv_read_allowed_by_default": False,
        "keyring_read_allowed_by_default": False,
        "browser_session_read_allowed_by_default": False,
        "live_hydration_allowed_now": False,
        "fake_provider_supported": True,
        "next_gate": next_gate,
    }


# Default future-source profile most platforms share for THIS docs-only task.
_DEFAULT_FUTURE_SOURCES = (
    FUTURE_SOURCE_INTERACTIVE_PROMPT,
    FUTURE_SOURCE_EXTERNAL_SECRET_MANAGER,
    FUTURE_SOURCE_OPERATOR_SESSION_MEMORY,
)
_OAUTH_FUTURE_SOURCES = (
    FUTURE_SOURCE_INTERACTIVE_PROMPT,
    FUTURE_SOURCE_EXTERNAL_SECRET_MANAGER,
    FUTURE_SOURCE_OPERATOR_SESSION_MEMORY,
    FUTURE_SOURCE_PLATFORM_OAUTH_CALLBACK,
)


def _build_credential_profiles():
    p = {}
    p["telegram"] = _profile(
        "telegram", "Telegram", FAM_BOT_TOKEN,
        "bot_channel_message_future", "telegram_getMe_identity_proof_gate",
        _DEFAULT_FUTURE_SOURCES,
        "telegram_credential_presence_symbolic_gate")
    p["discord"] = _profile(
        "discord", "Discord", FAM_WEBHOOK_URL_SECRET,
        "webhook_channel_message_future", "discord_webhook_binding_gate",
        _DEFAULT_FUTURE_SOURCES,
        "discord_credential_presence_symbolic_gate",
        forbidden_extra=["webhook_url_with_token"])
    p["mastodon"] = _profile(
        "mastodon", "Mastodon", FAM_INSTANCE_OAUTH,
        "instance_status_write_future", "mastodon_instance_binding_gate",
        _OAUTH_FUTURE_SOURCES,
        "mastodon_credential_presence_symbolic_gate")
    p["bluesky"] = _profile(
        "bluesky", "Bluesky", FAM_APP_PASSWORD_OR_SESSION,
        "repo_record_create_future", "bluesky_session_binding_gate",
        _DEFAULT_FUTURE_SOURCES,
        "bluesky_credential_presence_symbolic_gate")
    p["reddit"] = _profile(
        "reddit", "Reddit", FAM_OAUTH2_USER_CONTEXT,
        "subreddit_submit_future", "reddit_subreddit_post_requirements_gate",
        _OAUTH_FUTURE_SOURCES,
        "reddit_credential_presence_symbolic_gate")
    p["x"] = _profile(
        "x", "X (Twitter)", FAM_OAUTH2_USER_CONTEXT,
        "short_form_post_future_paid",
        "x_supervised_account_binding_proof_acceptance_gate",
        _OAUTH_FUTURE_SOURCES,
        "x_credential_presence_symbolic_gate")
    p["linkedin"] = _profile(
        "linkedin", "LinkedIn", FAM_OAUTH2_USER_CONTEXT,
        "member_post_future_review", "linkedin_member_binding_gate",
        _OAUTH_FUTURE_SOURCES,
        "linkedin_credential_presence_symbolic_gate")
    p["tiktok"] = _profile(
        "tiktok", "TikTok", FAM_OAUTH2_USER_CONTEXT,
        "content_post_future_audit", "tiktok_audit_readiness_gate",
        _OAUTH_FUTURE_SOURCES,
        "tiktok_credential_presence_symbolic_gate")
    p["youtube"] = _profile(
        "youtube", "YouTube", FAM_OAUTH2_USER_CONTEXT,
        "video_insert_future_audit", "youtube_audit_readiness_gate",
        _OAUTH_FUTURE_SOURCES,
        "youtube_credential_presence_symbolic_gate")
    p["facebook"] = _profile(
        "facebook", "Facebook", FAM_OAUTH2_USER_CONTEXT,
        "page_publish_future_docs_unresolved",
        "meta_authenticated_docs_recheck_gate",
        _OAUTH_FUTURE_SOURCES,
        "facebook_credential_presence_symbolic_gate")
    p["instagram"] = _profile(
        "instagram", "Instagram", FAM_OAUTH2_USER_CONTEXT,
        "media_container_publish_future_docs_unresolved",
        "meta_authenticated_docs_recheck_gate",
        _OAUTH_FUTURE_SOURCES,
        "instagram_credential_presence_symbolic_gate")
    p["threads"] = _profile(
        "threads", "Threads", FAM_OAUTH2_USER_CONTEXT,
        "post_future_docs_unresolved",
        "meta_authenticated_docs_recheck_gate",
        _OAUTH_FUTURE_SOURCES,
        "threads_credential_presence_symbolic_gate")
    p["substack"] = _profile(
        "substack", "Substack", FAM_UNSUPPORTED,
        "manual_only_no_public_api",
        "substack_official_api_confirmation_gate",
        _DEFAULT_FUTURE_SOURCES,
        "substack_manual_only_presence_gate")
    p["medium"] = _profile(
        "medium", "Medium", FAM_UNSUPPORTED,
        "manual_only_deprecated_api",
        "medium_api_support_status_recheck_gate",
        _DEFAULT_FUTURE_SOURCES,
        "medium_manual_only_presence_gate")
    return p


CREDENTIAL_PROFILES = _build_credential_profiles()
SUPPORTED_PLATFORMS = tuple(sorted(CREDENTIAL_PROFILES.keys()))


def get_profile(platform_id):
    """Return a deep copy of the credential profile for a platform, or None."""
    prof = CREDENTIAL_PROFILES.get(platform_id)
    if prof is None:
        return None
    return json.loads(json.dumps(prof))


# --------------------------------------------------------------------------- #
# Handle + fake-credential-provider result builders
# --------------------------------------------------------------------------- #
def build_handle(platform_id, credential_family, credential_use_class,
                 operator_supplied_handle_label,
                 future_source_class=FUTURE_SOURCE_INTERACTIVE_PROMPT):
    """Build a CredentialHandle dict from NON-SECRET operator inputs only."""
    return {
        "platform_id": platform_id,
        "credential_family": credential_family,
        "credential_use_class": credential_use_class,
        "operator_supplied_handle_label": operator_supplied_handle_label,
        "future_source_class": future_source_class,
    }


def make_fake_credential_provider_result(result_class, **overrides):
    """Build a deterministic FakeCredentialProviderResult.

    The fake provider NEVER calls a network, NEVER reads env / .env / keyring /
    browser sessions / credential files, and NEVER returns a secret value --
    only symbolic boolean/class signals that the readiness validator consumes.
    ``result_class`` selects the simulated case and seeds the default signal
    fields; ``overrides`` may adjust individual signals for targeted tests.
    """
    if result_class not in FAKE_CREDENTIAL_PROVIDER_RESULT_CLASSES:
        raise ValueError(
            f"unknown fake credential provider result class: {result_class}")

    # All-good baseline (what a clean symbolic-configured result looks like).
    signals = {
        "result_class": result_class,
        "no_network_performed": True,
        "no_env_read_performed": True,
        "no_dotenv_read_performed": True,
        "no_keyring_read_performed": True,
        "no_browser_session_read_performed": True,
        "no_credential_file_read_performed": True,
        "no_oauth_performed": True,
        "no_token_exchange_performed": True,
        "no_token_refresh_performed": True,
        "no_secret_returned": True,
        "presence_class": PRESENCE_CONFIGURED_SYMBOLIC,
        "source_class": "fake_provider_result",
        "source_policy_ok": True,
        "live_hydration_attempted": False,
        "forbidden_value_present": False,
    }

    seed = {
        FCP_CONFIGURED_SYMBOLIC: {},
        FCP_NOT_CONFIGURED: {"presence_class": PRESENCE_NOT_CONFIGURED},
        FCP_UNKNOWN: {"presence_class": PRESENCE_UNKNOWN},
        FCP_EXPIRED_SYMBOLIC: {"presence_class": PRESENCE_EXPIRED_SYMBOLIC},
        FCP_REVOKED_SYMBOLIC: {"presence_class": PRESENCE_REVOKED_SYMBOLIC},
        FCP_INSUFFICIENT_SCOPE_SYMBOLIC: {
            "presence_class": PRESENCE_INSUFFICIENT_SCOPE_SYMBOLIC},
        FCP_WRONG_ACCOUNT_SYMBOLIC: {
            "presence_class": PRESENCE_WRONG_ACCOUNT_SYMBOLIC},
        FCP_SOURCE_POLICY_BLOCKED: {
            "presence_class": PRESENCE_SOURCE_POLICY_BLOCKED,
            "source_policy_ok": False},
        FCP_FORBIDDEN_VALUE_DETECTED: {
            "presence_class": PRESENCE_FORBIDDEN_VALUE_DETECTED,
            "forbidden_value_present": True},
        FCP_LIVE_HYDRATION_ATTEMPT_BLOCKED: {
            "presence_class": PRESENCE_LIVE_HYDRATION_NOT_ALLOWED,
            "live_hydration_attempted": True},
    }[result_class]

    signals.update(seed)
    signals.update(overrides)
    return signals


# --------------------------------------------------------------------------- #
# Credential readiness validation
# --------------------------------------------------------------------------- #
# Presence classes that block (not ready) but are NOT fail-closed.
_BLOCKING_PRESENCE = {
    PRESENCE_NOT_CONFIGURED,
    PRESENCE_UNKNOWN,
    PRESENCE_UNAVAILABLE,
    PRESENCE_EXPIRED_SYMBOLIC,
    PRESENCE_REVOKED_SYMBOLIC,
    PRESENCE_INSUFFICIENT_SCOPE_SYMBOLIC,
    PRESENCE_WRONG_ACCOUNT_SYMBOLIC,
    PRESENCE_SOURCE_POLICY_BLOCKED,
    PRESENCE_LIVE_HYDRATION_NOT_ALLOWED,
}


def validate_credential_handle(profile, handle, fake_provider_result,
                               operator_go=False):
    """Validate a credential handle against a fake-provider result.

    Deterministic, fail-closed, and NON-side-effecting. NEVER enables live
    hydration or live write. Returns a redacted CredentialReadinessDecision
    dict. The ``fake_provider_result`` is the ONLY source of provider signals
    and is itself secret-free.

    Rules:
      * configured_symbolic may pass ONLY as a symbolic readiness candidate;
        it does NOT enable live hydration.
      * not_configured / unknown / expired / revoked / insufficient_scope /
        wrong_account / source_policy_blocked / live_hydration_not_allowed
        all block.
      * any forbidden value in the handle or fake result fails closed.
      * operator_go NEVER changes live_hydration_allowed (always False).
    """
    blocked = []
    status = CredentialStatus.PASS

    platform_id = (handle or {}).get("platform_id")
    credential_family = (handle or {}).get("credential_family")
    credential_use_class = (handle or {}).get("credential_use_class")
    label = (handle or {}).get("operator_supplied_handle_label")
    future_source_class = (handle or {}).get(
        "future_source_class", FUTURE_SOURCE_INTERACTIVE_PROMPT)

    handle_id = compute_handle_id(
        platform_id, credential_family, credential_use_class, label,
        future_source_class)

    # Fail-closed redaction scan of all caller-supplied inputs. If a forbidden
    # value is present anywhere, refuse to validate.
    forbidden = scan_for_leaks([handle, fake_provider_result])
    forbidden_detected = bool(forbidden)

    prof = profile or {}
    fpr = fake_provider_result or {}
    presence_class = fpr.get("presence_class", PRESENCE_UNKNOWN)
    source_class = fpr.get("source_class", "fake_provider_result")

    readiness_status = READINESS_NOT_READY
    redaction_status = "redaction_verified"

    if forbidden_detected or fpr.get("forbidden_value_present"):
        status = CredentialStatus.FAIL_CLOSED
        readiness_status = READINESS_FAIL_CLOSED
        presence_class = PRESENCE_FORBIDDEN_VALUE_DETECTED
        redaction_status = "fail_closed_forbidden_value_detected"
        blocked.append("forbidden_value_detected")
    else:
        # Profile/handle consistency.
        if platform_id != prof.get("platform_id"):
            blocked.append("profile_handle_platform_mismatch")
        if credential_family != prof.get("credential_family"):
            blocked.append("credential_family_mismatch")

        # Source policy: only the allowed symbolic sources are permitted now.
        if not fpr.get("source_policy_ok", False):
            blocked.append("source_policy_blocked")
        if source_class not in ALLOWED_CURRENT_SOURCE_CLASSES:
            blocked.append("source_class_not_allowed_now")

        # A live hydration attempt is always refused by this boundary.
        if fpr.get("live_hydration_attempted"):
            blocked.append("live_hydration_attempt_blocked")

        # Presence evaluation.
        if presence_class == PRESENCE_CONFIGURED_SYMBOLIC:
            readiness_status = READINESS_SYMBOLIC_CANDIDATE
        elif presence_class in _BLOCKING_PRESENCE:
            blocked.append(f"presence_{presence_class}")
        else:
            blocked.append("presence_unrecognized")

        if blocked:
            status = CredentialStatus.BLOCKED
            readiness_status = READINESS_NOT_READY

    decision = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": status,
        "platform_id": platform_id,
        "credential_family": credential_family,
        "credential_handle_id": handle_id,
        "credential_presence_class": presence_class,
        "credential_source_class": source_class,
        "credential_readiness_status": readiness_status,
        "credential_redaction_status": redaction_status,
        "fake_provider_result_class": fpr.get("result_class"),
        "operator_go_status": (
            "operator_go_present" if operator_go else "operator_go_absent"),
        # Hard safety invariants -- ALWAYS these values.
        "live_hydration_allowed": False,
        "live_write_enabled": False,
        "autonomous_posting_allowed": False,
        "manual_fallback_available": True,
        "no_network_performed": True,
        "no_env_read_performed": True,
        "no_dotenv_read_performed": True,
        "no_keyring_read_performed": True,
        "no_browser_session_read_performed": True,
        "no_credential_file_read_performed": True,
        "no_oauth_performed": True,
        "no_token_exchange_performed": True,
        "no_token_refresh_performed": True,
        "no_credential_value_returned": True,
        "no_credential_value_persisted": True,
        "no_credential_hash_or_fingerprint_created": True,
        "no_credential_prefix_or_suffix_exposed": True,
        "blocked_reasons": sorted(set(blocked)),
        "forbidden_fields_detected": forbidden_detected,
        "redaction_verified": not forbidden_detected,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }
    return decision


# --------------------------------------------------------------------------- #
# Packet builder
# --------------------------------------------------------------------------- #
def build_packet():
    """Build the deterministic redacted 0174EC model packet."""
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "credential_handle_boundary_status": (
            "deterministic_local_foundation_ready"),
        "fake_credential_provider_contract_status": (
            "deterministic_no_network_no_env_no_secret"),
        "credential_profile_count": len(CREDENTIAL_PROFILES),
        "platform_list": list(SUPPORTED_PLATFORMS),
        "credential_profiles": {
            pid: CREDENTIAL_PROFILES[pid] for pid in SUPPORTED_PLATFORMS
        },
        "credential_families": list(CREDENTIAL_FAMILIES),
        "presence_classes": list(PRESENCE_CLASSES),
        "fake_credential_provider_result_classes": list(
            FAKE_CREDENTIAL_PROVIDER_RESULT_CLASSES),
        "handle_id_inputs": [
            "model_salt_version",
            "platform_id",
            "credential_family",
            "credential_use_class",
            "operator_supplied_handle_label",
            "future_source_class",
        ],
        "handle_id_excludes": (
            "no token value, no refresh/bearer token, no client secret, no "
            "api key, no webhook URL, no profile URL, no account id, no "
            "username or handle, no credential hash/prefix/suffix/fingerprint, "
            "no env var value, no callback or query string"
        ),
        "source_policy": {
            "allowed_current_source_classes": list(
                ALLOWED_CURRENT_SOURCE_CLASSES),
            "forbidden_current_source_classes": list(
                FORBIDDEN_CURRENT_SOURCE_CLASSES),
            "future_source_classes": list(FUTURE_SOURCE_CLASSES),
            "live_hydration_allowed_now": False,
        },
        "redaction_policy": {
            "may_store_classes": list(ALLOWED_IDENTIFIER_CLASSES_BASE),
            "must_not_store_classes": list(FORBIDDEN_IDENTIFIER_CLASSES_BASE),
            "fail_closed_on_forbidden_value": True,
            "credential_value_allowed_in_artifacts": False,
            "credential_hash_allowed": False,
            "credential_fingerprint_allowed": False,
            "credential_prefix_suffix_allowed": False,
            "scanner_catches": (
                "tokens, bearer strings, telegram/slack/discord-style tokens, "
                "GitHub PATs, AWS-like keys, JWT-like strings, OAuth code/"
                "state/verifier/challenge, refresh/access token KV strings, "
                "env assignments, .env-style lines, callback URLs with query, "
                "raw sensitive query strings, social profile URLs, discord "
                "webhook URLs, raw handles, long raw numeric ids, secret hash/"
                "fingerprint/prefix/suffix claims, first6/last4 claims, raw "
                "response headers/cookies/authorization, secret vault paths, "
                "and forbidden dict keys"
            ),
        },
        "result_field_classes": [
            "status",
            "credential_presence_class",
            "credential_source_class",
            "credential_readiness_status",
            "credential_redaction_status",
            "credential_handle_id",
            "blocked_reasons",
        ],
        "safety_flags": {
            "live_hydration_allowed": False,
            "live_write_enabled": False,
            "autonomous_posting_allowed": False,
            "manual_fallback_available": True,
            "no_network_performed": True,
            "no_env_read_performed": True,
            "no_dotenv_read_performed": True,
            "no_keyring_read_performed": True,
            "no_browser_session_read_performed": True,
            "no_credential_file_read_performed": True,
            "no_oauth_performed": True,
            "no_token_exchange_performed": True,
            "no_token_refresh_performed": True,
            "no_credential_value_returned": True,
            "no_credential_value_persisted": True,
            "no_credential_hash_or_fingerprint_created": True,
            "no_credential_prefix_or_suffix_exposed": True,
            "no_live_posting_scheduler_or_dispatch": True,
        },
        "strategic_posture": {
            "manual_posting": "fallback",
            "automation": "main_build_path",
            "autonomous_posting": "forbidden",
            "supervised_publishing": "final_product",
        },
        "status": CredentialStatus.PASS,
        "next_required_gate": NEXT_REQUIRED_GATE,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
    }
    packet["checksum_sha256"] = compute_checksum(packet)
    return packet


# --------------------------------------------------------------------------- #
# Documentation builder
# --------------------------------------------------------------------------- #
def build_doc():
    """Build the deterministic redacted 0174EC markdown documentation."""
    platforms = "\n".join(
        f"- `{pid}` ({CREDENTIAL_PROFILES[pid]['platform_label']}) -- "
        f"family `{CREDENTIAL_PROFILES[pid]['credential_family']}`"
        for pid in SUPPORTED_PLATFORMS)
    families = "\n".join(f"- `{f}`" for f in CREDENTIAL_FAMILIES)
    presence = "\n".join(f"- `{c}`" for c in PRESENCE_CLASSES)
    fp_classes = "\n".join(
        f"- `{c}`" for c in FAKE_CREDENTIAL_PROVIDER_RESULT_CLASSES)
    allowed_now = "\n".join(f"- `{c}`" for c in ALLOWED_CURRENT_SOURCE_CLASSES)
    forbidden_now = "\n".join(
        f"- `{c}`" for c in FORBIDDEN_CURRENT_SOURCE_CLASSES)
    future = "\n".join(f"- `{c}`" for c in FUTURE_SOURCE_CLASSES)

    return f"""# Social Credential Handle + Redaction Boundary (0174EC)

Task: {TASK_LABEL}
Model: {MODEL} ({MODEL_VERSION})
Source baseline commit: {SOURCE_BASELINE_COMMIT}
Mode: Implementation Mode. Deterministic, stdlib-only, local foundation.

> [!IMPORTANT]
> This module introduces NO live posting, NO credential read, NO environment
> or `.env` read, NO keyring or browser-session read, NO credential-file read,
> NO OAuth execution, NO token exchange or refresh, NO live hydration, NO
> network call, and NO scheduler. It is a symbolic boundary only.

## Strategic Posture
- Manual posting is the **fallback** path, not the strategic destination.
- **Automation is the main build path.**
- **Autonomous posting is forbidden.**
- **Supervised publishing is the final product.**

## What a Credential Handle Is
A credential handle is a **symbolic reference** to the credential a future
supervised adapter will need for a platform. It records, in non-secret terms:
the platform, the credential family, the credential use class, an operator-
supplied non-secret label, a declared future source class, and a deterministic
handle id derived from those non-secret fields only.

## What a Credential Handle Is NOT
A credential handle is **never** a credential value. It does not store, print,
log, hash, fingerprint, prefix, suffix, or otherwise expose any token, refresh
token, bearer token, client secret, API key, webhook URL, profile URL, account
id, username, or handle. It carries no env var value and no callback/query
string.

## Why No Value / Hash / Prefix / Suffix Is Allowed
Even a hash, fingerprint, or "first 6 / last 4" of a secret is a partial
disclosure and a correlation handle. The boundary therefore stores only
symbolic presence/source/readiness classes. A fail-closed redaction scanner
rejects any forbidden material in a handle or a fake-provider result; if found,
validation returns `fail_closed`.

## Presence Classes (symbolic only)
{presence}

## Current Source Policy

Allowed now (symbolic, secret-free):
{allowed_now}

Forbidden now (never exercised by this task):
{forbidden_now}

## Future Source Classes (declared, NOT used now)
{future}

> [!WARNING]
> Future source classes are declarations of intent for later operator-owned,
> separately-gated tasks. This task never reads from any of them.

## Fake Credential Provider Contract
The fake provider simulates credential scenarios with **no network, no env
read, no file read, no keyring access, and no secret return** -- only symbolic
classes and booleans. Simulated result classes:
{fp_classes}

## Supported Platforms
{platforms}

## Credential Families
{families}

## Validation Rules
- `configured_symbolic` may pass ONLY as a symbolic readiness candidate
  (`credential_symbolic_readiness_candidate`); it does **not** enable live
  hydration or live write.
- `not_configured`, `unknown`, `unavailable`, `expired_symbolic`,
  `revoked_symbolic`, `insufficient_scope_symbolic`, `wrong_account_symbolic`,
  `source_policy_blocked`, and `live_hydration_not_allowed` all **block**.
- A `live_hydration_attempt` is always blocked.
- Any forbidden value in the handle or fake result triggers **fail_closed**.
- `operator_go` never changes `live_hydration_allowed`; it is always `False`.
- No result may imply live posting or credential use is ready.

## Handle ID Inputs (non-secret only)
- model salt/version
- platform id
- credential family
- credential use class
- operator-supplied handle label
- future source class

The handle id **excludes** every token, secret, api key, webhook URL, profile
URL, account id, username/handle, secret hash/fingerprint/prefix/suffix, env
value, and callback/query string.

## Next Task
Recommended next task after PASS:
`{EXACT_NEXT_TASK_RECOMMENDATION}`

Next required gate: {NEXT_REQUIRED_GATE}
"""


# --------------------------------------------------------------------------- #
# Explicit artifact writer (no writes happen on import)
# --------------------------------------------------------------------------- #
def write_artifacts(repo_root):
    """Write the deterministic 0174EC packet + doc under ``repo_root``.

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
