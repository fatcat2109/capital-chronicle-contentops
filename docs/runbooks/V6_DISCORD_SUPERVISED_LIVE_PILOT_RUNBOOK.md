# V6 Discord Supervised Live Pilot Runbook

## Purpose

Execute one supervised Discord webhook pilot only after exact operator approval gates pass.

## Operator Inputs

- Dry-run outbox packet path
- Separate operator approval declaration path
- Env key `DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK`
- Kill switch state
- Request budget `1`

## Safe Blocked Run

Without an approval declaration, run the module to emit a blocked sample result. This must show:

- `live_send_attempted=false`
- `request_count=0`
- `result_class=blocked`

## Live Pilot Run

Only proceed when Jim/operator supplies a declaration with:

- `operator_approval_status=approved`
- Non-empty `approved_by`
- Non-empty `approved_at`
- Exact payload hash matching the recomputed preview hash

The module performs no retry and records only redacted outcome data.

## After Action

Record the final result class, status class, request count, and safety booleans. Do not copy webhook values, headers, env lines, or response bodies into evidence.
