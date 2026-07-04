# X CDP Exact Live-Click Authorization — Operator Runbook

## Status

`TASK_CONTENTOPS_V6_X_CDP_EXACT_LIVE_CLICK_AUTHORIZATION_V0` is complete as local exact authorization metadata.

## Use

```powershell
python -m live_contentops.x_cdp_exact_live_click_authorization_v6 --dry-run --fixture-bundle --write-evidence docs/automation/X_SUPERVISED_CDP_EXACT_LIVE_CLICK_AUTHORIZATION/task_contentops_v6_x_cdp_exact_live_click_authorization_evidence.json
```

Or through the operator lab:

```powershell
python -m live_contentops.operator_browser_lab exact-authorize-x-live-click --dry-run --payload-text "<exact payload>" --operator-go-phrase "<exact phrase>" --scope-decision approve_future_scope --cdp-port 9223 --command-line "<operator-supplied process metadata>"
```

## Boundary

This packet authorizes only a later one-click operator-supervised execution task. It does not click, publish, append registry, fetch public URL, probe CDP, or read session/secret state.

## Next

`TASK_CONTENTOPS_V6_X_CDP_EXACT_LIVE_CLICK_EXECUTION_V0` must execute, capture public URL, and append registry only if every exact check still passes.
