# Telegram Adapter Dry-Run and Staging Contract

The local Telegram dry-run adapter (`cc-live-contentops/live_contentops/adapters/telegram.py`) simulates Telegram delivery behavior without actual platform APIs, tokens, or network requests.

### Purpose
- Converts upstream provider simulator results into platform-shaped message previews.
- Strictly offline, enforces `safe_for_publish = False`.
- Evaluates policy bounds again.

### Safety Rules
- **No Bot Token:** Adapter explicitly scans for and rejects values shaped like a Telegram API bot token.
- **No Live Chat ID:** Attempts to send to strings resembling real `@channel` or `-100123...` IDs are rejected unless marked explicitly as a placeholder.

### Staging Contract
`build_telegram_staging_contract()` defines the absolute checklist (credential acquisition, approval gating, quarantine rules) that must be true before this adapter is ever converted into a real HTTP executor.
