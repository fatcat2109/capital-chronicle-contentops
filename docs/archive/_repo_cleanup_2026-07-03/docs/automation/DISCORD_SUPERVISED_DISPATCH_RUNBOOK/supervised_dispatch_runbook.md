# Discord Supervised Dispatch Runbook

## Status

Readiness status: `PASS`
Supervised Discord dispatch ready: `true`

## What Is Verified

The Discord approved-outbox adapter path is live verified for all three destinations.
Each accepted pilot used one request, zero retries, `wait=false`, and redacted evidence only.

## Ready Targets

| Target | Payload ID | Payload type | Last HTTP | Last result | Env key name |
|---|---|---|---:|---|---|
| `announcements` | `discord_dryrun_announcement_001` | `announcement` | `204` | `PASS` | `DISCORD_ANNOUNCEMENTS_WEBHOOK_URL` |
| `substack_drops` | `discord_dryrun_substack_drop_001` | `substack_drop` | `204` | `PASS` | `DISCORD_SUBSTACK_DROPS_WEBHOOK_URL` |
| `product_updates` | `discord_dryrun_product_update_001` | `product_update` | `204` | `PASS` | `DISCORD_PRODUCT_UPDATES_WEBHOOK_URL` |

## Required Approval Before Live Dispatch

Before any future live dispatch, operator must confirm:

1. Payload is in approved/outbox state.
2. Target binding matches target-specific destination binding.
3. Payload hash matches hash approval gate packet.
4. Jim gives explicit authorization for exactly one dispatch.
5. Request budget and retry budget are explicit.

## Future Supervised Dispatch Command Pattern

```powershell
python -m live_contentops.discord_approved_outbox_live_dispatch --target <target_name> --payload-id <payload_id> --execute --output <redacted_result_packet.json>
```

Use only one of: `announcements`, `substack_drops`, `product_updates`.

## Forbidden

- No autonomous posting.
- No hidden scheduler.
- No unapproved target mutation.
- No raw webhook URL printing or storage.
- No response body/header recording by default.
- No retry unless a future approved task changes policy.
- No financial advice, trading signal, or market-direction language.

## Result Packet Interpretation

- `PASS` with HTTP `2xx`: dispatch succeeded.
- `FAIL` with HTTP `403`: credential unauthorized or blocked.
- `FAIL` with HTTP `404`: webhook not found or deleted.
- `BLOCKED`: local precondition failed before dispatch.

## Recovery From Non-2xx

1. Stop. Do not retry automatically.
2. Preserve redacted result packet only.
3. Verify credential handle and target binding without printing secret values.
4. Re-run dry-run/preflight only.
5. Request explicit authorization before any new live attempt.
