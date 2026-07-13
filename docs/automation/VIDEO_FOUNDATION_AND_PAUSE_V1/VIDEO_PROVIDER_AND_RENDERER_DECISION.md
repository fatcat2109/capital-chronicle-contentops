# Video Provider and Renderer Decision

## Classification

`PASS_VIDEO_FOUNDATION_DEEP_REPO_DISCOVERY_AND_EXECUTION_PACKET_V1`

The repository-side renderer and abstraction decisions are resolved. Under the operator override, fresh official-document access is not required for this local-only planning phase. Provider boundaries remain schema/request-builder-only and no unverified endpoint, field, model, limit, price, scope, or response claim is accepted.

## 1. Renderer decision

## Decision

**Use a Python-first local renderer built around existing chart/media code plus FFmpeg. Do not adopt Remotion for Phase 2.**

## Repository evidence for this decision

1. **A real FFmpeg-based short-video renderer already exists**
   - [live_contentops/source_chart_short_video_v1.py](live_contentops/source_chart_short_video_v1.py)
   - It already discovers `ffmpeg`, builds a vertical chart-sequence command, and outputs MP4.

2. **A real rendered MP4 artifact already exists in committed evidence**
   - [eight_platform_live_20260710_recovery1_source_charts_short.mp4](docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/video/eight_platform_live_20260710_recovery1_source_charts_short.mp4)
   - Matching manifest: [video_manifest_v1.json](docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/video_manifest_v1.json)

3. **The repo already uses Python image/chart tooling**
   - [live_contentops/macro_chart_renderer_v6.py](live_contentops/macro_chart_renderer_v6.py) uses `matplotlib`
   - [live_contentops/media_manifest_authority_v1.py](live_contentops/media_manifest_authority_v1.py) uses `PIL`
   - [live_contentops/oil_rc_editorial_repair_v1.py](live_contentops/oil_rc_editorial_repair_v1.py) uses both `PIL` and `matplotlib`
   - tests also rely on these packages

4. **No Remotion surface exists**
   - no `remotion` dependency found in [ui/contentops_v5/package.json](ui/contentops_v5/package.json) or inspected lockfiles
   - no dedicated Node video-render project exists
   - frontend is standard Vite/React, not a render pipeline

5. **Current runtime architecture is overwhelmingly Python-first**
   - canonical runner, evidence bridge, freshness, visual gates, media manifest, platform adapters, repair logic, and evidence packets all live in [live_contentops/](live_contentops/)

## Practical Phase 2 outcome

Phase 2 should:

- keep rendering local and deterministic;
- extend the existing FFmpeg path rather than introduce a second renderer family;
- add metadata probing, subtitle sidecars, proof-render QA, and packetization around the existing renderer;
- keep all video work non-posting and local-only.

## 2. Dependency decision

## Decision

**Do not add Remotion or another Node-based rendering stack in Phase 2.**

**Prefer zero net-new runtime dependencies if possible. If dependency declaration hardening is required, formalize only Python packages that runtime modules already import.**

## Repository-grounded rationale

- `PIL`/Pillow and `matplotlib` are already imported by committed runtime modules and tests.
- `ffmpeg` is already assumed as an external binary and discovered via `CONTENTOPS_FFMPEG_BINARY` or `shutil.which("ffmpeg")` in [live_contentops/source_chart_short_video_v1.py](live_contentops/source_chart_short_video_v1.py).
- Top-level manifests inspected during Phase 1 do **not** clearly declare these rendering packages as project dependencies.

## Phase 2 dependency plan

1. First preference:
   - reuse existing charts/images and FFmpeg without adding a new third-party rendering family.
2. If dependency declaration hardening is needed:
   - update [pyproject.toml](pyproject.toml) to formalize `Pillow` and/or `matplotlib` only if Phase 2 local validation proves that declaration is required.
3. Do **not** add Remotion.

## 3. Provider decision model

Provider decisions are limited to **safe abstraction boundaries**, not live-integration claims.

### ElevenLabs

**Decision:** primary TTS abstraction target, request-builder/schema only.

- planned runtime file: `live_contentops/video_provider_boundaries_v1.py`
- Phase 2 should define normalized TTS request packets only.
- No live provider call, no audio generation, no secret handling, no usage telemetry call in Phase 2.

### HeyGen

**Decision:** primary avatar abstraction target, request-builder/schema only.

- planned runtime file: `live_contentops/video_provider_boundaries_v1.py`
- Phase 2 should define normalized avatar request packets only.
- No live job submission or polling in Phase 2.

### D-ID

**Decision:** optional avatar fallback, request-builder/schema only.

- same boundary file as above
- no live provider call in Phase 2

### YouTube

**Decision:** request-builder boundary only; no upload executor in Phase 2.

- planned runtime file: `live_contentops/video_provider_boundaries_v1.py`
- keep YouTube Community as the default text/image surface
- keep Shorts and long-form as explicit non-default video modes
- no public or private video upload in Phase 2

### TikTok

**Decision:** request-builder boundary only; no browser or API posting in Phase 2.

- planned runtime file: `live_contentops/video_provider_boundaries_v1.py`
- no TikTok Studio browser execution in Phase 2
- no native Content Posting API call in Phase 2

## 4. Fresh official-document research status

## Retried in this continuation

The following official pages were retried in this session via `WebFetch` and/or equivalent official-web tooling attempts, and remained unavailable because the harness safety classifier refused the calls before execution:

### ElevenLabs
- `https://elevenlabs.io/docs/api-reference/text-to-speech`
- `https://elevenlabs.io/docs/api-reference/pronunciation-dictionaries`

### HeyGen
- `https://docs.heygen.com/`

### D-ID
- `https://docs.d-id.com/`

### YouTube
- `https://developers.google.com/youtube/v3/docs/videos/insert`
- `https://developers.google.com/youtube/v3/guides/uploading_a_video`
- `https://support.google.com/youtube/answer/15424877`

### TikTok
- `https://developers.tiktok.com/doc/content-posting-api-get-started/`

### Renderer docs
- `https://remotion.dev/docs`
- `https://ffmpeg.org/ffmpeg-doc.html`

## Result

Fresh live inspection date for these pages was not established in-session. This does not block Phase 1. It establishes the deferred prerequisite `LIVE_PROVIDER_DOC_REVALIDATION_REQUIRED_BEFORE_PROVIDER_INTEGRATION`.

## 5. Repo-grounded official-doc evidence still available

The repo does contain prior official-doc grounding for **YouTube** and **TikTok**.

### YouTube repo-grounded references

- official URL recorded in repo: `https://developers.google.com/youtube/v3/docs/videos/insert`
- upload guide URL recorded in repo: `https://developers.google.com/youtube/v3/guides/uploading_a_video`
- Shorts help URL recorded in repo evidence: `https://support.google.com/youtube/answer/15424877`
- snapshot timestamp recorded in repo: `2026-06-23T07:09:32Z`
- snapshot source: [live_contentops/platform_docs_registry.py](live_contentops/platform_docs_registry.py)

### TikTok repo-grounded references

- official URL recorded in repo: `https://developers.tiktok.com/doc/content-posting-api-get-started/`
- snapshot timestamp recorded in repo: `2026-06-23T07:09:32Z`
- snapshot source: [live_contentops/platform_docs_registry.py](live_contentops/platform_docs_registry.py)

### No comparable repo-grounded evidence found for Phase 1 continuation

No pre-existing committed official-doc grounding was found during this task for:
- ElevenLabs
- HeyGen
- D-ID
- Remotion
- FFmpeg

Accordingly, Phase 2 remains boundary-only. Any later provider execution requires fresh official-document validation first.

## 6. Partial vs safe-to-reuse runtime surfaces

### Safe to extend

- [live_contentops/source_chart_short_video_v1.py](live_contentops/source_chart_short_video_v1.py)
  - local-only renderer primitive
- [live_contentops/media_manifest_authority_v1.py](live_contentops/media_manifest_authority_v1.py)
  - strong exact-hash media authority model
- [live_contentops/video_platform_capability_matrix_v1.py](live_contentops/video_platform_capability_matrix_v1.py)
  - non-posting capability audit surface

### Partial / must not be treated as production-ready video execution surfaces

- [live_contentops/edge_cdp_publishing_adapter_v1.py](live_contentops/edge_cdp_publishing_adapter_v1.py)
  - `publish_youtube_short_via_edge`: explicit/non-default browser helper, not canonical default path
  - `publish_tiktok_video_via_edge`: partial browser helper, not a hardened canonical path
  - long-form YouTube helpers support readback/metadata/visibility maintenance, not a complete upload runtime

## 7. Final decision table

| Surface | Decision | Phase 2 live calls allowed? | Notes |
|---|---|---:|---|
| Renderer | Python-first local renderer + FFmpeg | No | Reuse existing renderer primitive and manifests |
| Remotion | Do not use | No | No repo footprint; wrong stack for first implementation |
| ElevenLabs | Primary TTS abstraction target | No | Boundary/schema only until fresh docs are available |
| HeyGen | Primary avatar abstraction target | No | Boundary/schema only until fresh docs are available |
| D-ID | Optional avatar fallback | No | Boundary/schema only until fresh docs are available |
| YouTube long-form | Request-builder only | No | Private-first boundary only |
| YouTube Shorts | Keep explicit non-default helper separate | No | Existing helper remains outside default lane |
| TikTok | Request-builder only | No | No browser/API posting in Phase 2 |

## 8. Phase 1 closeout

Phase 1 is `PASS_VIDEO_FOUNDATION_DEEP_REPO_DISCOVERY_AND_EXECUTION_PACKET_V1` because the planning artifacts are coherent and the required local validation passed. Provider execution remains prohibited. Before any future integration or execution, revalidate the official URLs listed above and record the verified contract separately.
