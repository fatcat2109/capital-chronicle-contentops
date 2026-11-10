# CC-406 Vietnamese morning gold note

The installed Publisher CLI produced a 100-word Vietnamese note with one BLS
chart for 11 November. The note was ready at 02:48 GMT+7. The installed CC-418
reader consumed its exact bytes, the desk's normal refresh included it, and
BrowserOS Neo showed the note, its chart and the Copy note control on Jim's page.

The three-morning acceptance remains open. The backlog names 13 November as
the first morning. The 11 November delivery is an early working example and
is excluded from that count. The next three trading mornings are 13, 16 and
17 November, each with delivery by 07:30 GMT+7. Future deliveries need their
real file and desk observations.

## Product path

`scripts/run_native_desktop_editorial.py` attaches the note to the existing
Publisher entry through its housekeeping function. It exposes the pending
native MAX request and explicit submit, inspect and accept continuations.
The existing editorial outbox retains each dated request and return.

The producer selects Main's latest original capture, projects its gold view
and six-market rows through the existing public-span adapter, and searches
held Main evidence for the newest official BLS CPI release known by that
capture. Both printed figures match Main's summary when Main restates them.
The chart uses the exact official monthly headline and core observations,
with the period, seasonal adjustment, units and BLS attribution.

I chose the held CPI driver chart because it explains the rates channel in
Main's gold view and supplies the item's one chart from an official source.
The original capture, report observation, retrieval, native response, render
review and actual desk delivery clocks remain separate in the artifacts.

The native writer authors the Vietnamese prose. Validation checks the
150-word ceiling, the exact final line, source-bound numbers, official
attribution and public-text restrictions. The writer inspects the rendered
PNG and text before the producer installs the paired dated files into
`A:\Capital Chronicle\Runtime\ContentOps\gold-notes`. The installed CC-418
consumer already reads that folder.

The current launch arguments configure `gpt-6.1-sol/max`. The exact response
and review record `CONFIGURED_NOT_OBSERVED`, with runtime model and effort
fields left null because supported runtime telemetry is unavailable.

## Existing CLI

Run from `A:\Capital Chronicle\ContentOps` with the applied rollout.

```text
python -B scripts/run_native_desktop_editorial.py gold-note --rollout config/native_desktop_rollout_v1.json
python -B scripts/run_native_desktop_editorial.py gold-note-submit --rollout config/native_desktop_rollout_v1.json --note-date YYYY-MM-DD --response <authored-response.json>
python -B scripts/run_native_desktop_editorial.py gold-note-accept --rollout config/native_desktop_rollout_v1.json --note-date YYYY-MM-DD --response <render-review.json>
python -B scripts/run_native_desktop_editorial.py gold-note-status --rollout config/native_desktop_rollout_v1.json --note-date YYYY-MM-DD
```

Use the date and hash returned by the pending request. The native response
contains `request_sha256`, `output.text`, `output.fact_ids` and the actual
`invocation_observation`. The review contains `text_sha256`, `chart_sha256`,
`accepted` and the findings from inspecting those exact artifacts. A retry
reuses the saved response and preserves the first delivery clock. A late
delivery retains its real timestamp and fails that morning's deadline.

Jim can copy the note and share it with its paired chart in his community.
The later bot setup described by the backlog starts with Jim creating a bot
and adding it to that community. Zalo's verified official account remains
its separately named setup step.

## Evidence

- [Validation](validation.json) records the 17 feature checks and 37 editorial regression checks.
- [Native delivery](native-delivery.json) binds the actual note, chart, original sources and render review.
- [Installed consumer](installed-desk-consumer.json) records the exact installed CC-418 reader consuming the dated files.
- [Desk refresh](cached-desk-readback.json) verifies the refreshed desk data contains the exact note.
- [Browser readback](browser-readback.json) records the note, Copy note control and chart link in the task's Neo tab.

One early source-inventory command overprinted metadata into the session.
The committed evidence contains only the bounded records linked above.
