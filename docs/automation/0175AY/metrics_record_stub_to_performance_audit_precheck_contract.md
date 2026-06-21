# Metrics Record Stub to Performance Audit Precheck Contract

> [!IMPORTANT]
> This is a performance audit precheck contract, not performance reporting and not analytics ingestion.
> It creates blocked performance audit precheck metadata and non-public metric references only.
> It preserves citation, limitation, DQR/readiness, operator identity, signature, hash-lock, metrics-gate, performance-audit-gate, account-binding, credential, and dispatch-gate requirements.
> It cannot record metrics, score performance, compare KPIs, generate claims/recommendations, pull analytics, scrape platforms, create publish records, publication URLs, platform post IDs, timestamps, files, screenshots, clipboard payloads, downloads, approvals, exports, publishable payloads, dispatches, schedules, or platform/API calls.

- **Task Label**: `TASK_CONTENTOPS_0175AY_METRICS_RECORD_STUB_TO_PERFORMANCE_AUDIT_PRECHECK_V0`
- **Matrix Version**: `0175AY_METRICS_RECORD_STUB_TO_PERFORMANCE_AUDIT_PRECHECK_V1`
- **Source Baseline Commit**: `f3e0cb0e2774b8a9566e652ee61be947bf686a5e`
- **Packet Hash**: `4921ee64b6306b36cb6b836c9edb0a24fbd967bd0dbaedb8a1ecd0bed5a181e4`
- **Ledger Family**: `metrics_record_stub_to_performance_audit_precheck_future`
- **Next Required Gate**: `lane_c_performance_audit_precheck_to_summary_stub`

## Invariant Validation Safety Flags

| Invariant Flag | Required State | Status |
|---|---|---|
| `local_only` | `True` | ✅ |
| `fixture_only` | `True` | ✅ |
| `schema_only` | `True` | ✅ |
| `performance_audit_precheck_only` | `True` | ✅ |
| `metrics_record_stub_only` | `True` | ✅ |
| `metrics_precheck_only` | `True` | ✅ |
| `manual_publish_record_stub_only` | `True` | ✅ |
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
| `metric_score_computed` | `False` | ✅ |
| `kpi_comparison_computed` | `False` | ✅ |
| `performance_claim_generated` | `False` | ✅ |
| `recommendation_generated` | `False` | ✅ |
| `platform_analytics_pull_performed` | `False` | ✅ |
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

- **Registered Performance Audit Precheck Records**: `10`
- **Registered Performance Audit Targets**: `10`
- **Invariants Checked**: `36`
- **Placeholder Metric References Defined**: `46`

## Blocked Capabilities & Missing Gates

### Blocked Capabilities
- `live_publishing_dispatch`
- `autonomous_reply_automation`
- `live_credential_hydration`
- `active_scheduler_triggers`
- `manual_review_export`
- `live_metrics_retrieval`
- `scraping`
- `performance_scoring`
- `analytics_ingestion`

### Missing Future Gates
- `lane_c_performance_audit_precheck_to_summary_stub`
- `production_key_vault_decrypter`
- `live_operator_signature_vault`

## Performance Audit target configurations

| Platform Target ID | Performance Target Type | Description |
|---|---|---|
| `x` | `x_performance_audit_precheck` | Performance audit precheck for X platform |
| `telegram_channel_destination` | `telegram_channel_performance_audit_precheck` | Performance audit precheck for Telegram channel |
| `telegram_remote_operator` | `telegram_remote_operator_log_performance_audit_precheck` | Performance audit precheck for Telegram remote operator |
| `substack` | `substack_performance_audit_precheck` | Performance audit precheck for Substack |
| `linkedin` | `linkedin_performance_audit_precheck` | Performance audit precheck for LinkedIn |
| `threads` | `threads_performance_audit_precheck` | Performance audit precheck for Meta Threads |
| `instagram` | `instagram_performance_audit_precheck` | Performance audit precheck for Instagram |
| `facebook_page` | `facebook_page_performance_audit_precheck` | Performance audit precheck for Facebook Page |
| `tiktok` | `tiktok_performance_audit_precheck` | Performance audit precheck for TikTok |
| `youtube` | `youtube_performance_audit_precheck` | Performance audit precheck for YouTube |

## Platform Performance Audit Prechecks

### Performance Audit Precheck Record: `performance_audit_precheck_x`

- **Source Metrics Record Stub ID**: `metrics_record_stub_x`
- **Source Metrics Precheck ID**: `metrics_precheck_x`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_x`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_x`
- **Source Audit Summary ID**: `audit_summary_x`
- **Source Export Packet Stub ID**: `export_packet_stub_x`
- **Source Manual Export Precheck ID**: `manual_export_precheck_x`
- **Source Decision Gate ID**: `decision_gate_x`
- **Platform Target ID**: `x`
- **Platform Family**: `x_microblog`
- **Performance Audit Precheck Status**: `performance_audit_precheck_blocked`
- **Performance Target Type**: `x_performance_audit_precheck`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Metric Score Computed**: `False`
- **KPI Comparison Computed**: `False`
- **Performance Claim Generated**: `False`
- **Recommendation Generated**: `False`
- **Platform Analytics Pull Performed**: `False`
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
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Metric References

| Metric Name | Source Field Name | Requires Human Performance Review |
|---|---|---|
| `impressions_stub` | `impressions_stub` | `True` |
| `likes_stub` | `likes_stub` | `True` |
| `replies_stub` | `replies_stub` | `True` |
| `reposts_stub` | `reposts_stub` | `True` |
| `clicks_stub` | `clicks_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance score has been computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_recommendation_generated` | `no_recommendation` | `no_recommendation` | `True` | Verified no performance recommendation or suggestion was generated. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_performance_audit_gate` | `required` | `required` | `True` | Verified performance audit gate is required. |

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
- `blocked_no_performance_audit_gate`

### Performance Audit Precheck Record: `performance_audit_precheck_telegram_channel_destination`

- **Source Metrics Record Stub ID**: `metrics_record_stub_telegram_channel_destination`
- **Source Metrics Precheck ID**: `metrics_precheck_telegram_channel_destination`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_telegram_channel_destination`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_telegram_channel_destination`
- **Source Audit Summary ID**: `audit_summary_telegram_channel_destination`
- **Source Export Packet Stub ID**: `export_packet_stub_telegram_channel_destination`
- **Source Manual Export Precheck ID**: `manual_export_precheck_telegram_channel_destination`
- **Source Decision Gate ID**: `decision_gate_telegram_channel_destination`
- **Platform Target ID**: `telegram_channel_destination`
- **Platform Family**: `telegram_chat`
- **Performance Audit Precheck Status**: `performance_audit_precheck_blocked`
- **Performance Target Type**: `telegram_channel_performance_audit_precheck`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Metric Score Computed**: `False`
- **KPI Comparison Computed**: `False`
- **Performance Claim Generated**: `False`
- **Recommendation Generated**: `False`
- **Platform Analytics Pull Performed**: `False`
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
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Metric References

| Metric Name | Source Field Name | Requires Human Performance Review |
|---|---|---|
| `views_stub` | `views_stub` | `True` |
| `reactions_stub` | `reactions_stub` | `True` |
| `forwards_stub` | `forwards_stub` | `True` |
| `replies_stub` | `replies_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance score has been computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_recommendation_generated` | `no_recommendation` | `no_recommendation` | `True` | Verified no performance recommendation or suggestion was generated. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_performance_audit_gate` | `required` | `required` | `True` | Verified performance audit gate is required. |

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
- `blocked_no_performance_audit_gate`

### Performance Audit Precheck Record: `performance_audit_precheck_telegram_remote_operator`

- **Source Metrics Record Stub ID**: `metrics_record_stub_telegram_remote_operator`
- **Source Metrics Precheck ID**: `metrics_precheck_telegram_remote_operator`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_telegram_remote_operator`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_telegram_remote_operator`
- **Source Audit Summary ID**: `audit_summary_telegram_remote_operator`
- **Source Export Packet Stub ID**: `export_packet_stub_telegram_remote_operator`
- **Source Manual Export Precheck ID**: `manual_export_precheck_telegram_remote_operator`
- **Source Decision Gate ID**: `decision_gate_telegram_remote_operator`
- **Platform Target ID**: `telegram_remote_operator`
- **Platform Family**: `telegram_chat`
- **Performance Audit Precheck Status**: `performance_audit_precheck_blocked`
- **Performance Target Type**: `telegram_remote_operator_log_performance_audit_precheck`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Metric Score Computed**: `False`
- **KPI Comparison Computed**: `False`
- **Performance Claim Generated**: `False`
- **Recommendation Generated**: `False`
- **Platform Analytics Pull Performed**: `False`
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
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Metric References

| Metric Name | Source Field Name | Requires Human Performance Review |
|---|---|---|
| `operator_review_count_stub` | `operator_review_count_stub` | `True` |
| `manual_action_count_stub` | `manual_action_count_stub` | `True` |
| `audit_event_count_stub` | `audit_event_count_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance score has been computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_recommendation_generated` | `no_recommendation` | `no_recommendation` | `True` | Verified no performance recommendation or suggestion was generated. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_performance_audit_gate` | `required` | `required` | `True` | Verified performance audit gate is required. |

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
- `blocked_no_performance_audit_gate`

### Performance Audit Precheck Record: `performance_audit_precheck_substack`

- **Source Metrics Record Stub ID**: `metrics_record_stub_substack`
- **Source Metrics Precheck ID**: `metrics_precheck_substack`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_substack`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_substack`
- **Source Audit Summary ID**: `audit_summary_substack`
- **Source Export Packet Stub ID**: `export_packet_stub_substack`
- **Source Manual Export Precheck ID**: `manual_export_precheck_substack`
- **Source Decision Gate ID**: `decision_gate_substack`
- **Platform Target ID**: `substack`
- **Platform Family**: `substack_newsletter`
- **Performance Audit Precheck Status**: `performance_audit_precheck_blocked`
- **Performance Target Type**: `substack_performance_audit_precheck`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Metric Score Computed**: `False`
- **KPI Comparison Computed**: `False`
- **Performance Claim Generated**: `False`
- **Recommendation Generated**: `False`
- **Platform Analytics Pull Performed**: `False`
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
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Metric References

| Metric Name | Source Field Name | Requires Human Performance Review |
|---|---|---|
| `opens_stub` | `opens_stub` | `True` |
| `clicks_stub` | `clicks_stub` | `True` |
| `likes_stub` | `likes_stub` | `True` |
| `comments_stub` | `comments_stub` | `True` |
| `subscriber_delta_stub` | `subscriber_delta_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance score has been computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_recommendation_generated` | `no_recommendation` | `no_recommendation` | `True` | Verified no performance recommendation or suggestion was generated. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_performance_audit_gate` | `required` | `required` | `True` | Verified performance audit gate is required. |

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
- `blocked_no_performance_audit_gate`

### Performance Audit Precheck Record: `performance_audit_precheck_linkedin`

- **Source Metrics Record Stub ID**: `metrics_record_stub_linkedin`
- **Source Metrics Precheck ID**: `metrics_precheck_linkedin`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_linkedin`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_linkedin`
- **Source Audit Summary ID**: `audit_summary_linkedin`
- **Source Export Packet Stub ID**: `export_packet_stub_linkedin`
- **Source Manual Export Precheck ID**: `manual_export_precheck_linkedin`
- **Source Decision Gate ID**: `decision_gate_linkedin`
- **Platform Target ID**: `linkedin`
- **Platform Family**: `linkedin_professional`
- **Performance Audit Precheck Status**: `performance_audit_precheck_blocked`
- **Performance Target Type**: `linkedin_performance_audit_precheck`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Metric Score Computed**: `False`
- **KPI Comparison Computed**: `False`
- **Performance Claim Generated**: `False`
- **Recommendation Generated**: `False`
- **Platform Analytics Pull Performed**: `False`
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
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Metric References

| Metric Name | Source Field Name | Requires Human Performance Review |
|---|---|---|
| `impressions_stub` | `impressions_stub` | `True` |
| `reactions_stub` | `reactions_stub` | `True` |
| `comments_stub` | `comments_stub` | `True` |
| `reposts_stub` | `reposts_stub` | `True` |
| `clicks_stub` | `clicks_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance score has been computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_recommendation_generated` | `no_recommendation` | `no_recommendation` | `True` | Verified no performance recommendation or suggestion was generated. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_performance_audit_gate` | `required` | `required` | `True` | Verified performance audit gate is required. |

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
- `blocked_no_performance_audit_gate`

### Performance Audit Precheck Record: `performance_audit_precheck_threads`

- **Source Metrics Record Stub ID**: `metrics_record_stub_threads`
- **Source Metrics Precheck ID**: `metrics_precheck_threads`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_threads`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_threads`
- **Source Audit Summary ID**: `audit_summary_threads`
- **Source Export Packet Stub ID**: `export_packet_stub_threads`
- **Source Manual Export Precheck ID**: `manual_export_precheck_threads`
- **Source Decision Gate ID**: `decision_gate_threads`
- **Platform Target ID**: `threads`
- **Platform Family**: `threads_microblog`
- **Performance Audit Precheck Status**: `performance_audit_precheck_blocked`
- **Performance Target Type**: `threads_performance_audit_precheck`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Metric Score Computed**: `False`
- **KPI Comparison Computed**: `False`
- **Performance Claim Generated**: `False`
- **Recommendation Generated**: `False`
- **Platform Analytics Pull Performed**: `False`
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
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Metric References

| Metric Name | Source Field Name | Requires Human Performance Review |
|---|---|---|
| `views_stub` | `views_stub` | `True` |
| `likes_stub` | `likes_stub` | `True` |
| `replies_stub` | `replies_stub` | `True` |
| `reposts_stub` | `reposts_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance score has been computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_recommendation_generated` | `no_recommendation` | `no_recommendation` | `True` | Verified no performance recommendation or suggestion was generated. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_performance_audit_gate` | `required` | `required` | `True` | Verified performance audit gate is required. |

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
- `blocked_no_performance_audit_gate`

### Performance Audit Precheck Record: `performance_audit_precheck_instagram`

- **Source Metrics Record Stub ID**: `metrics_record_stub_instagram`
- **Source Metrics Precheck ID**: `metrics_precheck_instagram`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_instagram`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_instagram`
- **Source Audit Summary ID**: `audit_summary_instagram`
- **Source Export Packet Stub ID**: `export_packet_stub_instagram`
- **Source Manual Export Precheck ID**: `manual_export_precheck_instagram`
- **Source Decision Gate ID**: `decision_gate_instagram`
- **Platform Target ID**: `instagram`
- **Platform Family**: `instagram_media`
- **Performance Audit Precheck Status**: `performance_audit_precheck_blocked`
- **Performance Target Type**: `instagram_performance_audit_precheck`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Metric Score Computed**: `False`
- **KPI Comparison Computed**: `False`
- **Performance Claim Generated**: `False`
- **Recommendation Generated**: `False`
- **Platform Analytics Pull Performed**: `False`
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
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Metric References

| Metric Name | Source Field Name | Requires Human Performance Review |
|---|---|---|
| `views_stub` | `views_stub` | `True` |
| `likes_stub` | `likes_stub` | `True` |
| `comments_stub` | `comments_stub` | `True` |
| `shares_stub` | `shares_stub` | `True` |
| `saves_stub` | `saves_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance score has been computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_recommendation_generated` | `no_recommendation` | `no_recommendation` | `True` | Verified no performance recommendation or suggestion was generated. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_performance_audit_gate` | `required` | `required` | `True` | Verified performance audit gate is required. |

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
- `blocked_no_performance_audit_gate`

### Performance Audit Precheck Record: `performance_audit_precheck_facebook_page`

- **Source Metrics Record Stub ID**: `metrics_record_stub_facebook_page`
- **Source Metrics Precheck ID**: `metrics_precheck_facebook_page`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_facebook_page`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_facebook_page`
- **Source Audit Summary ID**: `audit_summary_facebook_page`
- **Source Export Packet Stub ID**: `export_packet_stub_facebook_page`
- **Source Manual Export Precheck ID**: `manual_export_precheck_facebook_page`
- **Source Decision Gate ID**: `decision_gate_facebook_page`
- **Platform Target ID**: `facebook_page`
- **Platform Family**: `facebook_page_media`
- **Performance Audit Precheck Status**: `performance_audit_precheck_blocked`
- **Performance Target Type**: `facebook_page_performance_audit_precheck`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Metric Score Computed**: `False`
- **KPI Comparison Computed**: `False`
- **Performance Claim Generated**: `False`
- **Recommendation Generated**: `False`
- **Platform Analytics Pull Performed**: `False`
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
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Metric References

| Metric Name | Source Field Name | Requires Human Performance Review |
|---|---|---|
| `reach_stub` | `reach_stub` | `True` |
| `reactions_stub` | `reactions_stub` | `True` |
| `comments_stub` | `comments_stub` | `True` |
| `shares_stub` | `shares_stub` | `True` |
| `clicks_stub` | `clicks_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance score has been computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_recommendation_generated` | `no_recommendation` | `no_recommendation` | `True` | Verified no performance recommendation or suggestion was generated. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_performance_audit_gate` | `required` | `required` | `True` | Verified performance audit gate is required. |

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
- `blocked_no_performance_audit_gate`

### Performance Audit Precheck Record: `performance_audit_precheck_tiktok`

- **Source Metrics Record Stub ID**: `metrics_record_stub_tiktok`
- **Source Metrics Precheck ID**: `metrics_precheck_tiktok`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_tiktok`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_tiktok`
- **Source Audit Summary ID**: `audit_summary_tiktok`
- **Source Export Packet Stub ID**: `export_packet_stub_tiktok`
- **Source Manual Export Precheck ID**: `manual_export_precheck_tiktok`
- **Source Decision Gate ID**: `decision_gate_tiktok`
- **Platform Target ID**: `tiktok`
- **Platform Family**: `tiktok_video`
- **Performance Audit Precheck Status**: `performance_audit_precheck_blocked`
- **Performance Target Type**: `tiktok_performance_audit_precheck`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Metric Score Computed**: `False`
- **KPI Comparison Computed**: `False`
- **Performance Claim Generated**: `False`
- **Recommendation Generated**: `False`
- **Platform Analytics Pull Performed**: `False`
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
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Metric References

| Metric Name | Source Field Name | Requires Human Performance Review |
|---|---|---|
| `views_stub` | `views_stub` | `True` |
| `likes_stub` | `likes_stub` | `True` |
| `comments_stub` | `comments_stub` | `True` |
| `shares_stub` | `shares_stub` | `True` |
| `saves_stub` | `saves_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance score has been computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_recommendation_generated` | `no_recommendation` | `no_recommendation` | `True` | Verified no performance recommendation or suggestion was generated. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_performance_audit_gate` | `required` | `required` | `True` | Verified performance audit gate is required. |

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
- `blocked_no_performance_audit_gate`

### Performance Audit Precheck Record: `performance_audit_precheck_youtube`

- **Source Metrics Record Stub ID**: `metrics_record_stub_youtube`
- **Source Metrics Precheck ID**: `metrics_precheck_youtube`
- **Source Manual Publish Record Stub ID**: `manual_publish_record_stub_youtube`
- **Source Manual Publish Record Precheck ID**: `manual_publish_record_precheck_youtube`
- **Source Audit Summary ID**: `audit_summary_youtube`
- **Source Export Packet Stub ID**: `export_packet_stub_youtube`
- **Source Manual Export Precheck ID**: `manual_export_precheck_youtube`
- **Source Decision Gate ID**: `decision_gate_youtube`
- **Platform Target ID**: `youtube`
- **Platform Family**: `youtube_video`
- **Performance Audit Precheck Status**: `performance_audit_precheck_blocked`
- **Performance Target Type**: `youtube_performance_audit_precheck`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Metric ID Recorded**: `False`
- **External Metric Timestamp Recorded**: `False`
- **Public Metrics Recorded**: `False`
- **Metric Score Computed**: `False`
- **KPI Comparison Computed**: `False`
- **Performance Claim Generated**: `False`
- **Recommendation Generated**: `False`
- **Platform Analytics Pull Performed**: `False`
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
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Metric References

| Metric Name | Source Field Name | Requires Human Performance Review |
|---|---|---|
| `views_stub` | `views_stub` | `True` |
| `likes_stub` | `likes_stub` | `True` |
| `comments_stub` | `comments_stub` | `True` |
| `watch_time_stub` | `watch_time_stub` | `True` |
| `subscriber_delta_stub` | `subscriber_delta_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_platform_metric_id_recorded` | `no_id` | `no_id` | `True` | Verified platform metric ID is unrecorded. |
| `no_external_metric_timestamp_recorded` | `no_timestamp` | `no_timestamp` | `True` | Verified external metric timestamp remains unrecorded. |
| `no_public_metrics_recorded` | `no_metrics` | `no_metrics` | `True` | Verified public audience metrics remain unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance score has been computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_recommendation_generated` | `no_recommendation` | `no_recommendation` | `True` | Verified no performance recommendation or suggestion was generated. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_manual_publish_record_created` | `no_record` | `no_record` | `True` | Verified no manual publish record created. |
| `no_platform_publication_url_recorded` | `no_url` | `no_url` | `True` | Verified platform publication URL remains unrecorded. |
| `no_platform_post_id_recorded` | `no_post_id` | `no_post_id` | `True` | Verified platform post ID remains unrecorded. |
| `no_export_file_created` | `no_file` | `no_file` | `True` | Checked local workspace; no export files exist. |
| `no_clipboard_payload_created` | `no_clipboard` | `no_clipboard` | `True` | Verified clipboard payload remains ungenerated. |
| `no_download_artifact_created` | `no_download` | `no_download` | `True` | Verified no download artifact created. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_financial_advice` | `absent` | `absent` | `True` | Verified draft does not contain financial advice. |
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_metrics_gate` | `required` | `required` | `True` | Verified performance metrics gate is required. |
| `require_performance_audit_gate` | `required` | `required` | `True` | Verified performance audit gate is required. |

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
- `blocked_no_performance_audit_gate`
