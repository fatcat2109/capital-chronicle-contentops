# CC-403 — reader copy, daily notes and the data clock

The existing native writer and sole publication coordinator now consume the
reader contract. New requests lead with our call in first person, use clean
titles, carry one Main-sourced scenario set and a "So what" line, and limit
prose sentences to 35 words. The source validator names an internal phrase or
unsupported number in its refusal. The transport boundary checks again before
an actual write, including a delayed BrowserOS request's `begin` operation.

The daily note has one six-market table, at most 350 words outside that table,
"What changed since yesterday" and "What we got wrong". Decision 114 supplies
the first draft through the existing AGY text CLI, with its approved model,
effort, empty working folder and 120-second bound. Code checks the draft, then
the existing native request dispatches one `gpt-6.1-sol/low` editorial pass with
the draft and findings. A failed AGY call returns to that same Codex pass.
Restart reuses the exact saved result, including a failure. There is no new
queue, scheduler, publisher, model fallback or per-card writer.

Weekly reviews retain the strong Codex assignment and CC-379's complete dated
call record. The native candidate's `headline_text` now selects that existing
source hook too. The existing validator still refuses omitted losses, changed
counts and duplicate records. The daily word cap does not apply to the weekly
review. Both formats retain the source, rights, public-instrument, scenario,
image, identity, exactly-once and readback owners.

For retained native Main reports, the public-span adapter reads only the
original capture's `known_at_utc` into the public source's clock metadata,
binding the capture file hash. It projects no account or execution values.
The first admitted Main passage is the lead source. Older context retains its
separate clock and neither ages nor refreshes the lead. Report generation,
retrieval, text approval and media refresh cannot restart the deadline.

The current source pack and its data clock bind the new request and the
compiler article. A canonical write after 60 minutes is refused. Publication
status reports an observed publication clock separately from an exact-object
readback's upper bound. A late readback without a publication clock leaves the
timing unknown. It never invents a send time. Derivative recovery and all
readback/reconciliation remain available after the deadline.

New request settings still select the assigned roles explicitly. Actual model
and effort observations are retained as returned, including unknown or different
values. The old return-label veto is removed under decisions 60 and 86. The
same source, public-copy, rights, operation, writer identity, paid-speed and
exact-render checks remain in their owning functions.

Historical requests, responses, public objects and their hashes are preserved.
An older frozen source pack also retains its original bytes when the only
newly available fields are the two added source-clock metadata fields.

Implementation owners:

- [Reader checks and clock](../../../live_contentops/reader_article_contract_v1.py).
- [AGY first draft](../../../live_contentops/daily_note_first_draft_v1.py).
- [Native request/return](../../../live_contentops/native_desktop_editorial_v1.py)
  and [role dispatch](../../../live_contentops/codex_desktop_newsroom_operator_v1.py).
- [Source/reader validator](../../../live_contentops/v1_simple_gemini_newsroom_v1.py),
  [public Main spans](../../../live_contentops/main_report_projection_source_v1.py)
  and [weekly record](../../../live_contentops/weekly_scored_calls_v1.py).
- [Live publication check](../../../live_contentops/article_publication_quality_v1.py),
  [existing editor review](../../../live_contentops/contentops_editorial_desk_v1.py)
  and [publication timing](../../../live_contentops/native_publication_latency_v1.py).

Validation so far: **274 distinct tests pass**, with 3 preview-host cases skipped under decision 83. The [test summary](tests-summary.json) preserves every failed run and its corrected result. Runs use at most three targeted files, one pytest process at a time, without parallel workers; no suite ran. No test started before **10 November 22:30 GMT+7**.

Regression checks exposed two owned handoff defects: the newly compiled destination count was not updated, and final visual review still requested a removed destination. The handoff now records its actual count and reviews its compiled variants; frozen originals are unchanged. Definite no-writes caused by platform rules are excluded from the timing target with their exact cause; uncertain writes still require recovery and remain in the timing result. Older text fixtures now use decision 109's current public notice and current transport-return semantics.

The syntax-only read of 16 Python files passed without imports. The new policy also keeps an older bound operation's epoch, including its unfinished stages. Operating-root verification and the actual decision-114 draft result follow before integration is reported.

The [launch record](launch.json) reads back `gpt-6.1-sol/max`, labelled
`CONFIGURED_NOT_OBSERVED`; actual runtime telemetry is unavailable. The
[preserved-work record](preserved-work.json) binds the three inherited builder
files and six inherited operating-root files. They stay out of this item's
commits. The base is the current operating commit `17c49b960d54a7dc6e090ab048fb047bd6c04a89`;
remote master predates the installed Publisher work.

The full public acceptance remains the next eligible daily note's clean-title
Substack readback and publication within 60 minutes of its actual data cutoff.
Today's CPI preview already serves as the 10 November wrap under decision 98;
that decision bars a second wrap. The existing dated evidence is
[CC-124's source check](../CC-124/run-20261110-2014/README.md). The article cap is
not the cause. The next ordinary daily note is 11 November's pre-US wrap. This
item changes no schedule and sends no chat message.
