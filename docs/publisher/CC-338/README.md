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

[Validation](validation.json) contains **187 distinct passing checks**, deduplicated
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
