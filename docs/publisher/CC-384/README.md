# CC-384 — public instrument and both entry conditions

The existing plan-status composer reads CC-383's `entries` and
`public_instrument`, including the latter's aligned `entries`. One combined
conditional call carries the limit and breakout alternatives, the direction,
window and invalidation. The idea still has one queue identity and one first
post per API destination. X keeps its existing thread route.

Mapped prices are used only as a complete set. Null or incomplete mappings
retain the plan prices, explicitly labelled, and never fill or convert a null.
The fill post names the instrument. Only declared public fields enter the
composer; execution metadata is excluded. Existing rows without the new fields
keep their original text and package behavior. New rows carry format 3 so their
conditional lines remain intact in X threads; frozen older rows keep format 2.

Initial validation: 15 targeted tests passed in 6.19 seconds, in
[focused-tests.xml](focused-tests.xml). They exercise the export queue, card
facts, existing coordinator, destination limits and repeat suppression using
isolated stores and fixture transports. No real post was sent by these tests.

The branch starts at fresh remote master and fast-forwards to the operating
root's accepted `cdb2b25e`, preserving its current consumers. The two inherited
modified ledgers stay uncommitted. This run configures gpt-6.1-sol/high,
CONFIGURED_NOT_OBSERVED; no editorial model call is made here.

Compatibility validation: **97 passed in 337.95 seconds**, one pytest process,
across the seven targeted status-post queue, publication, rationale, recovery,
fill and correction files. See [regression-tests.xml](regression-tests.xml).
Final item validation: **20 passed in 3.85 seconds**, including the committed
Main producer's EUR spot, dual WTI null and dual WTI mapped public exports.
See [final-tests.xml](final-tests.xml), [producer-shape.json](producer-shape.json)
and [sample-posts.json](sample-posts.json). Samples are fixtures, not public posts.

The producer supplies its mapped direction, used for inverse expressions without
inferring a conversion. A dual-entry fill does not identify the filled leg, so
its wording confirms an entry without claiming that the limit zone filled.
Delayed first posts preserve registration and update clocks within the short
copy limit. New public fields do not change the retained result-post price basis.

The existing `CapitalChronicle-PlanStatusPosts-V1` task runs `pythonw.exe -B
scripts\plan_status_posts.py --publish` from the operating root. Its readback
is in [live-consumer-task.json](live-consumer-task.json). There is no task change.
The exact launch arguments are recorded in [launch-config.json](launch-config.json).

Pending: operating-root integration and the first real Telegram/Discord/Threads
post after Main CC-383 integrates. No schedule or
other chat changes are part of this item.
