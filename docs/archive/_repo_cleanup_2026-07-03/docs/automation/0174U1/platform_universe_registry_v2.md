# 0174U1 Platform Universe Registry V2

- task_label: `TASK_CONTENTOPS_0174U1_PLATFORM_UNIVERSE_REGISTRY_V2_AND_PRIMARY_PAYLOAD_CLASSES_CONTRACT_V0`
- model_version: `0174U1_PLATFORM_UNIVERSE_REGISTRY_V2_V1`
- source_baseline_commit: `ae424c27c69338aa189edaf23f8240151cbff6ac`
- registry_checksum: `de586ffd70646e253c2ef7689705311058009e8d3f5ce66c1dadd83f568c52ff`
- next_heavy_batch_recommendation: `TASK_CONTENTOPS_0174U2_PRIMARY_PLATFORM_PAYLOAD_PREVIEW_CONTRACTS_V0`

## Platform tiers
- `x`: `primary_now` / `primary_distribution` / `preview_only`
- `telegram_remote_operator`: `primary_now` / `remote_operator_review` / `remote_review_only`
- `telegram_channel_destination`: `primary_now` / `controlled_channel_distribution` / `preview_only`
- `substack_newsletter`: `primary_now` / `owned_long_form` / `manual_export_only`
- `linkedin`: `secondary_next` / `professional_credibility` / `preview_only`
- `threads`: `expansion_later` / `expansion_distribution` / `preview_only`
- `instagram`: `expansion_later` / `expansion_distribution` / `preview_only`
- `facebook_page`: `expansion_later` / `expansion_distribution` / `preview_only`
- `tiktok`: `video_later` / `later_video_distribution` / `preview_only`
- `youtube`: `video_later` / `later_video_distribution` / `preview_only`

## Payload classes
- `x_short_post` -> `x`; dispatch_ready_default=`false`; public_postable_default=`false`
- `x_thread` -> `x`; dispatch_ready_default=`false`; public_postable_default=`false`
- `telegram_channel_update` -> `telegram_channel_destination`; dispatch_ready_default=`false`; public_postable_default=`false`
- `telegram_operator_review_message` -> `telegram_remote_operator`; dispatch_ready_default=`false`; public_postable_default=`false`
- `substack_newsletter_issue` -> `substack_newsletter`; dispatch_ready_default=`false`; public_postable_default=`false`
- `substack_longform_post` -> `substack_newsletter`; dispatch_ready_default=`false`; public_postable_default=`false`
- `linkedin_professional_post` -> `linkedin`; dispatch_ready_default=`false`; public_postable_default=`false`
- `threads_short_post` -> `threads`; dispatch_ready_default=`false`; public_postable_default=`false`
- `instagram_caption_asset_packet` -> `instagram`; dispatch_ready_default=`false`; public_postable_default=`false`
- `instagram_carousel_script` -> `instagram`; dispatch_ready_default=`false`; public_postable_default=`false`
- `facebook_page_post` -> `facebook_page`; dispatch_ready_default=`false`; public_postable_default=`false`
- `video_script_metadata_packet` -> `tiktok`; dispatch_ready_default=`false`; public_postable_default=`false`
- `youtube_video_metadata_packet` -> `youtube`; dispatch_ready_default=`false`; public_postable_default=`false`
- `tiktok_video_metadata_packet` -> `tiktok`; dispatch_ready_default=`false`; public_postable_default=`false`

## No-live defaults

All platform/API/provider/credential/env/scheduler/autonomous/scraping/DM flags default false.
Official docs refs are string metadata only; this module performs no network behavior.

## Scope confirmations

- No UI/dashboard work.
- No ingestion repo mutation.
- No live/API/credential/provider/scheduler/scraping/DM behavior.
- Artifact writer is locked to `docs/automation/0174U1`.
