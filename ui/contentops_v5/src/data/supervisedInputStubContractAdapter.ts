import { supervisedInputStubContractPacket } from './supervisedInputStubContractPacket';

export interface SupervisedInputStubFieldPolicy {
  readonly required: boolean;
  readonly slot_status: string;
  readonly value_status: string;
  readonly current_value: null;
  readonly placeholder_value: string;
  readonly capture_enabled_in_this_task: boolean;
  readonly editable_in_this_task: boolean;
  readonly generated_by_system: boolean;
  readonly operator_must_provide_later: boolean;
  readonly future_supervised_capture_required: boolean;
  readonly persistence_enabled: boolean;
  readonly validation_enabled: boolean;
}

export type SupervisedInputStubFieldPolicyMap = Readonly<Record<string, SupervisedInputStubFieldPolicy>>;

export interface SupervisedInputStubItem {
  readonly stub_item_id: string;
  readonly source_intent_item_id: string;
  readonly source_candidate_id: string;
  readonly relative_path: string;
  readonly evidence_role: string;
  readonly source_family: string;
  readonly records_count: number;
  readonly contract_name: string | null;
  readonly intent_scope_label: string;
  readonly source_precheck_status: string;
  readonly supervised_input_stub_status: string;
  readonly required_input_fields: readonly string[];
  readonly input_stub_field_policy: SupervisedInputStubFieldPolicyMap;
  readonly blocked_reasons: readonly string[];
  readonly missing_requirements: readonly string[];
  readonly allowed_next_step: string;
  readonly disallowed_outputs: readonly string[];
  readonly forbidden_current_actions: readonly string[];
}

export interface SupervisedInputStubTruthProtectionFlags {
  readonly current_truth_promoted: boolean;
  readonly dqr_cleared_by_contentops: boolean;
  readonly market_data_promoted: boolean;
  readonly numeric_truth_promoted: boolean;
  readonly readiness_cleared_by_contentops: boolean;
}

export interface SupervisedInputStubSafetyFlags {
  readonly actual_operator_input_capture_enabled: boolean;
  readonly credential_hydrated: boolean;
  readonly dispatch_ready: boolean;
  readonly editable_ui_enabled: boolean;
  readonly env_secret_read: boolean;
  readonly live_api_called: boolean;
  readonly persistence_enabled: boolean;
  readonly platform_api_called: boolean;
  readonly provider_api_called: boolean;
  readonly public_postable: boolean;
  readonly scheduler_enabled: boolean;
  readonly scraping_performed: boolean;
  readonly secret_values_observed: boolean;
}

export interface SupervisedInputStubContractPacketType {
  readonly task_label: string;
  readonly source_operator_input_capture_precheck_packet_hash: string;
  readonly source_packet_task_label: string;
  readonly source_input_capture_precheck_item_count: number;
  readonly global_supervised_input_stub_status: string;
  readonly supervised_input_stub_items: readonly SupervisedInputStubItem[];
  readonly required_input_fields: readonly string[];
  readonly input_stub_field_policy: SupervisedInputStubFieldPolicyMap;
  readonly allowed_future_capture_modes: readonly string[];
  readonly future_capture_modes_enabled_in_this_task: boolean;
  readonly forbidden_current_actions: readonly string[];
  readonly validation_rules: readonly string[];
  readonly blocked_reasons: readonly string[];
  readonly allowed_next_step: string;
  readonly disallowed_outputs: readonly string[];
  readonly truth_protection_flags: SupervisedInputStubTruthProtectionFlags;
  readonly safety_flags: SupervisedInputStubSafetyFlags;
  readonly next_recommended_task: string;
  readonly ledger_family: string;
  readonly hash_algorithm: string;
  readonly packet_hash: string;
}

export const supervisedInputStubContractAdapter = {
  packet: supervisedInputStubContractPacket as unknown as SupervisedInputStubContractPacketType,
  supervisedInputStubItems: (supervisedInputStubContractPacket?.supervised_input_stub_items ?? []) as readonly SupervisedInputStubItem[],
  requiredInputFields: (supervisedInputStubContractPacket?.required_input_fields ?? []) as readonly string[],
  fieldPolicy: (supervisedInputStubContractPacket?.input_stub_field_policy ?? {}) as SupervisedInputStubFieldPolicyMap,
  allowedFutureCaptureModes: (supervisedInputStubContractPacket?.allowed_future_capture_modes ?? []) as readonly string[],
  forbiddenCurrentActions: (supervisedInputStubContractPacket?.forbidden_current_actions ?? []) as readonly string[],
  validationRules: (supervisedInputStubContractPacket?.validation_rules ?? []) as readonly string[],
  blockedReasons: (supervisedInputStubContractPacket?.blocked_reasons ?? []) as readonly string[],
  disallowedOutputs: (supervisedInputStubContractPacket?.disallowed_outputs ?? []) as readonly string[],
  truthProtectionFlags: (supervisedInputStubContractPacket?.truth_protection_flags ?? {
    current_truth_promoted: false,
    dqr_cleared_by_contentops: false,
    market_data_promoted: false,
    numeric_truth_promoted: false,
    readiness_cleared_by_contentops: false,
  }) as SupervisedInputStubTruthProtectionFlags,
  safetyFlags: (supervisedInputStubContractPacket?.safety_flags ?? {
    actual_operator_input_capture_enabled: false,
    credential_hydrated: false,
    dispatch_ready: false,
    editable_ui_enabled: false,
    env_secret_read: false,
    live_api_called: false,
    persistence_enabled: false,
    platform_api_called: false,
    provider_api_called: false,
    public_postable: false,
    scheduler_enabled: false,
    scraping_performed: false,
    secret_values_observed: false,
  }) as SupervisedInputStubSafetyFlags,
};
