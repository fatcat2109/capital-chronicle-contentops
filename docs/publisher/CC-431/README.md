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

Remaining acceptance: operating-root integration and the exact live X readbacks.
`live-no-write-inventory.json` records the three current active status obligations.
