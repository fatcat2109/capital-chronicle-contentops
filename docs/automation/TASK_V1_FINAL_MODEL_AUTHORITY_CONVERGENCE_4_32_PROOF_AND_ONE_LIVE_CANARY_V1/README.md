# V1 final model-authority convergence, 4/32 proof, and one-live-canary gate

Classification: `DEGRADED_DAILY_OUTPUT_DEFICIT / CANARY_NOT_AUTHORIZED`

Starting baseline: `2d39880fda3504201add67b15a0801847cc496b1`

Run date: 2026-08-22 (Asia/Bangkok)

## Phase A — permanent routed-model authority

Every reachable current V1 9Router role is restricted to exactly this ordered pair:

1. `vx/gemini-3.1-pro-preview(high)`
2. `vx/gemini-3.5-flash(high)`

Role order is deliberate: leaf/passive semantics use Flash then Pro; global assignment, grounded
research, and the legacy zero-write compatibility writer use Pro then Flash. The focused role-matrix
regression enumerates the integration manifest and rejects Fable, Opus, GPT, CX, Terra, and every other
non-Gemini routed model. The production article boundary is unchanged: a qualified article requires the
native `gpt-5.6-sol / HIGH` coordinator to request a fresh isolated `gpt-5.6-sol / XHIGH` worker. There
is no routed GPT/CX editorial rescue.

The live zero-write 9Router preflight verified the exact effective identities for both Gemini routes.
It reported no provider cost fields. Pro used 2,171 tokens (2,015 prompt, 156 completion) and Flash used
2,112 tokens (2,015 prompt, 97 completion).

## Phase B — four-frontier current-input proof

The runner command was:

```powershell
$env:PYTHONPATH='.'; python scripts/run_v1_current_multi_frontier_floor_rehearsal.py `
  --root artifacts/v1_final_model_authority_convergence_4_32_20260822 `
  --action probe `
  --task-label TASK_V1_FINAL_MODEL_AUTHORITY_CONVERGENCE_4_32_PROOF_AND_ONE_LIVE_CANARY_V1
```

The command was run four times against one frozen genuine-current runtime input:

- frozen input SHA-256: `6986d0be62dbfb21bd5cb1c77411cf0c751acccd7842db859f7e305a0d51a329`;
- four frontiers; exact headline identity coverage; no candidate reuse;
- 0 qualified article records and 0 of 32 derivative intents; remaining deficit 4/32;
- 64 bounded public source reads and 0 official source reads; no provider cost field;
- Phase-B model telemetry: 12 successful Pro invocations, 50,523 tokens (35,019 prompt, 15,504 completion); Flash was not reached; no provider cost field;
- 0 XHIGH editorial-worker requests/receipts/revisions, because every frontier stopped before the article boundary;
- 0 public writes, 0 publication-provider writes, `UNKNOWN_WRITE=0`, 0 production-store resets, and 0 fifth-Automation creations.

The four-frontier classification is `DEGRADED_DAILY_OUTPUT_DEFICIT`. The exact final blocker taxonomy is
`ALL_RANKED_CLUSTERS_EVIDENCE_BLOCKED` and
`EVIDENCE_REQUEST_BUDGET_EXHAUSTED_BEFORE_PUBLISHABILITY_POOL_CLOSURE`: accessible sources failed the
existing trustworthy/official evidence and capability gates. Those gates were not weakened or retried
beyond their bound.

The complete machine receipts remain in the local run root
`artifacts/v1_final_model_authority_convergence_4_32_20260822/`, including the frozen input, the summary,
and each frontier's candidate/evidence/read-only activity artifacts. They are runtime evidence and are
not committed as source fixtures.

## Phase C — deliberately not executed

Phase B did not meet the required 4 qualified articles and 32 derivative intents. Accordingly, this task
did not inspect or alter a live destination, call a publisher, create/enable/resume an Automation, or
perform a canary. No article/package/XHIGH receipt exists because no candidate earned the worker handoff.

## Validation

- router, research ladder, and provider/preflight tests: `23 passed`;
- hierarchical assignment, newsroom, targeted-evidence, official-loader, and locator tests: `141 passed`;
- Python compilation and `git diff --check`: passed.

The wider article-builder sweep had one pre-existing baseline expectation failure in
`test_ordinary_story_uses_one_quality_writer_and_skips_semantic_review`: an unchanged derivative payload
contains `Watch: No market reaction is asserted here.` where the fixture expected no reply text. This
does not exercise the model-pool change, and no unrelated product behavior was changed to mask it.
