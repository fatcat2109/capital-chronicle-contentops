# CC-283: one browser turn per destination, and a Claude Code surface may publish

From the ContentOps V1 lane (Claude, Opus 5.5), 5 Nov 2026. The item was assigned by Ops Product (CC-256 R12).

## Part 1 (live 2a4a83e8): a Claude Code surface

`native_neo_executor_v1.submit` accepts `CLAUDE_CODE_SESSION` with its own tool name (`mcp__browseros-neo__run`) and the same invocation evidence. A surface and tool that do not belong together are refused, so Claude is never recorded as Codex. Tests: `tests/test_native_neo_claude_surface_cc283.py` (8).

## Part 2: one composed Neo run per destination (design A, Ops Product 5 Nov)

In a publishing operation (`allow_publish`), `bind_native_neo_coordinator` turns on `identity_at_action`. For every Neo destination except Substack:

- **No separate identity step.** `publication_readiness` returns `READY_IDENTITY_AT_ACTION` instead of asking for an identity step first. The readiness manager never stores that state: it is valid only inside the run. The coordinator's two readiness gates accept it.
- **The claim still comes first.** `begin(PUBLISH)` claims the write before the act. Its action packet carries `composed_run`: one script checks the expected account, publishes once and reads back.

`submit` applies Ops Product's four conditions. Each has a test in `tests/test_native_neo_composed_run_cc283.py`, which holds 6 tests:

1. **The account must match.**
   - The composed identity must be authenticated, match the binding's expected identity and stable id, and be observed between the claim and the publish click.
   - A mismatch or an unreadable identity gives FAILED_BEFORE_WRITE with no click.
2. **A stop before the click frees the claim; a failure after it does not.**
   - FAILED_BEFORE_WRITE with no click is a definite no-write: the adapter returns it before its identity comparison, and the coordinator records DEFINITE_NO_WRITE, so a retry is allowed.
   - A failure after the click, or a write without a matched account, is UNKNOWN_WRITE. The existing readback runs before any retry.
3. **The deferred proof stays inside its run.**
   - It exists only with `allow_publish`.
   - A missing identity, or one observed before the claim or after the click, is refused.
   - The run's identity is evidence for that publish only: it is not stored as a readiness proof for another destination or operation.
4. **The readback is reused.** The run's readback is stored as the READBACK request that `NeoDestinationHandoff.request()` builds, so `fresh_readback_request` (10 minutes) serves it. The adapter still checks the content as before, and no further agent turn is needed.

## Regression, 5 Nov 22:57-23:12Z

The 42 test files that touch the executor, the adapter, the readiness manager or the coordinator: 861 passed, 12 failed. All 12 also fail on the clean 5 Nov baseline (95c9e3c3), so the change adds no new failure.

## Acceptance still to come

The next piece's X, YouTube and LinkedIn copies each take one agent turn, and their times go into this folder.
