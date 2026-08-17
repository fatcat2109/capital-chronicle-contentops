# V2 unattended core factory durable supervisor — final evidence

Authority date: 2026-08-17

Task: `TASK_CONTENTOPS_V2_UNATTENDED_CORE_FACTORY_DURABLE_SUPERVISOR_AND_ACTUAL_MEDIA_PROOF_V1`

Builder result: `FAIL_QUARANTINED_AT_OWNER_LOCKED_CREATIVE_EDITOR_ROUTE`

Requested PASS ceiling reached: **no**

Owner actual-media acceptance claimed: **no**

## Outcome

The durable isolated supervisor, atomic claim, immutable checkpoint ledger, exact V2 creative-role
routing, hard gates, restart/recovery behavior, local media execution path, platform-neutral package
path, and safe CLI were implemented and passed focused/affected validation.

The one authorized committed-head proof job did not reach creative-editor lock or media. It failed
truthfully when the exact owner-locked `V2_CREATIVE_EDITOR` route ended
`BLOCKED_AUTHORIZED_MODEL_POOL_EXHAUSTED`. The supervisor quarantined the job. No alternate model,
HIGH substitution, manual output replacement, restart from zero, or second proof job was used.

## Git and reconciliation

- freshly fetched starting `origin/master`: `8f6e4422d09fc9794c38ccc036ff1d1d9650034c`;
- accepted TikTok canary/evidence branch: `9af400a42829db3b0ee2f679e09e6aab7f8266dd`;
- merge base: `97cd13c914f1a48029cdc8529ab9ffd31637ec1d`;
- fetched divergence: master-only `1`, canary-only `3`;
- task branch: `task/v2-unattended-core-factory-durable-supervisor-actual-media-proof-v1`;
- implementation execution HEAD: `32648b355d3e526c91b412ccb09ca1cb32d6f7df`;
- implementation commit: `feat(v2): add durable unattended core factory supervisor`;
- reconciliation method: exact accepted canary code/CLI/tests/evidence files were transplanted;
  shared V2 authority was reconciled manually on fresh master; root V1 authority and the current
  V1 research ladder were preserved; no stale generated CodeGraph bytes were transplanted.

## Product capability delivered

The implementation adds:

- isolated SQLite V2 job/outbox under task runtime;
- content-addressed job identity and atomic `BEGIN IMMEDIATE` claim;
- one-active-run constraint;
- append-only stage events protected against update/delete by SQLite triggers;
- checkpoint artifact hash validation with affected-stage/downstream invalidation;
- run-once resume from the last valid checkpoint;
- exact owner-locked role registry:
  `V2_CREATIVE_EDITOR`, `V2_MOTION_CODE_AUTHOR`, `V2_CREATIVE_REVISION_AUTHOR`;
- exact route `new/gpt-5.6-sol-xhigh`, at most three same-route attempts, zero fallback;
- isolated 9Router invocation that does not read or mutate operational V1 control/cost state;
- governed-anchor and asset-hash gates;
- bounded generated-source sandbox and TypeScript validation;
- Remotion proxy/final render, actual-media contact-sheet review input, Kokoro audio, FFmpeg mux,
  caption sidecars, technical media QA, platform-neutral package identity, cost/runtime receipts,
  secret scan, and owner-review bundle path;
- no scheduler or daemon.

## Proof job

- runtime database class: `.task-runtime/v2-unattended-core-factory-v1/proof-32648b35/v2_jobs.sqlite3`;
- `video_job_id`: `v2_fwb_78d20d15daae43c3ed2d`;
- `run_id`: `run_6ff9b22f0617423cb8467ef2cf0ff9e0`;
- input hash: `78d20d15daae43c3ed2d4a8e94a1a7014dc7d7a3b18d288529aeeb364f9755bd`;
- target: `SHORT_9_16_1080X1920_30FPS`;
- `PROOF_RUN_STARTED_AT`: `2026-08-17T09:19:37.1061463Z`;
- implementation HEAD recorded on run: `32648b355d3e526c91b412ccb09ca1cb32d6f7df`;
- immutable stage-event count: `3`;
- passing checkpoints: `CLAIMED`, `GOVERNED_INPUT_LOCKED`;
- terminal state: `QUARANTINED`;
- terminal result:
  `HARD_FAILURE:CreativeContractError:creative_route_failed:V2_CREATIVE_EDITOR:BLOCKED_AUTHORIZED_MODEL_POOL_EXHAUSTED`;
- resume count: `0`;
- render count: `0`;
- rerender count: `0`;
- final media: none;
- package: none;
- operator source edits after start: `0`;
- operator generated-source edits after start: `0`;
- operator narration/media edits after start: `0`;
- manual checkpoint edits: `0`;
- operator intervention minutes: `0`;
- observed command wall time: approximately `9.68` seconds.

The failed runtime remains outside Git and was not mutated after quarantine.

## Creative truth

The immutable proof packet contains only accepted Frozen Without Breaking factual/evidence anchors,
permitted Capital Chronicle analysis statements, approved rights-safe asset identities, and hard
boundaries. It explicitly excludes the prior viewer-facing source, final narration, choreography,
layouts, and repair answer.

The editor checkpoint was never produced. Therefore:

- prior creative source reused as input: `false`;
- accepted creative artifacts: `0`;
- accepted XHIGH role calls: `0` (the editor invocation did not produce an accepted output);
- requested route: `new/gpt-5.6-sol-xhigh`;
- fallback count: `0` by the role policy and terminal disposition;
- safe per-attempt usage/cost receipt: unavailable because the invocation failed before the
  supervisor persisted a successful role receipt;
- factual-anchor gate before provider execution: `PASS`;
- generated-source sandbox/typecheck for the proof output: not reached.

The missing persisted safe failure-attempt receipt is an observability gap. It does not change the
truthful terminal disposition and was not repaired after proof start.

## Actual media

No proof media exists. Accordingly there is no MP4, SHA-256, duration, codec, loudness result,
caption set, package ID, contact sheet, or comparison judgment. Professional visual/audio
acceptance is not claimed.

## Safety

- TikTok credential reads: `0`;
- TikTok API calls: `0`;
- TikTok drafts: `0`;
- YouTube API calls: `0`;
- Meta API calls: `0`;
- other platform calls: `0`;
- public/private/unlisted writes: `0`;
- browser/CDP publication actions: `0`;
- operational V1 reads/writes/mutations: `0`;
- scheduler mutations: `0`;
- secret exposure: `false`;
- public-write authority stayed `false` on the job and every ledger event.

## Validation before proof

Focused/affected command result: `226 passed`.

Coverage included the new durable supervisor/store tests, canonical 9Router router and adapter
tests, free-form chapter pipeline, multiformat/package factory, publication-adapter shadow tests,
social binding/provider contract tests, and accepted TikTok canary tests. The new suite specifically
covers atomic-claim race, immutable events, legal stage order, exact role route, three same-route
attempt ceiling, zero fallback, V1-isolated invocation, factual rejection, creative sandbox,
real generated-source TypeScript compilation, accepted asset hashes, editor/motion restart,
render-cache reuse, corrupted artifact invalidation, terminal idempotency, quarantine, duplicate
identity/run prevention, zero writes, and owner-bundle identity.

Additional readiness evidence:

- Python compile checks passed;
- Kokoro `af_heart / 1.06 / en-us` synthesis smoke passed at 24 kHz;
- FFmpeg/ffprobe were available;
- real Remotion browser/bundle/frame render passed;
- CodeGraph was regenerated from the reconciled implementation and reported `CODEGRAPH_CURRENT`
  before the implementation commit.

## Result ceiling and blocker

`PASS_IMPLEMENTATION_UNATTENDED_V2_CORE_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW` is **not** claimed.

The remaining blocker is a fresh owner-authorized proof attempt after deciding whether to retain or
adjust the strict editor output contract and adding safe persistence for failed role-attempt
receipts. This task does not authorize that repair/retry, the production soak, V1 integration,
scheduling, or any platform operation.

## Exact next

Do not start automatically.

`JIM_DECISION_REQUIRED_ON_BOUNDED_PROOF_REPAIR_AND_FRESH_RETRY_AUTHORITY`

`TASK_CONTENTOPS_V2_UNATTENDED_PRODUCTION_SOAK_V1` remains gated because no owner-review media was
produced or accepted.
