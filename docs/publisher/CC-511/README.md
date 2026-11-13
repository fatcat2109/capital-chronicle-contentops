# CC-511 — live reply topics and the complete US-session funnel

The named-driver map is integrated into the operating root at
`97d8d9aa928914d8a121297a7b251ced2fea2115`. The existing minute consumer used its market links:
two distinct Nvidia targets each carried 13 usable source facts into ranking.
That first observed call ended with `AGY_RANK_TIMEOUT_90S`; no send is inferred.
The later light-caller recovery is the separate CC-512 delivery.

The complete 12 November US-session readback is now in
[us-session-funnel.json](us-session-funnel.json). Its 156 completed natural runs
retain all 171 on-topic posts' first undrafted causes. The session produced no
returned drafts or confirmed private sends. The market-driver map and its
consumers remain installed; this readback completes the outstanding reporting
acceptance without treating zero output as delivery success.

The map ties index weights and sectors to their US indices; Middle East and
Russian supply risk to oil and gold; central-bank speakers and sovereign rates
to currencies and gold; OPEC and inventories to oil; and flows and regulation to
Bitcoin. The DAX link explains euro-area equities and cross-market risk appetite.
Links describe relevance. They never assert a measured market reaction.

The same link reaches topic selection, fact selection, on-demand quote selection,
ranking and writer instructions. A reply using a linked-market fact names the
original driver, the fact's market and their relationship in one sentence. It
need not repeat the event's wording. Explicit indices and oil instruments keep
their separate identities. A bank-sector post does not borrow a Nasdaq fact.
Actual source dates, rights, identity, numeric checks, uncertain-send deduplication
and the 15-minute send deadline continue to apply.

## Verification and integration

- `topic-cases.json`: three exact requested positives and five named negatives
  from the retained 12 November intake, with original IDs, line numbers and hashes.
  The negatives are the Meta fine, two South Korea/APEC diplomacy posts, voter-ID
  politics and the Russia/Ukraine prisoner exchange without an energy tie.
- `topic-consumer-tests.xml`: 86 passing targeted checks at the first checkpoint.
- `funnel-bot-tests.xml`: 74 passing topic, report and bot checks.
- `final-feature-tests.xml`: 47 passing final topic, report and minute-entry checks.
- `final-policy-tests.xml`: 76 passing final source/link/report checks.
- `installed-consumer-tests.xml`: 100 passing installed topic, fact and bot checks,
  53.54 seconds, one pytest process.
- `installed-final-policy-tests.xml`: 76 passing final installed checks,
  19.31 seconds reported by pytest, one process; JUnit records its suite clock
  separately. Tests read isolated fixtures, never the production store.
- [resume-20261114/acceptance-tests.xml](resume-20261114/acceptance-tests.xml):
  50 passing topic and session-report checks on the current operating base,
  including the three exact positives, five negatives and linked-fact consumers.

[integration.json](integration.json) records the operating HEAD, exact Git blobs,
normalized source hashes and preserved unrelated dirty-file hashes. Raw filesystem
hashes differ where Git converts LF to CRLF; the committed blobs and normalized
source agree. The initial live tag is `contentops-live-20261112-cc511`, the current
code tag is `contentops-live-20261112-cc511-driver-link`, and rollback is
`contentops-rollback-20261112-cc511`. All are pushed. Historical issued requests
and public objects keep their bytes.

[installed-consumer-readback.json](installed-consumer-readback.json) binds the
first natural live run to its exact requests and call record. It records the
ranker's configured model/effort and timeout duration; unavailable runtime model
telemetry stays `CONFIGURED_NOT_OBSERVED`. The top-level launch was
`gpt-6.1-sol / max`, also `CONFIGURED_NOT_OBSERVED` (`run-context.json`).
The resumed launch has the same configured values, read from its actual process
arguments in [resume-20261114/run-context.json](resume-20261114/run-context.json).
No manual production tick, application restart, schedule change or public reply
was made. Jim remains the sender of public replies.

## Observed premarket funnel

The bounded premarket observation covers 12 November 12:00 GMT+7 to
12 Nov 2026 20:29:50 GMT+7. It contains 311 completed natural runs;
the last ended at 12 Nov 2026 20:27:42 GMT+7.
This is a partial premarket observation, not the full US-session acceptance.
Counts are distinct post IDs, never a sum of repeated feed appearances.

| Stage | Distinct posts |
|---|---:|
| Posts seen, including stale rows | 1136 |
| Fresh targets | 316 |
| On topic | 91 |
| With a usable fact | 58 |
| Sent to ranking | 37 |
| Ranked above the floor | 4 |
| Writer returned a draft | 3 |
| Draft passed pack checks | 0 |
| Confirmed private sends | 0 |

All 91 on-topic posts without a validated draft have their first retained
cause and artifact in [premarket-funnel.json](premarket-funnel.json). A writer
return is counted before the pack checks; three returns produced zero validated
drafts. Later causes remain alongside the first one, including the later explicit
link failure after a writer timeout.

| First cause before a validated draft | Posts |
|---|---:|
| `NO_ADDED_FACT_ABOVE_QUALITY_FLOOR` | 46 |
| `NO_USABLE_FACT` | 33 |
| `AGY_RANK_TIMEOUT_90S` | 8 |
| `CODEX_DRAFT_TIMEOUT_90S` | 1 |
| `REPLY_UNBOUND_OR_CHANGED_NUMBER` | 1 |
| `FACT_DRIVER_LINK_NOT_STATED` | 1 |
| Writer: no held fact for the Bitcoin annual-return or STRC payout claim | 1 |

The recorded durations below are minutes of work in each stage, with the median
restricted to runs that did work in that stage. They are not invented per-post
waiting times. The JSON preserves each confirmed send's post-to-draft,
post-to-send-attempt and post-to-delivery clocks when a send exists.

| Stage | Runs with work | Median minutes | Maximum minutes |
|---|---:|---:|---:|
| Filter | 311 | 0.026 | 0.970 |
| Ranking | 44 | 0.562 | 2.234 |
| Drafting | 6 | 1.272 | 1.505 |
| Checks | 38 | 0.001 | 0.025 |
| Whole tick | 311 | 0.065 | 2.525 |

There were no confirmed sends in this observation. Post-to-send latency and
Telegram-send duration are therefore unavailable. The largest gap between
completed runs was 5.88 minutes. Saved historical
scores and omissions are read from their original call artifacts; the new map
is never applied retrospectively to inflate the original on-topic count.

## Full-session readback

The report window is 09:30–16:00 ET on 12 November: 21:30 GMT+7 on 12 November
through 04:00 GMT+7 on 13 November. Records retain 14:30–21:00 UTC.
[us-session-funnel.json](us-session-funnel.json) records the completed window
from the saved results, requests and editorial returns. The first natural run
started at 21:30:27 GMT+7 on 12 November; the last completed at 03:59:56 GMT+7
on 13 November. There are 156 completed runs, 540 hashed source artifacts and
no missing results among the 156 retained session-run folders. The largest gap between completed runs is
5.820 minutes. Counts are distinct post IDs across the session.

[resume-20261114/session-readback.json](resume-20261114/session-readback.json)
verifies every artifact hash and the retained run folders. The live requests
carried 132 distinct candidates with explicit market links and usable facts
into recorded ranking input, proving that the consumers used the widened map.

| Stage | Distinct posts |
|---|---:|
| Posts seen, including stale rows | 1239 |
| Fresh targets | 356 |
| On topic | 171 |
| With a usable fact | 163 |
| Sent to ranking | 163 |
| Ranked above the floor | 1 |
| Writer returned a draft | 0 |
| Draft passed pack checks | 0 |
| Confirmed private sends | 0 |

All 171 on-topic posts lacked an authored draft. The report preserves each
post's first cause, its original artifact and clock, and any later causes.
There are no unknown first causes. The original runs' topic decisions and
ranking scores are retained without applying today's code retrospectively.

| First cause before an authored draft | Posts |
|---|---:|
| `NO_ADDED_FACT_ABOVE_QUALITY_FLOOR` | 126 |
| `AGY_RANK_TIMEOUT_90S` | 19 |
| `AGY_RANK_TIMEOUT_65S` | 17 |
| `NO_USABLE_FACT` | 8 |
| `CODEX_DRAFT_TIMEOUT_90S` | 1 |

The 36 ranking timeouts and the writer timeout are recorded failures in this
session. Later caller fixes do not change those historical outcomes.

| Stage | Runs with work | Median minutes | Maximum minutes |
|---|---:|---:|---:|
| Filter | 156 | 0.090 | 3.402 |
| Ranking | 103 | 1.215 | 2.538 |
| Drafting | 1 | 1.504 | 1.504 |
| Checks | 62 | 0.005 | 0.321 |
| Whole tick | 156 | 1.238 | 4.669 |

These are measured work durations for each stage; medians include only runs
with work. The sole drafting attempt timed out. With no returned draft or
confirmed send, post-to-draft, post-to-send-attempt, post-to-delivery and
Telegram-send minutes are unavailable. No latency is inferred from a tick's
duration. Run outcomes were 62 `NO_FRESH_UNSENT_DRAFTS`, 41 `REPLY_BOT_FAILED`
and 53 `NO_NEW_ELIGIBLE_TARGETS`.

The report was generated once after the session with:

```powershell
python docs/publisher/CC-511/session_funnel.py
```

The reporter reads existing results, requests and editorial returns and writes
only the named report. It starts no consumer, model, transport, scheduler or
watcher. A missing historical stage or first cause is named as unknown. The
session clock's passing alone never proves that all run records exist.
