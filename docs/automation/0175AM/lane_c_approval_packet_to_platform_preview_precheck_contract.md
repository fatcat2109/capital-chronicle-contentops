# Lane C Approval Packet to Platform Preview Precheck Contract

> [!IMPORTANT]
> This is a platform preview precheck report for human inspection only.
> It does not compile publishable payloads, does not perform dispatch, and does not schedule posts.
> It preserves all citations, active limitations, and missing signature requirements.

- **Task Label**: `TASK_CONTENTOPS_0175AM_LANE_C_APPROVAL_PACKET_TO_PLATFORM_PREVIEW_PRECHECK_V0`
- **Matrix Version**: `0175AM_LANE_C_APPROVAL_PACKET_TO_PLATFORM_PREVIEW_PRECHECK_V1`
- **Source Baseline Commit**: `ba81ce1851c8365cbd00f332daba2e087ea309df`
- **Packet Hash**: `8dcb619e1052efc2b28f728b1d3935330b2344e3f7ae3f1d55bbbac93834abad`
- **Ledger Family**: `lane_c_approval_packet_to_platform_preview_precheck_future`

## Invariant Validation Safety Flags

| Invariant Flag | Required State | Status |
|---|---|---|
| `local_only` | `True` | ✅ |
| `fixture_only` | `True` | ✅ |
| `network_performed` | `False` | ✅ |
| `env_read` | `False` | ✅ |
| `credential_values_loaded` | `False` | ✅ |
| `platform_api_called` | `False` | ✅ |
| `provider_api_called` | `False` | ✅ |
| `ingestion_repo_mutated` | `False` | ✅ |
| `dqr_cleared_by_contentops` | `False` | ✅ |
| `readiness_cleared_by_contentops` | `False` | ✅ |
| `current_truth_promoted` | `False` | ✅ |
| `public_postable` | `False` | ✅ |
| `dispatch_ready` | `False` | ✅ |
| `platform_payload_allowed` | `False` | ✅ |
| `platform_payload_created` | `False` | ✅ |
| `publishable_payload_created` | `False` | ✅ |
| `approved_for_publication` | `False` | ✅ |
| `scheduler_enabled` | `False` | ✅ |
| `autonomous_posting` | `False` | ✅ |
| `autonomous_reply_or_dm` | `False` | ✅ |
| `scraping` | `False` | ✅ |
| `financial_advice` | `False` | ✅ |
| `signal_language` | `False` | ✅ |
| `broker_order_execution` | `False` | ✅ |
| `raw_vendor_redistribution` | `False` | ✅ |
| `approved_internal_alpha_artifacts_available` | `False` | ✅ |

## Supported Platform Targets

| Target ID | Platform Family | Status | Limits & Notes | account_binding | credential_gate | operator_approval | hash_lock | precheck_only |
|---|---|---|---|---|---|---|---|---|
| `x` | `x_microblog` | `precheck_only` | 280 character limit with media slots | `True` | `True` | `True` | `True` | `True` |
| `telegram_channel_destination` | `telegram_chat` | `precheck_only` | 4096 characters limit for channel messages | `True` | `True` | `True` | `True` | `True` |
| `telegram_remote_operator` | `telegram_chat` | `precheck_only` | 4096 characters limit for operator logs | `True` | `True` | `True` | `True` | `True` |
| `substack` | `substack_newsletter` | `precheck_only` | standard newsletter email layout, markdown-enabled | `True` | `True` | `True` | `True` | `True` |
| `linkedin` | `linkedin_professional` | `precheck_only` | 3000 character limit professional feed structure | `True` | `True` | `True` | `True` | `True` |
| `threads` | `threads_microblog` | `precheck_only` | 500 character limit microblog shape | `True` | `True` | `True` | `True` | `True` |
| `instagram` | `instagram_media` | `precheck_only` | 2200 character limit image/caption requirement | `True` | `True` | `True` | `True` | `True` |
| `facebook_page` | `facebook_page_media` | `precheck_only` | standard page layout with attachment fields | `True` | `True` | `True` | `True` | `True` |
| `tiktok` | `tiktok_video` | `precheck_only` | caption character limit and video format details | `True` | `True` | `True` | `True` | `True` |
| `youtube` | `youtube_video` | `precheck_only` | description character limit and video metadata check | `True` | `True` | `True` | `True` | `True` |

## Precheck Evaluation Rules

| Rule ID | Description | Status |
|---|---|---|
| `no_public_postable_content` | Ensure no post is marked postable publicly without active operator override. | ✅ |
| `no_dispatch_ready_state` | Ensure no post state transitions to dispatch ready. | ✅ |
| `no_platform_payload_created` | Ensure no real platform-ready payloads are compiled or saved. | ✅ |
| `no_platform_api_call` | Enforce strict dry local-only path blocks on all network adapters. | ✅ |
| `no_credential_or_env_read` | Strict block on external dot-env or key-vault reads for platforms. | ✅ |
| `no_scheduler` | Enforce no active scheduler triggers or timers. | ✅ |
| `no_autonomous_posting` | Block any unsupervised publishing flows. | ✅ |
| `no_autonomous_reply_or_dm` | Block any automated operator responses or inbox handlers. | ✅ |
| `no_scraping` | Ensure zero active HTTP scraping rules are executed. | ✅ |
| `no_financial_advice` | Validate that no financial recommendation keywords are in payloads. | ✅ |
| `no_signal_language` | Validate that no signal/trading system descriptors are in payloads. | ✅ |
| `no_market_number_fabrication` | Validate candidate lineage to block fake stats or price estimates. | ✅ |
| `preserve_citation_requirements` | Validate citation proofs are referenced and kept un-cleared. | ✅ |
| `preserve_limitations` | Ensure active limitations remain in stub metadata. | ✅ |
| `preserve_dqr_readiness_blocks` | Block post promotion while DQR snapshot indicates unresolved details. | ✅ |
| `require_operator_review` | Always mark operator signoff requirements as active. | ✅ |
| `require_future_account_binding` | Explicitly register account binding requirements. | ✅ |
| `require_future_payload_hash_lock` | Explicitly register payload hash lock check requirements. | ✅ |

## Preview Precheck Records

| Record ID | Platform Target | Precheck Status | Preview Stub Status | dqr_status | readiness_status |
|---|---|---|---|---|---|
| `precheck_candidate_shape_valid_but_not_authorized_x` | `x` | `blocked_missing_payload_hash_lock` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_shape_valid_but_not_authorized_telegram_channel_destination` | `telegram_channel_destination` | `blocked_missing_account_binding` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_shape_valid_but_not_authorized_telegram_remote_operator` | `telegram_remote_operator` | `blocked_missing_credential_gate` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_shape_valid_but_not_authorized_substack` | `substack` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_shape_valid_but_not_authorized_linkedin` | `linkedin` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_shape_valid_but_not_authorized_threads` | `threads` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_shape_valid_but_not_authorized_instagram` | `instagram` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_shape_valid_but_not_authorized_facebook_page` | `facebook_page` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_shape_valid_but_not_authorized_tiktok` | `tiktok` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_shape_valid_but_not_authorized_youtube` | `youtube` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_lineage_manifest_x` | `x` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_lineage_manifest_telegram_channel_destination` | `telegram_channel_destination` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_lineage_manifest_telegram_remote_operator` | `telegram_remote_operator` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_lineage_manifest_substack` | `substack` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_lineage_manifest_linkedin` | `linkedin` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_lineage_manifest_threads` | `threads` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_lineage_manifest_instagram` | `instagram` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_lineage_manifest_facebook_page` | `facebook_page` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_lineage_manifest_tiktok` | `tiktok` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_lineage_manifest_youtube` | `youtube` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_stale_or_missing_freshness_x` | `x` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_stale_or_missing_freshness_telegram_channel_destination` | `telegram_channel_destination` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_stale_or_missing_freshness_telegram_remote_operator` | `telegram_remote_operator` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_stale_or_missing_freshness_substack` | `substack` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_stale_or_missing_freshness_linkedin` | `linkedin` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_stale_or_missing_freshness_threads` | `threads` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_stale_or_missing_freshness_instagram` | `instagram` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_stale_or_missing_freshness_facebook_page` | `facebook_page` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_stale_or_missing_freshness_tiktok` | `tiktok` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_stale_or_missing_freshness_youtube` | `youtube` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_degraded_proxy_label_required_x` | `x` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_degraded_proxy_label_required_telegram_channel_destination` | `telegram_channel_destination` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_degraded_proxy_label_required_telegram_remote_operator` | `telegram_remote_operator` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_degraded_proxy_label_required_substack` | `substack` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_degraded_proxy_label_required_linkedin` | `linkedin` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_degraded_proxy_label_required_threads` | `threads` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_degraded_proxy_label_required_instagram` | `instagram` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_degraded_proxy_label_required_facebook_page` | `facebook_page` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_degraded_proxy_label_required_tiktok` | `tiktok` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_degraded_proxy_label_required_youtube` | `youtube` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_operator_approval_x` | `x` | `blocked_missing_payload_hash_lock` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_operator_approval_telegram_channel_destination` | `telegram_channel_destination` | `blocked_missing_account_binding` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_operator_approval_telegram_remote_operator` | `telegram_remote_operator` | `blocked_missing_credential_gate` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_operator_approval_substack` | `substack` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_operator_approval_linkedin` | `linkedin` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_operator_approval_threads` | `threads` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_operator_approval_instagram` | `instagram` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_operator_approval_facebook_page` | `facebook_page` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_operator_approval_tiktok` | `tiktok` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_missing_operator_approval_youtube` | `youtube` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_local_fixture_only_x` | `x` | `blocked_missing_payload_hash_lock` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_local_fixture_only_telegram_channel_destination` | `telegram_channel_destination` | `blocked_missing_account_binding` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_local_fixture_only_telegram_remote_operator` | `telegram_remote_operator` | `blocked_missing_credential_gate` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_local_fixture_only_substack` | `substack` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_local_fixture_only_linkedin` | `linkedin` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_local_fixture_only_threads` | `threads` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_local_fixture_only_instagram` | `instagram` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_local_fixture_only_facebook_page` | `facebook_page` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_local_fixture_only_tiktok` | `tiktok` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_local_fixture_only_youtube` | `youtube` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_quarantined_review_only_x` | `x` | `blocked_missing_payload_hash_lock` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_quarantined_review_only_telegram_channel_destination` | `telegram_channel_destination` | `blocked_missing_account_binding` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_quarantined_review_only_telegram_remote_operator` | `telegram_remote_operator` | `blocked_missing_credential_gate` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_quarantined_review_only_substack` | `substack` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_quarantined_review_only_linkedin` | `linkedin` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_quarantined_review_only_threads` | `threads` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_quarantined_review_only_instagram` | `instagram` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_quarantined_review_only_facebook_page` | `facebook_page` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_quarantined_review_only_tiktok` | `tiktok` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_quarantined_review_only_youtube` | `youtube` | `precheck_created_blocked_for_operator_review` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_forbidden_public_ready_claim_x` | `x` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_forbidden_public_ready_claim_telegram_channel_destination` | `telegram_channel_destination` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_forbidden_public_ready_claim_telegram_remote_operator` | `telegram_remote_operator` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_forbidden_public_ready_claim_substack` | `substack` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_forbidden_public_ready_claim_linkedin` | `linkedin` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_forbidden_public_ready_claim_threads` | `threads` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_forbidden_public_ready_claim_instagram` | `instagram` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_forbidden_public_ready_claim_facebook_page` | `facebook_page` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_forbidden_public_ready_claim_tiktok` | `tiktok` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |
| `precheck_candidate_forbidden_public_ready_claim_youtube` | `youtube` | `blocked_unresolved_dqr_or_readiness` | `stub_compiled_precheck_only` | `dqr_unresolved` | `readiness_unresolved` |

## Compiled Payload Preview Stubs

### Payload Stub: `preview_stub_candidate_shape_valid_but_not_authorized_x`

- **Platform Target ID**: `x`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_shape_valid_but_not_authorized drafted content preview for x`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_shape_valid_but_not_authorized_telegram_channel_destination`

- **Platform Target ID**: `telegram_channel_destination`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_shape_valid_but_not_authorized drafted content preview for telegram_channel_destination`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_shape_valid_but_not_authorized_telegram_remote_operator`

- **Platform Target ID**: `telegram_remote_operator`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_shape_valid_but_not_authorized drafted content preview for telegram_remote_operator`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_shape_valid_but_not_authorized_substack`

- **Platform Target ID**: `substack`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_shape_valid_but_not_authorized drafted content preview for substack`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_shape_valid_but_not_authorized_linkedin`

- **Platform Target ID**: `linkedin`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_shape_valid_but_not_authorized drafted content preview for linkedin`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_shape_valid_but_not_authorized_threads`

- **Platform Target ID**: `threads`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_shape_valid_but_not_authorized drafted content preview for threads`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_shape_valid_but_not_authorized_instagram`

- **Platform Target ID**: `instagram`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_shape_valid_but_not_authorized drafted content preview for instagram`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_shape_valid_but_not_authorized_facebook_page`

- **Platform Target ID**: `facebook_page`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_shape_valid_but_not_authorized drafted content preview for facebook_page`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_shape_valid_but_not_authorized_tiktok`

- **Platform Target ID**: `tiktok`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_shape_valid_but_not_authorized drafted content preview for tiktok`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_shape_valid_but_not_authorized_youtube`

- **Platform Target ID**: `youtube`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_shape_valid_but_not_authorized drafted content preview for youtube`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_lineage_manifest_x`

- **Platform Target ID**: `x`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_lineage_manifest drafted content preview for x`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_lineage_manifest_telegram_channel_destination`

- **Platform Target ID**: `telegram_channel_destination`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_lineage_manifest drafted content preview for telegram_channel_destination`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_lineage_manifest_telegram_remote_operator`

- **Platform Target ID**: `telegram_remote_operator`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_lineage_manifest drafted content preview for telegram_remote_operator`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_lineage_manifest_substack`

- **Platform Target ID**: `substack`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_lineage_manifest drafted content preview for substack`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_lineage_manifest_linkedin`

- **Platform Target ID**: `linkedin`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_lineage_manifest drafted content preview for linkedin`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_lineage_manifest_threads`

- **Platform Target ID**: `threads`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_lineage_manifest drafted content preview for threads`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_lineage_manifest_instagram`

- **Platform Target ID**: `instagram`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_lineage_manifest drafted content preview for instagram`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_lineage_manifest_facebook_page`

- **Platform Target ID**: `facebook_page`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_lineage_manifest drafted content preview for facebook_page`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_lineage_manifest_tiktok`

- **Platform Target ID**: `tiktok`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_lineage_manifest drafted content preview for tiktok`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_lineage_manifest_youtube`

- **Platform Target ID**: `youtube`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_lineage_manifest drafted content preview for youtube`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_stale_or_missing_freshness_x`

- **Platform Target ID**: `x`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_stale_or_missing_freshness drafted content preview for x`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_stale_or_missing_freshness_telegram_channel_destination`

- **Platform Target ID**: `telegram_channel_destination`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_stale_or_missing_freshness drafted content preview for telegram_channel_destination`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_stale_or_missing_freshness_telegram_remote_operator`

- **Platform Target ID**: `telegram_remote_operator`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_stale_or_missing_freshness drafted content preview for telegram_remote_operator`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_stale_or_missing_freshness_substack`

- **Platform Target ID**: `substack`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_stale_or_missing_freshness drafted content preview for substack`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_stale_or_missing_freshness_linkedin`

- **Platform Target ID**: `linkedin`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_stale_or_missing_freshness drafted content preview for linkedin`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_stale_or_missing_freshness_threads`

- **Platform Target ID**: `threads`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_stale_or_missing_freshness drafted content preview for threads`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_stale_or_missing_freshness_instagram`

- **Platform Target ID**: `instagram`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_stale_or_missing_freshness drafted content preview for instagram`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_stale_or_missing_freshness_facebook_page`

- **Platform Target ID**: `facebook_page`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_stale_or_missing_freshness drafted content preview for facebook_page`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_stale_or_missing_freshness_tiktok`

- **Platform Target ID**: `tiktok`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_stale_or_missing_freshness drafted content preview for tiktok`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_stale_or_missing_freshness_youtube`

- **Platform Target ID**: `youtube`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_stale_or_missing_freshness drafted content preview for youtube`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_degraded_proxy_label_required_x`

- **Platform Target ID**: `x`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_degraded_proxy_label_required drafted content preview for x`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_degraded_proxy_label_required_telegram_channel_destination`

- **Platform Target ID**: `telegram_channel_destination`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_degraded_proxy_label_required drafted content preview for telegram_channel_destination`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_degraded_proxy_label_required_telegram_remote_operator`

- **Platform Target ID**: `telegram_remote_operator`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_degraded_proxy_label_required drafted content preview for telegram_remote_operator`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_degraded_proxy_label_required_substack`

- **Platform Target ID**: `substack`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_degraded_proxy_label_required drafted content preview for substack`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_degraded_proxy_label_required_linkedin`

- **Platform Target ID**: `linkedin`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_degraded_proxy_label_required drafted content preview for linkedin`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_degraded_proxy_label_required_threads`

- **Platform Target ID**: `threads`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_degraded_proxy_label_required drafted content preview for threads`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_degraded_proxy_label_required_instagram`

- **Platform Target ID**: `instagram`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_degraded_proxy_label_required drafted content preview for instagram`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_degraded_proxy_label_required_facebook_page`

- **Platform Target ID**: `facebook_page`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_degraded_proxy_label_required drafted content preview for facebook_page`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_degraded_proxy_label_required_tiktok`

- **Platform Target ID**: `tiktok`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_degraded_proxy_label_required drafted content preview for tiktok`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_degraded_proxy_label_required_youtube`

- **Platform Target ID**: `youtube`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_degraded_proxy_label_required drafted content preview for youtube`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_operator_approval_x`

- **Platform Target ID**: `x`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_operator_approval drafted content preview for x`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_operator_approval_telegram_channel_destination`

- **Platform Target ID**: `telegram_channel_destination`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_operator_approval drafted content preview for telegram_channel_destination`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_operator_approval_telegram_remote_operator`

- **Platform Target ID**: `telegram_remote_operator`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_operator_approval drafted content preview for telegram_remote_operator`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_operator_approval_substack`

- **Platform Target ID**: `substack`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_operator_approval drafted content preview for substack`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_operator_approval_linkedin`

- **Platform Target ID**: `linkedin`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_operator_approval drafted content preview for linkedin`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_operator_approval_threads`

- **Platform Target ID**: `threads`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_operator_approval drafted content preview for threads`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_operator_approval_instagram`

- **Platform Target ID**: `instagram`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_operator_approval drafted content preview for instagram`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_operator_approval_facebook_page`

- **Platform Target ID**: `facebook_page`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_operator_approval drafted content preview for facebook_page`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_operator_approval_tiktok`

- **Platform Target ID**: `tiktok`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_operator_approval drafted content preview for tiktok`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_missing_operator_approval_youtube`

- **Platform Target ID**: `youtube`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_missing_operator_approval drafted content preview for youtube`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_local_fixture_only_x`

- **Platform Target ID**: `x`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_local_fixture_only drafted content preview for x`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_local_fixture_only_telegram_channel_destination`

- **Platform Target ID**: `telegram_channel_destination`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_local_fixture_only drafted content preview for telegram_channel_destination`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_local_fixture_only_telegram_remote_operator`

- **Platform Target ID**: `telegram_remote_operator`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_local_fixture_only drafted content preview for telegram_remote_operator`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_local_fixture_only_substack`

- **Platform Target ID**: `substack`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_local_fixture_only drafted content preview for substack`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_local_fixture_only_linkedin`

- **Platform Target ID**: `linkedin`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_local_fixture_only drafted content preview for linkedin`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_local_fixture_only_threads`

- **Platform Target ID**: `threads`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_local_fixture_only drafted content preview for threads`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_local_fixture_only_instagram`

- **Platform Target ID**: `instagram`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_local_fixture_only drafted content preview for instagram`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_local_fixture_only_facebook_page`

- **Platform Target ID**: `facebook_page`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_local_fixture_only drafted content preview for facebook_page`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_local_fixture_only_tiktok`

- **Platform Target ID**: `tiktok`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_local_fixture_only drafted content preview for tiktok`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_local_fixture_only_youtube`

- **Platform Target ID**: `youtube`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_local_fixture_only drafted content preview for youtube`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_quarantined_review_only_x`

- **Platform Target ID**: `x`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_quarantined_review_only drafted content preview for x`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_quarantined_review_only_telegram_channel_destination`

- **Platform Target ID**: `telegram_channel_destination`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_quarantined_review_only drafted content preview for telegram_channel_destination`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_quarantined_review_only_telegram_remote_operator`

- **Platform Target ID**: `telegram_remote_operator`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_quarantined_review_only drafted content preview for telegram_remote_operator`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_quarantined_review_only_substack`

- **Platform Target ID**: `substack`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_quarantined_review_only drafted content preview for substack`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_quarantined_review_only_linkedin`

- **Platform Target ID**: `linkedin`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_quarantined_review_only drafted content preview for linkedin`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_quarantined_review_only_threads`

- **Platform Target ID**: `threads`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_quarantined_review_only drafted content preview for threads`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_quarantined_review_only_instagram`

- **Platform Target ID**: `instagram`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_quarantined_review_only drafted content preview for instagram`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_quarantined_review_only_facebook_page`

- **Platform Target ID**: `facebook_page`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_quarantined_review_only drafted content preview for facebook_page`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_quarantined_review_only_tiktok`

- **Platform Target ID**: `tiktok`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_quarantined_review_only drafted content preview for tiktok`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_quarantined_review_only_youtube`

- **Platform Target ID**: `youtube`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_quarantined_review_only drafted content preview for youtube`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_forbidden_public_ready_claim_x`

- **Platform Target ID**: `x`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_forbidden_public_ready_claim drafted content preview for x`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_forbidden_public_ready_claim_telegram_channel_destination`

- **Platform Target ID**: `telegram_channel_destination`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_forbidden_public_ready_claim drafted content preview for telegram_channel_destination`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_forbidden_public_ready_claim_telegram_remote_operator`

- **Platform Target ID**: `telegram_remote_operator`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_forbidden_public_ready_claim drafted content preview for telegram_remote_operator`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_forbidden_public_ready_claim_substack`

- **Platform Target ID**: `substack`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_forbidden_public_ready_claim drafted content preview for substack`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_forbidden_public_ready_claim_linkedin`

- **Platform Target ID**: `linkedin`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_forbidden_public_ready_claim drafted content preview for linkedin`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_forbidden_public_ready_claim_threads`

- **Platform Target ID**: `threads`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_forbidden_public_ready_claim drafted content preview for threads`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_forbidden_public_ready_claim_instagram`

- **Platform Target ID**: `instagram`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_forbidden_public_ready_claim drafted content preview for instagram`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_forbidden_public_ready_claim_facebook_page`

- **Platform Target ID**: `facebook_page`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_forbidden_public_ready_claim drafted content preview for facebook_page`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_forbidden_public_ready_claim_tiktok`

- **Platform Target ID**: `tiktok`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_forbidden_public_ready_claim drafted content preview for tiktok`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

### Payload Stub: `preview_stub_candidate_forbidden_public_ready_claim_youtube`

- **Platform Target ID**: `youtube`
- **Preview Content**: `[PRECHECK STUB] approval_packet_candidate_forbidden_public_ready_claim drafted content preview for youtube`
- **Payload Created**: `False`
- **Publishable Payload Created**: `False`
- **Dispatch Ready**: `False`

