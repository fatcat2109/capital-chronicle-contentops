# Manual Publish Record Precheck to Record Stub Contract

> [!IMPORTANT]
> This is a manual publish record stub contract, not a manual publish record and not metrics logging.
> It creates blocked stub metadata and non-public placeholders only.
> It preserves citation, limitation, DQR/readiness, operator identity, signature, hash-lock, publish-record-gate, account-binding, credential, and dispatch-gate requirements.
> It cannot create publish records, publication URLs, platform post IDs, timestamps, metrics, files, clipboard payloads, downloads, approvals, exports, publishable payloads, dispatches, schedules, or platform/API calls.

- **Task Label**: `TASK_CONTENTOPS_0175AV_MANUAL_PUBLISH_RECORD_PRECHECK_TO_RECORD_STUB_V0`
- **Matrix Version**: `0175AV_MANUAL_PUBLISH_RECORD_PRECHECK_TO_RECORD_STUB_V1`
- **Source Baseline Commit**: `0c817cdfef6d71fe5e6f4b20040665b157d50596`
- **Packet Hash**: `908f1103b965ba0a9f2d6531da2d76bab3d9e23346d0a72b4d6df7966eccb2e4`
- **Ledger Family**: `manual_publish_record_precheck_to_record_stub_future`
- **Next Required Gate**: `lane_c_platform_manual_publish_stub_to_metrics_precheck`

## Invariant Validation Safety Flags

| Invariant Flag | Required State | Status |
|---|---|---|
| `local_only` | `True` | ✅ |
| `fixture_only` | `True` | ✅ |
| `schema_only` | `True` | ✅ |
| `manual_publish_record_stub_only` | `True` | ✅ |
| `manual_publish_record_precheck_only` | `True` | ✅ |
| `operator_audit_summary_only` | `True` | ✅ |
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
| `manual_publish_record_allowed` | `False` | ✅ |
| `manual_publish_record_created` | `False` | ✅ |
| `platform_publication_url_recorded` | `False` | ✅ |
| `platform_post_id_recorded` | `False` | ✅ |
| `external_publish_timestamp_recorded` | `False` | ✅ |
| `public_metrics_recorded` | `False` | ✅ |
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

## Stub summary counts

- **Registered Manual Publish Record Stubs**: `10`
- **Registered Manual Publish Targets**: `10`
- **Invariants Checked**: `26`
- **Placeholder Fields Defined**: `40`

## Blocked Capabilities & Missing Gates

### Blocked Capabilities
- `live_publishing_dispatch`
- `autonomous_reply_automation`
- `live_credential_hydration`
- `active_scheduler_triggers`
- `manual_review_export`

### Missing Future Gates
- `lane_c_platform_manual_publish_stub_to_metrics_precheck`
- `production_key_vault_decrypter`
- `live_operator_signature_vault`

## Manual Publish target configurations

| Platform Target ID | Manual Publish Record Type | Description |
|---|---|---|
| `x` | `x_manual_publish_record_stub` | Manual publish record stub for X platform |
| `telegram_channel_destination` | `telegram_channel_manual_publish_record_stub` | Manual publish record stub for Telegram channel |
| `telegram_remote_operator` | `telegram_remote_operator_log_record_stub` | Manual publish record stub for Telegram remote operator |
| `substack` | `substack_manual_publish_record_stub` | Manual publish record stub for Substack |
| `linkedin` | `linkedin_manual_publish_record_stub` | Manual publish record stub for LinkedIn |
| `threads` | `threads_manual_publish_record_stub` | Manual publish record stub for Meta Threads |
| `instagram` | `instagram_manual_publish_record_stub` | Manual publish record stub for Instagram |
| `facebook_page` | `facebook_page_manual_publish_record_stub` | Manual publish record stub for Facebook Page |
| `tiktok` | `tiktok_manual_publish_record_stub` | Manual publish record stub for TikTok |
| `youtube` | `youtube_manual_publish_record_stub` | Manual publish record stub for YouTube |

## Platform Manual Publish Record Stubs

### Record Stub: `manual_publish_record_stub_x`

- **Source Manual Publish Precheck ID**: `manual_publish_record_precheck_x`
- **Source Audit Summary ID**: `audit_summary_x`
- **Source Export Packet Stub ID**: `export_packet_stub_x`
- **Source Manual Export Precheck ID**: `manual_export_precheck_x`
- **Source Decision Gate ID**: `decision_gate_x`
- **Platform Target ID**: `x`
- **Platform Family**: `x_microblog`
- **Record Stub Status**: `manual_publish_record_stub_blocked`
- **Publish Record Target Type**: `x_manual_publish_record_precheck`
- **Manual Publish Record Type**: `x_manual_publish_record_stub`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Fields

| Field Name | Placeholder Value | Requires Human Logging |
|---|---|---|
| `platform_name_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: x.platform_name_stub]` | `True` |
| `publication_url_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: x.publication_url_stub]` | `True` |
| `post_id_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: x.post_id_stub]` | `True` |
| `published_at_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: x.published_at_stub]` | `True` |
| `operator_note_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: x.operator_note_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_external_publish_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external publish timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public metrics remain unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_publish_record_gate` | `required` | `required` | `True` | Verified manual publish record gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`

### Record Stub: `manual_publish_record_stub_telegram_channel_destination`

- **Source Manual Publish Precheck ID**: `manual_publish_record_precheck_telegram_channel_destination`
- **Source Audit Summary ID**: `audit_summary_telegram_channel_destination`
- **Source Export Packet Stub ID**: `export_packet_stub_telegram_channel_destination`
- **Source Manual Export Precheck ID**: `manual_export_precheck_telegram_channel_destination`
- **Source Decision Gate ID**: `decision_gate_telegram_channel_destination`
- **Platform Target ID**: `telegram_channel_destination`
- **Platform Family**: `telegram_chat`
- **Record Stub Status**: `manual_publish_record_stub_blocked`
- **Publish Record Target Type**: `telegram_channel_manual_publish_record_precheck`
- **Manual Publish Record Type**: `telegram_channel_manual_publish_record_stub`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Fields

| Field Name | Placeholder Value | Requires Human Logging |
|---|---|---|
| `platform_name_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: telegram_channel_destination.platform_name_stub]` | `True` |
| `message_url_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: telegram_channel_destination.message_url_stub]` | `True` |
| `chat_id_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: telegram_channel_destination.chat_id_stub]` | `True` |
| `message_id_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: telegram_channel_destination.message_id_stub]` | `True` |
| `published_at_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: telegram_channel_destination.published_at_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_external_publish_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external publish timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public metrics remain unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_publish_record_gate` | `required` | `required` | `True` | Verified manual publish record gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`

### Record Stub: `manual_publish_record_stub_telegram_remote_operator`

- **Source Manual Publish Precheck ID**: `manual_publish_record_precheck_telegram_remote_operator`
- **Source Audit Summary ID**: `audit_summary_telegram_remote_operator`
- **Source Export Packet Stub ID**: `export_packet_stub_telegram_remote_operator`
- **Source Manual Export Precheck ID**: `manual_export_precheck_telegram_remote_operator`
- **Source Decision Gate ID**: `decision_gate_telegram_remote_operator`
- **Platform Target ID**: `telegram_remote_operator`
- **Platform Family**: `telegram_chat`
- **Record Stub Status**: `manual_publish_record_stub_blocked`
- **Publish Record Target Type**: `telegram_remote_operator_log_record_precheck`
- **Manual Publish Record Type**: `telegram_remote_operator_log_record_stub`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Fields

| Field Name | Placeholder Value | Requires Human Logging |
|---|---|---|
| `operator_log_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: telegram_remote_operator.operator_log_stub]` | `True` |
| `audit_ref_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: telegram_remote_operator.audit_ref_stub]` | `True` |
| `manual_review_status_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: telegram_remote_operator.manual_review_status_stub]` | `True` |
| `published_at_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: telegram_remote_operator.published_at_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_external_publish_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external publish timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public metrics remain unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_publish_record_gate` | `required` | `required` | `True` | Verified manual publish record gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`

### Record Stub: `manual_publish_record_stub_substack`

- **Source Manual Publish Precheck ID**: `manual_publish_record_precheck_substack`
- **Source Audit Summary ID**: `audit_summary_substack`
- **Source Export Packet Stub ID**: `export_packet_stub_substack`
- **Source Manual Export Precheck ID**: `manual_export_precheck_substack`
- **Source Decision Gate ID**: `decision_gate_substack`
- **Platform Target ID**: `substack`
- **Platform Family**: `substack_newsletter`
- **Record Stub Status**: `manual_publish_record_stub_blocked`
- **Publish Record Target Type**: `substack_manual_publish_record_precheck`
- **Manual Publish Record Type**: `substack_manual_publish_record_stub`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Fields

| Field Name | Placeholder Value | Requires Human Logging |
|---|---|---|
| `publication_url_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: substack.publication_url_stub]` | `True` |
| `newsletter_issue_id_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: substack.newsletter_issue_id_stub]` | `True` |
| `published_at_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: substack.published_at_stub]` | `True` |
| `subscriber_visibility_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: substack.subscriber_visibility_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_external_publish_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external publish timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public metrics remain unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_publish_record_gate` | `required` | `required` | `True` | Verified manual publish record gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`

### Record Stub: `manual_publish_record_stub_linkedin`

- **Source Manual Publish Precheck ID**: `manual_publish_record_precheck_linkedin`
- **Source Audit Summary ID**: `audit_summary_linkedin`
- **Source Export Packet Stub ID**: `export_packet_stub_linkedin`
- **Source Manual Export Precheck ID**: `manual_export_precheck_linkedin`
- **Source Decision Gate ID**: `decision_gate_linkedin`
- **Platform Target ID**: `linkedin`
- **Platform Family**: `linkedin_professional`
- **Record Stub Status**: `manual_publish_record_stub_blocked`
- **Publish Record Target Type**: `linkedin_manual_publish_record_precheck`
- **Manual Publish Record Type**: `linkedin_manual_publish_record_stub`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Fields

| Field Name | Placeholder Value | Requires Human Logging |
|---|---|---|
| `publication_url_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: linkedin.publication_url_stub]` | `True` |
| `post_id_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: linkedin.post_id_stub]` | `True` |
| `published_at_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: linkedin.published_at_stub]` | `True` |
| `visibility_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: linkedin.visibility_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_external_publish_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external publish timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public metrics remain unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_publish_record_gate` | `required` | `required` | `True` | Verified manual publish record gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`

### Record Stub: `manual_publish_record_stub_threads`

- **Source Manual Publish Precheck ID**: `manual_publish_record_precheck_threads`
- **Source Audit Summary ID**: `audit_summary_threads`
- **Source Export Packet Stub ID**: `export_packet_stub_threads`
- **Source Manual Export Precheck ID**: `manual_export_precheck_threads`
- **Source Decision Gate ID**: `decision_gate_threads`
- **Platform Target ID**: `threads`
- **Platform Family**: `threads_microblog`
- **Record Stub Status**: `manual_publish_record_stub_blocked`
- **Publish Record Target Type**: `threads_manual_publish_record_precheck`
- **Manual Publish Record Type**: `threads_manual_publish_record_stub`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Fields

| Field Name | Placeholder Value | Requires Human Logging |
|---|---|---|
| `publication_url_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: threads.publication_url_stub]` | `True` |
| `post_id_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: threads.post_id_stub]` | `True` |
| `published_at_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: threads.published_at_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_external_publish_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external publish timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public metrics remain unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_publish_record_gate` | `required` | `required` | `True` | Verified manual publish record gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`

### Record Stub: `manual_publish_record_stub_instagram`

- **Source Manual Publish Precheck ID**: `manual_publish_record_precheck_instagram`
- **Source Audit Summary ID**: `audit_summary_instagram`
- **Source Export Packet Stub ID**: `export_packet_stub_instagram`
- **Source Manual Export Precheck ID**: `manual_export_precheck_instagram`
- **Source Decision Gate ID**: `decision_gate_instagram`
- **Platform Target ID**: `instagram`
- **Platform Family**: `instagram_media`
- **Record Stub Status**: `manual_publish_record_stub_blocked`
- **Publish Record Target Type**: `instagram_manual_publish_record_precheck`
- **Manual Publish Record Type**: `instagram_manual_publish_record_stub`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Fields

| Field Name | Placeholder Value | Requires Human Logging |
|---|---|---|
| `publication_url_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: instagram.publication_url_stub]` | `True` |
| `media_id_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: instagram.media_id_stub]` | `True` |
| `published_at_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: instagram.published_at_stub]` | `True` |
| `media_type_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: instagram.media_type_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_external_publish_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external publish timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public metrics remain unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_publish_record_gate` | `required` | `required` | `True` | Verified manual publish record gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`

### Record Stub: `manual_publish_record_stub_facebook_page`

- **Source Manual Publish Precheck ID**: `manual_publish_record_precheck_facebook_page`
- **Source Audit Summary ID**: `audit_summary_facebook_page`
- **Source Export Packet Stub ID**: `export_packet_stub_facebook_page`
- **Source Manual Export Precheck ID**: `manual_export_precheck_facebook_page`
- **Source Decision Gate ID**: `decision_gate_facebook_page`
- **Platform Target ID**: `facebook_page`
- **Platform Family**: `facebook_page_media`
- **Record Stub Status**: `manual_publish_record_stub_blocked`
- **Publish Record Target Type**: `facebook_page_manual_publish_record_precheck`
- **Manual Publish Record Type**: `facebook_page_manual_publish_record_stub`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Fields

| Field Name | Placeholder Value | Requires Human Logging |
|---|---|---|
| `publication_url_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: facebook_page.publication_url_stub]` | `True` |
| `post_id_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: facebook_page.post_id_stub]` | `True` |
| `published_at_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: facebook_page.published_at_stub]` | `True` |
| `page_id_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: facebook_page.page_id_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_external_publish_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external publish timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public metrics remain unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_publish_record_gate` | `required` | `required` | `True` | Verified manual publish record gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`

### Record Stub: `manual_publish_record_stub_tiktok`

- **Source Manual Publish Precheck ID**: `manual_publish_record_precheck_tiktok`
- **Source Audit Summary ID**: `audit_summary_tiktok`
- **Source Export Packet Stub ID**: `export_packet_stub_tiktok`
- **Source Manual Export Precheck ID**: `manual_export_precheck_tiktok`
- **Source Decision Gate ID**: `decision_gate_tiktok`
- **Platform Target ID**: `tiktok`
- **Platform Family**: `tiktok_video`
- **Record Stub Status**: `manual_publish_record_stub_blocked`
- **Publish Record Target Type**: `tiktok_manual_publish_record_precheck`
- **Manual Publish Record Type**: `tiktok_manual_publish_record_stub`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Fields

| Field Name | Placeholder Value | Requires Human Logging |
|---|---|---|
| `publication_url_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: tiktok.publication_url_stub]` | `True` |
| `video_id_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: tiktok.video_id_stub]` | `True` |
| `published_at_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: tiktok.published_at_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_external_publish_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external publish timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public metrics remain unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_publish_record_gate` | `required` | `required` | `True` | Verified manual publish record gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`

### Record Stub: `manual_publish_record_stub_youtube`

- **Source Manual Publish Precheck ID**: `manual_publish_record_precheck_youtube`
- **Source Audit Summary ID**: `audit_summary_youtube`
- **Source Export Packet Stub ID**: `export_packet_stub_youtube`
- **Source Manual Export Precheck ID**: `manual_export_precheck_youtube`
- **Source Decision Gate ID**: `decision_gate_youtube`
- **Platform Target ID**: `youtube`
- **Platform Family**: `youtube_video`
- **Record Stub Status**: `manual_publish_record_stub_blocked`
- **Publish Record Target Type**: `youtube_manual_publish_record_precheck`
- **Manual Publish Record Type**: `youtube_manual_publish_record_stub`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Fields

| Field Name | Placeholder Value | Requires Human Logging |
|---|---|---|
| `publication_url_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: youtube.publication_url_stub]` | `True` |
| `video_id_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: youtube.video_id_stub]` | `True` |
| `published_at_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: youtube.published_at_stub]` | `True` |
| `visibility_stub` | `[MANUAL_PUBLISH_RECORD_STUB_ONLY: youtube.visibility_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_external_publish_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external publish timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public metrics remain unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_publish_record_gate` | `required` | `required` | `True` | Verified manual publish record gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`
