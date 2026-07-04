# X Adapter Dry-Run and Staging Contract

The local X dry-run adapter (`cc-live-contentops/live_contentops/adapters/x_adapter.py`) simulates X/Twitter posting behavior without actual platform APIs, tokens, or network requests.

### Purpose
- Converts upstream provider simulator results into platform-shaped post/thread previews.
- Strictly offline, enforces `safe_for_publish = False`.
- Evaluates policy bounds again.

### Safety Rules
- **No OAuth/Bearer Tokens:** Adapter explicitly scans for and rejects values shaped like bearer tokens, API keys, or oauth tokens.
- **No Live Handles/IDs:** Attempts to send to strings resembling real `@handle` or `123456789012345678` IDs are rejected unless marked explicitly as a placeholder.

### Staging Contract
`build_x_staging_contract()` defines the absolute checklist (credential acquisition, approval gating, quarantine rules, daily post caps) that must be true before this adapter is ever converted into a real HTTP executor.
