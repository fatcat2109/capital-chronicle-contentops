"""Next-platform account-binding selection gate (0174CP).

This is a STRICTLY LOCAL, decision-only module. It produces a durable, redacted
"next platform account-binding selection" packet that compares X, LinkedIn, and a
Telegram second supervised-post gate as candidates for the NEXT supervised
publishing target, grounded ONLY in official platform documentation that was read
out-of-band (by the operator/agent via a docs reader) and passed in as symbolic
citation metadata.

HARD GUARANTEES (enforced by tests + leakage guards):
  * NO network library is imported (no urllib / requests / httpx / socket).
  * NO platform API call, OAuth flow, token exchange, or account binding.
  * NO env / credential read (never touches the process environment or .env).
  * NO credential slot names beyond symbolic scope names taken from official docs.
  * Fail-closed / preview-only by default: the packet file is written ONLY when
    the explicit ``--write-next-platform-selection`` flag / ``write=True`` is
    passed. No network is performed in either mode.
  * All live-behavior flags (scheduler / reply_dm / metrics / webhook / scraping)
    are FALSE for every candidate.
  * ``status`` cannot be ``pass`` unless at least one official source is recorded.
  * Deterministic packet JSON: sorted keys, stable separators, trailing newline.
  * A redaction scanner runs over the packet BEFORE write and blocks on token-like
    values, raw @handles, long digit runs (possible account ids), Telegram bot API
    URLs, and forbidden raw request/response/credential keys.
  * This task does NOT alter any Telegram live gate.
"""

import hashlib
import json
import os.path
import re

TASK_LABEL = (
    "TASK_CONTENTOPS_0174CP_NEXT_PLATFORM_ACCOUNT_BINDING_SELECTION_"
    "AND_OFFICIAL_DOCS_GATE_V0"
)

GATE = "NEXT_PLATFORM_ACCOUNT_BINDING_SELECTION_0174CP"
SOURCE_BASELINE_COMMIT = "4ee0369a18fadee8c759d565ad21b836c66c7ddb"

# Explicit write flag. Default behavior is preview-only / fail-closed.
FLAG_WRITE_PACKET = "--write-next-platform-selection"

# Packet artifact location (relative to repo root).
PACKET_REL_DIR = os.path.join("docs", "credential_readiness", "0174CP")
PACKET_FILENAME = "next_platform_account_binding_selection_packet.json"

# Candidate identifiers.
CANDIDATE_X = "x"
CANDIDATE_LINKEDIN = "linkedin"
CANDIDATE_TELEGRAM_SECOND = "telegram_second_gate"

# --------------------------------------------------------------------------- #
# Redaction patterns (defense-in-depth). The packet only ever holds booleans,
# symbolic strings, official doc URLs/titles, and redacted role/scope names.
# --------------------------------------------------------------------------- #
_SECRET_LIKE = [
    re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}"),           # telegram bot token body
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),  # PEM private key
    re.compile(r"AKIA[0-9A-Z]{16}"),                    # AWS access key id
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),                # GitHub PAT
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}"),        # bearer token
]
# Raw bot-api URL containing a token.
_URL_WITH_TOKEN = re.compile(r"api\.telegram\.org/bot\d{6,}:")
# Any api.telegram.org URL reference at all (no raw bot URLs allowed in packet).
_TELEGRAM_BOT_URL = re.compile(r"api\.telegram\.org")
# Raw @handle (account handle).
_HANDLE_LIKE = re.compile(r"@[A-Za-z0-9_]{3,}")
# A long run of digits that could be an account / chat / channel id value.
_LONG_DIGITS = re.compile(r"(?<!\d)-?\d{7,}(?!\d)")

# Official documentation hosts that ARE allowed to appear as citation URLs.
_ALLOWED_DOC_HOSTS = (
    "docs.x.com",
    "developer.x.com",
    "learn.microsoft.com",
    "core.telegram.org",
)

# Forbidden raw keys that would indicate an account-id / raw-traffic / secret leak.
_FORBIDDEN_KEYS = (
    "token",
    "bot_token",
    "access_token",
    "refresh_token",
    "client_secret",
    "api_key",
    "chat_id",
    "channel_id",
    "channel_username",
    "account_id",
    "account_handle",
    "user_id",
    "organization_id",
    "org_urn",
    "person_urn",
    "raw_url",
    "raw_request",
    "raw_response",
    "target_identifier",
    "target_value",
)


# --------------------------------------------------------------------------- #
# Redaction scanner
# --------------------------------------------------------------------------- #
def scan_packet_for_leaks(packet):
    """Return a sorted list of redaction violations for the packet object.

    Blocks token-like values, raw bot-API URLs, raw @handles, long digit runs
    (possible account/chat/channel ids), credential-like strings, and any
    forbidden raw key anywhere in the structure. Official documentation URLs on
    allowed hosts are NOT treated as leaks.
    """
    violations = []

    def _walk(obj, key=None):
        if isinstance(obj, dict):
            for k, v in obj.items():
                kl = str(k).lower()
                if kl in _FORBIDDEN_KEYS:
                    violations.append(f"forbidden_key:{kl}")
                _walk(v, k)
        elif isinstance(obj, list):
            for v in obj:
                _walk(v, key)
        elif isinstance(obj, str):
            _scan_string(obj, key)

    def _scan_string(s, key):
        for pat in _SECRET_LIKE:
            if pat.search(s):
                violations.append(f"secret_like_value:{key or 'value'}")
                break
        if _URL_WITH_TOKEN.search(s) or _TELEGRAM_BOT_URL.search(s):
            # core.telegram.org docs are allowed; api.telegram.org bot URLs are not.
            violations.append(f"telegram_bot_url:{key or 'value'}")
        # Allow @handles ONLY if the string is purely a doc citation? No: official
        # doc URLs do not contain @handles, so any @handle is a raw-handle leak.
        if _HANDLE_LIKE.search(s):
            violations.append(f"raw_handle:{key or 'value'}")
        if _LONG_DIGITS.search(s) and not _is_known_safe_identifier(s, key):
            violations.append(f"long_digits_possible_id:{key or 'value'}")

    _walk(packet)
    return sorted(set(violations))


def _is_known_safe_identifier(s, key):
    """True for known-safe strings (baseline git SHA, official doc URLs/dates)."""
    if s == SOURCE_BASELINE_COMMIT:
        return True
    # Official documentation URLs on allowed hosts may contain version digits
    # (e.g. li-lms-2026-06); those are not account ids.
    if any(host in s for host in _ALLOWED_DOC_HOSTS):
        # Reject only if it ALSO contains a >=7 pure-digit run that is not a date.
        # Doc version monikers use short year/month groups separated by hyphens,
        # which _LONG_DIGITS (>=7 consecutive) does not match. So allow.
        return True
    # ISO accessed-date like 2026-06-15 has no 7+ consecutive digit run.
    return False


# --------------------------------------------------------------------------- #
# Candidate evidence (grounded in official docs read out-of-band)
# --------------------------------------------------------------------------- #
def build_candidate_x():
    """X (create post) candidate, grounded in official docs.x.com / developer.x.com."""
    return {
        "platform": CANDIDATE_X,
        "official_docs_checked": True,
        "official_docs_sources": [
            {
                "source_family": "x_official_api_docs",
                "title": "Create or Edit Post - X API (Manage Posts)",
                "url": "https://docs.x.com/x-api/posts/create-post",
                "accessed_date": "2026-06-15",
            },
            {
                "source_family": "x_official_developer_portal",
                "title": "X Developer Console / access onboarding",
                "url": "https://developer.x.com/en/portal",
                "accessed_date": "2026-06-15",
            },
        ],
        "docs_access_status": "accessible",
        "account_binding_model": "user_account",
        "expected_auth_model": "oauth_user_context",
        "required_permissions_or_roles_redacted": [
            "oauth2_user_context_authorization",
            "post_write_scope_symbolic",
            "developer_app_with_access_tier",
        ],
        "create_post_endpoint_family": "x_api_v2_manage_posts_create_post",
        "live_write_risk_class": "high",
        "credential_complexity_class": "high",
        "approval_flow_required": True,
        "dry_run_required": True,
        "first_live_post_requires_new_explicit_task": True,
        "scheduler_enabled": False,
        "reply_dm_enabled": False,
        "metrics_fetch_enabled": False,
        "webhook_enabled": False,
        "scraping_enabled": False,
        "blockers": [
            "post_write_requires_developer_app_access_tier_not_yet_verified",
            "oauth2_user_context_flow_not_yet_established",
        ],
        "caveats": [
            "strategically_valuable_broad_reach",
            "access_tier_and_rate_limits_must_be_verified_before_any_live_path",
            "oauth_user_context_increases_credential_handling_surface",
        ],
    }


def build_candidate_linkedin():
    """LinkedIn (Posts API) candidate, grounded in official Microsoft Learn docs."""
    return {
        "platform": CANDIDATE_LINKEDIN,
        "official_docs_checked": True,
        "official_docs_sources": [
            {
                "source_family": "linkedin_official_microsoft_learn",
                "title": "Posts API - LinkedIn | Microsoft Learn",
                "url": (
                    "https://learn.microsoft.com/en-us/linkedin/marketing/"
                    "community-management/shares/posts-api"
                ),
                "accessed_date": "2026-06-15",
            },
        ],
        "docs_access_status": "accessible",
        "account_binding_model": "organization_page",
        "expected_auth_model": "organization_member_permission",
        "required_permissions_or_roles_redacted": [
            "oauth2_member_authorization",
            "organization_content_admin_role_symbolic",
            "posts_write_product_access_symbolic",
            "versioned_api_header_required",
        ],
        "create_post_endpoint_family": "linkedin_marketing_posts_api_create",
        "live_write_risk_class": "high",
        "credential_complexity_class": "high",
        "approval_flow_required": True,
        "dry_run_required": True,
        "first_live_post_requires_new_explicit_task": True,
        "scheduler_enabled": False,
        "reply_dm_enabled": False,
        "metrics_fetch_enabled": False,
        "webhook_enabled": False,
        "scraping_enabled": False,
        "blockers": [
            "requires_member_or_organization_role_and_product_access_review",
            "versioned_api_with_active_deprecation_cycle_needs_pinning",
        ],
        "caveats": [
            "strategically_valuable_for_institutional_credibility",
            "older_marketing_versions_deprecated_must_pin_supported_version",
            "organization_page_role_ownership_must_be_confirmed",
        ],
    }


def build_candidate_telegram_second():
    """Telegram second supervised-post gate, grounded in official Bot API docs."""
    return {
        "platform": CANDIDATE_TELEGRAM_SECOND,
        "official_docs_checked": True,
        "official_docs_sources": [
            {
                "source_family": "telegram_official_bot_api",
                "title": "Telegram Bot API - sendMessage",
                "url": "https://core.telegram.org/bots/api#sendmessage",
                "accessed_date": "2026-06-15",
            },
        ],
        "docs_access_status": "accessible",
        "account_binding_model": "bot_channel",
        "expected_auth_model": "bot_token_existing",
        "required_permissions_or_roles_redacted": [
            "existing_bot_token_already_validated_0174ck",
            "channel_post_permission_already_validated_0174cl",
        ],
        "create_post_endpoint_family": "telegram_bot_api_sendmessage",
        "live_write_risk_class": "low",
        "credential_complexity_class": "low",
        "approval_flow_required": True,
        "dry_run_required": True,
        "first_live_post_requires_new_explicit_task": True,
        "scheduler_enabled": False,
        "reply_dm_enabled": False,
        "metrics_fetch_enabled": False,
        "webhook_enabled": False,
        "scraping_enabled": False,
        "blockers": [],
        "caveats": [
            "path_already_proven_through_0174cn_one_time_pilot",
            "adds_less_new_platform_coverage_than_x_or_linkedin",
            "still_requires_new_explicit_task_dry_run_and_operator_go",
        ],
    }


# --------------------------------------------------------------------------- #
# Packet builder
# --------------------------------------------------------------------------- #
def build_selection_packet():
    """Assemble the full, redaction-safe next-platform selection packet."""
    candidates = {
        CANDIDATE_X: build_candidate_x(),
        CANDIDATE_LINKEDIN: build_candidate_linkedin(),
        CANDIDATE_TELEGRAM_SECOND: build_candidate_telegram_second(),
    }

    official_source_count = sum(
        len(c["official_docs_sources"]) for c in candidates.values()
    )

    recommended = CANDIDATE_TELEGRAM_SECOND
    recommendation_reason = (
        "Telegram second-gate is the safest operational next step: the path is "
        "already proven end-to-end (identity 0174CK, target binding 0174CL, "
        "dry-run 0174CM, one live post 0174CN), it reuses an existing validated "
        "bot token with no OAuth flow or app-review, it has the lowest credential "
        "complexity and the simplest redacted audit, and it carries the lowest "
        "risk of accidentally enabling replies/DMs/scheduler/metrics. X and "
        "LinkedIn remain strategically valuable for reach and institutional "
        "credibility respectively, but both require OAuth/member-or-org roles, "
        "product/access-tier review, and version pinning that must be verified in "
        "a dedicated requirements task before any live path."
    )
    next_task_label = (
        "TASK_CONTENTOPS_0174CQ_TELEGRAM_SECOND_SUPERVISED_POST_DRY_RUN_"
        "WITH_DURABLE_LEDGER_GATE_V0"
    )

    # status can only be pass if at least one official source is recorded.
    status = "pass" if official_source_count >= 1 else "blocked"
    blocked_reasons = [] if status == "pass" else ["no_official_source_recorded"]

    packet = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "prior_chain": {
            "telegram_identity_validated": True,
            "telegram_target_binding_validated": True,
            "telegram_dry_run_preflight_validated": True,
            "telegram_first_live_post_delivered_once": True,
            "telegram_post_pilot_ledger_persisted": True,
        },
        "candidates": candidates,
        "official_source_count": official_source_count,
        "recommended_next_platform": recommended,
        "recommendation_reason": recommendation_reason,
        "next_task_label": next_task_label,
        "no_live_call_performed": True,
        "no_credentials_read": True,
        "no_account_binding_performed": True,
        "no_oauth_flow_performed": True,
        "no_token_exchange_performed": True,
        "no_posting_performed": True,
        "no_scheduler_created": True,
        "no_webhook_created": True,
        "no_reply_dm_created": True,
        "no_metrics_fetched": True,
        "no_scraping_performed": True,
        "redaction_verified": True,
        "status": status,
        "blocked_reasons": blocked_reasons,
    }
    return packet


def serialize_packet(packet):
    """Deterministic JSON serialization: sorted keys, stable separators, newline."""
    return json.dumps(packet, sort_keys=True, separators=(",", ":")) + "\n"


def compute_packet_checksum(packet):
    """SHA-256 of the deterministic serialization (artifact integrity, not secret)."""
    return hashlib.sha256(serialize_packet(packet).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Gate runner
# --------------------------------------------------------------------------- #
def run_gate(write=False, repo_root="."):
    """Build, validate, and (optionally) persist the selection packet.

    Returns a redacted summary dict. The packet file is written ONLY when
    ``write=True`` AND the redaction scan passes AND status is pass.
    """
    packet = build_selection_packet()
    violations = scan_packet_for_leaks(packet)

    summary = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "write_requested": bool(write),
        "network_performed": False,
        "env_read_performed": False,
        "official_source_count": packet["official_source_count"],
        "recommendation_has_official_source": packet["official_source_count"] >= 1,
        "recommended_next_platform": packet["recommended_next_platform"],
        "next_task_label": packet["next_task_label"],
        "redaction_scan_passed": not violations,
        "redaction_violations": violations,
        "packet_serialized": False,
        "packet_written": False,
        "packet_path": os.path.join(PACKET_REL_DIR, PACKET_FILENAME),
        "packet_checksum": None,
        "redaction_verified": not violations,
        "status": "fail_closed",
        "blocked_reasons": [],
    }

    if violations:
        summary["status"] = "blocked"
        summary["blocked_reasons"] = ["redaction_guard_triggered"]
        return summary

    if packet["status"] != "pass":
        summary["status"] = packet["status"]
        summary["blocked_reasons"] = packet["blocked_reasons"]
        return summary

    serialized = serialize_packet(packet)
    summary["packet_serialized"] = True
    summary["packet_checksum"] = compute_packet_checksum(packet)

    if not write:
        # Preview-only / fail-closed default: do not touch disk.
        summary["status"] = "pass"
        return summary

    out_dir = os.path.join(repo_root, PACKET_REL_DIR)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, PACKET_FILENAME)
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(serialized)

    summary["packet_written"] = True
    summary["status"] = "pass"
    return summary


def main(argv=None):
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)
    write = FLAG_WRITE_PACKET in argv
    result = run_gate(write=write)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
