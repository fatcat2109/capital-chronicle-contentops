# Owned-surface secret scan boundary and fresh owner-ready proof — final evidence

## Classification

`PASS_IMPLEMENTATION_OWNED_SURFACE_SECRET_SCAN_V2_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW`

The canonical V2 factory now scans only explicit Capital Chronicle-owned text surfaces, preserves
the existing secret patterns and fail-closed behavior, and cannot follow a junction or symlink out
of the job root. Exactly one fresh Frozen Without Breaking Short proof passed both final secret-scan
gates, `PACKAGE_QA_PASSED`, and `OWNER_REVIEW_READY`.

This is the maximum builder classification authorized by the task. Jim/ChatGPT acceptance is not
claimed. No soak task, publication action, or next gate was started.

## Git and authority

- Repository: `fatcat2109/capital-chronicle-contentops`
- Branch: `task/v2-owned-surface-secret-scan-fresh-owner-ready-proof-v1`
- Freshly fetched `origin/master`: `8f6e4422d09fc9794c38ccc036ff1d1d9650034c`
- Starting owner-authority HEAD: `72bbc2dcdf11321cdcbf79cd5d546e8ed64e0b0e`
- Implementation HEAD: `52c92ec1e097ef2441a2cb916132576c241b5def`
- Frozen pre-proof/CodeGraph HEAD: `c34782e6297e7e8efeefe529ce20d641cd61d4e5`
- Pre-proof remote parity: exact
- Implementation changes after `PROOF_RUN_STARTED_AT`: none
- Master merge/push/mutation: none

The focused implementation changed the canonical supervisor, its existing V2 factory tests, the
persisted CodeGraph context, and task-scoped CodeGraph evidence. The local `.codegraph/` working
index remained untracked and was not staged.

## Corrected trust boundary

The singular canonical scanner now receives the complete job path contract and scans exactly these
owned text roots:

1. `artifacts/`
2. `desktop_session_inbox/`
3. `generated_project/src/`
4. `package/`, including captions
5. `review/`, including technical, factual, rights, cost, safety, ledger, and owner-bundle text

Owned suffixes remain `.json`, `.md`, `.txt`, `.tsx`, `.ts`, `.srt`, and `.vtt`. The four secret
patterns are unchanged. Every owned root and file is resolved and checked for containment inside
the job root before reading. A missing or unreadable owned surface, or any symlink/junction in an
owned traversal, fails closed and reports only a job-relative path.

Projected `generated_project/node_modules`, external dependency/vendor trees, Remotion/browser
caches, media, audio, and other binary outputs are outside this text-scanner boundary. Their
existing dependency identity, hash, rights, and media-QA controls remain unchanged. No filename
exception, dependency allowlist, pattern relaxation, parallel scanner, or bypass was added.

Security regressions prove:

- the original pattern strings are byte-for-byte unchanged;
- a synthetic secret hard-fails on each of the five owned surfaces;
- the prior Zod-shaped `node_modules` vendor fixture is not scanned;
- an external junction/symlink under an owned root fails before target content is read or reported;
- `PACKAGE_QA_PASSED` and `OWNER_REVIEW_READY` invoke the same complete scanner contract.

## CodeGraph and pre-proof validation

Before implementation, CodeGraph indexed 2,037 files, 48,103 nodes, and 124,097 edges. It located
one production caller of `_secret_scan()`, with active calls at both final gates, and confirmed that
the former whole-job `rglob()` could reach the projected dependency tree.

After implementation, the synchronized graph contained 2,037 files, 48,118 nodes, and 124,158
edges. It confirmed one canonical scanner and one production caller, no whole-job `rglob()`, no
alternate scanner or bypass, and unchanged dependency-root, narration-timing, creative provenance,
and zero-write paths. Generated context validation returned `CODEGRAPH_CURRENT`.

Mechanical validation before the real proof:

- full V2 factory suite: `33 passed, 1 skipped`;
- deterministic context-generator suite: `12 passed`;
- Python compile: pass;
- `git diff --check`: pass;
- generated CodeGraph check: `CODEGRAPH_CURRENT`.

Detailed graph routing evidence is in `CODEGRAPH_DISCOVERY_AND_VERIFICATION.md`.

## Sole fresh proof

- `PROOF_RUN_STARTED_AT`: `2026-08-17T17:04:38.1107904Z`
- Runtime root: `A:\c2scan_c347`
- Job: `v2_fwb_owned_scan_c34782e6`
- Run: `run_b8682fdad0934ba39475f442a6e8c34b`
- Governed input SHA-256: `78d20d15daae43c3ed2d4a8e94a1a7014dc7d7a3b18d288529aeeb364f9755bd`
- Implementation recorded by the run: `c34782e6297e7e8efeefe529ce20d641cd61d4e5`
- Terminal state: `OWNER_REVIEW_READY`
- Terminal result: `PASS_IMPLEMENTATION_OWNED_SURFACE_SECRET_SCAN_V2_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW`
- Proof wall-clock duration: `1759.715s` (about `29m 19.715s`)
- Resume/retry/second-proof count: `0 / 0 / 0`

All thirteen immutable events retained `public_write_authority=false`. Passed stages:

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
12. `PACKAGE_QA_PASSED`
13. `OWNER_REVIEW_READY`

## Creative, timing, and review truth

- Parent/coordinator: native Codex Desktop `gpt-5.6-sol / HIGH`
- Bounded XHIGH executions: 4 across 3 fresh child tasks
  - fresh editorial/narration authorship;
  - one same-video editorial timing revision before motion;
  - fresh waveform-locked Remotion authorship;
  - fresh actual-media review.
- XHIGH mechanical-work executions: 0
- CLI/SDK/headless/9Router/provider creative substitutions: 0
- Prior proof creative source reused: false
- Actual-media decision: `NO_MATERIAL_REVISION`
- Render/rerender/creative-rerender count: `2 / 0 / 0`

The actual-media reviewer found no material revision requirement. Its sole non-material observation
was that the claims comparison scene settles after its reveal, while the stable comparison and
documentary strip earn the hold. No replacement source or rerender followed.

Accepted Kokoro timing lock:

- timing-lock SHA-256: `a64576ae729bf499914e4f3b61fc573285a076933d9058277f049532d9fbb805`
- route: local `kokoro-onnx / kokoro-v1.0`
- voice/speed/language: `af_heart / 1.06 / en-us`
- narration duration: `57.852667s`
- narration SHA-256: `2b24889d7f3c99fd77bca02038e20fa574cd445923ce220e8bdae5c799da2fe2`
- external media cost: USD `0.00`

## Owner-review media and package

- Final MP4: H.264 High/AAC LC, 1080x1920, 30 fps, `59.185s`, 16,843,882 bytes
- Final MP4 SHA-256: `7f58e126840c8399fc0c79177faa1838f8708055d41a03a36fa1dda16b08ccfb`
- Media contract: `PASS_MEDIA_CONTRACT / SHORT_9_16`
- Integrated loudness / true peak: `-16.0 LUFS / -1.5 dBFS`
- Final mix SHA-256: `324b85060d9a8bb31332b64f249299917ee78a6e9be56d1ff73a8fb83339bacc`
- Picture-lock SHA-256: `2ddaab492a7cfcc9090203a30311a627b65510e45ffd4abf4ff3e97590fa1bac`
- Proxy SHA-256: `742e30dbc5afa7cefd809339a5af995976caecec403983ded9be233f60d81998`
- Final contact-sheet SHA-256: `279cf153fcc622a554dd771b3941631fb4cb8dc66cf178577d7cbd3e9b56ee89`
- Package ID: `pkg_adb597c307e1216b94e802329fecaa99cf0d4dd9cc39ce4411f0c7a416d1ec5b`
- Package manifest SHA-256: `d9ec1666335f90e2b825f6132ccb91d32dc10529e6d38703fb5d13700aa00f1e`
- Caption JSON/SRT/VTT SHA-256: `a7ddbf70... / 0921b0cd... / f9056ff6...`
- Owner-review bundle SHA-256: `fb44dbd761fc9422772260c52eaa00554ba0b15c551bc7043581584710295aff`
- Technical/factual/rights/cost/safety/ledger reports: present, hashed, and passing

The package is explicitly `AUDIO_SIDECAR_FIRST_PACKAGE_ONLY_ZERO_PUBLIC_WRITE`, with no intended
future surfaces and `transport=null`.

## Manual intervention and safety truth

- Operator narration/source/media/checkpoint edits after proof start: `0 / 0 / 0 / 0`
- Operator intervention minutes: `0`
- Manual repair, proof retry, proof resume, or second proof: `0`
- TikTok credential reads/API calls/draft deliveries: `0 / 0 / 0`
- YouTube, Meta, or other platform calls: `0 / 0 / 0`
- Public/private/unlisted writes: `0`
- Browser/CDP actions: `0`
- Credential/session/auth reads: `0`
- V1 reads/writes/mutations: `0 / 0 / 0`
- Scheduler/Automation mutations: `0`
- Public-write authority: `false`

## Exact next gate

The implementation and owner-review package are ready for Jim/ChatGPT inspection. Only an explicit
Jim/ChatGPT acceptance of the actual media and package can authorize the named unattended
production-soak task. That task remains blocked and unstarted.
