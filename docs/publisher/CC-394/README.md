# CC-394 — One public result scorecard

Live and pinned at [Telegram message 134](https://t.me/s/CapitalChronicle/134).
The existing minute consumer created it at 17:04 GMT+7 on 10 November 2026.
Bot API and public-page readbacks verified the exact five rows and totals at
17:07 GMT+7: two scored calls, one STOPPED and one EXPIRED, plus three explicit
unscored expiries. Six observed minute runs retained the same object, with one
bootstrap send and no later send or edit while Main's results were unchanged.

**Acceptance remains BLOCKED: FIRST_NEW_EXPORTED_MAIN_RESULT_PENDING.**
The fresh 17:10 GMT+7 plan-status export still has the same two scored
outcomes. The next new exported score must appear on this message within 60
minutes, read back through the Bot API and public channel page, without an
extra result feed post caused by the scorecard. This says nothing about
separate Main scorer runs; CC-391 and CC-398 keep their own integration and
export records. Publisher's next run performs that observation. There is no
new schedule or person-only step.

Operating code: `75394f93cf99e2cb08cf81981679e66f7145c4dd`;
live tag `contentops-live-20261110-cc394-r2`; rollback tag
`contentops-rollback-20261110-cc394`. [acceptance.json](acceptance.json),
[minute-consumer.json](minute-consumer.json),
[public-readback.json](public-readback.json) and
[next-result-check.json](next-result-check.json) retain the evidence.

The existing `scripts/plan_status_posts.py --publish` minute consumer now
updates one pinned Telegram message through `DurablePublicationCoordinator`.
It uses the official Bot API and the existing store, outbox and lease. No
schedule changes. Decision 106's selective feed posts remain unchanged.

The projection reads Main through its own export reader, then reuses
`result_rows_from_export`. HIT, STOPPED and EXPIRED share one dated ET form.
Main-supplied scored NOT_TRIGGERED results enter this record without adding
unfilled feed posts. Current untriggered expiries remain explicitly unscored.
Window-end direction appears only when Main supplies it; absent values stay
null in the retained rows. Public instruments and
mapped levels use the existing CC-384 projection; incomplete mappings keep
the original plan levels, identified in the line.

All held outcomes feed running totals. The message keeps the newest complete
lines within 4,096 UTF-16 units; it never selects by result. The existing
CC-379 weekly record now also keeps explicit unscored expiries and accepts
Main-scored NOT_TRIGGERED results. Removed export
rows cannot erase outcomes already held in this scorecard's outbox revisions.
Corrections replace their plan's current result without a second denominator;
the old immutable revision remains retained.

Only initial setup sends a scorecard message. Later results edit that same
public object. A store lease serializes updates. Lost writes require exact
Bot API readback and reconciliation before another write. Unknown creation
never sends a second message. Channel identity, current operating mode, Main
source bindings, private-data checks and the public notice remain enforced.

`--scorecard-only` updates just this record. Add `--dry-run` to render it
without any API or store writes. Normal `--dry-run --publish` also remains
read-only. No editorial model is called for this structured result record.

The combined targeted run passes 221 checks across the scorecard, CC-322
results, CC-400 export contracts, public output guard and CC-379 weekly
record. All 111 canonical coordinator checks also pass (`coordinator-tests.xml`).
The final weekly-source clock check is in `weekly-final-tests.xml` (27 pass).
The separate observation-clock correction passes all 30 scorecard checks
(`scorecard-final-tests.xml`). There are 333 distinct passing targeted checks.
Installed verification passed 56 scorecard/weekly checks, followed by all 30
scorecard checks after the clock correction; see `installed-tests.xml` and
`installed-scorecard-final-tests.xml`.
`targeted-tests.xml` is the combined evidence. The old CC-322 replay fixture
was corrected to put an aged outcome in a fresh export; advancing the whole
export four days tested the later freshness refusal instead of old results.
`live-preview.json` binds the actual five current results and their source
hashes. The source cutoff and actual API observation clocks stay separate;
recovery preserves the first retained observation. The next newly scored
result's 60-minute observation is not yet met.

Base: operating root `8e7b6f51e8ab8c4ce192a5fe054c203b047fbdcd`;
fresh `origin/master` is its ancestor. Branch:
`backlog/cc-394-pinned-results-scorecard`. Existing unrelated work is excluded.
The launch arguments configure `gpt-6.1-sol` / `max`, recorded as
`CONFIGURED_NOT_OBSERVED`.

Official transport references: [Telegram editMessageText](https://core.telegram.org/bots/api#editmessagetext),
[pinChatMessage](https://core.telegram.org/bots/api#pinchatmessage) and
[ChatFullInfo](https://core.telegram.org/bots/api#chatfullinfo).
