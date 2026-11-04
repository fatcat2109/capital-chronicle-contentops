# CC-216: early event-preview backgrounds

The existing newsroom can now use its hash-bound preparation in an explicit
`EVENT_PREVIEW` operation. `newsroom --preview-event-id <retained event id>` binds
that event once, freezes the verified prior BLS passages in the existing input
outbox, and passes them through the retained-source resolver to the actual writer.
The preparation's question and background remain editorial context; the dated
official passages establish past facts. No future release values or dossier
probabilities are supplied by this adapter.

One selected CC-068 consensus fact joins as attributed context under decision 44
and host rule 7. Its original capture and projection hashes, period, source and
known-at clock are checked. The writer receives that single fact, without the raw
table; it cannot become a chart or consensus series. The capture's original rights
class is preserved. BLS history still comes from CC-010 through the existing chart
owner, including real gaps and first-print vintages.

This branch starts at the operating root's `eee788fd5d5f3aa17773f1c52f6ee0586d625b53`,
which contains Publisher's integrated fixes after remote master. The two modified
V6 history files and the untracked earlier-run evidence are excluded from commits.

Validation: 42 source/feed/history checks passed; 26 native-entry/live-launch checks
passed; 29 preview/source-research checks passed, followed by 8 passing preview
checks after the bounded outbox query and usable preparation label were applied.
The tests exercise the actual feed-to-writer source pack, one consensus citation
without raw-table disclosure, immutable resume, source/capture hashes, event scope,
rights and clocks. XML results are beside this file.

The top-level Ops launch was configured as `gpt-6.1-sol / max`, PID 50056, started
5 November 2026 at 03:30:52 GMT+7. This is `CONFIGURED_NOT_OBSERVED`; no supported
runtime telemetry established the actual model/effort. Editorial role observations
are retained with their actual native request/return artifacts.

CC-107 retains the post-freeze scenario insertion and canonical-first dispatch.
Final publication acceptance depends on the future frozen dossiers and actual
destination readbacks. Preparing or reviewing a background is not that acceptance.
