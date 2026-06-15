# Approval Ledger, Kill Switch, and Redacted Audit (0131)

## What This Layer Is
This layer provides deterministic local authority checks between 0130 (Dry Run Renderer) and future mock/live publishing flows (e.g. 0132 Mock Publish). It verifies that an operator explicitly approved a specific dry-run payload, and that the kill switch globally permits the desired execution.

## What This Layer Is Not
- This does **NOT** publish content.
- This does **NOT** schedule content.
- This does **NOT** interact with live APIs, network sockets, or credentials.

## Kill Switch
The `kill_switch_state` is rigidly enforced to block all live posting. `kill_switch_enabled` must always be `true`. `live_publish_allowed_now` and other external side-effect flags must be `false`. `mock_publish_allowed_when_enabled` allows local sandbox execution for the forthcoming 0132 task.

## Redacted Audit
Any payload evaluated by this layer must be documented into a `redacted_audit_event`. The validator strictly inspects the stringified payload for common secret patterns (e.g. `Bearer`, `api_key=`, `fake_token`) and hard-blocks the event if unredacted traces are found, preventing secrets from leaking into the test or log traces.
