# V6 Substack Manual Approval Export Evidence Runbook

## Scope

This runbook covers the fixture-only V6 Substack manual approval/export evidence lane surfaced inside `ui/contentops_v5/`.

## Operator flow

1. Review the canonical article studio card in V5.
2. Confirm the export packet ID and exact payload hash.
3. Review the approval/export evidence packet.
4. Use the manual copy checklist only after separate human approval outside this fixture.
5. Do not use Substack API, provider APIs, dispatch queues, schedulers, or live publishing controls.

## Hard blockers

- `live_publish_allowed=false`
- `live_publish_performed=false`
- `substack_api_used=false`
- `provider_call_made=false`
- `network_call_made=false`
- `credential_read_made=false`
- `env_value_read_made=false`
- `browser_session_used=false`

## V5 evidence locations

- Manual Export: pending manual review and checklist.
- Approval Queue: pending approval/export evidence status.
- Evidence Vault: evidence cards and packet hash.

## Non-goals

No live post, no publish, no send, no dispatch, no scheduler, no hidden retry, no env reads, and no credential/session inspection.
