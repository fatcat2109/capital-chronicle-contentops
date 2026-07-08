# V6 Next Task Pointer

Current task just completed: `TASK_CONTENTOPS_V6_CONTROLLED_8_PLATFORM_PUBLIC_CANDIDATE_OPERATOR_GO_READBACK_AND_CROP_QA_V0`.

Result:
- Acceptance label: `BLOCKED_PRE_PUBLIC_GATE`.
- No public dispatch was run.
- No platform API/public write was attempted.
- Fresh non-oil slot selected: slot 6 from `docs/automation/V6_DAILY_EDITORIAL_SCHEDULE/daily_schedule_2026_07_08.json`.
- Fresh dry-run run id: `v6_fresh_fed_funds_prepublic_rehearsal_20260709`.
- Fresh dry-run status: `REHEARSAL_BLOCKED`.
- Public-write flags: `public_write=false`, `live_platform_api_called=false`, `credential_lookup_performed=false`.

Evidence:
- Pre-public gate packet: `docs/automation/V6_CONTROLLED_8_PLATFORM_PUBLIC_CANDIDATE_QA/pre_public_gate_evidence_v0.json`.
- Fresh-slot rehearsal packet: `docs/automation/V6_CONTROLLED_8_PLATFORM_PUBLIC_CANDIDATE_QA/fresh_slot6_dry_run_rehearsal_evidence_v0.json`.
- Fresh-slot rehearsal readback summary: `docs/automation/V6_CONTROLLED_8_PLATFORM_PUBLIC_CANDIDATE_QA/rehearsal_readback_summary.md`.
- Dispatch audit: `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/latest_dispatch_audit.json`.
- Current canonical packet: `docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json`.
- Current variant packet: `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/platform_variant_packet.json`.

Blocking summary:
- The prior oil/yields rehearsal is not public-safe because it collapses into the Telegram duplicate incident's Crude/WTI/oil-volatility family.
- The fresh Fed-funds candidate blocked before dispatch with article quality blockers: `article_too_short_words:140<2000`, `too_few_sections`, `source_trail_too_thin`, `missing_specific_numbers`, and `editorial_quality_gate:EDITORIAL_BLOCKED`.
- The fresh Fed-funds candidate also inherited WTI/Hormuz media, so the pre-public gate records `duplicate_media_family:crude_wti_oil_volatility`.
- No Substack public URL, Telegram message id, platform readback, crop proof, or public visual proof exists for this task because no public write occurred.

Recommended next task:
```text
TASK_CONTENTOPS_V6_FRESH_NON_OIL_SOURCE_BACKED_ARTICLE_AND_MEDIA_REHEARSAL_REPAIR_V0
```

Purpose: Build or repair the fresh-news path so a non-oil topic can produce a full source-backed canonical article and matching non-oil visuals, then run dry-run gates until the pre-public gate can pass.

Required proof for the next task:
- Fresh non-duplicate topic/slot selection with duplicate family check.
- Source-backed article >= 2,000 words, >= 5 sections, concrete source trail/citations, and editorial audit PASS.
- Non-oil media pack whose visual family matches the selected topic.
- Media diversification/provenance PASS with at least two visuals, preferably three for longform.
- Telegram variant with meaningful non-empty caption/body and canonical URL placeholder proof.
- Substack variant with visual markers separated by meaningful body text.
- Pre-public gate evidence showing no duplicate article/media/payload family risk.

Out of scope for the next task:
- Public dispatch.
- TikTok.
- YouTube video.
- YouTube Shorts.
- Video creator/editor.
- ElevenLabs/video voice.
- YouTube Community.
