import { contentIntentGatePrecheckPacket } from './contentIntentGatePrecheckPacket';

export interface CandidateGateItem {
  readonly candidate_id: string;
  readonly relative_path: string;
  readonly evidence_role: string;
  readonly source_family: string;
  readonly records_count: number;
  readonly contract_name: string | null;
  readonly advisory_only: boolean;
  readonly candidate_only: boolean;
  readonly operator_review_required: boolean;
  readonly content_intent_gate_status: string;
  readonly blocked_reasons: readonly string[];
  readonly missing_requirements: readonly string[];
  readonly allowed_next_step: string;
}

export interface TruthProtectionFlags {
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

export interface ContentIntentGatePrecheckPacketType {
  readonly task_label: string;
  readonly source_editorial_brief_review_packet_hash: string;
  readonly source_packet_task_label: string;
  readonly source_candidate_count: number;
  readonly candidate_gate_items: readonly CandidateGateItem[];
  readonly content_intent_gate_status: string;
  readonly operator_review_required: boolean;
  readonly blocked_reasons: readonly string[];
  readonly allowed_next_step: string;
  readonly disallowed_outputs: readonly string[];
  readonly truth_protection_flags: TruthProtectionFlags;
  readonly safety_flags: SafetyFlags;
  readonly next_recommended_task: string;
  readonly packet_hash: string;
  readonly ledger_family: string;
}

export const contentIntentGatePrecheckAdapter = {
  packet: contentIntentGatePrecheckPacket as unknown as ContentIntentGatePrecheckPacketType,
  candidateGateItems: (contentIntentGatePrecheckPacket?.candidate_gate_items ?? []) as readonly CandidateGateItem[],
  blockedReasons: (contentIntentGatePrecheckPacket?.blocked_reasons ?? []) as readonly string[],
  disallowedOutputs: (contentIntentGatePrecheckPacket?.disallowed_outputs ?? []) as readonly string[],
  truthProtectionFlags: (contentIntentGatePrecheckPacket?.truth_protection_flags ?? {
    current_truth_promoted: false,
    dqr_cleared_by_contentops: false,
    market_data_promoted: false,
    numeric_truth_promoted: false,
    readiness_cleared_by_contentops: false,
  }) as TruthProtectionFlags,
  safetyFlags: (contentIntentGatePrecheckPacket?.safety_flags ?? {
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
