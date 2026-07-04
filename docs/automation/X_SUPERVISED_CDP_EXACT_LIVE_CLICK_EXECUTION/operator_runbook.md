# X CDP Exact Live-Click Execution — Operator Runbook

## Scope

Use this only after exact authorization passes for one payload, one account, one destination, and one X post click.

## Operator steps

1. Confirm the payload hash from the authorization packet.
2. Confirm the destination account is the intended X account.
3. Confirm kill switch / stop condition is available.
4. Perform exactly one supervised X post click in the live UI.
5. Copy the resulting public X status URL.
6. Run `operator_browser_lab execute-x-live-click` with the captured URL and matching payload hash.

## Stop conditions

- Payload hash mismatch.
- Account/destination uncertainty.
- Missing or non-status public X URL.
- Any UI uncertainty before click.
- Any prior registry append.
- Any request to comment, DM, react, retry, schedule, or publish multiple posts.

## Next task

`TASK_CONTENTOPS_V6_X_CDP_EXACT_LIVE_CLICK_REGISTRY_RECONCILIATION_V0` appends/reconciles registry state only after captured URL and payload hash match.
