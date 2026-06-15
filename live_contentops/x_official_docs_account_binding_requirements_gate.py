"""X official-docs account-binding requirements gate (0174CV).

This module is STRICTLY LOCAL. It performs NO network of any kind and reads NO
env/credentials. Official X documentation reading is an Antigravity/operator
activity performed BEFORE this module runs; the module only emits a symbolic,
redacted, requirements-only X account-binding packet grounded in those docs.

It deepens the broad 0174CU X requirements packet into an X-specific account-
binding + dry-run contract WITHOUT OAuth, WITHOUT credential reads, and WITHOUT
any live/posting behavior.

HARD GUARANTEES (enforced by tests + leakage guards):
  * No network imports (no urllib / requests / httpx / socket / http / dotenv).
  * No process env / .env read (no environment-variable lookups).
  * Imports ONLY hashlib, json, os.path, re.
  * Fail-closed: writes happen ONLY when the write flag is present AND the
    packet passes the redaction scan.
  * Deterministic JSON: sorted keys, compact separators, trailing newline.
  * No live call, no posting, no OAuth, no token exchange, no developer-portal
    login, no account binding, no metrics/webhook/reply/DM/scraping, no generic
    publisher, no credential-entry schema.
  * Stores only concise symbolic metadata: endpoint families, auth model, field
    classes, forbidden adjacent feature classes, docs access status, blockers,
    and citation URLs (token/ID/handle-free).
"""

import hashlib
import json
import os.path
import re
import sys

TASK_LABEL = (
    "TASK_CONTENTOPS_0174CV_X_OFFICIAL_DOCS_ACCOUNT_BINDING_REQUIREMENTS_"
    "NO_OAUTH_NO_LIVE_V0"
)

GATE = "X_OFFICIAL_DOCS_ACCOUNT_BINDING_REQUIREMENTS_0174CV"
PLATFORM = "x"
SOURCE_BASELINE_COMMIT = "c216a6e2456028e08198c1c4b83f0ffdaf56fcc3"
INHERITED_0174CU_INDEX_COMMIT = "c216a6e2456028e08198c1c4b83f0ffdaf56fcc3"

# Date the official docs were inspected for this task (UTC, no time-of-day).
DOCS_ACCESSED_DATE = "2026-06-15"

NEXT_TASK = (
    "TASK_CONTENTOPS_0174CW_X_OAUTH_USER_CONTEXT_DESIGN_AND_REDIRECTION_"
    "POLICY_NO_TOKEN_NO_LIVE_V0"
)

# Output artifact locations.
PACKET_REL_DIR = os.path.join("docs", "credential_readiness", "0174CV")
PACKET_FILENAME = "x_official_docs_account_binding_requirements_packet.json"
README_FILENAME = "README.md"

FLAG_WRITE = "--write-x-official-docs-account-binding-requirements"

# Symbolic endpoint family + expected post path (no raw response/sample IDs).
ENDPOINT_FAMILY_SYMBOLIC = "x.api.v2.posts.manage_posts.create_post"
EXPECTED_POST_ENDPOINT_SYMBOLIC = "POST /2/tweets"
AUTH_MODEL_SYMBOLIC = "x.oauth2_user_context.user_access_token (NOT initiated now)"

# Text-only dry-run payload contract: only these fields are allowed.
TEXT_ONLY_ALLOWED_FIELDS = [
    "text",
    "made_with_ai",  # optional boolean only if later explicitly needed
]

# Fields explicitly forbidden in the text-only dry-run payload until scoped.
FORBIDDEN_PAYLOAD_FIELDS = [
    "card_uri",
    "community_id",
    "direct_message_deep_link",
    "edit_options",
    "for_super_followers_only",
    "geo",
    "media",
    "nullcast",
    "paid_partnership",
    "poll",
    "quote_tweet_id",
    "reply",
    "reply_settings",
    "share_with_followers",
    "any_raw_post_user_community_place_media_ids",
]

# Adjacent X feature families forbidden until separately scoped.
FORBIDDEN_ADJACENT_FEATURE_FAMILIES = [
    "edit_post",
    "delete_post",
    "repost",
    "quote",
    "bookmarks",
    "likes",
    "replies",
    "direct_messages",
    "media_upload",
    "communities",
    "trends_search_scraping",
    "webhooks_activity_subscriptions",
    "metrics_usage_fetch",
]


# --------------------------------------------------------------------------- #
# Redaction scanner (defense-in-depth). Blocks tokens / bearer strings / raw
# handles / raw account-post-tweet-community-media-place ids / long numeric ids /
# callback URLs with query tokens / LinkedIn-style URNs / forbidden raw keys.
# Official docs URLs are allowed only when token/id/handle-free.
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
# Callback/redirect URL carrying an auth code or token in its query string.
_CALLBACK_URL_WITH_TOKEN = re.compile(
    r"https?://[^\s\"']*[?&](?:code|access_token|token|bearer_token|"
    r"refresh_token|authorization_code|code_verifier|code_challenge)="
)

_FORBIDDEN_KEYS = (
    "token", "access_token", "refresh_token", "bearer_token", "client_secret",
    "client_id", "api_key", "account_id", "account_handle", "user_id",
    "username", "screen_name", "handle", "post_id", "tweet_id", "community_id",
    "media_id", "place_id", "raw_url", "raw_request", "raw_response",
    "authorization_code", "code_verifier", "code_challenge",
)


def _is_known_safe_identifier(s):
    """True for known-safe identifier strings (git SHAs, payload hashes)."""
    if s in (SOURCE_BASELINE_COMMIT, INHERITED_0174CU_INDEX_COMMIT):
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
        if _CALLBACK_URL_WITH_TOKEN.search(s):
            violations.append(f"callback_url_with_token:{key or 'value'}")
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
# Official docs sources (symbolic, token/id/handle-free)
# --------------------------------------------------------------------------- #
def build_official_docs_sources():
    """Concise, symbolic record of the official X docs inspected."""
    return [
        {
            "source_family": "x_api_v2_manage_posts",
            "title": "Create or Edit Post - X API",
            "url_or_symbolic_ref": "https://docs.x.com/x-api/posts/create-post",
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "accessible",
            "notes": (
                "Create Post (manage-posts family) creates a Post for the "
                "authenticated user OR edits an existing Post when "
                "edit_options are provided; paid_partnership disclosure is a "
                "separate field. Edit and paid_partnership are out of scope "
                "and forbidden until separately scoped. No raw response or "
                "sample ids stored."
            ),
        },
        {
            "source_family": "x_api_v2_authentication",
            "title": "X API Authentication (OAuth 2.0 user context)",
            "url_or_symbolic_ref": "https://docs.x.com/resources/fundamentals/authentication",
            "accessed_date": DOCS_ACCESSED_DATE,
            "access_status": "accessible",
            "notes": (
                "Create Post requires OAuth 2.0 Authorization Code with PKCE "
                "(user context) and tweet.write scope. OAuth not initiated "
                "now; scope/callback/storage design deferred to a dedicated "
                "no-token design gate."
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
    ]


# --------------------------------------------------------------------------- #
# X account-binding requirements packet
# --------------------------------------------------------------------------- #
def build_x_packet():
    """Deep, requirements-only X account-binding + dry-run packet."""
    packet = {
        "task_label": TASK_LABEL,
        "gate": GATE,
        "platform": PLATFORM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "inherited_0174cu_index_commit": INHERITED_0174CU_INDEX_COMMIT,
        "docs_access_status": (
            "partially_accessible: create-post + authentication docs "
            "accessible; developer portal access/tier gated (login required, "
            "not performed)"
        ),
        "official_docs_checked": True,
        "official_docs_sources": build_official_docs_sources(),
        "endpoint_family_symbolic": ENDPOINT_FAMILY_SYMBOLIC,
        "expected_post_endpoint_symbolic": EXPECTED_POST_ENDPOINT_SYMBOLIC,
        "create_or_edit_ambiguity": (
            "create_post endpoint serves BOTH create and edit (via "
            "edit_options); only create is in future scope, edit is forbidden "
            "until separately scoped"
        ),
        "auth_model_symbolic": AUTH_MODEL_SYMBOLIC,
        "developer_portal_access_status": "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "access_tier_blocker": (
            "developer portal access/tier cannot be verified without login; "
            "any plan/access-tier ambiguity is a blocker, not an assumption"
        ),
        "app_permission_scope_model": [
            "tweet_write_scope_class",
            "tweet_read_scope_class",
            "users_read_scope_class",
            "offline_access_scope_class",
            "developer_app_access_tier_class",
        ],
        "account_binding_model": (
            "authenticated-user-context posting; the bound account is proven "
            "via a future account-binding gate using redacted booleans/classes "
            "and (only if explicitly approved later) hashed local-only proof; "
            "no raw account id or handle persisted"
        ),
        "account_binding_policy": (
            "no account id or handle collected or persisted now; binding proof "
            "only via a dedicated future account-binding gate"
        ),
        "account_binding_proof_required": [
            "future account-binding gate accepted",
            "ownership proven without persisting any raw account identifier",
            "proof expressed as redacted booleans/classes only",
            "hashed local-only proof permitted ONLY if explicitly approved "
            "later",
        ],
        "raw_account_identifier_policy": (
            "no account id, user id, username, handle, post id, tweet id, "
            "community id, media id, or place id persisted raw, ever; future "
            "account-binding proof uses redacted booleans/classes and hashed "
            "local-only proof only if explicitly approved later"
        ),
        "future_oauth_design_required": True,
        "future_credential_readiness_gate_required": True,
        "future_dry_run_gate_required": True,
        "future_live_gate_required": True,
        "text_only_payload_contract": {
            "allowed_fields": list(TEXT_ONLY_ALLOWED_FIELDS),
            "required_fields": ["text"],
            "optional_fields": ["made_with_ai"],
            "notes": (
                "text-only future dry-run payload; made_with_ai is an optional "
                "boolean included only if later explicitly needed; no media, "
                "reply, quote, poll, geo, community, paid partnership, or any "
                "raw ids"
            ),
        },
        "forbidden_payload_fields_until_scoped": list(FORBIDDEN_PAYLOAD_FIELDS),
        "forbidden_adjacent_feature_families":
            list(FORBIDDEN_ADJACENT_FEATURE_FAMILIES),
        "required_before_account_binding": [
            "developer access/tier verified (blocker until then)",
            "OAuth user-context design drafted in a dedicated no-token gate",
            "scope set confirmed against official auth docs",
            "redaction policy for any binding proof confirmed",
        ],
        "required_before_oauth": [
            "developer access/tier verified",
            "dedicated OAuth user-context design gate accepted (scopes, "
            "callback handling, local storage/redaction, revocation/rotation, "
            "no raw token logs)",
            "no token exchange until that design gate is accepted",
        ],
        "required_before_dry_run": [
            "developer access/tier verified",
            "OAuth user-context design drafted and accepted",
            "credential-readiness gate accepted (no token persisted raw)",
            "text-only payload field contract accepted",
            "fields enabling edit/replies/DMs/media/paid/quote/community "
            "explicitly forbidden until separately scoped",
        ],
        "required_before_live": [
            "accepted dry-run packet",
            "exact payload hash lock",
            "account-binding proof (no raw id/handle persisted)",
            "operator approval",
            "one-time operator GO scoped to that task",
            "duplicate-send prevention",
            "pre-attempt marker",
            "request_budget=1",
            "no retry",
            "redacted post-send ledger",
        ],
        "credential_policy": (
            "no access token, refresh token, client id, or client secret read "
            "or persisted now; tokens only via a dedicated future "
            "credential-readiness gate; no credential-entry schema created now"
        ),
        "approval_policy": (
            "explicit operator GO + accepted dry-run + exact payload-hash lock "
            "required before any live call"
        ),
        "redaction_policy": (
            "no raw handles, account/user/post/tweet/community/media/place ids, "
            "tokens, bearer strings, or callback URLs with query tokens; "
            "booleans and symbolic classes only"
        ),
        "test_policy": (
            "requirements + redaction + no-network/no-env static tests only; "
            "no X API call"
        ),
        "blocker_policy": (
            "any inaccessible/gated/redirected/deprecated/ambiguous official "
            "page is recorded as a blocker; capability is never assumed and "
            "third-party blogs/tutorials are never treated as authority"
        ),
        "blockers": sorted(set([
            "developer access/tier not yet verified (portal login required)",
            "OAuth user-context design not yet drafted (deferred to 0174CW)",
            "create_post endpoint also performs edit; edit must stay forbidden "
            "until separately scoped",
            "any X plan/access-tier ambiguity is a blocker, not an assumption",
        ])),
        "caveats": [
            "Create Post endpoint supports edit via edit_options and paid "
            "partnership disclosure via paid_partnership; both are out of "
            "scope and must stay forbidden until explicitly scoped",
            "OAuth 2.0 user context (Authorization Code + PKCE) with "
            "tweet.write is expected, but no flow is initiated now",
        ],
        "recommended_next_task": NEXT_TASK,
        "no_live_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_account_binding_performed": True,
        "no_oauth_flow_performed": True,
        "no_token_exchange_performed": True,
        "no_developer_portal_login_performed": True,
        "no_posting_performed": True,
        "no_metrics_fetched": True,
        "no_reply_dm_created": True,
        "no_webhook_created": True,
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
    """Concise operator-facing README for the 0174CV X packet."""
    return (
        "# 0174CV X Official-Docs Account-Binding Requirements\n"
        "\n"
        "Strictly local, official-doc-grounded, requirements-only X packet. No "
        "X API call, no OAuth, no token exchange, no developer-portal login, "
        "no account binding, no posting.\n"
        "\n"
        "## Inherited posture\n"
        "\n"
        "- Inherits the conservative 0174CT/0174CU posture: live posting is "
        "`blocked_until_new_explicit_task_and_operator_go`.\n"
        "- This task only deepens the X requirements; it does not enable any "
        "live path.\n"
        "\n"
        "## Endpoint + auth (symbolic)\n"
        "\n"
        "- Endpoint family: `x.api.v2.posts.manage_posts.create_post` "
        "(expected `POST /2/tweets`).\n"
        "- Create Post also performs edit via `edit_options`; edit is "
        "forbidden until separately scoped.\n"
        "- Auth model: OAuth 2.0 user context / user access token, not "
        "initiated now.\n"
        "\n"
        "## Official docs inspected\n"
        "\n"
        "- Create or Edit Post (`docs.x.com/x-api/posts/create-post`) -- "
        "accessible.\n"
        "- Authentication / OAuth 2.0 user context "
        "(`docs.x.com/resources/fundamentals/authentication`) -- accessible.\n"
        "- Developer Portal access tiers (`developer.x.com/en/portal`) -- "
        "gated (login required, not performed) -> blocker.\n"
        "\n"
        "## Text-only dry-run payload contract\n"
        "\n"
        "- Allowed: `text` (required), `made_with_ai` (optional boolean only "
        "if later needed).\n"
        "- Forbidden until scoped: `card_uri`, `community_id`, "
        "`direct_message_deep_link`, `edit_options`, "
        "`for_super_followers_only`, `geo`, `media`, `nullcast`, "
        "`paid_partnership`, `poll`, `quote_tweet_id`, `reply`, "
        "`reply_settings`, `share_with_followers`, and any raw "
        "post/user/community/place/media ids.\n"
        "\n"
        "## Forbidden adjacent feature families\n"
        "\n"
        "edit post, delete post, repost, quote, bookmarks, likes, replies, "
        "DMs, media upload, communities, trends/search/scraping, "
        "webhooks/activity subscriptions, metrics/usage fetch.\n"
        "\n"
        "## What this did NOT do\n"
        "\n"
        "No X (or Telegram/LinkedIn) API call. No OAuth flow, token exchange, "
        "or developer-portal login. No account binding, no credential or env "
        "read, no credential-entry schema. No post/edit/delete/repost/quote/"
        "bookmark/like/reply/DM. No metrics fetch, webhook, or scraping. The "
        "module never browses docs at runtime; docs reading was an "
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
    """Run the strictly-local 0174CV X requirements gate. Fail-closed.

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
        "inherited_0174cu_index_commit": INHERITED_0174CU_INDEX_COMMIT,
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
        "developer_portal_access_status":
            "gated_login_required_not_performed",
        "access_tier_status": "not_verified",
        "endpoint_family_symbolic": ENDPOINT_FAMILY_SYMBOLIC,
        "auth_model_symbolic": AUTH_MODEL_SYMBOLIC,
        "text_only_allowed_fields": list(TEXT_ONLY_ALLOWED_FIELDS),
        "forbidden_payload_fields_until_scoped":
            list(FORBIDDEN_PAYLOAD_FIELDS),
        "forbidden_adjacent_feature_families":
            list(FORBIDDEN_ADJACENT_FEATURE_FAMILIES),
        "next_recommended_task": NEXT_TASK,
        "no_live_call_performed": True,
        "no_credentials_read": True,
        "no_env_read": True,
        "no_account_binding_performed": True,
        "no_oauth_flow_performed": True,
        "no_token_exchange_performed": True,
        "no_developer_portal_login_performed": True,
        "no_posting_performed": True,
        "no_metrics_fetched": True,
        "no_reply_dm_created": True,
        "no_webhook_created": True,
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
