# CC-431 — restore the existing X Neo publication route

Jim's decision 112 restores X publication, readiness, requests and exact readback.
The required derivative set is derived from the existing transport/bar registry:
Telegram, X, Discord, LinkedIn member, Facebook Page, Instagram Business and Threads.
YouTube Community, LinkedIn company and Instagram browser edits retain their bars;
CC-386 replies remain parked. The dated CC-393 platform review stays unchanged.

The branch starts at operating HEAD `9496221eb9e628de84d964325ae05b01e875f647`,
which already contains CC-393/395 and the current status-post consumer. Remote
`origin/master` predates those live changes. The three earlier lane modifications
are preserved separately, as recorded in `pre-existing-work.json`.

`route-tests.xml` records 38 passing route, coordinator-consumer, public notice,
saved-request, uncertainty and remaining-platform-bar checks. X uncertainty is
counted by normal recovery again. These tests use controlled transports.
`launch-observation.json` records the observed launch configuration as
`gpt-6.1-sol/max`, `CONFIGURED_NOT_OBSERVED` for actual runtime model telemetry.

The copied production-store replay in `copied-store-seven-replay.json` confirms
all seven through the real coordinator and Neo handoff, with controlled returns,
strict X content readback and no duplicate on resume. The copy preserves real
incidents; a declared next-day simulation avoids their current-day cooldown.

The restored consumer includes both legacy status posts and the current call-card
format, carrying the full existing copy in bounded X threads. Article distribution
requires fresh X identity before fanout. Exact old X bar no-writes can be claimed
once only when the current Main export still admits that active plan. A second
activity check runs before the browser claim; readback survives plan expiry.
Other no-writes, identified writes and uncertain attempts cannot use this path.
Frozen source/copy times remain exact; new dispatch records carry the true clock.

`consumer-tests.xml`: 243 passes, including canonical coordinator and durable-store
regressions, plus two old call-card expectations corrected afterward.
`final-route-tests.xml`: 73 passes including those two cases, active/ended/uncertain
recovery, atomic claim fencing, X readiness, restored agent routes, public copy,
call-card parent continuity and the remaining platform bars.

The measured live WTI failure exposed Unicode weighting in the old `len()` helper.
The helper now follows Twitter Text v3's weighted ranges and URL length. Frozen
copy can be reflowed across post boundaries only when every word, number and its
order remain exact. `unicode-reflow-tests.xml` has 19 passes; the broader existing
native regression has 130 passes; `final-reflow-tests.xml` has 11 passes including
exact reflow acceptance. Changed or missing numeric content still fails.
`unicode-source-and-incident.json` retains the official configuration and the
92-second regression's machine-load overrun. No additional tests are needed.

All three 10 November active status no-writes now have strict live confirmation:

| Market | Root | Posts | Actual send (GMT+7) |
|---|---|---:|---|
| S&P 500 | [2120014234310541324](https://x.com/Capitalnicle/status/2120014234310541324) | 12 | 10 Nov 2026 11:42:35 |
| EUR/USD | [2120015650529964275](https://x.com/Capitalnicle/status/2120015650529964275) | 9 | 10 Nov 2026 11:48:13 |
| WTI | [2120031752936923332](https://x.com/Capitalnicle/status/2120031752936923332) | 12 | 10 Nov 2026 12:52:12 |

Each `*-submit.json` records `RECONCILED_CONFIRMED`. Full ordered text and each
original card were read back; source and platform images were inspected and the
platform bytes stay binary under `media-readback/`. Original event times, frozen
wording and hashes remain exact. No ended plan was posted late. WTI's original
disabled composer was read back before recovery; its stale tab was closed after
the final exact thread was confirmed.

`live-consumer-final.json` records the installed modules, source hashes, seven
required destinations, unchanged remaining browser bars, and all three durable
confirmations. The existing `CapitalChronicle-PlanStatusPosts-V1` task already runs
`scripts/plan_status_posts.py` from `A:\Capital Chronicle\ContentOps`; its schedule
was not changed. Operating-root source and the pushed item branch match (allowing
Git's CRLF conversion in the call-card module). All three earlier lane files and
all six earlier operating-root modified files are byte-preserved. No chat was
messaged, no application was restarted, and no test process remains.
