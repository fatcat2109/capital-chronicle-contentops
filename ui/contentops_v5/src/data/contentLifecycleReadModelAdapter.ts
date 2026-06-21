import { contentLifecycleReadModelPacket } from './contentLifecycleReadModelPacket';
import type { StatusKind } from '../types';

export interface LifecycleStage {
  stage_id: string;
  stage_order: number;
  stage_name: string;
  lifecycle_phase: string;
  source_task_label: string;
  source_module: string;
  source_packet_path: string;
  upstream_stage_ids: readonly string[];
  downstream_stage_ids: readonly string[];
  platform_scope: string;
  evidence_refs: readonly string[];
  blocker_codes: readonly string[];
  required_future_gate: string | null;
  state: 'COMPLETED' | 'PENDING' | 'BLOCKED';
  operator_action_required: boolean;
  public_postable: boolean;
  dispatch_ready: boolean;
  live_api_called: boolean;
  provider_api_called: boolean;
  env_read: boolean;
  credential_hydrated: boolean;
  scheduler_enabled: boolean;
  scraping_performed: boolean;
  autonomous_reply_or_dm_enabled: boolean;
  dqr_cleared_by_contentops: boolean;
  readiness_cleared_by_contentops: boolean;
  current_truth_promoted: boolean;
}

export interface LifecycleSummary {
  total_stage_count: number;
  blocked_stage_count: number;
  dispatch_ready_count: number;
  public_postable_count: number;
  live_api_call_count: number;
  provider_api_call_count: number;
  credential_hydration_count: number;
  env_read_count: number;
  all_safety_locks_active: boolean;
  current_lifecycle_position: string;
  next_blocker: string | null;
  next_recommended_task: string;
}

export const contentLifecycleReadModel = {
  packet: contentLifecycleReadModelPacket,
  stages: (contentLifecycleReadModelPacket?.stages ?? []) as readonly LifecycleStage[],
  summary: (contentLifecycleReadModelPacket?.summary ?? {
    total_stage_count: 16,
    blocked_stage_count: 12,
    dispatch_ready_count: 0,
    public_postable_count: 0,
    live_api_call_count: 0,
    provider_api_call_count: 0,
    credential_hydration_count: 0,
    env_read_count: 0,
    all_safety_locks_active: true,
    current_lifecycle_position: 'operator_review_bundle',
    next_blocker: 'approval_gate',
    next_recommended_task: 'TASK_CONTENTOPS_0175BF_OPERATOR_REVIEW_READ_MODEL_TO_V5_QUEUE_BINDING_V0',
  }) as LifecycleSummary,
  safetyFlags: contentLifecycleReadModelPacket?.safety_flags ?? {
    all_safety_locks_active: true,
    live_api_called: false,
    provider_api_called: false,
    env_read: false,
    credential_hydrated: false,
    scheduler_enabled: false,
    scraping_performed: false,
    autonomous_reply_or_dm_enabled: false,
    public_postable: false,
    dispatch_ready: false,
  },
  nextBlocker: contentLifecycleReadModelPacket?.summary?.next_blocker ?? 'approval_gate',
  currentLifecyclePosition: contentLifecycleReadModelPacket?.summary?.current_lifecycle_position ?? 'operator_review_bundle',
  nextRecommendedTask: contentLifecycleReadModelPacket?.summary?.next_recommended_task ?? 'TASK_CONTENTOPS_0175BF_OPERATOR_REVIEW_READ_MODEL_TO_V5_QUEUE_BINDING_V0',
};

export const getStatusColor = (status: 'COMPLETED' | 'PENDING' | 'BLOCKED'): StatusKind => {
  if (status === 'COMPLETED') return 'verified';
  if (status === 'BLOCKED') return 'blocked';
  return 'review';
};
