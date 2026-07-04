# 0174U2 Primary Platform Payload Preview Contracts

- task_label: `TASK_CONTENTOPS_0174U2_PRIMARY_PLATFORM_PAYLOAD_PREVIEW_CONTRACTS_V0`
- model_version: `0174U2_PRIMARY_PLATFORM_PAYLOAD_PREVIEW_CONTRACTS_V1`
- source_baseline_commit: `b377d9a2abb9177f9b24e312e0991cfc5238695b`
- registry_checksum: `de586ffd70646e253c2ef7689705311058009e8d3f5ce66c1dadd83f568c52ff`
- preview_contract_checksum: `f3a756428517a6cb9b1d9c542743b540afb98b72ef0885f420ecbd47c6886780`
- next_heavy_batch_recommendation: `TASK_CONTENTOPS_0174U3_SUBSTACK_NEWSLETTER_AND_MANUAL_EXPORT_CONTRACT_V0`

## Builder coverage
- `facebook_page_post`
- `instagram_caption_asset_packet`
- `instagram_carousel_script`
- `linkedin_professional_post`
- `substack_longform_post`
- `substack_newsletter_issue`
- `telegram_channel_update`
- `telegram_operator_review_message`
- `threads_short_post`
- `tiktok_video_metadata_packet`
- `x_short_post`
- `x_thread`
- `youtube_video_metadata_packet`

## Hash rules

Payload hashes include platform, payload class, symbolic destination binding, symbolic credential handle, text fields, media manifest, citations, limitations, visibility, and disclosure.

## No-live rules

Dispatch and public-postable defaults stay false. Platform/API/provider/credential/env/scheduler/scraping/DM behavior stays false.

## Scope confirmations

- No UI/dashboard work.
- No ingestion repo mutation.
- No live/API/credential/provider/scheduler/scraping/DM behavior.
- Artifact writer is locked to `docs/automation/0174U2`.
