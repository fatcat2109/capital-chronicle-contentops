# Discord Operator Review Candidate Summary

- Task label: `TASK_CONTENTOPS_V6_DISCORD_OPERATOR_REVIEW_AND_DISPATCH_CANDIDATE_PACKET_V0`
- Source baseline: `docs/automation/DISCORD_APPROVAL_LEDGER_OUTBOX/approval_ledger_outbox_packet.json`
- Source hash approval gate packet: `docs/automation/DISCORD_PAYLOAD_HASH_APPROVAL_GATE/hash_approval_gate_packet.json`
- current_task_dispatchable=false for every candidate
- live_write_allowed_now=false
- future live task required=true
- explicit operator live approval required=true
- endpoint_family=null, method=null, request_budget=null
- host_allowlist=[] and path_family_allowlist=[]
- no webhook URL/token values are included
- no live send happened

| payload_type | target_name | payload_hash | destination_binding_id | credential_handle_id | outbox_status | revalidation_status | send_gate_decision | candidate_status | current_task_dispatchable | live_write_allowed_now |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| announcement | announcements | b166aebf1f53956f04ffa5122d6d065fc09e4f7953ec816e1b0b66a01be9d17d | discord_announcements_capital_chronicle_01 | discord_announcements_webhook_01 | queued_non_live_refusal_review | pass_non_dispatchable | REFUSE | future_live_pilot_candidate_ready | false | false |
| substack_drop | substack_drops | a084ced7249d9b764132e17888c15c5cfd6177329dbe5ce718311e07e849175d | discord_substack_drops_capital_chronicle_01 | discord_substack_drops_webhook_01 | queued_non_live_refusal_review | pass_non_dispatchable | REFUSE | future_live_pilot_candidate_ready | false | false |
| product_update | product_updates | 81075439dcafcdc979482d51dd56ce7cb0a704827a9fbe702a2994b3f329efdd | discord_product_updates_capital_chronicle_01 | discord_product_updates_webhook_01 | queued_non_live_refusal_review | pass_non_dispatchable | REFUSE | future_live_pilot_candidate_ready | false | false |
| operator_private_summary | operator_private | 32496155fbd7763cd9929cbebbc178b29d397a57ff0af20b26ff902932e3fad3 | discord_operator_private_capital_chronicle_01 | discord_operator_private_manual_no_webhook_01 | queued_non_live_refusal_review | pass_non_dispatchable | REFUSE | future_live_pilot_candidate_ready | false | false |

## Future Live Handoff Skeleton

Future live pilot must require exact dispatch_candidate_id, payload_hash, payload_id, target_name, destination_binding_id, credential_handle_id, rendered payload preview, endpoint family Discord webhook execute, official host allowlist, method POST, request budget 1 request and 0 retries unless separately approved, fixed timeout, kill switch check, idempotency key, post-request redacted audit, and stop on any mismatch or hidden destination/account/channel change.
