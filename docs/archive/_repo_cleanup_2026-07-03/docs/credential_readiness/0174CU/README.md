# 0174CU Platform Requirements + Account-Binding Policy Packets

Strictly local, official-doc-grounded, requirements-only packets. No live calls, no credentials, no OAuth, no account binding, no posting.

## Inherited posture (from 0174CT)

- Live posting state: `blocked_until_new_explicit_task_and_operator_go`.
- Additional live sends paused; two Telegram pilots still require operator review.

## Packets

- `telegram_third_gate_requirements_packet.json` -- requirements for a possible future third Telegram send (no send now).
- `x_account_binding_requirements_packet.json` -- X binding + dry-run requirements (no OAuth/token/post now).
- `linkedin_account_binding_requirements_packet.json` -- LinkedIn member/org/page binding + dry-run requirements (no OAuth/token/post now).
- `platform_requirements_account_binding_policy_index.json` -- index referencing the three platform packets with checksums.

## Platform priority recommendation

1. X requirements (no live)
2. LinkedIn requirements (no live)
3. Telegram third gate (later)

## Official docs inspected

- X: Create or Edit Post (`docs.x.com/x-api/posts/create-post`) -- accessible; developer portal access tiers -- gated (login required, not performed).
- LinkedIn: Posts API (Microsoft Learn) -- accessible; versioned via the LinkedIn-Version header; Marketing 202506 sunset noted.
- Telegram: Bot API sendMessage (`core.telegram.org/bots/api`) -- accessible; already validated upstream.

## What this did NOT do

No Telegram/X/LinkedIn API call. No sendMessage / getMe / getChat / getChatMember / getUpdates / webhook / scheduler / reply / DM / metrics / scraping. No OAuth flow, token exchange, developer portal login, or account-binding mutation. No credential or env read. The module never browses docs at runtime; docs reading was an Antigravity/operator activity before writing symbolic packet data.

## Next

Recommended next task: `TASK_CONTENTOPS_0174CV_X_OFFICIAL_DOCS_ACCOUNT_BINDING_REQUIREMENTS_NO_OAUTH_NO_LIVE_V0`.
