# 0174CK — Telegram Live Read-Only getMe Identity Gate

Task: `TASK_CONTENTOPS_0174CK_TELEGRAM_LIVE_GATE_READ_ONLY_BOT_ID_VALIDATION_V0`

## Purpose

The first and only module authorized to make a bounded, live, read-only Telegram
Bot API request, and only the `getMe` method. It confirms that the repo-local bot
token authenticates with Telegram (token identity). Nothing more.

Module: `live_contentops/telegram_live_getme_gate.py`
CLI: `python -m live_contentops.cli telegram-live-getme-gate --live-telegram-getme`

## What this gate does NOT do

This gate does not post, schedule, reply/DM, set webhooks, call `sendMessage` /
`getUpdates` / `getChat`, validate channel-write permission, or fetch metrics. The
`live_publish_gate` remains `blocked` and a separate future gate is required before
any posting.

## Hard guarantees (enforced by tests + leakage guards)

- **Fail-closed**: no network is performed unless the caller passes the explicit
  arming flag (`armed=True` / CLI `--live-telegram-getme`).
- **Method allowlist**: only `getMe` is ever constructed/called. All write/admin
  methods are explicitly forbidden.
- **Host allowlist**: only `api.telegram.org`.
- **Request budget**: at most one live request per execution (a second attempt is
  only possible with `allow_second_attempt=True`, still capped at 2).
- **Hard timeout**: default 10s.
- **Redacted-only output**: never emits the token, chat id, request URL, raw
  response JSON, bot id, bot username, any prefix/suffix/length, or hash/digest.
  Output is booleans plus redacted classes only. A defensive secret-like scan
  scrubs and fails closed if anything sensitive survives into the summary.

The token is read from the approved local env source via the existing 0174CJ
readiness reader (`prelaunch_telegram_credential_readiness`); this module never
prints or inspects the raw `.env` line.

## Usage

```bash
# Fail-closed (default): no network, status=blocked, reason not_armed_live_request_skipped
python -m live_contentops.cli telegram-live-getme-gate

# Armed: performs ONE live getMe call, prints ONLY the redacted summary
python -m live_contentops.cli telegram-live-getme-gate --live-telegram-getme

# Optional: process-env fallback if no local .env / .env.local is present
python -m live_contentops.cli telegram-live-getme-gate --live-telegram-getme --process-env
```

## Recorded live-run result (redacted)

The single authorized live `getMe` call for 0174CK returned:

| Field | Value |
| --- | --- |
| `status` | `pass` |
| `armed` | `true` |
| `request_count` | `1` (budget `1`) |
| `host_allowlist_passed` | `true` |
| `method_allowlist_passed` | `true` |
| `token_present` | `true` |
| `token_shape_class` | `present_redacted_telegram_bot_token_like` |
| `response_ok` | `true` |
| `bot_identity_validated` | `true` |
| `redaction_verified` | `true` |
| `live_publish_gate` | `blocked` |
| `posting_enabled` / `send_message_enabled` / `get_updates_enabled` / `webhook_enabled` | `false` |
| `channel_write_validated` / `scheduler_enabled` / `autonomous_replies_enabled` / `metrics_fetch_enabled` | `false` |
| `next_gate_required_before_posting` | `true` |
| `blocked_reasons` | `[]` |

No token, chat id, URL, bot id, bot username, or raw response body was emitted.

## Next gate

A separate, explicitly operator-gated task is required before any channel-write
validation or posting. This gate establishes token identity only.
