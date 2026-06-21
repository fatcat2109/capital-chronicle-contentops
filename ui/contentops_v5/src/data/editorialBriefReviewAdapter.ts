import { editorialBriefReviewPacket } from './editorialBriefReviewPacket';

export interface CandidateReviewItem {
  readonly candidate_id: string;
  readonly relative_path: string;
  readonly evidence_role: string;
  readonly source_family: string;
  readonly records_count: number;
  readonly contract_name: string | null;
  readonly advisory_only: boolean;
  readonly candidate_only: boolean;
  readonly operator_review_required: boolean;
  readonly blocked_reasons: readonly string[];
  readonly allowed_next_step: string;
}

export interface ProtectedTruthFlags {
  readonly current_truth_promoted: boolean;
  readonly dqr_cleared_by_contentops: boolean;
  readonly market_data_promoted: boolean;
  readonly numeric_truth_promoted: boolean;
  readonly readiness_cleared_by_contentops: boolean;
}

export interface SafetyFlags {
  readonly credential_hydrated: boolean;
  readonly dispatch_ready: boolean;
  readonly env_secret_read: boolean;
  readonly live_api_called: boolean;
  readonly platform_api_called: boolean;
  readonly provider_api_called: boolean;
  readonly public_postable: boolean;
  readonly scheduler_enabled: boolean;
  readonly scraping_performed: boolean;
  readonly secret_values_observed: boolean;
}

export interface EditorialBriefReviewPacketType {
  readonly task_label: string;
  readonly source_bridge_task_label: string;
  readonly source_bridge_packet_hash: string;
  readonly contentops_source_head: string;
  readonly packet_hash: string;
  readonly ledger_family: string;
  readonly ingestion_repo_path_checked: string;
  readonly ingestion_repo_head: string;
  readonly ingestion_repo_branch: string;
  readonly ingestion_repo_status: string;
  readonly candidate_count: number;
  readonly candidate_review_items: readonly CandidateReviewItem[];
  readonly topic_families: readonly string[];
  readonly evidence_roles: readonly string[];
  readonly required_operator_review_checklist: readonly string[];
  readonly blocked_reasons: readonly string[];
  readonly protected_truth_flags: ProtectedTruthFlags;
  readonly safety_flags: SafetyFlags;
  readonly next_recommended_task: string;
}

export const editorialBriefReviewAdapter = {
  packet: editorialBriefReviewPacket as unknown as EditorialBriefReviewPacketType,
  candidateReviewItems: (editorialBriefReviewPacket?.candidate_review_items ?? []) as readonly CandidateReviewItem[],
  topicFamilies: (editorialBriefReviewPacket?.topic_families ?? []) as readonly string[],
  evidenceRoles: (editorialBriefReviewPacket?.evidence_roles ?? []) as readonly string[],
  checklist: (editorialBriefReviewPacket?.required_operator_review_checklist ?? []) as readonly string[],
  blockedReasons: (editorialBriefReviewPacket?.blocked_reasons ?? []) as readonly string[],
  protectedTruthFlags: (editorialBriefReviewPacket?.protected_truth_flags ?? {
    current_truth_promoted: false,
    dqr_cleared_by_contentops: false,
    market_data_promoted: false,
    numeric_truth_promoted: false,
    readiness_cleared_by_contentops: false,
  }) as ProtectedTruthFlags,
  safetyFlags: (editorialBriefReviewPacket?.safety_flags ?? {
    credential_hydrated: false,
    dispatch_ready: false,
    env_secret_read: false,
    live_api_called: false,
    platform_api_called: false,
    provider_api_called: false,
    public_postable: false,
    scheduler_enabled: false,
    scraping_performed: false,
    secret_values_observed: false,
  }) as SafetyFlags,
};
