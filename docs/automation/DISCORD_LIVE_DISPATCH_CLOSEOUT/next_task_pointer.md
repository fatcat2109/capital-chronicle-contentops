# Next Task Pointer

## Recommended Next Task

`TASK_CONTENTOPS_V6_DISCORD_SUBSTACK_APPROVED_OUTBOX_ONE_REQUEST_LIVE_DISPATCH_PILOT_V0`

## Goal

Run one approved-outbox adapter dispatch pilot for `substack_drops`, using existing verified adapter and smoke evidence.

## Suggested Constraints

- Exactly one live POST only if explicitly authorized.
- No retry.
- Use existing `live_contentops.discord_dispatch_adapter`.
- Verify approved payload hash before dispatch.
- Store only redacted result packet.
- Do not print or store raw webhook URL.

## Current Readiness

- `announcements`: `ready_for_supervised_dispatch`
- `substack_drops`: `ready_for_adapter_dispatch_pilot`
- `product_updates`: `ready_for_adapter_dispatch_pilot`
