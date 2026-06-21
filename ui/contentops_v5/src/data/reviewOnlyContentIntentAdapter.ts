import { reviewOnlyContentIntentPacket } from './reviewOnlyContentIntentPacket';

export interface RequiredOperatorInputs {
  readonly claim_scope_boundary: string;
  readonly content_purpose_category: string;
  readonly intended_audience_lane: string;
  readonly manual_operator_decision: string;
  readonly risk_review_notes: string;
  readonly source_review_notes: string;
}

export interface ReviewOnlyIntentItem {
  readonly intent_item_id: string;
  readonly source_candidate_id: string;
  readonly relative_path: string;
  readonly evidence_role: string;
  readonly source_family: string;
  readonly records_count: number;
  readonly contract_name: string | null;
  readonly advisory_only: boolean;
  readonly candidate_only: boolean;
  readonly source_gate_status: string;
  readonly review_only_intent_status: string;
  readonly operator_review_required: boolean;
  readonly required_operator_inputs: RequiredOperatorInputs;
  readonly blocked_reasons: readonly string[];
  readonly missing_requirements: readonly string[];
  readonly allowed_next_step: string;
  readonly disallowed_outputs: readonly string[];
  readonly intent_scope_label: string;
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

export interface ReviewOnlyContentIntentPacketType {
  readonly task_label: string;
  readonly source_content_intent_gate_precheck_packet_hash: string;
  readonly source_packet_task_label: string;
  readonly source_candidate_count: number;
  readonly review_only_intent_items: readonly ReviewOnlyIntentItem[];
  readonly global_intent_packet_status: string;
  readonly operator_review_required: boolean;
  readonly blocked_reasons: readonly string[];
  readonly allowed_next_step: string;
  readonly required_operator_inputs: RequiredOperatorInputs;
  readonly disallowed_outputs: readonly string[];
  readonly truth_protection_flags: TruthProtectionFlags;
  readonly safety_flags: SafetyFlags;
  readonly next_recommended_task: string;
  readonly packet_hash: string;
  readonly ledger_family: string;
}

export const reviewOnlyContentIntentAdapter = {
  packet: reviewOnlyContentIntentPacket as unknown as ReviewOnlyContentIntentPacketType,
  reviewOnlyIntentItems: (reviewOnlyContentIntentPacket?.review_only_intent_items ?? []) as readonly ReviewOnlyIntentItem[],
  blockedReasons: (reviewOnlyContentIntentPacket?.blocked_reasons ?? []) as readonly string[],
  disallowedOutputs: (reviewOnlyContentIntentPacket?.disallowed_outputs ?? []) as readonly string[],
  truthProtectionFlags: (reviewOnlyContentIntentPacket?.truth_protection_flags ?? {
    current_truth_promoted: false,
    dqr_cleared_by_contentops: false,
    market_data_promoted: false,
    numeric_truth_promoted: false,
    readiness_cleared_by_contentops: false,
  }) as TruthProtectionFlags,
  safetyFlags: (reviewOnlyContentIntentPacket?.safety_flags ?? {
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
