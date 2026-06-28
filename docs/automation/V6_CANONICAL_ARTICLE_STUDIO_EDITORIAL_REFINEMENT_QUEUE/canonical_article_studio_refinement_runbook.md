# V6 Canonical Article Studio Editorial Refinement Queue Runbook

This runbook documents operator and system actions for the offline simulated Refinement Queue state.

## Operator Review Checklist
1. Confirm that all rendered and refined values remain unpopulated (null).
2. Verify that no raw sources or signatures are leaked.
3. Confirm that all active dispatch, publication, and outbox flags are locked to false.

## Resolving Blockers
- Rendered draft is required to clear `rendered_draft_missing` and route to refinement.
