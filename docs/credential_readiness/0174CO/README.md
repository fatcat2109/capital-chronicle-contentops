# 0174CO — Telegram Post-Pilot Ledger & Next-Platform Binding Roadmap

Task: `TASK_CONTENTOPS_0174CO_TELEGRAM_POST_PILOT_LEDGER_AND_NEXT_PLATFORM_ACCOUNT_BINDING_ROADMAP_V0`

## Purpose

A **strictly local** gate that persists a durable, redacted ledger record for the
accepted 0174CN supervised live Telegram pilot post, plus a concise next-platform
account-binding roadmap stub. It makes **no live calls** and reads **no env /
credentials**.

Module: `live_contentops/telegram_post_pilot_ledger_gate.py`
CLI: `python -m live_contentops.cli telegram-post-pilot-ledger-gate`
Write flag: `--write-telegram-post-pilot-ledger`
Ledger artifact: `docs/credential_readiness/0174CO/telegram_post_pilot_ledger_0174cn.json`

## What this gate does NOT do

No live Telegram API call. No `sendMessage` / `getMe` / `getChat` / `getChatMember`
/ `getUpdates`. No webhook, scheduler, reply/DM, metrics fetch, delivery lookup, or
scraping. It does not enable any future posting and makes no claim that posting is
enabled. The post-pilot `live_publish_gate` remains `blocked_after_one_time_pilot`.

## Hard guarantees (enforced by tests + leakage guards)

- **No network**: imports no `urllib` / `requests` / `httpx` / `socket`.
- **No env read**: never touches `os.environ` / `os.getenv` / `.env`.
- **Fail-closed / preview-only**: the ledger file is written ONLY when the explicit
  `--write-telegram-post-pilot-ledger` flag (`write=True`) is passed. No network in
  either mode.
- **Hash re-verification**: the 0174CN canonical payload hash is recomputed from the
  committed `telegram_first_supervised_live_post_gate.build_default_payload()` and
  must equal the expected hash, or the task blocks and writes nothing.
- **Deterministic artifact**: sorted keys, stable separators, trailing newline.
- **Redaction scan before write**: blocks token-like values, any `api.telegram.org`
  URL, raw `@handles`, long digit runs (possible chat/channel/message ids),
  credential-like strings, and forbidden raw keys (`token`, `chat_id`, `channel_id`,
  `channel_username`, `bot_id`, `bot_username`, `message_id`, `date`, `raw_url`,
  `raw_request`, `raw_response`, `target_identifier`).
- **No message id value persisted**: only `message_id_present: true` is recorded.

## Accepted 0174CN live result (redacted, recorded only)

| Field | Value |
| --- | --- |
| `status` | `pass` |
| `request_count` / `request_budget` | `1` / `1` |
| `allowed_method` | `sendMessage` |
| `message_sent` | `true` |
| `telegram_response_ok_class` | `true` |
| `message_id_present` | `true` (value never persisted) |
| `live_publish_gate` | `blocked_after_one_time_pilot` |
| `next_gate_required_before_next_live_post` | `true` |

Source live commit: `71bcd9cb79fe6039290145d438969987b2728222`
Verified canonical payload hash:
`b9955db3a78d0738aa99f12e8889d70bae450395b9eae58e313fd70b9d73baa1`

## Usage

```bash
# Preview-only (default): no write, status=fail_closed, reason write_flag_absent_preview_only
python -m live_contentops.cli telegram-post-pilot-ledger-gate

# Write the redacted ledger artifact (local only; no network)
python -m live_contentops.cli telegram-post-pilot-ledger-gate --write-telegram-post-pilot-ledger
```

## Next-platform binding roadmap (stub only)

- `next_platform_binding_candidate`: `x_or_linkedin_or_telegram_second_gate_pending_operator_choice`
- `requirement_before_next_live_send`: new explicit task + operator GO +
  platform-specific account binding + dry-run + approval hash
- No autonomous publishing, no scheduler, no reply/DM, no metrics fetch, no scraping.

## Next gate

`TASK_CONTENTOPS_0174CP_NEXT_PLATFORM_ACCOUNT_BINDING_SELECTION_AND_OFFICIAL_DOCS_GATE_V0`
— select the next platform and ground it in official docs. No live send until a new
explicit task + operator GO.
