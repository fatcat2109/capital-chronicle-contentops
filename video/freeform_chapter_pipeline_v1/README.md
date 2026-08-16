# Free-form chapter pipeline V1

This is the minimum deterministic production substrate for a chapterized, creator-authored Remotion film. It does not accept a storyboard schema, layout enum, scene quota, visual-state quota, creative score, or fixed compositor contract. Viewer-facing React/Remotion source remains the creative artifact.

The pipeline owns only hard production work:

- the 1920×1080/30 fps, five-to-forty-five-minute longform contract;
- zero video public-write and zero V1-mutation authority;
- HIGH parent / XHIGH creative-worker orchestration metadata;
- MAX, ULTRA, and 4K prohibition for this task;
- local dirty-range picture rendering with handles;
- chapter picture cache identity from actual source and asset bytes;
- full-chapter picture lock only after creative approval;
- concat-compatible picture assembly;
- independent narration, authority, music, SFX, and ambience stems;
- audio-only rebuilds and final muxes that do not render video;
- deterministic media probes and performance telemetry.

The task manifest is `frozen_without_breaking.manifest.json`. Runtime media, bundles, caches, proxies, and masters live under the caller-selected workspace and remain outside Git.

`package_factory.py` extends this same substrate with configurable global locale profiles,
factual-anchor validation, actual-audio-timed SRT/WebVTT/JSON captions, one canonical picture
identity per editorial format, and immutable platform-neutral manifests. Production is
`AUDIO_SIDECAR_FIRST`: burned captions are optional-only and locale changes do not render picture.

`governed_translation.py` is a fail-closed, local-files-only Qwen3-4B translation adapter. It is
not factual authority and never silently repairs a failed anchor. `tts_routes.json` and
`voice_registry.json` make provider/voice selection an explicit one-time capability decision.
`zero_rerender_sidecar_proof.py` writes captions/metadata and performs only an FFmpeg
`-c:v copy` mux while recording zero Remotion, public-write, V1 and scheduler operations.

Examples from the repository root:

```text
python video/freeform_chapter_pipeline_v1/pipeline.py validate
python video/freeform_chapter_pipeline_v1/pipeline.py render-range Chapter04 1200 1410 .task-runtime/ch4-fix.mp4 --profile fast --concurrency 4
python video/freeform_chapter_pipeline_v1/pipeline.py render-chapter Chapter04 --profile lock --concurrency 4
python video/freeform_chapter_pipeline_v1/pipeline.py assemble .task-runtime/picture.mp4 <seven locked chapter paths>
python video/freeform_chapter_pipeline_v1/pipeline.py mix-audio audio-edit-plan.json .task-runtime/final-mix.wav
python video/freeform_chapter_pipeline_v1/pipeline.py mux .task-runtime/picture.mp4 .task-runtime/final-mix.wav .task-runtime/owner-master.mp4
```

Creative telemetry may be recorded, but it is not a target and cannot block media. Only truth/numeric authority, rights/provenance, security/sandbox, corrupt media, the format contract, and publication authority are deterministic blockers.
