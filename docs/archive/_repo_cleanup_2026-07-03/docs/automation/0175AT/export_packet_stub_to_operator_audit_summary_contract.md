# Export Packet Stub to Operator Audit Summary Contract

> [!IMPORTANT]
> This is an operator audit summary contract, not a signed audit and not manual export.
> It summarizes blocked export packet stubs using metadata only.
> It preserves citation, limitation, DQR/readiness, operator identity, signature, hash-lock, export-gate, account-binding, credential, and dispatch-gate requirements.
> It cannot create files, clipboard payloads, downloads, approvals, exports, publishable payloads, dispatches, schedules, manual publish records, or platform/API calls.

- **Task Label**: `TASK_CONTENTOPS_0175AT_EXPORT_PACKET_STUB_TO_OPERATOR_AUDIT_SUMMARY_V0`
- **Matrix Version**: `0175AT_EXPORT_PACKET_STUB_TO_OPERATOR_AUDIT_SUMMARY_V1`
- **Source Baseline Commit**: `3441635cad8010a7325d83d856351275f897ce37`
- **Packet Hash**: `978f302d87f896bf38f2c729393009f21802e338553ead5c752232a976783514`
- **Ledger Family**: `export_packet_stub_to_operator_audit_summary_future`
- **Next Required Gate**: `lane_c_platform_operator_audit_summary_to_manual_publish_record_precheck`

## Invariant Validation Safety Flags

| Invariant Flag | Required State | Status |
|---|---|---|
| `local_only` | `True` | ✅ |
| `fixture_only` | `True` | ✅ |
| `schema_only` | `True` | ✅ |
| `operator_audit_summary_only` | `True` | ✅ |
| `export_packet_stub_only` | `True` | ✅ |
| `manual_export_precheck_only` | `True` | ✅ |
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

## Operator Audit Summary Counts

- **Registered Operator Audit Summary Records**: `10`
- **Registered Operator Audit Summary Subjects**: `10`
- **Operator Audit Invariants Checked**: `22`
- **Operator Audit Findings Documented**: `8`

## Blocked Capabilities & Missing Gates

### Blocked Capabilities
- `live_publishing_dispatch`
- `autonomous_reply_automation`
- `live_credential_hydration`
- `active_scheduler_triggers`
- `manual_review_export`

### Missing Future Gates
- `lane_c_platform_operator_audit_summary_to_manual_publish_record_precheck`
- `production_key_vault_decrypter`
- `live_operator_signature_vault`

## Operator Audit Summary Subject Configurations

| Platform Target ID | Audit Subject Type | Description |
|---|---|---|
| `x` | `x_export_stub_audit_summary` | Audit summary for X platform manual export packet stub |
| `telegram_channel_destination` | `telegram_channel_export_stub_audit_summary` | Audit summary for Telegram channel manual export packet stub |
| `telegram_remote_operator` | `telegram_remote_operator_export_stub_audit_summary` | Audit summary for Telegram remote operator manual export packet stub |
| `substack` | `substack_export_stub_audit_summary` | Audit summary for Substack manual export packet stub |
| `linkedin` | `linkedin_export_stub_audit_summary` | Audit summary for LinkedIn manual export packet stub |
| `threads` | `threads_export_stub_audit_summary` | Audit summary for Meta Threads manual export packet stub |
| `instagram` | `instagram_export_stub_audit_summary` | Audit summary for Instagram manual export packet stub |
| `facebook_page` | `facebook_page_export_stub_audit_summary` | Audit summary for Facebook Page manual export packet stub |
| `tiktok` | `tiktok_export_stub_audit_summary` | Audit summary for TikTok manual export packet stub |
| `youtube` | `youtube_export_stub_audit_summary` | Audit summary for YouTube manual export packet stub |

## Platform Export Packet Stub to Operator Audit Summary Records

### Audit Summary Record: `audit_summary_x`

- **Source Export Packet Stub ID**: `export_packet_stub_x`
- **Source Manual Export Precheck ID**: `manual_export_precheck_x`
- **Source Decision Gate ID**: `decision_gate_x`
- **Platform Target ID**: `x`
- **Platform Family**: `x_microblog`
- **Audit Summary Status**: `operator_audit_summary_blocked`
- **Audit Subject Type**: `x_export_stub_audit_summary`
- **Export Packet Type**: `x_manual_copy_packet_stub`
- **Stub Status**: `export_packet_stub_blocked`
- **Publishability Status**: `publishability_required_but_blocked`
- **Manual Export Status**: `manual_export_blocked`
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

- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Operator Audit Invariants (All Checked)

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
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
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order execution terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_export_gate` | `required` | `required` | `True` | Verified manual export gate is required. |
| `require_future_manual_publish_record_precheck` | `required` | `required` | `True` | Verified next step requires manual publish record precheck gate. |

#### Documented Findings

| Finding ID | Description | Active Status |
|---|---|---|
| `finding_export_stub_blocked` | The export packet stub is currently blocked from release. | `True` |
| `finding_no_publishable_text` | No publishable text has been compiled or made public. | `True` |
| `finding_no_export_outputs` | No physical export files, clipboards, or download artifacts exist. | `True` |
| `finding_no_operator_signature` | Cryptographic approval signature is missing from the audit log. | `True` |
| `finding_payload_hash_not_locked` | Draft payload hash lock is not secured. | `True` |
| `finding_citations_unresolved` | Citations are preserved as unresolved stubs. | `True` |
| `finding_limitations_unresolved` | Platform limitation acknowledgements are pending. | `True` |
| `finding_dqr_readiness_unresolved` | DQR readiness checks are unresolved. | `True` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_export_gate`
- `blocked_no_export_output`

### Audit Summary Record: `audit_summary_telegram_channel_destination`

- **Source Export Packet Stub ID**: `export_packet_stub_telegram_channel_destination`
- **Source Manual Export Precheck ID**: `manual_export_precheck_telegram_channel_destination`
- **Source Decision Gate ID**: `decision_gate_telegram_channel_destination`
- **Platform Target ID**: `telegram_channel_destination`
- **Platform Family**: `telegram_chat`
- **Audit Summary Status**: `operator_audit_summary_blocked`
- **Audit Subject Type**: `telegram_channel_export_stub_audit_summary`
- **Export Packet Type**: `telegram_channel_manual_copy_packet_stub`
- **Stub Status**: `export_packet_stub_blocked`
- **Publishability Status**: `publishability_required_but_blocked`
- **Manual Export Status**: `manual_export_blocked`
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

- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Operator Audit Invariants (All Checked)

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
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
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order execution terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_export_gate` | `required` | `required` | `True` | Verified manual export gate is required. |
| `require_future_manual_publish_record_precheck` | `required` | `required` | `True` | Verified next step requires manual publish record precheck gate. |

#### Documented Findings

| Finding ID | Description | Active Status |
|---|---|---|
| `finding_export_stub_blocked` | The export packet stub is currently blocked from release. | `True` |
| `finding_no_publishable_text` | No publishable text has been compiled or made public. | `True` |
| `finding_no_export_outputs` | No physical export files, clipboards, or download artifacts exist. | `True` |
| `finding_no_operator_signature` | Cryptographic approval signature is missing from the audit log. | `True` |
| `finding_payload_hash_not_locked` | Draft payload hash lock is not secured. | `True` |
| `finding_citations_unresolved` | Citations are preserved as unresolved stubs. | `True` |
| `finding_limitations_unresolved` | Platform limitation acknowledgements are pending. | `True` |
| `finding_dqr_readiness_unresolved` | DQR readiness checks are unresolved. | `True` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_export_gate`
- `blocked_no_export_output`

### Audit Summary Record: `audit_summary_telegram_remote_operator`

- **Source Export Packet Stub ID**: `export_packet_stub_telegram_remote_operator`
- **Source Manual Export Precheck ID**: `manual_export_precheck_telegram_remote_operator`
- **Source Decision Gate ID**: `decision_gate_telegram_remote_operator`
- **Platform Target ID**: `telegram_remote_operator`
- **Platform Family**: `telegram_chat`
- **Audit Summary Status**: `operator_audit_summary_blocked`
- **Audit Subject Type**: `telegram_remote_operator_export_stub_audit_summary`
- **Export Packet Type**: `telegram_remote_operator_review_log_packet_stub`
- **Stub Status**: `export_packet_stub_blocked`
- **Publishability Status**: `publishability_required_but_blocked`
- **Manual Export Status**: `manual_export_blocked`
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

- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Operator Audit Invariants (All Checked)

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
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
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order execution terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_export_gate` | `required` | `required` | `True` | Verified manual export gate is required. |
| `require_future_manual_publish_record_precheck` | `required` | `required` | `True` | Verified next step requires manual publish record precheck gate. |

#### Documented Findings

| Finding ID | Description | Active Status |
|---|---|---|
| `finding_export_stub_blocked` | The export packet stub is currently blocked from release. | `True` |
| `finding_no_publishable_text` | No publishable text has been compiled or made public. | `True` |
| `finding_no_export_outputs` | No physical export files, clipboards, or download artifacts exist. | `True` |
| `finding_no_operator_signature` | Cryptographic approval signature is missing from the audit log. | `True` |
| `finding_payload_hash_not_locked` | Draft payload hash lock is not secured. | `True` |
| `finding_citations_unresolved` | Citations are preserved as unresolved stubs. | `True` |
| `finding_limitations_unresolved` | Platform limitation acknowledgements are pending. | `True` |
| `finding_dqr_readiness_unresolved` | DQR readiness checks are unresolved. | `True` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_export_gate`
- `blocked_no_export_output`

### Audit Summary Record: `audit_summary_substack`

- **Source Export Packet Stub ID**: `export_packet_stub_substack`
- **Source Manual Export Precheck ID**: `manual_export_precheck_substack`
- **Source Decision Gate ID**: `decision_gate_substack`
- **Platform Target ID**: `substack`
- **Platform Family**: `substack_newsletter`
- **Audit Summary Status**: `operator_audit_summary_blocked`
- **Audit Subject Type**: `substack_export_stub_audit_summary`
- **Export Packet Type**: `substack_manual_markdown_packet_stub`
- **Stub Status**: `export_packet_stub_blocked`
- **Publishability Status**: `publishability_required_but_blocked`
- **Manual Export Status**: `manual_export_blocked`
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

- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Operator Audit Invariants (All Checked)

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
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
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order execution terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_export_gate` | `required` | `required` | `True` | Verified manual export gate is required. |
| `require_future_manual_publish_record_precheck` | `required` | `required` | `True` | Verified next step requires manual publish record precheck gate. |

#### Documented Findings

| Finding ID | Description | Active Status |
|---|---|---|
| `finding_export_stub_blocked` | The export packet stub is currently blocked from release. | `True` |
| `finding_no_publishable_text` | No publishable text has been compiled or made public. | `True` |
| `finding_no_export_outputs` | No physical export files, clipboards, or download artifacts exist. | `True` |
| `finding_no_operator_signature` | Cryptographic approval signature is missing from the audit log. | `True` |
| `finding_payload_hash_not_locked` | Draft payload hash lock is not secured. | `True` |
| `finding_citations_unresolved` | Citations are preserved as unresolved stubs. | `True` |
| `finding_limitations_unresolved` | Platform limitation acknowledgements are pending. | `True` |
| `finding_dqr_readiness_unresolved` | DQR readiness checks are unresolved. | `True` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_export_gate`
- `blocked_no_export_output`

### Audit Summary Record: `audit_summary_linkedin`

- **Source Export Packet Stub ID**: `export_packet_stub_linkedin`
- **Source Manual Export Precheck ID**: `manual_export_precheck_linkedin`
- **Source Decision Gate ID**: `decision_gate_linkedin`
- **Platform Target ID**: `linkedin`
- **Platform Family**: `linkedin_professional`
- **Audit Summary Status**: `operator_audit_summary_blocked`
- **Audit Subject Type**: `linkedin_export_stub_audit_summary`
- **Export Packet Type**: `linkedin_manual_copy_packet_stub`
- **Stub Status**: `export_packet_stub_blocked`
- **Publishability Status**: `publishability_required_but_blocked`
- **Manual Export Status**: `manual_export_blocked`
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

- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Operator Audit Invariants (All Checked)

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
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
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order execution terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_export_gate` | `required` | `required` | `True` | Verified manual export gate is required. |
| `require_future_manual_publish_record_precheck` | `required` | `required` | `True` | Verified next step requires manual publish record precheck gate. |

#### Documented Findings

| Finding ID | Description | Active Status |
|---|---|---|
| `finding_export_stub_blocked` | The export packet stub is currently blocked from release. | `True` |
| `finding_no_publishable_text` | No publishable text has been compiled or made public. | `True` |
| `finding_no_export_outputs` | No physical export files, clipboards, or download artifacts exist. | `True` |
| `finding_no_operator_signature` | Cryptographic approval signature is missing from the audit log. | `True` |
| `finding_payload_hash_not_locked` | Draft payload hash lock is not secured. | `True` |
| `finding_citations_unresolved` | Citations are preserved as unresolved stubs. | `True` |
| `finding_limitations_unresolved` | Platform limitation acknowledgements are pending. | `True` |
| `finding_dqr_readiness_unresolved` | DQR readiness checks are unresolved. | `True` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_export_gate`
- `blocked_no_export_output`

### Audit Summary Record: `audit_summary_threads`

- **Source Export Packet Stub ID**: `export_packet_stub_threads`
- **Source Manual Export Precheck ID**: `manual_export_precheck_threads`
- **Source Decision Gate ID**: `decision_gate_threads`
- **Platform Target ID**: `threads`
- **Platform Family**: `threads_microblog`
- **Audit Summary Status**: `operator_audit_summary_blocked`
- **Audit Subject Type**: `threads_export_stub_audit_summary`
- **Export Packet Type**: `threads_manual_copy_packet_stub`
- **Stub Status**: `export_packet_stub_blocked`
- **Publishability Status**: `publishability_required_but_blocked`
- **Manual Export Status**: `manual_export_blocked`
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

- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Operator Audit Invariants (All Checked)

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
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
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order execution terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_export_gate` | `required` | `required` | `True` | Verified manual export gate is required. |
| `require_future_manual_publish_record_precheck` | `required` | `required` | `True` | Verified next step requires manual publish record precheck gate. |

#### Documented Findings

| Finding ID | Description | Active Status |
|---|---|---|
| `finding_export_stub_blocked` | The export packet stub is currently blocked from release. | `True` |
| `finding_no_publishable_text` | No publishable text has been compiled or made public. | `True` |
| `finding_no_export_outputs` | No physical export files, clipboards, or download artifacts exist. | `True` |
| `finding_no_operator_signature` | Cryptographic approval signature is missing from the audit log. | `True` |
| `finding_payload_hash_not_locked` | Draft payload hash lock is not secured. | `True` |
| `finding_citations_unresolved` | Citations are preserved as unresolved stubs. | `True` |
| `finding_limitations_unresolved` | Platform limitation acknowledgements are pending. | `True` |
| `finding_dqr_readiness_unresolved` | DQR readiness checks are unresolved. | `True` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_export_gate`
- `blocked_no_export_output`

### Audit Summary Record: `audit_summary_instagram`

- **Source Export Packet Stub ID**: `export_packet_stub_instagram`
- **Source Manual Export Precheck ID**: `manual_export_precheck_instagram`
- **Source Decision Gate ID**: `decision_gate_instagram`
- **Platform Target ID**: `instagram`
- **Platform Family**: `instagram_media`
- **Audit Summary Status**: `operator_audit_summary_blocked`
- **Audit Subject Type**: `instagram_export_stub_audit_summary`
- **Export Packet Type**: `instagram_caption_media_manual_packet_stub`
- **Stub Status**: `export_packet_stub_blocked`
- **Publishability Status**: `publishability_required_but_blocked`
- **Manual Export Status**: `manual_export_blocked`
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

- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Operator Audit Invariants (All Checked)

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
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
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order execution terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_export_gate` | `required` | `required` | `True` | Verified manual export gate is required. |
| `require_future_manual_publish_record_precheck` | `required` | `required` | `True` | Verified next step requires manual publish record precheck gate. |

#### Documented Findings

| Finding ID | Description | Active Status |
|---|---|---|
| `finding_export_stub_blocked` | The export packet stub is currently blocked from release. | `True` |
| `finding_no_publishable_text` | No publishable text has been compiled or made public. | `True` |
| `finding_no_export_outputs` | No physical export files, clipboards, or download artifacts exist. | `True` |
| `finding_no_operator_signature` | Cryptographic approval signature is missing from the audit log. | `True` |
| `finding_payload_hash_not_locked` | Draft payload hash lock is not secured. | `True` |
| `finding_citations_unresolved` | Citations are preserved as unresolved stubs. | `True` |
| `finding_limitations_unresolved` | Platform limitation acknowledgements are pending. | `True` |
| `finding_dqr_readiness_unresolved` | DQR readiness checks are unresolved. | `True` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_export_gate`
- `blocked_no_export_output`

### Audit Summary Record: `audit_summary_facebook_page`

- **Source Export Packet Stub ID**: `export_packet_stub_facebook_page`
- **Source Manual Export Precheck ID**: `manual_export_precheck_facebook_page`
- **Source Decision Gate ID**: `decision_gate_facebook_page`
- **Platform Target ID**: `facebook_page`
- **Platform Family**: `facebook_page_media`
- **Audit Summary Status**: `operator_audit_summary_blocked`
- **Audit Subject Type**: `facebook_page_export_stub_audit_summary`
- **Export Packet Type**: `facebook_page_manual_copy_packet_stub`
- **Stub Status**: `export_packet_stub_blocked`
- **Publishability Status**: `publishability_required_but_blocked`
- **Manual Export Status**: `manual_export_blocked`
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

- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Operator Audit Invariants (All Checked)

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
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
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order execution terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_export_gate` | `required` | `required` | `True` | Verified manual export gate is required. |
| `require_future_manual_publish_record_precheck` | `required` | `required` | `True` | Verified next step requires manual publish record precheck gate. |

#### Documented Findings

| Finding ID | Description | Active Status |
|---|---|---|
| `finding_export_stub_blocked` | The export packet stub is currently blocked from release. | `True` |
| `finding_no_publishable_text` | No publishable text has been compiled or made public. | `True` |
| `finding_no_export_outputs` | No physical export files, clipboards, or download artifacts exist. | `True` |
| `finding_no_operator_signature` | Cryptographic approval signature is missing from the audit log. | `True` |
| `finding_payload_hash_not_locked` | Draft payload hash lock is not secured. | `True` |
| `finding_citations_unresolved` | Citations are preserved as unresolved stubs. | `True` |
| `finding_limitations_unresolved` | Platform limitation acknowledgements are pending. | `True` |
| `finding_dqr_readiness_unresolved` | DQR readiness checks are unresolved. | `True` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_export_gate`
- `blocked_no_export_output`

### Audit Summary Record: `audit_summary_tiktok`

- **Source Export Packet Stub ID**: `export_packet_stub_tiktok`
- **Source Manual Export Precheck ID**: `manual_export_precheck_tiktok`
- **Source Decision Gate ID**: `decision_gate_tiktok`
- **Platform Target ID**: `tiktok`
- **Platform Family**: `tiktok_video`
- **Audit Summary Status**: `operator_audit_summary_blocked`
- **Audit Subject Type**: `tiktok_export_stub_audit_summary`
- **Export Packet Type**: `tiktok_caption_video_manual_packet_stub`
- **Stub Status**: `export_packet_stub_blocked`
- **Publishability Status**: `publishability_required_but_blocked`
- **Manual Export Status**: `manual_export_blocked`
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

- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Operator Audit Invariants (All Checked)

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
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
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order execution terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_export_gate` | `required` | `required` | `True` | Verified manual export gate is required. |
| `require_future_manual_publish_record_precheck` | `required` | `required` | `True` | Verified next step requires manual publish record precheck gate. |

#### Documented Findings

| Finding ID | Description | Active Status |
|---|---|---|
| `finding_export_stub_blocked` | The export packet stub is currently blocked from release. | `True` |
| `finding_no_publishable_text` | No publishable text has been compiled or made public. | `True` |
| `finding_no_export_outputs` | No physical export files, clipboards, or download artifacts exist. | `True` |
| `finding_no_operator_signature` | Cryptographic approval signature is missing from the audit log. | `True` |
| `finding_payload_hash_not_locked` | Draft payload hash lock is not secured. | `True` |
| `finding_citations_unresolved` | Citations are preserved as unresolved stubs. | `True` |
| `finding_limitations_unresolved` | Platform limitation acknowledgements are pending. | `True` |
| `finding_dqr_readiness_unresolved` | DQR readiness checks are unresolved. | `True` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_export_gate`
- `blocked_no_export_output`

### Audit Summary Record: `audit_summary_youtube`

- **Source Export Packet Stub ID**: `export_packet_stub_youtube`
- **Source Manual Export Precheck ID**: `manual_export_precheck_youtube`
- **Source Decision Gate ID**: `decision_gate_youtube`
- **Platform Target ID**: `youtube`
- **Platform Family**: `youtube_video`
- **Audit Summary Status**: `operator_audit_summary_blocked`
- **Audit Subject Type**: `youtube_export_stub_audit_summary`
- **Export Packet Type**: `youtube_metadata_manual_packet_stub`
- **Stub Status**: `export_packet_stub_blocked`
- **Publishability Status**: `publishability_required_but_blocked`
- **Manual Export Status**: `manual_export_blocked`
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

- **Export Ready**: `False`
- **Manual Export Allowed**: `False`
- **Export File Created**: `False`
- **Clipboard Payload Created**: `False`
- **Download Artifact Created**: `False`
- **Publishable Payload Created**: `False`
- **Platform Payload Created**: `False`
- **Public Postable**: `False`
- **Publishable Text**: `False`
- **Platform Ready**: `False`
- **Dispatch Ready**: `False`
- **Approval Granted**: `False`
- **Approved for Publication**: `False`
- **Operator Identity Bound**: `False`
- **Operator Signature Present**: `False`
- **Payload Hash Locked**: `False`

#### Operator Audit Invariants (All Checked)

| Invariant ID | Expected State | Actual State | Passed | Evidence Note |
|---|---|---|---|---|
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
| `no_signal_language` | `absent` | `absent` | `True` | Verified draft does not contain trading signals or order execution terminology. |
| `no_market_number_fabrication` | `absent` | `absent` | `True` | Verified draft contains no fabricated market numbers. |
| `preserve_citation_requirements` | `pending` | `pending` | `True` | Verified citations are preserved as unresolved placeholders. |
| `preserve_limitations` | `pending` | `pending` | `True` | Verified limitation slot is preserved as unresolved. |
| `preserve_dqr_readiness_blocks` | `pending` | `pending` | `True` | Verified DQR readiness blocks are preserved. |
| `require_operator_signature` | `required` | `required` | `True` | Verified operator signature required for validation. |
| `require_payload_hash_lock` | `required` | `required` | `True` | Verified payload hash lock is required. |
| `require_manual_export_gate` | `required` | `required` | `True` | Verified manual export gate is required. |
| `require_future_manual_publish_record_precheck` | `required` | `required` | `True` | Verified next step requires manual publish record precheck gate. |

#### Documented Findings

| Finding ID | Description | Active Status |
|---|---|---|
| `finding_export_stub_blocked` | The export packet stub is currently blocked from release. | `True` |
| `finding_no_publishable_text` | No publishable text has been compiled or made public. | `True` |
| `finding_no_export_outputs` | No physical export files, clipboards, or download artifacts exist. | `True` |
| `finding_no_operator_signature` | Cryptographic approval signature is missing from the audit log. | `True` |
| `finding_payload_hash_not_locked` | Draft payload hash lock is not secured. | `True` |
| `finding_citations_unresolved` | Citations are preserved as unresolved stubs. | `True` |
| `finding_limitations_unresolved` | Platform limitation acknowledgements are pending. | `True` |
| `finding_dqr_readiness_unresolved` | DQR readiness checks are unresolved. | `True` |

#### Blocked Reasons (Active)

- `blocked_no_operator_signature`
- `blocked_no_payload_hash_lock`
- `blocked_unresolved_citations`
- `blocked_unresolved_limitations`
- `blocked_dqr_readiness_unresolved`
- `blocked_no_manual_export_gate`
- `blocked_no_export_output`
