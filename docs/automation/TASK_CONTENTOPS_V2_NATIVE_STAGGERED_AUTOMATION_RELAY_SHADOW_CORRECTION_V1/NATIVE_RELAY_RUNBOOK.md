# V2 native staggered automation relay shadow runbook

Authority date: 2026-08-18

Task: `TASK_CONTENTOPS_V2_NATIVE_STAGGERED_AUTOMATION_RELAY_SHADOW_CORRECTION_V1`

Classification ceiling:
`PASS_V2_V1_READONLY_TRIGGER_AND_NATIVE_CODEX_AUTOMATION_RELAY_SHADOW`.

This runbook completes the Task-3 shadow through three separate native Codex Desktop
Automations. No Codex process invokes another Codex process. The shared coordination surface is
the existing V2-only SQLite store under
`A:\Capital Chronicle\Runtime\ContentOpsV2\daily_operator_shadow_v1`.

All three Automations use `Runs in: New chat`. The HIGH Daily Operator and HIGH Finalizer use
`gpt-5.6-sol / high`; the Creative Worker uses `gpt-5.6-sol / xhigh`. Repository mechanics run
only from the dedicated correction worktree. The XHIGH worker may use that worktree only for the
minimum relay command and may write only its immutable V2 runtime result.

## Durable transition contract

`READY_FOR_CREATIVE -> CREATIVE_CLAIMED -> CREATIVE_READY -> HIGH_FINALIZATION -> LOCAL_TERMINAL_RESULT`

The request and every transition are append-only. `(request_id, state)` is unique. Replays return
the existing receipt or no eligible request; they do not duplicate a request, claim, result,
finalization, job, or package.

Each transition records the actual task, run, thread, model/reasoning, worktree, input hashes,
output hashes, and zero-write state exposed by the native run. Use the exact marker
`NOT_EXPOSED_BY_CODEX_AUTOMATION` only for an identity dimension that the actual App does not
expose. Never invent provenance.

## HIGH Daily Operator

1. Verify the correction branch and exact implementation HEAD in the dedicated worktree.
2. Run the existing V1 read-only Daily Operator twice against one fixed proof instant with distinct
   run IDs. Confirm immutable decision and job idempotence.
3. Never manufacture a candidate. If no genuine candidate qualifies, create exactly one
   `SHADOW_ISOLATION_PROBE` request bound to
   `video/unattended_core_factory_v1/frozen_without_breaking_proof_input_v1.json` with
   `create-creative-request`.
4. Stop after `READY_FOR_CREATIVE`. Do not create or message the XHIGH task.

## XHIGH Creative Worker

1. Read only one `READY_FOR_CREATIVE` request and claim it with `claim-creative-request` using the
   actual native task/thread/model/reasoning/worktree identity.
2. For the bounded probe, read only the governed fixture and author one small three-beat
   editorial/visual treatment. This is orchestration evidence, not a qualified content outcome.
3. Write the immutable creative result under the V2 shadow runtime and call
   `record-creative-result`.
4. Do not perform Git, CodeGraph, general research, acquisition, rendering, tests, evidence
   mechanics, provider calls, browser/CDP work, or any V1/platform/public write.

## HIGH Finalizer

1. Consume only the single `CREATIVE_READY` request. Validate the request/result identity and
   output hash; create one bounded deterministic validation receipt.
2. Call `finalize-creative-request`, which atomically appends `HIGH_FINALIZATION` and
   `LOCAL_TERMINAL_RESULT`.
3. Record the native handoff compatibility receipt and run `finalize-automation` to emit the
   durable App review result.
4. Re-run the finalization read once to prove idempotence. Do not render the probe and do not start
   Task 4.

## Hard boundaries

- V1 is opened read-only (`mode=ro`, `query_only=1`) and V1 writes remain zero.
- Platform/public writes, adapter calls, browser/CDP, uploads, drafts, and publication remain zero.
- Codex CLI/`codex exec`, SDK/API/headless Codex, 9Router creative substitution, and process-to-
  process Codex invocation remain zero.
- The four V1 Automations are never changed.
- Pause all V2 proof Automations before handoff.
- Builder evidence never claims Jim/ChatGPT App-UI acceptance.
