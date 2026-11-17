# CC-639: evening public-output readback

The command writes `day_readback.json` and `day_readback.md` beside the existing
19:15 digest run's `result.json`. It projects sealed publications, platform
dispatches, outbox messages, stored readbacks, digest delivery evidence and
reply-bot results. Its stdout includes the exceptions for the task's completion
notice.

Source delivery is on `backlog/cc-639-day-readback-v1`, from ContentOps operating
HEAD `ddd333fa7032aa26ecabb367eecc517c9d8207c5`. Remote `master`
`5be8fc63317be06d8319f3dd51ac4137a107cbb5` predates the digest and publication-feed
modules this item consumes. The delivery changes only its implementation,
command, tests, fixture and evidence files. It is not installed or run against
the live inputs by Publisher-B.

## Command and consumer

After integration, the first Publisher stream runs this once from
`A:\Capital Chronicle\ContentOps` against the retained 16 November run:

```powershell
python -B scripts/run_day_readback.py --run-dir "A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\route-1900\20261116T121550Z"
```

Ops Product adds that same command, with the current run folder, as the last
step of the existing `cc-contentops-digest-1900-bp` task after `result.json` is
saved. Its completion notice quotes stdout's `exceptions`. This delivery changes
no task, schedule or live installation. The first stream performs the item's
merge, focused tests and live/rollback tags through its existing route.

`--store` and `--feed` default to the exact runtime inputs in the backlog.
`--since` and `--until` permit an explicit UTC interval for bounded replay.
Otherwise selection starts strictly after the preceding run folder's timestamp
and ends at this run result's `recorded_at_utc`. A run without a result uses the
current clock. With no earlier retained run, the explicitly labelled fallback
starts at the previous day's scheduled 19:15 GMT+7 boundary.

Store states are observed when the command runs; this is not a reconstruction
of historical store states. Public HTTP checks carry their own actual check
clocks. A replay on an old folder selects its original interval and checks the
pages as they are now. JSON records use UTC; the short Markdown report uses
GMT+7.

## What reaches the reader

Each piece carries its platform statuses, first recorded causes, public URLs and
stored readback observations. Required destinations come from the held intent
and sealed outlets. A missing expected row is an exception. Current uncertain,
definitely refused and reconciled-absent rows are named, along with retained
failure observations in the interval. An unrecorded cause stays
`FIRST_CAUSE_NOT_RECORDED`. Native request/return diagnostics supplement missing
dispatch readbacks without changing the store.

Unauthenticated HTTP GET checks cover Capital Chronicle's Substack posts and
Notes and `t.me/CapitalChronicle/<number>?embed=1`. All other destinations,
including X, use stored readbacks. Sign-in redirects, Telegram Web, private
Telegram routes and cross-platform redirects are refused before following them.
Each public URL is fetched once, with a timeout and response-size bound.

The comparison checks the title or first line, ordered stored text and link
targets within the post body. Missing text or links is an exception. Unreadable
HTTP pages remain named HTTP failures; they do not assert that a post is absent.
The SQLite connection uses `mode=ro` and `query_only=ON` and closes before HTTP.
A damaged sealed feed is named while the held store publications remain usable.

The digest section identifies its exact packet and page and reports recipients,
opens and open rate from that run's retained dashboard observation. Missing
metrics remain null. Reply-bot output contains counts by status and first cause
and public post IDs and recorded delivery clocks for delivered drafts.
Private identifiers and draft copy are never projected. No report key contains
`chat`, `token`, `secret`, `webhook`, `phone`, `user_id` or `binding`.

## Verification and remaining acceptance

[Final targeted results](final-tests.xml): **28 passed**. One pytest process,
one explicit test file, no workers or shards. The command test invokes the real
CLI entry function with isolated SQLite/feed/run inputs and a supplied HTTP
fixture, then reads both generated files. The database bytes remain unchanged.

[The projected stored-row fixture](../../../tests/fixtures/cc639_day_readback_20261116.json)
preserves CC-536 piece 2's eight confirmations, Telegram 186, personal LinkedIn's
`RECONCILED_ABSENT_SAFE_TO_RETRY` and YouTube's
`YOUTUBE_EXTERNAL_LINK_VERIFICATION_REQUIRED`. The retained 16 November digest
observation supplies **5 recipients, 1 open and 20% open rate**. Tests also cover
missing expected destinations, uncertain outbox rows, old dispatch clocks with
new readbacks, private-field exclusion, HTTP failures, hidden text and exact
link targets.

HTTP test pages are constructed from held public intents, not retained live HTTP
responses. The Telegram 187 regression cuts its held text and removes its link,
then verifies both exceptions. It makes no new claim about Telegram 187's current
page or historical HTTP bytes. No live report or publication was performed in
this build. The first integrated 19:15 run and Ops Product's store/page spot-check
remain the item's live acceptance.

The launch arguments were read from the running Codex process: `--model
gpt-6.1-sol` and `model_reasoning_effort="max"`. Actual model/effort telemetry:
`CONFIGURED_NOT_OBSERVED`. The implementation invokes no editorial model.
