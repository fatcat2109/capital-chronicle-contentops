# CC-603 — Original call, outcome and pinned record

The implementation is live at `c5ee1ef32f32fc9c35e83fc4ff2205d2cb53be33` in
`A:\Capital Chronicle\ContentOps`. **Live acceptance remains incomplete:** the
Substack Note lost its original-link text. One link reply is prepared, but
Substack Notes' existing daily failure circuit refused it before any write.

The earliest next ET day is **17 November 2026, 12:00 GMT+7**. The existing
minute consumer can resume that same reply after the circuit ends, or after
the prior uncertain write is reconciled. This run changed no schedule and
performed no public post, edit or deletion.

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

## One missing-link reply

Ops Product's 16 November amendment permits a missing line once as a reply in
the same thread, or a recorded gap. The new consumer path prepares only the
two exact original/record URLs and the existing notices. It binds to Note
`c-388486151`, requires its confirmed identity and matching chart evidence,
and refuses any missing analytical sentence or changed original.

The reply has one durable identity:
`cc603-followup-5da8be4c6a0f24959930f9bd8870753f-missing-links`.
It remains `CC603_PREPARED`, with **zero dispatches** at the final observation.
The existing coordinator returned `DESTINATION_FAILED_ET_DAY_SKIP`.

The first failure is a different, existing Notes dispatch:
`dispatch_52b74856711d9922bcacceba907a1974`. It remains `UNKNOWN_WRITE` with
`NEO_EXACT_PUBLIC_OBJECT_NOT_FOUND`. One readback-only reconciliation in this
run remained pending. No retry or circuit override was performed. CC-401's
daily failure policy remains intact.

After strict reply readback, the consumer can recognize the complete parent
thread. It preserves the root's `RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE`
record rather than claiming the root itself recovered its missing text.

## Integration and checks

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

Completion requires the existing reply's strict readback beside the original
Substack chart, with its original and pinned-record links. Resume that exact
identity; preserve all issued objects and uncertain-write recovery.
