# Status Ledger SHA Model

## Definitions

- `last_verified_remote_sha`: current `origin/master` HEAD observed when the status ledger is updated.
- `accepted_product_baseline_sha`: latest accepted product/feature commit.
- `last_status_commit_sha`: most recent status-only repair commit that adjusted ledger metadata without changing product behavior.

## Current values

- current remote HEAD verified before this status-only repair: `6dde149fd71b06637ff7bb394ae6ba8f3184482b`
- accepted product baseline SHA: `6dde149fd71b06637ff7bb394ae6ba8f3184482b`
- previous accepted product baseline: `4c04d74b54a9aef9405aaa6c9a05dae999ce09f6`
- status-only repair commit SHA: `d077a22bf4faf16153ea5b2e79993d7666aa44a5` until this repair commit is accepted; final evidence reports the new repo HEAD separately.

## Update rules

1. Update `last_verified_remote_sha` when a task verifies the current remote HEAD and updates the status ledger.
2. Update `accepted_product_baseline_sha` only when a product or feature commit is accepted.
3. Update `last_status_commit_sha` when a status-only repair commit is accepted.
4. Status-only repair commits must not become product baselines.

## Avoiding infinite SHA repair loops

A status-only commit may cause `origin/master` to advance beyond the product baseline. This is expected. Do not open another SHA repair solely because the post-repair repo HEAD differs from the pre-repair `last_verified_remote_sha`; report the final repo HEAD in task evidence and compare each SHA against its own field semantics.

## Canonical UI surface

Browser QA and product UI work target `ui/contentops_v5/`. V4 remains fallback/reference only and must not be used as the product target.


## V6 Substack publication audit review / manual metrics summary baseline note

Substack publication audit review / manual metrics summary feature commits are product baselines only after push and remote readback. Status-only repairs may advance HEAD but must not replace the accepted product baseline unless explicitly accepted as feature work. Previous baseline 4c04d74b54a9aef9405aaa6c9a05dae999ce09f6 is archived in status history.
