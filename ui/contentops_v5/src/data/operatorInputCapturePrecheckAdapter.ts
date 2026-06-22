import { operatorInputCapturePrecheckPacket } from './operatorInputCapturePrecheckPacket';

export interface OperatorInputFieldPolicy {
  readonly required: boolean;
  readonly value_status: string;
  readonly capture_enabled: boolean;
  readonly editable_in_this_task: boolean;
  readonly generated_by_system: boolean;
  readonly stored_value: string;
  readonly operator_must_provide_later: boolean;
}

export type OperatorInputFieldPolicyMap = Readonly<Record<string, OperatorInputFieldPolicy>>;

export interface InputCapturePrecheckItem {
  readonly intent_item_id: string;
  readonly source_candidate_id: string;
  readonly relative_path: string;
  readonly evidence_role: string;
  readonly source_family: string;
  readonly records_count: number;
  readonly contract_name: string | null;
  readonly intent_scope_label: string;
  readonly source_gate_status: string;
  readonly operator_input_capture_precheck_status: string;
  readonly operator_review_required: boolean;
  readonly required_input_fields: readonly string[];
  readonly field_policy: OperatorInputFieldPolicyMap;
  readonly blocked_reasons: readonly string[];
  readonly missing_requirements: readonly string[];
  readonly allowed_next_step: string;
  readonly disallowed_outputs: readonly string[];
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

export interface OperatorInputCapturePrecheckPacketType {
  readonly task_label: string;
  readonly source_review_only_intent_packet_hash: string;
  readonly source_packet_task_label: string;
  readonly source_intent_item_count: number;
  readonly global_operator_input_capture_status: string;
  readonly input_capture_precheck_items: readonly InputCapturePrecheckItem[];
  readonly required_input_fields: readonly string[];
  readonly field_policy: OperatorInputFieldPolicyMap;
  readonly validation_rules: readonly string[];
  readonly blocked_reasons: readonly string[];
  readonly allowed_next_step: string;
  readonly disallowed_outputs: readonly string[];
  readonly truth_protection_flags: TruthProtectionFlags;
  readonly safety_flags: SafetyFlags;
  readonly next_recommended_task: string;
  readonly ledger_family: string;
  readonly hash_algorithm: string;
  readonly packet_hash: string;
}

export const operatorInputCapturePrecheckAdapter = {
  packet: operatorInputCapturePrecheckPacket as unknown as OperatorInputCapturePrecheckPacketType,
  inputCapturePrecheckItems: (operatorInputCapturePrecheckPacket?.input_capture_precheck_items ?? []) as readonly InputCapturePrecheckItem[],
  requiredInputFields: (operatorInputCapturePrecheckPacket?.required_input_fields ?? []) as readonly string[],
  fieldPolicy: (operatorInputCapturePrecheckPacket?.field_policy ?? {}) as OperatorInputFieldPolicyMap,
  validationRules: (operatorInputCapturePrecheckPacket?.validation_rules ?? []) as readonly string[],
  blockedReasons: (operatorInputCapturePrecheckPacket?.blocked_reasons ?? []) as readonly string[],
  disallowedOutputs: (operatorInputCapturePrecheckPacket?.disallowed_outputs ?? []) as readonly string[],
  truthProtectionFlags: (operatorInputCapturePrecheckPacket?.truth_protection_flags ?? {
    current_truth_promoted: false,
    dqr_cleared_by_contentops: false,
    market_data_promoted: false,
    numeric_truth_promoted: false,
    readiness_cleared_by_contentops: false,
  }) as TruthProtectionFlags,
  safetyFlags: (operatorInputCapturePrecheckPacket?.safety_flags ?? {
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
