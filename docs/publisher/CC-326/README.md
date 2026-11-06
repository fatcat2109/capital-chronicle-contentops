# CC-326: public times in ET

Decision 90 uses America/New_York, labelled ET, for new public copy. UTC records,
Bangkok schedules, already-published objects and immutable historical records stay intact.

The formatter feeds article/recovery prompts, retrospective notices, digest title/card
and card dates. The coordinator, resolved API router, Neo handoff and frozen Neo begin
check final public copy before a fresh write. Readback remains available.

First passing sub-step: `builders-tests.xml`, 148 focused tests passed. This covers DST,
date rollover, nine destination checks, actual consumer acceptance of ET, retrospective
history, exact frozen-request replay, digest delivery and reader-presentation recovery.
`launch.json` records gpt-6.1-sol/high from the running exec's configured arguments;
actual model and effort telemetry are unavailable (CONFIGURED_NOT_OBSERVED).

Integration and next-article public readback are recorded below when observed.

Second passing sub-step: `media-tests.xml`, 78 focused checks passed. The ET
retrospective notice survives all eight native derivative packages, and delivery-card
source dates convert aware instants before selecting the New York day. Date-only source
periods and sealed historical article bytes remain intact.
