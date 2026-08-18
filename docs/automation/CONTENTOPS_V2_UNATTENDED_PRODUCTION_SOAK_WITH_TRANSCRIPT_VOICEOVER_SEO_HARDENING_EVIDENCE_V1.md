# ContentOps V2 Unattended Production Soak With Transcript, Voiceover, and SEO Hardening - Evidence V1

Authority date: 2026-08-18

Task: `TASK_CONTENTOPS_V2_UNATTENDED_PRODUCTION_SOAK_WITH_TRANSCRIPT_VOICEOVER_SEO_HARDENING_V1`

## Result

`FAIL_V2_UNATTENDED_PRODUCTION_SOAK_SHARED_RUNTIME_WINERROR_206`

Three distinct current candidates qualified and entered the frozen soak. All three passed governed editorial validation, canonical spoken-transcript construction, real Kokoro timing lock, and transcript voiceover QA. All three also passed the post-transcript asset-selection and Remotion source contract before submission.

The first renderer advance failed in `MediaExecutor.typecheck_project -> subprocess.run -> CreateProcess` with `FileNotFoundError: [WinError 206] The filename or extension is too long`. This is a shared Windows runtime/path-or-command-length defect, not a candidate-specific defect. The frozen-epoch rule therefore prohibited a patch, workaround retry, or restart. The observed retail run was quarantined, the two unattempted render runs were quarantined under the shared-stop rule, and the soak stopped.

No success classification is authorized. There are no `OWNER_REVIEW_READY` jobs and no claim of Jim/ChatGPT media acceptance.

## Repository and freeze

- repository: `fatcat2109/capital-chronicle-contentops`
- branch: `task/v2-unattended-production-soak-transcript-voiceover-seo-hardening-v1`
- fresh `origin/master` at task start: `4be025ab1dd23bf8cfa71d18499987de2f674aa0`
- starting owner lineage: `task/v2-core-proof-owner-acceptance-and-soak-gate-v1` at `77d7ac16432415afcbb113596554d551cd4f0fb9`
- implementation commit: `9590f275ba086f5f874e872639c71d146d2461e6`
- frozen implementation/CodeGraph HEAD: `0a17bf3cb98a6c7024a4f474f526f054a781ed33`
- implementation remote parity before soak: exact
- `SOAK_EPOCH_STARTED_AT`: `2026-08-18T08:08:10.2828314Z`
- implementation patches after epoch start: `0`
- final evidence HEAD: the branch-tip commit containing this record; its exact local/remote parity is reported in the task handoff because a commit cannot contain its own hash

Implementation paths changed before freeze:

- `AGENTS.md`
- `docs/codegraph/INDEX.md`
- `docs/codegraph/V2_CONTEXT.md`
- `docs/codegraph/graph.json`
- `scripts/generate_codex_context_index.py`
- `scripts/run_v2_unattended_core_factory_v1.py`
- `tests/test_codex_context_index.py`
- `tests/test_v2_unattended_core_factory_v1.py`
- `video/AGENTS.md`
- `video/freeform_chapter_pipeline_v1/package_factory.py`
- `video/unattended_core_factory_v1/creative.py`
- `video/unattended_core_factory_v1/media.py`
- `video/unattended_core_factory_v1/store.py`
- `video/unattended_core_factory_v1/supervisor.py`
- `video/unattended_core_factory_v1/transcript.py`

## CodeGraph and pre-soak validation

- owner-lineage graph before implementation: `7,179` nodes / `13,484` edges
- frozen graph after implementation: `7,195` nodes / `13,521` edges
- post-generation result: `CODEGRAPH_CURRENT`
- graph post-check: one production canonical-transcript builder call; captions, SEO, and package consume the timing-locked transcript; no source-selection bypass; job/run/worker/input identity is checked across isolated roots
- focused suite: `64 passed, 1 skipped`
- configured Windows Remotion dependency-root/asset/typecheck test: `1 passed`
- `compileall`: pass
- `git diff --check`: pass
- deterministic isolation proof: one quarantined job does not block a later independent job; no cross-root or cross-package leakage

## Candidate qualification

No filler and no abstentions were used.

1. U.S. July 2026 retail sales - U.S. Census Bureau MARTS, published 2026-08-14. Distinct consumer/category and nominal-measurement story with official evidence and feasible commerce/process visuals.
2. Japan second-quarter 2026 GDP - Cabinet Office ESRI, published 2026-08-17. Distinct growth-composition story centered on domestic demand, net exports, investment, and government consumption.
3. Euro-area June 2026 goods trade - Eurostat, published 2026-08-14. Distinct goods-flow story covering June versus first-half balances, export/import direction, and energy/chemicals product contrast.

The three asset boards were authored after actual narration lock. HIGH downloaded and hash-verified eight selected rights-clear documentary assets; native data treatments remained governed-source-derived and code-authored. Unclear, weak, dated, unreadable, or semantically misleading candidates were rejected.

## Per-job immutable identity

### U.S. retail

- job: `v2_soak_us_retail_july_2026`
- run: `run_4bfd973737054f5f82f07107a97f0af1`
- governed input: `9d89f8c68910afd19df5e7d51d878afc865524ac4ed7ae3398be9e8491b1c372`
- editorial: `e5620febfaee8fb5863aa9de7f10e2ccf9eb4120ea5d7634274c3b7194d5d65e`
- canonical transcript: `6d70b9819a36ebef25af3a590ed25a15cb444bbdecec3cfae968ae0fa2a86bb5`
- timing lock: `91884b63ae79087804fe3ca4089e72512d87e7bc2a466ce49267674d1209ed0d`
- final narration WAV: `d50e26ff1dff051863dc337d3d7bef1735e6b83aee57ce5c0cb01a2b9b5dec63`
- actual narration: `46.588667s`; picture source: `1,418` frames
- asset selection: `46639e456387455940fc6933ba7c220a493f579ef15581cd7652548189c4ada2`
- motion manifest: `aa9fe2ad3972a878dfa7bcc9d1477490276afbbf88c2e3c4d4e67bb911367a9d`
- voice QA: `PASS_TRANSCRIPT_VOICEOVER_QA`; pronunciation-adjusted segment: `segment_01`
- terminal result: `QUARANTINED_SHARED_RUNTIME_WINERROR_206_OBSERVED`

### Japan GDP

- job: `v2_soak_japan_gdp_q2_2026`
- run: `run_134c824999e54565a07bc5fef47168fa`
- governed input: `5cbded87bcf0f5ce2ec27c6b0a243c0424345041e5366135155805370fb942d6`
- editorial: `b537965daa4352fd70e6d43c32a3e0c3fc0e49311cab57f1223c5ec9450c0594`
- canonical transcript: `ab7ffdc9a46baf41968041c537d99678e93f8a450e0dee27e455f07263941d18`
- timing lock: `00a860939e81f8b2fd25ee37a46516ac3c6cb281d2b3c9c2ab584badbc2bbf81`
- final narration WAV: `c4b4c7056ed80df9842ee3d0dfe6d28ec4038b98eb8d9706f13cdf1e76d869f0`
- actual narration: `46.663333s`; picture source: `1,420` frames
- asset selection: `d58d12834c3d3700a760b9a22998653955f9ad0061d6370d662f895d76b1aa21`
- motion manifest: `f5b81043e4baaf6e4e5b5985f55a628afbda0ba6ef5db913ea5536d62b20e541`
- voice QA: `PASS_TRANSCRIPT_VOICEOVER_QA`; pronunciation-adjusted segments: `seg_01` through `seg_05`
- terminal result: `QUARANTINED_SHARED_RUNTIME_SOAK_STOP_BEFORE_RENDER`

### Euro-area trade

- job: `v2_soak_euro_area_trade_june_2026`
- run: `run_2941d4af008b4617817ed635c468561b`
- governed input: `0ea1f4e12d46bc7f3571f3c25782b6252cea1e101e609760e9f983b697dbed1c`
- editorial: `12ddc77c3f9710d32bc58df733e9b519ccd1ea61b9ecf04b0ba1a82e7d659313`
- canonical transcript: `39e77909505c6d541206fd07baee3f1499a305ff09343bb5d54889287014d337`
- timing lock: `a95bc897eaa5bd4333c58e75f58f45bae7e86fca68fead1502106b44658d8729`
- final narration WAV: `f8986eda27e42c8f7d380f94602377db5ce63ec3fdc892beba1eb9fea8388779`
- actual narration: `44.498s`; picture source: `1,356` frames
- asset selection: `ecbb6dc4519e8fa669b59bd426446c66f5f2bc6e3f72b344a63f5fceb9390bc6`
- motion manifest: `3b6a9374af8d1392499696815af5248ec231d509701f150ec68e564a44029648`
- voice QA: `PASS_TRANSCRIPT_VOICEOVER_QA`; no pronunciation substitution required
- terminal result: `QUARANTINED_SHARED_RUNTIME_SOAK_STOP_BEFORE_RENDER`

## XHIGH, intervention, QA, and cost truth

- three fresh isolated `gpt-5.6-sol / XHIGH` workers, one per video
- each same-video worker performed bounded editorial/narration, post-transcript asset-board/discovery, and viewer-facing Remotion authorship
- creative turns: `9` total across the three same-video workers
- accepted editorial submissions: `3`; accepted motion submissions: `3`
- durable XHIGH stage-event count in the stopped store: `4` (`3` editorial locks plus the retail motion event reached before the shared failure); Japan/Euro motion submissions remained accepted inbox artifacts but were not advanced after STOP
- actual-media XHIGH review/revision turns: `0` because no proxy existed
- provider/headless/CLI/API/9Router creative substitutions: `0`
- narration revisions/resynthesis reruns: `0`; all timing locks passed on the first actual Kokoro synthesis
- completed renders/rerenders: `0 / 0`
- operator creative/code/media repair after soak start: `0`
- store intervention counters: source edits `0`, media edits `0`, checkpoint edits `0`, resume count `0`
- factual/editorial validation: pass for all three
- transcript/pronunciation/negation/number/institution QA: pass for all three
- motion claim binding, source sandbox, asset identity/hash, and timing contract: pass for all three before submission
- runtime caption, SEO, owned-secret, final package, and actual-media checks: not reached; no claim of pass
- external media cost: `$0.00`
- model cost: not exposed; no fabricated estimate
- recorded successful stage wall time before stop: `64.087202s`

## Failure, zero-write, and terminal state

- failure evidence SHA-256: `d51769d4c47fe51c4ec1b6d2474c938280c41a0d26040555f416ac72de8d2fb8`
- failure evidence size: `1,623` bytes
- renderer retries/workaround attempts: `0`
- store state: `QUARANTINED=3`, `RUNNING=0`, `QUEUED=0`, `OWNER_REVIEW_READY=0`
- MP4/package paths: none; no owner-review-ready artifact exists
- `public_write_authority`: `false` for every job, run, and event
- browser/platform/scheduler/V1 mutations or writes: `0`
- uploads/publications: `0`

## Stop and next-task gate

The soak epoch is closed and cannot be repaired or restarted under this task. `TASK_CONTENTOPS_V2_LOCALE_ACTIVATION_HARDENING_V1` was not started and remains unauthorized until a later exact task resolves the shared runtime defect and a fresh soak plus independent GitHub/actual-media audit succeeds.
