# Platform Preview Dry Render Packet Contract

> [!IMPORTANT]
> This is a platform preview dry render report for human inspection only.
> It renders placeholders and active blockers but contains no publishable copy.
> It does not compile live platform payloads, does not perform dispatch, and does not schedule posts.

- **Task Label**: `TASK_CONTENTOPS_0175AO_PLATFORM_PREVIEW_DRY_RENDER_PACKET_V0`
- **Matrix Version**: `0175AO_PLATFORM_PREVIEW_DRY_RENDER_PACKET_V1`
- **Source Baseline Commit**: `f57a23fb61a550d9528c1984d8e758e7f00ab265`
- **Packet Hash**: `70a2efc915ffd8df17ae82af0c56070dac193b2136bf5151ec8ac4fdbe948991`
- **Ledger Family**: `platform_preview_dry_render_packet_future`
- **Next Required Gate**: `lane_c_platform_preview_dry_render_to_review_bundle_gate`

## Invariant Validation Safety Flags

| Invariant Flag | Required State | Status |
|---|---|---|
| `local_only` | `True` | ✅ |
| `fixture_only` | `True` | ✅ |
| `schema_only` | `True` | ✅ |
| `dry_render_only` | `True` | ✅ |
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
| `approved_for_publication` | `False` | ✅ |
| `financial_advice` | `False` | ✅ |
| `signal_language` | `False` | ✅ |
| `broker_order_execution` | `False` | ✅ |
| `raw_vendor_redistribution` | `False` | ✅ |
| `approved_internal_alpha_artifacts_available` | `False` | ✅ |

## Dry Render Summary Counts

- **Registered Platform Shapes**: `10`
- **Registered Dry Renders**: `10`
- **Total Fields Rendered**: `42`
- **Global Blocker Evaluators**: `8`

## Blocked Capabilities & Missing Gates

### Blocked Capabilities
- `live_publishing_dispatch`
- `autonomous_reply_automation`
- `live_credential_hydration`
- `active_scheduler_triggers`

### Missing Future Gates
- `lane_c_platform_preview_dry_render_to_review_bundle_gate`
- `production_key_vault_decrypter`
- `live_operator_signature_vault`

## Global Dry Render Blocker Status

| Blocker ID | Description | Active Status |
|---|---|---|
| `blocked_no_operator_review` | Operator review gate is required but pending. | ✅ Active |
| `blocked_no_account_binding` | Account binding is required but inactive. | ✅ Active |
| `blocked_no_credential_gate` | Credential gate authentication is required but pending. | ✅ Active |
| `blocked_no_payload_hash_lock` | Payload hash lock verification is required but pending. | ✅ Active |
| `blocked_dqr_readiness_unresolved` | DQR and publish readiness checks are unresolved. | ✅ Active |
| `blocked_not_public_postable` | Candidate is not marked public postable. | ✅ Active |
| `blocked_no_dispatch_gate` | Dispatch gate has not cleared the post. | ✅ Active |
| `blocked_no_platform_api_authorization` | Platform API is not authorized (local contract dry run). | ✅ Active |

## Registered Platform Preview Dry Renders

### Render Record: `dry_render_x`

- **Platform Target ID**: `x`
- **Platform Family**: `x_microblog`
- **Source Shape ID**: `shape_x`
- **Render Status**: `dry_render_blocked`
- **Preview Surface Type**: `x_thread_stub_surface`
- **Watermark**: `[DRY_RENDER_WATERMARK_NON_PUBLISHABLE_SCHEMA_ONLY]`
- **Blocker Banner**: `[DRY_RENDER_BLOCKER_BANNER: ACTIVE_BLOCKERS_PREVENT_PUBLICATION: blocked_no_operator_review, blocked_no_account_binding, blocked_no_credential_gate, blocked_no_payload_hash_lock, blocked_dqr_readiness_unresolved, blocked_not_public_postable, blocked_no_dispatch_gate, blocked_no_platform_api_authorization]`
- **Citation Slot Status**: `citation_rendering_required_but_pending`
- **Limitation Slot Status**: `limitation_rendering_required_but_pending`
- **Operator Review**: `review_required_but_pending`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`
- **Publishability Status**: `non_publishable_dry_render`

#### Field Renders

| Field Name | Placeholder Value | placeholder_only | publishable_text | platform_ready | dispatch_ready |
|---|---|---|---|---|---|
| `text_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: x.text_stub]` | `True` | `False` | `False` | `False` |
| `citation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: x.citation_stub]` | `True` | `False` | `False` | `False` |
| `limitation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: x.limitation_stub]` | `True` | `False` | `False` | `False` |
| `thread_hint` | `[DRY_RENDER_PLACEHOLDER_ONLY: x.thread_hint]` | `True` | `False` | `False` | `False` |
| `media_slot_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: x.media_slot_stub]` | `True` | `False` | `False` | `False` |

### Render Record: `dry_render_telegram_channel_destination`

- **Platform Target ID**: `telegram_channel_destination`
- **Platform Family**: `telegram_chat`
- **Source Shape ID**: `shape_telegram_channel_destination`
- **Render Status**: `dry_render_blocked`
- **Preview Surface Type**: `telegram_channel_stub_surface`
- **Watermark**: `[DRY_RENDER_WATERMARK_NON_PUBLISHABLE_SCHEMA_ONLY]`
- **Blocker Banner**: `[DRY_RENDER_BLOCKER_BANNER: ACTIVE_BLOCKERS_PREVENT_PUBLICATION: blocked_no_operator_review, blocked_no_account_binding, blocked_no_credential_gate, blocked_no_payload_hash_lock, blocked_dqr_readiness_unresolved, blocked_not_public_postable, blocked_no_dispatch_gate, blocked_no_platform_api_authorization]`
- **Citation Slot Status**: `citation_rendering_required_but_pending`
- **Limitation Slot Status**: `limitation_rendering_required_but_pending`
- **Operator Review**: `review_required_but_pending`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`
- **Publishability Status**: `non_publishable_dry_render`

#### Field Renders

| Field Name | Placeholder Value | placeholder_only | publishable_text | platform_ready | dispatch_ready |
|---|---|---|---|---|---|
| `message_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: telegram_channel_destination.message_stub]` | `True` | `False` | `False` | `False` |
| `citation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: telegram_channel_destination.citation_stub]` | `True` | `False` | `False` | `False` |
| `limitation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: telegram_channel_destination.limitation_stub]` | `True` | `False` | `False` | `False` |
| `operator_note_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: telegram_channel_destination.operator_note_stub]` | `True` | `False` | `False` | `False` |

### Render Record: `dry_render_telegram_remote_operator`

- **Platform Target ID**: `telegram_remote_operator`
- **Platform Family**: `telegram_chat`
- **Source Shape ID**: `shape_telegram_remote_operator`
- **Render Status**: `dry_render_blocked`
- **Preview Surface Type**: `telegram_remote_operator_stub_surface`
- **Watermark**: `[DRY_RENDER_WATERMARK_NON_PUBLISHABLE_SCHEMA_ONLY]`
- **Blocker Banner**: `[DRY_RENDER_BLOCKER_BANNER: ACTIVE_BLOCKERS_PREVENT_PUBLICATION: blocked_no_operator_review, blocked_no_account_binding, blocked_no_credential_gate, blocked_no_payload_hash_lock, blocked_dqr_readiness_unresolved, blocked_not_public_postable, blocked_no_dispatch_gate, blocked_no_platform_api_authorization]`
- **Citation Slot Status**: `citation_rendering_required_but_pending`
- **Limitation Slot Status**: `limitation_rendering_required_but_pending`
- **Operator Review**: `review_required_but_pending`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`
- **Publishability Status**: `non_publishable_dry_render`

#### Field Renders

| Field Name | Placeholder Value | placeholder_only | publishable_text | platform_ready | dispatch_ready |
|---|---|---|---|---|---|
| `operator_summary_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: telegram_remote_operator.operator_summary_stub]` | `True` | `False` | `False` | `False` |
| `decision_buttons_stub_disabled` | `[DRY_RENDER_PLACEHOLDER_ONLY: telegram_remote_operator.decision_buttons_stub_disabled]` | `True` | `False` | `False` | `False` |
| `audit_ref_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: telegram_remote_operator.audit_ref_stub]` | `True` | `False` | `False` | `False` |

### Render Record: `dry_render_substack`

- **Platform Target ID**: `substack`
- **Platform Family**: `substack_newsletter`
- **Source Shape ID**: `shape_substack`
- **Render Status**: `dry_render_blocked`
- **Preview Surface Type**: `substack_outline_stub_surface`
- **Watermark**: `[DRY_RENDER_WATERMARK_NON_PUBLISHABLE_SCHEMA_ONLY]`
- **Blocker Banner**: `[DRY_RENDER_BLOCKER_BANNER: ACTIVE_BLOCKERS_PREVENT_PUBLICATION: blocked_no_operator_review, blocked_no_account_binding, blocked_no_credential_gate, blocked_no_payload_hash_lock, blocked_dqr_readiness_unresolved, blocked_not_public_postable, blocked_no_dispatch_gate, blocked_no_platform_api_authorization]`
- **Citation Slot Status**: `citation_rendering_required_but_pending`
- **Limitation Slot Status**: `limitation_rendering_required_but_pending`
- **Operator Review**: `review_required_but_pending`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`
- **Publishability Status**: `non_publishable_dry_render`

#### Field Renders

| Field Name | Placeholder Value | placeholder_only | publishable_text | platform_ready | dispatch_ready |
|---|---|---|---|---|---|
| `title_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: substack.title_stub]` | `True` | `False` | `False` | `False` |
| `subtitle_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: substack.subtitle_stub]` | `True` | `False` | `False` | `False` |
| `body_outline_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: substack.body_outline_stub]` | `True` | `False` | `False` | `False` |
| `citation_section_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: substack.citation_section_stub]` | `True` | `False` | `False` | `False` |
| `limitation_section_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: substack.limitation_section_stub]` | `True` | `False` | `False` | `False` |

### Render Record: `dry_render_linkedin`

- **Platform Target ID**: `linkedin`
- **Platform Family**: `linkedin_professional`
- **Source Shape ID**: `shape_linkedin`
- **Render Status**: `dry_render_blocked`
- **Preview Surface Type**: `linkedin_feed_stub_surface`
- **Watermark**: `[DRY_RENDER_WATERMARK_NON_PUBLISHABLE_SCHEMA_ONLY]`
- **Blocker Banner**: `[DRY_RENDER_BLOCKER_BANNER: ACTIVE_BLOCKERS_PREVENT_PUBLICATION: blocked_no_operator_review, blocked_no_account_binding, blocked_no_credential_gate, blocked_no_payload_hash_lock, blocked_dqr_readiness_unresolved, blocked_not_public_postable, blocked_no_dispatch_gate, blocked_no_platform_api_authorization]`
- **Citation Slot Status**: `citation_rendering_required_but_pending`
- **Limitation Slot Status**: `limitation_rendering_required_but_pending`
- **Operator Review**: `review_required_but_pending`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`
- **Publishability Status**: `non_publishable_dry_render`

#### Field Renders

| Field Name | Placeholder Value | placeholder_only | publishable_text | platform_ready | dispatch_ready |
|---|---|---|---|---|---|
| `professional_intro_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: linkedin.professional_intro_stub]` | `True` | `False` | `False` | `False` |
| `body_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: linkedin.body_stub]` | `True` | `False` | `False` | `False` |
| `citation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: linkedin.citation_stub]` | `True` | `False` | `False` | `False` |
| `limitation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: linkedin.limitation_stub]` | `True` | `False` | `False` | `False` |

### Render Record: `dry_render_threads`

- **Platform Target ID**: `threads`
- **Platform Family**: `threads_microblog`
- **Source Shape ID**: `shape_threads`
- **Render Status**: `dry_render_blocked`
- **Preview Surface Type**: `threads_stub_surface`
- **Watermark**: `[DRY_RENDER_WATERMARK_NON_PUBLISHABLE_SCHEMA_ONLY]`
- **Blocker Banner**: `[DRY_RENDER_BLOCKER_BANNER: ACTIVE_BLOCKERS_PREVENT_PUBLICATION: blocked_no_operator_review, blocked_no_account_binding, blocked_no_credential_gate, blocked_no_payload_hash_lock, blocked_dqr_readiness_unresolved, blocked_not_public_postable, blocked_no_dispatch_gate, blocked_no_platform_api_authorization]`
- **Citation Slot Status**: `citation_rendering_required_but_pending`
- **Limitation Slot Status**: `limitation_rendering_required_but_pending`
- **Operator Review**: `review_required_but_pending`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`
- **Publishability Status**: `non_publishable_dry_render`

#### Field Renders

| Field Name | Placeholder Value | placeholder_only | publishable_text | platform_ready | dispatch_ready |
|---|---|---|---|---|---|
| `short_text_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: threads.short_text_stub]` | `True` | `False` | `False` | `False` |
| `citation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: threads.citation_stub]` | `True` | `False` | `False` | `False` |
| `limitation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: threads.limitation_stub]` | `True` | `False` | `False` | `False` |

### Render Record: `dry_render_instagram`

- **Platform Target ID**: `instagram`
- **Platform Family**: `instagram_media`
- **Source Shape ID**: `shape_instagram`
- **Render Status**: `dry_render_blocked`
- **Preview Surface Type**: `instagram_caption_media_stub_surface`
- **Watermark**: `[DRY_RENDER_WATERMARK_NON_PUBLISHABLE_SCHEMA_ONLY]`
- **Blocker Banner**: `[DRY_RENDER_BLOCKER_BANNER: ACTIVE_BLOCKERS_PREVENT_PUBLICATION: blocked_no_operator_review, blocked_no_account_binding, blocked_no_credential_gate, blocked_no_payload_hash_lock, blocked_dqr_readiness_unresolved, blocked_not_public_postable, blocked_no_dispatch_gate, blocked_no_platform_api_authorization]`
- **Citation Slot Status**: `citation_rendering_required_but_pending`
- **Limitation Slot Status**: `limitation_rendering_required_but_pending`
- **Operator Review**: `review_required_but_pending`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`
- **Publishability Status**: `non_publishable_dry_render`

#### Field Renders

| Field Name | Placeholder Value | placeholder_only | publishable_text | platform_ready | dispatch_ready |
|---|---|---|---|---|---|
| `caption_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: instagram.caption_stub]` | `True` | `False` | `False` | `False` |
| `image_requirement_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: instagram.image_requirement_stub]` | `True` | `False` | `False` | `False` |
| `alt_text_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: instagram.alt_text_stub]` | `True` | `False` | `False` | `False` |
| `citation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: instagram.citation_stub]` | `True` | `False` | `False` | `False` |
| `limitation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: instagram.limitation_stub]` | `True` | `False` | `False` | `False` |

### Render Record: `dry_render_facebook_page`

- **Platform Target ID**: `facebook_page`
- **Platform Family**: `facebook_page_media`
- **Source Shape ID**: `shape_facebook_page`
- **Render Status**: `dry_render_blocked`
- **Preview Surface Type**: `facebook_page_stub_surface`
- **Watermark**: `[DRY_RENDER_WATERMARK_NON_PUBLISHABLE_SCHEMA_ONLY]`
- **Blocker Banner**: `[DRY_RENDER_BLOCKER_BANNER: ACTIVE_BLOCKERS_PREVENT_PUBLICATION: blocked_no_operator_review, blocked_no_account_binding, blocked_no_credential_gate, blocked_no_payload_hash_lock, blocked_dqr_readiness_unresolved, blocked_not_public_postable, blocked_no_dispatch_gate, blocked_no_platform_api_authorization]`
- **Citation Slot Status**: `citation_rendering_required_but_pending`
- **Limitation Slot Status**: `limitation_rendering_required_but_pending`
- **Operator Review**: `review_required_but_pending`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`
- **Publishability Status**: `non_publishable_dry_render`

#### Field Renders

| Field Name | Placeholder Value | placeholder_only | publishable_text | platform_ready | dispatch_ready |
|---|---|---|---|---|---|
| `post_text_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: facebook_page.post_text_stub]` | `True` | `False` | `False` | `False` |
| `attachment_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: facebook_page.attachment_stub]` | `True` | `False` | `False` | `False` |
| `citation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: facebook_page.citation_stub]` | `True` | `False` | `False` | `False` |
| `limitation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: facebook_page.limitation_stub]` | `True` | `False` | `False` | `False` |

### Render Record: `dry_render_tiktok`

- **Platform Target ID**: `tiktok`
- **Platform Family**: `tiktok_video`
- **Source Shape ID**: `shape_tiktok`
- **Render Status**: `dry_render_blocked`
- **Preview Surface Type**: `tiktok_caption_video_stub_surface`
- **Watermark**: `[DRY_RENDER_WATERMARK_NON_PUBLISHABLE_SCHEMA_ONLY]`
- **Blocker Banner**: `[DRY_RENDER_BLOCKER_BANNER: ACTIVE_BLOCKERS_PREVENT_PUBLICATION: blocked_no_operator_review, blocked_no_account_binding, blocked_no_credential_gate, blocked_no_payload_hash_lock, blocked_dqr_readiness_unresolved, blocked_not_public_postable, blocked_no_dispatch_gate, blocked_no_platform_api_authorization]`
- **Citation Slot Status**: `citation_rendering_required_but_pending`
- **Limitation Slot Status**: `limitation_rendering_required_but_pending`
- **Operator Review**: `review_required_but_pending`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`
- **Publishability Status**: `non_publishable_dry_render`

#### Field Renders

| Field Name | Placeholder Value | placeholder_only | publishable_text | platform_ready | dispatch_ready |
|---|---|---|---|---|---|
| `caption_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: tiktok.caption_stub]` | `True` | `False` | `False` | `False` |
| `video_requirement_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: tiktok.video_requirement_stub]` | `True` | `False` | `False` | `False` |
| `disclosure_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: tiktok.disclosure_stub]` | `True` | `False` | `False` | `False` |
| `citation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: tiktok.citation_stub]` | `True` | `False` | `False` | `False` |

### Render Record: `dry_render_youtube`

- **Platform Target ID**: `youtube`
- **Platform Family**: `youtube_video`
- **Source Shape ID**: `shape_youtube`
- **Render Status**: `dry_render_blocked`
- **Preview Surface Type**: `youtube_metadata_video_stub_surface`
- **Watermark**: `[DRY_RENDER_WATERMARK_NON_PUBLISHABLE_SCHEMA_ONLY]`
- **Blocker Banner**: `[DRY_RENDER_BLOCKER_BANNER: ACTIVE_BLOCKERS_PREVENT_PUBLICATION: blocked_no_operator_review, blocked_no_account_binding, blocked_no_credential_gate, blocked_no_payload_hash_lock, blocked_dqr_readiness_unresolved, blocked_not_public_postable, blocked_no_dispatch_gate, blocked_no_platform_api_authorization]`
- **Citation Slot Status**: `citation_rendering_required_but_pending`
- **Limitation Slot Status**: `limitation_rendering_required_but_pending`
- **Operator Review**: `review_required_but_pending`
- **Account Binding**: `binding_required_but_inactive`
- **Credential Gate**: `credential_required_but_locked`
- **Payload Hash Lock**: `hash_lock_required_but_pending`
- **Dispatch Gate**: `dispatch_gate_required_but_locked`
- **Publishability Status**: `non_publishable_dry_render`

#### Field Renders

| Field Name | Placeholder Value | placeholder_only | publishable_text | platform_ready | dispatch_ready |
|---|---|---|---|---|---|
| `title_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: youtube.title_stub]` | `True` | `False` | `False` | `False` |
| `description_outline_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: youtube.description_outline_stub]` | `True` | `False` | `False` | `False` |
| `video_requirement_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: youtube.video_requirement_stub]` | `True` | `False` | `False` | `False` |
| `citation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: youtube.citation_stub]` | `True` | `False` | `False` | `False` |
| `limitation_stub` | `[DRY_RENDER_PLACEHOLDER_ONLY: youtube.limitation_stub]` | `True` | `False` | `False` | `False` |
