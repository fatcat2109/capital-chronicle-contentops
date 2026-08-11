# ContentOps Tier-2-B — Remotion Multimodal Bakeoff Vertical Slice

Task: `TASK_CONTENTOPS_TIER2_B_REMOTION_MULTIMODAL_QA_PROVIDER_BAKEOFF_BOUNDED_REVISION_AND_DIVERSE_CORPUS_V1`

Result: `COMPLETE_TIER2_B_PRODUCT_SLICE_AWAITING_CHATGPT_JIM_VISUAL_AUDIO_REVIEW`

This is provisional product work. Final visual/audio/brand acceptance is Jim/ChatGPT's; no
`CANONICAL_PROVIDER_LOCK_ACCEPTED` is claimed and provider selection stays provisional.

## What was built

- **Remotion compositor promoted to primary Tier-2 prototype compositor** (`video/remotion/`),
  consuming a compiled renderer-target render-job schema. The renderer-neutral `VideoProgram`
  (`live_contentops/tier2_remotion_factory_v1.py`) remains the authority; Remotion/FFmpeg are
  compiler targets only.
- **Professional motion primitives** (`video/remotion/src/scenes/`): title/opening, chapter card,
  chart, document, comparison, timeline, number callout, source card, callout, disclaimer/end card,
  lower source label, caption band, real xfade/acrossfade transitions. Scene primitive materially
  changes composition (no single-card-for-every-scene).
- **9Router Video Director** (bounded, selection-only, no numeric authority) + **independent
  multimodal visual critic** via the canonical 9Router adapter (`call_nine_router_multimodal`),
  producing structured defects; **bounded revision (<=2 rounds)** with a whitelist that never touches
  scripts/claims/numbers/assets; **selective rerender** (scene/chapter cache keyed on semantic scene +
  asset hashes + narration identity + motion/renderer version).
- **Deterministic computed QA** (duration/resolution/aspect/fps/codecs/streams/captions/claim
  coverage/source credits/assembly consistency/hash-manifest integrity) — no hardcoded PASS.
- **Immutable package**: hash manifest + package lock; `verify_package()` re-checks every file.
- **VIDEO_NOT_SELECTED proof**: FOMC-minutes metadata-only candidate resolves
  `VIDEO_NOT_SELECTED` (insufficient evidence strength + visualizability + narrative depth).

## Canonical command

```text
python -m live_contentops.cli tier2-video-remotion \
  --output-root <isolated-runtime-root> --provider enabled
```

## Rendered evidence (outside Git, isolated runtime root)

`A:\Capital Chronicle\Runtime\ContentOps\tier2\tier2b-v1`

- `package/master_16x9.mp4` — **1013.62s (16:53)**, 1280x720 @ 24fps, H.264+AAC (16:9 long-form,
  >=15-minute target met, no filler — grounded in the packet's 65-day curve series).
- `package/short_01_9x16.mp4` — 72.92s, 1080x1920 (native 9:16, independent direction).
- `package/captions/long.{srt,vtt}`, `short.{srt,vtt}` — narration segment-boundary timing.
- `visual_acceptance/long_form_contact_sheet.jpg`, `short_vertical_contact_sheet.jpg` + key frames.
- `bakeoff/bakeoff_manifest.json`, `bakeoff/voice/chatterbox_reference.wav`.
- `REVIEW_README.md` — human review guide + known visual issues.

## Provider bakeoff (provisional)

- **Image generation** (`new/qwen-image-2.0`, `new/wan2.7-image-pro`, `new/gpt-5.5`): the 9router
  `/v1/images/generations` route returns "provider does not support image generation" for all three;
  bare names route to an `openai` image provider with no credentials. No image generated.
  Deterministic Pillow/Remotion art direction remains the visual foundation.
- **Voice**: Kokoro-82M baseline (used in product, local, RTF ~1.9-2.3). Chatterbox (resemble-ai)
  viable on CPU (8.68s sample, ~99s wall, Perth watermarking). ElevenLabs entitlement
  `UNAVAILABLE` — configured env value is an API key ID, not a usable `sk_` API key.
- **Music**: Mixkit direct asset download blocked (HTTP 403, no bypass) →
  `LICENSED_LOCAL_TRACK_BENCHMARK_REQUIRES_MANUAL_ASSET_IMPORT`; ACE-Step deferred (repo-clone +
  multi-GB model, not feasible in session). Product ships narration-only (no music).

## Safety / boundaries

- No public or private upload; no platform/browser/CDP write. `public_or_private_upload: false`.
- No secrets emitted (credentials checked presence-only).
- V1 production runtime/store untouched; protected `v1.0` untouched.
- Deterministic QA long/short PASS; claim binding coverage 1.0.

## Focused tests

`tests/test_tier2_remotion_factory_v1.py` — 12 passing (eligibility/not-selected, program invariants
+ claim coverage, semantic-vs-execution hash separation, scene/chapter cache-key sensitivity,
assembly offset math + caption boundaries, revision whitelist never touches facts,
critic fail-closed + non-factual-scope).

## Next blocker

`CHATGPT_JIM_TIER2_B_VISUAL_AUDIO_PROVIDER_BAKEOFF_AUDIT` — human review of `master_16x9.mp4`,
`short_01_9x16.mp4`, the contact sheets, and the narration/audio; plus resolution of the ElevenLabs
API key (secret `sk_` key vs key ID) and Mixkit manual asset import if music is wanted. Do not
advance to Tier-2-C before that acceptance.
