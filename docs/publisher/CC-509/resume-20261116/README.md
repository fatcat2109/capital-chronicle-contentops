# CC-509 — both live consumers verified

The remaining acceptance passes. The first natural private delivery after the
12 November installation used the on-demand Brent quote and arrived within
15 minutes. The next published plan chart was compared against a timely CNBC
gold quote. This continuation reads the original records; it creates no new
draft, source fetch, editorial call or public post.

| Private message | Confirmed delivery, GMT+7 | Bound fact | Post to delivery | Fetch time |
| --- | --- | --- | ---: | ---: |
| 4 | 12 Nov 2026 20:43:03 | Brent futures, Yahoo Finance | 8.5797 min | 0.2561 s |
| 5 | 13 Nov 2026 20:43:38 | Dollar index, CNBC, explicitly linked to gold | 8.3204 min | 0.8289 s |
| 6 | 13 Nov 2026 20:53:12 | WTI futures, Yahoo Finance | 5.5920 min | 0.1549 s |

Each immutable observation retains its exact source symbol, source and receipt
clocks, price, prior close, daily change, units and fetch seconds. The original
outbox receipt and pack still agree. Production fact and send checks pass at
their original saved check clocks. The formatter reproduces these age labels:
11, 3 and 12 minutes old. This is Bot API-confirmed delivery, not evidence of
Jim opening a phone message or sending a public X reply. CC-509 requires
15 minutes; the separate five-minute target was not met by these three drafts.

The original minute-run records show the search order: Main's timed price,
native M1, then the public quote when the earlier sources were absent or stale.
They retain fetch seconds for every attempted symbol, including failures.
Brent and WTI remain futures, without a conversion to a CFD. The Yahoo/Data
symbol map and CNBC spot/yield source choice remain as documented in the
[original implementation](../README.md).

The first published plan chart was gold, captured on **12 Nov 2026 at
23:28:30 GMT+7**. Its CNBC `XAU=` observation was **47.40083 seconds** old and
was received before capture. The displayed price differed by **0.0490547%**,
within the existing **0.15%** limit. Replaying the production comparison on
the retained image metadata gives the exact original `AT_CAPTURE` result.
The original PNG and quote hashes match their retained bytes.

The canonical [gold plan page](https://capitalchronicle.substack.com/p/gold-our-bearish-plan-39543964-entry)
has an observed publication clock of **12 Nov 2026 23:46:41 GMT+7**, and its
saved readback is **13 Nov 2026 00:02:54 GMT+7**. The same capture is bound in
the published image register and confirmed Telegram, Discord and Threads
dispatches. Telegram's retained object is [post 181](https://t.me/CapitalChronicle/181),
dispatched at **13 Nov 2026 00:58:56 GMT+7**. Dispatch, observed publication,
capture and readback clocks stay separate. Repeated records of that image
count as one capture. These are saved publication confirmations, not a new
public-page read or a newly posted chart.

[readback.json](readback.json) binds the original deliveries, source observations,
per-symbol fetch timings, chart comparison and confirmed dispatch/readback rows
by exact identity and hash. It reads SQLite with `mode=ro` and `query_only=ON`
in one read transaction. It exports no target text, private chat identity,
raw provider response or image bytes. Reproduce it once from the repository:

```powershell
python -B docs/publisher/CC-509/resume-20261116/readback.py
```

All **81 targeted tests passed in 16.63 seconds**, in one pytest process:
the public-quote, chart-reference and chart-audit files. They exercise failed,
stale and wrong-symbol answers, the cross-consumer one-minute limit, source
precedence, immutable fact delivery and the actual publication image register.
[targeted-tests.xml](targeted-tests.xml) retains the result. Eleven installed
source and entry files match this branch. Production code is unchanged.

The current source snapshot is recorded in [run-context.json](run-context.json).
The live launch command explicitly configures `gpt-6.1-sol/max`, recorded as
`CONFIGURED_NOT_OBSERVED`; it is not runtime model telemetry. The retained
editorial calls keep their own actual available identity and timing fields.
The six-market chart calibration belongs to CC-489; this item's live proof
does not establish a three-day sample or widen any limits. WTI's delayed free
quote can support an eligible reply while failing the chart's two-minute rule.

Publisher fast-forwarded proof commit
`57acca4cc01fee3804480e07325f269bb819c58f` into the operating root on
**16 Nov 2026 at 04:28 GMT+7**. The same **81 installed tests passed in
18.45 seconds**. The installed reader then ran from the operating root and
confirmed the original delivery, receipt, pack and chart bindings again.
[installed-readback.json](installed-readback.json),
[installed-tests.xml](installed-tests.xml) and
[integration.json](integration.json) retain these results.

The [existing scheduled consumer](scheduled-consumer.json) still runs
`pythonw.exe -B scripts\plan_status_posts.py --publish` in that root. Its
04:28 GMT+7 task result is 0. All eight original dirty-file hashes still match.
The delivery uses live tag `contentops-live-20261116-cc509-acceptance`; rollback
tag `contentops-rollback-20261116-cc509-acceptance` retains the original operating
HEAD `fa7533c6bacbc7c4816de8e9a0da9d8a1193857f`.
No integration, Ops review or person action remains for CC-509.
