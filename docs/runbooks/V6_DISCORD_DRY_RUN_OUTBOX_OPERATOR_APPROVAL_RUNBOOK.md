# V6 Discord Dry-Run Outbox Operator Approval Runbook

## Purpose

Prepare a Discord announcement for operator review without sending it.

## Steps

1. Generate or consume a unified capability/env readiness packet.
2. Build the Discord dry-run outbox packet.
3. Review `discord_preview_text` and `approved_payload_hash`.
4. Confirm the approval record is still pending.
5. If Discord key-name presence is absent, use the manual fallback preview.
6. Do not send live until the separately scoped supervised live pilot task.

## Safety Checks

- `live_send_performed=false`
- `provider_call_made=false`
- `network_call_made=false`
- `raw_secret_values_serialized=false`
- `env_lines_serialized=false`

## Operator Note

Manual paste must be done by Jim/operator. This packet does not authorize automated Discord dispatch.
