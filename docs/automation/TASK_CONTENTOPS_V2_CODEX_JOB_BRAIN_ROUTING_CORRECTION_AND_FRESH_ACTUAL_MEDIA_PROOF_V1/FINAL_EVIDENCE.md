# V2 Codex job-brain routing correction and fresh actual-media proof — final evidence

Authority date: 2026-08-17

Task: `TASK_CONTENTOPS_V2_CODEX_JOB_BRAIN_ROUTING_CORRECTION_AND_FRESH_ACTUAL_MEDIA_PROOF_V1`

Builder result: `FAIL_NATIVE_CODEX_EXEC_QUARANTINED_NO_MEDIA`

Requested PASS ceiling reached: **no**

Owner actual-media acceptance claimed: **no**

## Outcome

The unattended V2 creative path was corrected on a fresh branch from the failed-proof head. Active
creative work now uses a native, fresh-per-job `CodexJobBrain` requesting `gpt-5.6-sol` with
`xhigh` reasoning. The prior 9Router V2 creative entrypoints fail closed before any provider call;
the exact V1/V2 grounded-research ladder remains unchanged and research-only.

The implementation passed the full affected validation suite and was committed and pushed before
proof execution. The single authorized committed-head proof then stopped truthfully during its
initial native Codex execution. The safe receipt records exit code `1` and
`FAIL_CODEX_EXEC`; no final message or accepted creative artifact was produced. The supervisor
persisted the failure receipt in the immutable ledger and quarantined the job. No fallback, repair,
manual output insertion, resumed execution, or second proof was used.

## Git and authority reconciliation

- freshly fetched starting `origin/master`: `8f6e4422d09fc9794c38ccc036ff1d1d9650034c`;
- failed proof head and branch base: `59ad508f98621bcc169c4164dc2b49e15e123ab5`;
- task branch: `task/v2-codex-job-brain-routing-correction-fresh-actual-media-proof-v1`;
- implementation execution HEAD: `622b19e1282d4fbd81fad47f76f399b97c454737`;
- implementation commit: `feat(v2): route unattended creative work to Codex job brain`;
- local/remote implementation parity before proof: exact;
- canonical dirty checkout: preserved and untouched;
- implementation was built in the dedicated task worktree.

## Product capability delivered

- native `CodexJobBrain` and `CodexCliExecutor` own fresh job-scoped creative execution;
- exact requested selection is `gpt-5.6-sol / xhigh`;
- local CLI capability is checked before execution against the bundled model catalog;
- the initial execution writes editorial/source artifacts only inside the isolated job workspace;
- actual-media review is designed to resume only that job's Codex thread;
- receipts are hash-bound to governed packets, asset boards, generated outputs, and execution IDs;
- raw Codex JSONL, transcripts, stderr, and session/credential material are not persisted;
- Codex failure is fail-closed with a safe durable receipt and immediate quarantine;
- no creative fallback exists;
- the compatibility V2 creative seam and V2 creative router roles fail closed before provider use;
- the research-only ladder remains
  `cx/gpt-5.6-terra(high)` -> `vx/gemini-3.1-pro-preview(high)` ->
  `vx/gemini-3.5-flash(high)`;
- durable supervisor restart/invalidation, generated-source sandbox, rendering, audio, QA, package,
  zero-write, and owner-bundle behavior remain covered by tests.

## Proof job

- isolated runtime:
  `.task-runtime/v2-codex-job-brain-proof-v1/proof-622b19e1`;
- `video_job_id`: `v2_fwb_78d20d15daae43c3ed2d`;
- `run_id`: `run_d6d887379ea24a4383fffc7d4b3ba292`;
- input hash: `78d20d15daae43c3ed2d4a8e94a1a7014dc7d7a3b18d288529aeeb364f9755bd`;
- target: `SHORT_9_16_1080X1920_30FPS`;
- `PROOF_RUN_STARTED_AT`: `2026-08-17T10:35:48.7023717Z`;
- implementation HEAD recorded for the run:
  `622b19e1282d4fbd81fad47f76f399b97c454737`;
- immutable stage-event count: `3`;
- passing checkpoints: `CLAIMED`, `GOVERNED_INPUT_LOCKED`;
- terminal state: `QUARANTINED`;
- terminal result: `HARD_FAILURE:CodexJobBrainError:codex_cli_execution_failed`;
- safe failure-receipt SHA-256:
  `63bfc0b8e3a760c273fd3c3b045e8d80ab4b190286434d00cea6204b44f69caf`;
- resume count: `0`;
- proof jobs created: `1`;
- proof executions attempted: `1`;
- render/rerender count: `0 / 0`;
- final media: none;
- platform-neutral package: none;
- manual source, narration, media, or checkpoint edits after proof start: `0`;
- operator intervention after proof start: `0` minutes;
- native Codex execution wall time: `4.541619` seconds;
- proof start to durable quarantine: approximately `9.434` seconds.

The failed runtime remains outside Git and was not mutated after quarantine except for read-only
status and receipt inspection.

## Creative execution truth

- execution plane: `CODEX_CLI_EXEC`;
- execution kind: `INITIAL_CREATIVE`;
- requested model family: `gpt-5.6-sol`;
- requested reasoning effort: `xhigh`;
- actual model family exposed by the failed execution: `null`;
- actual reasoning effort exposed by the failed execution: `null`;
- local catalog supports exact selection: `true`;
- CLI version: `codex-cli 0.148.0-alpha.9`;
- thread ID: `01a00f4a-c72a-7dc1-bae0-3b6145df7a3e`;
- result classification: `FAIL_CODEX_EXEC`;
- exit code: `1`;
- event count reported by Codex CLI: `5`;
- final-message classification: `null`;
- safe usage/cost: unavailable (`null`);
- 9Router creative route: `null`;
- 9Router creative provider calls: `0`;
- fallback allowed: `false`;
- fallback count: `0`;
- attempt count: `1`;
- accepted creative artifacts: `0`;
- public-write authority: `false`.

The safe receipt intentionally does not persist raw stderr or a transcript. Therefore this task
does not infer a more specific provider or CLI cause beyond the observed
`codex_cli_execution_failed` classification.

## Actual media

No proof media exists. There is no MP4, audio, contact sheet, technical media report, caption set,
package ID, or professional visual/audio judgment. The proof therefore cannot reach
`PASS_IMPLEMENTATION_UNATTENDED_V2_CODEX_BRAIN_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW`.

## Safety and isolation

- TikTok credential reads: `0`;
- TikTok API calls/drafts: `0 / 0`;
- YouTube API calls: `0`;
- Meta API calls: `0`;
- other platform calls: `0`;
- public/private/unlisted writes: `0`;
- browser/CDP publication actions: `0`;
- operational V1 reads/writes/mutations: `0 / 0 / 0`;
- scheduler mutations: `0`;
- soak started: `false`;
- secret/session material persisted or exposed: `false`;
- public-write authority stayed `false` on the job and every ledger event.

## Validation before proof

- full affected suite: `252 passed, 1 skipped`;
- focused implementation suite: `125 passed, 1 skipped`;
- configured real generated-source TypeScript/asset-hash test: `1 passed`;
- Python compile checks: `PASS`;
- Git whitespace check: `PASS`;
- exact native Codex CLI parser/capability check: `PASS`;
- CodeGraph generated context: `CODEGRAPH_CURRENT`;
- implementation local/remote parity before proof: `PASS`.

Pre-proof audio dependencies were fetched from the official `kokoro-onnx` v1.0 model release into
the ignored task runtime. SHA-256:

- `kokoro-v1.0.onnx`:
  `7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5`;
- `voices-v1.0.bin`:
  `bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d`.

Audio synthesis was not reached by the proof.

## Result ceiling and exact next

Classification: `FAIL`.

The implementation correction is committed and validated, but the required actual-media proof did
not complete. The remaining blocker is the observed native Codex execution failure. This task does
not authorize a diagnostic mutation, proof repair, second proof, soak, V1 integration, scheduling,
or platform operation.

`JIM_DECISION_REQUIRED_ON_NATIVE_CODEX_EXECUTION_FAILURE_AND_FRESH_PROOF_AUTHORITY`

`TASK_CONTENTOPS_V2_UNATTENDED_PRODUCTION_SOAK_V1` remains gated.
