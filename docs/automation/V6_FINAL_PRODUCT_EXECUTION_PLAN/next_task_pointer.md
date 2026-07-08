# V6 Next Task Pointer

Current task just completed: `TASK_CONTENTOPS_V6_DRY_RUN_IMAGE_SEARCH_ISOLATION_AND_REAL_FULL_AUTOMATION_REHEARSAL_V0`.

Result:
- Acceptance label: `PASS_REAL_FULL_AUTOMATION_DRY_RUN_REHEARSAL_NO_PUBLIC_WRITE`.
- Real CLI/full automation dry-run rehearsal ran end-to-end.
- Rehearsal status: `LIVE_READY_REQUIRES_OPERATOR_GO`.
- Run ID: `v6_dry_run_rehearsal_20260709`.
- Public writes: `false` for every attempted platform.
- Live platform API calls: `false`.
- Credential lookup: `false`.
- Dry-run image/media discovery is network-isolated and uses committed local source-backed assets.

Evidence:
- Rehearsal packet: `docs/automation/V6_DRY_RUN_FULL_AUTOMATION_REHEARSAL/dry_run_full_automation_rehearsal_evidence_v0.json`.
- Rehearsal readback summary: `docs/automation/V6_DRY_RUN_FULL_AUTOMATION_REHEARSAL/rehearsal_readback_summary.md`.
- Dispatch audit: `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/latest_dispatch_audit.json`.
- Canonical packet: `docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json`.
- Variant packet: `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/platform_variant_packet.json`.

Rehearsal summary:
- Schedule slot: slot 1 from `docs/automation/V6_DAILY_EDITORIAL_SCHEDULE/daily_schedule_2026_07_08.json`.
- Sidecar file: `headline_ingestion/data/intake/headline_sidecars/step1_headline_sidecar_2026_07_08.jsonl`.
- Sidecar count: 1,024 rows; latest captured at `2026-07-08T13:21:21Z`.
- Topic hash: `6ec6c3d3cbc58f82`.
- Canonical packet hash: `0cc5c3bb4c0130a93b04e672080e0d3b0489e07f2e6979e25ab535a7d79c1e04`.
- Platform variant packet hash: `05b1a63252e641d68960684fb5b67897c6ba951dbedb3d5d3d2f770cd8cef57c`.
- Telegram payload hash: `de2b71eb33b51986`.
- Duplicate ledger result: `PASS`.
- Quality gate result: `PASS`.
- Successful dry-run platforms: Substack, LinkedIn, X, Instagram, Facebook Page, Telegram, Threads, Discord.

Recommended next task:
```text
TASK_CONTENTOPS_V6_CONTROLLED_8_PLATFORM_PUBLIC_CANDIDATE_OPERATOR_GO_READBACK_AND_CROP_QA_V0
```

Purpose: With explicit operator GO, run exactly one non-bypassed 8-platform public candidate from the approved rehearsal state and capture public proof.

Required proof for the next task:
- Substack public URL, visual count, visual order, and placement/readback proof.
- Telegram message ID, meaningful caption/body, canonical URL, duplicate guard proof, and Bot API photo proof when a photo is requested.
- LinkedIn native image proof and stable URL/permalink if recoverable.
- X and Threads thread/public proof.
- Instagram and Facebook Page image/crop/readability proof.
- Discord and Telegram link/image proof.
- Per-platform manual audit requirement where automatic readback is unavailable.

Out of scope for the next task:
- TikTok.
- YouTube video.
- YouTube Shorts.
- Video creator/editor.
- ElevenLabs/video voice.
- YouTube Community.
