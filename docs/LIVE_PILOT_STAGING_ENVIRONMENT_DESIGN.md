# LIVE PILOT STAGING ENVIRONMENT DESIGN

## 1. Environment Modes
- **Local-Only Dev Mode:** Current state. Simulator only.
- **Dry-Run Simulator Mode:** Deterministic policy and mock providers.
- **Future Credentialed Staging Mode:** Real keys, real network, but locked entirely to a private staging channel sandbox (e.g. Telegram test channel).
- **Future Limited Live Mode:** Locked to a public channel, but 1-per-day manual approval constraint.

## 2. Environment Separation
The `cc-live-contentops` repository is the absolute boundary. It will ingest clean bundles from `cc-contentops`. It will never mutate `cc-contentops`.

## 3. The Staging Flow
1. **Bundle Ingestion:** `cc-live-contentops` loads local bundle.
2. **Policy Gate:** Deterministic regex gating evaluates the bundle payload.
3. **Provider Dry-Run Gate:** Simulator validates request syntax.
4. **Platform Dry-Run Gate:** Simulator validates staging contract.
5. **Publish Job Quarantine:** The payload is held in the local file-backed approval queue.
6. **Manual Review Gate:** Operator types `publish_now`.
7. **Kill-Switch Check:** Final verification before network dispatch.
8. **Audit Event Capture:** Every state change logs an event.

**NO PRODUCTION OR LIVE BEHAVIOR MAY PROCEED UNTIL EXPLICIT GO.**

## 4. Output and Log Redaction
The audit log and all CLI outputs explicitly scrub and replace secret-looking strings with `[REDACTED]`.

## 5. Runtime Directory Structure (Gitignored)
The following directories must be created locally but explicitly excluded via `.gitignore` to prevent leakage:
- `outputs/`
- `runtime_state/`
- `audit_logs/`
- `operator_packets/`
- `staging_runs/`
- `quarantined/`
