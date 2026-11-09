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

Canonical regression: `consumer-regression-initial.xml` passed 214 checks and exposed one
stale assertion equating issued scheduler prompt wording with regenerated prompt wording.
The corrected check preserves every schedule field except the deliberately frozen prompt
and checks decision 90 in new prompt generation. `native-editorial-regression.xml` passes
all 13 tests in that file. No schedule or rollout configuration changed.

Operating root: `A:\Capital Chronicle\ContentOps`, verified code commit
`73053979d3db099d4f03fee3c595266a6537260a`. `operating-root-tests.xml` passes all 55 CC-326 checks from that root,
including ET copy reaching the real coordinator implementation with isolated test stores
and transports. `integration.json` binds matching source hashes and unchanged WIP hashes
in both worktrees. Rollback: `contentops-rollback-20261106-cc326` (`c1abfa82d9c6570363a168b951b38a80fbd82bf9`).
Live tag: `contentops-live-20261106-cc326` on the final evidence commit with those same code bytes.

Remaining acceptance: the next ordinary article's actual canonical/channel public readback.
The latest confirmed canonical was dispatched at `2026-11-06T04:15:30.548809+00:00`, before decision 90
and this integration. It cannot satisfy that check. CC-326 stays IN_PROGRESS for this
single observation; the existing Publisher publication/readback flow supplies it on the
next article. No schedule, mailbox, desktop, public object or production store was changed.
