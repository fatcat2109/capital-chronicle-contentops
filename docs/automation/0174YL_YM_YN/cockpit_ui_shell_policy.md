# Cockpit UI Shell Policy

Task: `TASK_CONTENTOPS_0174YL_YM_YN_COCKPIT_UI_SHELL_CONTRACT_V0`

Status: `pass`

Readiness: `NOT_READY_FOR_LIVE_DISPATCH`

Live dispatch: `BLOCKED`

## Shell Regions

- `CommandHero`: title, readiness_class, local_governance_status, live_dispatch_status, next_safe_operator_action
- `SignalLockStrip`: no_live_dispatch, no_platform_api, no_credential_hydration, no_scheduler, no_autonomous_replies_or_dms, no_scraping, no_financial_advice_or_signal_language
- `OperationalTruthRail`: platform_statuses, review_queue_count, blocker_count
- `BlockerStack`: current_truth, required_future_gates, live_blocker_reasons
- `ContentLane`: manual_export_queue, x_preview_queue, telegram_preview_queue, blocked_live_dispatch_queue
- `EvidenceCard`: payload_hash_short, payload_class, platform, source_payload_id, source_notes, evidence_refs, can_dispatch, public_postable
- `AuditTable`: evidence_index, checksum, source_stage, status
- `NextActionPanel`: allowed_local_review_actions, forbidden_live_platform_actions

## Safety Rails

- Local-only: `True`
- Dispatch allowed: `False`
- Public-postable: `False`
- Runtime network allowed: `False`
- External assets allowed: `False`
- Hidden live affordances allowed: `False`

## Checksum

`91339095ff05fddfc832ccd180be10480c3f619c1153467523575208a3ce5a3a`
