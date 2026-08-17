# ContentOps V2 — Dependency-Root Preflight Owner Audit V1

Authority date: 2026-08-17
Status: `CURRENT_OWNER_AUDIT`
Owner/auditor: Jim + ChatGPT

Audited task:

`TASK_CONTENTOPS_V2_ACTUAL_NARRATION_TIMING_LOCK_AND_FRESH_OWNER_REVIEW_MEDIA_PROOF_V1`

Evidence HEAD:

`baa918e10dbca71035a286a05aefca89903784b9`

## Classification

Task terminal classification remains:

`FAIL_QUARANTINED_AT_HARD_SOURCE_VALIDATION_DEPENDENCY_ROOT_CONFIG`

Independent audit:

- narration-timing-lock architecture: `PASS`;
- HIGH parent / bounded-XHIGH separation: `PASS`;
- CodeGraph discovery and post-implementation graph verification: `PASS_WITH_CAVEAT`;
- proof configuration/preflight discipline: `FAIL`;
- actual media: `NOT PRODUCED`;
- owner media acceptance: `NOT AVAILABLE`;
- production soak: `BLOCKED`.

## What was proven

The implementation commit `a163b0ad488e7d628531ac9f218ec72b79073bfb` successfully moves actual Kokoro waveform timing before canonical motion timing.

The one fresh proof reached:

`CLAIMED -> GOVERNED_INPUT_LOCKED -> CREATIVE_EDITOR_LOCKED -> ACTUAL_NARRATION_TIMING_LOCKED -> MOTION_SOURCE_LOCKED`

The immutable narration timing lock was created successfully:

- lock hash: `7bf38d7140183a8a01615402c8897b7a527ac07accd76dbb5d9a41c3aea6dca7`;
- Kokoro: `af_heart / speed=1.06 / en-us`;
- actual narration duration: `55.442s`;
- fresh motion contract: `56.000s / 1680 frames / 30fps`;
- two bounded XHIGH executions were accepted: `EDITORIAL_NARRATION` and `MOTION_VISUAL_AUTHORSHIP`;
- XHIGH mechanical-work count remained zero.

This directly proves that the prior audio-duration architecture blocker was corrected: actual waveform duration now exists before motion/picture timing.

## CodeGraph audit

This task materially improved compliance with the owner CodeGraph doctrine.

The writable worktree initialized and queried a real CodeGraph index before edits, traced the active timing/audio/caption path, found the reusable localized-audio segment cache pattern, then resynced after implementation and verified the active callers and absence of timing bypasses. Persisted evidence is in the task `CODEGRAPH_DISCOVERY_AND_VERIFICATION.md`.

Caveat: the deterministic `docs/codegraph/V2_CONTEXT.md` at frozen pre-proof HEAD correctly records source HEAD `a163b0ad...`, but its descriptive prose still contains older V2 routing/task wording. That prose is descriptive and superseded by current owner authority; the local structural graph queries remain the accepted impact-analysis evidence. A future bounded edit may clean the generator wording, but it is not the current product blocker.

## Exact failure diagnosis

The proof supplied the Remotion project root as `--dependency-root`.

The canonical runtime contract actually requires the project `node_modules` directory.

As a result, `resolve_remotion_browser_executable()` searched:

`<project>/.remotion/chrome-headless-shell`

instead of:

`<project>/node_modules/.remotion/chrome-headless-shell`

and correctly failed closed with zero browser matches before typecheck/render.

A read-only post-failure diagnostic confirmed the correct existing `node_modules` root and the previously proven canonical 222-character browser executable.

## Root-cause classification

This is both:

1. an operator/proof invocation error; and
2. a real preflight-validation gap in the canonical runner.

The canonical runner exposes `--dependency-root` without enforcing its semantic contract. `FactoryConfig.validate()` currently verifies only that the configured path exists. Therefore a wrong-but-existing project directory survives construction and consumes proof/creative work before failing at hard source validation.

The correct reliability fix is not a renderer change and not another architecture phase. Add the smallest fail-fast pre-proof dependency-root contract so an invalid root is rejected before job claim/proof epoch/creative expenditure.

## Required next behavior

The canonical HIGH runner must validate the dependency root before proof consumption. The accepted root must prove at minimum that the required Remotion CLI/dependency surface and the unique canonical browser identity resolve from that exact root.

Prefer explicit fail-fast validation with an actionable error over silently guessing from arbitrary directories. Preserve current Windows-safe canonical browser handling.

A wrong project root must fail before `PROOF_RUN_STARTED_AT` and before any bounded XHIGH creative execution.

## Exact next task

`TASK_CONTENTOPS_V2_DEPENDENCY_ROOT_PREFLIGHT_GUARD_AND_FRESH_OWNER_REVIEW_MEDIA_PROOF_V1`

Use a **fresh Codex Desktop App parent/task session at `GPT-5.6 Sol / HIGH`**.

This is a new implementation task and new proof/job. Do not reuse the quarantined task/session as execution authority and do not resume `run_dfbcf87ff70347aca26f28e323df3cba`.

Task scope is intentionally narrow:

1. use CodeGraph in the writable worktree to trace canonical runner/config/media dependency-root flow and affected tests;
2. add the smallest pre-proof semantic validation for the dependency root;
3. prove both invalid project-root rejection and valid `node_modules` acceptance without consuming a creative proof;
4. preserve the accepted narration timing-lock architecture unchanged except where the guard must connect;
5. commit/push before proof;
6. run exactly one fresh end-to-end Frozen Without Breaking Short proof;
7. if `OWNER_REVIEW_READY` is reached, provide actual MP4/audio to Jim/ChatGPT for independent media acceptance.

Do not open a generic configuration framework, asset program, multilingual activation, publication integration, scheduler work, premium voice/avatar work, or V1 mutation.

## Media/creative carry-forward

The previous actual-media owner audit remains controlling for the fresh proof:

- avoid blind reuse of the same station/office/desk/warehouse visual families;
- avoid using split/vertical-rail layout grammar as the default scene solution;
- prefer concrete/documentary/native-data carriers before abstract geometry;
- keep charts/data evidence stable and readable rather than adding ornamental zoom/pan;
- bounded XHIGH actual-media review must explicitly inspect visual-family and layout repetition.

These are creative judgment, not deterministic aesthetic quotas.

## Safety

`ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY`

No current task may perform platform publication/upload, platform credential reads, V1 operational mutation, scheduler mutation, multilingual activation, 4K/longform expansion, or production soak.

Production soak remains blocked until a fresh proof reaches `OWNER_REVIEW_READY` and Jim/ChatGPT accept the actual final media.
