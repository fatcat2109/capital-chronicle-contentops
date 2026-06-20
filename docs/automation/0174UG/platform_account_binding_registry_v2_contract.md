# 0174UG Platform Account Binding Registry V2 Contract

- task_label: `TASK_CONTENTOPS_0174UG_PLATFORM_ACCOUNT_BINDING_REGISTRY_V2_CONTRACT_V0`
- registry_version: `0174UG_PLATFORM_ACCOUNT_BINDING_REGISTRY_V2_CONTRACT_V1`
- source_baseline_commit: `ee309aa9513c81c1ae028935b5b23c8a391ee2ef`
- packet_id: `platform_account_binding_registry_packet_5e9320282937510b2ec9e1ff`
- packet_hash: `5e9320282937510b2ec9e1ffaf01a498a3a166385f9b202dc7dc5328a898850e`
- next_required_gate: `TASK_CONTENTOPS_0174UH_CREDENTIAL_HANDLE_AND_DOTENV_SECRET_BOUNDARY_V2_CONTRACT_V0`

## Binding Coverage
- `x` / `user_profile` / `brand_channel` / `needs_identity_proof`
- `telegram_remote_operator` / `operator_inbox` / `operator` / `needs_identity_proof`
- `telegram_channel_destination` / `channel` / `brand_channel` / `needs_permission_proof`
- `substack_newsletter` / `newsletter_publication` / `owned_publication` / `configured_symbolic`
- `linkedin` / `user_profile` / `professional_profile` / `needs_identity_proof`
- `linkedin` / `organization_page` / `organization_page` / `missing_binding`
- `threads` / `user_profile` / `expansion_channel` / `needs_identity_proof`
- `instagram` / `business_account` / `expansion_channel` / `needs_permission_proof`
- `facebook_page` / `page` / `organization_page` / `needs_permission_proof`
- `tiktok` / `creator_account` / `video_channel` / `needs_identity_proof`
- `youtube` / `video_channel` / `video_channel` / `needs_permission_proof`

## Required Distinctions

- `telegram_remote_operator` is an `operator_inbox` binding and is not a public channel destination.
- `telegram_channel_destination` is a `channel` binding for future supervised channel posts.
- `linkedin` includes member/profile symbolic binding and separate organization/page missing proof state.

## Safety

- All live read/write/public post flags remain false.
- Credential handles are symbolic only; no credentials are hydrated or read.
- No provider/API/network/env/browser/scheduler/scraping/DM behavior.
- U9 audit family: `platform_account_binding_future`.
- Wrong destination/platform preview binding mismatches fail closed as `wrong_destination_blocked`.

## Packet Summary

```json
{
  "binding_count": 11,
  "blocked_binding_platforms": [],
  "credential_hydrated_count": 0,
  "live_read_allowed_count": 0,
  "live_write_allowed_count": 0,
  "missing_binding_platforms": [
    "linkedin"
  ],
  "platform_api_called_count": 0,
  "platform_count": 10,
  "public_post_allowed_count": 0,
  "wrong_destination_block_count": 0
}
```
