# V6 Discord Dry-Run Outbox Operator Approval Contract

This contract defines the Discord dry-run outbox and operator approval spine for the Fast Ship V6 Discord lane.

## Scope

- Build a Discord-native message preview from a canonical article fixture or operator-provided article object.
- Bind the exact preview text to a deterministic public audit hash.
- Emit pending operator approval, dry-run outbox, redacted audit, and manual fallback records.
- Mark supervised live-pilot candidacy only when Discord key-name presence is true and all local records are valid.

## Safety Boundary

- No Discord message is sent.
- No provider API is called.
- No network or browser action is performed.
- No credential value is read, logged, hashed, digested, measured, or serialized.
- Env scanning is key-name presence only through the unified capability/env readiness packet.

## Approval Defaults

The operator approval record is pending by default:

- `operator_approval_status=pending`
- `approved_by=null`
- `approved_at=null`
- `live_send_allowed=false`

## Manual Fallback

Manual fallback remains available even when the Discord credential key name is absent. The packet includes a copyable message preview and exact payload hash. Jim/operator must perform any manual paste separately.

## Next Boundary

Recommended next task:

`TASK_CONTENTOPS_V6_DISCORD_SUPERVISED_LIVE_PILOT_FROM_APPROVED_OUTBOX_HEAVY_BATCH_V0`
