// Generated static packet for TASK_CONTENTOPS_0174UY.
import type { V5OperatorReviewQueueManualPilotTrailPacket } from '../types';

export const operatorReviewQueuePacket: V5OperatorReviewQueueManualPilotTrailPacket = {
  "blocked_reasons": [
    "manual_review_required",
    "no_platform_credentials",
    "no_live_dispatch_allowed"
  ],
  "contract_version": "0174UY_V5_OPERATOR_REVIEW_QUEUE_MANUAL_PILOT_TRAIL_CONTRACT_V1",
  "disabled_live_action_state": {
    "connect_account_enabled": false,
    "live_dispatch_enabled": false,
    "publish_enabled": false,
    "reason": "manual_export_pilot_verification_only_no_live_affordance",
    "schedule_enabled": false,
    "send_enabled": false,
    "state_id": "disabled_live_action_0174UY",
    "sync_platform_enabled": false,
    "verify_credentials_enabled": false
  },
  "item_status_summary": "review_pending_operator_actions",
  "local_review_trail_entries": [
    {
      "entry_id": "trail_created_local_review_item",
      "entry_type": "created_local_review_item",
      "label": "Created local review items for X, Telegram, Substack, LinkedIn.",
      "status": "verified",
      "timestamp_placeholder": "local_only_time_placeholder"
    },
    {
      "entry_id": "trail_checklist_pending",
      "entry_type": "checklist_pending",
      "label": "Operator checklist is pending manual verification.",
      "status": "review",
      "timestamp_placeholder": "local_only_time_placeholder"
    },
    {
      "entry_id": "trail_manual_publish_url_empty",
      "entry_type": "manual_publish_url_empty",
      "label": "Manual publish URL empty — waiting for off-system operator publish.",
      "status": "review",
      "timestamp_placeholder": "local_only_time_placeholder"
    },
    {
      "entry_id": "trail_metrics_empty",
      "entry_type": "metrics_empty",
      "label": "Manual publish metrics empty — waiting for off-system operator recording.",
      "status": "review",
      "timestamp_placeholder": "local_only_time_placeholder"
    },
    {
      "entry_id": "trail_live_dispatch_disabled",
      "entry_type": "live_dispatch_disabled",
      "label": "Live dispatch disabled — proof of local-only safety bounds verified.",
      "status": "verified",
      "timestamp_placeholder": "local_only_time_placeholder"
    }
  ],
  "manual_publish_placeholders": [
    {
      "detail": "Manual publish URL must be recorded after operator acts outside ContentOps.",
      "status": "empty_not_recorded",
      "value": ""
    },
    {
      "detail": "Manual metrics must be recorded after operator observation outside ContentOps.",
      "status": "empty_not_recorded",
      "value": ""
    }
  ],
  "missing_proofs": [
    "operator_checklist_uncompleted",
    "manual_publish_url_unrecorded",
    "manual_metrics_unrecorded"
  ],
  "next_recommended_task": "TASK_CONTENTOPS_0174UZ_MANUAL_PILOT_TRAIL_RECONCILIATION_V0",
  "packet_hash": "473a376d9ff812ff830391e24d3cd75fd71b4faf576414f8b8a157b2ea9f284c",
  "packet_hash_algorithm": "sha256",
  "queue_id": "v5_operator_review_queue_473a376d9ff812ff830391e2",
  "review_items": [
    {
      "detail": "Verify X draft copy matches 0174UW local prechecks. Operator must publish manually.",
      "item_id": "item_x_manual_post_draft_review",
      "label": "X manual post draft review",
      "local_only": true,
      "manual_review_required": true,
      "no_api": true,
      "no_credentials": true,
      "no_scheduler": true,
      "not_dispatch_ready": true,
      "not_public_postable": true,
      "operator_action_outside_contentops_required": true,
      "status": "manual_review_required"
    },
    {
      "detail": "Verify Telegram message copy matches 0174UW local prechecks. Operator must copy manually.",
      "item_id": "item_telegram_channel_manual_message_review",
      "label": "Telegram Channel manual message review",
      "local_only": true,
      "manual_review_required": true,
      "no_api": true,
      "no_credentials": true,
      "no_scheduler": true,
      "not_dispatch_ready": true,
      "not_public_postable": true,
      "operator_action_outside_contentops_required": true,
      "status": "manual_review_required"
    },
    {
      "detail": "Verify Substack newsletter draft matches 0174UW local prechecks. Operator must paste manually.",
      "item_id": "item_substack_manual_newsletter_export_review",
      "label": "Substack manual newsletter/export review",
      "local_only": true,
      "manual_review_required": true,
      "no_api": true,
      "no_credentials": true,
      "no_scheduler": true,
      "not_dispatch_ready": true,
      "not_public_postable": true,
      "operator_action_outside_contentops_required": true,
      "status": "manual_review_required"
    },
    {
      "detail": "Verify LinkedIn draft copy matches 0174UW local prechecks. Operator must publish manually.",
      "item_id": "item_linkedin_manual_post_review",
      "label": "LinkedIn manual post review",
      "local_only": true,
      "manual_review_required": true,
      "no_api": true,
      "no_credentials": true,
      "no_scheduler": true,
      "not_dispatch_ready": true,
      "not_public_postable": true,
      "operator_action_outside_contentops_required": true,
      "status": "manual_review_required"
    }
  ],
  "safety_flags": {
    "credential_hydrated": false,
    "credential_values_accessed": false,
    "dispatch_ready": false,
    "dm_or_reply_automation_allowed": false,
    "dotenv_loaded": false,
    "env_read": false,
    "ingestion_repo_mutated": false,
    "local_only": true,
    "manual_export_only": true,
    "network_performed": false,
    "pilot_verification_only": true,
    "platform_api_called": false,
    "posting_performed": false,
    "provider_api_called": false,
    "public_postable": false,
    "readiness_cleared": false,
    "scheduler_enabled": false,
    "scraping_performed": false,
    "secret_output_allowed": false,
    "token_hash_or_prefix_suffix_output": false
  },
  "source_baseline_commit": "c6ab726a5762bad55179c77bbafbe379bc38f136",
  "source_manual_export_packet_hash": "277fb7d44b247efc6021f038e362256f746cc039",
  "task_label": "TASK_CONTENTOPS_0174UY_V5_OPERATOR_REVIEW_QUEUE_AND_MANUAL_PILOT_TRAIL_V0"
};
