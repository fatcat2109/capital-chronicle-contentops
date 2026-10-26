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

## Local review, correction and re-review (Goal38)

Use the same CLI over an existing completed package, with a **separate output
directory**. The original package remains unchanged. No local server is required.

```powershell
python -m live_contentops.cli speech-highlight-current-source `
  --review-package .task-runtime/speech_highlight_relay_v1/goal37/fed-job `
  --review-surface --output-dir .task-runtime/speech_highlight_relay_v1/review-01
```

Open the returned local `index.html` in Neo. Play the full original and either clean
or captioned cut. Seek the selected passage, start with15seconds adjacent context,
remove the boundary to inspect more, or click a caption to seek both players. Context
adequacy is a reviewer decision; the15second convenience is not a full-context gate.
The page shows original source/transcript/edit hashes and separated speaker assertions,
independent evidence and CC interpretation. Playback/time advance does not mean heard.

Record a status and finding for every dimension: VISUAL, CAPTIONS, AUDIO, TIMING,
CONTEXT, RIGHTS. Keep unavailable dimensions NOT_VERIFIED. For a PASS or requested
revision, provide pinned evidence using repo-relative `file`/`sha256` references.
Use actual observed frames for visual review, not a controlled unit fixture. Evidence
and reviewer identity/method are self-reports; parsing/hash validation is not independent
attestation. Unsupported attestation/capability, text/ASR-only audio PASS, missing or
changed evidence, stale source/transcript/edit/output binding are rejected. Claims from
a genuinely capable reviewer remain recorded findings, with no automatic rights,
publication or production promotion.

Export the JSON, then ingest it explicitly. `--review-surface` also builds a new
snapshot displaying the accepted findings and unresolved dimensions:

```powershell
python -m live_contentops.cli speech-highlight-current-source `
  --review-package <exact-package-directory> --review-return <exported-findings.json> `
  --review-surface --output-dir .task-runtime/speech_highlight_relay_v1/review-02
```

The receipt and original return have content-derived filenames. An exact repeat reuses
their bytes without a duplicate record. Changed findings create a distinct immutable
receipt. A changed page context uses a new review snapshot directory; previous snapshots
are not overwritten.

A correction spec has schema `contentops.signal_clips.revision.v1`, exact
`parent_binding` copied from the reviewed context, `review_sha256` (canonical JSON digest
of the return), `change_kind`, and a concrete `reason` tied to the matching requested
finding. The supported kinds are:

- PRESENTATION: requested VISUAL finding plus `presentation` with style
  `SOURCE_CENTRAL_PHONE_V1`, framing reason, explicit `source_evidence_preserved` basis
  and contiguous relative shot ranges (`start_seconds`, `end_seconds`, `framing`).
  SPEAKER_CENTER uses a full-height center crop of62.5% of source width; FULL_SOURCE
  retains the whole original frame. Use the latter for wide/context/evidential shots.
  There is no face identification or automatic evidence-safe cropping claim. Check
  actual rendered shots and boundaries. Text is inherited from the saved native meaning;
  this mode does not invent another hook or silently rewrite uncertainty.
- CAPTIONS: requested CAPTIONS finding and `cues` with valid relative times, unique cue
  IDs and exact source speaker. Re-segmentation/timing may change; cumulative normalized
  wording must equal the selected original quote. Only the captioned render/sidecars,
  metadata and review are invalidated; the clean master/source/clip/native work is reused.
  A literal spoken-word correction requires a separately verified source/transcript and
  native admission; it is rejected by this bounded caption-layout ingress.
- SEMANTIC: requested CONTEXT finding and a fresh assigned native Sol MAX
  `meaning_return`, bound to the same source/selection and a distinct native task/turn
  identity. Changed context rebuilds both renders, metadata and review while retaining
  source, transcript, selection and extracted clip. This does not permit changing the
  actual quote, source, speaker or span via a presentation patch.

```powershell
python -m live_contentops.cli speech-highlight-current-source `
  --revision-from <exact-reviewed-package> --revision-spec <correction.json> `
  --review-return <same-findings.json> `
  --output-dir .task-runtime/speech_highlight_relay_v1/successor-01
```

The successor directory must be distinct and non-nested. It freezes the spec and prior
review, copies verified unaffected inputs, reuses sealed completed renders after an
interruption and binds new media/metadata/review. Old review findings never clear the
successor: export a fresh review from its exact local surface. No separate ledger,
background process, queue or uploader is involved. One writer owns each directory.

Actual Goal38 release review entry:
`.task-runtime/speech_highlight_relay_v1/goal38/release-reviewed/index.html`.
The original Goal37 job and all three Goal38 presentation attempts are preserved.
Revision1 was held for a real Windows CRLF/FFmpeg line-spacing defect; revision2 uses
exact LF layout. The final revision3 also retains the full saved context rather than
truncating input lines, and has its own actual visual-only PASS. The source, selected quote, original caption
words/timing, extraction and native turns were reused. Final caption/audio/timing/context/
rights acceptance remains open. The full evidence and commands are in the existing
`goal38/CHECKPOINT.md`; prepared media is neither uploaded nor published.
