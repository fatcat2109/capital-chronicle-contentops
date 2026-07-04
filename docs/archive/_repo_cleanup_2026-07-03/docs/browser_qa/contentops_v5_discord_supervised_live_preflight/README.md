# Browser QA Evidence — Discord Supervised Live Preflight

This directory contains the visual browser verification artifacts for the Discord supervised live preflight.

## Target Surface
* **Target Layout**: Local V5 Dashboard surface only (`http://localhost:5173/`).
* **Legacy Exclusion**: No V4, static, or other legacy views are modified or targeted.

## Verification Boundaries
* The screenshots serve as visual layout evidence only. They do not represent live environment execution readiness.
* The Discord supervised live preflight is fully review-only.
* The source parser and normalized candidate are currently in a blocked state due to a missing operator source artifact.
* **Locks & Invariants verified**:
  * Zero Discord webhook execution or network calls occurred.
  * Zero executable outbox entries or real approval ledger entries were written.
  * No external network request was initiated except for local Vite rendering and official Discord documentation reading.
  * No LLM provider or platform API calls were performed.
  * No browser session, environment variable, or credential values were read (presence check only).
  * No scheduler or automatic retry capabilities are active.
  * All actual dispatch controls are disabled.

## Screenshots List
1. **Approval Queue** ([approval_queue_discord_supervised_live_preflight.png](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/browser_qa/contentops_v5_discord_supervised_live_preflight/approval_queue_discord_supervised_live_preflight.png))
2. **Platform Preview** ([platform_preview_discord_supervised_live_preflight.png](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/browser_qa/contentops_v5_discord_supervised_live_preflight/platform_preview_discord_supervised_live_preflight.png))
3. **Preflight Bundle** ([preflight_bundle_discord_supervised_live_preflight.png](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/browser_qa/contentops_v5_discord_supervised_live_preflight/preflight_bundle_discord_supervised_live_preflight.png))
4. **Evidence Vault** ([evidence_vault_discord_supervised_live_preflight.png](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/browser_qa/contentops_v5_discord_supervised_live_preflight/evidence_vault_discord_supervised_live_preflight.png))
