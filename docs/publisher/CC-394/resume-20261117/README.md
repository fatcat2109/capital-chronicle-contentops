# CC-394 completed public scorecard readback

The existing [pinned scorecard, message 134](https://t.me/s/CapitalChronicle/134),
matches Main's projected outcomes through both the official Bot API and the
public channel page. BrowserOS Neo observed its exact text and pin notice at
**09:40 GMT+7 on 17 November 2026**. The [public readback](public-readback.json)
and [Bot readback](bot-readback.json) have the same SHA256.

The message counts **42 results: five STOPPED and 37 EXPIRED**. Six are scored;
36 expiries remain explicitly unscored until Main supplies their scores. The
message shows 23 complete newest lines and uses **3,947 of 4,096 UTF-16 units**.
The [installed projection](installed-projection.json) comes from the existing
export reader and retained source-bound outcomes, without price-based scoring.

The [score timing](score-timing.json) confirms the first new Main score after
the original acceptance checkpoint reached this pinned object in **24.17 seconds**.
Later EURUSD and oil scores took 24.61 and 83.00 seconds. This satisfies the
item's next-result check. The latest scored oil result, from 12 November, took
**2 hours 43 minutes 25 seconds** and missed the 60-minute deadline. The prior
[delay evidence](../resume-20261115/live-consumer.json) retains `PLAN_EXPORT_STALE`:
the score preceded Main's fresh export; Publisher read it back 24.07 seconds
after that fresh export. This historical miss remains an operational limit;
the new public-page observation does not erase it.

[Live-consumer evidence](live-consumer.json) covers the existing minute entry:
one bootstrap message, only object 134, no extra scorecard feed posts, and no
scorecard feed outbox or platform dispatch rows. Its latest completed runs
confirm the pinned text. [Task readback](live-consumer-task.json) and
[installed-source hashes](installed-source.json) identify the operating root
and its actual consumers. No publishing command, schedule change, application
restart or signed-in Telegram access was needed.

[Targeted checks](targeted-tests.xml): **5 passed, 25 deselected**, in one
pytest process. They cover identical win/loss form, the limit and totals,
one-object updates, the existing minute consumer's use of Main rows through
the coordinator, and separate observation clocks.

The first test attempt was stopped without a terminal test result after its
minute-consumer test reached later editorial services and spawned an unintended
Codex CLI child. Both owned processes exited. The test now stubs those companion
services, uses fake Main rows, and fails if a subprocess is attempted; the
successful rerun took 3.10 seconds. Production publishing code is unchanged.
[Launch evidence](launch-config.json) records configured `gpt-6.1-sol/max` as
`CONFIGURED_NOT_OBSERVED`, plus the interrupted child's unobserved model and effort.

The delivery reuses the installed scorecard because a replacement message or
formatter would not supply the missing public observation. Existing modified
files remain outside the commits. [Integration evidence](integration.json)
records the operating-root merge and live/rollback tags.
