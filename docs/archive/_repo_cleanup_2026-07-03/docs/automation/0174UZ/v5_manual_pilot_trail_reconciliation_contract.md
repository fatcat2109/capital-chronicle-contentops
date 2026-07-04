# V5 Manual Pilot Trail Reconciliation Contract

> [!IMPORTANT]
> Local-only reconciliation review contract. No posting, scheduling, network, APIs, or live actions.

- **Task Label**: `TASK_CONTENTOPS_0174UZ_MANUAL_PILOT_TRAIL_RECONCILIATION_V0`
- **Reconciliation ID**: `v5_reconciliation_7998084518f5b9cabd948ab8`
- **Packet Hash**: `7998084518f5b9cabd948ab803ffd1a69f18ae95a68ce4999fd98218f5304f00`
- **Source Manual Export Packet Hash**: `277fb7d44b247efc6021f038e362256f746cc039`
- **Source Operator Review Queue ID**: `v5_operator_review_queue_473a376d9ff812ff830391e2`
- **Reconciliation Status**: `blocked_reconciliation_pending_evidence`

## Safety Declarations

| Flag | Required Value | Actual Status |
|---|---|---|
| `local_only` | `True` | `verified` |
| `manual_only` | `True` | `verified` |
| `no_platform_api` | `True` | `verified` |
| `no_credentials` | `True` | `verified` |
| `no_scheduler` | `True` | `verified` |
| `no_live_dispatch` | `True` | `verified` |
| `public_postable` | `False` | `verified` |
| `dispatch_ready` | `False` | `verified` |
| `approval_mutation` | `False` | `verified` |
| `credential_values_loaded` | `False` | `verified` |
| `network_performed` | `False` | `verified` |

## Lifecycle Reconciliation Steps

| Step ID | Label | Status | Detail |
|---|---|---|---|
| `export_packet_prepared` | Export Packet Prepared | `verified` | Supervised pilot manual export packet generated and local file paths sealed. |
| `operator_review_pending` | Operator Review Pending | `review` | Operator review queue has registered the export package and is awaiting checklist completion. |
| `checklist_pending` | Checklist Pending | `review` | Human compliance checks (X, Telegram, Substack, LinkedIn) must be checked off-system. |
| `manual_publish_url_empty` | Manual Publish URL Empty | `review` | No live URL has been recorded. Operator must post off-system and supply the link. |
| `manual_metrics_empty` | Manual Metrics Empty | `review` | No performance indicators recorded. Metrics remain uncaptured until manual operator entry. |
| `off_system_operator_action_required` | Off-System Operator Action Required | `review` | Publishing requires the compliance officer to post copy blocks outside ContentOps. |
| `reconciliation_blocked_until_evidence_recorded` | Reconciliation Blocked Until Evidence Recorded | `blocked` | Reconciliation record cannot be sealed without valid off-system manual publish links. |
| `live_dispatch_disabled` | Live Dispatch Disabled | `verified` | Local compliance engine actively prevents automated publishing or credential hydration. |

## Placeholder Evidence Fields

| Field ID | Label | Current Value | Verification Detail |
|---|---|---|---|
| `manual_publish_url` | Manual Publish URL | `""` | Target destination URL where the operator manually posted the content. |
| `manual_publish_timestamp` | Manual Publish Timestamp | `""` | Operator-recorded exact timestamp of the off-system publish action. |
| `manual_metrics_snapshot` | Manual Metrics Snapshot | `""` | Manual copy of impressions, shares, likes, and comments from original source views. |
| `platform_post_id` | Platform Post ID | `""` | Unique post/status identifier extracted from the platform URL. |
| `platform_permalink` | Platform Permalink | `""` | Direct canonical link back to the published institutional message. |
| `operator_notes` | Operator Notes | `""` | Manual compliance overrides or warnings noted by the operator during verification. |
