# Private manual native factory integration

This selectively ports the existing V2 job/stage owner from donor `10d18873`.
It is an isolated, manually stepped integration candidate. It does not install or
invoke an Automation, daemon, model bridge or platform provider.

## Existing owners

- `store.py`: one V2 SQLite store, jobs, exact dedupe and append-only stage events.
- `desktop_session.py`: requested native role contracts; model fields do not
  independently attest the actual runtime model or reasoning setting.
- `supervisor.py`: existing ordered factory stages and hard validation.
- `media.py`: current shared freeform render/cache and package owners, local
  Kokoro waveform timing, separate audio, captions and FFmpeg mux.
- `../daily_operator_v1.py`: read-only canonical published-corpus qualification;
  manual qualification writes only this same `runtime_root/v2_jobs.sqlite3`.
- `../locale_activation_hardening_v1`: retained locale/timing compatibility;
  external voice execution is disabled and credentials are never read.
- `caption_revision.py`: caption layout/position successors, separately measured
  phrase narration and local captioned review through existing media/package owners.
  Layout changes preserve words/timing/media. Phrase narration creates a new audio,
  transcript and SEO identity, fitting original picture windows at the same voice
  speed or returning an overflow HOLD. Listening remains a separate review.
- `../freeform_chapter_pipeline_v1/native_narrative.py`: binds a saved native
  source/narrative return, verifies exact source/asset bytes and measures existing
  local narration. It applies the real five-to-forty-five-minute duration contract;
  it does not pad a short script or supply chapter creative.

The current 23-locale registry and six official shadow surfaces remain in their
existing owners. They are not equivalent to active voices or ready accounts.

## Bounded commands

Run from the repository root. An explicit config contains `mode` equal to
`ISOLATED_MANUAL_PRIVATE_ENGINEERING`, a `runtime_root` beneath this checkout's
`.task-runtime`, `scaffold_root`, accepted canonical project `dependency_root`,
`asset_root`, local `kokoro_model` / `kokoro_voices`, an exact
`implementation_head`, `worker_id` and `session_label`. Keep host-specific config
and artifacts outside Git. Do not include credentials.

```text
python -m video.unattended_core_factory_v1.manual admit --config <config.json> --packet <governed.json> --job <identity>
python -m video.unattended_core_factory_v1.manual step --config <config.json> --job <identity> --max-stages 1
python -m video.unattended_core_factory_v1.manual submit --config <config.json> --job <identity> --return-file <native-return.json>
python -m video.unattended_core_factory_v1.manual status --config <config.json>
python -m video.unattended_core_factory_v1.manual caption-layout --config <config.json> --job <sealed-identity> --revision <new-identity> --width 32
python -m video.unattended_core_factory_v1.manual repair-mux --config <config.json> --job <sealed-identity> --revision <new-identity>
python -m video.unattended_core_factory_v1.manual recover-editorial --config <config.json> --job <quarantined-identity> --revision <new-identity>
python -m video.unattended_core_factory_v1.manual phrase-audio --config <config.json> --job <sealed-identity> --revision <new-identity>
python -m video.unattended_core_factory_v1.manual caption-layout --config <config.json> --job <sealed-identity> --revision <new-identity> --width 29 --line-percent 10
python -m video.unattended_core_factory_v1.manual caption-review --config <config.json> --job <sealed-identity> --revision <new-identity>
python -m video.unattended_core_factory_v1.manual longform-narration --config <config.json> --packet <native-source-request.json> --return-file <native-source-return.json> --revision <new-identity>
python -m video.unattended_core_factory_v1.manual locale-package --config <config.json> --job <sealed-identity> --packet <native-localized-request.json> --return-file <native-localized-editorial.json> --revision <new-identity>
python -m video.unattended_core_factory_v1.manual locale-review --config <config.json> --job <sealed-identity> --locale es --revision <new-identity>
```

`step` resumes the saved run after reacquiring a released claim. Its optional exact
job selector cannot silently claim a different queued story. Missing creative input
leaves an immutable request in the existing job inbox, bound to exact input bytes.
A human/native Codex task performs the actual bounded creative work. Python only
validates and ingests the explicit returned artifact. No Python-to-chat invocation
is implied. Never invent a native task identity or substitute a retained artifact
for a fresh native return.

A return contains `kind`, `request_sha256`, the actual self-reported
`native_task_id`, requested `model=gpt-5.6-sol`, `reasoning_effort=xhigh`,
`provenance_limit=ASSIGNED_ROLE_NOT_INDEPENDENT_RUNTIME_ATTESTATION`, and `artifact`.
Kinds are `EDITORIAL_NARRATION`, `EDITORIAL_TIMING_REVISION`, `MOTION_VISUAL`, and
`ACTUAL_MEDIA_REVIEW`. Use the generated request and validators for exact fields.

For a qualified published candidate, governed expansion must bind
`published_source_binding` to its exact `candidate_key`, `source_content_hash`,
`trigger_packet_hash`, and `source_v1_identity`; `story_id` must match the saved
published story. This closes the donor's unrelated-packet activation gap. Dated
owner-permitted engineering inputs remain separate from published qualification.
Qualification's batch bound is caller-selected, not a daily product output ceiling.

`repair-mux` applies only after an observed picture-stream mismatch in a sealed
private package. It preserves original files, reuses picture/narration/mix/captions,
and rebuilds only mux/package/review descendants in a distinct revision. The same
ledger records the three affected stages as invalidated and superseded. Future
caption revisions resolve that ledger's latest package, avoiding superseded media.
The final mux never uses `-shortest` and verifies exact video stream/frame identity.

`recover-editorial` is limited to one exact pre-motion retention/timing quarantine.
It preserves the job, run and original failure event. Mixed factual/security failures
cannot enter this path. A fresh native editor returns against the saved request;
unchanged segment audio can be reused even after reordering.

`phrase-audio` keeps the existing voice and speed, measures each phrase waveform,
rejects window overflow and binds new audio/transcript/caption/package descendants
to the same job ledger. `caption-layout` and its position option also update that
ledger. Same-revision replay verifies artifact hashes and does no duplicate media
work. `caption-review` is an explicitly private local caption burn and playable
review page, separate from the canonical clean picture. It performs no transport.
The inline review cues work on local file pages without browser file-origin fetches.

`locale-package` currently demonstrates the retained Spanish `ef_dora / 1.45`
candidate. Exact current package, governed source, source timing, translated segment
identities and registered voice settings are mandatory. Existing local synthesis and
locale alignment/mux owners measure the actual phrases and reject window overflow;
they never increase speed to make a translation fit. A locale descendant records its
manifest in the same job ledger while preserving the sealed English source state.
`locale-review` resolves that locale event rather than replacing the English package.
Spanish listening/voice acceptance remains required; this command enables no provider
or platform. The existing23profiles/sixsurfaces retain their separate readiness holds.

## Acceptance limits

### Private native chapter and final-picture corrections

The same manual entry admits sealed longform source and renders individual
chapters through `freeform_chapter_pipeline_v1`; it does not create a second
compositor or renderer. These bounded commands require the existing isolated
configuration:

```powershell
python -m video.unattended_core_factory_v1.manual longform-admit --config <config.json> --packet <exact-native-request.json> --return-file <sealed-native-return.json> --revision <identity>
python -m video.unattended_core_factory_v1.manual longform-chapter --config <config.json> --revision <identity> --chapter CH01
python -m video.unattended_core_factory_v1.manual longform-phrases --config <config.json> --revision <identity> --caption-revision <phrase-identity>
python -m video.unattended_core_factory_v1.manual longform-package --config <config.json> --revision <identity> --caption-revision <phrase-identity>
python -m video.unattended_core_factory_v1.manual longform-reflow --config <config.json> --revision <native-timing-correction-identity>
python -m video.unattended_core_factory_v1.manual picture-revision --config <config.json> --job <existing-job> --revision <identity> --packet <exact-native-request.json> --return-file <sealed-native-return.json>
python -m video.unattended_core_factory_v1.manual review-cohort --config <config.json> --revision <identity> --packet <four-package-review-specification.json>
```

An optional `--request-owner-snapshot` preserves exact original engineering source
bytes when the execution owner has subsequently changed. The admission records
both hashes separately; this never substitutes for the exact factual inputs.
Every chapter render rechecks admitted sources, assets, inputs, manifest and
execution owner before consulting its cache. Measured phrase overflow remains a
HOLD, requiring a justified timing/editorial correction rather than faster speech.
`--phrase-geometry-json` selects bounded two-line grouping by exact segment;
changing grouping requires a distinct revision and preserves words and voice speed.

`picture-revision` accepts a source-bound native material correction after a sealed
short package. It writes separate source/media/package descendants in the same job
ledger, verifies unchanged frame timing and retains original audio/captions. It
does not invalidate or repeat narration synthesis. The package remains private and
requires actual final-picture review. A previous revision's review page is retained.

`longform-reflow` places verified cached phrase waves inside explicit native-corrected
chapter windows. It checks every word, waveform identity and actual duration and
performs no synthesis. `review-cohort` creates one local page linking exactly four
existing packages/players and verifies their artifact hashes; it changes no job state.

`OWNER_REVIEW_READY` is a saved private package boundary. It grants no final AV,
voice, factual/numeric authority, rights release, account readiness, deployment,
unattended-runtime or publication acceptance. Actual independent review remains
required. Silent proxy frames, text and loudness measurements do not prove hearing.

The bounded Goal39 checkpoint and retained technical probe live at
`docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal39/`.
The probe explicitly preserves its historical source bytes and any current-contract
HOLD. It never becomes a native return or enters the current factory as accepted work.
