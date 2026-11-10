# CC-338: frozen public calls

The scorecard reads the existing confirmed publication feed and plan-post outbox.
One confirmed destination includes a call even when another channel is pending.
Removed posts remain in the population. Repeated state updates retain the original
wording. A changed call is a separate version. Execution states never enter the
public projection. Main supplies numerical scores; public states do not establish
returns or forecasting skill.

[Seven initial focused tests](scorecard-tests.xml) passed in 6.66 seconds in one pytest
process. [The corrected operating-data read](observed-20261107-validated/public-call-scorecard.md)
shows two calls since 6 November 00:00 ET: one invalidated and one triggered.
This projection is an observation through 7 November 01:55 GMT+7, not a public
publication or a numerical resolution. The exporter writes only its requested
output directory and reads the existing store without migration.
Neither call retains an exact public publication clock. Dispatch and call-state
times remain distinct; the table leaves publication time unknown. The earlier
observation is retained as initial-step evidence and is superseded by this read.

The item branch starts at the operating root's
`be449906fc6955acc984e49131111f36c9734d7e`. The fresh remote default is an
ancestor but lacks the live Publisher consumers, so retaining that live base
permits forward integration. Inherited telemetry, duplicate-ledger and CC-107
files are outside CC-338 commits.

Ops launched and resumed this run with `gpt-6.1-sol/max`.
`CONFIGURED_NOT_OBSERVED`: actual runtime model and effort telemetry is unavailable.
No editorial model call, schedule change or chat message was made by this step.
The future CPI preview, matching review attachment and event score remain to be
observed; this item is not DONE.

The [freeze/preview checks](freeze-tests.xml) pass 23 tests in 22.08 seconds.
They include the real feed reaching the writer with the exact freeze metadata,
the review retaining every byte (including BOM, CRLF and final newline), and the
Neo payload requiring a downloaded attachment hash before verified readback.
The existing preparation now resolves equal source clocks by append order;
the source normalizer retains verified owned context and does not truncate the
scorecard denominator. Historical native requests remain unchanged.

Ops Live supplies the public subset, never a raw private dossier. Its contract is
`capital_chronicle.frozen_public_calls.v1`, with exactly these root fields:

- `schema_version`, `event_id`, `event_time_utc`, `frozen_at_utc`;
- `reaction_map`: each row has `condition`, `market`, `direction` (bullish or
  bearish), `minimum_move`, `horizon`, `invalidation`, `naive_release_beta`;
- `q1_probabilities`: each row has `question`, `outcome`, `probability`;
- `resolution_rule`: Main's rule stated before the outcome.
- `estimate_label`: "Capital Chronicle model estimate"; `notice`: "Analysis, not
  financial advice."; `conflicts_notice`: "Capital Chronicle may hold positions
  in the markets it covers." (decisions 40 and 72 b).

Every reaction/probability row also has `source_ref`, `source_sha256` and
`known_at_utc`. Analytical displays remain exact strings in Main's units. This
consumer computes neither them nor unsupported probability complements. An empty
Q1 array preserves an explicit absent Q1 input; it does not invent one.

Attach Ops Live's exact file and hash to the existing event preparation:

```powershell
python scripts/event_public_record.py --attach-freeze <existing-event-id> --freeze-file <absolute-public-file> --freeze-sha256 <Ops-Live-SHA256>
```

This appends one preparation in the existing store, preserves older packets and
refuses replacement of an attached freeze. It creates no operation or schedule.
The existing feed pointer's `preview_event_id` uses it before the release;
`review_event_id` uses the same preparation after the release and includes the
complete existing-store scorecard. Optional `published_feed_path` selects the
same publication feed (tests select an isolated fixture).

The approved native writer authors the prose. Code supplies only structured
source/table/attachment metadata. The preview prints the full hash and ET freeze
time and leads with one exact conditional reaction. The two-hour deadline is
rechecked at the actual new browser action: CPI is due by **10 November 18:30
GMT+7** (06:30 ET). A missed CPI deadline uses the backlog's PPI alternative;
it does not relabel a late preview. Readback and reconciliation remain available.

For a review, the existing Neo transport copies the original file into that
article's own media folder, binds its hash and size to the request, and requests
an actual download hash on the same published object. A displayed filename is
insufficient. Upload uses Neo's upload tool or file-chooser interception only.
An unsupported attachment control is reported before publishing; it never opens
a native file dialog or quietly substitutes another file.

[Validation](validation.json) contains **190 distinct passing checks**, deduplicated
across the targeted JUnit files. The final feature selection is 31 tests in 42.74
seconds. All 83 native-executor regressions pass in five serial selections; a
preceding whole-file run hit the 55-second load limit and was stopped. The writer
selection passes 64, the feed 14, and the focused finished-release selection 6.
Ruff passes on every changed Python file. These are focused checks, not a suite
or new public-output claim.

[The input check](input-check-20261107.json) finds the existing
`bls-cpi-20261110` preparation and its three official sources, with no frozen
public record attached. The current Main public manifest has 15 entries and no
CPI entry. Searches of held event/catch-up runs and both lanes' research outputs
find no issued G05 public file. The first outside cause is
`G05_FROZEN_PUBLIC_FILE_NOT_ISSUED`. Ops Live supplies that Main-owned file and
hash; Publisher then resumes this item to publish the CPI preview by 10 November
18:30 GMT+7, followed by its matching post-event review and Main's actual scores.
The backlog permits PPI on 13 November if CPI is missed. No schedule was changed.

The first operating-root read exposed `PREVIEW_CONSENSUS_PROJECTION_CHANGED`:
the old CPI preparation pinned a daily index that had since changed. The repaired
existing preparation owner retains only the selected fact's exact fields and its
original source/capture hashes. Later index refreshes cannot replace that fact;
changed captures still fail. An explicit current revision appends a new preparation
with its actual receipt time and the source's original known-at time. Earlier
preparations and frozen requests stay readable and unchanged. Three added
regressions cover index changes, original cutoffs and source-byte corruption;
the updated feature selection passes 34 tests in 28.20 seconds.

Code is integrated into `A:\Capital Chronicle\ContentOps` at
`9b0470bcf870f182f02b335b66547142fdfc0133`.
[Integration evidence](integration.json) verifies all 13 changed Python files
against their Git blobs and preserves the six inherited dirty operating-root
files and both inherited builder files. The live source tag is
`contentops-live-20261107-cc338`; the source rollback tag is
`contentops-rollback-20261107-cc338` at the original `be449906` base.

The initial operating-root feature selection passed 31 checks in 24.27 seconds.
After the consensus repair, a combined root selection hit the 55-second load
limit; the [changed preparation owner's 15 checks](operating-preparation-tests.xml)
then passed in 20.23 seconds. The remaining source blobs match the tested builder
and initial root checks. Both bounded interruptions remain named in validation.

[Runtime application](preparation-repair.json) appended one current CPI preparation
and verified all earlier CPI preparation payloads unchanged. The original source
known-at time remains 5 November; its new receipt keeps its actual 7 November
time. [The operating consumer](operating-consumer-read.json) loads the installed
modules from the operating root, reads the real publication feed and outbox,
returns the two public calls, and successfully reads the current CPI background
and its single cited consensus fact. It still has no G05 frozen public file.
No public write, model call, chat message, schedule change or process restart was
performed. This is integrated code and an applied input repair; CC-338 remains
BLOCKED on the Main-owned G05 file and the subsequent real public acceptance.

## CPI run, 10 November

The current run retains the operating-root base `a7f2c6cd` and the inherited dirty
files. Its launch is `gpt-6.1-sol/max`, CONFIGURED_NOT_OBSERVED. The preparation
now uses the 10 November Investing.com core monthly forecast rather than the
old annual forecast. The named Main research reaches the existing preview writer
as exact hash-bound excerpts; its Desk p decimals have a deterministic percent
display, with no new estimate or freeze claim. The 16 focused event-record checks
pass in 6.61 seconds; Ruff passes. Source changes, invented excerpts and later
known-at times are still refused. Publication and the later event review remain
the item’s operating acceptance.

The actual CPI calendar selection exposed an unrelated-identity source projection.
The existing context attachment now accepts verified held CPI sources during
media preparation, retains the selected topic documents and joins the official
history before writing. Nineteen focused context checks pass in 18.02 seconds.
The original native selection, source clocks and source budgets remain recorded.
