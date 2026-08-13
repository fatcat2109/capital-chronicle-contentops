# Capital Chronicle ContentOps V2 — Current Execution Pointer V2

Authority date: 2026-08-13
Status: `CURRENT_V2_EXECUTION_POINTER`

## Canonical V2 read order

1. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_NORTH_STAR_V2.md`
2. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_MASTER_PLAN_V2.md`
3. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_TASK_GRAPH_V2.md`
4. `docs/automation/CONTENTOPS_V2_RETENTION_NATIVE_VIDEO_FACTORY_CURRENT_EXECUTION_POINTER_V2.md`
5. `docs/automation/CONTENTOPS_V2_REMOTION_AGENT_SKILL_BASELINE_V1.md`
6. `docs/automation/CONTENTOPS_V2_FRESH_CHAT_HANDOFF_V1.md`
7. `docs/status/CONTENTOPS_V2_GPT56_CREATIVE_CODE_AND_ASSET_DENSITY_OWNER_OVERRIDE_V1.md` for historical rationale/details already folded into V2 docs
8. `video/AGENTS.md`
9. exact task branch/code/tests/evidence

Older `...NORTH_STAR_V1`, `...MASTER_PLAN_V1`, `...TASK_GRAPH_V1`, and `...CURRENT_EXECUTION_POINTER_V1` remain historical/reference once this V2 set is committed. V2 documents control where they conflict.

## Current next task

`TASK_CONTENTOPS_TIER2_V2_GPT56_CREATIVE_CODE_ASSET_RICH_VIDEO_VERTICAL_SLICE_V1`

Required result:

`PASS_RETENTION_NATIVE_VERTICAL_SLICE_VISUAL_AUDIO_ACCEPTED`

Do not advance to V2-02 until Jim/ChatGPT accepts actual MP4/audio.

## Current creative authority

Exact primary 9Router model:

`new/gpt-5.6-sol-xhigh`

Required primary roles:

- `V2_CREATIVE_EDITOR`
- `V2_MOTION_CODE_AUTHOR`
- `V2_CREATIVE_REVISION_AUTHOR`

GPT-5.6 directly authors screenplay/narration/edit decisions and bounded per-shot creative code. Remotion is deterministic renderer/compiler.

Every new creative invocation starts `new/gpt-5.6-sol-xhigh`. HIGH and then MEDIUM are execution fallbacks only after an evidenced blocker; fallback output is `DEGRADED_CREATIVE_MODEL` and cannot self-advance through professional acceptance. Fresh runs use story-specific semantic decomposition and deterministic downstream prompt construction rather than monolithic creative requests or fixed half-splits.

## Current execution state

The 2026-08-13 replacement V2-01 has final isolated `r4` short and midform media with passing deterministic render, audio, retention-contract, rights/provenance, selective-rerender, and safety gates. Under Jim/ChatGPT's one-purpose operator authorization, the canonical independent critic reviewed the exact hash-bound R4 media and returned `REVISE`: two localized `MAJOR` short-form defects and one localized `MINOR` midform issue. Current state is `FAIL_CURRENT_PROOF_MATERIAL_CREATIVE_DEFECTS_REVISION_BUDGET_EXHAUSTED`.

Both authorized creative-revision rounds remain consumed, so do not manually alter the proof or invoke revision #3. The operator pause was restored immediately after the complete critic verdict and must not be cleared again under the spent authorization. Do not claim professional or owner acceptance or advance to V2-02. Evidence is under `docs/automation/TASK_CONTENTOPS_TIER2_V2_GPT56_CREATIVE_CODE_ASSET_RICH_VIDEO_VERTICAL_SLICE_V1/`.

## Current failed reference

`task/tier2-v2-retention-native-video-factory-vertical-slice-v1`

HEAD:

`b6f5002903fba65a668506e4ca38ae61b907ab18`

Classification:

`FAIL_CREATIVE_MOTION_ARCHITECTURE / REJECTED_CREATIVE_PRODUCT_REFERENCE_ONLY`

Do not merge or continue its creative grammar.

## Current provider/asset direction

Preserve working image/asset/voice/audio infrastructure.

- direct image boundary remains separate;
- `gpt-5.5` remains provisional generated-illustration default;
- generated media remains illustrative only;
- real-person documentary media must be real and rights-cleared;
- current voice/TTS abstraction and local/Kokoro baseline remain;
- current music/SFX/mastering infrastructure remains;
- expand rights-safe asset candidate and selected-state richness instead of provider churn.

## Current Remotion technical reference

Official primary baseline:

`remotion-dev/skills@b12104ef5f1b1ca2ca5590fcc7c1804fbc85556f`

Community skills are selective craft references only.

## Current proof scope

- native 45–60s 9:16 short;
- 90–150s 16:9 editorial proof;
- exact sanitized GPT-5.6 creative-author receipts;
- sandboxed per-shot source;
- rich rights-safe candidate assets;
- roughly 12–20 purposeful short visual states and 25–45 proof states when story supply justifies them;
- current narration/music/SFX;
- zero accepted text collisions;
- motion repetition/chart-crawl diagnostics;
- independent multimodal critic;
- maximum two localized creative revision rounds;
- actual Jim/ChatGPT media review.

## Public-write authority

`ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY`

No YouTube/TikTok public or private upload is authorized by the current task.

## Local sync requirement

Remote GitHub is repo-state authority. The local Windows canonical checkout may lag after direct GitHub authority updates.

Before builder implementation:

- inspect local status and preserve unrelated work;
- fetch origin;
- verify fresh `origin/master`;
- create a clean dedicated V2 task worktree/branch from fresh master rather than hard-resetting unrelated local work;
- regenerate/check CodeGraph and require `CODEGRAPH_CURRENT` before implementation commit.
