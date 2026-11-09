# CC-379 — the complete weekly scored-call record

Decision 106 is wired into the existing native newsroom source stage, writer,
article validator and canonical reader projection. The sole publisher and its
exact Substack readback remain in use. No schedule or historical post changes.

For a weekend/weekly wrap, `NativeDesktopTurn.weekly_call_sources` reads Main's
existing public plan-status export through its own contract reader. It adds one
source document before the evidence packet and writer freeze. An explicit
`weekly_call_record: true` candidate or `WEEKLY_WRAP` / `WEEKEND_WRAP` tag also
selects this path when the headline has a different name. Ordinary articles and
previously frozen requests retain their original inputs.

The source includes every `SCORED` plan whose **resolution** is in the most recent
complete Monday–Friday in New York time, and whose score is known by the operation
cutoff. Late scoring retains the original resolution week. A corrected score uses
Main's current outcome once. Untriggered plans are not scored. The cumulative
`scored_call_count` is checked against the exported scored plans; the weekly counts
come from the included rows. They are never substituted for one another.

The record gives the market, original direction, entry zone and explicit result:
hit, stopped, or closed at the end of its window. It prints weekly scored-call,
hit and stop counts and decision 40's notices. Private score commentary, money,
size, account fields and R never enter the public projection. It makes no
performance or track-record claim. Entry-zone decimals retain source precision.

The native MAX writer receives the exact section and usual source-marker rules.
The ordinary article validator rejects omitted losses, altered values or duplicate
sections, and strips any writer-supplied certification metadata. The reader
projection retains all lines and source-derived binding metadata. The public-copy
guard recognizes only the complete dated, resolved-result grammar as a historical
direction; new unconditional calls and execution details still fail.

`weekly_scored_calls_v1.json` stays beside the existing operation's evidence. It
retains source hashes, source clocks, the ET week, exact selected rows and text.
Restart reuses that file; it does not refresh an issued writer request. The public
source document's publication clock is the latest included Main score's own clock
(the export clock for an empty record). The export's separate generation clock
remains recorded. No price or outcome is inferred.

Validation: **227 targeted tests passed** in 12.03 seconds, one pytest process:

```text
python -m pytest -q tests/test_weekly_scored_calls_cc379.py tests/test_event_article_guard_v1.py tests/test_native_desktop_editorial_v1.py tests/test_v1_simple_gemini_newsroom_v1.py --tb=short
```

The tests exercise the actual newsroom source hook, native request owner, article
validator, canonical reader projection and Substack readback comparator. Readback
rejects a missing loss and an altered weekly stop count. Fixtures also cover two
losses despite selective exit posting, a window-end close, corrections, ET/DST
boundaries, future knowledge, empty weeks and unchanged frozen inputs.

[Live source probe](live-source-probe.json) records a successful read at
**10 November 00:10:55 GMT+7**, with no public write. The completed 2–6 November
week has one window-end close; the cumulative export has two scored calls. The
Sunday result is outside that Monday–Friday record. This probe does not substitute
for the requested 9–13 November wrap.

This Ops-dispatched launch configured `gpt-6.1-sol/high` (PID 21004, launch
9 November 23:50:46 GMT+7), `CONFIGURED_NOT_OBSERVED`. No editorial model call was
made for this implementation. Future wrap preparation, writing, editing and
distribution keep the existing approved roles and coordinator.

The next acceptance is the **14–15 November** wrap, after the 9–13 November ET
week is complete (**14 November 12:00 GMT+7**). Resume its existing CC-124 or
weekly-wrap operation, compare the retained Main rows with the assembled section,
then use the ordinary Substack readback. CC-379 is not DONE until that real
readback confirms every row and the counts. No replacement post or retrospective
edit is used to manufacture acceptance.

[Operating-root verification](integration.json) records the fast-forward into
`A:\Capital Chronicle\ContentOps` at `42bcef82` and **25 passing weekly-path tests**
there in 6.87 seconds. All four changed modules have matching committed Git blobs;
checkout newline conversion is recorded separately from raw-byte hashes. The
inherited two builder ledgers and six modified operating-root files remain out
of these commits. New native CLI processes load the integrated source; no app
restart was needed.
