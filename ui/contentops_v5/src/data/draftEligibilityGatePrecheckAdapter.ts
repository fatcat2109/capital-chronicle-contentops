import { draftEligibilityGatePrecheckPacket } from './draftEligibilityGatePrecheckPacket';

export interface EligibilityFieldPolicy {
  readonly required: boolean;
  readonly source_slot_status: string;
  readonly source_value_status: string;
  readonly current_value: null;
  readonly placeholder_value: string;
  readonly missing: boolean;
  readonly pending_operator_input: boolean;
  readonly capture_enabled_in_source_task: boolean;
  readonly editable_in_source_task: boolean;
  readonly generated_by_system: boolean;
  readonly persistence_enabled: boolean;
  readonly validation_enabled: boolean;
  readonly draft_eligible: boolean;
  readonly blocking_reason: string;
}

export type EligibilityFieldPolicyMap = Readonly<Record<string, EligibilityFieldPolicy>>;

export interface DraftGenerationPolicy {
  readonly draft_generation_enabled: boolean;
  readonly headline_generation_enabled: boolean;
  readonly hook_generation_enabled: boolean;
  readonly caption_generation_enabled: boolean;
  readonly platform_copy_generation_enabled: boolean;
  readonly ai_writer_generation_enabled: boolean;
  readonly public_postable: boolean;
  readonly dispatch_ready: boolean;
  readonly draft_storage_enabled: boolean;
  readonly operator_input_capture_enabled: boolean;
  readonly validation_enabled: boolean;
}

export interface DraftEligibilityItem {
  readonly draft_eligibility_item_id: string;
  readonly source_stub_item_id: string;
  readonly source_intent_item_id: string;
  readonly source_candidate_id: string;
  readonly relative_path: string;
  readonly evidence_role: string;
  readonly source_family: string;
  readonly records_count: number;
  readonly contract_name: string | null;
  readonly intent_scope_label: string;
  readonly source_supervised_input_stub_status: string;
  readonly draft_eligibility_status: string;
  readonly required_input_fields: readonly string[];
  readonly missing_required_input_fields: readonly string[];
  readonly eligibility_field_policy: EligibilityFieldPolicyMap;
  readonly draft_generation_enabled: boolean;
  readonly public_postable: boolean;
  readonly draft_generation_policy: DraftGenerationPolicy;
  readonly blocked_reasons: readonly string[];
  readonly missing_requirements: readonly string[];
  readonly allowed_next_step: string;
  readonly disallowed_outputs: readonly string[];
  readonly forbidden_current_actions: readonly string[];
}

export interface DraftEligibilityTruthProtectionFlags {
  readonly draft_truth_promoted: boolean;
  readonly current_truth_promoted: boolean;
  readonly dqr_cleared_by_contentops: boolean;
  readonly market_data_promoted: boolean;
  readonly numeric_truth_promoted: boolean;
  readonly readiness_cleared_by_contentops: boolean;
}

export interface DraftEligibilitySafetyFlags {
  readonly ai_writer_generation_enabled: boolean;
  readonly live_api_called: boolean;
  readonly provider_api_called: boolean;
  readonly platform_api_called: boolean;
  readonly credential_hydrated: boolean;
  readonly secret_values_observed: boolean;
  readonly env_secret_read: boolean;
  readonly scheduler_enabled: boolean;
  readonly scraping_performed: boolean;
  readonly dispatch_ready: boolean;
  readonly public_postable: boolean;
  readonly actual_operator_input_capture_enabled: boolean;
  readonly editable_ui_enabled: boolean;
  readonly persistence_enabled: boolean;
  readonly draft_generation_enabled: boolean;
}

export interface DraftEligibilityGatePrecheckPacketType {
  readonly task_label: string;
  readonly source_supervised_input_stub_packet_hash: string;
  readonly source_packet_task_label: string;
  readonly source_supervised_input_stub_item_count: number;
  readonly global_draft_eligibility_status: string;
  readonly draft_eligibility_items: readonly DraftEligibilityItem[];
  readonly required_input_fields: readonly string[];
  readonly missing_required_input_fields: readonly string[];
  readonly allowed_next_step: string;
  readonly validation_rules: readonly string[];
  readonly blocked_reasons: readonly string[];
  readonly forbidden_current_actions: readonly string[];
  readonly disallowed_outputs: readonly string[];
  readonly truth_protection_flags: DraftEligibilityTruthProtectionFlags;
  readonly safety_flags: DraftEligibilitySafetyFlags;
  readonly next_recommended_task: string;
  readonly ledger_family: string;
  readonly hash_algorithm: string;
  readonly packet_hash: string;
}

export const draftEligibilityGatePrecheckAdapter = {
  packet: draftEligibilityGatePrecheckPacket as unknown as DraftEligibilityGatePrecheckPacketType,
  draftEligibilityItems: (draftEligibilityGatePrecheckPacket?.draft_eligibility_items ?? []) as readonly DraftEligibilityItem[],
  requiredInputFields: (draftEligibilityGatePrecheckPacket?.required_input_fields ?? []) as readonly string[],
  missingRequiredInputFields: (draftEligibilityGatePrecheckPacket?.missing_required_input_fields ?? []) as readonly string[],
  forbiddenCurrentActions: (draftEligibilityGatePrecheckPacket?.forbidden_current_actions ?? []) as readonly string[],
  validationRules: (draftEligibilityGatePrecheckPacket?.validation_rules ?? []) as readonly string[],
  blockedReasons: (draftEligibilityGatePrecheckPacket?.blocked_reasons ?? []) as readonly string[],
  disallowedOutputs: (draftEligibilityGatePrecheckPacket?.disallowed_outputs ?? []) as readonly string[],
  truthProtectionFlags: (draftEligibilityGatePrecheckPacket?.truth_protection_flags ?? {
    draft_truth_promoted: false,
    current_truth_promoted: false,
    dqr_cleared_by_contentops: false,
    market_data_promoted: false,
    numeric_truth_promoted: false,
    readiness_cleared_by_contentops: false,
  }) as DraftEligibilityTruthProtectionFlags,
  safetyFlags: (draftEligibilityGatePrecheckPacket?.safety_flags ?? {
    ai_writer_generation_enabled: false,
    live_api_called: false,
    provider_api_called: false,
    platform_api_called: false,
    credential_hydrated: false,
    secret_values_observed: false,
    env_secret_read: false,
    scheduler_enabled: false,
    scraping_performed: false,
    dispatch_ready: false,
    public_postable: false,
    actual_operator_input_capture_enabled: false,
    editable_ui_enabled: false,
    persistence_enabled: false,
    draft_generation_enabled: false,
  }) as DraftEligibilitySafetyFlags,
};
