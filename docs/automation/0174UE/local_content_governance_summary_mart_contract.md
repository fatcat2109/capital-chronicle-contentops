# 0174UE Local Content Governance Summary Mart Contract

- task_label: `TASK_CONTENTOPS_0174UE_LOCAL_CONTENT_GOVERNANCE_SUMMARY_MART_CONTRACT_V0`
- model_version: `0174UE_LOCAL_CONTENT_GOVERNANCE_SUMMARY_MART_CONTRACT_V1`
- source_baseline_commit: `b2a403607846fbc97e6cb23e5fc3170e93097351`
- packet_id: `local_content_governance_summary_mart_packet_7edbd6cfd601995402fcfa12`
- packet_hash: `7edbd6cfd601995402fcfa12c0ac80a348cfa3cb542151bc5b8f58ea7da02e08`

## Contract rules

- Mart aggregates local U4 through UD contract packets.
- Rows are review-only governance summaries, not UI state or publish truth.
- Public postable, dispatch-ready, auto-generation, approval, and public claim authority remain false.
- 0174UD U9 `unknown_or_blocked` audit families are preserved as soft caveats, not hard blockers.

## Safety

- No UI, API/provider/network/env/credential reads, scraping, browser, scheduler, DM/reply, dispatch, DQR/readiness clearing, current-truth promotion, or ingestion repo mutation.

## Next heavy batch

`TASK_CONTENTOPS_0174UF_AUDIT_LEDGER_FAMILY_TAXONOMY_EXTENSION_V0`

## Packet summary

```json
{
  "approval_ready_count": 0,
  "blocked_reasons": [],
  "current_truth_promoted_count": 0,
  "dispatch_ready_count": 0,
  "dqr_cleared_count": 0,
  "evidence_summaries": 10,
  "hard_blockers": [],
  "packet_hash": "7edbd6cfd601995402fcfa12c0ac80a348cfa3cb542151bc5b8f58ea7da02e08",
  "packet_id": "local_content_governance_summary_mart_packet_7edbd6cfd601995402fcfa12",
  "platform_summaries": 10,
  "public_postable_count": 0,
  "readiness_cleared_count": 0,
  "soft_caveats": [
    "0174UD_u9_audit_family_unknown_or_blocked_soft_caveat",
    "upstream_future_send_gate_preserved_soft_caveat"
  ],
  "summary_rows": 1
}
```
