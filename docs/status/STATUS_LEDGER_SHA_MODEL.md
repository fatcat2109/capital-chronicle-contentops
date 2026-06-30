# Status Ledger SHA Model

## Definitions

- `last_verified_remote_sha`: current `origin/master` HEAD observed when the status ledger is updated.
- `accepted_product_baseline_sha`: latest accepted product/feature commit.
- `last_status_commit_sha`: most recent status-only repair commit that adjusted ledger metadata without changing product behavior.

## Current values

- current remote HEAD: `84c65844a5ae55178463390fb29d8d9325cf2771`
- accepted product baseline SHA: `f688294d210065c21fe74740db8818ee09c526d2`
- status-only repair commit SHA: `84c65844a5ae55178463390fb29d8d9325cf2771`

## Update rules

1. Update `last_verified_remote_sha` when a task verifies the current remote HEAD and updates the status ledger.
2. Update `accepted_product_baseline_sha` only when a product or feature commit is accepted.
3. Update `last_status_commit_sha` when a status-only repair commit is accepted.
4. Status-only repair commits must not become product baselines.

## Avoiding infinite SHA repair loops

A status-only commit may cause `origin/master` to advance beyond the product baseline. This is expected. Do not open another SHA repair solely because `last_verified_remote_sha` differs from `accepted_product_baseline_sha`; compare each SHA against its own field semantics.

## Canonical UI surface

Browser QA and product UI work target `ui/contentops_v5/`. V4 remains fallback/reference only and must not be used as the product target.
