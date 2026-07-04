# Draft Eligibility Gate Precheck

> [!IMPORTANT]
> This is a local-only schema draft eligibility precheck. It does not compile actual drafts, headlines, hooks, or platform copy, nor does it invoke live APIs or authorize publications.

- **Task Label**: `TASK_CONTENTOPS_0175BS_SUPERVISED_INPUT_STUB_TO_DRAFT_ELIGIBILITY_GATE_PRECHECK_V0`
- **Source Supervised Input Stub Packet Hash**: `cb0ce2665803ae05a5b407ad002f8277ea246b397c3193bd57b54a36b3a11dd4`
- **Source Packet Task Label**: `TASK_CONTENTOPS_0175BP_OPERATOR_INPUT_CAPTURE_PRECHECK_TO_SUPERVISED_INPUT_STUB_CONTRACT_V0`
- **Packet Hash**: `01ca95b8738a8f65b50a5edcdf59cf46fba72ce468e2de690e2e659332501b90`
- **Global Draft Eligibility Status**: `BLOCKED_DRAFT_ELIGIBILITY_SUPERVISED_INPUT_REQUIRED`
- **Source Supervised Input Stub Item Count**: `7`
- **Draft Eligibility Item Count**: `7`
- **Global Draft Generation Enabled**: `False`
- **Global Public Postable**: `False`
- **Ledger Family**: `supervised_input_stub_to_draft_eligibility_gate_precheck_future`

## Required Input Fields

- `intended_audience_lane`
- `content_purpose_category`
- `source_review_notes`
- `risk_review_notes`
- `claim_scope_boundary`
- `manual_operator_decision`

## Missing Required Input Fields

- `intended_audience_lane`
- `content_purpose_category`
- `source_review_notes`
- `risk_review_notes`
- `claim_scope_boundary`
- `manual_operator_decision`

## Eligibility Field Policy

| Field | Required | Source Slot Status | Source Value Status | Current Value | Placeholder Value | Missing | Pending | Draft Eligible |
|---|---|---|---|---|---|---|---|---|
| `intended_audience_lane` | `True` | `STUB_SLOT_PENDING_SUPERVISED_INPUT` | `PENDING_OPERATOR_INPUT` | `null` | `PENDING_OPERATOR_INPUT` | `True` | `True` | `False` |
| `content_purpose_category` | `True` | `STUB_SLOT_PENDING_SUPERVISED_INPUT` | `PENDING_OPERATOR_INPUT` | `null` | `PENDING_OPERATOR_INPUT` | `True` | `True` | `False` |
| `source_review_notes` | `True` | `STUB_SLOT_PENDING_SUPERVISED_INPUT` | `PENDING_OPERATOR_INPUT` | `null` | `PENDING_OPERATOR_INPUT` | `True` | `True` | `False` |
| `risk_review_notes` | `True` | `STUB_SLOT_PENDING_SUPERVISED_INPUT` | `PENDING_OPERATOR_INPUT` | `null` | `PENDING_OPERATOR_INPUT` | `True` | `True` | `False` |
| `claim_scope_boundary` | `True` | `STUB_SLOT_PENDING_SUPERVISED_INPUT` | `PENDING_OPERATOR_INPUT` | `null` | `PENDING_OPERATOR_INPUT` | `True` | `True` | `False` |
| `manual_operator_decision` | `True` | `STUB_SLOT_PENDING_SUPERVISED_INPUT` | `PENDING_OPERATOR_INPUT` | `null` | `PENDING_OPERATOR_INPUT` | `True` | `True` | `False` |

## Draft Generation Policy

| Policy Flag | State |
|---|---|
| `draft_generation_enabled` | `False` |
| `headline_generation_enabled` | `False` |
| `hook_generation_enabled` | `False` |
| `caption_generation_enabled` | `False` |
| `platform_copy_generation_enabled` | `False` |
| `ai_writer_generation_enabled` | `False` |
| `public_postable` | `False` |
| `dispatch_ready` | `False` |
| `draft_storage_enabled` | `False` |
| `operator_input_capture_enabled` | `False` |
| `validation_enabled` | `False` |

## Draft Eligibility Items

| Eligibility Item ID | Source Stub Item ID | Candidate ID | Status | Draft Gen Enabled | Public Postable | Allowed Next Step |
|---|---|---|---|---|---|---|
| `draft_eligibility_item_01_intent_item_STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1` | `supervised_input_stub_01_intent_item_STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1` | `STEP1_OFFICIAL_TEXT_LIVE_PROBE_MANIFEST_V1` | `BLOCKED_DRAFT_ELIGIBILITY_SUPERVISED_INPUT_REQUIRED` | `False` | `False` | `resolve_supervised_input_stub_contract_requirements` |
| `draft_eligibility_item_02_intent_item_STEP1_OFFICIAL_TEXT_SPINE_CONTRACT_V1` | `supervised_input_stub_02_intent_item_STEP1_OFFICIAL_TEXT_SPINE_CONTRACT_V1` | `STEP1_OFFICIAL_TEXT_SPINE_CONTRACT_V1` | `BLOCKED_DRAFT_ELIGIBILITY_SUPERVISED_INPUT_REQUIRED` | `False` | `False` | `resolve_supervised_input_stub_contract_requirements` |
| `draft_eligibility_item_03_intent_item_BEA_BLS_CENSUS_NORMALIZED_CONTRACT_V1` | `supervised_input_stub_03_intent_item_BEA_BLS_CENSUS_NORMALIZED_CONTRACT_V1` | `BEA_BLS_CENSUS_NORMALIZED_CONTRACT_V1` | `BLOCKED_DRAFT_ELIGIBILITY_SUPERVISED_INPUT_REQUIRED` | `False` | `False` | `resolve_supervised_input_stub_contract_requirements` |
| `draft_eligibility_item_04_intent_item_BEA_BLS_CENSUS_NORMALIZED_CANDIDATE_RECORDS_V1` | `supervised_input_stub_04_intent_item_BEA_BLS_CENSUS_NORMALIZED_CANDIDATE_RECORDS_V1` | `BEA_BLS_CENSUS_NORMALIZED_CANDIDATE_RECORDS_V1` | `BLOCKED_DRAFT_ELIGIBILITY_SUPERVISED_INPUT_REQUIRED` | `False` | `False` | `resolve_supervised_input_stub_contract_requirements` |
| `draft_eligibility_item_05_intent_item_BROKER_PROXY_NO_VALUE_SNAPSHOT_MANIFEST_V1` | `supervised_input_stub_05_intent_item_BROKER_PROXY_NO_VALUE_SNAPSHOT_MANIFEST_V1` | `BROKER_PROXY_NO_VALUE_SNAPSHOT_MANIFEST_V1` | `BLOCKED_DRAFT_ELIGIBILITY_SUPERVISED_INPUT_REQUIRED` | `False` | `False` | `resolve_supervised_input_stub_contract_requirements` |
| `draft_eligibility_item_06_intent_item_DATABASE_FOUNDATION_TTL_FRESHNESS_POLICY_CONTRACT_V1` | `supervised_input_stub_06_intent_item_DATABASE_FOUNDATION_TTL_FRESHNESS_POLICY_CONTRACT_V1` | `DATABASE_FOUNDATION_TTL_FRESHNESS_POLICY_CONTRACT_V1` | `BLOCKED_DRAFT_ELIGIBILITY_SUPERVISED_INPUT_REQUIRED` | `False` | `False` | `resolve_supervised_input_stub_contract_requirements` |
| `draft_eligibility_item_07_intent_item_ECONOMIC_PRINTS_SCHEMA_CONTRACT_V1` | `supervised_input_stub_07_intent_item_ECONOMIC_PRINTS_SCHEMA_CONTRACT_V1` | `ECONOMIC_PRINTS_SCHEMA_CONTRACT_V1` | `BLOCKED_DRAFT_ELIGIBILITY_SUPERVISED_INPUT_REQUIRED` | `False` | `False` | `resolve_supervised_input_stub_contract_requirements` |

## Blocked Reasons

- `supervised_input_capture_not_enabled`
- `operator_values_not_collected`
- `draft_eligibility_blocked_by_pending_inputs`

## Missing Requirements

- `operator_must_provide_supervised_inputs`
- `draft_generation_requires_inputs_validation`

## Forbidden Current Actions

- `[FORBIDDEN]` actual_input_capture
- `[FORBIDDEN]` editable_input_fields
- `[FORBIDDEN]` form_submission
- `[FORBIDDEN]` save_capture_approve_generate_controls
- `[FORBIDDEN]` operator_prose_generation
- `[FORBIDDEN]` content_generation
- `[FORBIDDEN]` draft_generation
- `[FORBIDDEN]` headline_hook_caption_generation
- `[FORBIDDEN]` platform_copy_generation
- `[FORBIDDEN]` ai_writer_generation
- `[FORBIDDEN]` draft_storage
- `[FORBIDDEN]` public_posting
- `[FORBIDDEN]` live_dispatch
- `[FORBIDDEN]` provider_or_platform_api_call

## Disallowed Output Enforcement

- `[FORBIDDEN]` raw_record_contents
- `[FORBIDDEN]` source_extracted_facts
- `[FORBIDDEN]` market_values
- `[FORBIDDEN]` narrative_thesis
- `[FORBIDDEN]` headline
- `[FORBIDDEN]` hook
- `[FORBIDDEN]` caption
- `[FORBIDDEN]` draft_paragraph
- `[FORBIDDEN]` platform_copy
- `[FORBIDDEN]` prediction
- `[FORBIDDEN]` recommendation
- `[FORBIDDEN]` buy_sell_hold_sizing_signal_language

## Truth Protection Flags

| Flag | State |
|---|---|
| `dqr_cleared_by_contentops` | `False` |
| `readiness_cleared_by_contentops` | `False` |
| `current_truth_promoted` | `False` |
| `numeric_truth_promoted` | `False` |
| `market_data_promoted` | `False` |
| `draft_truth_promoted` | `False` |

## Safety Flags

| Flag | State |
|---|---|
| `live_api_called` | `False` |
| `provider_api_called` | `False` |
| `platform_api_called` | `False` |
| `credential_hydrated` | `False` |
| `secret_values_observed` | `False` |
| `env_secret_read` | `False` |
| `scheduler_enabled` | `False` |
| `scraping_performed` | `False` |
| `dispatch_ready` | `False` |
| `public_postable` | `False` |
| `actual_operator_input_capture_enabled` | `False` |
| `editable_ui_enabled` | `False` |
| `persistence_enabled` | `False` |
| `draft_generation_enabled` | `False` |
| `ai_writer_generation_enabled` | `False` |

## Validation Rules

- `supervised_input_capture_must_be_enabled`
- `operator_inputs_must_be_fully_collected`
- `draft_generation_must_remain_disabled_until_inputs_provided`
- `public_postable_must_remain_disabled_until_signoff`

## Navigation

- **Allowed Next Step**: `resolve_supervised_input_stub_contract_requirements`
- **Next Recommended Task**: `TASK_CONTENTOPS_0175BT_DRAFT_ELIGIBILITY_GATE_TO_V5_READONLY_STATUS_PANEL_BINDING_V0`
