# CC-172 — 14 November 2026

**The implementation is live; the real 15-minute dispatch acceptance has not
passed.** This continuation refreshes the evidence without changing product code.

The existing publication projection consumed a consistent, read-only SQLite
snapshot covering 30 native article reviews and 25 runs, including registered
LinkedIn company copies. None supplies complete 15-minute dispatch proof.
[Actual saved clocks](live-timing-observation.json) retain missing observations,
the first approval, original public identities and exact channel states. This is
a durable-record observation, not a fresh browser readback.

The latest article is `cc338-cpi-preview-20261110-v1`. Its text was approved on
10 November at **18:32:49 GMT+7**. Substack's observed send was **19:09:33 GMT+7**
(36.7 minutes later); Instagram's was **19:24:00 GMT+7** (51.2 minutes later).
LinkedIn lacks a confirmed send. Later reviews did not restart the text clock.
Closed historical YouTube/company no-writes remain closed; this check does not
retry them. Neither their treatment nor any missing clock changes the observed
Substack and Instagram deadline misses.

Newer canonical objects were also checked for scope. The daily digest is the
existing link index, and the newer plan pages/status posts keep their separate
contracts. They do not substitute for a newly approved newsroom article.

## Why the next sample cannot run now

The [source consumer readback](source-consumer-readback.json) rechecks all 41
retained Main source files against CC-124's 14 November assessment. Their exact
bytes are unchanged. The installed operating-root publication-clock consumer
uses their bound original data clocks: 39 return `ARTICLE_DATA_CUTOFF_EXPIRED`
and two lack a source-supplied cutoff. None of the completed outputs is eligible.

The latest completed analysis captured data on **13 November at 22:06:27 GMT+7**;
its publication deadline was **23:06:27 GMT+7**. Retrieval, report completion,
media refresh and a new review cannot extend that deadline (decision 98/CC-403).
The held-source assessment also covers event dossiers, horizon/strategy output,
Data/Publisher research, the configured Main feed and the backlog/archive; see
[CC-124's assessment](../../CC-124/run-20261114-0033/README.md).

The outside cause is `ARTICLE_DATA_CUTOFF_EXPIRED`. Main/Ops Live supplies a
fresh Main output. The existing CC-124 opportunity consumes it, then CC-172
measures every applicable dispatch from that article's first text approval.
The old Web `NEWSROOM_CANONICAL_REQUIRED` dependency is not this run's cause.

## Verification

The focused repair-cap, approval-clock, missing-send, image-load and binary/output
selection passed **19 tests**, with 20 deselected, in one pytest process:
[test result](focused-tests.xml). Source hashes verify that these tested files
match the operating root; no product source needed changing.

[Validation](validation.json) records the live consumers and inherited work.
[Integration](integration.json) records the pushed evidence commit, operating
root, live/rollback tags and preserved work. No public or production-store write,
editorial-role call, browser action, app restart, schedule change or chat message
was made. The launch arguments explicitly set `gpt-6.1-sol/high`, recorded as
`CONFIGURED_NOT_OBSERVED`; runtime model/effort telemetry is unavailable.
