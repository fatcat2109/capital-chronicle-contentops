# V6 Canonical Article Studio Placeholder Binding Runbook

This runbook documents operator and system actions for the offline simulated Placeholder Binding state.

## Operator Review Checklist
1. Confirm that all placeholder values remain unmaterialized (null).
2. Verify that no raw sources or signatures are leaked.
3. Confirm that all active dispatch, publication, and outbox flags are locked to false.

## Resolving Blockers
- Real Jim approval is required to clear `real_source_pack_not_approved` and `runtime_operator_approval_missing`.
