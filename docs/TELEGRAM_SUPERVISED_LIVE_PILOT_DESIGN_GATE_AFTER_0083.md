# Telegram Supervised Live Pilot Design Gate

This document serves as the local-only design gate and checklist for the future Telegram supervised live pilot. It ensures that the system is fully prepared to execute a live post but does **NOT** grant live-action authority.

## Status
* **Gate Active**: YES
* **Live Posting Allowed**: NO
* **Mock Testing Allowed**: YES

## Prerequisites for Future Live Go
Before the operator can explicitly authorize a future live posting task (e.g., Task 0084), the following conditions must be met and validated by the gate:

1.  **Exact Live Go Phrase**: The explicit authorization must include the exact phrase:
    `I APPROVE TELEGRAM SUPERVISED LIVE PILOT FOR ONE CHANNEL POST ONLY`
2.  **Strict Scope**:
    *   One manually approved post to a private test sandbox only.
    *   No autonomous replies.
    *   No DMs.
    *   No scheduling.
    *   No cross-platform posting.
    *   No metrics fetching unless separately authorized.
3.  **Local Validations**:
    *   The `live_execution_allowed_now` flag is currently strictly `False`.
    *   No real Telegram credentials (e.g., bot tokens) are read or stored in the repository.
    *   No network access or Telegram API calls are performed during the design phase.
    *   Public posting capability must be completely disabled (`public_postable=False`).
4.  **Required Evidence**:
    *   **Preflight**: Verified Telegram credential policy, no secret logging/printing.
    *   **Dry-run**: Dry-run payload must be successfully rendered.
    *   **Approval Ledger**: The ledger must show `operator_approved_for_live_publish_later`.
    *   **Kill Switch**: Must be set to `permit_only_scoped_telegram_live_pilot`.

## Fallback & Rollback Plan
*   **Rollback**: If an accidental live post occurs, the operator must manually delete the message using the official Telegram app, as the ContentOps sidecar lacks automated deletion capabilities to prevent runaway scripts.
*   **Manual Fallback**: If the ContentOps integration fails, the operator will copy the reviewed content packet and post it manually via the official Telegram client.
