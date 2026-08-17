# Dependency-root preflight and fresh media proof — final evidence

## Classification

`PASS_IMPLEMENTATION_DEPENDENCY_ROOT_PREFLIGHT_V2 / FAIL_FRESH_PROOF_QUARANTINED_BEFORE_PACKAGE_QA / BLOCKED_OWNER_REVIEW_READY`

The dependency-root implementation and every required pre-proof validation passed. The one authorized fresh proof produced a valid picture lock, locked-audio mix, and final 1080x1920 MP4, but the run then quarantined during package QA because the secret scanner traversed projected `node_modules` and flagged a third-party Zod test file. `OWNER_REVIEW_READY` was not reached, so `PASS_IMPLEMENTATION_DEPENDENCY_ROOT_PREFLIGHT_V2_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW` is forbidden. Jim/ChatGPT acceptance is not claimed.

## Git and authority

- Repository: `fatcat2109/capital-chronicle-contentops`
- Branch: `task/v2-dependency-root-preflight-fresh-owner-review-media-proof-v1`
- Freshly fetched `origin/master`: `8f6e4422d09fc9794c38ccc036ff1d1d9650034c`
- Starting owner-authority HEAD: `84017001dbc9fd5ec81908ab771711834d9b7ab7`
- Implementation HEAD: `289abf6c0d329a3c7ab37880bf08c96dc092f3dc`
- Implementation message: `fix(v2): fail fast on invalid Remotion dependency root`
- Frozen pre-proof/CodeGraph HEAD: `fbcb480ee8cbf31aeb21d348eb6d7d63e0d5dd0f`
- Pre-proof remote parity: exact
- Master merge/push/mutation: none

Implementation changed only the focused runner, media/supervisor seam, smoke, tests, context generator/tests, and persisted CodeGraph evidence. The untracked local `.codegraph/` working index was not staged.

## Dependency-root result

The canonical factory now validates the exact `node_modules` root before claim. It proves the Remotion and TypeScript CLIs, one canonical browser identity, root containment, Windows path safety, and projection suitability. A mistakenly supplied project root fails with an actionable `use_node_modules` error.

Pre-proof evidence:

- project root rejected before claim/proof epoch/XHIGH: pass;
- correct `node_modules`: pass;
- Remotion and TypeScript CLI resolution: pass;
- unique canonical browser: pass;
- canonical browser executable path: 222 characters, within the accepted 259-character bound;
- non-creative Remotion smoke: pass, SHA-256 `0ac34207af9ff2179ef369636672f275416c57ab9419076bf71da085058337ff`;
- affected factory/caption tests: `26 passed, 1 skipped`;
- context generator tests: `12 passed`;
- Python compile, `git diff --check`, and `CODEGRAPH_CURRENT`: pass.

The CodeGraph before/after routing evidence is in `CODEGRAPH_DISCOVERY_AND_VERIFICATION.md`. It confirms the canonical runner reaches the singular preflight before claim, no alternate proof runner bypass, unchanged narration-timing architecture, active Windows browser repair, and inactive forbidden creative substitutions.

## Sole fresh proof

- `PROOF_RUN_STARTED_AT`: `2026-08-17T16:02:22.3814039Z`
- Runtime: `A:\c2proof_fbcb`
- Job: `v2_fwb_dependency_preflight_fbcb480e`
- Run: `run_407fd03b00f345df83d477e7bee0d2d4`
- Governed packet SHA-256: `78d20d15daae43c3ed2d4a8e94a1a7014dc7d7a3b18d288529aeeb364f9755bd`
- Terminal state: `QUARANTINED`
- Resume/retry/second-proof count: `0 / 0 / 0`
- Terminal result: `HARD_FAILURE:SupervisorError:secret_scan_failed:A:\c2proof_fbcb\jobs\v2_fwb_dependency_preflight_fbcb480e\generated_project\node_modules\zod\src\v4\mini\tests\string.test.ts`

Passed stages:

1. `CLAIMED`
2. `GOVERNED_INPUT_LOCKED`
3. `CREATIVE_EDITOR_LOCKED`
4. `ACTUAL_NARRATION_TIMING_LOCKED`
5. `MOTION_SOURCE_LOCKED`
6. `HARD_SOURCE_VALIDATED`
7. `PROXY_RENDERED`
8. `ACTUAL_MEDIA_REVIEWED`
9. `PICTURE_LOCKED`
10. `AUDIO_BUILT`
11. `FINAL_MEDIA_BUILT`
12. `HARD_FAILURE / FAIL_QUARANTINED`

Not reached: `PACKAGE_QA_PASSED`, `OWNER_REVIEW_READY`.

Consequently there is no accepted caption sidecar, platform-neutral package manifest, final contact sheet, persisted stage-ledger summary artifact, or owner-review bundle.

## Creative and timing evidence

- HIGH parent: `gpt-5.6-sol / high`
- Bounded XHIGH executions: 4 across 3 fresh child tasks
  - fresh editorial/narration authorship;
  - one same-video editorial timing revision;
  - fresh waveform-locked motion authorship;
  - fresh actual-media review.
- XHIGH mechanical-work executions: 0
- Provider/9Router/CLI/SDK/headless creative fallback: 0
- Actual-media decision: `NO_MATERIAL_REVISION`
- Prior creative source reused: false
- Render/rerender/creative-rerender count: `2 / 0 / 0`

Kokoro timing lock:

- hash: `17a887cf67e1857bd38ce6b43090c5c3b83d3e12b3f3fbab754616b1c2c6b69a`
- route: local `kokoro-onnx / kokoro-v1.0`
- voice/speed/language: `af_heart / 1.06 / en-us`
- locked narration duration: `54.567333s`
- locked narration SHA-256: `03f4db377f13ad4cfe5902b458300a7dc240e511b18a760d9adca8b21af747c6`
- external media cost: USD `0.00`

## Quarantined media identities

These artifacts passed their individual deterministic media/factual/rights checks before the later package-QA quarantine. They are diagnostic proof artifacts, not an accepted owner-review bundle.

- Picture lock: 1080x1920, 30 fps, `55.333333s`, SHA-256 `ebbe42747394589e2fcf012e0e40f0d1dcb273ff5b289c4b55d22fbc1c4ea2cb`
- Final MP4: H.264/AAC, 1080x1920, 30 fps, `55.333333s`, 20,868,147 bytes
- Final MP4 SHA-256: `030668862a34c37f411c0de05f463070e132b50436f08fd775d59467e599e639`
- Integrated loudness: `-16.1 LUFS`
- True peak: `-1.5 dBFS`
- Final mix: PCM 24-bit stereo/48 kHz, `55.362667s`, SHA-256 `3ddd83151d8519533de75ea856dbb7291500506b960530386e5af7addcc568ee`
- Proxy SHA-256: `05f1b498bec10972c3c0fb1e424fd15f01ee392992ddeaa43bedd68983f6b17d`
- Proxy contact-sheet SHA-256: `748defb86ad5700ad920518d302d5a46d37a5a3470cc701feab07fec649d8403`

## Manual intervention and safety truth

- Operator narration edits after proof start: 0
- Operator viewer-facing source edits after proof start: 0
- Manual media repairs: 0
- Manual checkpoint mutations: 0
- Proof retries/resumes: 0
- One non-mutating CLI flag correction occurred before motion submission; the rejected invocation wrote no checkpoint and did not alter creative content.
- Public/private/unlisted/platform writes: 0
- Platform API/browser/CDP actions: 0
- Credential/session/auth reads: 0
- V1 reads/writes/mutations: 0
- Scheduler/Automation mutations: 0
- Public-write authority: 0 throughout every durable event

## Exact blocker and next gate

Package QA secret scanning currently enters the projected dependency tree and treats a third-party Zod test file as a secret violation. The sole proof is durably quarantined. This task forbids repairing or rerunning after `PROOF_RUN_STARTED_AT`, so no code patch or second proof was attempted.

A new exact owner-authorized repair-and-proof task is required. The unattended production-soak task is not authorized because `OWNER_REVIEW_READY` was not reached and Jim/ChatGPT have not accepted an owner-review bundle.
