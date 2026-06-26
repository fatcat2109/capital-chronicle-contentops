# Next Task Pointer

## Recommended Next Task

`TASK_CONTENTOPS_V6_DISCORD_APPROVED_OUTBOX_ONE_REQUEST_LIVE_DISPATCH_PILOT_V0`

## Goal

Use the new [discord_dispatch_adapter.py](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/live_contentops/discord_dispatch_adapter.py) to perform one explicitly authorized live dispatch from an approved outbox/candidate packet.

## Suggested Constraints

- Exactly one live Discord POST.
- One target only.
- Existing approved payload/outbox packet only.
- Request budget: `1`.
- Retry budget: `0`.
- Timeout: `10` seconds.
- `wait=false`.
- `User-Agent: CapitalChronicleContentOps/1.0`.
- Write redacted dispatch result packet.

## Prerequisites

- Operator selects payload ID.
- Operator selects target.
- Operator confirms env key already configured locally.
- No additional smoke test needed.
