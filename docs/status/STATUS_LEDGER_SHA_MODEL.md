# Status Ledger SHA Model

## Definitions

- `last_verified_remote_sha`: current `origin/master` HEAD observed when the status ledger is updated.
- `accepted_product_baseline_sha`: latest accepted product/feature commit.
- `last_status_commit_sha`: most recent status/evidence repair commit that adjusted ledger metadata.

## Current values

- current remote HEAD verified before this editorial QA task: `bcf5574d16a433b7b1b3bcb6deea2d7ead402502`
- accepted visual repair commit: `6a810aadadef4b3c9078173b32bed4b243f8552a`
- latest headline ingestion commit: `bcf5574d16a433b7b1b3bcb6deea2d7ead402502`
- editorial QA task product/evidence commit SHA: reported in final evidence after commit/push
- docs/status refresh SHA for this task is the same final product/evidence commit because the status refresh and QA gate ship together.

## Update rules

1. Update `last_verified_remote_sha` when a task verifies the current remote HEAD and updates the status ledger.
2. Update `accepted_product_baseline_sha` only when a product or feature commit is accepted after push/readback.
3. Update `last_status_commit_sha` when a status/evidence repair commit is accepted.
4. Status-only repair commits must not become product baselines unless the user explicitly accepts them as product work.
5. Docs/status refresh commits must not replace accepted product baselines unless the user explicitly accepts them as product work.

## Avoiding infinite SHA repair loops

A status/evidence commit may cause `origin/master` to advance beyond the pre-task verified remote HEAD. This is expected. Do not open another SHA repair solely because the post-repair repo HEAD differs from the pre-repair `last_verified_remote_sha`; report the final repo HEAD in task evidence and compare each SHA against its own field semantics.

## Canonical UI surface

Browser QA and product UI work target `ui/contentops_v5/`. V4 remains fallback/reference only and must not be used as the product target.

## Latest restore note

`TASK_CONTENTOPS_V6_RESTORE_NON_BYPASSED_FULL_AUTOMATION_SUCCESS_AND_EDITORIAL_QUALITY_V0` restored the non-bypassed full live automation run. Final run `v6_pipeline_3c44a9855cc6` reached `DISPATCH_COMPLETE` with article quality, source-backed media, Substack visual readback, and all implemented platform lanes successful. The final pushed commit SHA is reported in the final response.

## Latest editorial QA note

`TASK_CONTENTOPS_V6_POST_VISUAL_REPAIR_BASELINE_AND_EDITORIAL_QA_GATE_V0` adds a separate editorial acceptance field so dispatch completion cannot be confused with tier-1 editorial approval. The latest Crude Awakenings packet audits as `EDITORIAL_BLOCKED` while the scoped Substack + LinkedIn dispatch run remains transport-complete evidence.
