# CC-394 resumed acceptance

The pinned scorecard remains live on [Telegram message 134](https://t.me/CapitalChronicle/134).
Its latest Main result and totals matched an official Bot API `getChat` read at
**22:27 GMT+7, 15 November 2026**. Completion is **BLOCKED:
NEO_ENDPOINT_CONNECTIONERROR**. Initializing the existing Neo MCP endpoint
`http://127.0.0.1:9010/mcp` failed before a public tab could be opened.

Next action: Ops Product restores that existing Neo connection, then Publisher
reads the exact message at `https://t.me/s/CapitalChronicle/134`. No browser
restart, alternate browser, signed-in Telegram read, public write or schedule
change was performed. No source fix was necessary for this observation.

[Bot readback](bot-readback.json) binds the channel identity, message ID,
exact public text, SHA256 and observation clock. It matched the
[installed projection](installed-projection.json): **42 results, six scored,
23 complete visible lines, 3,947 UTF-16 units** within the 4,096-unit limit.
The results are five STOPPED and 37 EXPIRED; 36 expiries are explicitly
unscored. No live HIT or Main-scored NOT TRIGGERED result is claimed.

The old `FIRST_NEW_EXPORTED_MAIN_RESULT_PENDING` cause is resolved. The first
new score after the original acceptance checkpoint was Main's gold STOPPED
result, scored **17:51:08 GMT+7 on 10 November**, observed on message 134 at
**17:51:32**, a **24.17-second** interval. Subsequent EURUSD and oil scores
arrived in 24.61 and 83.00 seconds. Their first exact Bot observations are
retained in [score-timing.json](score-timing.json).

The newest scored result, oil STOPPED on **12 November**, missed the
score-to-publication deadline: scored **15:30:12 GMT+7**, first Bot readback
**18:13:37**, or **2 hours 43 minutes 25 seconds**. The retained minute records
name `PLAN_EXPORT_STALE`: Main's export remained dated **12:12:12** through
the **18:12:35** run. The first fresh export was dated **18:13:13**, followed
by the exact Bot observation **24.07 seconds** later. This is an observed
deadline miss, not a successful 60-minute result. The Main export owner must
keep scored outcomes reaching its export promptly; Publisher does not infer
an unexported score from prices.

[Live-consumer evidence](live-consumer.json) covers **3,378 scorecard run
records** from 10–15 November: one bootstrap message, only object 134, and
zero records of an extra result feed post. The scorecard work item has no
feed outbox row or platform dispatch. The existing direct scorecard Bot path
is owned by `DurablePublicationCoordinator`. Decision 106's feed selection
was not changed or retriggered.

[Task readback](live-consumer-task.json) still names `pythonw.exe -B
scripts\plan_status_posts.py --publish` in `A:\Capital Chronicle\ContentOps`.
Its Running state is not completion evidence. The actual completed minute
records above prove its scorecard use. The installed source and focused test
file match this worktree byte for byte; see [installed-source.json](installed-source.json).

[Targeted validation](targeted-tests.xml): **5 passed, 25 deselected in
17.75 seconds**, one pytest process and one test file. The selected checks
prove identical win/loss form, message-limit handling, update of one public
object without feed posts, explicit unscored expiry handling, and distinct
source/observation clocks. A preceding full-file attempt was interrupted
with the turn and produced no terminal result; it is not counted as a pass.
No production code changed, so no broader test run was needed.

[Launch readback](launch-config.json) records configured `gpt-6.1-sol/max`,
`CONFIGURED_NOT_OBSERVED`, for the original and resumed exec processes.
No editorial model was called. The chosen action was to reuse the installed
scorecard and exact object because a new formatter or repost would not
supply the missing public-page observation. Existing work in both checkouts
remains outside this delivery.
