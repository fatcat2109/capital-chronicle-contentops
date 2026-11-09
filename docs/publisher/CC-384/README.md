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

Integrated into `A:\Capital Chronicle\ContentOps` by fast-forward at
`15ad2aab542d97186131d092f5d2f6348650de9c`. **20 installed tests passed in
4.50 seconds**, saved in [installed-tests.xml](installed-tests.xml). A fresh
installed import read the live export through Main's strict reader, consuming
85 transition/result rows. Its source blob matches the committed module, and
all six pre-existing modified operating-root files retain their prior hashes.
See [integration.json](integration.json). The two inherited modified builder
ledgers remain outside every item commit.

CC-384 remains **BLOCKED: CC383_LIVE_EXPORT_FIELDS_PENDING**. At **10 November
2026 02:30 GMT+7**, the validated live export had 47 plans, zero
`public_instrument` fields and zero `entries` fields; CC-383 was still
IN_PROGRESS. The first real post using those fields, including both entries
when present, cannot yet be read back on Telegram, Discord and Threads.
This is an upstream production-data dependency, not an integration wait.

Choice: one conditional call with both entry alternatives keeps the idea in one
first post and fits the destination limits. The consumer is installed before
CC-383 lands. Ops Live integrates CC-383 through its existing reviewed route;
then Codex Publisher verifies the first eligible new idea and its three public
readbacks through the existing minute publisher/coordinator. No historical plan
is reposted to manufacture that evidence. No schedule or
other chat changes are part of this item.
