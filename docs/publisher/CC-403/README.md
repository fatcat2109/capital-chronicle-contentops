# CC-403 — reader copy, daily notes and the data clock

**CC-403 remains blocked on a current completed Main analysis for its public daily-note acceptance.** At **10:02 GMT+7 on 17 November**, the newest completed usable single-pass Main report retained its **07:37:43 GMT+7** data cutoff and **08:37:43 GMT+7** publication deadline. The installed clock consumer returned `ARTICLE_DATA_CUTOFF_EXPIRED:8678s`. Two exact Main passages enter the actual writer source pack with their original capture clocks. [Current continuation](run-20261117-0954/README.md).

**114 targeted tests pass.** This continuation corrects a daily-note test fixture whose claim text still included internal source markers. The existing integration case now proves that all claim bindings survive current source validation and the article body stays exact. Production validation is unchanged. Both the initial 66-pass/one-failure run and the corrected three-file run are retained. The [verification](run-20261117-0954/verification.json) confirms all eight inspected production owners match the tested source and all eight inherited modified files remain exact.

The source search now includes Main's current `analysis-native.json` reports and shocks, superseding the older assumption that only 11 November's `owner-native.json` reports were available. Today's article count is 0/2. The existing CC-124 request remains invalidated and is not retried. Ops Live supplies a current completed Main analysis; Publisher then continues the existing daily-note path and records its clean-title Substack readback and actual publication within 60 minutes of its original cutoff. No new operation, public write, application restart, chat message, Claude invocation or schedule change was made.

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
exact-render checks remain in their owning functions. The downstream qualification
owner also records actual model/effort values without a second label veto; its
new daily-note cases and canonical production-day tests pass.

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

Targeted validation has no unresolved failures. The test history records 330 passing case identities across its revisions, with three preview-host cases skipped under decision 83; the final installed-source run has 91 passing tests. The [test summary](tests-summary.json) preserves failed runs and their corrected results. Parameter variants retained from the earlier test name are counted as distinct there; they are not additional model calls. Runs use at most three targeted files, one pytest process at a time, without parallel workers; no full suite ran. No test started before **10 November 22:30 GMT+7**.

Regression checks exposed two owned handoff defects: a newly compiled destination count was not updated, and final visual review still requested a removed destination. The handoff now records its actual count and reviews its compiled variants; frozen originals are unchanged. Definite no-writes caused by platform rules are excluded from the timing target with their exact cause; uncertain writes still require recovery and remain in the timing result. Older text fixtures use decision 109's current public notice and current transport-return semantics. The final recovery cases prove allowed destinations receive the copy while barred browser routes retain a definite no-write.

The syntax-only read of 16 Python files passed without imports. The new policy keeps an older bound operation's epoch, including unfinished stages. An adversarial wrapped Markdown sentence still receives the same length check as its rendered paragraph.

One actual decision-114 first-draft call used the held 9 November public packet. It returned **AGY_UNAVAILABLE: AGY_DAILY_DRAFT_TIMEOUT_120S**, with no final response, from **22:52:16 to 22:54:17 GMT+7**. Its configured `gemini-3.8-flash-high/high` remains `CONFIGURED_NOT_OBSERVED`. The [saved summary](retained-draft/summary.json), exact local receipt and [artifact hashes](retained-draft/artifact-inspection.json) preserve that failure. It was not retried and created no publication operation. Tests exercise the unavailable result through the real native request owner and still dispatch the one light editor. A successful actual AGY draft is not claimed.

The [launch record](launch.json) reads back `gpt-6.1-sol/max`, labelled
`CONFIGURED_NOT_OBSERVED`; actual runtime telemetry is unavailable. The
[preserved-work record](preserved-work.json) binds the three inherited builder
files and six inherited operating-root files. They stay out of this item's
commits. The base is the current operating commit `17c49b960d54a7dc6e090ab048fb047bd6c04a89`;
remote master predates the installed Publisher work.

The full public acceptance remains the next eligible daily note's clean-title
Substack readback and publication within 60 minutes of its actual data cutoff.
The 10 November CPI preview served as that day's wrap under decision 98; its
no-second-wrap restriction was the earlier hold, not the current cause.
The 11 November source check finds zero daily article slots used; the source's
expired data clock is the cause. A fresh completed Main analysis is the next
required input. This item changes no schedule and sends no chat message.
