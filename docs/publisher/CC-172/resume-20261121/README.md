# CC-172 dispatch timing readback, 21 November 2026

**The 15-minute live acceptance remains unmet.** The installed timing projection
found zero passing samples across 28 native review runs. The 20 November CC-715
wrap had three bound editions and zero dispatches. The first edition's text was
approved at 21:48:15 GMT+7, and its data window ended at 21:57:05 GMT+7. The other
two editions had no recorded text approval. See the
[native readback](native-timing-readback.json).

The next observed published article, CC-536 piece 5, also missed the target.
Its approved body hash matches both the committed reviewed copy and the runtime
copy. Text approval was recorded at **10:49:43 GMT+7 on 21 November**, so the
dispatch deadline was **11:04:43 GMT+7**. Native action evidence records the
Substack send at **10:53:54 GMT+7** and the X send at **11:13:15 GMT+7**, 23 minutes
31 seconds after approval. Discord, Facebook, Instagram and Telegram each had an
exact verified readback by the deadline. Threads had a later verified readback,
which supplies an upper bound. LinkedIn member was reconciled absent, LinkedIn
company was confirmed with no exact send clock in the retained evidence, and
YouTube recorded a definite no-write. The [channel readback](cc536-clock-readback.json)
keeps attempted, observed send, verified readback and publication clocks distinct.
It uses the original coordinator records and makes no platform request.

The [Main source readback](main-readback.json) found that the latest completed
report expired at 21:32:01 GMT+7. Two newer Main captures had no completion
receipts at 22:02 GMT+7. The next scheduled CC-124 check is 22 November at
03:40 GMT+7. The weekend wrap (CC-379) is also an eligible source of live timing
evidence when it runs. Replay the first approved text and the actual dispatches
from the next timely article through the existing timing consumer.

The [targeted checks](targeted-tests.xml) report 28 passes from the operating
root at `4c9fe4ac8655cf5fcc96ef47261f1928cfc69663`. They include the one-repair
cap, preserving the first approval clock, automated image checks, pending Neo
requests, the binary and tool-output guards, the confirmed-post golden fixtures
and the wrap renderer. A broader latency test attempt exceeded the decision-window
budget, and a separate diagnostic attempt timed out. The completed targeted
run is the recorded test result.

Launch arguments recorded `gpt-6.2-sol/high` as `CONFIGURED_NOT_OBSERVED` in
`ResearchRuns/claude-ops-integrations/codex-exec/publisher-cc-172-20261121T1453/launch.json`.
This is an evidence delivery from the operating HEAD. Editorial roles and
public transports were idle during this run.
