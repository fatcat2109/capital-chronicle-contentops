# Operator Decision Gate to Manual Export Precheck Contract

> [!IMPORTANT]
> This is a manual export precheck contract report for schema validation only.
> It defines blocked precheck records and does not perform manual exports, approvals, or publications.
> It cannot create export files, clipboard payloads, downloads, dispatches, schedules, or platform API calls.

- **Task Label**: `TASK_CONTENTOPS_0175AR_OPERATOR_DECISION_GATE_TO_MANUAL_EXPORT_PRECHECK_V0`
- **Matrix Version**: `0175AR_OPERATOR_DECISION_GATE_TO_MANUAL_EXPORT_PRECHECK_V1`
- **Source Baseline Commit**: `68a7e425d229d7876fdfa1f37a65f3ef8c388849`
- **Packet Hash**: `116b69959db0b212383a33bf12b1b2f06ab1eafd99b5977cb231e825f86b4d11`
- **Ledger Family**: `operator_decision_gate_to_manual_export_precheck_future`
- **Next Required Gate**: `lane_c_platform_manual_export_precheck_to_export_packet_gate`

## Invariant Validation Safety Flags

| Invariant Flag | Required State | Status |
|---|---|---|
| `local_only` | `True` | ✅ |
| `fixture_only` | `True` | ✅ |
| `schema_only` | `True` | ✅ |
| `manual_export_precheck_only` | `True` | ✅ |
| `decision_gate_only` | `True` | ✅ |
| `network_performed` | `False` | ✅ |
| `env_read` | `False` | ✅ |
| `credential_values_loaded` | `False` | ✅ |
| `platform_api_called` | `False` | ✅ |
| `provider_api_called` | `False` | ✅ |
| `account_binding_active` | `False` | ✅ |
| `scheduler_enabled` | `False` | ✅ |
| `autonomous_posting` | `False` | ✅ |
| `autonomous_reply_or_dm` | `False` | ✅ |
| `scraping` | `False` | ✅ |
| `ingestion_repo_mutated` | `False` | ✅ |
| `dqr_cleared_by_contentops` | `False` | ✅ |
| `readiness_cleared_by_contentops` | `False` | ✅ |
| `current_truth_promoted` | `False` | ✅ |
| `public_postable` | `False` | ✅ |
| `dispatch_ready` | `False` | ✅ |
| `platform_payload_created` | `False` | ✅ |
| `publishable_payload_created` | `False` | ✅ |
| `export_ready` | `False` | ✅ |
| `manual_export_allowed` | `False` | ✅ |
| `export_file_created` | `False` | ✅ |
| `clipboard_payload_created` | `False` | ✅ |
| `download_artifact_created` | `False` | ✅ |
| `approval_granted` | `False` | ✅ |
| `approved_for_publication` | `False` | ✅ |
| `operator_approval_granted` | `False` | ✅ |
| `operator_identity_bound` | `False` | ✅ |
| `operator_signature_present` | `False` | ✅ |
| `payload_hash_locked` | `False` | ✅ |
| `financial_advice` | `False` | ✅ |
| `signal_language` | `False` | ✅ |
| `broker_order_execution` | `False` | ✅ |
| `raw_vendor_redistribution` | `False` | ✅ |
| `approved_internal_alpha_artifacts_available` | `False` | ✅ |
| `publishable_text` | `False` | ✅ |
| `platform_ready` | `False` | ✅ |

## Precheck Summary Counts

- **Registered Precheck Records**: `10`
- **Registered Precheck Targets**: `10`
- **Precheck Rules Configured**: `21`
- **Evidence Requirements Defined**: `6`

## Blocked Capabilities & Missing Gates

### Blocked Capabilities
- `live_publishing_dispatch`
- `autonomous_reply_automation`
- `live_credential_hydration`
- `active_scheduler_triggers`
- `manual_review_export`

### Missing Future Gates
- `lane_c_platform_manual_export_precheck_to_export_packet_gate`
- `production_key_vault_decrypter`
- `live_operator_signature_vault`

## Precheck Target Configurations

| Platform Target ID | Export Target Type | Description |
|---|---|---|
| `x` | `x_manual_copy_precheck` | Precheck for manual copy to X platform |
| `telegram_channel_destination` | `telegram_channel_manual_copy_precheck` | Precheck for manual copy to Telegram channel |
| `telegram_remote_operator` | `telegram_remote_operator_review_log_precheck` | Precheck for Telegram operator remote log |
| `substack` | `substack_manual_markdown_precheck` | Precheck for manual copy of Substack markdown copy |
| `linkedin` | `linkedin_manual_copy_precheck` | Precheck for manual copy to LinkedIn professional network |
| `threads` | `threads_manual_copy_precheck` | Precheck for manual copy to Meta Threads |
| `instagram` | `instagram_caption_media_manual_precheck` | Precheck for manual copy of Instagram media caption |
| `facebook_page` | `facebook_page_manual_copy_precheck` | Precheck for manual copy to Facebook page |
| `tiktok` | `tiktok_caption_video_manual_precheck` | Precheck for manual copy of TikTok video caption |
| `youtube` | `youtube_metadata_manual_precheck` | Precheck for manual copy of YouTube metadata descriptions |

## Platform Operator Decision Gate to Manual Export Precheck Records

### Precheck Record: `manual_export_precheck_x`

- **Source Decision Gate ID**: `decision_gate_x`
- **Source Bundle Item ID**: `bundle_item_x`
- **Platform Target ID**: `x`
- **Platform Family**: `x_microblog`
- **Precheck Status**: `manual_export_precheck_blocked`
- **Export Target Type**: `x_manual_copy_precheck`
- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Manual Export Gate**: `manual_export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Precheck Evaluation Rules (All Enforced)

| Rule ID | Description | Passed Status |
|---|---|---|
| `no_export_file_created` | Enforce rule: no export file created | `True` |
| `no_clipboard_payload_created` | Enforce rule: no clipboard payload created | `True` |
| `no_download_artifact_created` | Enforce rule: no download artifact created | `True` |
| `no_publishable_payload_created` | Enforce rule: no publishable payload created | `True` |
| `no_platform_payload_created` | Enforce rule: no platform payload created | `True` |
| `no_platform_api_call` | Enforce rule: no platform api call | `True` |
| `no_credential_or_env_read` | Enforce rule: no credential or env read | `True` |
| `no_account_binding_active` | Enforce rule: no account binding active | `True` |
| `no_scheduler` | Enforce rule: no scheduler | `True` |
| `no_autonomous_posting` | Enforce rule: no autonomous posting | `True` |
| `no_autonomous_reply_or_dm` | Enforce rule: no autonomous reply or dm | `True` |
| `no_scraping` | Enforce rule: no scraping | `True` |
| `no_financial_advice` | Enforce rule: no financial advice | `True` |
| `no_signal_language` | Enforce rule: no signal language | `True` |
| `no_market_number_fabrication` | Enforce rule: no market number fabrication | `True` |
| `preserve_citation_requirements` | Enforce rule: preserve citation requirements | `True` |
| `preserve_limitations` | Enforce rule: preserve limitations | `True` |
| `preserve_dqr_readiness_blocks` | Enforce rule: preserve dqr readiness blocks | `True` |
| `require_operator_signature` | Enforce rule: require operator signature | `True` |
| `require_payload_hash_lock` | Enforce rule: require payload hash lock | `True` |
| `require_manual_export_gate` | Enforce rule: require manual export gate | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |
| `evidence_manual_export_gate_cleared` | Verify operator manual export gate is cleared. | `False` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_export_gate`
- `blocked_no_publishable_payload`

### Precheck Record: `manual_export_precheck_telegram_channel_destination`

- **Source Decision Gate ID**: `decision_gate_telegram_channel_destination`
- **Source Bundle Item ID**: `bundle_item_telegram_channel_destination`
- **Platform Target ID**: `telegram_channel_destination`
- **Platform Family**: `telegram_chat`
- **Precheck Status**: `manual_export_precheck_blocked`
- **Export Target Type**: `telegram_channel_manual_copy_precheck`
- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Manual Export Gate**: `manual_export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Precheck Evaluation Rules (All Enforced)

| Rule ID | Description | Passed Status |
|---|---|---|
| `no_export_file_created` | Enforce rule: no export file created | `True` |
| `no_clipboard_payload_created` | Enforce rule: no clipboard payload created | `True` |
| `no_download_artifact_created` | Enforce rule: no download artifact created | `True` |
| `no_publishable_payload_created` | Enforce rule: no publishable payload created | `True` |
| `no_platform_payload_created` | Enforce rule: no platform payload created | `True` |
| `no_platform_api_call` | Enforce rule: no platform api call | `True` |
| `no_credential_or_env_read` | Enforce rule: no credential or env read | `True` |
| `no_account_binding_active` | Enforce rule: no account binding active | `True` |
| `no_scheduler` | Enforce rule: no scheduler | `True` |
| `no_autonomous_posting` | Enforce rule: no autonomous posting | `True` |
| `no_autonomous_reply_or_dm` | Enforce rule: no autonomous reply or dm | `True` |
| `no_scraping` | Enforce rule: no scraping | `True` |
| `no_financial_advice` | Enforce rule: no financial advice | `True` |
| `no_signal_language` | Enforce rule: no signal language | `True` |
| `no_market_number_fabrication` | Enforce rule: no market number fabrication | `True` |
| `preserve_citation_requirements` | Enforce rule: preserve citation requirements | `True` |
| `preserve_limitations` | Enforce rule: preserve limitations | `True` |
| `preserve_dqr_readiness_blocks` | Enforce rule: preserve dqr readiness blocks | `True` |
| `require_operator_signature` | Enforce rule: require operator signature | `True` |
| `require_payload_hash_lock` | Enforce rule: require payload hash lock | `True` |
| `require_manual_export_gate` | Enforce rule: require manual export gate | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |
| `evidence_manual_export_gate_cleared` | Verify operator manual export gate is cleared. | `False` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_export_gate`
- `blocked_no_publishable_payload`

### Precheck Record: `manual_export_precheck_telegram_remote_operator`

- **Source Decision Gate ID**: `decision_gate_telegram_remote_operator`
- **Source Bundle Item ID**: `bundle_item_telegram_remote_operator`
- **Platform Target ID**: `telegram_remote_operator`
- **Platform Family**: `telegram_chat`
- **Precheck Status**: `manual_export_precheck_blocked`
- **Export Target Type**: `telegram_remote_operator_review_log_precheck`
- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Manual Export Gate**: `manual_export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Precheck Evaluation Rules (All Enforced)

| Rule ID | Description | Passed Status |
|---|---|---|
| `no_export_file_created` | Enforce rule: no export file created | `True` |
| `no_clipboard_payload_created` | Enforce rule: no clipboard payload created | `True` |
| `no_download_artifact_created` | Enforce rule: no download artifact created | `True` |
| `no_publishable_payload_created` | Enforce rule: no publishable payload created | `True` |
| `no_platform_payload_created` | Enforce rule: no platform payload created | `True` |
| `no_platform_api_call` | Enforce rule: no platform api call | `True` |
| `no_credential_or_env_read` | Enforce rule: no credential or env read | `True` |
| `no_account_binding_active` | Enforce rule: no account binding active | `True` |
| `no_scheduler` | Enforce rule: no scheduler | `True` |
| `no_autonomous_posting` | Enforce rule: no autonomous posting | `True` |
| `no_autonomous_reply_or_dm` | Enforce rule: no autonomous reply or dm | `True` |
| `no_scraping` | Enforce rule: no scraping | `True` |
| `no_financial_advice` | Enforce rule: no financial advice | `True` |
| `no_signal_language` | Enforce rule: no signal language | `True` |
| `no_market_number_fabrication` | Enforce rule: no market number fabrication | `True` |
| `preserve_citation_requirements` | Enforce rule: preserve citation requirements | `True` |
| `preserve_limitations` | Enforce rule: preserve limitations | `True` |
| `preserve_dqr_readiness_blocks` | Enforce rule: preserve dqr readiness blocks | `True` |
| `require_operator_signature` | Enforce rule: require operator signature | `True` |
| `require_payload_hash_lock` | Enforce rule: require payload hash lock | `True` |
| `require_manual_export_gate` | Enforce rule: require manual export gate | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |
| `evidence_manual_export_gate_cleared` | Verify operator manual export gate is cleared. | `False` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_export_gate`
- `blocked_no_publishable_payload`

### Precheck Record: `manual_export_precheck_substack`

- **Source Decision Gate ID**: `decision_gate_substack`
- **Source Bundle Item ID**: `bundle_item_substack`
- **Platform Target ID**: `substack`
- **Platform Family**: `substack_newsletter`
- **Precheck Status**: `manual_export_precheck_blocked`
- **Export Target Type**: `substack_manual_markdown_precheck`
- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Manual Export Gate**: `manual_export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Precheck Evaluation Rules (All Enforced)

| Rule ID | Description | Passed Status |
|---|---|---|
| `no_export_file_created` | Enforce rule: no export file created | `True` |
| `no_clipboard_payload_created` | Enforce rule: no clipboard payload created | `True` |
| `no_download_artifact_created` | Enforce rule: no download artifact created | `True` |
| `no_publishable_payload_created` | Enforce rule: no publishable payload created | `True` |
| `no_platform_payload_created` | Enforce rule: no platform payload created | `True` |
| `no_platform_api_call` | Enforce rule: no platform api call | `True` |
| `no_credential_or_env_read` | Enforce rule: no credential or env read | `True` |
| `no_account_binding_active` | Enforce rule: no account binding active | `True` |
| `no_scheduler` | Enforce rule: no scheduler | `True` |
| `no_autonomous_posting` | Enforce rule: no autonomous posting | `True` |
| `no_autonomous_reply_or_dm` | Enforce rule: no autonomous reply or dm | `True` |
| `no_scraping` | Enforce rule: no scraping | `True` |
| `no_financial_advice` | Enforce rule: no financial advice | `True` |
| `no_signal_language` | Enforce rule: no signal language | `True` |
| `no_market_number_fabrication` | Enforce rule: no market number fabrication | `True` |
| `preserve_citation_requirements` | Enforce rule: preserve citation requirements | `True` |
| `preserve_limitations` | Enforce rule: preserve limitations | `True` |
| `preserve_dqr_readiness_blocks` | Enforce rule: preserve dqr readiness blocks | `True` |
| `require_operator_signature` | Enforce rule: require operator signature | `True` |
| `require_payload_hash_lock` | Enforce rule: require payload hash lock | `True` |
| `require_manual_export_gate` | Enforce rule: require manual export gate | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |
| `evidence_manual_export_gate_cleared` | Verify operator manual export gate is cleared. | `False` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_export_gate`
- `blocked_no_publishable_payload`

### Precheck Record: `manual_export_precheck_linkedin`

- **Source Decision Gate ID**: `decision_gate_linkedin`
- **Source Bundle Item ID**: `bundle_item_linkedin`
- **Platform Target ID**: `linkedin`
- **Platform Family**: `linkedin_professional`
- **Precheck Status**: `manual_export_precheck_blocked`
- **Export Target Type**: `linkedin_manual_copy_precheck`
- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Manual Export Gate**: `manual_export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Precheck Evaluation Rules (All Enforced)

| Rule ID | Description | Passed Status |
|---|---|---|
| `no_export_file_created` | Enforce rule: no export file created | `True` |
| `no_clipboard_payload_created` | Enforce rule: no clipboard payload created | `True` |
| `no_download_artifact_created` | Enforce rule: no download artifact created | `True` |
| `no_publishable_payload_created` | Enforce rule: no publishable payload created | `True` |
| `no_platform_payload_created` | Enforce rule: no platform payload created | `True` |
| `no_platform_api_call` | Enforce rule: no platform api call | `True` |
| `no_credential_or_env_read` | Enforce rule: no credential or env read | `True` |
| `no_account_binding_active` | Enforce rule: no account binding active | `True` |
| `no_scheduler` | Enforce rule: no scheduler | `True` |
| `no_autonomous_posting` | Enforce rule: no autonomous posting | `True` |
| `no_autonomous_reply_or_dm` | Enforce rule: no autonomous reply or dm | `True` |
| `no_scraping` | Enforce rule: no scraping | `True` |
| `no_financial_advice` | Enforce rule: no financial advice | `True` |
| `no_signal_language` | Enforce rule: no signal language | `True` |
| `no_market_number_fabrication` | Enforce rule: no market number fabrication | `True` |
| `preserve_citation_requirements` | Enforce rule: preserve citation requirements | `True` |
| `preserve_limitations` | Enforce rule: preserve limitations | `True` |
| `preserve_dqr_readiness_blocks` | Enforce rule: preserve dqr readiness blocks | `True` |
| `require_operator_signature` | Enforce rule: require operator signature | `True` |
| `require_payload_hash_lock` | Enforce rule: require payload hash lock | `True` |
| `require_manual_export_gate` | Enforce rule: require manual export gate | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |
| `evidence_manual_export_gate_cleared` | Verify operator manual export gate is cleared. | `False` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_export_gate`
- `blocked_no_publishable_payload`

### Precheck Record: `manual_export_precheck_threads`

- **Source Decision Gate ID**: `decision_gate_threads`
- **Source Bundle Item ID**: `bundle_item_threads`
- **Platform Target ID**: `threads`
- **Platform Family**: `threads_microblog`
- **Precheck Status**: `manual_export_precheck_blocked`
- **Export Target Type**: `threads_manual_copy_precheck`
- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Manual Export Gate**: `manual_export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Precheck Evaluation Rules (All Enforced)

| Rule ID | Description | Passed Status |
|---|---|---|
| `no_export_file_created` | Enforce rule: no export file created | `True` |
| `no_clipboard_payload_created` | Enforce rule: no clipboard payload created | `True` |
| `no_download_artifact_created` | Enforce rule: no download artifact created | `True` |
| `no_publishable_payload_created` | Enforce rule: no publishable payload created | `True` |
| `no_platform_payload_created` | Enforce rule: no platform payload created | `True` |
| `no_platform_api_call` | Enforce rule: no platform api call | `True` |
| `no_credential_or_env_read` | Enforce rule: no credential or env read | `True` |
| `no_account_binding_active` | Enforce rule: no account binding active | `True` |
| `no_scheduler` | Enforce rule: no scheduler | `True` |
| `no_autonomous_posting` | Enforce rule: no autonomous posting | `True` |
| `no_autonomous_reply_or_dm` | Enforce rule: no autonomous reply or dm | `True` |
| `no_scraping` | Enforce rule: no scraping | `True` |
| `no_financial_advice` | Enforce rule: no financial advice | `True` |
| `no_signal_language` | Enforce rule: no signal language | `True` |
| `no_market_number_fabrication` | Enforce rule: no market number fabrication | `True` |
| `preserve_citation_requirements` | Enforce rule: preserve citation requirements | `True` |
| `preserve_limitations` | Enforce rule: preserve limitations | `True` |
| `preserve_dqr_readiness_blocks` | Enforce rule: preserve dqr readiness blocks | `True` |
| `require_operator_signature` | Enforce rule: require operator signature | `True` |
| `require_payload_hash_lock` | Enforce rule: require payload hash lock | `True` |
| `require_manual_export_gate` | Enforce rule: require manual export gate | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |
| `evidence_manual_export_gate_cleared` | Verify operator manual export gate is cleared. | `False` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_export_gate`
- `blocked_no_publishable_payload`

### Precheck Record: `manual_export_precheck_instagram`

- **Source Decision Gate ID**: `decision_gate_instagram`
- **Source Bundle Item ID**: `bundle_item_instagram`
- **Platform Target ID**: `instagram`
- **Platform Family**: `instagram_media`
- **Precheck Status**: `manual_export_precheck_blocked`
- **Export Target Type**: `instagram_caption_media_manual_precheck`
- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Manual Export Gate**: `manual_export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Precheck Evaluation Rules (All Enforced)

| Rule ID | Description | Passed Status |
|---|---|---|
| `no_export_file_created` | Enforce rule: no export file created | `True` |
| `no_clipboard_payload_created` | Enforce rule: no clipboard payload created | `True` |
| `no_download_artifact_created` | Enforce rule: no download artifact created | `True` |
| `no_publishable_payload_created` | Enforce rule: no publishable payload created | `True` |
| `no_platform_payload_created` | Enforce rule: no platform payload created | `True` |
| `no_platform_api_call` | Enforce rule: no platform api call | `True` |
| `no_credential_or_env_read` | Enforce rule: no credential or env read | `True` |
| `no_account_binding_active` | Enforce rule: no account binding active | `True` |
| `no_scheduler` | Enforce rule: no scheduler | `True` |
| `no_autonomous_posting` | Enforce rule: no autonomous posting | `True` |
| `no_autonomous_reply_or_dm` | Enforce rule: no autonomous reply or dm | `True` |
| `no_scraping` | Enforce rule: no scraping | `True` |
| `no_financial_advice` | Enforce rule: no financial advice | `True` |
| `no_signal_language` | Enforce rule: no signal language | `True` |
| `no_market_number_fabrication` | Enforce rule: no market number fabrication | `True` |
| `preserve_citation_requirements` | Enforce rule: preserve citation requirements | `True` |
| `preserve_limitations` | Enforce rule: preserve limitations | `True` |
| `preserve_dqr_readiness_blocks` | Enforce rule: preserve dqr readiness blocks | `True` |
| `require_operator_signature` | Enforce rule: require operator signature | `True` |
| `require_payload_hash_lock` | Enforce rule: require payload hash lock | `True` |
| `require_manual_export_gate` | Enforce rule: require manual export gate | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |
| `evidence_manual_export_gate_cleared` | Verify operator manual export gate is cleared. | `False` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_export_gate`
- `blocked_no_publishable_payload`

### Precheck Record: `manual_export_precheck_facebook_page`

- **Source Decision Gate ID**: `decision_gate_facebook_page`
- **Source Bundle Item ID**: `bundle_item_facebook_page`
- **Platform Target ID**: `facebook_page`
- **Platform Family**: `facebook_page_media`
- **Precheck Status**: `manual_export_precheck_blocked`
- **Export Target Type**: `facebook_page_manual_copy_precheck`
- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Manual Export Gate**: `manual_export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Precheck Evaluation Rules (All Enforced)

| Rule ID | Description | Passed Status |
|---|---|---|
| `no_export_file_created` | Enforce rule: no export file created | `True` |
| `no_clipboard_payload_created` | Enforce rule: no clipboard payload created | `True` |
| `no_download_artifact_created` | Enforce rule: no download artifact created | `True` |
| `no_publishable_payload_created` | Enforce rule: no publishable payload created | `True` |
| `no_platform_payload_created` | Enforce rule: no platform payload created | `True` |
| `no_platform_api_call` | Enforce rule: no platform api call | `True` |
| `no_credential_or_env_read` | Enforce rule: no credential or env read | `True` |
| `no_account_binding_active` | Enforce rule: no account binding active | `True` |
| `no_scheduler` | Enforce rule: no scheduler | `True` |
| `no_autonomous_posting` | Enforce rule: no autonomous posting | `True` |
| `no_autonomous_reply_or_dm` | Enforce rule: no autonomous reply or dm | `True` |
| `no_scraping` | Enforce rule: no scraping | `True` |
| `no_financial_advice` | Enforce rule: no financial advice | `True` |
| `no_signal_language` | Enforce rule: no signal language | `True` |
| `no_market_number_fabrication` | Enforce rule: no market number fabrication | `True` |
| `preserve_citation_requirements` | Enforce rule: preserve citation requirements | `True` |
| `preserve_limitations` | Enforce rule: preserve limitations | `True` |
| `preserve_dqr_readiness_blocks` | Enforce rule: preserve dqr readiness blocks | `True` |
| `require_operator_signature` | Enforce rule: require operator signature | `True` |
| `require_payload_hash_lock` | Enforce rule: require payload hash lock | `True` |
| `require_manual_export_gate` | Enforce rule: require manual export gate | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |
| `evidence_manual_export_gate_cleared` | Verify operator manual export gate is cleared. | `False` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_export_gate`
- `blocked_no_publishable_payload`

### Precheck Record: `manual_export_precheck_tiktok`

- **Source Decision Gate ID**: `decision_gate_tiktok`
- **Source Bundle Item ID**: `bundle_item_tiktok`
- **Platform Target ID**: `tiktok`
- **Platform Family**: `tiktok_video`
- **Precheck Status**: `manual_export_precheck_blocked`
- **Export Target Type**: `tiktok_caption_video_manual_precheck`
- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Manual Export Gate**: `manual_export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Precheck Evaluation Rules (All Enforced)

| Rule ID | Description | Passed Status |
|---|---|---|
| `no_export_file_created` | Enforce rule: no export file created | `True` |
| `no_clipboard_payload_created` | Enforce rule: no clipboard payload created | `True` |
| `no_download_artifact_created` | Enforce rule: no download artifact created | `True` |
| `no_publishable_payload_created` | Enforce rule: no publishable payload created | `True` |
| `no_platform_payload_created` | Enforce rule: no platform payload created | `True` |
| `no_platform_api_call` | Enforce rule: no platform api call | `True` |
| `no_credential_or_env_read` | Enforce rule: no credential or env read | `True` |
| `no_account_binding_active` | Enforce rule: no account binding active | `True` |
| `no_scheduler` | Enforce rule: no scheduler | `True` |
| `no_autonomous_posting` | Enforce rule: no autonomous posting | `True` |
| `no_autonomous_reply_or_dm` | Enforce rule: no autonomous reply or dm | `True` |
| `no_scraping` | Enforce rule: no scraping | `True` |
| `no_financial_advice` | Enforce rule: no financial advice | `True` |
| `no_signal_language` | Enforce rule: no signal language | `True` |
| `no_market_number_fabrication` | Enforce rule: no market number fabrication | `True` |
| `preserve_citation_requirements` | Enforce rule: preserve citation requirements | `True` |
| `preserve_limitations` | Enforce rule: preserve limitations | `True` |
| `preserve_dqr_readiness_blocks` | Enforce rule: preserve dqr readiness blocks | `True` |
| `require_operator_signature` | Enforce rule: require operator signature | `True` |
| `require_payload_hash_lock` | Enforce rule: require payload hash lock | `True` |
| `require_manual_export_gate` | Enforce rule: require manual export gate | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |
| `evidence_manual_export_gate_cleared` | Verify operator manual export gate is cleared. | `False` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_export_gate`
- `blocked_no_publishable_payload`

### Precheck Record: `manual_export_precheck_youtube`

- **Source Decision Gate ID**: `decision_gate_youtube`
- **Source Bundle Item ID**: `bundle_item_youtube`
- **Platform Target ID**: `youtube`
- **Platform Family**: `youtube_video`
- **Precheck Status**: `manual_export_precheck_blocked`
- **Export Target Type**: `youtube_metadata_manual_precheck`
- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Operator Identity Status**: `identity_required_but_unbound`
- **Operator Signature Status**: `signature_required_but_missing`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Citation Status**: `citation_rendering_required_but_pending`
- **Limitation Status**: `limitation_rendering_required_but_pending`
- **DQR Status**: `dqr_unresolved`
- **Readiness Status**: `readiness_unresolved`
- **Current Truth Status**: `current_truth_unpromoted`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Manual Export Gate**: `manual_export_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Safety Invariants Status

- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Precheck Evaluation Rules (All Enforced)

| Rule ID | Description | Passed Status |
|---|---|---|
| `no_export_file_created` | Enforce rule: no export file created | `True` |
| `no_clipboard_payload_created` | Enforce rule: no clipboard payload created | `True` |
| `no_download_artifact_created` | Enforce rule: no download artifact created | `True` |
| `no_publishable_payload_created` | Enforce rule: no publishable payload created | `True` |
| `no_platform_payload_created` | Enforce rule: no platform payload created | `True` |
| `no_platform_api_call` | Enforce rule: no platform api call | `True` |
| `no_credential_or_env_read` | Enforce rule: no credential or env read | `True` |
| `no_account_binding_active` | Enforce rule: no account binding active | `True` |
| `no_scheduler` | Enforce rule: no scheduler | `True` |
| `no_autonomous_posting` | Enforce rule: no autonomous posting | `True` |
| `no_autonomous_reply_or_dm` | Enforce rule: no autonomous reply or dm | `True` |
| `no_scraping` | Enforce rule: no scraping | `True` |
| `no_financial_advice` | Enforce rule: no financial advice | `True` |
| `no_signal_language` | Enforce rule: no signal language | `True` |
| `no_market_number_fabrication` | Enforce rule: no market number fabrication | `True` |
| `preserve_citation_requirements` | Enforce rule: preserve citation requirements | `True` |
| `preserve_limitations` | Enforce rule: preserve limitations | `True` |
| `preserve_dqr_readiness_blocks` | Enforce rule: preserve dqr readiness blocks | `True` |
| `require_operator_signature` | Enforce rule: require operator signature | `True` |
| `require_payload_hash_lock` | Enforce rule: require payload hash lock | `True` |
| `require_manual_export_gate` | Enforce rule: require manual export gate | `True` |

#### Evidence Requirements (Pending)

| Requirement ID | Description | Satisfied |
|---|---|---|
| `evidence_operator_identity_verified` | Verify operator identity matches key binding registry. | `False` |
| `evidence_approval_signature_verified` | Verify cryptographic approval signature matches operator key. | `False` |
| `evidence_payload_hash_lock_confirmed` | Verify payload hash lock matches draft variant snapshot. | `False` |
| `evidence_citation_clearance_verified` | Verify citation references are validated. | `False` |
| `evidence_limitation_ack_verified` | Verify limitation acknowledgement is logged. | `False` |
| `evidence_manual_export_gate_cleared` | Verify operator manual export gate is cleared. | `False` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_export_gate`
- `blocked_no_publishable_payload`
