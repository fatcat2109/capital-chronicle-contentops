# Probe Hardening Report — Batch B

Task: `TASK_CONTENTOPS_MULTI_PLATFORM_LIVE_FOUNDATION_BATCH_B_OPERATOR_SETUP_TELEGRAM_READONLY_PROOF_AND_PROBE_HARDENING_V0`

## Hardened rules

- Endpoint families must match registry allowlist.
- Method must be `GET` for network probes or `LOCAL` for no-network probes.
- Network probe request budget must be exactly one.
- Auto retry must be false.
- Raw response persistence must be false.
- Telegram final host must be `api.telegram.org`.
- Telegram final scheme must be `https`.
- Telegram `getMe` allows no query parameters.
- Telegram `getChat` allows only `chat_id` query parameter.
- URL fragments are forbidden.
- Redirect policy is `redirect_disabled_fail_closed`.

## Approved Batch B Telegram probes

| Probe | Endpoint family | Purpose | Request budget |
|---|---|---|---|
| `getMe` | `telegram_bot_identity` | Confirm bot identity redacted | 1 |
| `getChat` | `telegram_channel_read` | Confirm destination readability redacted | 1 |

## Explicitly forbidden behavior

No `sendMessage`, `sendPhoto`, `sendDocument`, uploads, publish endpoints, scheduler, autonomous replies, DMs, webhooks, polling, or scraping.

## Evidence model

Persisted evidence contains only:

- credential presence/shape classes;
- request counts;
- symbolic result classifications;
- redacted presence classes;
- hard safety flags;
- blocked reasons.

Evidence excludes raw credentials, chat IDs, bot IDs, usernames, channel titles, request URLs, headers, and raw Telegram JSON.
