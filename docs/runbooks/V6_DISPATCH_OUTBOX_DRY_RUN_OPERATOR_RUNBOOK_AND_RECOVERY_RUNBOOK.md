# V6 Dispatch Outbox Operator Runbook and Recovery Runbook

This is a local/manual-only runbook for the operator recovery process (`TASK_CONTENTOPS_V6_DISPATCH_OUTBOX_DRY_RUN_TO_OPERATOR_RUNBOOK_AND_RECOVERY_HEAVY_BATCH_V0`).

## Purpose
Establishes preflight verification checklists and recovery procedures for the dispatch outbox dry-run state.
* **No live actions**: Direct publishing remains disabled.
* **Kill-switch**: The local kill-switch `kill_switch_active` is hardcoded to `true`.
* Manual, future, or deferred platform states (such as deferred LinkedIn/Instagram/YouTube/TikTok adapters) are valid states and are not treated as failures.

## Operator Preflight Checklist
1. **Verify local kill-switch flag is active** (Status: verified)
2. **Assert all live credentials and secrets are fully redacted from local database** (Status: verified)
3. **Validate destination room/channel binding descriptors match manual-only fixtures** (Status: verified)
4. **Confirm dry-run payload hash matches the signed canonical draft approval record** (Status: verified)
5. **Ensure manual fallback guidelines are accessible by local operator** (Status: verified)

## Manual Dispatch Fallback Steps
1. **Copy platform-native variant payload** from Platform Preview tab.
2. **Authenticate manually** to the respective platform web interfaces (Substack, Discord, Telegram, X, Threads, Facebook).
3. **Paste payloads into the draft composer**, perform a final visual validation, and post/dispatch.
4. **Wait for public URL generation** on live platforms, and copy URL for the audit import phase.

## Dry-Run Replay Verification Steps
1. **Regenerate dry-run outbox structures** locally from source approval preview to verify build parity.
2. **Inspect outbox dry-run payload text and formatting** against UI container styling.
3. **Ensure dry-run hashes match** across local execution files.

## Rollback & Stop Conditions
* **Payload hash mismatch**: Halt immediately, delete temporary draft preview, and restart intake validation.
* **Unexpected live request**: Trigger kill-switch, lock credentials, and stop local build server.
* **Wording warning triggered**: Reject draft, flag compliance violation, and notify operator.

## Failure Mode & Recovery Matrix
* **Platform API connection timed out**: Retain deferred state; do not retry network calls; fallback to manual publishing.
* **Webhook validation error**: Check structure formats; regenerate JSON payload templates; do not send requests.
* **Formatting error or text truncation**: Adjust styling containment classes (e.g. break-all); regenerate preview.

## Evidence Collection Checklist
1. **Collect generated dispatch outbox dry-run payload hashes** (Status: pending)
2. **Capture local browser screenshots of all V5 dispatch & platform panels** (Status: pending)
3. **Verify zero live/webhook calls are recorded in local transaction logger** (Status: verified)
4. **Save operator recovery runbook and preflight checklist to automation docs** (Status: pending)

## Platform-Specific Manual Handoff & Recovery Notes
* **Substack**: Use Substack dashboard draft editor to paste preview content; schedule manually if needed.
* **Discord Webhook**: Verify mock payload matches Discord webhook body schema; do not invoke live webhooks.
* **Telegram**: Confirm telegram JSON structure meets bot message requirements; copy manually to client.
* **X (Twitter)**: Paste text into composer; ensure character counts remain within post limits; do not automate tweet dispatch.
* **LinkedIn**: LinkedIn is future-gated. Maintain deferred status until explicit live distribution scope is granted.
* **Threads**: Threads requires manual copy-paste from browser; automation endpoints remain disabled.
* **Facebook**: Facebook page post must be created manually via Meta Business Suite interface.
* **Instagram**: Instagram is deferred. Maintain deferred status. Do not try to authenticate via mobile/API.
* **YouTube**: YouTube video description is deferred. Maintain deferred status.
* **TikTok**: TikTok video caption is deferred. Maintain deferred status.
