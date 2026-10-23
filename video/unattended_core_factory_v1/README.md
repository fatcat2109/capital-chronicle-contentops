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
- `caption_revision.py`: whitespace-only caption revision through the current
  package factory. It preserves cue timings and words and does not render picture
  or synthesize audio. It does not prove readable or synchronized final captions.

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

## Acceptance limits

`OWNER_REVIEW_READY` is a saved private package boundary. It grants no final AV,
voice, factual/numeric authority, rights release, account readiness, deployment,
unattended-runtime or publication acceptance. Actual independent review remains
required. Silent proxy frames, text and loudness measurements do not prove hearing.

The bounded Goal39 checkpoint and retained technical probe live at
`docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal39/`.
The probe explicitly preserves its historical source bytes and any current-contract
HOLD. It never becomes a native return or enters the current factory as accepted work.
