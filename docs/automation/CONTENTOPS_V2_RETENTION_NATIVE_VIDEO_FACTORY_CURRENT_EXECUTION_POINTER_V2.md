# Capital Chronicle ContentOps V2 — Current Execution Pointer V2

Authority date: 2026-08-17
Status: `CURRENT_CANONICAL_EXECUTION_POINTER`
Product direction: `FREEFORM_CHAPTERIZED_CREATIVE_AUTHORITY / TRANSCRIPT_FIRST_V2_PRODUCTION`
Reasoning topology: `HIGH_PARENT_SESSION -> BOUNDED_XHIGH_VIDEO_CREATIVE_WORK`
Workflow topology: `GITHUB_AUTHORITY -> CODEGRAPH -> EXACT_SOURCE_TESTS -> IMPLEMENTATION -> CODEGRAPH_VERIFY -> FOCUSED_TESTS_REAL_E2E -> GITHUB_AUDIT`

## Current authority chain

Read in this order:

1. `AGENTS.md`
2. `docs/codegraph/INDEX.md`
3. `docs/codegraph/V2_CONTEXT.md`
4. `docs/automation/CONTENTOPS_CODEGRAPH_MANDATORY_AND_ORCHESTRATION_TOOL_DECISION_V1.md`
5. `docs/automation/CONTENTOPS_V2_HIGH_PARENT_XHIGH_VIDEO_CREATIVE_REASONING_OWNER_CORRECTION_V1.md`
6. `docs/automation/CONTENTOPS_V2_FREEFORM_CHAPTERIZED_HIGH_XHIGH_OWNER_OVERRIDE_V1.md`
7. `docs/automation/CONTENTOPS_V2_NORTH_STAR_MASTER_PLAN_TRANSCRIPT_SEO_MULTILINGUAL_AMENDMENT_V1.md`
8. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_NORTH_STAR_V2.md`
9. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_MASTER_PLAN_V2.md`
10. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_TASK_GRAPH_V2.md`
11. this file
12. nearest scoped `AGENTS.md`
13. exact current task code/tests/evidence.

Repository refs/commits/exact bytes remain repo-state authority. Jim's latest explicit direction remains product authority.

## Tool/process decision

CodeGraph is mandatory for meaningful implementation and audit. It must be used for discovery/impact routing before edits and for affected-flow/orphan/duplicate verification after edits. `CODEGRAPH_CURRENT` by itself is not proof of proper graph use.

Superpowers is not installed/activated for the current project. Three-Level Delivery is not activated. Do not add another process/control plane. Reuse useful debugging/TDD/verification principles directly when they add value.

## Reasoning-effort topology

- Parent/session: `GPT-5.6 Sol / HIGH`.
- Bounded consequential video creative/editorial/review work: `GPT-5.6 Sol / XHIGH`.
- Do not spend XHIGH on Git, CodeGraph, tests, rendering, FFmpeg/transcoding, mechanical diagnostics, waiting/polling, evidence formatting, commit, or push.
- No Codex CLI/`codex exec`, SDK/API/headless, 9Router, Terra/Gemini, provider, or generic-model creative substitution.

## Audited current implementation/proof truth

Branch:

`task/v2-high-parent-xhigh-runtime-short-path-fresh-media-proof-v1`

Implementation HEAD:

`8ed062577b7cb61d4ee8aec69e74822d1946c759`

Evidence HEAD:

`d81ea603d729269d903e72e8a47e9375771ddd88`

Classification:

`FAIL_QUARANTINED_AT_AUDIO_DURATION_GATE`

Verified product progress:

- HIGH parent provenance is implemented;
- exactly two bounded XHIGH creative executions were recorded: initial creative work and actual-media review;
- XHIGH receipts report zero mechanical work and zero CLI/API/headless/provider/9Router fallback;
- Windows Remotion browser launch defect was confirmed: projected 303-character executable path failed while canonical 222-character executable path launched;
- explicit canonical `--browser-executable` and `--public-dir` handling passed a non-creative Remotion smoke;
- the real proof passed `CLAIMED -> GOVERNED_INPUT_LOCKED -> CREATIVE_EDITOR_LOCKED -> MOTION_SOURCE_LOCKED -> HARD_SOURCE_VALIDATED -> PROXY_RENDERED -> ACTUAL_MEDIA_REVIEWED -> PICTURE_LOCKED`;
- actual-media XHIGH review returned `NO_MATERIAL_REVISION`;
- picture lock exists at `1080x1920 / 30fps / h264 / 54.058667s`;
- Kokoro `af_heart / speed=1.06 / en-us` narration exists at `57.788667s`;
- deterministic audio fit correctly rejected the 3.730-second overrun;
- no retry, second proof, operator creative edit, manual media repair, V1/platform/scheduler/public write occurred;
- no final mux, captions, package, or `OWNER_REVIEW_READY` bundle exists.

Production soak remains blocked.

## CodeGraph audit caveat

The evidence packet labels CodeGraph current, but the committed `docs/codegraph/V2_CONTEXT.md` at evidence HEAD states it was generated from source HEAD `558acbdf766754f9ad2902c67c181bb4a7e14cac`, predating implementation HEAD `8ed062577b7cb61d4ee8aec69e74822d1946c759`.

Therefore the next task must regenerate CodeGraph in the actual writable worktree and actively query the audio timing call path before edits.

## Current root cause / product design conclusion

The audio gate itself is correct and must not be weakened.

Current sequencing is the blocker:

`editor word-count duration estimate -> motion/picture duration lock -> actual Kokoro synthesis -> audio duration gate`

`validate_editor_artifact()` only performs a coarse word-count duration lower-bound estimate. Actual Kokoro waveform timing is not known until `AUDIO_BUILT`, after proxy review and `PICTURE_LOCKED`. This allows a truthful script/picture contract to pass while the real waveform exceeds the locked picture.

Do not fix this by truncating narration, globally speeding Kokoro above the owner voice setting, silently stretching picture, relaxing the audio gate, or adding arbitrary duration padding.

The next capability should make actual narration timing a first-class pre-motion timing authority.

## Exact next task

`TASK_CONTENTOPS_V2_ACTUAL_NARRATION_TIMING_LOCK_AND_FRESH_OWNER_REVIEW_MEDIA_PROOF_V1`

Required capability sequence:

`HIGH claim/governed input -> bounded XHIGH editorial/narration artifact -> HIGH Kokoro segment synthesis -> ACTUAL_NARRATION_TIMING_LOCKED -> bounded XHIGH motion/visual authorship using exact segment/audio timing -> deterministic validation -> proxy -> bounded XHIGH actual-media review/revision if needed -> picture lock -> HIGH audio mix/captions/final/package -> OWNER_REVIEW_READY`

The implementation may choose the smallest compatible contract, but actual measured narration timing must be available before canonical motion/picture timing is finalized.

Prefer segment-level audio/timing artifacts and bounded resynthesis of changed lines. Do not introduce a generic timing framework unrelated to the real pipeline.

## Build/media contract

- 1080p only.
- Fresh proof: one `1080x1920 / 30fps / normally 30–60s` Short.
- Kokoro `af_heart / 1.06 / en-us` remains fixed for current build proof.
- No 4K, longform, ElevenLabs, avatar, multilingual activation, V1 trigger/scheduler, platform credential/API/public write.
- Do not resume or mutate the quarantined prior proof.

## Next gate after success

Only after the fresh proof reaches `OWNER_REVIEW_READY` and Jim/ChatGPT independently inspect and accept the actual MP4/audio:

`TASK_CONTENTOPS_V2_UNATTENDED_PRODUCTION_SOAK_WITH_TRANSCRIPT_VOICEOVER_SEO_HARDENING_V1`
