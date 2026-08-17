# TikTok Local Desktop OAuth PKCE Helper V1

## Result

`PASS_TIKTOK_LOCAL_DESKTOP_OAUTH_PKCE_HELPER_READY_FOR_SUPERVISED_SANDBOX_OAUTH`

This is a local bootstrap capability only. No real TikTok OAuth/API call, token persistence,
content-posting call, media upload, public write, portal mutation, V1 mutation, or scheduler change
was performed.

## Git and authority

- Repository: `fatcat2109/capital-chronicle-contentops`
- Branch: `task/contentops-tiktok-local-desktop-oauth-pkce-helper-v1`
- Freshly fetched starting `origin/master`: `0b8f5a7f4c3f003b686c9a85e0ecdf73b9c94f22`
- The V2 authority chain required by the task and `video/AGENTS.md` was read before implementation.
- The reverted file
  `docs/automation/CONTENTOPS_V2_SOCIAL_CREDENTIAL_BOOTSTRAP_BLOCKER_REMOVAL_AND_RETURN_PLAN_V1.md`
  remains absent.
- Remote publication-adapter branch was observed, not modified, at
  `18c16722ddf0fbdf1c42c8356de2f3245039f36a`.
- `python scripts/generate_codex_context_index.py --check`: `CODEGRAPH_CURRENT`.

## Current official TikTok contract

First-party sources re-read on 2026-08-17:

- Login Kit Overview: <https://developers.tiktok.com/doc/login-kit-overview>
- Login Kit for Desktop: <https://developers.tiktok.com/doc/login-kit-desktop/>
- OAuth v2 User Access Token Management:
  <https://developers.tiktok.com/doc/oauth-user-access-token-management>
- TikTok API Scopes: <https://developers.tiktok.com/doc/tiktok-api-scopes>
- Upload to TikTok: <https://developers.tiktok.com/doc/content-posting-api-get-started-upload-content>

The reviewed Desktop contract permits an HTTP loopback URI using `localhost` or `127.0.0.1`,
requires an explicit port and a static URI without query or fragment, and requires PKCE. The frozen
callback `http://127.0.0.1:8765/oauth/tiktok/callback` is syntactically valid. The helper implements
TikTok's documented lowercase hexadecimal SHA-256 challenge for a fresh 43–128-character verifier,
not generic base64url encoding.

- Authorization endpoint: `https://www.tiktok.com/v2/auth/authorize/`
- Token endpoint: `https://open.tiktokapis.com/v2/oauth/token/`
- Exact scopes: `user.info.basic,video.list,video.upload`
- `video.publish` requested: `false`

## Implementation contract

- Library: `live_contentops/tiktok_local_desktop_oauth_pkce_v1.py`
- Supervised CLI: `scripts/run_tiktok_local_desktop_oauth_pkce_v1.py`
- Listener: one shot, bounded, `127.0.0.1:8765`, exact path `/oauth/tiktok/callback`
- State: fresh CSPRNG value, exact constant-time comparison, never logged or persisted
- PKCE: fresh OAuth-unreserved verifier and TikTok hex SHA-256 S256 challenge
- Token transport: injected form-POST seam with a bounded HTTP timeout and no code-exchange retry
- Refresh: injected refresh grant; a returned rotated refresh token replaces the old in-memory value
- Result: secret-bearing session object remains in memory and has redacted `repr`/`str`
- CLI: requires `--run-supervised-sandbox-oauth` and emits only a redacted JSON receipt

The only approved input variable names are:

- `CONTENTOPS_TIKTOK_CLIENT_KEY`
- `CONTENTOPS_TIKTOK_CLIENT_SECRET`

Validation did not read their real values. Environment mutations and invented persistent token
names are both zero.

## Validation

- Focused helper plus directly relevant existing credential/redaction tests: `33 passed in 2.52s`
- Real local fake OAuth + refresh E2E: passed in `0.31s`
- Adversarial coverage: mismatched/missing state, missing code, provider error, wrong path,
  malformed/duplicate query, timeout, late callback, browser failure, HTTP failure, malformed JSON,
  missing token fields, incomplete/extra scopes, refresh rotation, redacted string forms, zero
  persistence, zero environment mutation, no `video.publish`, and no Content Posting execution
- Distinctive fake-secret capture over receipt/stdout/stderr/string forms: no leak
- Scoped changed-artifact secret/leak scan: passed
- Real TikTok/OAuth calls: `0`
- Content Posting calls: `0`; media uploads: `0`; public writes: `0`
- V1 mutations: `0`; scheduler changes: `0`; external billable cost: `$0`

## Caveats and exact next operation

The TikTok Sandbox must still be checked for an exact registered callback match. Windows default
browser launch, operator consent, and the real provider response remain for supervised proof.
Tokens are intentionally not stored; Jim must make a separate persistence decision after OAuth.

Exact next operation:
`COMET_JIM_SUPERVISED_TIKTOK_SANDBOX_DESKTOP_OAUTH_V1`.

That operation must keep Direct Post off, keep the three reviewed scopes, use target user
`jimpham.cc`, let Jim handle login/2FA/consent, report only redacted outcome fields, perform no media
upload, and stop for Jim's explicit token-storage decision. After a later read-only identity/scope
preflight, return to deliberate reconciliation of the untouched publication-adapter branch.
