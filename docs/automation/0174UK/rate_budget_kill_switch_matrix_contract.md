# 0174UK Rate Budget & Kill Switch Matrix V0

- task_label: `TASK_CONTENTOPS_0174UK_RATE_BUDGET_AND_KILL_SWITCH_MATRIX_V0`
- matrix_version: `0174UK_RATE_BUDGET_AND_KILL_SWITCH_MATRIX_V1`
- source_baseline_commit: `a3d4b82f74fe78a296b24f0a013ab3e8ad85fd4b`
- packet_id: `rate_budget_kill_switch_packet_e8b6c1ebef06237362095ad1`
- packet_hash: `e8b6c1ebef06237362095ad122fb75c23e548c7b57b65d10833213452148d8b3`
- next_required_gate: `TASK_CONTENTOPS_0174UL_PLATFORM_PREFLIGHT_AND_DRY_RUN_REQUEST_BUDGET_CONTRACT_V0`

## Rate Limit, Quota & Kill Switch Matrix

| Platform ID | Role | Gate Status | Strength | Kill Switch Required | Retry Allowed | Auto-Retry | Blockers |
|---|---|---|---|---|---|---|---|
| `x` | `primary_distribution` | `needs_human_review` | `partial_official_docs` | `True` | `False` | `False` | `rate_limit_and_spend_gate_unresolved` |
| `telegram_remote_operator` | `remote_operator_review` | `needs_human_review` | `partial_official_docs` | `True` | `False` | `False` | `operator_inbox_chat_proof_required, no_arbitrary_dm_allowed` |
| `telegram_channel_destination` | `controlled_channel_distribution` | `needs_human_review` | `partial_official_docs` | `True` | `False` | `False` | `channel_permission_proof_required` |
| `substack_newsletter` | `owned_long_form` | `manual_export_no_api` | `weak_manual_policy` | `False` | `False` | `False` | `manual_export_first_no_api` |
| `linkedin` | `professional_credibility` | `needs_human_review` | `partial_official_docs` | `True` | `False` | `False` | `linkedin_organization_page_binding_missing, rate_budget_unverified` |
| `threads` | `expansion_distribution` | `needs_human_review` | `partial_official_docs` | `True` | `False` | `False` | `meta_app_review_closed, rate_budget_unverified` |
| `instagram` | `expansion_distribution` | `needs_human_review` | `partial_official_docs` | `True` | `False` | `False` | `instagram_content_publish_gate_closed, rate_budget_unverified` |
| `facebook_page` | `expansion_distribution` | `needs_human_review` | `partial_official_docs` | `True` | `False` | `False` | `pages_manage_posts_gate_closed, rate_budget_unverified` |
| `tiktok` | `later_video_distribution` | `needs_human_review` | `partial_official_docs` | `True` | `False` | `False` | `tiktok_audit_closed, rate_budget_unverified` |
| `youtube` | `later_video_distribution` | `symbolic_rate_budget_ready` | `strong_official_docs` | `True` | `False` | `False` | `quota_upload_gate_closed` |

## Required Distinctions & Caveats

- **X**: Credit-budget pay-per-use caveat and endpoint-specific 15-minute rate limit windows.
- **Telegram Bot (Remote Operator & Channel)**: Restricted message limits with one-request budget models. Operator separate from Channel posting. Zero arbitrary DM access.
- **Substack**: Grounded strictly as manual copy-paste markdown export without API request budgets.
- **LinkedIn/Meta/TikTok**: Throttling, container publication limitations, and Meta app review rate caps. All are blocked or pending review.
- **YouTube**: Direct doc-grounded videos.insert quota limit (100 calls/day, 1 unit cost) without any stale quota claims.

## Safety Enforcements

- All live read/write/posting and env/credential access flags are strictly false.
- `auto_retry_allowed` is false for all platforms.
- `kill_switch_required` is true for all API-capable platforms.
- U9 audit entry family: `rate_budget_kill_switch_future`.
- Unofficial domain references fail closed on construction.

## Packet Summary

```json
{
  "auto_retry_allowed_count": 0,
  "blocked_platforms": [],
  "live_read_allowed_count": 0,
  "live_write_allowed_count": 0,
  "manual_export_only_platforms": [
    "substack_newsletter"
  ],
  "platforms_requiring_kill_switch": [
    "x",
    "telegram_remote_operator",
    "telegram_channel_destination",
    "linkedin",
    "threads",
    "instagram",
    "facebook_page",
    "tiktok",
    "youtube"
  ],
  "platforms_with_exact_numeric_claims": [
    "youtube"
  ],
  "platforms_with_unsupported_numeric_claims": [],
  "requirement_count": 10
}
```
