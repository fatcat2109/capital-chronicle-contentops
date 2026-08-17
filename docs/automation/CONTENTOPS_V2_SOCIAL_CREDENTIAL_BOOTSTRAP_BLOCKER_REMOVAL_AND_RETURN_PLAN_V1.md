# Capital Chronicle ContentOps V2 — Social Credential Bootstrap Blocker-Removal and Return Plan V1

Authority date: 2026-08-17
Status: `CURRENT_TEMPORARY_BLOCKER_REMOVAL_ADDENDUM`
Parent plan: `CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_MASTER_PLAN_V2.md`
Parent pointer: `CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_CURRENT_EXECUTION_POINTER_V2.md`
Owner direction: Jim, 2026-08-17

## 1. Purpose

This addendum records a temporary social-platform credential/bootstrap detour without replacing the V2 product plan.

The product direction remains the Retention-Native Video Factory / Freeform Chapterized Creative Authority path. Credential work is admitted only because official publication adapters cannot be truthfully exercised against provider accounts without account binding, OAuth credentials, exact scopes, and readback identity.

This is blocker removal, not a new product lane.

## 2. Original V2 route preserved

The durable sequence remains:

`free-form creation substrate [ACCEPTED] -> zero-rerender global language sidecars [ACCEPTED INPUT] -> official publication adapters -> provider account/credential + identity/scope preflight -> one-destination live canary/readback when separately authorized -> live reconciliation -> unattended V2 core proof -> V1 integration/scheduling [DEFERRED]`

Do not replace this sequence with credential infrastructure work.

The completed but unmerged publication-adapter branch is:

- branch: `task/v2-official-platform-publication-adapters-shadow-closed-loop-v1`
- reviewed task HEAD: `18c16722ddf0fbdf1c42c8356de2f3245039f36a`
- original branch base: `74a3751b2cd28928c437b202dc7cbaac3669924d`

It is evidence and implementation input, not current `master` authority. It must be reconciled onto then-current `master` rather than blindly fast-forwarded or merged over newer V1/V2 work.

## 3. Publication-adapter repair backlog before live canary

Before any real provider canary, reconcile the prior shadow branch and close the known API-contract gaps against current first-party provider documentation:

1. YouTube: avoid destructive/invalid `videos.update` metadata behavior; either set required snippet fields correctly or update localizations through a semantically safe request path.
2. Instagram: bind the exact login variant, Graph host, token type, Graph version, account identity, and required permissions.
3. TikTok: if readback asserts public video metadata, use the exact supported readback endpoint/scope rather than treating publish-status output as a full video object.
4. Instagram Story: do not require readback fields that the selected official API surface does not guarantee.
5. Facebook Reels: verify the exact Page identity/edge and Graph-version request shape before live use.

No fake-provider shadow PASS may be promoted to live-provider correctness without this reconciliation.

## 4. Current temporary blocker-removal task

Current temporary task:

`TASK_CONTENTOPS_TIKTOK_LOCAL_DESKTOP_OAUTH_PKCE_HELPER_V1`

Why now:

- TikTok Developer Sandbox `CC ContentOps Sandbox` exists.
- Target user `jimpham.cc` has been added successfully.
- Login Kit and Content Posting API are configured in Sandbox.
- Current Sandbox scopes are `user.info.basic`, `video.upload`, and `video.list`.
- Direct Post is OFF.
- Current repository contains only TikTok OAuth callback/credential scaffolding, not an executable TikTok PKCE loopback OAuth helper.

This task exists only to make supervised Sandbox OAuth technically possible.

## 5. TikTok exact contract for this detour

Current repo callback convention:

`http://127.0.0.1:8765/oauth/tiktok/callback`

Do not silently replace it with another port/path. If current official TikTok Desktop Login Kit or the Developer Portal rejects this callback, report the incompatibility before changing repo authority.

Required Sandbox OAuth scopes:

- `user.info.basic`
- `video.list`
- `video.upload`

Do NOT request `video.publish` in this lane.

Direct Post remains OFF. Current Capital Chronicle internal/team-managed publication model is not to be misrepresented as an audited creator-facing Direct Post product.

## 6. Environment-variable authority

Jim's existing User Environment Variable naming is authority for this task.

Use exactly:

- `CONTENTOPS_TIKTOK_CLIENT_KEY`
- `CONTENTOPS_TIKTOK_CLIENT_SECRET`

Do not rename these variables and do not create `V2_*` aliases merely to match historical repository docs.

Historical repo references to `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_ACCESS_TOKEN`, `TIKTOK_REFRESH_TOKEN`, or `TIKTOK_OPEN_ID` are not authority to rename Jim's current environment.

No operator-approved persistent variable names currently exist for TikTok user access token, refresh token, or open_id. The helper must therefore keep token values secret and transient by default and stop at an explicit Jim secret-storage handoff. Do not invent persistent token variable names.

## 7. Helper capability boundary

The local helper may implement:

`existing client key/secret -> CSPRNG state + PKCE S256 -> loopback listener -> browser consent -> exact state validation -> authorization-code exchange -> access/refresh/open_id presence receipt -> refresh-token capability`

It must not:

- print/log/hash/commit client secret, authorization code, PKCE verifier, access token, or refresh token;
- write secrets to repo files;
- auto-create environment variables;
- upload TikTok media;
- call Content Posting API as part of implementation validation;
- enable Direct Post;
- request `video.publish`;
- submit Production review;
- expose publication authority;
- unquarantine unrelated live/scheduler entrypoints.

Implementation tests use mocks/local fake OAuth endpoints only. Real TikTok OAuth is a separate supervised Comet + Jim operation after code review.

## 8. Return path after helper PASS

After `TASK_CONTENTOPS_TIKTOK_LOCAL_DESKTOP_OAUTH_PKCE_HELPER_V1` passes:

1. Comet configures/saves the exact TikTok Sandbox Desktop redirect URI if still required by the portal.
2. Jim performs supervised TikTok consent/login; Comet/browser automation must not capture secrets.
3. The helper proves only redacted outcomes: access token received, refresh token received, open_id received, exact granted scopes, identity binding.
4. Jim explicitly chooses the persistent secret-storage names/destination before any token persistence.
5. Run a read-only account/scope/identity preflight. Do not upload yet.
6. Return immediately to the official-publication-adapter route: reconcile the `18c16722...` implementation onto current `master`, repair the provider API gaps above, and re-run deterministic shadow E2E.
7. Only after provider-specific account/scopes/identity and adapter semantics pass may a separately authorized one-destination live canary/readback occur.
8. TikTok current route is Upload-to-TikTok draft (`video.upload`) only. Direct Post remains excluded unless the actual product model and TikTok policy eligibility materially change and are reviewed separately.

## 9. Other platform credential work

YouTube, Instagram/Meta, and Facebook credential/account verification remain part of the publication-readiness blocker set, but do not broaden this TikTok helper task into a generic credential framework.

Use existing environment-variable names. Resolve only concrete provider blockers required by the next named canary.

## 10. Non-overlap / parked work

This ContentOps credential detour must not touch:

- Capital Chronicle Core Analyzer Stage-0B production runtime;
- Analyzer scheduler/deployment;
- Capital Chronicle database-hardening lane owned elsewhere;
- V1 publication/runtime/scheduler state except read-only authority inspection;
- V2 public-write authority.

`ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` remains in force during helper implementation and supervised OAuth bootstrap.

## 11. Exit condition

This addendum stops controlling execution once all of the following are true:

- local TikTok OAuth helper is validated;
- supervised Sandbox OAuth has produced a verified redacted account/scope/identity result;
- Jim has separately decided secret persistence;
- the next publication-adapter reconciliation task has started from current `master`.

At that point, resume the original V2 publication/readback sequence above. Do not continue building credential infrastructure without a named provider blocker.
