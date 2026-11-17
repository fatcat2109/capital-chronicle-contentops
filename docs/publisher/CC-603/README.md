# CC-603 — Original call, outcome and pinned record

The implementation and reply recovery are live in `A:\Capital Chronicle\ContentOps`
at code commit `8dcae0ccb1bc542c9182efdd6a8570a054e477d0`. Both corrections
and the first Bitcoin follow-up are public. The existing minute consumer used
the one queued link reply at **17 November 2026, 12:00:37 GMT+7**.

**The Substack original-link requirement remains unmet.** Substack dropped that
URL from the reply as well as the root. This run reconciled the exact reply as
an existing, incomplete object and recorded the gap under Ops Product's
16 November 08:47 GMT+7 amendment: one missing-line reply or a gap in the Result,
with no further edits. The reply and root remain `SETTLED`, without claiming
strict content completion. No second reply, edit or deletion is queued.

This is the amendment's recorded-gap outcome. It does not claim that Substack's
original-link acceptance passed. This run made no public write or schedule change.

## 17 November continuation

- [Reply readback](resume-20261117-noon/reply-readback.json) identifies
  [c-389505878](https://substack.com/@capitalchronicle/note/c-389505878) under
  the original follow-up. `UNKNOWN_WRITE` is cleared;
  `RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE` and the missing-link check remain.
- [Current X thread](resume-20261117-noon/x-public-readback.json) retains its
  chart, original quote and time, outcome, original/record links and both notices.
- [Public scorecard readback](resume-20261117-noon/pinned-public-record.json)
  still shows **0 hits, 5 stopped, 37 expiries; 42 results, 6 scored**. It matches
  the follow-up's record line. Its entry never traded; no trading win is claimed.
- [Final consumer observation](resume-20261117-noon/final-state.json) confirms
  both corrections and no pending link reply. The minute consumer continues
  scanning the existing call sources; other retained candidates still need their
  own move charts, and the gold candidate reports conflicting held price bars.
- [Acceptance](resume-20261117-noon/acceptance.json) records the exact permitted
  outcome and the remaining strict Substack gap.

The changed reader recognizes only a unique reply under the bound original,
then verifies its author on its own public page. Missing URLs can establish that
the write occurred; they can never establish complete copy. The existing
coordinator persists that distinction and the minute consumer settles the gap.

**51 targeted checks and 10 installed checks pass**, including a stored hit and
expiry, exactly-once delivery, wrong-author/parent/object rejection, ambiguous
replies, preserved issued bytes, and no repeat send after an incomplete reply.
Evidence is in [integration.json](resume-20261117-noon/integration.json).
Live tag: `contentops-live-20261117-cc603-reply-readback`; rollback tag:
`contentops-rollback-20261117-cc603-reply-readback` at
`6df78cbbbebabc957000bda8f20a63ccb141fbdd`.

All unrelated dirty files retain their original hashes. The existing
`CapitalChronicle-PlanStatusPosts-V1` task and sole coordinator are unchanged.
[Launch evidence](resume-20261117-noon/launch.json) records both configured
`gpt-6.1-sol/max` launches as `CONFIGURED_NOT_OBSERVED`; no new editorial role
or Claude invocation was made.

## Verified public objects

Both owed corrections were published and read back before the first follow-up:

- The oil/euro correction reuses CC-359, including [Telegram 107](https://t.me/CapitalChronicle/107).
- The gold timing correction retains [Telegram 184](https://t.me/CapitalChronicle/184),
  Discord, Threads and [Substack Note c-388463042](https://substack.com/@capitalchronicle/note/c-388463042).

The Bitcoin follow-up retains its exact existing objects:

- [Substack Note c-388486151](https://substack.com/@capitalchronicle/note/c-388486151)
  displays the approved call, outcome, notices and TradingView chart. Its
  `Original:` and `Record:` lines have lost their URLs; the record link card
  remains. Current browser inspection and coordinator readback confirm this.
  The Note was not edited again.
- [X thread](https://x.com/Capitalnicle/status/2122123689437323291) has a fresh
  strict confirmed readback, including chart, original link, outcome, record
  link and both notices.
- Telegram 185, Facebook, Threads and Instagram retain their confirmed identities.

The text says the Bitcoin entry zone never traded. It reports a directional
view, without a trading win. The pinned record remains **0 hits, 5 stopped,
37 expiries; 42 results, 6 scored**, matching [Telegram 134](https://t.me/CapitalChronicle/134).
The original publication and current readback clocks remain separate.

## Earlier preparation of the one reply

Ops Product's 16 November amendment permits a missing line once as a reply in
the same thread, or a recorded gap. The new consumer path prepares only the
two exact original/record URLs and the existing notices. It binds to Note
`c-388486151`, requires its confirmed identity and matching chart evidence,
and refuses any missing analytical sentence or changed original.

The reply has one durable identity:
`cc603-followup-5da8be4c6a0f24959930f9bd8870753f-missing-links`.
At the earlier 17 November 07:37 GMT+7 observation it was `CC603_PREPARED`,
with **zero dispatches**. The coordinator returned `DESTINATION_FAILED_ET_DAY_SKIP`.
The later continuation above records the actual single attempt and readback.

The first failure is a different, existing Notes dispatch:
`dispatch_52b74856711d9922bcacceba907a1974`. It remains `UNKNOWN_WRITE` with
`NEO_EXACT_PUBLIC_OBJECT_NOT_FOUND`. One readback-only reconciliation in this
run remained pending. No retry or circuit override was performed. CC-401's
daily failure policy remains intact.

Strict reply readback would complete the parent thread. The actual reply lost
its URLs, so both exact objects retain incomplete-content observations instead.

## Earlier integration and checks

The existing `CapitalChronicle-PlanStatusPosts-V1` task runs
`pythonw.exe -B scripts\plan_status_posts.py --publish` from the operating root.
It consumes the prepared reply through the existing store, outbox and
`DurablePublicationCoordinator`. No additional publisher or schedule was added.

- [61 targeted acceptance checks](resume-20261117/acceptance-tests.xml) pass,
  including stored hit/expiry, exactly-once delivery, missing-link replies and
  the publication image contract.
- [Eight installed checks](resume-20261117/installed-tests.xml) pass.
- The earlier [48-check baseline](resume-20261117/baseline-tests.xml) also passes.
- [Integration evidence](resume-20261117/integration.json) verifies source
  hashes and preserved unrelated work. Live tag:
  `contentops-live-20261117-cc603-links`; rollback tag:
  `contentops-rollback-20261117-cc603-links` at `527f5ca55d9ac5b4ba1e7f3266f6d9e41a4b8b6d`.
- [Launch evidence](resume-20261117/launch.json) records
  `gpt-6.1-sol/max`, `CONFIGURED_NOT_OBSERVED`. No additional editorial model
  or Claude call was made; the reply contains retained URLs and notices only.

Current evidence: [fresh original readbacks](resume-20261117/before-reply-readback.json),
[reply refusal](resume-20261117/missing-links-live.json),
[prior-write readback](resume-20261117/destination-readback.json) and
[final state](resume-20261117/final-state.json).

The current continuation above supersedes this earlier pending-reply state.
The one permitted reply has been used; its remaining gap is recorded, and the
original issued objects and all prior observations remain intact.
