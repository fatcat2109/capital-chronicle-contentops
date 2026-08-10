# ContentOps Tier-2-A Programmable Video Vertical Slice V1

Task: `TASK_CONTENTOPS_TIER2_A_LOCAL_LONG_FORM_AND_SHORT_FORM_PROGRAMMABLE_VERTICAL_SLICE_V1`

Result: `COMPLETE_LOCAL_PRODUCT_SLICE_AWAITING_CHATGPT_JIM_VISUAL_REVIEW`

## Product Capability

One read-only governed Treasury evidence package now compiles through video eligibility,
renderer-neutral `VideoProgram` / chapter / scene graphs, source-backed assets, local Kokoro
narration, SRT/VTT captions, Pillow/FFmpeg composition, scene/chapter/master caches, ffprobe QA,
native long/short packages, selective rerender, and immutable hash locking.

Canonical local command:

```text
python -m live_contentops.cli tier2-video-local \
  --input-dir <governed ContentOps package> \
  --output-root <isolated Tier-2 runtime root> \
  --tts-python <isolated Kokoro Python>
```

Final local evidence root:

`A:\Capital Chronicle\Runtime\ContentOps\tier2\tier2-a-treasury-curve-final-v2`

Key outputs:

- `master_16x9.mp4`: 600.121 seconds, 1920x1080, H.264/AAC, 30 fps;
- `short_01_9x16.mp4`: 71.634333 seconds, 1080x1920, H.264/AAC, 30 fps;
- five chapters, ten long-form scenes, five independently directed short scenes;
- claim-binding coverage 1.0 and rights coverage 1.0;
- 116 exact files verified by `hash_manifest.json` and `package_lock.json`;
- one controlled SceneGraph change invalidated/rerendered only `chapter-03-a`, rebuilt only
  `chapter-03`, reassembled the master, and left unrelated scene/chapter hashes unchanged.

Representative visual evidence:

- `visual_acceptance/long_form_contact_sheet.png` under the external package;
- five `visual_acceptance/vertical_*.png` frames under the external package.

Machine QA is `PASS`. Final visual acceptance is intentionally
`AWAITING_CHATGPT_JIM_VISUAL_REVIEW`.

## Decisions And Boundaries

- Renderer: existing local Pillow/matplotlib/FFmpeg stack. `VideoProgram` remains renderer-neutral.
- Remotion terms checked 2026-08-10: free for individuals/for-profit teams up to three people;
  otherwise automated use currently has a USD 100/month minimum. It was unnecessary for this
  zero-cash Python-first slice.
- TTS: Kokoro-82M / `af_heart`, Apache-2.0, isolated Python 3.12 environment, local CPU inference.
- TTS benchmark: three finance/news samples, 5.45-7.30 seconds output, 14.873-16.661 seconds wall
  time, realtime factor 2.0373-3.0570, approximately 1.07-1.17 GiB process RAM, zero VRAM.
- Runtime provider/model calls: zero. 9Router calls/tokens: zero.
- Cash cost: none.
- No browser/CDP action, video upload, private upload, platform adapter, or public write occurred.
- The production V1 runtime/store and protected `v1.0` tag were not modified.

Exact next product blocker:

`CHATGPT_JIM_VISUAL_REVIEW_THEN_TIER2_B_MULTIMODAL_QA_BOUNDED_REVISION_AND_DIVERSE_CORPUS`
