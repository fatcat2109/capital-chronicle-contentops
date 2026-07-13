# Current System Map

## 1. Repository architecture

### Canonical surfaces

- Canonical UI: `ui/contentops_v5/`
- Canonical UI entrypoint: `ui/contentops_v5/src/App.tsx`
- Canonical backend domain: `live_contentops/`
- Canonical live text/image runner: `live_contentops.eight_platform_substack_first_pipeline_v1`
- Canonical generalized prepare-only mode: same runner with `--prepare-generic-fabric`
- Canonical browser profile: Microsoft Edge profile at `A:\Capital Chronicle\operator-browser-profiles\contentops-social-main`

### Packaging and runtime

- Top-level Python packaging: `pyproject.toml`
- Python project name: `cc-live-contentops`
- Declared console scripts there are minimal and do not cover the canonical runner.
- Node/Vite frontend present under `ui/contentops_v5/`
- No Remotion project or dependency found.
- No `.github/workflows/` CI configuration found.

### Upstream evidence state and ContentOps pause

The Capital Chronicle public/free v1 database foundation is complete and analyzer handoff is ready at `c14e5a7f48d1d949da60c217c4467c2418f1fbf6`. That milestone does not satisfy ContentOps publication eligibility. The authoritative packet still records `dqr=BLOCKED` and false values for exact authority, forecast runtime, canonical apply, broker execution, and institutional exact authority.

The text/image lane state is therefore `FROZEN_WAITING_FOR_PUBLICATION_ELIGIBLE_UPSTREAM_EVIDENCE`, not `FROZEN_WAITING_FOR_DATABASE_BUILD_COMPLETION`. ContentOps resumes through `RESUME_TASK_CONTENTOPS_FINAL_AUTOMATION_PIPELINE_CLOSURE_AFTER_UPSTREAM_DQR_STATE_CHANGE` only when the consumed packet proves the necessary DQR/public-use permission, `reporting_allowed=true` where required, and fresh event/market evidence.

## 2. Canonical generalized prepare-only architecture

```text
operator command
→ live_contentops.eight_platform_substack_first_pipeline_v1.main()
→ --prepare-generic-fabric branch
→ live_contentops.generic_editorial_fabric_v2.run_generic_prepare_only()
→ live_contentops.cc_evidence_bridge_v2.build_evidence_packet_from_cc_root()
→ live_contentops.source_capability_registry_v2.resolve_story_capabilities()
→ live_contentops.freshness_market_state_v2.evaluate_freshness()
→ live_contentops.editorial_visual_research_v2.evaluate_visual_composition()
→ live_contentops.editorial_review_orchestrator_v2.run_editorial_review()
→ evidence packet + decision artifacts written to output dir
```

### Core modules

- Evidence bridge: `live_contentops/cc_evidence_bridge_v2.py`
- Freshness gate: `live_contentops/freshness_market_state_v2.py`
- Visual research/composition: `live_contentops/editorial_visual_research_v2.py`
- Editorial roles: `live_contentops/editorial_review_orchestrator_v2.py`
- Source/story capability registry loader: `live_contentops/source_capability_registry_v2.py`
- Identity registry loader and action guards: `live_contentops/distribution_identity_registry_v2.py`

## 3. Canonical public text/image architecture

```text
operator command
→ live_contentops.eight_platform_substack_first_pipeline_v1.main()
→ live_contentops.eight_platform_substack_first_pipeline_v1.run_eight_platform_substack_first_pipeline()
→ live_contentops.substack_first_north_star_pipeline_loop_v1.prepare_substack_first_pipeline()
→ article export + deterministic + LLM editorial gate
→ edge Substack publication
→ delivery media manifest binding
→ native derivative payload compilation
→ idempotent per-platform dispatch wrapper
→ platform adapters / strict readbacks
→ run evidence + platform matrix + operator audit packet
```

### Major runtime pieces

- Preparation loop: `live_contentops/substack_first_north_star_pipeline_loop_v1.py`
- Canonical runner/orchestrator: `live_contentops/eight_platform_substack_first_pipeline_v1.py`
- Browser publishing/readback adapter: `live_contentops/edge_cdp_publishing_adapter_v1.py`
- Delivery media authority: `live_contentops/media_manifest_authority_v1.py`
- Telegram adapter: `live_contentops/telegram_live_adapter_v6.py`
- Facebook adapter: `live_contentops/facebook_page_adapter_v6.py`
- Instagram adapter: `live_contentops/instagram_adapter_v6.py`
- Threads adapter: `live_contentops/threads_adapter_v6.py`
- Public duplicate freeze guard: `live_contentops/public_dispatch_freeze_guard_v6.py`

## 4. Identity and platform authority model

### Registry authority

- Visible identity authority file: `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/distribution_identity_persona_registry_v2.json`
- Runtime loader/validator: `live_contentops/distribution_identity_registry_v2.py`

### Effective approved identities

- Substack: Capital Chronicle
- Telegram: `@CapitalChronicle`
- Discord: `The Macro Pigeon`
- X: `@Capitalnicle`
- LinkedIn: founder-led / `Jim Pham` / `linkedin:jimcc`
- Facebook Page: Capital Chronicle
- Instagram Business: `official.capitalchronicle`
- Threads: `official.capitalchronicle`
- YouTube Community: `@CapitalChronicleYouTube`

## 5. Existing recovery and release-control architecture

### Repair/closure path

```text
operator command
→ live_contentops.eight_platform_substack_first_pipeline_v1.main()
→ --closure-historical-repair or --closure-release-verify or --finalize-v1-tag
→ live_contentops.final_automation_closure_v1
→ bounded repair / release verification / tag finalizer
```

### Closure modules

- Historical repair orchestrator: `live_contentops/final_automation_closure_v1.py`
- LinkedIn restore, Threads exact delete, Facebook repair all live here.
- Final release verifier and final tag gate also live here.

## 6. Frozen public-repair state

Successful repair surfaces that must not rerun automatically:

- LinkedIn historical restore for activity `7481311616265895936`
- Facebook in-place repair of `106091951705748_1342707111381039`
- Authorized Threads exact deletions for:
  - `17967130901934350`
  - `18368836642225190`
- Recreated valid Threads reply `18366144508233800` remains operator-audit caveated and preserved.

These are frozen both in current docs and in runtime evidence semantics.

## 7. Current video/media system map

### Canonical default rule

Video is **not** part of the default article-distribution lane.
YouTube default remains **Community text/image**, not Shorts or long-form video.

### Video-related modules actually present

- `live_contentops/video_platform_capability_matrix_v1.py`
  - redacted, non-posting capability audit for TikTok and YouTube video lanes
- `live_contentops/source_chart_short_video_v1.py`
  - local FFmpeg chart-sequence renderer
- `live_contentops/edge_cdp_publishing_adapter_v1.py`
  - YouTube Community publish/readback
  - YouTube Shorts browser upload helper
  - TikTok Studio browser upload helper
  - YouTube video metadata edit/readback/public-visibility helpers
- `live_contentops/macro_chart_renderer_v6.py`
  - minimal local macro chart renderer using matplotlib
- `live_contentops/media_manifest_authority_v1.py`
  - exact hash-bound chart/media authority for public text/image distribution

### Evidence proving video-related history exists

- `docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/video_platform_capability_matrix_v1.json`
- `docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/video_manifest_v1.json`
- `docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/video/eight_platform_live_20260710_recovery1_source_charts_short.mp4`
- `docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/reliability_hardening_evidence_v3.json`

## 8. Missing or partial video layers

### Implemented

- Local chart-sequence MP4 creation using FFmpeg
- Non-posting capability classification for TikTok / YouTube long-form / YouTube Shorts
- Explicit/non-default YouTube Shorts upload helper
- Partial TikTok Studio upload helper
- YouTube Community text/image publication/readback fully integrated in canonical runner

### Partial

- YouTube long-form support exists only as request-builder and metadata/visibility maintenance helpers
- TikTok browser upload helper lacks hardened readback/permalink recovery

### Missing

- ffprobe-backed media metadata extraction
- narration/audio generation pipeline
- subtitles/timing/burn-in pipeline
- avatar provider abstraction
- scene graph / claim-to-script schema
- private-first video upload request-builder envelope integrated into a canonical video runner
- machine-readable lane lock for pausing public text/image dispatch while leaving read-only and prepare-only flows available

## 9. Existing tests that govern these systems

### Text/image and freeze guards

- `tests/test_eight_platform_substack_first_pipeline_v1.py`
- `tests/test_edge_cdp_publishing_adapter_v1.py`
- `tests/test_generic_evidence_freshness_visual_editorial_fabric_v2.py`
- `tests/test_media_manifest_authority_v1.py`

### Video/media-specific

- `tests/test_video_platform_capability_matrix_v1.py`
- `tests/test_source_chart_short_video_v1.py`
- `tests/test_media_manifest_authority_v1.py`
- `tests/test_macro_chart_renderer_v6.py`

### Important behavioral guard already present

`tests/test_eight_platform_substack_first_pipeline_v1.py` explicitly verifies that the default article path does **not** call `publish_youtube_short_via_edge` or `build_source_chart_short_video`.

## 10. Architectural consequence for Phase 2

Phase 2, if separately authorized, must preserve these invariants:

1. default article text/image lane remains paused or locked via an explicit machine-readable guard, not via ad hoc flags;
2. prepare-only and read-only reconciliation remain available;
3. video is handled by an explicit canonical video runner, not by implicit extension of the already-large text/image runner;
4. YouTube Community remains the default YouTube text/image derivative surface;
5. Shorts and TikTok remain explicit, separately authorized modes;
6. local rendering should build on existing Python chart/media infrastructure and FFmpeg, unless a later verified dependency decision explicitly changes that.
