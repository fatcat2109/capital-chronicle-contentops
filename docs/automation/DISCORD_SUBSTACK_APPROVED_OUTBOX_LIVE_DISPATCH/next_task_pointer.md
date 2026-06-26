# Next Task Pointer

## Recommended Next Task

`TASK_CONTENTOPS_V6_DISCORD_PRODUCT_UPDATES_APPROVED_OUTBOX_ONE_REQUEST_LIVE_DISPATCH_PILOT_V0`

## Reason

`announcements` and `substack_drops` now have adapter-driven approved-outbox live dispatch evidence.

Remaining verified smoke target:

- `product_updates`

## Suggested Objective

Use the existing reusable Discord dispatch adapter to perform exactly one approved-outbox live dispatch for `product_updates`.

## Suggested Constraints

- Require explicit operator authorization for exactly one Discord webhook POST.
- Use `DISCORD_PRODUCT_UPDATES_WEBHOOK_URL`.
- Keep retry budget `0`.
- Keep `wait=false`.
- Keep `User-Agent: CapitalChronicleContentOps/1.0`.
- Do not print/store raw webhook URL.
- Do not commit `.env*`.
- Do not record response body or headers.
