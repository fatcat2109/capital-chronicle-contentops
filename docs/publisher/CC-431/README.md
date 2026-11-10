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

Remaining acceptance: a production-store-copy seven-derivative Neo replay, fresh
live X readiness, operating-root integration, and one exact live status/article
readback. Former no-writes may post late only while their plan is still active,
under the existing CC-340 source/time and coordinator checks.
