# Next Task Pointer

## Recommended Next Task

`TASK_CONTENTOPS_V6_DISCORD_SUPERVISED_DISPATCH_RUNBOOK_AND_UI_READINESS_PANEL_V0`

## Reason

Discord dispatch readiness is now complete across all three verified targets:

- `announcements`
- `substack_drops`
- `product_updates`

## Suggested Objective

Promote tri-target dispatch readiness into operator-facing workflow surfaces.

## Suggested Work

- Add supervised Discord dispatch runbook using existing adapter and approval gate.
- Connect approved payload queue to target-specific dispatch actions.
- Add UI/readiness panel or non-live dispatch history view if useful.
- Keep live dispatch behind explicit operator authorization.

## Constraints

- No live POST unless explicitly authorized.
- Do not print/store raw webhook URLs.
- Do not commit `.env*`.
- Keep `allowed_mentions={"parse":[]}`.
