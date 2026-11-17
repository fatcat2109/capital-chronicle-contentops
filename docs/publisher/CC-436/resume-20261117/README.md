# CC-436 continuation, 17 November 2026

Neo's endpoint responds, and the installed executor verifies retained public
objects again. The remaining live
acceptance condition is **AWAITING_FRESH_MAIN_STATUS_EVENT_FOR_2_MINUTE_TIMING_PROOF**.
No runtime source change was needed in this continuation.

Six targeted checks passed in **13.91 seconds**. They exercise copied-store X
and Notes publication, a plain Python child without a Codex dispatch, duplicate
prevention, lost-return readback recovery, the real minute consumer's automatic
executor selection, and its CLI wiring. See [endpoint-acceptance-tests.xml](endpoint-acceptance-tests.xml).

```powershell
python -m pytest tests/test_neo_endpoint_executor_cc436.py -q -k 'copied_store or status_minute_consumer_selects_automatic_executor or cli_publish_passes_automatic_transport_to_the_real_consumer or lost_publish_return_recovers_by_readback_without_reposting' --disable-warnings --tb=short --junitxml=docs/publisher/CC-436/resume-20261117/endpoint-acceptance-tests.xml
```

## Current endpoint and consumer

[runtime-observation.json](runtime-observation.json) binds the unchanged
`CapitalChronicle-PlanStatusPosts-V1` task to
`pythonw.exe -B scripts\plan_status_posts.py --publish` in
`A:\Capital Chronicle\ContentOps`, with `IgnoreNew`. All five checked entry,
consumer and executor files have identical worktree and operating-root SHA256s.
The task's last observed result was zero; its current run and Neo's local
listener were observed separately.

The installed `NeoBrowserDriver.perform` executed immutable existing READBACK
packets through `http://127.0.0.1:9010/mcp`, in this task's own tab group and the
one existing Neo window. It made no publish action or production-store write:

- [X 2122123689437323291](https://x.com/Capitalnicle/status/2122123689437323291): exact content verified.
- [Note c-385240262](https://substack.com/@capitalchronicle/note/c-385240262): exact content verified.
- The separate [follow-up Note c-388486151](https://substack.com/@capitalchronicle/note/c-388486151)
  correctly failed exact content verification: its two expected visible
  Telegram links are absent. CC-603 already holds its prepared `missing-links`
  reply. That public-content mismatch is retained in
  [endpoint-readback.json](endpoint-readback.json); no check was weakened and
  no repair or repeat post was issued under CC-436.

These current reads establish endpoint and installed readback behavior. They
do not change any object's original confirmation or publication time.

## Live timing

[live-timing.json](live-timing.json) was collected with SQLite `mode=ro`.
It binds natural status rows by their payload `key`, retains their original
source clocks, and joins the existing dispatch, first verified readback and
native endpoint-return records. Later readbacks never replace first
confirmation clocks; dispatch attempts never substitute for public writes.

Eight natural status operations since 11 November have Telegram and browser
dispatches. **Zero X pairs meet 120 seconds; one Notes pair does.** The passing
Notes pair remains 5.1276 seconds before Telegram. The most recent natural
source event is **13 November 06:00 GMT+7**; there were zero source events from
the preceding 60 minutes at collection. Natural status rows are settled,
published or explicitly superseded/stale; the fresh export and completed
minute runs do not manufacture a new status event.

The report also retains recent article/follow-up pairs separately. The latest
article X confirmation was 219.450642 seconds after Telegram, outside the
target, and it has no Notes twin. The later follow-up's X confirmation was
1116.401861 seconds after Telegram; its Notes content mismatch above remains
visible. Neither closes the natural status timing acceptance.

## Delivery and next action

Evidence commit `a3c6935c` was pushed and fast-forwarded into the operating root.
The two consumer/CLI checks then passed there in **3.74 seconds**; see
[installed-consumer-tests.xml](installed-consumer-tests.xml). The verification
and rollback binding is recorded in
[integration-verification.json](integration-verification.json). No runtime
restart is required for this evidence-only delivery.

This branch starts at operating HEAD
`4b83736bde70663c743ba239b1809cb7f5f8d80d`. Fresh `origin/master`
`5be8fc63317be06d8319f3dd51ac4137a107cbb5` is an ancestor, 1,275 commits
behind; using the installed HEAD preserves the current Publisher consumers.
Only this continuation's evidence is delivered. Existing telemetry edits and
unrelated untracked files remain outside the commits.

The observed launch arguments select `gpt-6.1-sol` and effort `max`, labelled
`CONFIGURED_NOT_OBSERVED`; actual runtime model/effort telemetry is unavailable.
No editorial model or public copy was invoked. No schedule, application or
public object was changed.

**Next action:** when Main supplies a new eligible status event, the existing
minute consumer sends the bound X and Notes copies. Read each first verified
confirmation against its own Telegram twin and source clock. Main owns the
new event; Publisher owns the timing readback. Existing objects keep their
original bytes and clocks. Do not repost or invent an event for this test.
