# CC-453: main-account Substack delivery

Main-account delivery is restored. The publication stays at
`capitalchronicle.substack.com`; new Notes use `@capitalchronicle` (decision 119).
The existing minute consumer imports the installed Publisher code. The live
route control is empty and remains in `AUTONOMOUS_DEFAULT`.

The remaining outside cause is **SUBSTACK_ORIGINAL_PROFILE_NOT_FOUND**. The
secondary author's uncertain S&P Note remains `UNKNOWN_WRITE` with
`RECONCILIATION_PENDING`. Its profile says "Profile not found". This cannot prove
absence, so that Note was not retried. Jim's existing appeal must restore its
visibility before Publisher can finish that exact readback. Other restored
destinations continue. CC-453 remains BLOCKED on that specific reconciliation.

## Verified delivery

- The retained [EUR/USD plan page](https://capitalchronicle.substack.com/p/eurusd-before-cpi-the-dollar-thesis)
  has a fresh coordinator-confirmed readback. Full public text and the exact
  source image bytes match: [verification](plan-public-verification.json).
- The retained [CPI article](https://capitalchronicle.substack.com/p/if-october-core-cpi-is-03-or-higher)
  is readable on the same publication under the main signed-in account:
  [observation](article-public-observation.json).
- One [Bitcoin analysis Note](https://substack.com/@capitalchronicle/note/c-384157466)
  was published under the main account. Its complete copy and canonical link
  card are `RECONCILED_CONFIRMED`: [bound readback](main-note-confirmed.json).
  Its original source-bound copy was reused; no new editorial model was called.
- A repeat through the installed coordinator produced no new native write
  claim: [repeat](confirmed-repeat.json). The immediate publish return did not
  finish its binding. Its real claim and later public-object recovery remain
  separate; no successful publish return was backfilled.
- Five confirmed plan pages retain ten confirmed Telegram/Threads link
  bindings. Current public Telegram readback contains all five plan links and
  the CPI article link, on the unchanged host:
  [bindings](retained-link-bindings.json), [public readback](telegram-public-readback.json).
- `substack_notes` was removed from the runtime suspension file only after the
  exact main Note was confirmed, at 06:00 GMT+7 on 11 November:
  [route readback](routes-reopened.json).
- CC-404's existing event-pack owner returned `NO_EVENT_PACK_DUE`:
  [continuation](cc404-resume.json). No extra article was created to prove access.

## Repairs used by the live consumer

The registry, handoff and endpoint executor use one configured Notes identity.
The browser verifies the exact profile URL, handle and own-profile edit control.
Historical objects and issued request bytes keep their original author and links.
Uncertain recovery selects the author of an actually claimed request; an issued
but unattempted request is not evidence of a write.

The coordinator can resume a definite pre-send suspension refusal after its route
reopens, using the existing atomic dispatch claim. An ambiguous action remains
readback-only. Repaired transport code can supersede its proven pre-click refusal
once; an unchanged transport cannot repeat it. Long editor observations use Neo's
bounded output files while the complete approved copy is checked before Post.

Fresh exact readback is reusable across executor runs. Account, object, content,
media and age remain bound. Absence is checked against the latest actual action
claim, so a later attempt invalidates an earlier observation. Confirmed intents
do not spend minute-executor slots on old pending requests. Local pre-click
validation and an already resolved failure do not masquerade as a platform outage.

The final protocol checks, consumer regressions, operating source and preserved
work hashes are recorded in [FINAL.json](FINAL.json). Targeted tests use temporary
stores. Production expiry, duplicate, rights and public-copy checks stay enforced.

The branch starts at operating HEAD
`6df166df521a4c51f2b0414ccfdd1d7cbdaa97e5`. Fresh `origin/master` was its ancestor,
854 commits behind. Unrelated work was excluded and preserved. Both exec launches
specified `gpt-6.1-sol/max`; actual model telemetry is `CONFIGURED_NOT_OBSERVED`.
No schedule, application process, account setting or other chat was changed.
