# CC-074 FOMC release check — For Ops

The retained FOMC article passes the source, chart and clock checks. Publication is
BLOCKED by the installed V1 release gate: `OWNER_MANUAL_PUBLICATION_NOT_AUTHORIZED`.
Decision 37 B1 supplies publication authority; this is a binding/promotion defect,
not a request for another approval or for clean production days.

The accepted base is `bade5d93fec8c72ee002bd0c0efbcee4b6e2cf83`. All 207 sealed
artifact hashes remain exact. The two charts show the 10/2 vote and the announced
policy settings, traced to the two retained Federal Reserve documents within the
28 October cutoff. Both PNGs were opened and compared with those values. The
accepted prose, source clocks, eight previews and prior MAX reviews are unchanged.
This check is not a new same-writer final-render acceptance.

The existing operation `cc074-retro-fomc-20261028-v1` is still bound to the private
copied store with `owner_manual_validation: true`. The exact installed
`scheduled_publication_authority` function rejects that binding before any store
call. Rewriting the flag would not promote the accepted operation into the live
store and would falsify its original private scope. No transport was called.

Validation: 37 targeted retrospective tests pass, including sealed-byte integrity,
chart geometry/source/rights checks and hindsight/writing-date fault injections.
The initial run had 25 passes and 11 failures because absolute fixture paths pointed
at the other worktree, now on CC-042. Tests now relocate only in-memory fixture
references to the same sealed files in this exec checkout. No source or historical
artifact was edited. Ruff and whitespace checks pass.

Evidence: [release-check.json](release-check.json) and
[targeted JUnit](retrospective-guards.xml). The launch arguments specify
`gpt-6.1-sol` and `model_reasoning_effort="max"`; actual model/effort remain
`CONFIGURED_NOT_OBSERVED`.

Next action: Claude Ops integrates a scoped promotion of this exact accepted packet
through the existing live owner/store and sole publisher, preserving its original
binding and review history, then resumes this article. Do not publish from the
copied store or allocate a replacement article. No schedule or chat was changed.
