# Capital Chronicle ContentOps final environment format

This document defines final `.env` format for local ContentOps operation.
It is source of truth for future edits to `A:\Capital Chronicle\tools\cc-live-contentops\.env`.

## Core safety rules

1. Keep one key per line: `KEY=value`.
2. Do not duplicate keys.
3. Do not use dotenv interpolation aliases unless parser support is explicitly proven in tests.
4. Do not paste raw token examples or raw secret values into docs, tests, packets, or logs.
5. Do not paste cookies, browser storage, passwords, browser profile dumps, or session IDs.
6. Do not paste service-account JSON blocks into `.env`.
7. Store JSON credentials in `A:\Capital Chronicle\local-secrets` and reference them by path only.
8. Keep browser sessions inside dedicated local profile directories outside repo source.
9. Keep local runtime evidence outside repo source tree.

## Final key naming conventions

- Platform prefix first: `META_GRAPH_`, `THREADS_`, `YOUTUBE_`, `SUBSTACK_`.
- Destination bindings end with `_DESTINATION_BINDING_ID`.
- Credential handles end with `_CREDENTIAL_HANDLE_ID`.
- Local paths end with `_PATH` or `_DIR`.
- Policy IDs end with `_POLICY_ID`.
- Runtime mode keys end with `_AUTOMATION_MODE` or `_ENGINE`.

## Meta Graph app vs Threads app separation

Meta Graph and Threads must stay as separate app identities.
Never reuse `META_GRAPH_APP_ID` for Threads.

```dotenv
META_GRAPH_APP_ID=
META_GRAPH_APP_SECRET=
META_GRAPH_CREDENTIAL_HANDLE_ID=meta_graph_app_01

THREADS_APP_ID=
THREADS_APP_SECRET=
THREADS_CREDENTIAL_HANDLE_ID=threads_official_capital_chronicle_01
```

## Deferred manual platforms

These keys intentionally remain present but empty until operator enables API posting.

```dotenv
X_CLIENT_ID=
X_CLIENT_SECRET=
X_ACCESS_TOKEN=
X_REFRESH_TOKEN=
X_USER_ID=
X_ACCESS_TIER_CLASS=
X_AUTOMATION_MODE=manual_posting

LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
LINKEDIN_ACCESS_TOKEN=
LINKEDIN_MEMBER_URN=
LINKEDIN_ORGANIZATION_URN=
LINKEDIN_AUTOMATION_MODE=pending_passport_business_page

TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
TIKTOK_ACCESS_TOKEN=
TIKTOK_REFRESH_TOKEN=
TIKTOK_OPEN_ID=
TIKTOK_AUTOMATION_MODE=disabled
```

## Substack browser profile strategy

Substack uses browser compose lab mode. No cookie export allowed.
The publication subdomain is `capitalnicle`, not `capitalchronicle`.

```dotenv
SUBSTACK_PUBLICATION_URL=https://capitalnicle.substack.com
SUBSTACK_DASHBOARD_URL=https://capitalnicle.substack.com/publish/home
SUBSTACK_POSTS_LIST_URL=https://capitalnicle.substack.com/publish/posts/published
SUBSTACK_COMPOSE_URL=https://capitalnicle.substack.com/publish/post/new
SUBSTACK_AUTOMATION_MODE=browser_compose_lab
SUBSTACK_BROWSER_PROFILE_PATH=A:\Capital Chronicle\local-browser-profiles\substack-capital-chronicle
```

## Browser operator local dirs

```dotenv
BROWSER_OPERATOR_ENGINE=playwright_cdp
BROWSER_OPERATOR_PROFILE_ROOT=A:\Capital Chronicle\local-browser-profiles
BROWSER_OPERATOR_SCREENSHOT_DIR=A:\Capital Chronicle\local-evidence\screenshots
BROWSER_OPERATOR_AUDIT_DIR=A:\Capital Chronicle\local-evidence\browser-audit
BROWSER_OPERATOR_REQUEST_BUDGET=1
BROWSER_OPERATOR_AUTO_RETRY_ALLOWED=false
BROWSER_OPERATOR_REQUIRES_JIM_GO=true
```

## AI provider metadata gate

Provider keys may exist locally, but provider use must remain policy-gated.
No raw provider key examples are allowed in this document.

```dotenv
AI_PROVIDER_SELECTED=nine_router
AI_PROVIDER_CREDENTIAL_HANDLE_ID=nine_router_local_01
AI_PROVIDER_COST_BUDGET_DAILY_USD=25
AI_PROVIDER_ALLOWED_CONTEXT_CLASSES=public_sources,operator_notes,approved_drafts,redacted_payloads
AI_PROVIDER_FORBIDDEN_CONTEXT_CLASSES=raw_credentials,cookies,session_storage,private_keys,unapproved_market_data
AI_PROVIDER_PROMPT_REDACTION_POLICY_ID=prompt_redaction_policy_v1
```

## Media rights local dirs

```dotenv
MEDIA_RIGHTS_MANIFEST_DIR=A:\Capital Chronicle\local-evidence\media-rights
MEDIA_APPROVED_DOWNLOAD_DIR=A:\Capital Chronicle\approved-media
MEDIA_GENERATED_CARD_DIR=A:\Capital Chronicle\generated-cards
MEDIA_LICENSE_POLICY_ID=media_rights_policy_v1
MEDIA_ATTRIBUTION_REQUIRED_DEFAULT=true
```

## Approval/outbox/audit runtime paths

```dotenv
APPROVAL_LEDGER_PATH=A:\Capital Chronicle\local-evidence\approval-ledger.jsonl
DISPATCH_OUTBOX_PATH=A:\Capital Chronicle\local-evidence\dispatch-outbox.jsonl
AUTOMATION_AUDIT_LOG_PATH=A:\Capital Chronicle\local-evidence\automation-audit.jsonl
PAYLOAD_HASH_LOCK_DIR=A:\Capital Chronicle\local-evidence\payload-hashes
VISUAL_CHECKPOINT_DIR=A:\Capital Chronicle\local-evidence\visual-checkpoints
```

## Vertex service-account rule

Service-account JSON must live outside `.env`.
`.env` only points to the path.

```dotenv
GOOGLE_APPLICATION_CREDENTIALS=A:\Capital Chronicle\local-secrets\vertex_service_account.json
VERTEX_PROJECT_ID=gen-lang-client-0019426105
VERTEX_SERVICE_ACCOUNT_EMAIL=capital-chronicle@gen-lang-client-0019426105.iam.gserviceaccount.com
```

Never paste `-----BEGIN PRIVATE KEY-----` or JSON service-account bodies into `.env`.

## Future edit checklist

Before editing `.env` again:

1. Read `live_contentops/final_environment_format_inventory.py` expected key families.
2. Preserve one key per line and do not duplicate keys.
3. Preserve empty placeholders for X, LinkedIn, and TikTok until explicitly enabled.
4. Keep raw JSON and browser sessions out of `.env`.
5. Run redacted inventory:

```powershell
python -m live_contentops.final_environment_format_inventory --repo-root .
```

6. Run tests:

```powershell
python -m pytest tests/test_final_environment_format_inventory.py -q
```

7. Verify `.env`, `.env.local`, local secrets, browser profiles, and evidence folders are not staged.
