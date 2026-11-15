# CC-436 continuation, 16 November 2026

Live acceptance is blocked by `NEO_ENDPOINT_CONNECTIONERROR`. The automatic
executor is already in the operating root and its copied-store path passes.
No new runtime implementation was needed for this continuation.

The real MCP `initialize` failed at **03:28:05 GMT+7 on 16 November**.
A separate host observation at **03:29:31 GMT+7** found no listener on local
port 9010. The unchanged scheduled minute worker also records
`NEO_ENDPOINT_UNAVAILABLE` for its exact pending request. The current suspension
control contains only YouTube's verification restriction; X and Notes are not
suspended by that control.

## Verification change

CC-543 added immediate API alerts before the later automatic browser phase.
CC-436's CLI test still assumed its first publication call selected Neo. The
test now verifies the immediate-alert phase and the subsequent automatic Neo
phase against the same isolated store. Its unrelated call-followup consumer is
stubbed, like the other unrelated consumers. Runtime behavior is unchanged.

The focused run passed **6 tests in 17.39 seconds**. It covers copied-store X
and Notes posting/reconciliation, a plain Python child with no Codex dispatch,
lost-return recovery without another publish, executor selection by the real
minute consumer, and CLI wiring. The first run exposed the outdated CLI
expectation; the passing JUnit file records the corrected run.

Verification commit `8cc55413a5d3a28f2e8bc1e41bcfc93719715b38` was pushed
and fast-forwarded into the operating root. Both installed consumer/CLI checks
then passed there in **7.02 seconds**; see
[installed-consumer-tests.xml](installed-consumer-tests.xml). SHA256 comparisons
of the minute entry, endpoint executor and native executor bind this checkout
to the operating consumer in `runtime-observation.json`.

Command:

```powershell
python -m pytest tests/test_neo_endpoint_executor_cc436.py -q -k 'copied_store or status_minute_consumer_selects_automatic_executor or cli_publish_passes_automatic_transport_to_the_real_consumer or lost_publish_return_recovers_by_readback_without_reposting' --disable-warnings --tb=short --junitxml=docs/publisher/CC-436/resume-20261116/endpoint-acceptance-tests.xml
```

## Actual timing

[live-timing.json](live-timing.json) was collected with SQLite `mode=ro` from
the existing production store. It binds source-event, registration, initial
verified readback and dispatch clocks separately. A dispatch-attempt clock is
never substituted for publication or confirmation.

Eight status operations since 11 November have a Telegram dispatch and at least
one browser-destination dispatch. None has an X confirmation within 120 seconds
of its Telegram confirmation. One Notes confirmation meets that interval:

| Operation suffix | Original source event (GMT+7) | Telegram confirmed (GMT+7) | Notes minus Telegram | X minus Telegram |
| --- | --- | --- | --- | --- |
| `cccd9a56d9a298bb95988ecec40ca9f2` | 11 Nov 10:19:22 | 11 Nov 10:25:54 | -5.1276 seconds | +7,551.088593 seconds |
| `6abb3bc55001d7b9ea3861ede3a19ae3` | 11 Nov 23:20:07 | 11 Nov 23:26:00 | +45,490.780593 seconds | +45,851.584617 seconds |

The second pair is later retained evidence, but both browser confirmations are
over twelve hours late. It does not close the live timing test. Native returns
bind `NEO_ENDPOINT_EXECUTOR` and `browseros-neo/run`; the report retains a small
sample and references the existing complete outbox history.

At collection there were **zero natural source events from the preceding
60 minutes**. The latest natural event remains dated 12 November. The prepared
CC-603 correction is recorded separately and is not a fresh Main status event.
Old objects are not reposted to create a passing timing sample. The existing
`UNKNOWN_WRITE` operation remains under readback/reconciliation.

## Installed consumer and remaining action

[runtime-observation.json](runtime-observation.json) records the active task
and process identity: `CapitalChronicle-PlanStatusPosts-V1`,
`pythonw.exe -B scripts\plan_status_posts.py --publish`, operating directory
`A:\Capital Chronicle\ContentOps`, `IgnoreNew`. No schedule was changed.

The branch starts at operating HEAD
`60d803e657cd1dc4148674cb496afe2bd3075e76`. Fresh `origin/master` was an ancestor,
1,195 commits behind that operating root; using the operating HEAD preserves
the installed Publisher changes. The two pre-existing telemetry edits and
unrelated files remain outside this delivery.

The observed top-level launch is `gpt-6.1-sol`, effort `max`, labelled
`CONFIGURED_NOT_OBSERVED`; actual model/effort telemetry was unavailable.
This verification authored no public copy and invoked no editorial model.

**Next action: Ops Product restores BrowserOS Neo's local MCP endpoint.** The
existing minute task then consumes the exact pending requests through their
coordinator, with readback first for uncertainty. On the next genuinely new
source-bound operation, measure X and Notes confirmations against their own
Telegram twin and original source clock. Only that live result can finish
CC-436's remaining acceptance condition.
