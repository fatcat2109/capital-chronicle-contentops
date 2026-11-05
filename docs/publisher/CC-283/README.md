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

## Regression, 4 Nov 22:57-23:12Z

The 42 test files that touch the executor, the adapter, the readiness manager or the coordinator: 861 passed, 12 failed. All 12 also fail on the clean baseline 95c9e3c3 (4 Nov 21:04Z), so the change adds no new failure.

## Acceptance: the PPI piece, 5 Nov

This is the first piece published after part 2 went live: CC-124 run `docs/publisher/CC-124/run-20261105-0610`, read from `final-publication-status-verified.json` and the step files. Every Neo destination used the composed run, labelled CODEX_EXEC with `mcp__browseros_neo__run`.

| Destination | Claim | Click | Recorded | Write runs |
|---|---|---|---|---|
| LinkedIn company | 00:30:28Z | 00:32:39Z | 00:34:03Z | 1 |
| X | 00:35:16Z | 00:49:55Z | 00:51:38Z | 2: the first left the third reply partial; a correction run (click 01:08:35Z, recorded 01:12:19Z) completed the thread |
| YouTube | 00:51:55Z | 00:54:03Z | 00:58:21Z | 1 (on 4 Nov: three turns, 18.2 min) |

- **One agent turn:** met for YouTube and LinkedIn company, not for X.
  - X spent 14 min 40 s between claim and click, with no recorded step.
  - Why the third reply was partial is NOT VERIFIED: the run's evidence does not say.
- **LinkedIn personal** goes through the API, not Neo. It returned `LinkedInAmbiguousWriteError` at 00:29:07Z and on its one retry at 01:02:17Z. The readback at 01:17:05Z found it absent, so the run keeps DISTRIBUTION_INCOMPLETE.
- **Every other destination** went out in the article's own run.
- **Owners:** Ops Product gave the X partial reply to this lane (below). The LinkedIn API ambiguity is CC-296 (Codex Publisher).
- **Second reading:** the Southwest piece (run-20261105-0832), below.

## The X partial reply and the 14 min 40 s (5 Nov)

- **What was posted (VERIFIED).** `x-four-post-readback.json` (01:09:13Z) shows the third reply as "Readers decide whether to trade.". It lost its first paragraph, up to the blank line: "Retrospective analysis, written on 5 November 2026 (GMT+7) Analysis, not financial advice." The root and the second reply match the approved posts exactly. The fourth reply, the correction, carries the whole notice.
- **Why (NOT VERIFIED).** The run keeps only the composed run's return: identity, stage and a page excerpt. The script the agent wrote is not retained. Nothing compared the composer with the approved posts before the click, so a box holding part of its post went out.
  - The likely mechanisms are text entered before the newly added box was ready, or entered paragraph by paragraph.
  - It is intermittent: Southwest's three-post thread went out whole by the same path.
  - A no-post reproduction in the live X composer was not run. Unsent composer text can carry over to another X tab, and Codex Publisher publishes in that browser.
- **The 14 min 40 s (inference from the record).** X was claimed at 00:35:16Z. No X step is recorded until the click at 00:49:55Z, and that run took 1 min 42 s from click to record. In between, the same agent finished the LinkedIn company confirmation: the media comparisons, the observation and the response, committed as a74b2bb8 at 00:49:33Z. That was 22 s before the X click.

### Fix (native_neo_executor_v1, the composed run packet)

- **`2_compose`:** enter each post in its own box, in order. For a thread, wait until each new box exists and has focus, then enter the post's whole text in one operation.
- **`3_verify_before_click`:** this step carries the exact posts (`expected_posts`).
  - Before the click, read every box back and compare it with its post (whitespace collapsed, links allowed to render shortened).
  - Re-enter a differing box once.
  - If a post still differs, return FAILED_BEFORE_WRITE, stage BEFORE_PUBLISH_CLICK, with no click. That is a definite no-write, so the claim is released.
  - Return the texts read as `composed.pre_click_posts`, so the next failure is diagnosable.
- **`after_run`:** submit the return at once and start the next destination. Extra checks of a destination already read back wait until every destination has gone out.
- **`one_run`:** the run replaces the request's legacy `steps` list (no separate identity, snapshot or binding step).
- **Tests:** `tests/test_native_neo_verify_before_click_cc283.py` (3). With the composed-run, Claude-surface, executor and handoff files, 91 pass.

## Second reading: the Southwest piece, 5 Nov

From CC-124 run `docs/publisher/CC-124/run-20261105-0832`, read from `live-consumer-acceptance.json` and `publication-final-summary.json`.

| Destination | Claim | Click | Result |
|---|---|---|---|
| LinkedIn company | 02:21:31Z | by 02:26:16Z (the dispatch clock was not recorded; this is an upper bound from the return) | confirmed, link and image |
| X | 02:32:29Z | 02:34:03Z | confirmed: all three posts, link and image, with no correction |
| YouTube | 02:36:19Z | 02:40:47Z | confirmed |

- **No correction or repair is recorded for any of the three.** Each has one claim and one click. X took 1 min 33 s from claim to click.
- **Outside the composed path:**
  - LinkedIn personal (API) is again absent (CC-296).
  - Threads (API) reads `RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE`.
