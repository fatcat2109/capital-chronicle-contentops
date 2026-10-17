# ContentOps BrowserOS Neo Wave 4 Scheduled Dry-Run — 2026-10-17

Status: `IMPLEMENTED / OFFLINE_FIXTURES_PROVEN / DISABLED_BY_DEFAULT / NO_SCHEDULER_START / NO_PUBLICATION_AUTHORITY`

## Scope

This slice adds one explicit opt-in branch to the existing Simple scheduler entrypoint. The normal
four-window scheduler and its detached process owner remain unchanged. The new branch exits before
constructing `SimpleGeminiLocalScheduler` or the publication handoff, so it does not start a
Windows task/process, read or write the durable store, call a model/provider, publish, comment, or
change an account/session.

The seam reuses `BrowserOSNeoReadOnlyPreflight` and accepts an injected wrapper around the existing
`dry_run_browser_rendered_recovery` resolver contract. It is disabled by default and calls neither
runner when disabled.

## Contract

- CLI opt-in: `scripts/run_v1_simple_gemini_scheduler.py --browseros-dry-run`.
- Opt-in preflight uses `auto_open=false`; the official BrowserOS shortcut is never launched by this
  scheduled seam.
- Healthy preflight returns structured `PASS`; unavailable or timeout returns `BROWSER_UNAVAILABLE`;
  profile ambiguity, identity/tool-boundary mismatch, or recovery contract violations return a
  fail-closed receipt.
- Recovery metadata preserves HTTP-first ordering, the shared request budget, and one maximum
  BrowserOS recovery attempt. An injected recovery wrapper can return the existing resolver's
  `HTTP_SUCCESS_NO_BROWSER` or `BROWSER_RENDERED_RECOVERY_DRY_RUN_PASS` statuses.
- The receipt always reports zero scheduler ticks, durable-store writes, model/provider calls, and
  public writes.

## Focused proof

```powershell
python -m pytest -q tests/test_v1_simple_gemini_scheduler_browseros_dry_run_v1.py tests/test_v1_simple_gemini_scheduler_process_v1.py tests/test_v1_simple_gemini_scheduler_v1.py tests/test_run_v1_simple_gemini_newsroom_cli_v1.py
```

The new fixture suite covers disabled zero-call behavior, healthy preflight, injected resolver
recovery, `BROWSER_UNAVAILABLE`, timeout, profile ambiguity, attempt-budget violation, and the
entrypoint's early exit before scheduler/publication construction. All BrowserOS and resolver
calls in these tests are injected; no live browser session is used.

## Integration boundary

- Implemented/tested: this branch only; no live scheduler or host activation occurred.
- Integrated/merged/deployed/live-published: not yet; branch starts at `master` head
  `75d3c748cae97c27473a235acfa4003315f910db`.
- V2, public-write authority, durable publication ownership, and account/session state remain
  unchanged.
