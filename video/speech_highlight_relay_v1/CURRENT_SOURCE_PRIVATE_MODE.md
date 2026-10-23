# Current-source private preparation

This additive mode uses `live_contentops/speech_highlight_current_source_v1.py`
and the existing relay's clipper, vertical compositor, caption generators and media
checks. Retained replay, its source packet/probe and validator are unchanged.

## Entry and source walk

Use the existing native Desktop conversation for editorial turns. There is no model
API, new scheduler, operational store, provider fallback or uploader in this mode.

```powershell
python -m live_contentops.cli speech-highlight-current-source `
  --owner-source explicit-source.json --stream-file existing-source-stream.json `
  --repo-root . --output-dir .task-runtime/speech_highlight_relay_v1/example/discovery
```

`explicit-source.json` is a source-reference object; the stream file is an array of
actual existing headline/manual/Neo source-reference rows. Each needs `source_id`
and `canonical_source_url` (HTTPS, no embedded credentials). Include publisher,
event/publication date or its unknown state, speaker attribution, relevance and the
existing stream/receipt identity. The adapter preserves these fields, gives the
explicit reference priority, deduplicates exact URLs and admits at most three
references. It does not crawl, download, infer rights, or make an owner grant.
Unchanged discovery reuses the same plan; changed inputs require a distinct plan.

For the bounded first operation, inspect up to three sources and prepare at most
two useful jobs. A rights or audio hold is a real outcome. Another official clip
does not establish delivery of the separate business/CEO category.

## Prepare and resume

```powershell
python -m live_contentops.cli speech-highlight-current-source `
  --source-config source.json --repo-root . `
  --output-dir .task-runtime/speech_highlight_relay_v1/example/job
# Supply the saved native returns when available:
python -m live_contentops.cli speech-highlight-current-source `
  --source-config source.json --repo-root . `
  --output-dir .task-runtime/speech_highlight_relay_v1/example/job `
  --selection-return selection.json --meaning-return meaning.json
```

The source schema is `contentops.speech_highlight_relay.current_source_private.v1`:

- Exact `source_id`, publisher, canonical URL, event date, acquisition receipt and
  attributed speaker (`name`, `role`); `production_eligible` must be false.
- `media`: repo-relative local `file`, SHA-256 and duration in seconds.
- `transcript`: repo-relative local file and SHA-256. Its JSON array contains finite,
  non-overlapping `start_seconds`, `end_seconds`, `text` utterances within that
  recording. Distinguish official text, publisher captions and ASR in acquisition
  provenance. Publisher clocks are not audio alignment proof.
- `rights`: source-specific private-processing basis, pinned evidence artifact,
  recording SHA-256 and explicit limitations. Missing permission prevents rendering.
- Separate `audio_review` and `timing_review`. An affirmative claim requires a named
  reviewer, method and pinned JSON evidence binding this exact media/transcript and
  matching status. This validates the binding, not the truth of the human claim.

The helper writes the frozen source and native selection request. The assigned
`gpt-6.1-sol/low` role returns exact source hash, role/model/effort, native task/turn
identity with provenance limits, selected format, continuous 5–120 second span,
unchanged complete utterance wording, rationale and surrounding context. The source
hash alone is not an independent model attestation.

The subsequent `gpt-6.1-sol/max` meaning request includes the selected span and its
digest. Its return binds both source and selection, and separates `speaker_claim`,
`independent_evidence` and `cc_interpretation` from concise `headline`/`context`.
KEEP permits private rendering; HOLD needs a reason. Neither grants factual or
publication authority. Preserve conditional wording, dates and attribution.

All five choices remain available: Moment + Context, What Changed, Claim Check,
Question and Answer, Consequence/Watchpoint. Comparison, claim-check and Q&A require
additional pinned supporting artifacts with source URL/date, relationship and
proposition. Existence/hashes do not prove semantic independence or a correct Q&A
association; the native meaning and subsequent audio/context reviewer must establish
those. A format declaration is not an actual completed format proof.

Only validated native returns are frozen. Saved returns are loaded on resume when
omitted. A changed source or completed return is rejected. Completed clip/render
stages are reused only after checking their edit seal, file hash and media shape.
An abandoned exact `.partial` output can be rebuilt; an unsealed final file requires
reconciliation. A completed package with changed bytes fails closed. Run one writer
per output directory; this bounded manual mode is not an unattended concurrency owner.

## Review-bound delivery

Outputs are a clean vertical master, captioned derivative, SRT/VTT/JSON, frozen
source/native requests and returns, YouTube Shorts/TikTok metadata, and
`review_request.json`/`current_package.json` binding exact source, edit and assets.
The review request names original listening, timing, contextual/qualifier fidelity,
visual/caption quality, rights and separate publication authority.

Inspect the real output. File presence, a waveform, transcript/ASR or a successful
FFmpeg run does not prove hearing, meaning, timing or viewer-facing quality. Missing
capable audio review stays unverified. Record reviewer evidence against the exact
edit/assets; do not rewrite original speech or accepted historical packets to clear
a gate. Media stays in task-local storage; commit provenance, hashes, probes and
review evidence only.

Every package stays `PRIVATE_PREPARED_REVIEW_REQUIRED`, `PUBLICATION_HOLD`,
`ZERO_PUBLIC_WRITE` and `production_eligible=false`. Its inherited zero call/write
counters describe the local helper, excluding explicit source acquisition and native
agent turns. There is no upload, unlisted/private post or platform draft. The existing
separately authorized delivery owner remains responsible for any later platform act.

Goal37's owning handoff and actual proof/held dimensions are in
`docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal37/CHECKPOINT.md`.
