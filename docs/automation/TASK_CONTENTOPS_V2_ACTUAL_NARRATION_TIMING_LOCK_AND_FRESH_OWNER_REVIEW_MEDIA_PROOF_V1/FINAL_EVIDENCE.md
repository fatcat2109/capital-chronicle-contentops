# V2 actual narration timing lock and fresh owner-review media proof

## Classification

`FAIL_QUARANTINED_AT_HARD_SOURCE_VALIDATION_DEPENDENCY_ROOT_CONFIG`

The implementation and deterministic tests passed, and the one fresh proof successfully created
an immutable actual Kokoro waveform timing lock before motion. Fresh XHIGH motion authored a
56-second picture contract against the 55.442-second locked narration. The proof then quarantined
before typecheck/proxy because HIGH supplied the Remotion project root as `--dependency-root`, while
the existing runtime contract required its `node_modules` directory. The fail-closed resolver found
zero browsers at the resulting project-level `.remotion` path.

No correction, resume, second proof, render, actual-media review, picture lock, final mix, captions,
package, or public write followed. This task does not claim
`PASS_IMPLEMENTATION_ACTUAL_NARRATION_TIMING_LOCK_V2_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW`.

## Repository authority

- Repository: `fatcat2109/capital-chronicle-contentops`
- Branch: `task/v2-actual-narration-timing-lock-fresh-owner-review-media-proof-v1`
- Fresh `origin/master`: `8f6e4422d09fc9794c38ccc036ff1d1d9650034c`
- Starting V2 authority HEAD: `e5ddbdedc1649f15c1eefd3cd7f72891835e29d2`
- Product implementation commit: `a163b0ad488e7d628531ac9f218ec72b79073bfb`
- Product implementation message: `fix(v2): lock actual narration timing before motion`
- Frozen pre-proof implementation HEAD: `76f3cb2b58aa1b6745b411489850fe25d89403a0`
- Frozen pre-proof HEAD message: `docs(codegraph): sync narration timing lock flow`
- Remote parity before proof: exact at `76f3cb2b58aa1b6745b411489850fe25d89403a0`
- Master was not merged, pushed, or mutated.

Pre-proof changed paths:

- `scripts/run_v2_unattended_core_factory_v1.py`
- `tests/test_v2_unattended_core_factory_v1.py`
- `video/unattended_core_factory_v1/creative.py`
- `video/unattended_core_factory_v1/desktop_session.py`
- `video/unattended_core_factory_v1/media.py`
- `video/unattended_core_factory_v1/supervisor.py`
- `docs/codegraph/INDEX.md`
- `docs/codegraph/V2_CONTEXT.md`
- `docs/codegraph/graph.json`
- `docs/automation/TASK_CONTENTOPS_V2_ACTUAL_NARRATION_TIMING_LOCK_AND_FRESH_OWNER_REVIEW_MEDIA_PROOF_V1/CODEGRAPH_DISCOVERY_AND_VERIFICATION.md`

## CodeGraph and validation

Before editing, the stale deterministic context was regenerated and a task-authorized local
CodeGraph index was initialized in the actual worktree. Discovery traced editor validation, late
narration synthesis, motion/picture duration, mix, captions, tests, and the reusable voice-bound
segment cache pattern.

After implementation, CodeGraph was synced and the deterministic graph regenerated. Verification
found exactly one caller each for `synthesize_narration`, `build_audio_mix`, and `build_captions`.
The synthesis call is only inside `ACTUAL_NARRATION_TIMING_LOCKED`; audio build reuses the lock;
captions consume the lock placements; and no canonical runner/supervisor path reaches CLI,
SDK/API/headless, 9Router, or provider creative execution. Full concise evidence is in
`CODEGRAPH_DISCOVERY_AND_VERIFICATION.md`.

Validation before proof:

- focused V2 factory: `21 passed, 1 skipped`;
- shared caption timing/guard plus explicit deterministic owner-ready E2E: `3 passed`;
- Python compile: pass;
- canonical CLI surface: pass;
- Windows-safe Remotion browser resolver unit coverage: pass;
- `CODEGRAPH_CURRENT`: pass;
- `git diff --check`: pass.

## One fresh proof

- `PROOF_RUN_STARTED_AT`: `2026-08-17T14:55:20.8268907Z`
- Quarantined at: `2026-08-17T15:09:43.779858Z`
- Wall time: `862.952967` seconds
- Runtime root: `A:\c2proof_76f3`
- Video job ID: `v2_fwb_narration_lock_76f3cb2b`
- Run ID: `run_dfbcf87ff70347aca26f28e323df3cba`
- Governed input hash: `78d20d15daae43c3ed2d4a8e94a1a7014dc7d7a3b18d288529aeeb364f9755bd`
- State: `QUARANTINED`
- Resume count: `0`
- Public-write authority: `0`

Passed stages:

1. `CLAIMED`
2. `GOVERNED_INPUT_LOCKED`
3. `CREATIVE_EDITOR_LOCKED`
4. `ACTUAL_NARRATION_TIMING_LOCKED`
5. `MOTION_SOURCE_LOCKED`

Terminal event:

`HARD_FAILURE:MediaExecutionError:canonical_remotion_browser_identity_invalid:0:<project>\.remotion\chrome-headless-shell`

Not reached: `HARD_SOURCE_VALIDATED`, proxy, actual-media review, picture lock, audio mix, final mux,
captions, package QA, contact sheet, or `OWNER_REVIEW_READY`.

## Actual narration timing lock

- Timing-lock hash: `7bf38d7140183a8a01615402c8897b7a527ac07accd76dbb5d9a41c3aea6dca7`
- Timing-lock JSON SHA-256: `e485c47b2fbc5c7da7d13352490b28de545034cf638d5105deee78dca96778a3`
- Editorial/narration hash: `7c7ea758eaa2a1ce4b250d2a66b165ce6acbf7eeea25bab61653993a219058f1`
- Locked narration SHA-256: `ccda02c0510fc4ba252c0c76f30811133b4d2bb2f665e5505b1feef22e562a9a`
- Provider/model: local `kokoro-onnx` / `kokoro-v1.0`
- Voice/speed/language: `af_heart / 1.06 / en-us`
- Format: PCM 24-bit little-endian, mono, 24 kHz
- Actual total duration: `55.442000` seconds
- Raw narration measurement: `-22.4 LUFS` integrated / `-4.0 dBFS` true peak
- External media cost: `USD 0.00`

| Segment | Start | Audio | End | Pause after |
|---|---:|---:|---:|---:|
| `payroll.drop` | 0.180 | 6.950 | 7.130 | 0.160 |
| `payroll.revisions` | 7.290 | 6.125 | 13.415 | 0.160 |
| `diagnosis.stasis` | 13.575 | 2.818 | 16.393 | 0.160 |
| `mobility.hires` | 16.553 | 5.249 | 21.802 | 0.160 |
| `mobility.quits` | 21.962 | 4.971 | 26.933 | 0.160 |
| `mobility.risk` | 27.093 | 4.310 | 31.403 | 0.160 |
| `counterforce.claims` | 31.563 | 12.693 | 44.256 | 0.160 |
| `capacity.risk` | 44.416 | 6.462 | 50.878 | 0.160 |
| `watch.condition` | 51.038 | 4.054 | 55.092 | 0.350 |

The fresh motion contract bound to this lock used 1,680 frames at 30 fps, 56.000 seconds total,
0.180 seconds authored head room, and 0.558 seconds intentional tail room. Motion source SHA-256:
`d0f9d0cf62a909ffd27b4f79c811ae64d604411ab8ea4365881e5f6f97a1670d`.

## Bounded XHIGH provenance

Accepted durable XHIGH execution count: `2`.

1. `EDITORIAL_NARRATION`: `/root/fwb_editorial_xhigh`; receipt SHA-256
   `b5f73b7de2a15a61f2e19c87b1a4700b4d522700f831db4a9f09008b851cd15e`.
2. `MOTION_VISUAL_AUTHORSHIP`: `/root/fwb_motion_xhigh`; receipt SHA-256
   `004c00153e11dcd1411ec90d999e7c52d17c946f6f04940838de46666830c30d`.

Both record `gpt-5.6-sol / xhigh`, parent `gpt-5.6-sol / high`, zero mechanical work, zero CLI,
SDK/API, headless, provider, 9Router, fallback, and public-write invocation. Usage/cost was not
exposed and remains null. No XHIGH actual-media review occurred because no proxy exists.

Before accepted submission, the same bounded workers made two contract-only corrections returned by
deterministic validation: empty unbound editorial bindings were normalized from JSON `null` to `""`,
and digit-bearing CSS unit strings were converted to numeric React styles. HIGH/operator changed no
narration, source, timing, facts, layout, or media.

## Render, final media, package, and safety truth

- Real proof render count: `0`
- Rerender count: `0`
- Final MP4: not available
- Picture/final duration: not available
- Final MP4 hash/codecs: not available
- Final mix loudness/true peak: not available
- Captions/package/contact sheet: not available
- Owner media acceptance: not claimed and impossible on this proof
- Operator narration edits: `0`
- Operator viewer-facing source edits: `0`
- Manual media repairs: `0`
- Checkpoint mutations: `0`
- Proof retries/resumes: `0`
- Second proof attempts: `0`
- XHIGH mechanical-work executions: `0`
- V1 reads/writes/mutations: `0`
- Scheduler/Automation mutations: `0`
- Platform/browser/CDP/API/credential operations: `0`
- Public/private/unlisted/draft uploads or writes: `0`
- `ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY`: preserved

## Exact blocker and stop boundary

The proof invocation supplied:

`<frozen_without_breaking_v1 project>`

as the dependency root. `prepare_project` therefore searched the nonexistent project-level
`.remotion/chrome-headless-shell` cache and quarantined with zero matches. A read-only post-failure
diagnostic confirmed that the correct existing dependency root is:

`<frozen_without_breaking_v1 project>\node_modules`

and that its canonical 222-character browser executable exists and resolves uniquely. The proof was
not resumed with that correction because the exact task permits only one proof and requires STOP
after quarantine. A new exact owner task is required for any correction and fresh proof. The
unattended production soak remains unauthorized.
