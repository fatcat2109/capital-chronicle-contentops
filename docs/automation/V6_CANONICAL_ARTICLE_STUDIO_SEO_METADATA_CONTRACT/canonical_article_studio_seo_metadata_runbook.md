# V6 Canonical Article Studio SEO Metadata Contract Runbook

This runbook documents operator and system actions for the offline simulated SEO contract state.

## Operator Review Checklist
1. Confirm that all SEO field values remain unpopulated (null or empty list).
2. Verify that no raw sources or signatures are leaked.
3. Confirm that all active dispatch, publication, and outbox flags are locked to false.

## Resolving Blockers
- Refined draft is required to clear `refined_draft_missing` and route to SEO metadata generation.
