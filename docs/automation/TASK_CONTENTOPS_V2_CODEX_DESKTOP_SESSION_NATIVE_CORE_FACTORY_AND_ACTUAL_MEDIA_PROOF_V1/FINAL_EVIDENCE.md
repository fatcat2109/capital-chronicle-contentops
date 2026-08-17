# V2 Codex Desktop-session-native core factory and actual-media proof — final evidence

Authority date: 2026-08-17

Task: `TASK_CONTENTOPS_V2_CODEX_DESKTOP_SESSION_NATIVE_CORE_FACTORY_AND_ACTUAL_MEDIA_PROOF_V1`

Builder result: `FAIL_QUARANTINED_AT_PROXY_BROWSER_PROCESS_LAUNCH_NO_MEDIA`

Requested PASS ceiling reached: **no**

Owner actual-media acceptance claimed: **no**

## Outcome

The active V2 factory was corrected from the rejected local-supervisor-to-CLI topology to an
explicit Codex Desktop App session boundary. The fresh Desktop task claimed the governed job,
authored fresh editorial and viewer-facing Remotion artifacts, and submitted them to deterministic
validation without Codex CLI, SDK/API/headless creative execution, 9Router, or a provider-model
substitute. Atomic claim, governed-input lock, exact factual/analysis validation, creative-source
sandboxing, artifact hash locks, and real TypeScript validation all passed.

The single committed-head proof failed before proxy media. Remotion attempted to launch its
task-local Chrome executable through a 303-character projected path and returned `spawn ...
ENOENT`, even though read-only checks after quarantine showed the exact executable exists both at
the canonical dependency target and through the junction path. The job was quarantined
immediately. No runtime/path repair, second proof, creative fallback, manual checkpoint change, or
media substitution was attempted.

## Git and authority

- freshly fetched `origin/master`: `8f6e4422d09fc9794c38ccc036ff1d1d9650034c`;
- starting V2 authority branch/head:
  `task/v2-codex-desktop-app-authority-reconciliation-v1` at
  `3718155c2b7228fb8b8b3a2d9b97edb49de4fd5f`;
- task branch:
  `task/v2-codex-desktop-session-native-core-factory-actual-media-proof-v1`;
- implementation HEAD: `de0d9748b36334d408f7cc845b8edda109df0ff8`;
- implementation message: `feat(v2): make core factory desktop-session native`;
- implementation local/remote parity before proof: exact;
- final evidence commit and remote parity are reported after commit/push because a commit cannot
  truthfully contain its own hash.

Implementation paths:

- `video/unattended_core_factory_v1/desktop_session.py`;
- `video/unattended_core_factory_v1/supervisor.py`;
- `video/unattended_core_factory_v1/codex_job_brain.py`;
- `video/unattended_core_factory_v1/__init__.py`;
- `scripts/run_v2_unattended_core_factory_v1.py`;
- `tests/test_v2_unattended_core_factory_v1.py`;
- generated `docs/codegraph/INDEX.md`, `docs/codegraph/V2_CONTEXT.md`, and
  `docs/codegraph/graph.json`.

## Active topology

```text
THIS FRESH CODEX DESKTOP APP TASK/SESSION
-> explicit durable claim and governed-input lock
-> fresh session-authored editorial + viewer-facing Remotion artifacts
-> immutable Desktop-session submission envelope
-> deterministic factual/rights/source/hash validation and TypeScript lock
-> deterministic Remotion proxy render [FAILED AT BROWSER PROCESS LAUNCH]
-> immediate durable quarantine
```

The historical `CodexCliExecutor`/`CodexJobBrain` compatibility names fail closed on construction
with `CODEX_CLI_NOT_V2_CREATIVE_AUTHORITY`. The active script/supervisor/session path contains no
CLI executor, `codex exec`, 9Router creative call, SDK/API creative call, headless creative
substitute, or provider-model fallback.

## Pre-proof validation

- focused/affected suite: `237 passed`;
- configured core-factory suite including real accepted asset hashes and real TypeScript
  validation: `14 passed`;
- deterministic fake/session-artifact E2E: reached `OWNER_REVIEW_READY` with zero live creative
  provider invocation;
- active-path forbidden-runtime scan: no match;
- Python compile: PASS;
- `git diff --check`: PASS;
- generated CodeGraph before implementation commit: `CODEGRAPH_CURRENT`;
- all six governed asset identities matched the packet SHA-256 values;
- Kokoro model/voice hashes matched the prior accepted evidence.

## Proof identity and ledger

- runtime: `.task-runtime/v2-desktop-session-core-proof-v1/proof-de0d9748`;
- `PROOF_RUN_STARTED_AT`: `2026-08-17T11:41:14.3631529Z`;
- `video_job_id`: `v2_fwb_desktop_session_de0d9748`;
- `run_id`: `run_231f3172582d4343a431ef3e2b4a955c`;
- governed input hash:
  `78d20d15daae43c3ed2d4a8e94a1a7014dc7d7a3b18d288529aeeb364f9755bd`;
- implementation HEAD recorded in `job_runs`:
  `de0d9748b36334d408f7cc845b8edda109df0ff8`;
- terminal state: `QUARANTINED`;
- immutable stage-event count: `6`;
- passing stages: `CLAIMED`, `GOVERNED_INPUT_LOCKED`, `CREATIVE_EDITOR_LOCKED`,
  `MOTION_SOURCE_LOCKED`, `HARD_SOURCE_VALIDATED`;
- failed stage: `PROXY_RENDERED` before artifact creation;
- terminal error class: `MediaExecutionError`;
- resume count: `0`;
- proof job count: `1`;
- proof epoch count: `1`;
- proof start to durable quarantine: approximately `320.95` seconds.

Hash evidence:

- immutable Desktop initial submission:
  `dcbda7a8168928cf2bb71dd1a2621b4a404035b466f59af717b3da183f15be41`;
- creative editor artifact:
  `d968cd75bb5a8ec0eb0b380e86ca0e855474d24852bb1e977dafc340505cd6a9`;
- motion source artifact:
  `0b1764317ea5d684a0149f8bea3c1a9131b9b8869dda74c93af60c5c1b12e4dd`;
- hard source/typecheck validation:
  `612cfc0b0db697f869e0e4342575ac94cdd1be2e8f55463179ec9a4d6f577867`;
- initial Desktop-session execution receipt:
  `101ca9c62fbe6e905e392feceba65af7197a9a929cfbf93e42e6d236a281f288`.

## Creative provenance truth

- creative runtime: `CODEX_DESKTOP_APP_FRESH_TASK_SESSION`;
- execution plane: `CODEX_DESKTOP_APP_TASK_SESSION`;
- model family: `gpt-5.6-sol`;
- reasoning effort: `xhigh`;
- provenance source: owner task/mode declaration in this fresh Desktop task;
- Desktop task/session database inspected: `false`;
- internal task-session ID exposed: `false`;
- session continuity key:
  `b007d965e55203cef98bf4b4532d43015b7360e23a129b916bb67771bf2805bd`;
- prior viewer-facing source/narration/choreography/layout/repair used as creative input: `false`;
- accepted initial creative stages: `1`;
- actual-media creative review stages: `0` because no proxy existed;
- CLI creative invocations: `0`;
- SDK/API/headless creative invocations: `0`;
- 9Router/provider creative invocations: `0`;
- fallback count: `0`;
- model usage/cost exposed: no;
- operator implementation patches after proof start: `0`;
- operator manual generated-source edits after proof start: `0`;
- operator manual narration/media/checkpoint repairs: `0`;
- Desktop-session creative authorship before immutable submission: yes, and is canonical job-brain
  activity rather than operator intervention.

## Media, runtime, and cost

- proxy render attempts: `1`;
- completed proxy renders: `0`;
- completed picture/final renders: `0`;
- rerenders: `0`;
- final MP4: none;
- audio synthesis/mix: not reached;
- captions/package: not reached;
- actual-media contact/review surface: none;
- owner-review bundle: none;
- external media cost: `$0`;
- model cost: unavailable/not exposed;
- successful media runtime: none.

## Exact blocker

Remotion resolved the Chrome executable beneath the generated project's `node_modules` junction.
The resulting executable path was 303 characters. Node reported:

`spawn <task-local chrome-headless-shell.exe> ENOENT`

Read-only post-quarantine checks showed:

- canonical dependency browser executable exists: true;
- projected task-local junction browser executable exists: true;
- projected path length: `303`;
- proxy file exists: false.

The observed evidence is consistent with a Windows process-launch path-length failure. A bounded
future repair should shorten the task-local runtime/browser executable path or configure Remotion
to use the existing browser through a short canonical path, then revalidate on a new committed
implementation and obtain explicit authority for exactly one new proof. This task does not make
that repair or run that proof.

## Safety

- TikTok credential reads/API calls/drafts: `0 / 0 / 0`;
- YouTube/Meta/other platform calls: `0 / 0 / 0`;
- public/private/unlisted writes: `0`;
- browser/CDP publication actions: `0`;
- operational V1 reads/writes/mutations: `0 / 0 / 0`;
- scheduler/automation mutations: `0`;
- secret/session/auth extraction: `0`;
- public-write authority remained false on the job and every event.

## Classification and next authority

`PASS_IMPLEMENTATION_DESKTOP_SESSION_NATIVE_V2_CORE_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW` is **not**
claimed because no actual media exists.

The generic Desktop-App handoff deep-research pointer is complete/superseded: the supported
one-job boundary is this explicit Desktop-session claim/submit/resume interface. The exact next
gate is now:

`JIM_DECISION_REQUIRED_ON_BOUNDED_SHORT_PATH_RUNTIME_REPAIR_AND_ONE_FRESH_PROOF_AUTHORITY`

`TASK_CONTENTOPS_V2_UNATTENDED_PRODUCTION_SOAK_V1` remains blocked.
