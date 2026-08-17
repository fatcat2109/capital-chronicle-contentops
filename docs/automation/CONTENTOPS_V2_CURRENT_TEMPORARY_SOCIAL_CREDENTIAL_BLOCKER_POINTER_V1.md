# Capital Chronicle ContentOps V2 — Current Temporary Social Credential Blocker Pointer V1

Authority date: 2026-08-17
Status: `CURRENT_TEMPORARY_BLOCKER_POINTER`

Read first with:

- `CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_NORTH_STAR_V2.md`
- `CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_MASTER_PLAN_V2.md`
- `CONTENTOPS_V2_SOCIAL_CREDENTIAL_BOOTSTRAP_BLOCKER_REMOVAL_AND_RETURN_PLAN_V1.md`

## Current temporary task

`TASK_CONTENTOPS_TIKTOK_LOCAL_DESKTOP_OAUTH_PKCE_HELPER_V1`

This is a bounded blocker-removal detour only.

Do not reinterpret it as a new product phase, generic credential program, social-platform expansion program, or public-write authorization.

## Current TikTok state

- Developer app: `Capital Chronicle ContentOps`.
- Sandbox: `CC ContentOps Sandbox`.
- Sandbox Target User: `jimpham.cc` added successfully.
- Login Kit: configured in Sandbox.
- Content Posting API: configured in Sandbox.
- Direct Post: OFF.
- Current scopes: `user.info.basic`, `video.upload`, `video.list`.
- Existing client credentials are present in Jim's User Environment under the approved names below.
- Missing capability: executable local TikTok Desktop OAuth PKCE helper.

## Approved environment names

Use exactly:

- `CONTENTOPS_TIKTOK_CLIENT_KEY`
- `CONTENTOPS_TIKTOK_CLIENT_SECRET`

Do not rename them.
Do not create `V2_*` aliases.
Do not invent persistent token variable names.

## Current repo callback convention

`http://127.0.0.1:8765/oauth/tiktok/callback`

Builder must verify this against current official TikTok Desktop Login Kit documentation before implementation. If current TikTok requirements conflict, stop or repair the approach explicitly; do not silently change authority.

## Builder result target

Implement and test a local supervised OAuth helper with:

- CSPRNG state;
- PKCE S256;
- exact loopback callback listener;
- authorization URL builder;
- state validation;
- authorization-code token exchange;
- refresh-token support;
- redacted success/status output only;
- zero token/secret logging or persistence by default.

Real TikTok OAuth is NOT part of the builder task. Tests use local mocks/fakes only.

## Hard boundary

The builder must not:

- use real TikTok network/OAuth;
- open a real browser consent session;
- write User Environment variables;
- print/read back secret values in reports;
- upload media;
- call Content Posting API;
- request `video.publish`;
- enable Direct Post;
- submit Production review;
- alter V1 runtime/scheduler;
- alter Capital Chronicle Analyzer/database work;
- grant public-write authority.

`ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` remains unchanged.

## Required return path

After helper PASS:

`Codex helper implementation -> Comet/Jim supervised Sandbox OAuth -> redacted identity/scope proof -> Jim explicit secret-storage decision -> read-only provider preflight -> reconcile official publication-adapter branch onto then-current master -> repair known provider API gaps -> deterministic shadow E2E -> separately authorized one-destination live canary/readback -> reconciliation -> unattended V2 core proof -> V1 integration/scheduling [DEFERRED]`

Do not continue credential infrastructure after TikTok OAuth bootstrap unless a named provider blocker proves it necessary.

## Publication branch context

Existing unmerged implementation evidence:

- branch: `task/v2-official-platform-publication-adapters-shadow-closed-loop-v1`
- reviewed task HEAD: `18c16722ddf0fbdf1c42c8356de2f3245039f36a`
- old base: `74a3751b2cd28928c437b202dc7cbaac3669924d`

Do not blindly merge it because `master` has advanced. Reconcile it onto current authority only after the credential/bootstrap blocker is cleared.
