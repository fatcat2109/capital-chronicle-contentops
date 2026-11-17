# CC-384 completed live readback

The installed consumer's first applicable post now has successful exact readbacks
on all three required destinations. Telegram's previously unavailable public
readback succeeded on **17 November 2026, 09:33 GMT+7**. No public object was
created or edited. The choice was to verify the existing issued objects because
the implementation was already integrated and reposting would duplicate a plan.

| Destination | Issued object | Verification |
|---|---|---|
| Telegram | [114](https://t.me/CapitalChronicle/114) | Neo public unsigned channel; exact retained text and object URL |
| Discord | [1569526675622985822](https://discord.com/channels/1519310996030750782/1519311669216673802/1569526675622985822) | Official adapter; exact identity and text |
| Threads | [DfivsEtozIr](https://www.threads.com/@official.capitalchronicle/post/DfivsEtozIr) | Official adapter; object, account and text bindings |

The issued post names **Micro E-mini S&P 500 (MES futures, Dec 2026)**. Its
single LIMIT entry is 7,520–7,530, invalidation below 7,480, with the plan-price
basis explicitly stated. The issued bytes predate CC-549's newer correction and
remain unchanged. See [bound readbacks](readbacks.json) and the
[public Telegram extraction](telegram-public-readback.json).

**20 targeted tests passed in 3.67 seconds**, using one pytest process and only
`tests/test_plan_status_instruments_cc384.py`; see [test results](targeted-tests.xml).
These cover two entries in one first post per API destination, destination
limits, single-entry compatibility, null mappings, fill naming, queue/coordinator
consumption and duplicate suppression. No production writes came from tests.

The [fresh installed reader](installed-export-read.json) consumed Main's real
export through the existing strict reader: **89 plans, 75 public instruments,
51 entry lists, zero dual-entry plans**. All 141 retained plan-status rows were
also searched; none contains two entries. Thus no live dual-entry example is
claimed; the acceptance's conditional dual-entry case is covered by tests.

[Installed source evidence](installed-consumer.json) confirms the earlier
delivery is an ancestor of the operating HEAD and the six relevant source/test
files match its committed blobs. Builder and installed text match; one file has
different line endings. The [existing minute task](live-consumer-task.json)
still consumes `scripts/plan_status_posts.py --publish` from the operating root.
Its Running state is not a completed run; the real issued objects and exact
readbacks above supply the live-consumer evidence.

The branch continues operating HEAD `944f53d36c1ccbdda1e34ffa1e15515cbdfb864b`,
which already contains the implementation and newer accepted consumers; remote
master predates them. Integration uses a fast-forward and live/rollback tags.
Inherited modified files remain outside this delivery and retain their hashes.
No schedule, application, Main file or other chat was changed.

[Selected live launch arguments](launch-config.json) record configured
`gpt-6.1-sol/high`, **CONFIGURED_NOT_OBSERVED**; actual runtime model telemetry
is unavailable. No editorial model was called. The bounded [verification script](verify.py)
uses read-only SQLite and existing official readback adapters.
