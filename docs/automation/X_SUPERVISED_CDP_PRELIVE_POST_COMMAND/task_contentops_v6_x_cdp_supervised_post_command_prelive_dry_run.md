# X CDP Supervised Post Command Pre-Live Dry Run

Task: `TASK_CONTENTOPS_V6_X_CDP_SUPERVISED_POST_COMMAND_PRELIVE_DRY_RUN_V0`

## Purpose

Validate an exact X post payload and ContentOps browser-profile binding before any future supervised live click.

## Command

```powershell
python -m live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 --dry-run --payload-text "Capital Chronicle educational briefing: supervised pre-live X payload validation." --cdp-port 9223 --command-line "msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"
```

Operator wrapper:

```powershell
python -m live_contentops.operator_browser_lab prelive-x-post --dry-run --payload-text "Capital Chronicle educational briefing: supervised pre-live X payload validation." --cdp-port 9223 --command-line "msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"
```

Fixture evidence:

```powershell
python -m live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 --dry-run --fixture-bundle
```

## Safety Boundary

- `--dry-run` is required.
- No browser launch.
- No CDP probe.
- No DOM read.
- No cookie, localStorage, sessionStorage, token, header, env, or credential read.
- No X API or paid API call.
- No public URL fetch.
- No registry append.
- No click, publish, scheduler, retry, comment, DM, or reaction.

## Ready State

A packet is ready for operator review only when:

1. Payload text is non-empty and within 280 characters.
2. Payload contains no secret/session/advice-like markers.
3. The profile guard classifies the supplied CDP command metadata as `contentops_profile_ok`.
4. Registry expectation is scaffolded for future post-click public URL capture.

Even then, `live_click_allowed` remains `false`; a future exact approved live GO phrase task is required.

## Evidence

- Evidence bundle: `docs/automation/X_SUPERVISED_CDP_PRELIVE_POST_COMMAND/task_contentops_v6_x_cdp_supervised_post_command_prelive_dry_run_evidence.json`
- Tests: `tests/test_x_cdp_supervised_post_command_prelive_dry_run_v6.py`
