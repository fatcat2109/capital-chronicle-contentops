# V6 Next Task Pointer

Current task just completed: `TASK_CONTENTOPS_V6_FRESH_NEWS_8_PLATFORM_PUBLIC_CANDIDATE_READBACK_AND_CROP_QA_V0`.

Baseline reconciliation:

- Verified pre-task `HEAD` and `origin/master`: `f0b4fa1cc4ff7d72e26443ef33adfe27d5d82b42`.
- Operator CDP setup was reachable at `http://localhost:9222/json/version` with Chrome `149.0.7827.201`.
- X list access was present for `https://x.com/i/lists/1843870469143048642`.
- Fresh headline sidecars were generated under `headline_ingestion/data/intake/headline_sidecars/`.

What changed:

- Fixed the daily scheduler to ingest the current Step 1 sidecar schema: `headline_text`, `headline_timestamp`, `author_handle`, `candidate_catalyst_tags`, and `follow_up_data_need_candidates`.
- Generated fresh sidecar evidence: `headline_ingestion/data/intake/headline_sidecars/step1_headline_sidecar_2026_07_08.jsonl`, 1,024 rows, captured from `2026-07-08T13:21:21Z` through `2026-07-08T13:22:01Z`.
- Rebuilt the daily schedule using only the fresh `2026_07_08` sidecar.
- Tried the fresh EIA oil-output slot first, but duplicate guard blocked public dispatch because generation collapsed into the same WTI/oil-volatility content family and slug as the prior public Crude run.
- Tried a fresh IMF global-growth official-release topic next, but editorial/media gates blocked public dispatch:
  - Editorial blockers: unrelated citation/source-note URLs and generic source-trail claims.
  - Media blockers: unverified current-topic time coverage, only one publication-unsafe fallback image, missing data chart, and missing contextual image/map.
- No public 8-platform dispatch was performed, correctly preserving the no-bypass and no-duplicate requirements.
- Blocked evidence written to `docs/automation/V6_FRESH_NEWS_8_PLATFORM_PUBLIC_CANDIDATE_QA/fresh_news_8_platform_public_candidate_blocked_after_cdp_evidence_v0.json`.

Evidence to read before the next task:

- `docs/automation/V6_FRESH_NEWS_8_PLATFORM_PUBLIC_CANDIDATE_QA/fresh_news_8_platform_public_candidate_blocked_after_cdp_evidence_v0.json`
- `headline_ingestion/data/intake/headline_sidecars/step1_headline_sidecar_2026_07_08.jsonl`
- `docs/automation/V6_DAILY_EDITORIAL_SCHEDULE/daily_schedule_2026_07_08.json`
- `docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json`
- `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/platform_variant_packet.json`
- `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/latest_dispatch_audit.json`
- `docs/automation/V6_NON_BYPASSED_LONGFORM_LIVE_RUN/non_bypassed_live_run_evidence_v0.json`

Recommended next task:

```text
TASK_CONTENTOPS_V6_IMF_OFFICIAL_SOURCE_PACK_AND_MEDIA_CHART_REPAIR_FOR_PUBLIC_CANDIDATE_V0
```

Purpose: add an official-source IMF/global-growth source pack and source-backed media/chart pack so the fresh IMF candidate can pass editorial source relevance, Tier 1 structure, media content, and media diversification gates before any public 8-platform dispatch is attempted.

Out of scope for the next task:

- Do not build TikTok.
- Do not build YouTube video, Shorts, or a video creator.
- Do not build ElevenLabs/video voice lanes.
- Keep YouTube Community as a future text/image platform after the current 8-platform QA lane is hardened.
