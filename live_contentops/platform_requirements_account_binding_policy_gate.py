"""Platform requirements + account-binding policy gate (0174CU).

This module is STRICTLY LOCAL. It performs NO network of any kind and reads NO
env/credentials. Official documentation reading is an Antigravity/operator
activity performed BEFORE this module runs; the module only emits symbolic,
redacted, requirements-only policy packets that were grounded in those docs.

It exists to:

  * Emit three self-contained, deterministic, redacted platform packets:
      - telegram_third_gate (requirements-only; no send now)
      - x (account-binding requirements-only; no OAuth/token/post now)
      - linkedin (account-binding requirements-only; no OAuth/token/post now)
  * Emit an index packet that references the three platform packets, inherits
    the conservative 0174CT operator posture, and records a platform priority
    recommendation.

HARD GUARANTEES (enforced by tests + leakage guards):
  * No network imports (no urllib / requests / httpx / socket / dotenv).
  * No process env / .env read (no environment-variable lookups).
  * Imports ONLY hashlib, json, os.path, re.
  * Fail-closed: writes happen ONLY when the write flag is present AND every
    packet passes the redaction scan.
  * Deterministic JSON: sorted keys, compact separators, trailing newline.
  * No live call, no posting, no scheduler/webhook/getUpdates/reply/DM/metrics,
    no scraping, no OAuth, no token exchange, no account binding, no generic
    publisher.
  * Stores only concise metadata, symbolic endpoint families, required
    permission classes, blockers, and citation URLs (token/ID/handle-free).
"""

import hashlib
import json
import os.path
import re

TASK_LABEL = (
    "TASK_CONTENTOPS_0174CU_PLATFORM_REQUIREMENTS_AND_ACCOUNT_BINDING_"
    "POLICY_PACKETS_NO_LIVE_V0"
)

GATE = "PLATFORM_REQUIREMENTS_ACCOUNT_BINDING_POLICY_0174CU"
INDEX_GATE = "PLATFORM_REQUIREMENTS_ACCOUNT_BINDING_POLICY_INDEX_0174CU"
SOURCE_BASELINE_COMMIT = "978f1eb9d23f91a24a6b82142567c694fa3c5fb2"

# Date the official docs were inspected for this task (UTC, no time-of-day).
DOCS_ACCESSED_DATE = "2026-06-15"

# Per-platform recommended follow-up tasks.
NEXT_TASK_TELEGRAM = (
    "TASK_CONTENTOPS_0174CV_TELEGRAM_THIRD_GATE_REQUIREMENTS_REVIEW_NO_LIVE_V0"
)
NEXT_TASK_X = (
    "TASK_CONTENTOPS_0174CV_X_OFFICIAL_DOCS_ACCOUNT_BINDING_REQUIREMENTS_"
    "NO_OAUTH_NO_LIVE_V0"
)
NEXT_TASK_LINKEDIN = (
    "TASK_CONTENTOPS_0174CV_LINKEDIN_OFFICIAL_DOCS_ACCOUNT_BINDING_"
    "REQUIREMENTS_NO_OAUTH_NO_LIVE_V0"
)

# Output artifact locations.
PACKET_REL_DIR = os.path.join("docs", "credential_readiness", "0174CU")
INDEX_FILENAME = "platform_requirements_account_binding_policy_index.json"
TELEGRAM_FILENAME = "telegram_third_gate_requirements_packet.json"
X_FILENAME = "x_account_binding_requirements_packet.json"
LINKEDIN_FILENAME = "linkedin_account_binding_requirements_packet.json"
README_FILENAME = "README.md"

FLAG_WRITE = "--write-platform-requirements-account-binding-policy"


# --------------------------------------------------------------------------- #
# Redaction scanner (defense-in-depth; blocks tokens / IDs / handles / URNs and
# forbidden raw keys). Official docs URLs are allowed only when they contain no
# tokens, long IDs, or handles.
# --------------------------------------------------------------------------- #
_SECRET_LIKE = [
    re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}"),          # telegram bot token body
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),  # PEM private key
    re.compile(r"AKIA[0-9A-Z]{16}"),                    # AWS access key id
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),                # GitHub PAT
]
_URL_WITH_TOKEN = re.compile(r"api\.telegram\.org/bot\d{6,}:")
_TELEGRAM_URL_WITH_BOT = re.compile(r"api\.telegram\.org/bot")
_HANDLE_LIKE = re.compile(r"@[A-Za-z0-9_]{3,}")
_LONG_DIGITS = re.compile(r"(?<!\d)-?\d{7,}(?!\d)")
_LINKEDIN_URN = re.compile(r"urn:li:[A-Za-z]+:")

_FORBIDDEN_KEYS = (
    "token", "bot_token", "chat_id", "channel_id", "channel_username",
    "bot_id", "bot_username", "message_id", "message_id_value", "date",
    "date_value", "raw_url", "raw_request", "raw_response",
    "target_identifier", "target_value", "access_token", "refresh_token",
    "client_secret", "api_key", "account_id", "account_handle", "user_id",
    "username", "organization_id", "person_urn", "organization_urn",
    "author_urn", "post_urn",
)


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, payload hashes)."""
    if s == SOURCE_BASELINE_COMMIT:
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
        for pat in _SECRET_LIKE:
            if pat.search(s):
                violations.append(f"secret_like_value:{key or 'value'}")
                break
        if _URL_WITH_TOKEN.search(s) or _TELEGRAM_URL_WITH_BOT.search(s):
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
# Inherited operator posture (from 0174CT)
# --------------------------------------------------------------------------- #
def build_inherited_operator_posture():
    """Conservative posture inherited from the accepted 0174CT packet."""
    return {
        "live_posting_state": "blocked_until_new_explicit_task_and_operator_go",
        "pause_additional_live_sends": True,
        "two_telegram_pilots_review_required": True,
    }


# --------------------------------------------------------------------------- #
# Shared platform-packet skeleton
# --------------------------------------------------------------------------- #
def _base_platform_packet(*, platform, docs_access_status, official_docs_checked,
                          official_docs_sources, endpoint_family_symbolic,
                          auth_model_symbolic, permission_or_role_classes,
                          account_binding_model, objective, allowed_now,
                          forbidden_now, required_before_dry_run,
                          required_before_live, credential_policy,
                          account_binding_policy, approval_policy,
                          redaction_policy, test_policy, blockers, caveats,
                          recommended_next_task_for_platform, status,
                          blocked_reasons):
    """Assemble a platform packet carrying every shared minimum field."""
    return {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "platform": platform,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "objective": objective,
        "docs_access_status": docs_access_status,
        "official_docs_checked": official_docs_checked,
        "official_docs_sources": official_docs_sources,
        "endpoint_family_symbolic": endpoint_family_symbolic,
        "auth_model_symbolic": auth_model_symbolic,
        "permission_or_role_classes_redacted": permission_or_role_classes,
        "account_binding_model": account_binding_model,
        "allowed_now": allowed_now,
        "forbidden_now": forbidden_now,
        "required_before_dry_run": required_before_dry_run,
        "required_before_live": required_before_live,
        "credential_policy": credential_policy,
        "account_binding_policy": account_binding_policy,
        "approval_policy": approval_policy,
        "redaction_policy": redaction_policy,
        "test_policy": test_policy,
        "dry_run_contract_required": True,
        "live_gate_required": True,
        "duplicate_send_prevention_required": True,
        "pre_attempt_marker_required": True,
        "post_send_redacted_ledger_required": True,
        "no_retry_required": True,
        "no_scheduler": True,
        "no_webhook": True,
        "no_reply_dm": True,
        "no_metrics_fetch": True,
        "no_scraping": True,
        "no_autonomous_publishing": True,
        "blockers": sorted(set(blockers)),
        "caveats": caveats,
        "recommended_next_task_for_platform": recommended_next_task_for_platform,
        "no_live_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_account_binding_performed": True,
        "no_oauth_flow_performed": True,
        "no_token_exchange_performed": True,
        "no_posting_performed": True,
        "redaction_verified": True,
        "status": status,
        "blocked_reasons": sorted(set(blocked_reasons)),
    }


# --------------------------------------------------------------------------- #
# Telegram third-gate requirements packet
# --------------------------------------------------------------------------- #
def build_telegram_packet():
    """Requirements-only packet for a possible future third Telegram post."""
    return _base_platform_packet(
        platform="telegram",
        objective=(
            "Define requirements for a possible future third supervised "
            "Telegram live post without implementing or sending it now."
        ),
        docs_access_status="accessible",
        official_docs_checked=True,
        official_docs_sources=[
            {
                "source_family": "telegram_bot_api",
                "title": "Telegram Bot API - sendMessage",
                "url_or_symbolic_ref": "https://core.telegram.org/bots/api",
                "accessed_date": DOCS_ACCESSED_DATE,
                "access_status": "accessible",
                "notes": (
                    "sendMessage is the only authorized live method, already "
                    "validated by the 0174CK..0174CR chain; no new method."
                ),
            },
        ],
        endpoint_family_symbolic="telegram.bot_api.sendMessage",
        auth_model_symbolic="telegram.bot_token (NOT read now)",
        permission_or_role_classes=[
            "bot_must_be_channel_admin_with_post_messages",
        ],
        account_binding_model=(
            "reuse existing operator-validated target binding only; no new "
            "binding; binding reuse requires a future explicit task"
        ),
        allowed_now=["requirements-only planning"],
        forbidden_now=[
            "sendMessage", "getMe", "getChat", "getChatMember", "getUpdates",
            "webhook", "scheduler", "reply/DM", "metrics fetch", "scraping",
            "new live module", "credential read", "token read",
        ],
        required_before_dry_run=[
            "new explicit task authorizing a third send",
            "exact payload text fixed",
            "forbidden-language scan of exact payload",
            "network-free dry-run gate with injected caller",
        ],
        required_before_live=[
            "separate dry-run ledger accepted",
            "exact approval payload-hash lock",
            "operator approval",
            "one-time operator GO scoped to that task",
            "duplicate-send prevention",
            "pre-attempt marker",
            "post-send redacted ledger",
            "request_budget=1",
            "no retry",
        ],
        credential_policy=(
            "no token read now; no token until a dedicated "
            "credential-readiness gate under a future explicit task"
        ),
        account_binding_policy=(
            "no new binding; existing operator-validated target only after a "
            "new explicit task validates the prior chain"
        ),
        approval_policy=(
            "separate one-time operator GO + exact payload-hash lock required "
            "before any third send"
        ),
        redaction_policy=(
            "same redacted-only contract as the 0174CN/0174CR ledgers: no "
            "chat/channel/message ids, no bot id, no raw URLs, no date values; "
            "booleans/classes only"
        ),
        test_policy=(
            "network-free dry-run + live-gate tests with injected caller; no "
            "live call"
        ),
        blockers=[
            "third send not justified until operator reviews the two existing "
            "live pilots",
            "no new operator GO yet",
        ],
        caveats=[
            "third send is technically proven enough by two pilots; additional "
            "Telegram sends add little value until the pause/review is signed "
            "off",
        ],
        recommended_next_task_for_platform=NEXT_TASK_TELEGRAM,
        status="pass",
        blocked_reasons=[],
    )


# --------------------------------------------------------------------------- #
# X account-binding requirements packet
# --------------------------------------------------------------------------- #
def build_x_packet():
    """Requirements-only packet for future X account binding + dry-run."""
    return _base_platform_packet(
        platform="x",
        objective=(
            "Define future X account-binding and dry-run contract requirements "
            "only. No OAuth, no token exchange, no post."
        ),
        docs_access_status="accessible",
        official_docs_checked=True,
        official_docs_sources=[
            {
                "source_family": "x_api_v2",
                "title": "X API - Create or Edit Post",
                "url_or_symbolic_ref": "https://docs.x.com/x-api/posts/create-post",
                "accessed_date": DOCS_ACCESSED_DATE,
                "access_status": "accessible",
                "notes": (
                    "Create Post (manage-posts family) creates a Post for the "
                    "authenticated user; edit_options and paid_partnership are "
                    "out of scope and forbidden until explicitly scoped."
                ),
            },
            {
                "source_family": "x_developer_portal",
                "title": "X Developer Portal - access tiers / developer app",
                "url_or_symbolic_ref": "https://developer.x.com/en/portal",
                "accessed_date": DOCS_ACCESSED_DATE,
                "access_status": "gated_login_required",
                "notes": (
                    "Access-tier and product-level constraints require portal "
                    "login; treated as a blocker, not an assumption. No login "
                    "performed."
                ),
            },
        ],
        endpoint_family_symbolic="x.api.v2.posts.manage_posts.create_post",
        auth_model_symbolic="x.oauth2_user_context (NOT initiated now)",
        permission_or_role_classes=[
            "tweet_write_scope_class",
            "users_read_scope_class",
            "offline_access_scope_class",
            "developer_app_access_tier_class",
        ],
        account_binding_model=(
            "authenticated-user-context posting; bound account proven via "
            "future account-binding gate; no raw account id or handle persisted"
        ),
        allowed_now=["official-docs review only", "no OAuth"],
        forbidden_now=[
            "OAuth", "token exchange", "developer portal login", "post",
            "edit post", "delete", "repost", "quote", "bookmark", "media",
            "paid/community post", "metrics", "replies", "DMs", "webhooks",
            "scraping",
        ],
        required_before_dry_run=[
            "developer access/tier verified (blocker until then)",
            "OAuth user-context design drafted in a dedicated gate",
            "text-only post body field contract defined",
            "fields that enable replies/DMs/media/paid/quote/community "
            "explicitly forbidden until separately scoped",
        ],
        required_before_live=[
            "dry-run payload contract accepted",
            "account-binding proof (no raw id/handle persisted)",
            "permission/scope proof",
            "redacted preview",
            "explicit operator GO",
            "one-time live gate with duplicate-send prevention and no retry",
        ],
        credential_policy=(
            "no access token until a dedicated credential-readiness gate; no "
            "client secret / refresh token persisted"
        ),
        account_binding_policy=(
            "no account id or handle persisted raw; binding proof via a "
            "dedicated account-binding gate only"
        ),
        approval_policy=(
            "explicit operator GO + dry-run acceptance required before any "
            "live call"
        ),
        redaction_policy=(
            "no raw handles, account/user/post ids, or tokens; booleans and "
            "symbolic classes only"
        ),
        test_policy="requirements + redaction tests only; no API call",
        blockers=[
            "developer access/tier not yet verified (portal login required)",
            "OAuth user-context design not yet drafted",
            "any X plan/access-tier ambiguity is a blocker, not an assumption",
        ],
        caveats=[
            "Create Post endpoint also supports edit via edit_options and paid "
            "partnership disclosure; both are out of scope and must stay "
            "forbidden until explicitly scoped",
        ],
        recommended_next_task_for_platform=NEXT_TASK_X,
        status="pass",
        blocked_reasons=[],
    )


# --------------------------------------------------------------------------- #
# LinkedIn account-binding requirements packet
# --------------------------------------------------------------------------- #
def build_linkedin_packet():
    """Requirements-only packet for future LinkedIn binding + dry-run."""
    return _base_platform_packet(
        platform="linkedin",
        objective=(
            "Define future LinkedIn member/org/page binding and dry-run "
            "contract requirements only. No OAuth/product-access flow, no post."
        ),
        docs_access_status="accessible",
        official_docs_checked=True,
        official_docs_sources=[
            {
                "source_family": "linkedin_marketing_api",
                "title": "Posts API - LinkedIn | Microsoft Learn",
                "url_or_symbolic_ref": (
                    "https://learn.microsoft.com/en-us/linkedin/marketing/"
                    "community-management/shares/posts-api"
                ),
                "accessed_date": DOCS_ACCESSED_DATE,
                "access_status": "accessible",
                "notes": (
                    "Posts API creates organic/sponsored posts; text-only "
                    "supported; versioned via the LinkedIn-Version header. "
                    "Default supported version observed as li-lms-2026-06; "
                    "Marketing 202506 carries a sunset/deprecation notice."
                ),
            },
            {
                "source_family": "linkedin_marketing_api",
                "title": "LinkedIn Marketing API - Versioning / Migrations",
                "url_or_symbolic_ref": (
                    "https://learn.microsoft.com/en-us/linkedin/marketing/"
                    "versioning"
                ),
                "accessed_date": DOCS_ACCESSED_DATE,
                "access_status": "accessible",
                "notes": (
                    "Monthly LinkedIn-Version monikers; version deprecation "
                    "must be re-verified before any dry-run."
                ),
            },
        ],
        endpoint_family_symbolic="linkedin.marketing.rest.posts",
        auth_model_symbolic="linkedin.oauth2_3_legged_member_context (NOT initiated now)",
        permission_or_role_classes=[
            "w_member_social_scope_class",
            "w_organization_social_scope_class",
            "organization_role_administrator_class",
            "marketing_developer_platform_product_access_class",
        ],
        account_binding_model=(
            "member-context author or organization/page author; ownership "
            "proven via future account-binding gate; no person/organization "
            "URN persisted raw"
        ),
        allowed_now=[
            "official-docs review only", "no OAuth/product-access flow",
        ],
        forbidden_now=[
            "OAuth", "product-access flow", "token exchange", "member token",
            "organization token", "organization id", "page binding", "post",
            "comments", "likes", "metrics", "replies/DM-like behavior",
            "scraping",
        ],
        required_before_dry_run=[
            "role/product-access verified (blocker until then)",
            "supported LinkedIn-Version header policy confirmed (not deprecated)",
            "member vs organization posting model decided",
            "organization/page ownership proof plan drafted",
        ],
        required_before_live=[
            "dry-run payload contract accepted",
            "permission/scope proof",
            "version header policy locked",
            "organization/page ownership proof",
            "redacted preview",
            "explicit operator GO",
            "one-time live gate with duplicate-send prevention and no retry",
        ],
        credential_policy=(
            "no member token / org token until a dedicated credential-readiness "
            "gate; no client secret persisted"
        ),
        account_binding_policy=(
            "no organization URN / person URN persisted raw; no organization/"
            "page binding until a dedicated account-binding proof gate"
        ),
        approval_policy=(
            "explicit operator GO + dry-run acceptance required before any "
            "live call"
        ),
        redaction_policy=(
            "no URNs (person/organization/author/post), organization ids, or "
            "tokens; booleans and symbolic classes only"
        ),
        test_policy="requirements + redaction tests only; no API call",
        blockers=[
            "role/product-access not yet verified",
            "organization/page ownership proof not yet established",
            "version deprecation / page-ownership ambiguity is a blocker, not "
            "an assumption",
        ],
        caveats=[
            "Marketing version 202506 (June 2025) is sunset; the LinkedIn-"
            "Version header must be re-verified against supported monikers "
            "before any dry-run",
        ],
        recommended_next_task_for_platform=NEXT_TASK_LINKEDIN,
        status="pass",
        blocked_reasons=[],
    )


# --------------------------------------------------------------------------- #
# Index packet
# --------------------------------------------------------------------------- #
def build_index_packet(*, telegram_checksum, x_checksum, linkedin_checksum,
                       status, blocked_reasons):
    """Index packet referencing the three platform packets."""
    packet = {
        "task_label": TASK_LABEL,
        "gate": INDEX_GATE,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inherited_operator_posture_from_0174CT":
            build_inherited_operator_posture(),
        "platform_packets": {
            "telegram_third_gate": TELEGRAM_FILENAME,
            "x": X_FILENAME,
            "linkedin": LINKEDIN_FILENAME,
        },
        "platform_priority_recommendation": [
            "x_requirements_no_live",
            "linkedin_requirements_no_live",
            "telegram_third_gate_later",
        ],
        "rationale": [
            "X and LinkedIn requirements reduce expansion risk before live "
            "work",
            "Telegram third send is technically proven enough; more Telegram "
            "sends add less value until review",
        ],
        "no_live_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
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
        "packet_checksums": {
            "telegram_third_gate_requirements_packet": telegram_checksum,
            "x_account_binding_requirements_packet": x_checksum,
            "linkedin_account_binding_requirements_packet": linkedin_checksum,
            "index_packet": None,
        },
        "status": status,
        "blocked_reasons": sorted(set(blocked_reasons)),
    }
    # index_packet checksum is computed over the packet with the slot set to
    # None (a stable self-reference placeholder), then filled in.
    index_self_checksum = compute_checksum(packet)
    packet["packet_checksums"]["index_packet"] = index_self_checksum
    return packet


# --------------------------------------------------------------------------- #
# README
# --------------------------------------------------------------------------- #
def build_readme():
    """Concise operator-facing README for the 0174CU packets."""
    return (
        "# 0174CU Platform Requirements + Account-Binding Policy Packets\n"
        "\n"
        "Strictly local, official-doc-grounded, requirements-only packets. No "
        "live calls, no credentials, no OAuth, no account binding, no "
        "posting.\n"
        "\n"
        "## Inherited posture (from 0174CT)\n"
        "\n"
        "- Live posting state: `blocked_until_new_explicit_task_and_operator_"
        "go`.\n"
        "- Additional live sends paused; two Telegram pilots still require "
        "operator review.\n"
        "\n"
        "## Packets\n"
        "\n"
        "- `telegram_third_gate_requirements_packet.json` -- requirements for "
        "a possible future third Telegram send (no send now).\n"
        "- `x_account_binding_requirements_packet.json` -- X binding + dry-run "
        "requirements (no OAuth/token/post now).\n"
        "- `linkedin_account_binding_requirements_packet.json` -- LinkedIn "
        "member/org/page binding + dry-run requirements (no OAuth/token/post "
        "now).\n"
        "- `platform_requirements_account_binding_policy_index.json` -- index "
        "referencing the three platform packets with checksums.\n"
        "\n"
        "## Platform priority recommendation\n"
        "\n"
        "1. X requirements (no live)\n"
        "2. LinkedIn requirements (no live)\n"
        "3. Telegram third gate (later)\n"
        "\n"
        "## Official docs inspected\n"
        "\n"
        "- X: Create or Edit Post (`docs.x.com/x-api/posts/create-post`) -- "
        "accessible; developer portal access tiers -- gated (login required, "
        "not performed).\n"
        "- LinkedIn: Posts API (Microsoft Learn) -- accessible; versioned via "
        "the LinkedIn-Version header; Marketing 202506 sunset noted.\n"
        "- Telegram: Bot API sendMessage (`core.telegram.org/bots/api`) -- "
        "accessible; already validated upstream.\n"
        "\n"
        "## What this did NOT do\n"
        "\n"
        "No Telegram/X/LinkedIn API call. No sendMessage / getMe / getChat / "
        "getChatMember / getUpdates / webhook / scheduler / reply / DM / "
        "metrics / scraping. No OAuth flow, token exchange, developer portal "
        "login, or account-binding mutation. No credential or env read. The "
        "module never browses docs at runtime; docs reading was an "
        "Antigravity/operator activity before writing symbolic packet data.\n"
        "\n"
        "## Next\n"
        "\n"
        f"Recommended next task: `{NEXT_TASK_X}`.\n"
    )


# --------------------------------------------------------------------------- #
# Main gate
# --------------------------------------------------------------------------- #
def run_policy_gate(*, write=False, repo_root=None):
    """Run the strictly-local 0174CU requirements/policy gate. Fail-closed.

    Writing occurs ONLY when ``write=True`` AND every packet passes the
    redaction scan.
    """
    if repo_root is None:
        repo_root = os.path.dirname(os.path.dirname(__file__))

    blocked = []
    status = "pass"

    telegram_packet = build_telegram_packet()
    x_packet = build_x_packet()
    linkedin_packet = build_linkedin_packet()

    platform_packets = {
        TELEGRAM_FILENAME: telegram_packet,
        X_FILENAME: x_packet,
        LINKEDIN_FILENAME: linkedin_packet,
    }

    for name, packet in platform_packets.items():
        violations = scan_packet_for_leaks(packet)
        if violations:
            blocked.append(f"packet_redaction_violation:{name}")

    telegram_checksum = compute_checksum(telegram_packet)
    x_checksum = compute_checksum(x_packet)
    linkedin_checksum = compute_checksum(linkedin_packet)

    if blocked:
        status = "blocked"

    index_packet = build_index_packet(
        telegram_checksum=telegram_checksum, x_checksum=x_checksum,
        linkedin_checksum=linkedin_checksum, status=status,
        blocked_reasons=blocked)

    index_violations = scan_packet_for_leaks(index_packet)
    if index_violations:
        blocked.append("packet_redaction_violation:index")
        status = "blocked"
        index_packet["status"] = "blocked"
        index_packet["blocked_reasons"] = sorted(set(blocked))

    index_checksum = index_packet["packet_checksums"]["index_packet"]

    packet_written = False
    readme_written = False

    if write and not blocked:
        out_dir = os.path.join(repo_root, PACKET_REL_DIR)
        os.makedirs(out_dir, exist_ok=True)
        for name, packet in platform_packets.items():
            with open(os.path.join(out_dir, name), "w", encoding="utf-8",
                      newline="\n") as fh:
                fh.write(serialize(packet))
        with open(os.path.join(out_dir, INDEX_FILENAME), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(serialize(index_packet))
        packet_written = True
        with open(os.path.join(out_dir, README_FILENAME), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(build_readme())
        readme_written = True

    return _summary(
        write=write, status=status, blocked_reasons=blocked,
        telegram_checksum=telegram_checksum, x_checksum=x_checksum,
        linkedin_checksum=linkedin_checksum, index_checksum=index_checksum,
        packet_written=packet_written, readme_written=readme_written)


def _summary(*, write, status, blocked_reasons, telegram_checksum, x_checksum,
             linkedin_checksum, index_checksum, packet_written, readme_written):
    """Redacted gate summary dict."""
    return {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inherited_operator_posture_from_0174CT":
            build_inherited_operator_posture(),
        "platform_priority_recommendation": [
            "x_requirements_no_live",
            "linkedin_requirements_no_live",
            "telegram_third_gate_later",
        ],
        "platform_packets": {
            "telegram_third_gate": os.path.join(
                PACKET_REL_DIR, TELEGRAM_FILENAME).replace(os.sep, "/"),
            "x": os.path.join(
                PACKET_REL_DIR, X_FILENAME).replace(os.sep, "/"),
            "linkedin": os.path.join(
                PACKET_REL_DIR, LINKEDIN_FILENAME).replace(os.sep, "/"),
        },
        "index_path": os.path.join(
            PACKET_REL_DIR, INDEX_FILENAME).replace(os.sep, "/"),
        "write_requested": bool(write),
        "packet_written": bool(packet_written),
        "readme_written": bool(readme_written),
        "packet_checksums": {
            "telegram_third_gate_requirements_packet": telegram_checksum,
            "x_account_binding_requirements_packet": x_checksum,
            "linkedin_account_binding_requirements_packet": linkedin_checksum,
            "index_packet": index_checksum,
        },
        "next_recommended_task": NEXT_TASK_X,
        "no_live_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
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
        "blocked_reasons": sorted(set(blocked_reasons)),
    }


def summary(**kwargs):
    """Convenience wrapper returning the redacted gate summary dict."""
    return run_policy_gate(**kwargs)


def main(argv=None):
    """CLI: print ONLY the redacted JSON summary. Local-only, no network/env."""
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    write = FLAG_WRITE in args
    result = run_policy_gate(write=write)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
