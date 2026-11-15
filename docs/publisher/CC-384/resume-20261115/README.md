# CC-384 resumed verification

The implementation remains installed and connected to the existing minute
publisher. No source change or new publication was needed. The old
`CC383_LIVE_EXPORT_FIELDS_PENDING` cause is gone. Current completion is
**BLOCKED: NEO_ENDPOINT_CONNECTIONERROR**, observed at about **22:17 GMT+7,
15 November 2026**, when initializing the existing local Neo MCP endpoint
`http://127.0.0.1:9010/mcp` for Telegram's public channel readback.

The next action is to restore that existing Neo connection, then have Publisher
read the exact Telegram object on `https://t.me/s/CapitalChronicle?before=115`.
This run did not start or restart a browser, use another browser, read signed-in
Telegram, change a schedule, or resend a historical plan.

## Source and consumer

[Installed consumer evidence](installed-consumer.json) verifies that delivery
`c57e27d9413eb3569e5c2d4fff970fa15efcdb15` is an ancestor of operating HEAD
`cb2bad3d1de06006af0a0dc696c482ed2bfc4b26`. The six relevant source/test files
match both this worktree and the installed Git blobs; file SHA256 values are
recorded separately from Git's line-ending-normalized blob identities.
[Task readback](live-consumer-task.json) still names `pythonw.exe -B
scripts\plan_status_posts.py --publish` in `A:\Capital Chronicle\ContentOps`.
The task's Running state is not a terminal run result.

[A fresh installed import](installed-export-read.json) reads Main's public
export through the existing strict reader: 89 plans, 75 public instruments,
51 entry lists, and zero two-entry plans. Its export clock is
**22:18:34 GMT+7, 15 November**. All 129 retained plan-post rows were also
searched: 72 contain one entry and 57 contain none; none contains two.
Thus no real dual-entry publication is claimed. The original item tests cover
that producer shape without manufacturing a public post.

The later CC-549 contract deliberately names the underlying market when
instrument prices are incomplete, rather than displaying plan prices beside a
futures name. Its accepted correction remains installed; see
[CC-549's field mapping](../../CC-549/README.md). Earlier issued objects retain
their original bytes. This resume does not undo that newer correction.

## Exact post evidence

The earliest retained first post carrying CC-383's instrument is
`plan-status-post-9d265480c8c1ab40d56cdd7e692f486b`, created at
**08:37:30 GMT+7, 10 November 2026**. It names
**Micro E-mini S&P 500 (MES futures, Dec 2026)**. Main supplied one LIMIT entry,
7,520–7,530, and invalidation below 7,480; the instrument mapping was incomplete,
so that historical post explicitly labelled its plan-price basis.

| Destination | Exact object | Retained coordinator readback, GMT+7 | Fresh result, 15 November |
|---|---|---|---|
| Telegram | [114](https://t.me/CapitalChronicle/114) | 10 Nov 08:38:45; verified identity/media | Not obtained: Neo connection error |
| Discord | [1569526675622985822](https://discord.com/channels/1519310996030750782/1519311669216673802/1569526675622985822) | 10 Nov 08:38:41; verified identity/media | Official API SUCCESS; exact text and identity matched |
| Threads | [DfivsEtozIr](https://www.threads.com/@official.capitalchronicle/post/DfivsEtozIr) | 10 Nov 08:39:02; text/account/object/media matched | Official API SUCCESS; text/account/object matched |

[Readback evidence](readbacks.json) binds the original outbox and dispatch IDs,
expected copy/hashes, original observations, current official-adapter results,
and the fresh export's public fields. Fresh API checks covered text and object
identity; they did not repeat binary chart comparison. Telegram's retained
normalized receipt does not contain an explicit text-match check, so it is not
presented as a fresh inspection of visible text. There were zero public writes.

## Validation and choice

[Targeted tests](targeted-tests.xml): **20 passed in 8.35 seconds**, one pytest
process, only `tests/test_plan_status_instruments_cc384.py`. They cover dual
mapped/null entries, single-entry compatibility, destination limits, source
immutability, the queue/coordinator, and duplicate suppression in isolated stores.
The tested files match the installed files. No full suite was run.

[Launch arguments](launch-config.json) show configured `gpt-6.1-sol/high`,
**CONFIGURED_NOT_OBSERVED**; actual runtime model/effort telemetry is unavailable.
No editorial model was called. The chosen action was to reuse the existing
live implementation and read exact objects, because neither a new formatter nor
a historical repost would supply the missing public Telegram observation.
The two inherited builder ledgers and all six operating-root work files remain
outside this delivery; their preserved hashes are checked during integration.
