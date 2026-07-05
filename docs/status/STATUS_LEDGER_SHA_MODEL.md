# Status Ledger SHA Model

## Definitions

- `last_verified_remote_sha`: current `origin/master` HEAD observed when the status ledger is updated.
- `accepted_product_baseline_sha`: latest accepted product/feature commit.
- `last_status_commit_sha`: most recent status-only repair commit that adjusted ledger metadata without changing product behavior.

## Current values

- current remote HEAD verified before this docs/status refresh: `1a4d0e904e0ae1775ea879753e22ba203b135658`
- accepted product baseline SHA: `37b2d2b4ed223ed1665bb174531e8c7cc25e590d`
- previous accepted product baseline: `666e006cac001fe2ae798463ac57460e809ffb8c`
- docs/status refresh commit SHA: reported in final evidence after commit/push; it must not become product baseline unless explicitly accepted as product work.

## Update rules

1. Update `last_verified_remote_sha` when a task verifies the current remote HEAD and updates the status ledger.
2. Update `accepted_product_baseline_sha` only when a product or feature commit is accepted after push/readback.
3. Update `last_status_commit_sha` when a status-only repair commit is accepted.
4. Status-only repair commits must not become product baselines.
5. Docs/status refresh commits must not replace accepted product baselines unless the user explicitly accepts them as product work.

## Avoiding infinite SHA repair loops

A status-only commit may cause `origin/master` to advance beyond the product baseline. This is expected. Do not open another SHA repair solely because the post-repair repo HEAD differs from the pre-repair `last_verified_remote_sha`; report the final repo HEAD in task evidence and compare each SHA against its own field semantics.

## Canonical UI surface

Browser QA and product UI work target `ui/contentops_v5/`. V4 remains fallback/reference only and must not be used as the product target.

## V6 LinkedIn manual publication evidence loop baseline note

LinkedIn manual publication evidence loop feature commit `83c53fd3a39b377d9f74fa70cd8b6a5357689ecb` is the accepted product baseline after push/readback. Its evidence remains fixture/manual/operator-supplied where publication URL or metrics fields appear. No LinkedIn API, URL fetch/scrape, browser automation, platform action, credential read, provider call, live publish, dispatch, send, schedule, approve, DM, comment, like, or reaction is implied by this SHA model.
