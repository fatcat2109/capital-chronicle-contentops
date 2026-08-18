# V2 Daily Operator Shadow — Native Codex App Automation Runbook

Authority date: 2026-08-18

Task: `TASK_CONTENTOPS_V2_V1_READONLY_TRIGGER_AND_CODEX_DAILY_OPERATOR_AUTOMATION_SHADOW_V1`

This runbook is the durable prompt authority for one standalone native Codex App Automation. Each
scheduled run must start a fresh Codex task in an isolated worktree on `gpt-5.6-sol / high`. The
automation is V2 shadow-only and has zero V1, scheduler, platform, upload, draft, or public-write
authority.

## Per-run contract

1. Fetch the remote and verify that the frozen implementation branch
   `task/v2-v1-readonly-trigger-codex-daily-operator-shadow-v1` is at its expected remote HEAD.
   Stop on parity failure. Do not merge or push from the scheduled proof run.
2. Run `scripts/run_v2_daily_operator_shadow_v1.py run` once against the canonical V1 production
   store and the isolated V2 shadow runtime. Pass the exact implementation HEAD, a unique safe
   operator-run ID, the native parent task ID when exposed, and a HIGH parent-session label.
3. Repeat the read/decision operation with a second unique run ID before creative work. Confirm
   that the repeat creates no duplicate candidate decision for the same immutable version and no
   duplicate video job.
4. Review the result. Performance is priority/packaging input only; it grants no factual or numeric
   authority. `NO_GENUINE_QUALIFIED_CANDIDATE_NO_VIDEO` is valid and must not be converted into a
   filler job.
5. If one genuine candidate is `QUALIFIED`, HIGH expands and validates the governed evidence packet,
   performs fresh rights-safe asset discovery and candidate-board work, and binds the resulting
   `contentops.v2.governed_proof_input.v1` packet with the `activate-job` command. Only then create
   one fresh isolated native Codex App task on exact `gpt-5.6-sol / xhigh` for the consequential
   per-video editorial/narration, visual/Remotion authorship, actual-media review, and bounded
   same-video revision. HIGH resumes acquisition, hashing, validation, rendering, audio, QA,
   packaging, evidence, waits, and recovery.
6. If no genuine candidate qualifies, create one fresh isolated native Codex App
   `gpt-5.6-sol / xhigh` task for a `SHADOW_ISOLATION_PROBE` using only
   `video/unattended_core_factory_v1/frozen_without_breaking_proof_input_v1.json`. The child may
   return a bounded three-beat editorial/visual treatment in its final response only. It must make
   no repository or runtime edit, perform no research, invoke no provider, and make no public or
   platform write. The probe is not a qualified content outcome.
7. Wait for the native child task, hash its returned result, and record the actual child task ID,
   model, reasoning effort, worktree, governed-input hash, and result hash with the
   `record-handoff` command. Do not infer IDs or provenance that the app does not expose.
8. Run `finalize-automation` to bind the automation identity, HIGH parent identity, fresh XHIGH
   child identity, V1 read snapshot, candidate/outbox state, idempotence counts, and durable review
   queue. Return that review result in the Scheduled inbox. Do not claim owner App-UI acceptance.

## Hard stops

- No `codex exec`, Codex CLI, SDK/API/headless, 9Router, provider, or persistent-XHIGH substitute.
- No V1 write, V1 scheduler change, performance-learning mutation, browser/CDP use, adapter call,
  upload, draft/private/unlisted upload, publication, or platform read/write.
- No ElevenLabs/TTS request in this shadow proof.
- No Task-4 work.
- If the native app cannot create and read back the fresh isolated XHIGH task, stop with
  `BLOCKED_NATIVE_CODEX_APP_FRESH_XHIGH_HANDOFF` and preserve the exact app evidence.
