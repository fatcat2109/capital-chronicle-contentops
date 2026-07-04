# Telegram Operator Setup — Batch B Read-Only Proof

Task: `TASK_CONTENTOPS_MULTI_PLATFORM_LIVE_FOUNDATION_BATCH_B_OPERATOR_SETUP_TELEGRAM_READONLY_PROOF_AND_PROBE_HARDENING_V0`

## Scope

This setup supports Telegram read-only identity proof only:

- `getMe` confirms bot credential identity.
- `getChat` confirms configured destination is readable by bot.

No posting, sending, publishing, uploading, scheduling, replying, DM, scraping, webhook, or polling behavior is allowed in this batch.

## Approved local keys

Place keys in repo-local `.env.local` only if operator chooses to run proof:

```text
TELEGRAM_BOT_TOKEN=<operator-provided value>
TELEGRAM_CHANNEL_ID=<operator-provided value>
TELEGRAM_OPERATOR_CHAT_ID=<operator-provided value>
```

Never paste raw values into chat, docs, screenshots, commits, shell history snippets, or evidence packets.

## BotFather setup

1. Create or select bot in BotFather.
2. Copy token only into local `.env.local`.
3. Do not display token in browser QA evidence.
4. Rotate token if it was exposed anywhere.

## Channel setup for `getChat`

1. Add bot to target Telegram channel/group.
2. Use channel id or public channel handle as `TELEGRAM_CHANNEL_ID`.
3. Run Batch B proof.
4. Treat any redacted blocked result as evidence, not reason to attempt write methods.

## Read-only proof command

```powershell
python -m live_contentops.telegram_batch_b_readonly_proof --repo-root . --live-readonly-telegram --write-evidence docs/automation/MULTI_PLATFORM_LIVE_FOUNDATION_BATCH_B/telegram_readonly_proof_redacted.json
```

## Hard safety boundary

- Raw token never persisted.
- Raw chat id never persisted.
- Raw Telegram response never persisted.
- Request budget is one per endpoint family.
- Auto retry is disabled.
- Redirects fail closed.
- Write methods are blocked by policy and tests.
