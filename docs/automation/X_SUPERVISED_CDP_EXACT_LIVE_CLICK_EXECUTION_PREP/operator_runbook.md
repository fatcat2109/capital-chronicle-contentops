# X CDP Exact Live-Click Execution Prep — Operator Runbook

## Status

`TASK_CONTENTOPS_V6_X_CDP_EXACT_LIVE_CLICK_EXECUTION_PREP_V0` is complete as local non-executable prep evidence.

## Use

```powershell
python -m live_contentops.x_cdp_exact_live_click_execution_prep_v6 --dry-run --fixture-bundle --write-evidence docs/automation/X_SUPERVISED_CDP_EXACT_LIVE_CLICK_EXECUTION_PREP/task_contentops_v6_x_cdp_exact_live_click_execution_prep_evidence.json
```

Or through the operator lab:

```powershell
python -m live_contentops.operator_browser_lab execution-prep-x-live-click --dry-run --payload-text "<exact payload>" --operator-go-phrase "<exact phrase>" --scope-decision approve_future_scope --cdp-port 9223 --command-line "<operator-supplied process metadata>"
```

## Boundary

This prep packet does not click, publish, append registry, fetch public URL, probe CDP, or read session/secret state.

## Next

`TASK_CONTENTOPS_V6_X_CDP_EXACT_LIVE_CLICK_AUTHORIZATION_V0` must re-verify every gate before any exact live action.
