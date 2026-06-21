# Metrics Precheck to Metrics Record Stub Contract

> [!IMPORTANT]
> This is a metrics record stub contract, not metrics logging and not analytics ingestion.
> It creates blocked metrics record stub metadata and non-public placeholders only.
> It preserves citation, limitation, DQR/readiness, operator identity, signature, hash-lock, publish-record-gate, metrics-gate, account-binding, credential, and dispatch-gate requirements.
> It cannot record metrics, pull analytics, scrape platforms, create publish records, publication URLs, platform post IDs, timestamps, files, clipboard payloads, downloads, approvals, exports, publishable payloads, dispatches, schedules, or platform/API calls.

- **Task Label**: `TASK_CONTENTOPS_0175AX_METRICS_PRECHECK_TO_METRICS_RECORD_STUB_V0`
- **Matrix Version**: `0175AX_METRICS_PRECHECK_TO_METRICS_RECORD_STUB_V1`
- **Source Baseline Commit**: `c0d3e9944767f82b470b7e3f1bff0ba718c6e01d`
- **Packet Hash**: `d0940d2e4549827d48a0954b757f853bb06a8e075b60df0ae8f9871fefd77ef0`
- **Ledger Family**: `metrics_precheck_to_metrics_record_stub_future`
- **Next Required Gate**: `lane_c_platform_metrics_record_stub_to_performance_audit_precheck`

## Invariant Validation Safety Flags

| Invariant Flag | Required State | Status |
|---|---|---|
| `local_only` | `True` | ✅ |
| `fixture_only` | `True` | ✅ |
| `schema_only` | `True` | ✅ |
| `metrics_record_stub_only` | `True` | ✅ |
| `metrics_precheck_only` | `True` | ✅ |
| `manual_publish_record_stub_only` | `True` | ✅ |
| `manual_publish_record_precheck_only` | `True` | ✅ |
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
| `real_metrics_recorded` | `False` | ✅ |
| `metric_values_recorded` | `False` | ✅ |
| `platform_metric_id_recorded` | `False` | ✅ |
| `external_metric_timestamp_recorded` | `False` | ✅ |
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

- **Registered Metrics Record Stubs**: `10`
- **Registered Metrics Record Targets**: `10`
- **Invariants Checked**: `31`
- **Placeholder Metric Fields Defined**: `46`

## Blocked Capabilities & Missing Gates

### Blocked Capabilities
- `live_publishing_dispatch`
- `autonomous_reply_automation`
- `live_credential_hydration`
- `active_scheduler_triggers`
- `manual_review_export`
- `live_metrics_retrieval`
- `scraping`

### Missing Future Gates
- `lane_c_platform_metrics_record_stub_to_performance_audit_precheck`
- `production_key_vault_decrypter`
- `live_operator_signature_vault`

## Metrics Record target configurations

| Platform Target ID | Metrics Record Type | Description |
|---|---|---|
| `x` | `x_metrics_record_stub` | Metrics record stub for X platform |
| `telegram_channel_destination` | `telegram_channel_metrics_record_stub` | Metrics record stub for Telegram channel |
| `telegram_remote_operator` | `telegram_remote_operator_log_metrics_record_stub` | Metrics record stub for Telegram remote operator |
| `substack` | `substack_metrics_record_stub` | Metrics record stub for Substack |
| `linkedin` | `linkedin_metrics_record_stub` | Metrics record stub for LinkedIn |
| `threads` | `threads_metrics_record_stub` | Metrics record stub for Meta Threads |
| `instagram` | `instagram_metrics_record_stub` | Metrics record stub for Instagram |
| `facebook_page` | `facebook_page_metrics_record_stub` | Metrics record stub for Facebook Page |
| `tiktok` | `tiktok_metrics_record_stub` | Metrics record stub for TikTok |
| `youtube` | `youtube_metrics_record_stub` | Metrics record stub for YouTube |

## Platform Metrics Record Stubs

### Metrics Record Stub: `metrics_record_stub_x`

- **Source Metrics Precheck ID**: `metrics_precheck_x`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_x`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_x`
- **Source Audit Summary ID**: `audit_summary_x`
- **Source Export Packet Stub ID**: `export_packet_stub_x`
- **Source Manual Export Precheck ID**: `manual_export_precheck_x`
- **Source Decision Gate ID**: `decision_gate_x`
- **Platform Target ID**: `x`
- **Platform Family**: `x_microblog`
- **Metrics Record Stub Status**: `metrics_record_stub_blocked`
- **Metrics Target Type**: `x_metrics_precheck`
- **Metrics Record Type**: `x_metrics_record_stub`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Metric Fields

| Field Name | Placeholder Value | Requires Human Metrics Logging |
|---|---|---|
| `impressions_stub` | `[METRICS_RECORD_STUB_ONLY: x.impressions_stub]` | `True` |
| `likes_stub` | `[METRICS_RECORD_STUB_ONLY: x.likes_stub]` | `True` |
| `replies_stub` | `[METRICS_RECORD_STUB_ONLY: x.replies_stub]` | `True` |
| `reposts_stub` | `[METRICS_RECORD_STUB_ONLY: x.reposts_stub]` | `True` |
| `clicks_stub` | `[METRICS_RECORD_STUB_ONLY: x.clicks_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
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
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_future_performance_audit_precheck` | `required` | `required` | `True` | Verified future performance audit precheck gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`
- `blocked_no_metrics_gate`
- `blocked_no_performance_audit_precheck`

### Metrics Record Stub: `metrics_record_stub_telegram_channel_destination`

- **Source Metrics Precheck ID**: `metrics_precheck_telegram_channel_destination`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_telegram_channel_destination`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_telegram_channel_destination`
- **Source Audit Summary ID**: `audit_summary_telegram_channel_destination`
- **Source Export Packet Stub ID**: `export_packet_stub_telegram_channel_destination`
- **Source Manual Export Precheck ID**: `manual_export_precheck_telegram_channel_destination`
- **Source Decision Gate ID**: `decision_gate_telegram_channel_destination`
- **Platform Target ID**: `telegram_channel_destination`
- **Platform Family**: `telegram_chat`
- **Metrics Record Stub Status**: `metrics_record_stub_blocked`
- **Metrics Target Type**: `telegram_channel_metrics_precheck`
- **Metrics Record Type**: `telegram_channel_metrics_record_stub`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Metric Fields

| Field Name | Placeholder Value | Requires Human Metrics Logging |
|---|---|---|
| `views_stub` | `[METRICS_RECORD_STUB_ONLY: telegram_channel_destination.views_stub]` | `True` |
| `reactions_stub` | `[METRICS_RECORD_STUB_ONLY: telegram_channel_destination.reactions_stub]` | `True` |
| `forwards_stub` | `[METRICS_RECORD_STUB_ONLY: telegram_channel_destination.forwards_stub]` | `True` |
| `replies_stub` | `[METRICS_RECORD_STUB_ONLY: telegram_channel_destination.replies_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
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
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_future_performance_audit_precheck` | `required` | `required` | `True` | Verified future performance audit precheck gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`
- `blocked_no_metrics_gate`
- `blocked_no_performance_audit_precheck`

### Metrics Record Stub: `metrics_record_stub_telegram_remote_operator`

- **Source Metrics Precheck ID**: `metrics_precheck_telegram_remote_operator`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_telegram_remote_operator`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_telegram_remote_operator`
- **Source Audit Summary ID**: `audit_summary_telegram_remote_operator`
- **Source Export Packet Stub ID**: `export_packet_stub_telegram_remote_operator`
- **Source Manual Export Precheck ID**: `manual_export_precheck_telegram_remote_operator`
- **Source Decision Gate ID**: `decision_gate_telegram_remote_operator`
- **Platform Target ID**: `telegram_remote_operator`
- **Platform Family**: `telegram_chat`
- **Metrics Record Stub Status**: `metrics_record_stub_blocked`
- **Metrics Target Type**: `telegram_remote_operator_log_metrics_precheck`
- **Metrics Record Type**: `telegram_remote_operator_log_metrics_record_stub`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Metric Fields

| Field Name | Placeholder Value | Requires Human Metrics Logging |
|---|---|---|
| `operator_review_count_stub` | `[METRICS_RECORD_STUB_ONLY: telegram_remote_operator.operator_review_count_stub]` | `True` |
| `manual_action_count_stub` | `[METRICS_RECORD_STUB_ONLY: telegram_remote_operator.manual_action_count_stub]` | `True` |
| `audit_event_count_stub` | `[METRICS_RECORD_STUB_ONLY: telegram_remote_operator.audit_event_count_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
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
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_future_performance_audit_precheck` | `required` | `required` | `True` | Verified future performance audit precheck gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`
- `blocked_no_metrics_gate`
- `blocked_no_performance_audit_precheck`

### Metrics Record Stub: `metrics_record_stub_substack`

- **Source Metrics Precheck ID**: `metrics_precheck_substack`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_substack`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_substack`
- **Source Audit Summary ID**: `audit_summary_substack`
- **Source Export Packet Stub ID**: `export_packet_stub_substack`
- **Source Manual Export Precheck ID**: `manual_export_precheck_substack`
- **Source Decision Gate ID**: `decision_gate_substack`
- **Platform Target ID**: `substack`
- **Platform Family**: `substack_newsletter`
- **Metrics Record Stub Status**: `metrics_record_stub_blocked`
- **Metrics Target Type**: `substack_metrics_precheck`
- **Metrics Record Type**: `substack_metrics_record_stub`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Metric Fields

| Field Name | Placeholder Value | Requires Human Metrics Logging |
|---|---|---|
| `opens_stub` | `[METRICS_RECORD_STUB_ONLY: substack.opens_stub]` | `True` |
| `clicks_stub` | `[METRICS_RECORD_STUB_ONLY: substack.clicks_stub]` | `True` |
| `likes_stub` | `[METRICS_RECORD_STUB_ONLY: substack.likes_stub]` | `True` |
| `comments_stub` | `[METRICS_RECORD_STUB_ONLY: substack.comments_stub]` | `True` |
| `subscriber_delta_stub` | `[METRICS_RECORD_STUB_ONLY: substack.subscriber_delta_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
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
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_future_performance_audit_precheck` | `required` | `required` | `True` | Verified future performance audit precheck gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`
- `blocked_no_metrics_gate`
- `blocked_no_performance_audit_precheck`

### Metrics Record Stub: `metrics_record_stub_linkedin`

- **Source Metrics Precheck ID**: `metrics_precheck_linkedin`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_linkedin`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_linkedin`
- **Source Audit Summary ID**: `audit_summary_linkedin`
- **Source Export Packet Stub ID**: `export_packet_stub_linkedin`
- **Source Manual Export Precheck ID**: `manual_export_precheck_linkedin`
- **Source Decision Gate ID**: `decision_gate_linkedin`
- **Platform Target ID**: `linkedin`
- **Platform Family**: `linkedin_professional`
- **Metrics Record Stub Status**: `metrics_record_stub_blocked`
- **Metrics Target Type**: `linkedin_metrics_precheck`
- **Metrics Record Type**: `linkedin_metrics_record_stub`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Metric Fields

| Field Name | Placeholder Value | Requires Human Metrics Logging |
|---|---|---|
| `impressions_stub` | `[METRICS_RECORD_STUB_ONLY: linkedin.impressions_stub]` | `True` |
| `reactions_stub` | `[METRICS_RECORD_STUB_ONLY: linkedin.reactions_stub]` | `True` |
| `comments_stub` | `[METRICS_RECORD_STUB_ONLY: linkedin.comments_stub]` | `True` |
| `reposts_stub` | `[METRICS_RECORD_STUB_ONLY: linkedin.reposts_stub]` | `True` |
| `clicks_stub` | `[METRICS_RECORD_STUB_ONLY: linkedin.clicks_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
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
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_future_performance_audit_precheck` | `required` | `required` | `True` | Verified future performance audit precheck gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`
- `blocked_no_metrics_gate`
- `blocked_no_performance_audit_precheck`

### Metrics Record Stub: `metrics_record_stub_threads`

- **Source Metrics Precheck ID**: `metrics_precheck_threads`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_threads`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_threads`
- **Source Audit Summary ID**: `audit_summary_threads`
- **Source Export Packet Stub ID**: `export_packet_stub_threads`
- **Source Manual Export Precheck ID**: `manual_export_precheck_threads`
- **Source Decision Gate ID**: `decision_gate_threads`
- **Platform Target ID**: `threads`
- **Platform Family**: `threads_microblog`
- **Metrics Record Stub Status**: `metrics_record_stub_blocked`
- **Metrics Target Type**: `threads_metrics_precheck`
- **Metrics Record Type**: `threads_metrics_record_stub`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Metric Fields

| Field Name | Placeholder Value | Requires Human Metrics Logging |
|---|---|---|
| `views_stub` | `[METRICS_RECORD_STUB_ONLY: threads.views_stub]` | `True` |
| `likes_stub` | `[METRICS_RECORD_STUB_ONLY: threads.likes_stub]` | `True` |
| `replies_stub` | `[METRICS_RECORD_STUB_ONLY: threads.replies_stub]` | `True` |
| `reposts_stub` | `[METRICS_RECORD_STUB_ONLY: threads.reposts_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
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
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_future_performance_audit_precheck` | `required` | `required` | `True` | Verified future performance audit precheck gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`
- `blocked_no_metrics_gate`
- `blocked_no_performance_audit_precheck`

### Metrics Record Stub: `metrics_record_stub_instagram`

- **Source Metrics Precheck ID**: `metrics_precheck_instagram`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_instagram`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_instagram`
- **Source Audit Summary ID**: `audit_summary_instagram`
- **Source Export Packet Stub ID**: `export_packet_stub_instagram`
- **Source Manual Export Precheck ID**: `manual_export_precheck_instagram`
- **Source Decision Gate ID**: `decision_gate_instagram`
- **Platform Target ID**: `instagram`
- **Platform Family**: `instagram_media`
- **Metrics Record Stub Status**: `metrics_record_stub_blocked`
- **Metrics Target Type**: `instagram_metrics_precheck`
- **Metrics Record Type**: `instagram_metrics_record_stub`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Metric Fields

| Field Name | Placeholder Value | Requires Human Metrics Logging |
|---|---|---|
| `views_stub` | `[METRICS_RECORD_STUB_ONLY: instagram.views_stub]` | `True` |
| `likes_stub` | `[METRICS_RECORD_STUB_ONLY: instagram.likes_stub]` | `True` |
| `comments_stub` | `[METRICS_RECORD_STUB_ONLY: instagram.comments_stub]` | `True` |
| `shares_stub` | `[METRICS_RECORD_STUB_ONLY: instagram.shares_stub]` | `True` |
| `saves_stub` | `[METRICS_RECORD_STUB_ONLY: instagram.saves_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
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
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_future_performance_audit_precheck` | `required` | `required` | `True` | Verified future performance audit precheck gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`
- `blocked_no_metrics_gate`
- `blocked_no_performance_audit_precheck`

### Metrics Record Stub: `metrics_record_stub_facebook_page`

- **Source Metrics Precheck ID**: `metrics_precheck_facebook_page`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_facebook_page`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_facebook_page`
- **Source Audit Summary ID**: `audit_summary_facebook_page`
- **Source Export Packet Stub ID**: `export_packet_stub_facebook_page`
- **Source Manual Export Precheck ID**: `manual_export_precheck_facebook_page`
- **Source Decision Gate ID**: `decision_gate_facebook_page`
- **Platform Target ID**: `facebook_page`
- **Platform Family**: `facebook_page_media`
- **Metrics Record Stub Status**: `metrics_record_stub_blocked`
- **Metrics Target Type**: `facebook_page_metrics_precheck`
- **Metrics Record Type**: `facebook_page_metrics_record_stub`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Metric Fields

| Field Name | Placeholder Value | Requires Human Metrics Logging |
|---|---|---|
| `reach_stub` | `[METRICS_RECORD_STUB_ONLY: facebook_page.reach_stub]` | `True` |
| `reactions_stub` | `[METRICS_RECORD_STUB_ONLY: facebook_page.reactions_stub]` | `True` |
| `comments_stub` | `[METRICS_RECORD_STUB_ONLY: facebook_page.comments_stub]` | `True` |
| `shares_stub` | `[METRICS_RECORD_STUB_ONLY: facebook_page.shares_stub]` | `True` |
| `clicks_stub` | `[METRICS_RECORD_STUB_ONLY: facebook_page.clicks_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
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
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_future_performance_audit_precheck` | `required` | `required` | `True` | Verified future performance audit precheck gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`
- `blocked_no_metrics_gate`
- `blocked_no_performance_audit_precheck`

### Metrics Record Stub: `metrics_record_stub_tiktok`

- **Source Metrics Precheck ID**: `metrics_precheck_tiktok`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_tiktok`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_tiktok`
- **Source Audit Summary ID**: `audit_summary_tiktok`
- **Source Export Packet Stub ID**: `export_packet_stub_tiktok`
- **Source Manual Export Precheck ID**: `manual_export_precheck_tiktok`
- **Source Decision Gate ID**: `decision_gate_tiktok`
- **Platform Target ID**: `tiktok`
- **Platform Family**: `tiktok_video`
- **Metrics Record Stub Status**: `metrics_record_stub_blocked`
- **Metrics Target Type**: `tiktok_metrics_precheck`
- **Metrics Record Type**: `tiktok_metrics_record_stub`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Metric Fields

| Field Name | Placeholder Value | Requires Human Metrics Logging |
|---|---|---|
| `views_stub` | `[METRICS_RECORD_STUB_ONLY: tiktok.views_stub]` | `True` |
| `likes_stub` | `[METRICS_RECORD_STUB_ONLY: tiktok.likes_stub]` | `True` |
| `comments_stub` | `[METRICS_RECORD_STUB_ONLY: tiktok.comments_stub]` | `True` |
| `shares_stub` | `[METRICS_RECORD_STUB_ONLY: tiktok.shares_stub]` | `True` |
| `saves_stub` | `[METRICS_RECORD_STUB_ONLY: tiktok.saves_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
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
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_future_performance_audit_precheck` | `required` | `required` | `True` | Verified future performance audit precheck gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`
- `blocked_no_metrics_gate`
- `blocked_no_performance_audit_precheck`

### Metrics Record Stub: `metrics_record_stub_youtube`

- **Source Metrics Precheck ID**: `metrics_precheck_youtube`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_youtube`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_youtube`
- **Source Audit Summary ID**: `audit_summary_youtube`
- **Source Export Packet Stub ID**: `export_packet_stub_youtube`
- **Source Manual Export Precheck ID**: `manual_export_precheck_youtube`
- **Source Decision Gate ID**: `decision_gate_youtube`
- **Platform Target ID**: `youtube`
- **Platform Family**: `youtube_video`
- **Metrics Record Stub Status**: `metrics_record_stub_blocked`
- **Metrics Target Type**: `youtube_metrics_precheck`
- **Metrics Record Type**: `youtube_metrics_record_stub`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Manual Publish Record Allowed**: `False`
- **Manual Publish Record Created**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
- **External Publish Timestamp Recorded**: `False`
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
- **Manual Publish Record Gate**: `manual_publish_record_gate_required_but_locked`
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Placeholder Metric Fields

| Field Name | Placeholder Value | Requires Human Metrics Logging |
|---|---|---|
| `views_stub` | `[METRICS_RECORD_STUB_ONLY: youtube.views_stub]` | `True` |
| `likes_stub` | `[METRICS_RECORD_STUB_ONLY: youtube.likes_stub]` | `True` |
| `comments_stub` | `[METRICS_RECORD_STUB_ONLY: youtube.comments_stub]` | `True` |
| `watch_time_stub` | `[METRICS_RECORD_STUB_ONLY: youtube.watch_time_stub]` | `True` |
| `subscriber_delta_stub` | `[METRICS_RECORD_STUB_ONLY: youtube.subscriber_delta_stub]` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
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
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_future_performance_audit_precheck` | `required` | `required` | `True` | Verified future performance audit precheck gate is required. |

#### Blocked Reasons

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_publish_record_gate`
- `blocked_no_platform_publication_identity`
- `blocked_no_external_publish_evidence`
- `blocked_no_metrics_gate`
- `blocked_no_performance_audit_precheck`
