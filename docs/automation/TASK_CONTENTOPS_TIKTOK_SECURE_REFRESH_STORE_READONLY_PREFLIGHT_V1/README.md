# TikTok Secure Refresh Store and Read-only Identity Preflight V1

## Result

`PASS_TIKTOK_SECURE_REFRESH_STORE_AND_READONLY_PREFLIGHT_READY_FOR_REAL_PERSISTENCE_AUDIT`

This result means the reviewed Desktop OAuth helper is on `master`, the secure persistence and
read-only account-binding code exists, fake provider/credential flows pass, and no real TikTok
credential has been persisted. It does not authorize real OAuth, upload, draft creation, posting,
or any other platform write.

## Phase 0 merge

- Fresh starting `origin/master`: `0b8f5a7f4c3f003b686c9a85e0ecdf73b9c94f22`
- Accepted helper branch:
  `task/contentops-tiktok-local-desktop-oauth-pkce-helper-v1`
- Accepted helper HEAD: `f994a9ed7b730e54d09b29900a527daa9b8f51c9`
- Ahead/behind versus fresh master: `1/0`
- Merge base: the fresh starting master
- Merge method: normal non-force fast-forward push to `master`
- Final fetched/remote `master`: `f994a9ed7b730e54d09b29900a527daa9b8f51c9`
- Synthetic merge/closeout commit: none

The dirty canonical checkout was not mutated. The implementation branch was created in a clean
dedicated worktree from the freshly verified remote master.

## Storage contract

- Backend: native Windows Credential Manager API through Python standard-library `ctypes`
- Credential type: Generic Credential
- Windows scope: current Windows user, persistent across that user's local logons
- Stable target: `CapitalChronicle.ContentOps/TikTok/Sandbox/primary`
- Credential blob: refresh token only
- Credential username: app-scoped TikTok `open_id`
- Access token persisted: `false`
- Client secret persisted in Credential Manager: `false`
- Authorization code, PKCE material, state, and handle persisted: `false`
- New token/open-id environment variables created: `0`
- Approved application variables remain exactly:
  `CONTENTOPS_TIKTOK_CLIENT_KEY` and `CONTENTOPS_TIKTOK_CLIENT_SECRET`

The module import path performs no environment read, Credential Manager call, network request, or
mutation. Credential and network access occur only through explicit calls. Secret-bearing objects
have redacted `repr` and `str`.

Refresh rotation is fail closed. The refreshed session must contain the required scopes and the
same `open_id`; a different refresh token is written over the same Generic Credential and read back
for confirmation without deleting the old credential first. A failed replacement is classified
`REFRESH_ROTATION_PERSISTENCE_FAILED`, and orchestration performs no second provider refresh.

## Read-only identity hard gate

Current first-party TikTok documentation was re-read on 2026-08-17:

- User Access Token Management:
  <https://developers.tiktok.com/doc/oauth-user-access-token-management>
- Get User Info:
  <https://developers.tiktok.com/doc/tiktok-api-v2-get-user-info/>
- TikTok API Scopes:
  <https://developers.tiktok.com/doc/tiktok-api-scopes>

Confirmed current contract:

- Token and refresh endpoint: `POST https://open.tiktokapis.com/v2/oauth/token/`
- Refresh fields: `client_key`, `client_secret`, `grant_type=refresh_token`, `refresh_token`
- Documented access-token lifetime: 24 hours after initial issuance
- Documented refresh-token lifetime: 365 days after initial issuance
- A refresh response may rotate the refresh token; the newly returned value must be used
- Identity endpoint: `GET https://open.tiktokapis.com/v2/user/info/`
- Requested fields: `open_id,display_name`
- Authorization: transient `Bearer` access token
- Required identity scope: `user.info.basic`
- Account-binding gate: API `open_id` must exactly equal the OAuth/token-session `open_id`
- Mismatch result: `IDENTITY_OPEN_ID_MISMATCH`, with no initial persistence/continuation

Portal target user `jimpham.cc` remains operator/browser-confirmed only. The implemented
`user.info.basic` request proves app-scoped `open_id` equality and optionally receives
`display_name`; it does **not** API-verify the public TikTok username. TikTok's current User Info
reference associates `username` with the separate `user.info.profile` scope, which this task does
not request.

## Implementation

- Existing OAuth helper:
  `live_contentops/tiktok_local_desktop_oauth_pkce_v1.py`
- Secure store/preflight/orchestration:
  `live_contentops/tiktok_secure_refresh_store_readonly_preflight_v1.py`
- Focused tests:
  `tests/test_tiktok_secure_refresh_store_readonly_preflight_v1.py`
- Redacted fake E2E receipt: `fake_e2e_receipt.json`

The future supervised path is:

`in-memory Desktop OAuth session -> read-only identity preflight -> exact open_id equality -> persist refresh token + open_id -> return redacted receipt`

The future stored path is:

`load refresh credential -> read the two approved app variables -> one refresh request -> validate scopes/open_id -> safely persist rotation -> transient access-token identity preflight -> redacted readiness receipt`

Neither path was executed against TikTok in this task.

## Validation

- Existing helper plus new non-native focused tests: `46 passed, 1 deselected in 4.79s`
- Fake supervised OAuth-session -> identity preflight -> Credential Manager store: passed
- Fake stored refresh -> rotated token replacement -> identity preflight: passed
- Windows native fake credential roundtrip: write -> read -> replace -> read -> delete -> absent
- Randomized test-only Credential Manager target deleted: `true`
- Provider failure coverage: user-info HTTP/malformed/missing/mismatch and refresh
  HTTP/malformed/incomplete-scope failures
- Credential failure coverage: missing/corrupt/unavailable/read/write/rotation/cleanup failures
- Distinctive fake-secret capture across stdout, stderr, objects, exceptions, and receipts: no leak
- Access-token persistence: `false`
- Token prefix/suffix/hash/fingerprint evidence: none

## Safety

- Real OAuth attempts: `0`
- Real TikTok API calls: `0`
- Real TikTok credentials stored: `0`
- Content Posting API calls: `0`
- `video.list` calls: `0`
- Media uploads: `0`
- Drafts: `0`
- Public writes: `0`
- V1 mutations: `0`
- Scheduler mutations: `0`
- Publication-adapter branch mutations: `0`
- Environment mutations: `0`

## Exact next operation

`COMET_JIM_TIKTOK_SECURE_PERSISTENCE_OAUTH_AND_READONLY_PREFLIGHT_V1`

That operation is permitted only after independent Jim/ChatGPT audit of this implementation
branch. It should run one supervised Sandbox Desktop OAuth, perform the read-only identity hard
gate, persist only refresh token + `open_id`, emit a redacted receipt, and stop. It must retain zero
Content Posting, upload, draft, and public-write authority.
