# V6 Canonical Article Studio Review Queue Runbook

This runbook documents operator and system actions for the offline simulated Review Queue state.

## Operator Review Checklist
1. Review the unapproved eligibility matrix and queue status.
2. Confirm that no raw sources or signatures are leaked.
3. Ensure no visual verification or screenshot claims are bypassed.

## Resolving Blockers
- Real Jim approval is required to clear `real_source_pack_not_approved` and `runtime_operator_approval_missing`.
