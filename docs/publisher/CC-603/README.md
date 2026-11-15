# CC-603 — Corrections first, then the original call and its outcome

**BLOCKED: `NEO_ENDPOINT_CONNECTIONERROR`.** The implementation is integrated in
`A:\Capital Chronicle\ContentOps` at `98eea144c7e99b3031bc92ce17b89f8fd3cd9a09`.
The required first follow-up has not been published. Its Substack and X
acceptance remains incomplete.

## What is live

The existing `CapitalChronicle-PlanStatusPosts-V1` task still runs
`pythonw.exe -B scripts\plan_status_posts.py --publish` from the operating root.
Its existing store, outbox, dispatch claims, recovery and
`DurablePublicationCoordinator` own this feature. No schedule was changed.
The new progress field uses its existing minute result file; it contains
identities and states, without article copy or image bytes.

The live tag is `contentops-live-20261116-cc603`; rollback is
`contentops-rollback-20261116-cc603` at
`ea9cd48e2b61592882fa1b99976e6c381ec98893`. Both tags and the delivery branch
are pushed. [Integration evidence](integration.json) records source hashes,
installed tests and the unrelated changes preserved in both worktrees.
Two newly added files differ between checkouts only in CRLF/LF endings;
all four installed paths match after line ending normalization.

## Corrections and exact public objects

The oil/euro correction already existed as CC-359. Its confirmed objects on
Telegram, Discord, Threads, X and Substack Notes are retained; this item
does not repost it. Its [Telegram correction is message 107](https://t.me/CapitalChronicle/107).

The new gold correction says the 12 November analysis and status post were
late and cannot be cited as foresight. It links the original analysis and
changes or deletes no original object. Confirmed copies are:

- [Telegram 184](https://t.me/CapitalChronicle/184).
- [Discord](https://discord.com/channels/1519310996030750782/1519311669216673802/1571605061375623189).
- [Threads first part](https://www.threads.com/@official.capitalchronicle/post/Dfxg403AWfN)
  and [its complete continuation](https://www.threads.com/@official.capitalchronicle/post/DfxiUuLgfWN).

The Threads continuation initially received a definite no-write because it
had no image. The repaired dispatch carries the same unannotated TradingView
image. Its new dispatch identity preserves the old refusal and the issued
first part. The continuation read back at **02:30:36 GMT+7, 16 November**.
[Recovery evidence](live-correction-recovery.json) retains the separate states.

The gold Substack Notes copy remains `NATIVE_NEO_TOOL_PENDING`:

- Work item: `cc603-gold-timing-correction-20261112`.
- Dispatch: `dispatch_796db3424675b9656112164e7a908724`.
- Request: `fef361bb49568b7ccc77e9b4b48554d6394861e62901b6b5c2e3b7f2e2967be7`.
- Retained outbox row: `native-neo-51d69d03d8578fda175d598dba490f23fc465ae0d56120b9660fb0cdcd4fb151`.

The existing Neo MCP endpoint `http://127.0.0.1:9010/mcp` failed initialization
again at **02:29:07 GMT+7, 16 November**. No browser action ran in that check.
[Endpoint evidence](resumed-neo-connection.json) records the exact error.
No native desktop control, browser restart or alternate browser was used.

## Follow-up behavior and prepared first candidate

The consumer joins Main's explicit as-written HITs to their original public
terms. It also reads published article tests and exact public-span annotations.
The older CPI article's empty call array is recovered from its published
conditional title, the retained official BLS core CPI response and held prices.
Its 0.3% condition occurred, but its complete price-and-time test failed;
it produces no follow-up. An intrahour move alone cannot satisfy an endpoint
claim. [Article evidence](article-price-checks.json) retains that check.

The eleven specifically approved CR views enter a separate dated view report.
An untraded entry never becomes an as-written hit or a trading win. Exact
original quote, ET time, condition, direction, horizon, invalidation and link
stay bound. The public time uses the confirmed dispatch minute, identified
as such in private metadata; no platform publication clock is invented.
New ordinary resolutions keep the one-hour window. The expressly named
historical CR set uses Ops Product's 14 November backfill instruction.

Only one durable follow-up exists per call. The two corrections must read
back first. The first follow-up includes the original destinations plus the
explicitly required Substack Notes and X acceptance destinations. A short
follow-up is not counted as a full article.

Bitcoin `d7eddc84` is prepared first because its held price path is complete.
It was published before the move, but its 76,000–76,700 entry zone never traded.
Gold `a0380280` has an uncovered interval in this held-price check, so no hit
is inferred through that interval. [All source checks](final-source-checks.json)
and the [first-candidate preparation](first-followup-preparation.json) retain
the source hashes, original terms and checks.

The pinned record was read through its official Bot API, matched to its
confirmed exact text and message 134. The observed line is **0 hits, 5 stopped,
37 expiries; 42 results, 6 scored**. This is the named pinned record, not the
different 88-call CR population. Every new write checks that its counts still
match. The old record is not changed by reporting an untraded CR view.

The original gold TradingView download was inspected with its full attribution.
The old overlaid picture, which contains a target, is not used. No held Bitcoin
chart captured after its resolution was found in the existing plan media.
The next chart must show the original and resolution, preserve attribution,
and bind its visible window in the existing media package before publication.

## Verification and remaining action

There are **23 distinct passing targeted checks**: 22 in
[final-tests.xml](final-tests.xml), plus the existing minute result projection
in [minute-record-tests.xml](minute-record-tests.xml). They cover stored HIT
versus expiry, exactly-once delivery through the real coordinator seam,
unmet conditions, partial matches, same-bar ambiguity, source gaps, correction
ordering, original preservation, pinned counts and continuation recovery.
Installed consumer/recovery checks also pass:
[three checks](installed-final-recovery-tests.xml) and the
[installed minute result check](installed-minute-record-tests.xml).

Both exec launches configured `gpt-6.1-sol/max`, recorded as
`CONFIGURED_NOT_OBSERVED` in [launch.json](launch.json) and
[resume-launch.json](resume-launch.json). No separate paid model call or
Claude session was started. Existing ledger and other unrelated work remains
uncommitted and outside the delivery.

**Next action:** Ops Product restores the existing Neo connection. Publisher
then resumes the exact pending gold Substack request, reads both corrections
back completely, acquires the bound Bitcoin move chart through that connection,
and publishes one follow-up. Read Substack and X back with the original link,
chart and scorecard counts observed in the same minute. Do not recreate the
operation or retry any uncertain public write.
