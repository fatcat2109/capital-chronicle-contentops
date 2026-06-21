# Performance Summary Stub to Content Feedback Precheck Contract

> [!IMPORTANT]
> This is a content feedback precheck contract, not content feedback and not editorial advice.
> It creates blocked content feedback precheck metadata and non-public feedback references only.
> It preserves citation, limitation, DQR/readiness, operator identity, signature, hash-lock, metrics-gate, performance-audit-gate, content-feedback-gate, account-binding, credential, and dispatch-gate requirements.
> It cannot generate feedback, rewrite suggestions, recommendations, platform strategy, scores, rankings, claims, pull analytics, scrape platforms, create publishable copy, approvals, dispatches, schedules, or platform/API calls.

- **Task Label**: `TASK_CONTENTOPS_0175BA_PERFORMANCE_SUMMARY_STUB_TO_CONTENT_FEEDBACK_PRECHECK_V0`
- **Matrix Version**: `0175BA_PERFORMANCE_SUMMARY_STUB_TO_CONTENT_FEEDBACK_PRECHECK_V1`
- **Source Baseline Commit**: `888d6c34b31daa107056bb5a56ab0d5e7430e49b`
- **Packet Hash**: `8cf8a7118719702a2adb0c2db5c4031d73c7ad3310e499dc76855a2295f7cadb`
- **Ledger Family**: `performance_summary_stub_to_content_feedback_precheck_future`
- **Next Required Gate**: `lane_c_content_feedback_precheck_to_feedback_stub`

## Invariant Validation Safety Flags

| Invariant Flag | Required State | Status |
|---|---|---|
| `local_only` | `True` | ✅ |
| `fixture_only` | `True` | ✅ |
| `schema_only` | `True` | ✅ |
| `content_feedback_precheck_only` | `True` | ✅ |
| `performance_summary_stub_only` | `True` | ✅ |
| `performance_audit_precheck_only` | `True` | ✅ |
| `metrics_record_stub_only` | `True` | ✅ |
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
| `publishable_copy_created` | `False` | ✅ |
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
| `metric_score_computed` | `False` | ✅ |
| `kpi_comparison_computed` | `False` | ✅ |
| `performance_claim_generated` | `False` | ✅ |
| `recommendation_generated` | `False` | ✅ |
| `optimization_suggestion_generated` | `False` | ✅ |
| `platform_strategy_generated` | `False` | ✅ |
| `content_score_computed` | `False` | ✅ |
| `ranking_generated` | `False` | ✅ |
| `best_or_worst_claim_generated` | `False` | ✅ |
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

- **Registered Content Feedback Precheck Records**: `10`
- **Registered Content Feedback Targets**: `10`
- **Invariants Checked**: `37`
- **Placeholder Feedback References Defined**: `42`

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
- `content_editorial_revisions`
- `platform_strategy_planning`

### Missing Future Gates
- `lane_c_content_feedback_precheck_to_feedback_stub`
- `production_key_vault_decrypter`
- `live_operator_signature_vault`

## Content Feedback Target Configurations

| Platform Target ID | Feedback Target Type | Description |
|---|---|---|
| `x` | `x_content_feedback_precheck` | Content feedback precheck for X platform |
| `telegram_channel_destination` | `telegram_channel_content_feedback_precheck` | Content feedback precheck for Telegram channel |
| `telegram_remote_operator` | `telegram_remote_operator_log_content_feedback_precheck` | Content feedback precheck for Telegram remote operator |
| `substack` | `substack_content_feedback_precheck` | Content feedback precheck for Substack |
| `linkedin` | `linkedin_content_feedback_precheck` | Content feedback precheck for LinkedIn |
| `threads` | `threads_content_feedback_precheck` | Content feedback precheck for Meta Threads |
| `instagram` | `instagram_content_feedback_precheck` | Content feedback precheck for Instagram |
| `facebook_page` | `facebook_page_content_feedback_precheck` | Content feedback precheck for Facebook Page |
| `tiktok` | `tiktok_content_feedback_precheck` | Content feedback precheck for TikTok |
| `youtube` | `youtube_content_feedback_precheck` | Content feedback precheck for YouTube |

## Platform Content Feedback Prechecks

### Content Feedback Precheck Record: `content_feedback_precheck_x`

- **Source Performance Summary Stub ID**: `performance_summary_stub_x`
- **Source Performance Audit Precheck ID**: `performance_audit_precheck_x`
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
- **Content Feedback Precheck Status**: `content_feedback_precheck_blocked`
- **Feedback Target Type**: `x_content_feedback_precheck`
- **Summary Stub Type**: `x_performance_summary_stub`
- **Feedback Generated**: `False`
- **Rewrite Suggestion Generated**: `False`
- **Recommendation Generated**: `False`
- **Optimization Suggestion Generated**: `False`
- **Platform Strategy Generated**: `False`
- **Content Score Computed**: `False`
- **Rank Generated**: `False`
- **Best or Worst Claim Generated**: `False`
- **Performance Claim Generated**: `False`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
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
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Content Feedback Gate**: `content_feedback_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Feedback References

| Reference Name | Source Summary Field | Requires Human Editorial Review |
|---|---|---|
| `hook_feedback_stub` | `hook_feedback_stub` | `True` |
| `clarity_feedback_stub` | `clarity_feedback_stub` | `True` |
| `citation_feedback_stub` | `citation_feedback_stub` | `True` |
| `limitation_feedback_stub` | `limitation_feedback_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_content_feedback_generated` | `absent` | `absent` | `True` | Verified no active content feedback or editorial revisions generated. |
| `no_rewrite_suggestion_generated` | `absent` | `absent` | `True` | Verified rewrite suggestions remain ungenerated. |
| `no_recommendation_generated` | `absent` | `absent` | `True` | Verified no performance recommendations or suggestions generated. |
| `no_optimization_suggestion_generated` | `absent` | `absent` | `True` | Verified optimization suggestions remain ungenerated. |
| `no_platform_strategy_generated` | `absent` | `absent` | `True` | Verified no platform-specific distribution strategy was generated. |
| `no_content_score_computed` | `no_score` | `no_score` | `True` | Verified no content score has been computed. |
| `no_ranking_generated` | `no_rank` | `no_rank` | `True` | Verified no platform rank generated. |
| `no_best_or_worst_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no best or worst performing claims generated. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance metrics score computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_publishable_copy_created` | `no_copy` | `no_copy` | `True` | Verified no publishable copy generated. |
| `no_public_postable` | `false` | `false` | `True` | Verified draft cannot be publicly posted. |
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
| `require_content_feedback_gate` | `required` | `required` | `True` | Verified content feedback gate is required. |

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
- `blocked_no_content_feedback_gate`

### Content Feedback Precheck Record: `content_feedback_precheck_telegram_channel_destination`

- **Source Performance Summary Stub ID**: `performance_summary_stub_telegram_channel_destination`
- **Source Performance Audit Precheck ID**: `performance_audit_precheck_telegram_channel_destination`
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
- **Content Feedback Precheck Status**: `content_feedback_precheck_blocked`
- **Feedback Target Type**: `telegram_channel_content_feedback_precheck`
- **Summary Stub Type**: `telegram_channel_performance_summary_stub`
- **Feedback Generated**: `False`
- **Rewrite Suggestion Generated**: `False`
- **Recommendation Generated**: `False`
- **Optimization Suggestion Generated**: `False`
- **Platform Strategy Generated**: `False`
- **Content Score Computed**: `False`
- **Rank Generated**: `False`
- **Best or Worst Claim Generated**: `False`
- **Performance Claim Generated**: `False`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
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
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Content Feedback Gate**: `content_feedback_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Feedback References

| Reference Name | Source Summary Field | Requires Human Editorial Review |
|---|---|---|
| `message_feedback_stub` | `message_feedback_stub` | `True` |
| `operator_context_feedback_stub` | `operator_context_feedback_stub` | `True` |
| `citation_feedback_stub` | `citation_feedback_stub` | `True` |
| `limitation_feedback_stub` | `limitation_feedback_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_content_feedback_generated` | `absent` | `absent` | `True` | Verified no active content feedback or editorial revisions generated. |
| `no_rewrite_suggestion_generated` | `absent` | `absent` | `True` | Verified rewrite suggestions remain ungenerated. |
| `no_recommendation_generated` | `absent` | `absent` | `True` | Verified no performance recommendations or suggestions generated. |
| `no_optimization_suggestion_generated` | `absent` | `absent` | `True` | Verified optimization suggestions remain ungenerated. |
| `no_platform_strategy_generated` | `absent` | `absent` | `True` | Verified no platform-specific distribution strategy was generated. |
| `no_content_score_computed` | `no_score` | `no_score` | `True` | Verified no content score has been computed. |
| `no_ranking_generated` | `no_rank` | `no_rank` | `True` | Verified no platform rank generated. |
| `no_best_or_worst_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no best or worst performing claims generated. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance metrics score computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_publishable_copy_created` | `no_copy` | `no_copy` | `True` | Verified no publishable copy generated. |
| `no_public_postable` | `false` | `false` | `True` | Verified draft cannot be publicly posted. |
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
| `require_content_feedback_gate` | `required` | `required` | `True` | Verified content feedback gate is required. |

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
- `blocked_no_content_feedback_gate`

### Content Feedback Precheck Record: `content_feedback_precheck_telegram_remote_operator`

- **Source Performance Summary Stub ID**: `performance_summary_stub_telegram_remote_operator`
- **Source Performance Audit Precheck ID**: `performance_audit_precheck_telegram_remote_operator`
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
- **Content Feedback Precheck Status**: `content_feedback_precheck_blocked`
- **Feedback Target Type**: `telegram_remote_operator_log_content_feedback_precheck`
- **Summary Stub Type**: `telegram_remote_operator_log_performance_summary_stub`
- **Feedback Generated**: `False`
- **Rewrite Suggestion Generated**: `False`
- **Recommendation Generated**: `False`
- **Optimization Suggestion Generated**: `False`
- **Platform Strategy Generated**: `False`
- **Content Score Computed**: `False`
- **Rank Generated**: `False`
- **Best or Worst Claim Generated**: `False`
- **Performance Claim Generated**: `False`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
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
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Content Feedback Gate**: `content_feedback_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Feedback References

| Reference Name | Source Summary Field | Requires Human Editorial Review |
|---|---|---|
| `operator_log_feedback_stub` | `operator_log_feedback_stub` | `True` |
| `audit_feedback_stub` | `audit_feedback_stub` | `True` |
| `manual_action_feedback_stub` | `manual_action_feedback_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_content_feedback_generated` | `absent` | `absent` | `True` | Verified no active content feedback or editorial revisions generated. |
| `no_rewrite_suggestion_generated` | `absent` | `absent` | `True` | Verified rewrite suggestions remain ungenerated. |
| `no_recommendation_generated` | `absent` | `absent` | `True` | Verified no performance recommendations or suggestions generated. |
| `no_optimization_suggestion_generated` | `absent` | `absent` | `True` | Verified optimization suggestions remain ungenerated. |
| `no_platform_strategy_generated` | `absent` | `absent` | `True` | Verified no platform-specific distribution strategy was generated. |
| `no_content_score_computed` | `no_score` | `no_score` | `True` | Verified no content score has been computed. |
| `no_ranking_generated` | `no_rank` | `no_rank` | `True` | Verified no platform rank generated. |
| `no_best_or_worst_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no best or worst performing claims generated. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance metrics score computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_publishable_copy_created` | `no_copy` | `no_copy` | `True` | Verified no publishable copy generated. |
| `no_public_postable` | `false` | `false` | `True` | Verified draft cannot be publicly posted. |
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
| `require_content_feedback_gate` | `required` | `required` | `True` | Verified content feedback gate is required. |

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
- `blocked_no_content_feedback_gate`

### Content Feedback Precheck Record: `content_feedback_precheck_substack`

- **Source Performance Summary Stub ID**: `performance_summary_stub_substack`
- **Source Performance Audit Precheck ID**: `performance_audit_precheck_substack`
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
- **Content Feedback Precheck Status**: `content_feedback_precheck_blocked`
- **Feedback Target Type**: `substack_content_feedback_precheck`
- **Summary Stub Type**: `substack_performance_summary_stub`
- **Feedback Generated**: `False`
- **Rewrite Suggestion Generated**: `False`
- **Recommendation Generated**: `False`
- **Optimization Suggestion Generated**: `False`
- **Platform Strategy Generated**: `False`
- **Content Score Computed**: `False`
- **Rank Generated**: `False`
- **Best or Worst Claim Generated**: `False`
- **Performance Claim Generated**: `False`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
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
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Content Feedback Gate**: `content_feedback_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Feedback References

| Reference Name | Source Summary Field | Requires Human Editorial Review |
|---|---|---|
| `title_feedback_stub` | `title_feedback_stub` | `True` |
| `thesis_feedback_stub` | `thesis_feedback_stub` | `True` |
| `structure_feedback_stub` | `structure_feedback_stub` | `True` |
| `citation_feedback_stub` | `citation_feedback_stub` | `True` |
| `limitation_feedback_stub` | `limitation_feedback_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_content_feedback_generated` | `absent` | `absent` | `True` | Verified no active content feedback or editorial revisions generated. |
| `no_rewrite_suggestion_generated` | `absent` | `absent` | `True` | Verified rewrite suggestions remain ungenerated. |
| `no_recommendation_generated` | `absent` | `absent` | `True` | Verified no performance recommendations or suggestions generated. |
| `no_optimization_suggestion_generated` | `absent` | `absent` | `True` | Verified optimization suggestions remain ungenerated. |
| `no_platform_strategy_generated` | `absent` | `absent` | `True` | Verified no platform-specific distribution strategy was generated. |
| `no_content_score_computed` | `no_score` | `no_score` | `True` | Verified no content score has been computed. |
| `no_ranking_generated` | `no_rank` | `no_rank` | `True` | Verified no platform rank generated. |
| `no_best_or_worst_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no best or worst performing claims generated. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance metrics score computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_publishable_copy_created` | `no_copy` | `no_copy` | `True` | Verified no publishable copy generated. |
| `no_public_postable` | `false` | `false` | `True` | Verified draft cannot be publicly posted. |
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
| `require_content_feedback_gate` | `required` | `required` | `True` | Verified content feedback gate is required. |

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
- `blocked_no_content_feedback_gate`

### Content Feedback Precheck Record: `content_feedback_precheck_linkedin`

- **Source Performance Summary Stub ID**: `performance_summary_stub_linkedin`
- **Source Performance Audit Precheck ID**: `performance_audit_precheck_linkedin`
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
- **Content Feedback Precheck Status**: `content_feedback_precheck_blocked`
- **Feedback Target Type**: `linkedin_content_feedback_precheck`
- **Summary Stub Type**: `linkedin_performance_summary_stub`
- **Feedback Generated**: `False`
- **Rewrite Suggestion Generated**: `False`
- **Recommendation Generated**: `False`
- **Optimization Suggestion Generated**: `False`
- **Platform Strategy Generated**: `False`
- **Content Score Computed**: `False`
- **Rank Generated**: `False`
- **Best or Worst Claim Generated**: `False`
- **Performance Claim Generated**: `False`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
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
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Content Feedback Gate**: `content_feedback_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Feedback References

| Reference Name | Source Summary Field | Requires Human Editorial Review |
|---|---|---|
| `professional_framing_feedback_stub` | `professional_framing_feedback_stub` | `True` |
| `body_feedback_stub` | `body_feedback_stub` | `True` |
| `citation_feedback_stub` | `citation_feedback_stub` | `True` |
| `limitation_feedback_stub` | `limitation_feedback_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_content_feedback_generated` | `absent` | `absent` | `True` | Verified no active content feedback or editorial revisions generated. |
| `no_rewrite_suggestion_generated` | `absent` | `absent` | `True` | Verified rewrite suggestions remain ungenerated. |
| `no_recommendation_generated` | `absent` | `absent` | `True` | Verified no performance recommendations or suggestions generated. |
| `no_optimization_suggestion_generated` | `absent` | `absent` | `True` | Verified optimization suggestions remain ungenerated. |
| `no_platform_strategy_generated` | `absent` | `absent` | `True` | Verified no platform-specific distribution strategy was generated. |
| `no_content_score_computed` | `no_score` | `no_score` | `True` | Verified no content score has been computed. |
| `no_ranking_generated` | `no_rank` | `no_rank` | `True` | Verified no platform rank generated. |
| `no_best_or_worst_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no best or worst performing claims generated. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance metrics score computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_publishable_copy_created` | `no_copy` | `no_copy` | `True` | Verified no publishable copy generated. |
| `no_public_postable` | `false` | `false` | `True` | Verified draft cannot be publicly posted. |
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
| `require_content_feedback_gate` | `required` | `required` | `True` | Verified content feedback gate is required. |

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
- `blocked_no_content_feedback_gate`

### Content Feedback Precheck Record: `content_feedback_precheck_threads`

- **Source Performance Summary Stub ID**: `performance_summary_stub_threads`
- **Source Performance Audit Precheck ID**: `performance_audit_precheck_threads`
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
- **Content Feedback Precheck Status**: `content_feedback_precheck_blocked`
- **Feedback Target Type**: `threads_content_feedback_precheck`
- **Summary Stub Type**: `threads_performance_summary_stub`
- **Feedback Generated**: `False`
- **Rewrite Suggestion Generated**: `False`
- **Recommendation Generated**: `False`
- **Optimization Suggestion Generated**: `False`
- **Platform Strategy Generated**: `False`
- **Content Score Computed**: `False`
- **Rank Generated**: `False`
- **Best or Worst Claim Generated**: `False`
- **Performance Claim Generated**: `False`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
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
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Content Feedback Gate**: `content_feedback_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Feedback References

| Reference Name | Source Summary Field | Requires Human Editorial Review |
|---|---|---|
| `short_text_feedback_stub` | `short_text_feedback_stub` | `True` |
| `clarity_feedback_stub` | `clarity_feedback_stub` | `True` |
| `citation_feedback_stub` | `citation_feedback_stub` | `True` |
| `limitation_feedback_stub` | `limitation_feedback_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_content_feedback_generated` | `absent` | `absent` | `True` | Verified no active content feedback or editorial revisions generated. |
| `no_rewrite_suggestion_generated` | `absent` | `absent` | `True` | Verified rewrite suggestions remain ungenerated. |
| `no_recommendation_generated` | `absent` | `absent` | `True` | Verified no performance recommendations or suggestions generated. |
| `no_optimization_suggestion_generated` | `absent` | `absent` | `True` | Verified optimization suggestions remain ungenerated. |
| `no_platform_strategy_generated` | `absent` | `absent` | `True` | Verified no platform-specific distribution strategy was generated. |
| `no_content_score_computed` | `no_score` | `no_score` | `True` | Verified no content score has been computed. |
| `no_ranking_generated` | `no_rank` | `no_rank` | `True` | Verified no platform rank generated. |
| `no_best_or_worst_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no best or worst performing claims generated. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance metrics score computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_publishable_copy_created` | `no_copy` | `no_copy` | `True` | Verified no publishable copy generated. |
| `no_public_postable` | `false` | `false` | `True` | Verified draft cannot be publicly posted. |
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
| `require_content_feedback_gate` | `required` | `required` | `True` | Verified content feedback gate is required. |

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
- `blocked_no_content_feedback_gate`

### Content Feedback Precheck Record: `content_feedback_precheck_instagram`

- **Source Performance Summary Stub ID**: `performance_summary_stub_instagram`
- **Source Performance Audit Precheck ID**: `performance_audit_precheck_instagram`
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
- **Content Feedback Precheck Status**: `content_feedback_precheck_blocked`
- **Feedback Target Type**: `instagram_content_feedback_precheck`
- **Summary Stub Type**: `instagram_performance_summary_stub`
- **Feedback Generated**: `False`
- **Rewrite Suggestion Generated**: `False`
- **Recommendation Generated**: `False`
- **Optimization Suggestion Generated**: `False`
- **Platform Strategy Generated**: `False`
- **Content Score Computed**: `False`
- **Rank Generated**: `False`
- **Best or Worst Claim Generated**: `False`
- **Performance Claim Generated**: `False`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
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
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Content Feedback Gate**: `content_feedback_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Feedback References

| Reference Name | Source Summary Field | Requires Human Editorial Review |
|---|---|---|
| `caption_feedback_stub` | `caption_feedback_stub` | `True` |
| `media_context_feedback_stub` | `media_context_feedback_stub` | `True` |
| `alt_text_feedback_stub` | `alt_text_feedback_stub` | `True` |
| `citation_feedback_stub` | `citation_feedback_stub` | `True` |
| `limitation_feedback_stub` | `limitation_feedback_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_content_feedback_generated` | `absent` | `absent` | `True` | Verified no active content feedback or editorial revisions generated. |
| `no_rewrite_suggestion_generated` | `absent` | `absent` | `True` | Verified rewrite suggestions remain ungenerated. |
| `no_recommendation_generated` | `absent` | `absent` | `True` | Verified no performance recommendations or suggestions generated. |
| `no_optimization_suggestion_generated` | `absent` | `absent` | `True` | Verified optimization suggestions remain ungenerated. |
| `no_platform_strategy_generated` | `absent` | `absent` | `True` | Verified no platform-specific distribution strategy was generated. |
| `no_content_score_computed` | `no_score` | `no_score` | `True` | Verified no content score has been computed. |
| `no_ranking_generated` | `no_rank` | `no_rank` | `True` | Verified no platform rank generated. |
| `no_best_or_worst_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no best or worst performing claims generated. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance metrics score computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_publishable_copy_created` | `no_copy` | `no_copy` | `True` | Verified no publishable copy generated. |
| `no_public_postable` | `false` | `false` | `True` | Verified draft cannot be publicly posted. |
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
| `require_content_feedback_gate` | `required` | `required` | `True` | Verified content feedback gate is required. |

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
- `blocked_no_content_feedback_gate`

### Content Feedback Precheck Record: `content_feedback_precheck_facebook_page`

- **Source Performance Summary Stub ID**: `performance_summary_stub_facebook_page`
- **Source Performance Audit Precheck ID**: `performance_audit_precheck_facebook_page`
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
- **Content Feedback Precheck Status**: `content_feedback_precheck_blocked`
- **Feedback Target Type**: `facebook_page_content_feedback_precheck`
- **Summary Stub Type**: `facebook_page_performance_summary_stub`
- **Feedback Generated**: `False`
- **Rewrite Suggestion Generated**: `False`
- **Recommendation Generated**: `False`
- **Optimization Suggestion Generated**: `False`
- **Platform Strategy Generated**: `False`
- **Content Score Computed**: `False`
- **Rank Generated**: `False`
- **Best or Worst Claim Generated**: `False`
- **Performance Claim Generated**: `False`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
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
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Content Feedback Gate**: `content_feedback_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Feedback References

| Reference Name | Source Summary Field | Requires Human Editorial Review |
|---|---|---|
| `post_text_feedback_stub` | `post_text_feedback_stub` | `True` |
| `attachment_context_feedback_stub` | `attachment_context_feedback_stub` | `True` |
| `citation_feedback_stub` | `citation_feedback_stub` | `True` |
| `limitation_feedback_stub` | `limitation_feedback_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_content_feedback_generated` | `absent` | `absent` | `True` | Verified no active content feedback or editorial revisions generated. |
| `no_rewrite_suggestion_generated` | `absent` | `absent` | `True` | Verified rewrite suggestions remain ungenerated. |
| `no_recommendation_generated` | `absent` | `absent` | `True` | Verified no performance recommendations or suggestions generated. |
| `no_optimization_suggestion_generated` | `absent` | `absent` | `True` | Verified optimization suggestions remain ungenerated. |
| `no_platform_strategy_generated` | `absent` | `absent` | `True` | Verified no platform-specific distribution strategy was generated. |
| `no_content_score_computed` | `no_score` | `no_score` | `True` | Verified no content score has been computed. |
| `no_ranking_generated` | `no_rank` | `no_rank` | `True` | Verified no platform rank generated. |
| `no_best_or_worst_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no best or worst performing claims generated. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance metrics score computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_publishable_copy_created` | `no_copy` | `no_copy` | `True` | Verified no publishable copy generated. |
| `no_public_postable` | `false` | `false` | `True` | Verified draft cannot be publicly posted. |
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
| `require_content_feedback_gate` | `required` | `required` | `True` | Verified content feedback gate is required. |

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
- `blocked_no_content_feedback_gate`

### Content Feedback Precheck Record: `content_feedback_precheck_tiktok`

- **Source Performance Summary Stub ID**: `performance_summary_stub_tiktok`
- **Source Performance Audit Precheck ID**: `performance_audit_precheck_tiktok`
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
- **Content Feedback Precheck Status**: `content_feedback_precheck_blocked`
- **Feedback Target Type**: `tiktok_content_feedback_precheck`
- **Summary Stub Type**: `tiktok_performance_summary_stub`
- **Feedback Generated**: `False`
- **Rewrite Suggestion Generated**: `False`
- **Recommendation Generated**: `False`
- **Optimization Suggestion Generated**: `False`
- **Platform Strategy Generated**: `False`
- **Content Score Computed**: `False`
- **Rank Generated**: `False`
- **Best or Worst Claim Generated**: `False`
- **Performance Claim Generated**: `False`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
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
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Content Feedback Gate**: `content_feedback_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Feedback References

| Reference Name | Source Summary Field | Requires Human Editorial Review |
|---|---|---|
| `caption_feedback_stub` | `caption_feedback_stub` | `True` |
| `video_context_feedback_stub` | `video_context_feedback_stub` | `True` |
| `disclosure_feedback_stub` | `disclosure_feedback_stub` | `True` |
| `citation_feedback_stub` | `citation_feedback_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_content_feedback_generated` | `absent` | `absent` | `True` | Verified no active content feedback or editorial revisions generated. |
| `no_rewrite_suggestion_generated` | `absent` | `absent` | `True` | Verified rewrite suggestions remain ungenerated. |
| `no_recommendation_generated` | `absent` | `absent` | `True` | Verified no performance recommendations or suggestions generated. |
| `no_optimization_suggestion_generated` | `absent` | `absent` | `True` | Verified optimization suggestions remain ungenerated. |
| `no_platform_strategy_generated` | `absent` | `absent` | `True` | Verified no platform-specific distribution strategy was generated. |
| `no_content_score_computed` | `no_score` | `no_score` | `True` | Verified no content score has been computed. |
| `no_ranking_generated` | `no_rank` | `no_rank` | `True` | Verified no platform rank generated. |
| `no_best_or_worst_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no best or worst performing claims generated. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance metrics score computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_publishable_copy_created` | `no_copy` | `no_copy` | `True` | Verified no publishable copy generated. |
| `no_public_postable` | `false` | `false` | `True` | Verified draft cannot be publicly posted. |
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
| `require_content_feedback_gate` | `required` | `required` | `True` | Verified content feedback gate is required. |

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
- `blocked_no_content_feedback_gate`

### Content Feedback Precheck Record: `content_feedback_precheck_youtube`

- **Source Performance Summary Stub ID**: `performance_summary_stub_youtube`
- **Source Performance Audit Precheck ID**: `performance_audit_precheck_youtube`
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
- **Content Feedback Precheck Status**: `content_feedback_precheck_blocked`
- **Feedback Target Type**: `youtube_content_feedback_precheck`
- **Summary Stub Type**: `youtube_performance_summary_stub`
- **Feedback Generated**: `False`
- **Rewrite Suggestion Generated**: `False`
- **Recommendation Generated**: `False`
- **Optimization Suggestion Generated**: `False`
- **Platform Strategy Generated**: `False`
- **Content Score Computed**: `False`
- **Rank Generated**: `False`
- **Best or Worst Claim Generated**: `False`
- **Performance Claim Generated**: `False`
- **Real Metrics Recorded**: `False`
- **Metric Values Recorded**: `False`
- **Platform Publication URL Recorded**: `False`
- **Platform Post ID Recorded**: `False`
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
- **Metrics Gate**: `metrics_gate_required_but_locked`
- **Performance Audit Gate**: `performance_audit_gate_required_but_locked`
- **Content Feedback Gate**: `content_feedback_gate_required_but_locked`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`

#### Feedback References

| Reference Name | Source Summary Field | Requires Human Editorial Review |
|---|---|---|
| `title_feedback_stub` | `title_feedback_stub` | `True` |
| `description_feedback_stub` | `description_feedback_stub` | `True` |
| `video_context_feedback_stub` | `video_context_feedback_stub` | `True` |
| `citation_feedback_stub` | `citation_feedback_stub` | `True` |
| `limitation_feedback_stub` | `limitation_feedback_stub` | `True` |

#### Evaluation Invariants

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
| `no_content_feedback_generated` | `absent` | `absent` | `True` | Verified no active content feedback or editorial revisions generated. |
| `no_rewrite_suggestion_generated` | `absent` | `absent` | `True` | Verified rewrite suggestions remain ungenerated. |
| `no_recommendation_generated` | `absent` | `absent` | `True` | Verified no performance recommendations or suggestions generated. |
| `no_optimization_suggestion_generated` | `absent` | `absent` | `True` | Verified optimization suggestions remain ungenerated. |
| `no_platform_strategy_generated` | `absent` | `absent` | `True` | Verified no platform-specific distribution strategy was generated. |
| `no_content_score_computed` | `no_score` | `no_score` | `True` | Verified no content score has been computed. |
| `no_ranking_generated` | `no_rank` | `no_rank` | `True` | Verified no platform rank generated. |
| `no_best_or_worst_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no best or worst performing claims generated. |
| `no_performance_claim_generated` | `no_claim` | `no_claim` | `True` | Verified no performance claims or analytics texts were generated. |
| `no_real_metrics_recorded` | `no_record` | `no_record` | `True` | Verified no real platform performance metrics recorded. |
| `no_metric_values_recorded` | `no_record` | `no_record` | `True` | Verified metric values are unrecorded. |
| `no_metric_score_computed` | `no_score` | `no_score` | `True` | Verified no performance metrics score computed. |
| `no_kpi_comparison_computed` | `no_comparison` | `no_comparison` | `True` | Verified no KPI comparison has been performed. |
| `no_platform_analytics_pull` | `no_pull` | `no_pull` | `True` | Verified no active analytics pulls were executed. |
| `no_scraping` | `disabled` | `disabled` | `True` | Verified scraping is blocked. |
| `no_provider_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no provider LLM API calls executed. |
| `no_platform_api_call` | `no_api_calls` | `no_api_calls` | `True` | Verified no platform API calls executed. |
| `no_credential_or_env_read` | `no_reads` | `no_reads` | `True` | Verified no credentials or environment read operations performed. |
| `no_account_binding_active` | `inactive` | `inactive` | `True` | Verified no account binding is active. |
| `no_scheduler` | `disabled` | `disabled` | `True` | Verified no scheduler enabled. |
| `no_autonomous_posting` | `disabled` | `disabled` | `True` | Verified autonomous posting is blocked. |
| `no_autonomous_reply_or_dm` | `disabled` | `disabled` | `True` | Verified autonomous replies and DMs are blocked. |
| `no_publishable_payload_created` | `no_payload` | `no_payload` | `True` | Verified no publishable payload created. |
| `no_platform_payload_created` | `no_payload` | `no_payload` | `True` | Verified platform payload is not generated. |
| `no_publishable_copy_created` | `no_copy` | `no_copy` | `True` | Verified no publishable copy generated. |
| `no_public_postable` | `false` | `false` | `True` | Verified draft cannot be publicly posted. |
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
| `require_content_feedback_gate` | `required` | `required` | `True` | Verified content feedback gate is required. |

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
- `blocked_no_content_feedback_gate`
