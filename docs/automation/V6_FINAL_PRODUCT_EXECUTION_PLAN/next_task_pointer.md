# V6 Next Task Pointer

Current task just completed: `TASK_CONTENTOPS_V6_FRESH_NON_OIL_SOURCE_BACKED_ARTICLE_AND_MEDIA_REHEARSAL_REPAIR_V0`.

Result:
- Acceptance label: `PASS_FRESH_NON_OIL_SOURCE_BACKED_REHEARSAL_READY_FOR_CONTROLLED_PUBLIC_CANDIDATE`.
- No public dispatch was run.
- No platform API/public write was attempted.
- Repaired topic: `Effective fed funds rate: 3.63% July 7th vs 3.63% July 6th`.
- Dry-run run id: `v6_fresh_fed_funds_repair_rehearsal_20260709`.
- Dry-run status: `LIVE_READY_REQUIRES_OPERATOR_GO`.
- Pre-public gate status: `PASS_PRE_PUBLIC_GATE`.
- Public-write flags: `public_write=false`, `live_platform_api_called=false`, `credential_lookup_performed=false`.

Evidence:
- Rehearsal packet: `docs/automation/V6_FRESH_NON_OIL_REHEARSAL_REPAIR/fresh_non_oil_rehearsal_evidence_v0.json`.
- Rehearsal readback summary: `docs/automation/V6_FRESH_NON_OIL_REHEARSAL_REPAIR/rehearsal_readback_summary.md`.
- Pre-public gate packet: `docs/automation/V6_FRESH_NON_OIL_REHEARSAL_REPAIR/pre_public_gate_evidence_v0.json`.
- Fixture-scope evidence: `docs/automation/V6_FRESH_NON_OIL_REHEARSAL_REPAIR/fallback_fixture_scope_evidence_v0.json`.
- CC artifact contract stub: `docs/automation/V6_CC_ARTIFACT_PACKET_CONTRACT/cc_content_artifact_packet_contract_v0.json`.
- Dispatch audit: `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/latest_dispatch_audit.json`.
- Current canonical packet: `docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json`.
- Current variant packet: `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/platform_variant_packet.json`.

Authority boundary:
- Current Fed/FRED/NY Fed/Treasury rates path is `TEMPORARY_CONTENTOPS_FALLBACK_FIXTURE`.
- Future numeric/source authority remains `FUTURE_CAPITAL_CHRONICLE_DATABASE_AUTHORITY`.
- ContentOps must later consume a `CC_CONTENT_ARTIFACT_PACKET` instead of owning source truth.
- No additional source families should be added directly to ContentOps unless explicitly approved.

Recommended next task:
```text
TASK_CONTENTOPS_V6_CONTROLLED_8_PLATFORM_PUBLIC_CANDIDATE_OPERATOR_GO_READBACK_AND_CROP_QA_V1
```

Purpose: With explicit operator GO, run exactly one non-bypassed 8-platform public candidate from the repaired fresh non-oil packet, then capture public readback, crop/readability, Telegram Bot API photo proof, Substack public visual placement proof, LinkedIn native image/permalink proof where recoverable, and exact blockers/manual audit requirements for any platform that cannot be automatically read back.

Required proof for the next task:
- Explicit operator GO marker bound to run id/topic hash/payload hashes.
- Duplicate ledger/pre-public gate still PASS immediately before dispatch.
- No quality bypass.
- Public URLs/IDs for all attempted platforms.
- Telegram caption/body + canonical URL + Bot API photo proof.
- Substack public URL, visual count/order/placement proof, and screenshots/readback where possible.
- LinkedIn native image proof and stable URL/permalink if recoverable.
- X/Threads thread proof.
- Instagram/Facebook image proof.
- Discord/Telegram link/image proof.
- Crop/readability status for visual platforms.

Out of scope for the next task:
- TikTok.
- YouTube video.
- YouTube Shorts.
- Video creator/editor.
- ElevenLabs/video voice.
- YouTube Community.
- Building a broad ContentOps source-ingestion framework.
