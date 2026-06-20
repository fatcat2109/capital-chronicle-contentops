# Live Read-Only Research Approval Packet Schema V0

- task_label: `TASK_CONTENTOPS_0174UO_LIVE_READ_ONLY_RESEARCH_APPROVAL_PACKET_SCHEMA_V0`
- matrix_version: `0174UO_LIVE_READ_ONLY_RESEARCH_APPROVAL_PACKET_SCHEMA_CONTRACT_V1`
- source_baseline_commit: `07c093bfab6c1dd998e309bde092a74b2a785397`
- packet_id: `live_read_only_research_approval_packet_schema_packet_ee8ec710e41729a6463f1f4c`
- packet_hash: `ee8ec710e41729a6463f1f4cd6d83d04319c18408c97a85c2b851098a9936427`
- next_required_gate: `TASK_CONTENTOPS_0174UP_LIVE_READ_ONLY_RESEARCH_EVIDENCE_PACKET_DRY_RUN_SCHEMA_V0`

## Defined Schema Fields

| Field Name | Kind | Required | Secret Safe | Live Safe |
|---|---|---|---|---|
| `explicit_task_label` | `explicit_task_label` | `True` | `True` | `True` |
| `platform_id` | `platform_id` | `True` | `True` | `True` |
| `endpoint_family` | `endpoint_family` | `True` | `True` | `True` |
| `endpoint_allowlist` | `endpoint_allowlist` | `True` | `True` | `True` |
| `credential_policy` | `credential_policy` | `True` | `True` | `True` |
| `credential_handle_key_names_only` | `credential_handle_key_names_only` | `True` | `True` | `True` |
| `request_budget` | `request_budget` | `True` | `True` | `True` |
| `timeout_seconds` | `timeout_seconds` | `True` | `True` | `True` |
| `redaction_policy` | `redaction_policy` | `True` | `True` | `True` |
| `secret_output_prohibition` | `secret_output_prohibition` | `True` | `True` | `True` |
| `no_raw_response_logging` | `no_raw_response_logging` | `True` | `True` | `True` |
| `kill_switch_state` | `kill_switch_state` | `True` | `True` | `True` |
| `stop_conditions` | `stop_conditions` | `True` | `True` | `True` |
| `rollback_or_abort_policy` | `rollback_or_abort_policy` | `True` | `True` | `True` |
| `evidence_packet_schema` | `evidence_packet_schema` | `True` | `True` | `True` |
| `operator_approval_ref` | `operator_approval_ref` | `True` | `True` | `True` |
| `live_read_boundary` | `live_read_boundary` | `True` | `True` | `True` |
| `live_write_prohibition` | `live_write_prohibition` | `True` | `True` | `True` |
| `env_read_boundary` | `env_read_boundary` | `True` | `True` | `True` |
| `audit_chain_requirement` | `audit_chain_requirement` | `True` | `True` | `True` |

## Platform Validation Decisions Matrix

| Platform ID | Status | Strength | Precheck Status | Fields Present | Allowlist Status | Credential Status | Budget Status | Kill Switch Status |
|---|---|---|---|---|---|---|---|---|
| `x` | `schema_blocked` | `deterministic_block` | `blocked_precheck` | `True` | `allowlist_symbolic` | `credential_key_names_only_verified` | `request_budget_within_symbolic_limit` | `kill_switch_closed` |
| `telegram_remote_operator` | `schema_not_ready` | `symbolic_template_only` | `not_ready` | `True` | `allowlist_symbolic` | `credential_key_names_only_verified` | `request_budget_within_symbolic_limit` | `kill_switch_closed` |
| `telegram_channel_destination` | `schema_not_ready` | `symbolic_template_only` | `not_ready` | `True` | `allowlist_symbolic` | `credential_key_names_only_verified` | `request_budget_within_symbolic_limit` | `kill_switch_closed` |
| `substack_newsletter` | `manual_only` | `manual_policy_only` | `manual_only` | `True` | `manual_no_api` | `manual_no_credential` | `manual_no_api` | `manual_stop_policy` |
| `linkedin` | `schema_blocked` | `deterministic_block` | `blocked_precheck` | `True` | `allowlist_symbolic` | `credential_key_names_only_verified` | `request_budget_within_symbolic_limit` | `kill_switch_closed` |
| `threads` | `schema_blocked` | `deterministic_block` | `blocked_precheck` | `True` | `allowlist_symbolic` | `credential_key_names_only_verified` | `request_budget_within_symbolic_limit` | `kill_switch_closed` |
| `instagram` | `schema_blocked` | `deterministic_block` | `blocked_precheck` | `True` | `allowlist_symbolic` | `credential_key_names_only_verified` | `request_budget_within_symbolic_limit` | `kill_switch_closed` |
| `facebook_page` | `schema_blocked` | `deterministic_block` | `blocked_precheck` | `True` | `allowlist_symbolic` | `credential_key_names_only_verified` | `request_budget_within_symbolic_limit` | `kill_switch_closed` |
| `tiktok` | `schema_blocked` | `deterministic_block` | `blocked_precheck` | `True` | `allowlist_symbolic` | `credential_key_names_only_verified` | `request_budget_within_symbolic_limit` | `kill_switch_closed` |
| `youtube` | `schema_not_ready` | `symbolic_template_only` | `not_ready` | `True` | `allowlist_symbolic` | `credential_key_names_only_verified` | `request_budget_within_symbolic_limit` | `kill_switch_closed` |

## Platform-Specific Constraints Enforced by Schema

- **X**: Requires spend and rate budget proof, app access, and endpoint allowlist.
- **Telegram Operator**: Distinct remote operator inbox proof required, prohibits arbitrary DM/reply automation.
- **Telegram Channel Destination**: Bot channel permissions and admin validation required, prohibits auto-posting.
- **Substack**: Strict manual export only template (no API request budget, no credential hydration).
- **LinkedIn/Meta/TikTok**: Org/page proof, app review, creator/video proof, and developer audit requirements.
- **YouTube**: Requires OAuth consent and quota proofs, strictly enforces no stale sixteen-hundred units claim.

## Safety and Invariants

- All live read/write/public post allowed counts are strictly zero.
- All template safety metrics remain false.
- U9 preflight audit entries compiled under family `live_read_only_research_approval_packet_schema_future`.

## Packet Summary

```json
{
  "all_live_actions_blocked": true,
  "field_count": 20,
  "global_status": "blocked",
  "manual_only_count": 1,
  "platform_count": 10,
  "schema_blocked_count": 6,
  "schema_not_ready_count": 3,
  "template_count": 10
}
```
