# Substack Live Publish Blocker Runbook

Task window: `TASK_0037` through `TASK_0051`.

## Known Blockers

### Wrong Edge/CDP profile

Symptom:

```text
connect ECONNREFUSED 127.0.0.1:9222
```

Fix:

```powershell
python -m live_contentops.operator_browser_lab open --platform substack
```

Use profile:

```text
A:\Capital Chronicle\operator-browser-profiles\contentops-social-main
```

Do not use Edge `Default`, `Profile 1`, or `Profile 2` unless rebuilding login state.

### Continue disabled after title fill

Symptom:

```text
Continue button visible but disabled.
```

Observed cause:

```text
Please replace the template text before you publish
```

Fix order:

1. Fill main editor title.
2. Fill subtitle if present.
3. Replace body template text, not only preview/settings title.
4. Wait for Substack validation/autosave.
5. Click `Continue` only after enabled.

Evidence:

- `task_0049_live_publish_evidence.json`
  - `body_replaced=true`
  - `continue_enabled_after_fill=true`
  - `continue_click_succeeded=true`

### Final publish label is not `Publish`

Symptom:

```text
publish_button_not_enabled
```

Observed cause: final action button label was:

```text
Send to everyone now
```

Fix: treat enabled `Send to everyone now` as final publish action after checks:

- no enabled `Schedule` action
- no raw secrets/DOM/screenshots/headers/body captured
- operator live-run authority exists

Evidence:

- `task_0050_publish_screen_diagnostics.json`
  - detected enabled `Send to everyone now`
- `task_0051_live_publish_evidence.json`
  - `final_button_label="Send to everyone now"`
  - `final_click_succeeded=true`

## Safe Diagnostic Rules

Keep evidence boolean/metadata-only:

- no DOM dump
- no screenshot
- no private URL
- no response body
- no response headers
- no cookies/localStorage/sessionStorage
- no raw secret output

## Minimal Recovery Loop

```powershell
python -m live_contentops.operator_browser_lab open --platform substack
python -m live_contentops.substack_operator_publish_preflight_cli --use-current-draft --task-id <id> --execute --allow-continue-preflight-click --operator-confirmation CONTINUE_PREFLIGHT_ONLY_NO_PUBLISH --output docs/automation/V6_SUBSTACK_OPERATOR_DRAFT_COMMAND/task_<id>_continue_preflight_evidence.json
```

If `Continue` remains disabled, inspect for template warning and replace body template text.

If final screen lacks `Publish`, inspect enabled action labels; Substack may use `Send to everyone now` for web-only publication.

## Retry Note: TASK_0055

If prior final click returns `PASS` but operator cannot see live post, retry from current editor state after `Continue` is enabled.

Observed successful retry:

- `continue_label="Continue"`
- `continue_click_succeeded=true`
- `final_button_label="Send to everyone now"`
- `final_click_succeeded=true`
- `result_status="PASS"`

Evidence: `task_0055_retry_continue_final_evidence.json`.

