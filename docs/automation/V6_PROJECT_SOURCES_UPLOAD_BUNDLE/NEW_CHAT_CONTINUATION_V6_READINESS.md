TASK_CONTENTOPS_V6_PROJECT_SOURCES_REFRESH_CONTINUATION_AFTER_READINESS_BUNDLE_V0

## Pipeline State Info
- **Repository**: cc-live-contentops
- **Branch**: master
- **Baseline before upload bundle task**: d97bc3968e1babf48c81f384fb547b439e48515c
- **Upload bundle generation HEAD (pre-commit generation input only, not runtime authority)**: 24dcfbf875fe10d59cf8a240272b03c3a398c022 (requires GitHub audit after push)
- **Latest Accepted Task**: TASK_CONTENTOPS_V6_OPERATOR_EVIDENCE_FIXTURE_LIFECYCLE_DRY_RUN_AND_AUDIT_TRAIL_HEAVY_BATCH_V0
- **Current Orchestrator Task**: TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_REFRESH_ORCHESTRATOR_AND_BLOCKED_PIPELINE_ROLLUP_HEAVY_BATCH_V0

## Safety & Governance Rules
- Environment access, provider integrations, and live adapter capabilities are permitted only when explicitly scoped via a task contract under the V6 Fast Ship Operating Profile.
- Never output raw secret values, webhook URLs, tokens, or cookies.

## Current Blockers
- Operator intent through supervised dispatch readiness is ready, but dispatch remains blocked.
- Blocker: `operator_idea_source_ref` is missing from preflight.

## Pipeline Dispatch State
- `public_postable`: false
- `dispatch_allowed_now`: false
- `approval_valid_for_dispatch`: false
- `kill_switch_active`: true

## Prompt Instruction
> [!IMPORTANT]
> Future Antigravity prompts in this workflow must start with the active task label on line one.

## Next Recommended Task
- **Task**: `TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0`
- **Goal**: Validate the operator facts and manual evidence fixture once Jim has populated the template values.
