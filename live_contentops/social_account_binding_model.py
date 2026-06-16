"""Social account binding model + fake-provider contract (0174EB).

This module is the platform-agnostic, deterministic, LOCAL foundation that
future supervised live adapters MUST use to prove that an approved payload is
bound to the EXACT intended destination account/channel/page/instance BEFORE
any supervised write is even considered.

HARD GUARANTEES (enforced by tests + leakage guards):
  * Pure Python stdlib only. No requests/httpx/aiohttp, no socket/ssl/http
    server, no selenium/playwright, no dotenv/keyring/sqlite.
  * NO network call of any kind.
  * NO credential / token / OAuth / env / .env / secret-store read.
  * NO live posting, mutation, scheduling, scraping, or dispatch.
  * NO live-write capability: every profile and every decision reports
    ``live_write_enabled = False`` and ``autonomous_posting_allowed = False``.
  * Only symbolic classes / booleans / operator-supplied non-secret labels are
    ever stored. Forbidden identifier values (tokens, OAuth codes, refresh /
    bearer tokens, client secrets, raw provider responses, response headers,
    sensitive raw account ids, forbidden profile URLs, callback URLs with
    query strings, env values, credential fingerprints/prefixes/suffixes/
    hashes) are rejected by a fail-closed redaction scanner.
  * The deterministic binding id is computed over NON-SECRET fields only.
  * Fake providers simulate success / failure cases WITHOUT any live
    credential or network, returning only symbolic result classes.

Importing this module performs NO writes and NO side effects. Artifacts are
written ONLY when ``write_artifacts(...)`` is called explicitly.
"""

import hashlib
import json
import os.path
import re

TASK_LABEL = (
    "TASK_CONTENTOPS_0174EB_SOCIAL_ACCOUNT_BINDING_MODEL_AND_FAKE_PROVIDER_"
    "CONTRACT_V0"
)
MODEL = "SOCIAL_ACCOUNT_BINDING_MODEL_0174EB"
MODEL_VERSION = "0174EB_BINDING_MODEL_V1"
# Salt/version constant mixed into the deterministic binding id.
BINDING_ID_SALT = "0174EB_BINDING_MODEL_V1"
SOURCE_BASELINE_COMMIT = "6c1e01c1238ca930b97fde1c4513ebc2c819da76"

# Output artifact locations (written ONLY by the explicit write helper).
DOC_REL_DIR = os.path.join("docs", "automation", "0174EB")
PACKET_FILENAME = "social_account_binding_model_packet.json"
DOC_FILENAME = "social_account_binding_model_and_fake_provider_contract.md"

NEXT_REQUIRED_GATE = (
    "credential handle + redaction boundary (presence-class only: configured "
    "/ not_configured / unknown; no value, hash, prefix, suffix, or "
    "fingerprint), then approval ledger + payload hash, outbox + idempotency, "
    "rate/spend/retry policy, and redacted dispatch audit before any "
    "supervised live write"
)
EXACT_NEXT_TASK_RECOMMENDATION = (
    "TASK_CONTENTOPS_0174EC_CREDENTIAL_HANDLE_AND_REDACTION_BOUNDARY_V0"
)


# --------------------------------------------------------------------------- #
# Status / decision vocabularies (symbolic classes only)
# --------------------------------------------------------------------------- #
class BindingStatus:
    PASS = "pass"
    BLOCKED = "blocked"
    FAIL_CLOSED = "fail_closed"


# account_binding_status classes
BINDING_CANDIDATE_VALIDATED = "binding_candidate_validated_fake_provider"
BINDING_NOT_VALIDATED = "binding_not_validated"
BINDING_FORBIDDEN_FIELD = "binding_fail_closed_forbidden_field_detected"

# Required-proof kinds (symbolic).
PROOF_IDENTITY = "identity_proof"
PROOF_PERMISSION = "permission_or_scope_proof"
PROOF_DESTINATION = "destination_match_proof"
PROOF_DOCS = "official_docs_verification_proof"
PROOF_AUDIT = "platform_audit_public_readiness_proof"
PROOF_SPEND = "spend_budget_proof"
PROOF_REDIRECT = "redirect_final_host_match_proof"
PROOF_DUPLICATE = "duplicate_destination_prevention_proof"

# Fake-provider result classes (the simulated scenarios this task must cover).
FP_SUCCESS = "identity_proof_success"
FP_WRONG_ACCOUNT = "wrong_account"
FP_MISSING_SCOPE = "missing_permission_or_scope"
FP_DOCS_UNRESOLVED = "docs_unresolved"
FP_AUDIT_NOT_APPROVED = "audit_not_approved"
FP_RATE_LIMITED = "rate_limited"
FP_SPEND_BLOCKED = "spend_budget_blocked"
FP_PRIVATE_TEST_ONLY = "private_test_only"
FP_DESTINATION_MISMATCH = "destination_mismatch"
FP_TOKEN_MISSING = "token_missing"
FP_CREDENTIAL_SOURCE_UNAVAILABLE = "credential_source_unavailable"
FP_REDIRECT_MISMATCH = "redirect_mismatch"
FP_DUPLICATE_DESTINATION = "duplicate_destination_candidate"

FAKE_PROVIDER_RESULT_CLASSES = (
    FP_SUCCESS, FP_WRONG_ACCOUNT, FP_MISSING_SCOPE, FP_DOCS_UNRESOLVED,
    FP_AUDIT_NOT_APPROVED, FP_RATE_LIMITED, FP_SPEND_BLOCKED,
    FP_PRIVATE_TEST_ONLY, FP_DESTINATION_MISMATCH, FP_TOKEN_MISSING,
    FP_CREDENTIAL_SOURCE_UNAVAILABLE, FP_REDIRECT_MISMATCH,
    FP_DUPLICATE_DESTINATION,
)

# Symbolic identifier classes that MAY be stored.
ALLOWED_IDENTIFIER_CLASSES_BASE = (
    "platform_id",
    "destination_kind",
    "redacted_account_class",
    "stable_destination_label",
    "symbolic_account_binding_id",
    "proof_status_class",
    "permission_status_class",
    "preflight_status_class",
    "docs_status_class",
    "cost_access_class",
    "intended_visibility_class",
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
    "raw_provider_response",
    "response_headers",
    "raw_account_id",
    "callback_url_with_query",
    "env_value",
    "credential_fingerprint",
    "credential_prefix",
    "credential_suffix",
    "credential_hash",
)


# --------------------------------------------------------------------------- #
# Redaction scanner (defense-in-depth; same family as the 0174DC..0174DE
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
    re.compile(r"\bAAAA[A-Za-z0-9%]{20,}\b"),            # X/Twitter bearer body
    re.compile(r"xoxb-[A-Za-z0-9-]{10,}"),               # slack-style bot token
    re.compile(r"\bey[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}"),
]
_BEARER_TOKEN = re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-%]{10,}")
_TOKEN_KV = re.compile(
    r"(?i)\b(?:access_token|refresh_token|bearer_token|client_secret|"
    r"api_key|authorization_code|auth_code|code_verifier|code_challenge|"
    r"webhook_token|bot_token|app_secret|access_jwt|refresh_jwt)\b\s*[:=]\s*"
    r"[A-Za-z0-9._\-/+]{4,}"
)
_TELEGRAM_URL_WITH_BOT = re.compile(r"api\.telegram\.org/bot")
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
    r"(?i)(?:secret|token|client_secret|credential)\s*"
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

_FORBIDDEN_KEYS = (
    "token", "access_token", "refresh_token", "bearer_token", "client_secret",
    "client_id", "api_key", "app_secret", "webhook_token", "bot_token",
    "access_jwt", "refresh_jwt", "account_id", "raw_account_id",
    "account_handle", "user_id", "username", "screen_name", "handle",
    "display_name", "post_id", "tweet_id", "message_id", "channel_id",
    "page_id", "community_id", "media_id", "subreddit_id", "place_id",
    "raw_url", "raw_request", "raw_response", "raw_provider_response",
    "raw_query", "query_string", "authorization_code", "auth_code", "code",
    "state", "code_verifier", "code_challenge", "redirect_uri", "callback_url",
    "token_response", "error_description", "secret", "password", "passwd",
    "secret_hash", "token_hash", "credential_hash", "secret_fingerprint",
    "token_fingerprint", "credential_fingerprint", "token_prefix",
    "token_suffix", "secret_prefix", "secret_suffix", "credential_prefix",
    "credential_suffix", "env_value", "dotenv_value", "source_value",
    "vault_path", "secret_path", "profile_url", "profile_image_url",
    "authorization", "cookie", "set_cookie", "response_headers", "raw_headers",
    "last4", "first6",
)

# Keys whose list values are allowed to contain declared field/class NAMES.
_SCHEMA_NAME_LIST_KEYS = frozenset({
    "allowed_identifier_classes",
    "forbidden_identifier_classes",
    "required_identity_proofs",
    "required_permission_proofs",
    "required_preflight_checks",
    "may_store_classes",
    "must_not_store_classes",
    "fake_provider_result_classes",
    "result_field_classes",
    "blocked_reasons",
    "platform_list",
    "destination_kinds",
})


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, sha256 binding ids)."""
    if s == SOURCE_BASELINE_COMMIT:
        return True
    if re.fullmatch(r"[0-9a-f]{40}", s) or re.fullmatch(r"[0-9a-f]{64}", s):
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
        if _PROFILE_URL.search(s):
            violations.append(f"profile_url:{key or 'value'}")
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
        if _LONG_DIGITS.search(s) and not _is_known_safe_identifier(s):
            violations.append(f"long_digits_possible_id:{key or 'value'}")

    _walk(obj)
    return sorted(set(violations))


# --------------------------------------------------------------------------- #
# Deterministic serialization + binding id
# --------------------------------------------------------------------------- #
def serialize(obj):
    """Deterministic JSON: sorted keys, stable separators, trailing newline."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False) + "\n"


def compute_checksum(obj):
    """SHA-256 of the deterministic serialization."""
    return hashlib.sha256(serialize(obj).encode("utf-8")).hexdigest()


def compute_binding_id(platform_id, destination_kind,
                       operator_supplied_destination_label,
                       intended_visibility_class, proof_class):
    """Deterministic symbolic binding id over NON-SECRET fields only.

    Inputs are restricted to: platform id, destination kind, the operator-
    supplied non-secret destination label, the intended visibility class, the
    required proof class, and the model salt/version. It MUST NOT include any
    token value, provider raw account id, username from a provider raw
    response, profile URL, or callback/query string.
    """
    parts = [
        BINDING_ID_SALT,
        str(platform_id or ""),
        str(destination_kind or ""),
        str(operator_supplied_destination_label or ""),
        str(intended_visibility_class or ""),
        str(proof_class or ""),
    ]
    payload = "\x1f".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Platform binding profiles
# --------------------------------------------------------------------------- #
def _profile(platform_id, platform_label, platform_role, readiness,
             docs_status, cost_class, destination_kinds, identity_proofs,
             permission_proofs, preflight_checks, next_gate,
             requires_docs_verification=False, requires_audit=False,
             requires_spend_proof=False,
             forbidden_extra=()):
    """Build a deterministic PlatformBindingProfile dict."""
    forbidden = list(FORBIDDEN_IDENTIFIER_CLASSES_BASE) + list(forbidden_extra)
    return {
        "platform_id": platform_id,
        "platform_label": platform_label,
        "platform_role": platform_role,
        "current_readiness_class": readiness,
        "official_docs_status": docs_status,
        "cost_or_access_class": cost_class,
        "destination_kinds": list(destination_kinds),
        "required_identity_proofs": list(identity_proofs),
        "required_permission_proofs": list(permission_proofs),
        "required_preflight_checks": list(preflight_checks),
        "allowed_identifier_classes": list(ALLOWED_IDENTIFIER_CLASSES_BASE),
        "forbidden_identifier_classes": sorted(set(forbidden)),
        "requires_docs_verification": bool(requires_docs_verification),
        "requires_audit": bool(requires_audit),
        "requires_spend_proof": bool(requires_spend_proof),
        "live_write_default_enabled": False,
        "autonomous_posting_allowed": False,
        "manual_fallback_available": True,
        "fake_provider_supported": True,
        "next_gate": next_gate,
    }


def _build_platform_profiles():
    p = {}
    p["telegram"] = _profile(
        "telegram", "Telegram", "controlled_channel_first_live_pilot",
        "api_plug_port_only_first_live_pilot_candidate",
        "official_docs_verified", "free_basic_paid_broadcast_off",
        ["channel", "group", "chat"],
        [PROOF_IDENTITY], [PROOF_PERMISSION],
        [PROOF_DESTINATION, PROOF_DUPLICATE],
        "telegram_getMe_identity_proof_gate")
    p["discord"] = _profile(
        "discord", "Discord", "internal_community_announcement",
        "api_plug_port_only", "official_docs_verified",
        "free_rate_header_governed",
        ["webhook_channel", "guild_channel"],
        [PROOF_IDENTITY], [PROOF_PERMISSION],
        [PROOF_DESTINATION, PROOF_REDIRECT, PROOF_DUPLICATE],
        "discord_webhook_binding_gate",
        forbidden_extra=["webhook_url_with_token"])
    p["mastodon"] = _profile(
        "mastodon", "Mastodon", "open_web_technical_audience",
        "api_plug_port_only", "official_docs_verified",
        "free_instance_specific",
        ["instance_account"],
        [PROOF_IDENTITY], [PROOF_PERMISSION],
        [PROOF_DESTINATION, PROOF_DUPLICATE],
        "mastodon_instance_binding_gate")
    p["bluesky"] = _profile(
        "bluesky", "Bluesky", "open_short_form_mirror",
        "api_plug_port_only", "official_docs_verified",
        "free_session_jwt",
        ["repo_account"],
        [PROOF_IDENTITY], [PROOF_PERMISSION],
        [PROOF_DESTINATION, PROOF_DUPLICATE],
        "bluesky_session_binding_gate")
    p["reddit"] = _profile(
        "reddit", "Reddit", "community_discussion_distribution",
        "api_plug_port_only_permission_review_required",
        "official_docs_verified", "free_community_rule_heavy",
        ["subreddit"],
        [PROOF_IDENTITY], [PROOF_PERMISSION],
        [PROOF_DESTINATION, PROOF_REDIRECT, PROOF_DUPLICATE],
        "reddit_subreddit_post_requirements_gate")
    p["x"] = _profile(
        "x", "X (Twitter)", "short_form_distribution_hook_layer",
        "api_plug_port_only_paid_api_required",
        "official_docs_verified_recheck_required", "paid_pay_per_write",
        ["account"],
        [PROOF_IDENTITY], [PROOF_PERMISSION],
        [PROOF_DESTINATION, PROOF_SPEND, PROOF_REDIRECT, PROOF_DUPLICATE],
        "x_supervised_account_binding_proof_acceptance_gate",
        requires_spend_proof=True)
    p["linkedin"] = _profile(
        "linkedin", "LinkedIn", "professional_operator_voice",
        "api_plug_port_only_permission_review_required",
        "official_docs_verified_partial_gated", "review_scope_gated",
        ["member_account", "organization_page"],
        [PROOF_IDENTITY], [PROOF_PERMISSION],
        [PROOF_DESTINATION, PROOF_DUPLICATE],
        "linkedin_member_binding_gate")
    p["tiktok"] = _profile(
        "tiktok", "TikTok", "video_photo_format_later",
        "api_plug_port_only_permission_review_required",
        "official_docs_verified", "review_audit_gated",
        ["creator_account"],
        [PROOF_IDENTITY], [PROOF_PERMISSION],
        [PROOF_DESTINATION, PROOF_AUDIT, PROOF_DUPLICATE],
        "tiktok_audit_readiness_gate",
        requires_audit=True)
    p["youtube"] = _profile(
        "youtube", "YouTube", "long_form_video_later",
        "api_plug_port_only_permission_review_required",
        "official_docs_verified", "quota_audit_gated",
        ["channel"],
        [PROOF_IDENTITY], [PROOF_PERMISSION],
        [PROOF_DESTINATION, PROOF_AUDIT, PROOF_DUPLICATE],
        "youtube_audit_readiness_gate",
        requires_audit=True)
    p["facebook"] = _profile(
        "facebook", "Facebook", "meta_page_distribution_later",
        "api_plug_port_only_official_docs_gated",
        "official_docs_gated_unresolved", "unresolved_review_likely",
        ["page"],
        [PROOF_IDENTITY], [PROOF_PERMISSION],
        [PROOF_DOCS, PROOF_DESTINATION, PROOF_DUPLICATE],
        "meta_authenticated_docs_recheck_gate",
        requires_docs_verification=True)
    p["instagram"] = _profile(
        "instagram", "Instagram", "visual_card_distribution_later",
        "api_plug_port_only_official_docs_gated",
        "official_docs_gated_unresolved", "unresolved_review_likely",
        ["business_account"],
        [PROOF_IDENTITY], [PROOF_PERMISSION],
        [PROOF_DOCS, PROOF_DESTINATION, PROOF_DUPLICATE],
        "meta_authenticated_docs_recheck_gate",
        requires_docs_verification=True)
    p["threads"] = _profile(
        "threads", "Threads", "conversational_mirror",
        "api_plug_port_only_official_docs_gated",
        "official_docs_gated_unresolved", "unresolved_review_likely",
        ["account"],
        [PROOF_IDENTITY], [PROOF_PERMISSION],
        [PROOF_DOCS, PROOF_DESTINATION, PROOF_DUPLICATE],
        "meta_authenticated_docs_recheck_gate",
        requires_docs_verification=True)
    p["substack"] = _profile(
        "substack", "Substack", "canonical_long_form_home",
        "manual_fallback_unsupported_or_unknown_api",
        "official_docs_unresolved_no_public_api", "unresolved_manual_only",
        ["publication"],
        [PROOF_IDENTITY], [PROOF_PERMISSION],
        [PROOF_DOCS, PROOF_DESTINATION, PROOF_DUPLICATE],
        "substack_official_api_confirmation_gate",
        requires_docs_verification=True)
    p["medium"] = _profile(
        "medium", "Medium", "optional_syndication",
        "manual_fallback_unsupported_or_unknown_api",
        "official_docs_unresolved_deprecated_api", "unresolved_manual_only",
        ["publication", "user_profile"],
        [PROOF_IDENTITY], [PROOF_PERMISSION],
        [PROOF_DOCS, PROOF_DESTINATION, PROOF_DUPLICATE],
        "medium_api_support_status_recheck_gate",
        requires_docs_verification=True)
    return p


PLATFORM_PROFILES = _build_platform_profiles()
SUPPORTED_PLATFORMS = tuple(sorted(PLATFORM_PROFILES.keys()))


def get_profile(platform_id):
    """Return a deep copy of the binding profile for a platform, or None."""
    prof = PLATFORM_PROFILES.get(platform_id)
    if prof is None:
        return None
    return json.loads(json.dumps(prof))


# --------------------------------------------------------------------------- #
# Destination + fake-provider result builders
# --------------------------------------------------------------------------- #
def build_destination(platform_id, destination_kind,
                      operator_supplied_destination_label,
                      intended_visibility_class="unlisted_default",
                      proof_class=PROOF_IDENTITY):
    """Build a DestinationBinding dict from NON-SECRET operator inputs only."""
    return {
        "platform_id": platform_id,
        "destination_kind": destination_kind,
        "operator_supplied_destination_label": (
            operator_supplied_destination_label),
        "intended_visibility_class": intended_visibility_class,
        "proof_class": proof_class,
    }


def make_fake_provider_result(result_class, **overrides):
    """Build a deterministic FakeProviderResult.

    The fake provider NEVER calls a network, NEVER reads env/credentials, and
    NEVER returns secret values -- only symbolic boolean/class signals that the
    binding validator consumes. ``result_class`` selects the simulated case and
    seeds the default signal fields; ``overrides`` may adjust individual
    signals for targeted tests.
    """
    if result_class not in FAKE_PROVIDER_RESULT_CLASSES:
        raise ValueError(f"unknown fake provider result class: {result_class}")

    # All-good baseline (what a clean success looks like).
    signals = {
        "result_class": result_class,
        "no_network_performed": True,
        "no_credential_read_performed": True,
        "no_secret_returned": True,
        "token_present": True,
        "credential_source_class": "available",
        "identity_match": True,
        "destination_match": True,
        "permission_granted": True,
        "redirect_match": True,
        "docs_status_class": "verified",
        "audit_status_class": "audit_complete_public",
        "spend_proof_class": "spend_budget_approved",
        "rate_limit_status_class": "ok",
        "duplicate_candidate": False,
        # Redacted identity proof: only a class, never an identifier value.
        "identity_proof_status_class": "identity_confirmed_redacted",
    }

    seed = {
        FP_SUCCESS: {},
        FP_WRONG_ACCOUNT: {
            "identity_match": False,
            "identity_proof_status_class": "wrong_account_redacted"},
        FP_MISSING_SCOPE: {"permission_granted": False},
        FP_DOCS_UNRESOLVED: {"docs_status_class": "unresolved"},
        FP_AUDIT_NOT_APPROVED: {"audit_status_class": "audit_not_approved"},
        FP_RATE_LIMITED: {"rate_limit_status_class": "rate_limited"},
        FP_SPEND_BLOCKED: {"spend_proof_class": "absent"},
        FP_PRIVATE_TEST_ONLY: {"audit_status_class": "private_test_only"},
        FP_DESTINATION_MISMATCH: {"destination_match": False},
        FP_TOKEN_MISSING: {
            "token_present": False,
            "identity_proof_status_class": "token_missing_redacted"},
        FP_CREDENTIAL_SOURCE_UNAVAILABLE: {
            "credential_source_class": "unavailable",
            "token_present": False},
        FP_REDIRECT_MISMATCH: {"redirect_match": False},
        FP_DUPLICATE_DESTINATION: {"duplicate_candidate": True},
    }[result_class]

    signals.update(seed)
    signals.update(overrides)
    return signals


# --------------------------------------------------------------------------- #
# Binding validation
# --------------------------------------------------------------------------- #
def validate_account_binding(profile, destination, fake_provider_result,
                             operator_go=False):
    """Validate a destination binding against a fake-provider result.

    Deterministic, fail-closed, and NON-side-effecting. NEVER enables live
    write. Returns a redacted BindingDecision dict. The ``fake_provider_result``
    is the ONLY source of provider signals and is itself secret-free.
    """
    blocked = []
    status = BindingStatus.PASS

    platform_id = (destination or {}).get("platform_id")
    destination_kind = (destination or {}).get("destination_kind")
    label = (destination or {}).get("operator_supplied_destination_label")
    visibility = (destination or {}).get(
        "intended_visibility_class", "unlisted_default")
    proof_class = (destination or {}).get("proof_class", PROOF_IDENTITY)

    binding_id = compute_binding_id(
        platform_id, destination_kind, label, visibility, proof_class)

    # Fail-closed redaction scan of all caller-supplied inputs. If a forbidden
    # value is present anywhere, refuse to validate.
    forbidden = scan_for_leaks({
        "destination": destination,
        "fake_provider_result": fake_provider_result,
    })
    forbidden_detected = bool(forbidden)

    prof = profile or {}
    fpr = fake_provider_result or {}

    identity_proof_status = "not_evaluated"
    permission_proof_status = "not_evaluated"
    preflight_status = "not_evaluated"
    account_binding_status = BINDING_NOT_VALIDATED

    if forbidden_detected:
        status = BindingStatus.FAIL_CLOSED
        account_binding_status = BINDING_FORBIDDEN_FIELD
        blocked.append("forbidden_field_detected")
    else:
        # Profile/destination consistency.
        if platform_id != prof.get("platform_id"):
            blocked.append("profile_destination_platform_mismatch")
        if (destination_kind not in (prof.get("destination_kinds") or [])):
            blocked.append("destination_kind_not_supported_by_profile")

        # --- Credential / token presence (symbolic only) ----------------- #
        if fpr.get("credential_source_class") == "unavailable":
            blocked.append("credential_source_unavailable")
            identity_proof_status = "credential_source_unavailable_blocked"
        elif not fpr.get("token_present", False):
            blocked.append("token_missing")
            identity_proof_status = "token_missing_blocked"
        elif not fpr.get("identity_match", False):
            blocked.append("wrong_account")
            identity_proof_status = "wrong_account_blocked"
        else:
            identity_proof_status = "identity_confirmed_redacted"

        # --- Destination match -------------------------------------------- #
        if not fpr.get("destination_match", False):
            blocked.append("destination_mismatch")

        # --- Redirect / final-host match (where required) ----------------- #
        if PROOF_REDIRECT in (prof.get("required_preflight_checks") or []):
            if not fpr.get("redirect_match", False):
                blocked.append("redirect_mismatch")

        # --- Permission / scope ------------------------------------------- #
        if not fpr.get("permission_granted", False):
            blocked.append("missing_permission_or_scope")
            permission_proof_status = "permission_missing_blocked"
        else:
            permission_proof_status = "permission_granted_redacted"

        # --- Duplicate destination candidate ------------------------------ #
        if fpr.get("duplicate_candidate", False):
            blocked.append("duplicate_destination_candidate")

        # --- Rate limited ------------------------------------------------- #
        if fpr.get("rate_limit_status_class") == "rate_limited":
            blocked.append("rate_limited")

        # --- Docs verification (Meta-family / Substack / Medium) ---------- #
        if prof.get("requires_docs_verification"):
            if fpr.get("docs_status_class") != "verified":
                blocked.append("docs_unresolved")

        # --- Audit public readiness (TikTok / YouTube) -------------------- #
        if prof.get("requires_audit"):
            if fpr.get("audit_status_class") != "audit_complete_public":
                blocked.append("audit_not_approved")

        # --- Spend budget proof (X) --------------------------------------- #
        if prof.get("requires_spend_proof"):
            if fpr.get("spend_proof_class") != "spend_budget_approved":
                blocked.append("spend_budget_blocked")

        # Preflight summary.
        preflight_blockers = {
            "destination_mismatch", "redirect_mismatch",
            "duplicate_destination_candidate", "rate_limited",
            "docs_unresolved", "audit_not_approved", "spend_budget_blocked",
        }
        if preflight_blockers & set(blocked):
            preflight_status = "preflight_blocked"
        elif identity_proof_status == "identity_confirmed_redacted":
            preflight_status = "preflight_candidate_passed_fake_provider"
        else:
            preflight_status = "preflight_blocked"

        if blocked:
            status = BindingStatus.BLOCKED
            account_binding_status = BINDING_NOT_VALIDATED
        else:
            status = BindingStatus.PASS
            account_binding_status = BINDING_CANDIDATE_VALIDATED

    decision = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": status,
        "platform_id": platform_id,
        "destination_kind": destination_kind,
        "intended_visibility_class": visibility,
        "binding_id": binding_id,
        "account_binding_status": account_binding_status,
        "identity_proof_status": identity_proof_status,
        "permission_proof_status": permission_proof_status,
        "preflight_status": preflight_status,
        "fake_provider_result_class": fpr.get("result_class"),
        "operator_go_status": (
            "operator_go_present" if operator_go else "operator_go_absent"),
        # Hard safety invariants -- ALWAYS these values.
        "live_write_enabled": False,
        "autonomous_posting_allowed": False,
        "manual_fallback_available": True,
        "blocked_reasons": sorted(set(blocked)),
        "redaction_verified": not forbidden_detected,
        "forbidden_fields_detected": forbidden_detected,
        "no_network_performed": True,
        "no_credential_read_performed": True,
        "no_live_post_performed": True,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }
    return decision


# --------------------------------------------------------------------------- #
# Packet builder
# --------------------------------------------------------------------------- #
def build_packet():
    """Build the deterministic redacted 0174EB model packet."""
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "binding_model_status": "deterministic_local_foundation_ready",
        "fake_provider_contract_status": "deterministic_no_network_no_secret",
        "platform_profiles_count": len(PLATFORM_PROFILES),
        "platform_list": list(SUPPORTED_PLATFORMS),
        "platform_profiles": {
            pid: PLATFORM_PROFILES[pid] for pid in SUPPORTED_PLATFORMS
        },
        "fake_provider_result_classes": list(FAKE_PROVIDER_RESULT_CLASSES),
        "binding_id_inputs": [
            "model_salt_version",
            "platform_id",
            "destination_kind",
            "operator_supplied_destination_label",
            "intended_visibility_class",
            "proof_class",
        ],
        "binding_id_excludes": (
            "no token value, no provider raw account id, no provider-derived "
            "username, no profile URL, no callback or query string, no "
            "credential hash/prefix/suffix/fingerprint"
        ),
        "redaction_policy": {
            "may_store_classes": list(ALLOWED_IDENTIFIER_CLASSES_BASE),
            "must_not_store_classes": list(FORBIDDEN_IDENTIFIER_CLASSES_BASE),
            "fail_closed_on_forbidden_value": True,
            "scanner_catches": (
                "tokens, bearer strings, OAuth code/state/verifier/challenge, "
                "callback URLs with query, raw sensitive query strings, env "
                "assignments, secret hash/fingerprint/prefix/suffix claims, "
                "raw social profile URLs, raw response headers/cookies, raw "
                "handles, and long raw numeric ids"
            ),
        },
        "result_field_classes": [
            "status",
            "account_binding_status",
            "identity_proof_status",
            "permission_proof_status",
            "preflight_status",
            "binding_id",
            "blocked_reasons",
        ],
        "safety_flags": {
            "live_write_enabled": False,
            "autonomous_posting_allowed": False,
            "manual_fallback_available": True,
            "no_network_performed": True,
            "no_credential_read_performed": True,
            "no_oauth_performed": True,
            "no_live_post_performed": True,
            "no_scheduler_introduced": True,
            "no_scrape_performed": True,
            "stdlib_only": True,
        },
        "strategic_posture": {
            "manual_posting": "fallback",
            "automation": "main_build_path",
            "autonomous_posting": "forbidden",
            "supervised_publishing": "final_product",
        },
        "next_required_gate": NEXT_REQUIRED_GATE,
        "exact_next_task_recommendation": EXACT_NEXT_TASK_RECOMMENDATION,
        "no_live_network_call_performed": True,
        "no_credential_or_token_read_performed": True,
        "no_posting_performed": True,
        "no_scheduler_or_autonomous_dispatch_introduced": True,
        "redaction_verified": True,
    }
    packet["packet_checksum"] = compute_checksum(
        {k: v for k, v in packet.items()})
    return packet


# --------------------------------------------------------------------------- #
# Contract documentation
# --------------------------------------------------------------------------- #
def build_contract_doc():
    """Deterministic markdown contract document (no secrets, no live refs)."""
    lines = [
        "# Social Account Binding Model + Fake-Provider Contract (0174EB)",
        "",
        f"Task: {TASK_LABEL}",
        "Mode: Implementation Mode. Deterministic, local, stdlib-only "
        "foundation.",
        "",
        "Status: platform-agnostic automation-core foundation. Introduces NO "
        "network call, NO credential/token/OAuth/env read, NO live posting, "
        "NO scheduler, and NO scrape. Every profile and decision reports "
        "`live_write_enabled = false` and `autonomous_posting_allowed = "
        "false`.",
        "",
        "## Strategic posture",
        "",
        "- Manual posting is **fallback**.",
        "- Automation is the **main build path**.",
        "- Autonomous posting is **forbidden**.",
        "- Supervised publishing is the **final product**.",
        "",
        "## Purpose",
        "",
        "Prove that an approved payload is bound to the EXACT intended "
        "destination account/channel/page/instance/subreddit/workspace before "
        "any future supervised write. This module answers: which platform, "
        "which destination, what identity proof is required, which identifier "
        "classes may be stored, which must remain redacted, what preflight "
        "status is required, and how a fake provider proves failure cases "
        "without live credentials or network.",
        "",
        "## Entities",
        "",
        "- `PlatformBindingProfile` -- per-platform binding requirements.",
        "- `DestinationBinding` -- non-secret operator-supplied destination.",
        "- `RequiredProof` -- symbolic proof kinds (identity, permission, "
        "destination, docs, audit, spend, redirect, duplicate-prevention).",
        "- `BindingPreflightResult` / `BindingDecision` / `BindingStatus` -- "
        "redacted decision output.",
        "- `FakeProviderIdentity` / `FakeProviderResult` -- secret-free "
        "simulated provider signals.",
        "",
        "## Deterministic binding id",
        "",
        "`compute_binding_id` hashes ONLY: model salt/version, `platform_id`, "
        "`destination_kind`, operator-supplied non-secret destination label, "
        "`intended_visibility_class`, and `proof_class`. It NEVER includes a "
        "token value, provider raw account id, provider-derived username, "
        "profile URL, or callback/query string.",
        "",
        "## Redaction policy",
        "",
        "May store only symbolic classes (platform id, destination kind, "
        "redacted account class, stable operator-supplied label, symbolic "
        "binding id, and status classes). Must never store tokens, OAuth "
        "codes, refresh/bearer tokens, client secrets, raw provider "
        "responses, response headers, sensitive raw account ids, forbidden "
        "profile URLs, callback URLs with query strings, env values, or "
        "credential fingerprints/prefixes/suffixes/hashes. Any forbidden "
        "value fails closed.",
        "",
        "## Supported platforms",
        "",
    ]
    for pid in SUPPORTED_PLATFORMS:
        prof = PLATFORM_PROFILES[pid]
        lines.append(
            f"- `{pid}` ({prof['platform_label']}): "
            f"{prof['current_readiness_class']}; docs "
            f"{prof['official_docs_status']}; cost "
            f"{prof['cost_or_access_class']}.")
    lines += [
        "",
        "## Fake-provider contract",
        "",
        "Fake providers simulate success, wrong-account, missing-scope, "
        "docs-unresolved, audit-not-approved, rate-limited, spend-blocked, "
        "private-test-only, destination-mismatch, token-missing, "
        "credential-source-unavailable, redirect-mismatch, and "
        "duplicate-destination-candidate cases. They never call a network, "
        "never read env or credentials, never persist secrets, and return only "
        "symbolic result classes.",
        "",
        "## Validation rules",
        "",
        "- Success identity + permission + preflight may produce "
        "`account_binding_status = binding_candidate_validated_fake_provider`.",
        "- Missing operator GO still keeps `live_write_enabled = false`.",
        "- Wrong account / destination mismatch blocks.",
        "- Docs unresolved blocks for Meta-family / Substack / Medium.",
        "- Audit-not-approved blocks for TikTok / YouTube.",
        "- Spend proof absent blocks for X.",
        "- No result implies live posting is ready.",
        "",
        "## What this did NOT do",
        "",
        "No platform API was called (Telegram, X, LinkedIn, Meta, TikTok, "
        "YouTube, Bluesky, Discord, Mastodon, Reddit, Substack, Medium). No "
        "`.env`, environment secret, credential file, browser session, or "
        "platform portal was read. No OAuth, scheduler, or dispatch was added.",
        "",
        "## Next",
        "",
        f"Recommended next task: `{EXACT_NEXT_TASK_RECOMMENDATION}`.",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Explicit artifact writer (NO writes happen on import)
# --------------------------------------------------------------------------- #
def write_artifacts(repo_root=None):
    """Write the deterministic packet + contract doc. Returns written paths.

    This is the ONLY function that touches the filesystem, and it is never
    called on import. It fails closed if the packet does not pass the
    redaction scan.
    """
    if repo_root is None:
        repo_root = os.path.dirname(os.path.dirname(__file__))

    packet = build_packet()
    violations = scan_for_leaks(packet)
    if violations:
        raise AssertionError(f"refusing to write; redaction violations: "
                             f"{violations}")

    out_dir = os.path.join(repo_root, DOC_REL_DIR)
    os.makedirs(out_dir, exist_ok=True)

    packet_path = os.path.join(out_dir, PACKET_FILENAME)
    with open(packet_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(serialize(packet))

    doc_path = os.path.join(out_dir, DOC_FILENAME)
    with open(doc_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_contract_doc())

    return {
        "packet_path": os.path.join(
            DOC_REL_DIR, PACKET_FILENAME).replace(os.sep, "/"),
        "doc_path": os.path.join(
            DOC_REL_DIR, DOC_FILENAME).replace(os.sep, "/"),
    }
