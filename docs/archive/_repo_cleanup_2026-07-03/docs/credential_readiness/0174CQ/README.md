# 0174CQ — Telegram Second Supervised Post Dry-Run + Durable Ledger Gate

Strictly local preflight that prepares a **second** supervised Telegram post via
dry-run, approval-hash lock, redacted preview, and a durable ledger. **It does
not send.** A future second live send would be a separate task with a new
operator GO (`0174CR`).

## Guarantees

- No network: no `urllib` / `requests` / `httpx` / `socket` / `dotenv` imports.
- No credential/env read; no `.env`, no `os.environ`, no `getenv`.
- No Telegram API call: no `sendMessage` / `getMe` / `getChat` / `getChatMember`
  / `getUpdates` / webhook / scheduler / reply / DM / metrics / scraping.
- Fail-closed / preview-only by default. The ledger is written only with the
  explicit `--write-telegram-second-dry-run-ledger` flag.
- Deterministic ledger JSON (sorted keys, stable separators, trailing newline).
- Redaction scanner runs before write and blocks token-like values, Telegram
  bot API URLs, raw `@handles`, long numeric ids, and forbidden raw keys.
- Reuses 0174CM forbidden-language + canonical-hash helpers; does not modify
  0174CM / 0174CN / 0174CO / 0174CP.

## Commands

```
# Preview (no write):
python -m live_contentops.cli telegram-second-supervised-post-dry-run-ledger-gate

# Write the durable ledger:
python -m live_contentops.cli telegram-second-supervised-post-dry-run-ledger-gate --write-telegram-second-dry-run-ledger
```

## Artifact

`docs/credential_readiness/0174CQ/telegram_second_supervised_post_dry_run_ledger.json`
