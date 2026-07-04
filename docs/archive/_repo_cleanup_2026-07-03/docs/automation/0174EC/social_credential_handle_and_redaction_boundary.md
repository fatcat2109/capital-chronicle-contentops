# Social Credential Handle + Redaction Boundary (0174EC)

Task: TASK_CONTENTOPS_0174EC_CREDENTIAL_HANDLE_AND_REDACTION_BOUNDARY_V0
Model: SOCIAL_CREDENTIAL_HANDLE_BOUNDARY_0174EC (0174EC_CREDENTIAL_HANDLE_BOUNDARY_V1)
Source baseline commit: c5763167bee79f41381465af517039498c219f63
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
- `unknown`
- `not_configured`
- `configured_symbolic`
- `unavailable`
- `expired_symbolic`
- `revoked_symbolic`
- `insufficient_scope_symbolic`
- `wrong_account_symbolic`
- `source_policy_blocked`
- `forbidden_value_detected`
- `live_hydration_not_allowed`

## Current Source Policy

Allowed now (symbolic, secret-free):
- `fake_provider_result`
- `operator_declared_symbolic_presence`
- `docs_declared_requirement`

Forbidden now (never exercised by this task):
- `os_environ_read`
- `dotenv_file_read`
- `keyring_read`
- `browser_session_read`
- `credential_file_read`
- `oauth_callback_server_execution`
- `token_exchange_or_refresh`
- `api_token_validation_call`

## Future Source Classes (declared, NOT used now)
- `interactive_hidden_prompt_future_gate`
- `external_secret_manager_future_gate`
- `operator_session_memory_future_gate`
- `platform_oauth_callback_future_gate`

> [!WARNING]
> Future source classes are declarations of intent for later operator-owned,
> separately-gated tasks. This task never reads from any of them.

## Fake Credential Provider Contract
The fake provider simulates credential scenarios with **no network, no env
read, no file read, no keyring access, and no secret return** -- only symbolic
classes and booleans. Simulated result classes:
- `configured_symbolic`
- `not_configured`
- `unknown`
- `expired_symbolic`
- `revoked_symbolic`
- `insufficient_scope_symbolic`
- `wrong_account_symbolic`
- `source_policy_blocked`
- `forbidden_value_detected`
- `live_hydration_attempt_blocked`

## Supported Platforms
- `bluesky` (Bluesky) -- family `app_password_or_session_token`
- `discord` (Discord) -- family `webhook_url_secret`
- `facebook` (Facebook) -- family `oauth2_user_context_token`
- `instagram` (Instagram) -- family `oauth2_user_context_token`
- `linkedin` (LinkedIn) -- family `oauth2_user_context_token`
- `mastodon` (Mastodon) -- family `instance_oauth_token`
- `medium` (Medium) -- family `unsupported_or_manual_only`
- `reddit` (Reddit) -- family `oauth2_user_context_token`
- `substack` (Substack) -- family `unsupported_or_manual_only`
- `telegram` (Telegram) -- family `bot_token`
- `threads` (Threads) -- family `oauth2_user_context_token`
- `tiktok` (TikTok) -- family `oauth2_user_context_token`
- `x` (X (Twitter)) -- family `oauth2_user_context_token`
- `youtube` (YouTube) -- family `oauth2_user_context_token`

## Credential Families
- `bot_token`
- `webhook_url_secret`
- `oauth2_user_context_token`
- `oauth2_client_credentials`
- `oauth1a_user_context_token_pair`
- `app_password_or_session_token`
- `instance_oauth_token`
- `api_key_delegated_provider`
- `unsupported_or_manual_only`

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
`TASK_CONTENTOPS_0174ED_APPROVAL_LEDGER_AND_PAYLOAD_HASH_CONTRACT_V0`

Next required gate: approval ledger + payload hash contract, then outbox + idempotency, rate/spend/retry policy, and redacted dispatch audit before any supervised live write; live credential hydration remains a separate future operator-owned gate and is NOT enabled here
