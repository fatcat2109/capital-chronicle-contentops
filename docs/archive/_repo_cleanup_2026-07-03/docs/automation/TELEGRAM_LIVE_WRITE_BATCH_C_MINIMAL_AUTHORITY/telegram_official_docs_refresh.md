# Telegram Official Docs Refresh — Batch C

Task: `TASK_CONTENTOPS_TELEGRAM_LIVE_WRITE_BATCH_C_MINIMAL_AUTHORITY_AND_SUPERVISED_SENDMESSAGE_PILOT_V0`

Source checked: `https://core.telegram.org/bots/api`

## Confirmed API Contract

- Telegram Bot API endpoint format is `https://api.telegram.org/bot<token>/METHOD_NAME`.
- `getMe` returns bot identity through `ok` and `result`.
- `getChat` accepts `chat_id` and returns chat metadata through `ok` and `result`.
- `sendMessage` accepts `chat_id` and `text`.
- Error responses are classified without persisting raw response bodies.
- Batch C persists only redacted endpoint path `/bot<redacted>/<method>`.
- Timeout is `10` seconds.
- Redirects are disabled/fail-closed.
- Auto retry is forbidden.
