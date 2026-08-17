# V2 HIGH-parent / bounded-XHIGH runtime correction, short-path repair, and fresh media proof

## Classification

`FAIL_QUARANTINED_AT_AUDIO_DURATION_GATE`

The runtime/provenance correction and Windows-safe Remotion repair passed. The one authorized fresh proof reached a real 1080x1920 picture lock and real Kokoro narration, then correctly quarantined because the 57.788667-second narration exceeded the 54.058667-second picture. No retry, source edit, narration edit, manual media repair, checkpoint mutation, second proof, or public write followed.

This task does **not** claim `PASS_IMPLEMENTATION_HIGH_PARENT_XHIGH_CREATIVE_V2_CORE_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW`, because no final muxed MP4, caption/package set, or `OWNER_REVIEW_READY` bundle exists.

## Repository and Git authority

- Repository: `fatcat2109/capital-chronicle-contentops`
- Canonical repository inspected: `A:\Capital Chronicle\ContentOps`
- Dedicated worktree: `A:\ccv2r`
- Branch: `task/v2-high-parent-xhigh-runtime-short-path-fresh-media-proof-v1`
- Freshly fetched `origin/master`: `8f6e4422d09fc9794c38ccc036ff1d1d9650034c`
- Verified starting V2 authority branch: `origin/task/v2-high-parent-xhigh-video-creative-authority-correction-v1`
- Starting V2 authority HEAD: `558acbdf766754f9ad2902c67c181bb4a7e14cac`
- Implementation HEAD: `8ed062577b7cb61d4ee8aec69e74822d1946c759`
- Implementation message: `fix(v2): align HIGH parent and bound Windows render paths`
- Implementation remote parity: exact `git ls-remote` parity at `8ed062577b7cb61d4ee8aec69e74822d1946c759` before proof start
- Evidence message: `docs(v2): record quarantined fresh media proof`
- Master was not merged, pushed, or mutated.

Implementation paths:

- `docs/codegraph/INDEX.md`
- `docs/codegraph/V2_CONTEXT.md`
- `docs/codegraph/graph.json`
- `scripts/run_v2_remotion_short_path_smoke_v1.py`
- `scripts/run_v2_unattended_core_factory_v1.py`
- `tests/test_v2_unattended_core_factory_v1.py`
- `video/unattended_core_factory_v1/__init__.py`
- `video/unattended_core_factory_v1/desktop_session.py`
- `video/unattended_core_factory_v1/media.py`
- `video/unattended_core_factory_v1/supervisor.py`

## Reasoning-effort topology evidence

The active runtime now distinguishes two non-interchangeable planes:

- Parent: `CODEX_DESKTOP_APP_PARENT_TASK_SESSION` / `CODEX_DESKTOP_APP_TASK_SESSION` / `gpt-5.6-sol` / `high`.
- Bounded video creative: `CODEX_DESKTOP_APP_BOUNDED_VIDEO_CREATIVE_REASONING` / `CODEX_DESKTOP_APP_BOUNDED_REASONING` / `gpt-5.6-sol` / `xhigh`.

The immutable parent receipt records `all_session_xhigh=false`, `bounded_xhigh_video_creative_required=true`, `parent_task_session_id_exposed=false`, and `session_database_inspected=false`. Each bounded creative receipt hash-locks the parent continuity key and same-video continuity key, records exact authorized creative scope, and records zero CLI, SDK/API, headless, provider, 9Router, fallback, public-write, and mechanical-work use. No opaque native parent ID or unexposed usage/cost was invented.

Fresh proof parent receipt:

- Path: `A:\c2proof_8ed0\jobs\v2_fwb_high_parent_xhigh_8ed06257\artifacts\parent_high_session_receipt.json`
- SHA-256: `0c150a91ae54535952e339abac5969e8a34fcdf273fe7f71eae4c2ab3ba3807a`
- Parent label: `TASK_CONTENTOPS_V2_HIGH_PARENT_XHIGH_RUNTIME_SHORT_PATH_FRESH_MEDIA_PROOF_V1_HIGH_PARENT`

Bounded XHIGH execution count: **2**.

1. Initial creative authorship: native child task ID exposed as `/root/fwb_initial_xhigh`; authored the institutional analytical map, narrative/narration, asset-to-purpose choices, and fresh viewer-facing Remotion source. Receipt SHA-256 `53609aef35526320487437196c5bd8ebbe186cd582729217d6f515ec6908d915`.
2. Actual-media creative review: native child task ID exposed as `/root/fwb_actual_media_xhigh`; reviewed the rendered proxy/contact sheet and returned `NO_MATERIAL_REVISION`, with two non-blocking minor observations. Receipt SHA-256 `e52bd2fda2a85c2fbb6efce8534d3f05ffd771635e91b4ec4545d804d24e6365`.

Both receipts record `mechanical_work_performed=false`, an empty `mechanical_work_categories` list, and null usage/cost because the Desktop task did not expose those values. XHIGH did not perform Git, repository repair, rendering, FFmpeg/transcoding, tests, waiting, polling, evidence formatting, commit, or push.

## Browser-launch diagnosis and minimal repair

The prior task-local projected Chrome-for-Testing executable path was 303 characters. The file existed, but direct Windows launch failed with `ApplicationFailedException` / unknown error `0xfffffffe`. The same browser binary at its canonical dependency-root path was 222 characters and executed `--version` successfully as `Google Chrome for Testing 149.0.7790.0`. This confirmed a Windows process-launch path defect rather than a missing browser.

The minimal repair:

- resolves and fail-closes around one canonical Remotion browser executable;
- passes its 222-character path explicitly through `--browser-executable`;
- rejects missing, ambiguous, escaping, or over-259-character Windows executable paths;
- passes the governed canonical asset root through `--public-dir`, avoiding the independently observed Windows `EPERM` directory-junction failure;
- does not add a renderer, replace Remotion, redesign storage, weaken the source sandbox, or change durable checkpoint/quarantine behavior.

## Non-creative render smoke

- Result: `PASS_NON_CREATIVE_REMOTION_BROWSER_SMOKE`
- Runtime: `A:\c2smk_558b`
- Creative proof consumed: `false`
- Creative reasoning used: `false`
- Parent reasoning effort: `high`
- Explicit browser path length: 222
- Explicit canonical public root: enabled
- Output: `A:\c2smk_558b\remotion_browser_smoke.mp4`
- Output SHA-256: `0ac34207af9ff2179ef369636672f275416c57ab9419076bf71da085058337ff`
- Probe: 320x568, 30 fps, H.264/AAC, 1.045333 seconds
- Render wall time: 12.9845 seconds
- Receipt: `A:\c2smk_558b\remotion_browser_smoke_receipt.json`

An earlier non-creative smoke attempt exposed the adjacent public-directory junction `EPERM` defect. It created no creative artifact and consumed no proof. The canonical `--public-dir` correction then produced the passing smoke above.

## Pre-proof validation

- Focused affected core and zero-sidecar tests: `22 passed`.
- Relevant deterministic fake/Desktop-session E2E: `1 passed`, reaching `OWNER_REVIEW_READY`.
- Python compile: passed.
- Active CLI/SDK/API/headless/9Router/provider/generic creative substitution scan: zero executable matches.
- Atomic claim, unique active-run enforcement, immutable ledger, input hashes/checkpoints, recovery/quarantine, Kokoro route, and zero-write semantics: covered by focused tests.
- `git diff --check`: passed.
- CodeGraph: the worktree had no root `.codegraph/`, so `codegraph explore` truthfully reported that indexing was not initialized and no index was created. The committed deterministic graph/context was regenerated and its currentness check returned `CODEGRAPH_CURRENT`.
- One unrelated broad freeform test invocation (not relied upon for acceptance) returned `34 passed, 1 failed` because the clean authority worktree lacks the historical documentary fixture `video/projects/frozen_without_breaking_v1/public/assets/documentary/grocery_cashier_pexels_4121754.mp4`. This was not changed.

## One fresh actual-media proof

- `PROOF_RUN_STARTED_AT`: `2026-08-17T13:32:54.9705764Z`
- Runtime root: `A:\c2proof_8ed0`
- Story: `Frozen Without Breaking`
- Format: one Short, 1080x1920, 30 fps
- Video job ID: `v2_fwb_high_parent_xhigh_8ed06257`
- Run ID: `run_1286d389e8fc4e7b8f645c6bf69b43bf`
- Input packet SHA-256: `78d20d15daae43c3ed2d4a8e94a1a7014dc7d7a3b18d288529aeeb364f9755bd`
- Terminal state: `QUARANTINED`
- Terminal result: `HARD_FAILURE:MediaExecutionError:narration_exceeds_picture:57.789>54.059`
- Total proof wall time to durable quarantine: 1786.714929 seconds
- Resume count: 0
- Public-write authority: 0

Durable stage progression:

1. `CLAIMED` — pass
2. `GOVERNED_INPUT_LOCKED` — pass
3. `CREATIVE_EDITOR_LOCKED` — pass
4. `MOTION_SOURCE_LOCKED` — pass
5. `HARD_SOURCE_VALIDATED` — pass
6. `PROXY_RENDERED` — pass
7. `ACTUAL_MEDIA_REVIEWED` — pass, `NO_MATERIAL_REVISION`
8. `PICTURE_LOCKED` — pass
9. `HARD_FAILURE` — `FAIL_QUARANTINED`

Not reached: `AUDIO_BUILT`, final mux, captions, package manifest, final QA, owner bundle, or `OWNER_REVIEW_READY`.

## Actual media and audio identities

Proxy:

- Path: `A:\c2proof_8ed0\jobs\v2_fwb_high_parent_xhigh_8ed06257\media\proxy.mp4`
- SHA-256: `c07b3c995d7d7f99015eeefb41a87f5a66ddf0e075c3fe47a3a68ead728e32a0`
- Contact sheet: `A:\c2proof_8ed0\jobs\v2_fwb_high_parent_xhigh_8ed06257\review\proxy_contact_sheet.jpg`
- Contact-sheet SHA-256: `b235b9d856f587fc710afcbc1a7354e467ecb648e44d41bc7763e8f45c298cba`

Picture lock:

- Path: `A:\c2proof_8ed0\jobs\v2_fwb_high_parent_xhigh_8ed06257\media\picture_lock.mp4`
- SHA-256: `5633cefa7aebbb3b62820be8a0b2c411a11a6610b1a56cc90c8eacc8898925d2`
- Probe: 1080x1920, 30 fps, H.264 video, 54.058667 seconds

Generated narration:

- Path: `A:\c2proof_8ed0\jobs\v2_fwb_high_parent_xhigh_8ed06257\audio\narration\narration.wav`
- SHA-256: `3a6f6a937b3b3f3c4fe8278409278edc77a9a98a8fbb9a730cc134482a0a71fc`
- Probe: PCM 24-bit little-endian, mono, 24 kHz, 57.788667 seconds
- Provider/model: local `kokoro-onnx` / `kokoro-v1.0`
- Voice/speed/language: `af_heart` / `1.06` / `en-us`
- External media cost: USD 0.00

No final muxed MP4 exists. Consequently there is no truthful final SHA-256, loudness/true-peak result, caption artifact, package manifest, final factual/rights report, cost/runtime bundle, or zero-write owner receipt. The immutable stage ledger and every recorded job/event retain `public_write_authority=0`.

Render count for the real proof: 2 (proxy plus picture lock). Creative rerender count: 0. The passing non-creative smoke is separate and did not consume the proof.

## Manual intervention, safety, and cost truth

- Operator viewer-facing source edits after proof start: 0
- Operator narration edits after proof start: 0
- Manual media repairs: 0
- Manual checkpoint mutations: 0
- Proof retries/resumes: 0
- Second proof attempts: 0
- XHIGH mechanical-work executions: 0
- Public/platform/browser/CDP operations: 0
- Credential/session/auth reads: 0
- V1 runtime/store/publication mutations: 0
- Scheduler/Automation mutations: 0
- Multilingual/localization work: 0
- Codex Desktop usage/cost: not exposed; recorded as null, not invented
- External media cost incurred by the local Kokoro route: USD 0.00

## Exact remaining blocker and next gate

The sole terminal blocker is deterministic audio-picture fit: at the authorized Kokoro route, the fresh narration is 3.730 seconds longer than the 54.058667-second picture. The active implementation correctly refuses clipping or implicit time compression.

Any correction requires a new owner-authorized task/proof because this task's one-proof rule forbids patching or retrying after `PROOF_RUN_STARTED_AT`. The production-soak task is not authorized: the proof did not reach `OWNER_REVIEW_READY`, and Jim/ChatGPT have no final muxed media to accept.
