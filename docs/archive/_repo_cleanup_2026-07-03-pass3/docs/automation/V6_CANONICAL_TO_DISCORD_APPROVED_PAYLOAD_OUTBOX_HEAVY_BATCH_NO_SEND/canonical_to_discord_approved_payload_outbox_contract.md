# V6 Canonical to Discord Approved Payload Outbox Contract - No Send

## Scope

Local-only bridge from operator-approved canonical payload declaration to Discord outbox packet.

## Hard State

- No live send.
- No env or `.env` read.
- No credential value read.
- No Discord API or webhook call.
- No browser session.
- No executable request artifact.
- No public URL.
- No metrics.
- No publication readiness.
- No dispatch.

## Input Requirements

- Final pre-live readiness packet must be eligible for future explicit live task only.
- Payload declaration must be operator approved and hash-bound.
- Payload is not marked public-postable in this task.
- Destination binding absent now and required later.
- Credential key name is symbolic only: `DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK`.

## Output Requirements

- `local_outbox_packet_created` is true.
- `local_outbox_packet_non_executable` is true.
- `eligible_for_future_explicit_live_send_task` may be true only when all checks pass.
- `eligible_for_live_send_now` is always false.
- `dispatch_allowed`, `publication_ready`, and `runtime_truth` are always false.

## Future Separate Live Task Gate

Future task must include exact GO, destination binding, credential presence membership-only proof, payload hash revalidation, kill switch, redacted audit, single request budget, zero hidden retry, stop-on-uncertainty, and manual fallback.
