# V6 Platform Variant Renderer Runbook

This runbook documents operator and system actions for the offline simulated platform variant renderer state.

## Operator Review Checklist
1. Confirm that all platform output fields remain unpopulated (null or empty list).
2. Verify that no raw sources or signatures are leaked.
3. Confirm that all active dispatch, publication, and outbox flags are locked to false.

## Resolving Blockers
- Approved canonical article is required to clear `approved_canonical_article_missing` and route to platform variant rendering.

