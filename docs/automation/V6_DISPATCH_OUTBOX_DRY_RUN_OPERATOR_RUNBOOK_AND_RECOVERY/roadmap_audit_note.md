# V6 Dispatch Outbox Operator Runbook and Recovery Audit Note

This document audits the V6 operator recovery and manual fallback mechanisms.

## Objectives
* Establish a deterministic, human-in-the-loop manual override for all platform publications.
* Formulate clear stop conditions and rollback triggers to avoid any accidental auto-publishing, credential leak, or trading recommendation delivery.
* Certify that manual, future, or deferred platform states (such as deferred LinkedIn/Instagram/YouTube/TikTok adapters) are valid, expected recovery states and not system failures.

## Design and Safety Gates
* **Kill-Switch Active**: `kill_switch_active` is hardcoded to `true`. This locks any automated webhook or API calls.
* **Redaction Verification**: No real secret materials, API keys, tokens, or credential values are written to recovery packages.
* **Zero Live Actions**: The UI controls for direct sending/publishing are disabled by default.
