# V6 Next Task Pointer

Current task just completed: `TASK_CONTENTOPS_V6_FRESH_NEWS_8_PLATFORM_PUBLIC_CANDIDATE_READBACK_AND_CROP_QA_V0`.

Baseline reconciliation:

- Verified pre-task remote `master`: `bea4aaedfdeccd936c807af53080d22d2932e6b9`.
- Accepted visual repair commit remains `6a810aadadef4b3c9078173b32bed4b243f8552a`.
- Latest scoped visual repair run remains `v6_pipeline_d49f6e14a856`, Substack + LinkedIn `DISPATCH_COMPLETE`.
- Prior full 8-platform run remains reconciled for unaffected lanes.
- Step 1 headline ingestion remains isolated under `headline_ingestion/`; source list target is `https://x.com/i/lists/1843870469143048642`.

What changed:

- Fresh-news public proof preflight blocked safely before generation/dispatch: no headline sidecars exist under `headline_ingestion/data/intake/headline_sidecars/`, and the CDP ingestion endpoint `localhost:9222` refused connection.
- No old Crude Awakenings duplicate was reused as final public proof.
- Blocked evidence written to `docs/automation/V6_FRESH_NEWS_8_PLATFORM_PUBLIC_CANDIDATE_QA/fresh_news_8_platform_public_candidate_blocked_evidence_v0.json`.
- Hardened Telegram visual dispatch QA: when the pipeline sends a Telegram photo, the dispatch result now records Bot API photo evidence and fails the lane as `FAILED_VISUAL_DELIVERY` if the response lacks photo proof.
- Hardened Substack visual placement QA: public readback can confirm successful visual placement when the editor reports `uploaded_unverified`, and dispatch evidence records both uploaded count and upload-attempt count.
- Added manifest-level media diversification and rights/provenance audit: `live_contentops/media_diversification_audit_v6.py`.
- Added daily newsroom scheduler from headline sidecars: `live_contentops/daily_editorial_scheduler_v6.py`.
- Hardened search-like image metadata so Google/Commons images are discovery/review candidates unless source-page, recency, rights, and provenance are complete.
- Expanded the source-backed WTI repair article to 3 in-body visual slots: primary WTI volatility chart, recent WTI price chart, and EIA-referenced Hormuz/geopolitics context visual.
- Rebuilt WTI canonical citations/source notes from official source trail rows so unrelated Yahoo/search results do not contaminate canonical packets.
- Wired editorial/media QA gates into dispatch blocking for live dispatch.

Latest local final candidate:

- Live dispatch performed: `false`.
- Local run id: `local_static_final_candidate_2026_07_08`.
- Reason no public run was performed: no headline sidecar data files exist in the clean checkout, `localhost:9222` CDP ingestion is unavailable, and reposting the Crude Awakenings topic would create duplicate public posts.
- Article title: `Crude Awakenings: Oil Volatility, Hormuz Risk, and the Recession Dashboard`.
- Article metrics: 2,174 words, 9 sections, 8 source-trail rows, 8 citations, 3 visual slots.
- Editorial acceptance: `EDITORIAL_APPROVED`; `tier1_editorial_approved=true`.
- Media diversification audit: `PASS`; 3 assets: `data_chart`, `data_chart`, `map_or_geography`.
- Scheduler output: `docs/automation/V6_DAILY_EDITORIAL_SCHEDULE/daily_schedule_2026_07_08.json`.
- Dispatch audit packet records local QA status only: `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/latest_dispatch_audit.json`.
- Visual repair evidence: `docs/automation/V6_PUBLIC_TELEGRAM_SUBSTACK_VISUAL_REGRESSION_REPAIR/public_telegram_substack_visual_regression_repair_evidence_v0.json`.

Evidence to read before the next task:

- `docs/automation/V6_EDITORIAL_QUALITY_AUDIT/editorial_quality_audit_v0.json`
- `docs/automation/V6_MEDIA_DIVERSIFICATION/media_diversification_audit_v0.json`
- `docs/automation/V6_DAILY_EDITORIAL_SCHEDULE/daily_schedule_2026_07_08.json`
- `docs/automation/V6_EDITORIAL_NEWSROOM_FINAL_CANDIDATE/newsroom_media_scheduler_final_candidate_evidence_v0.json`
- `docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json`
- `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/platform_variant_packet.json`
- `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/latest_dispatch_audit.json`
- `headline_ingestion/README.md`
- `headline_ingestion/Data_Ingestion.py`

Recommended next task:

```text
TASK_CONTENTOPS_V6_FRESH_NEWS_8_PLATFORM_PUBLIC_CANDIDATE_READBACK_AND_CROP_QA_V0
```

Purpose: rerun after the operator starts the X-list CDP ingestion browser on port `9222` or provides current headline sidecars under `headline_ingestion/data/intake/headline_sidecars/`; then choose a fresh schedule slot, run one non-bypassed 8-platform live candidate only after editorial/media gates pass, and capture public readback/crop/visual placement proof. The run must preserve the repaired Telegram photo-proof and Substack public-readback visual gates.

Out of scope for the next task:

- Do not build TikTok.
- Do not build YouTube video, Shorts, or a video creator.
- Do not build ElevenLabs/video voice lanes.
- Keep YouTube Community as a future text/image platform after the current 8-platform QA lane is hardened.
