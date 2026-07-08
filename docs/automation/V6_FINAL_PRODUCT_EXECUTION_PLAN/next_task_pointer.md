# V6 Next Task Pointer

Current task just completed: `TASK_CONTENTOPS_V6_POST_VISUAL_REPAIR_BASELINE_AND_EDITORIAL_QA_GATE_V0`.

Baseline reconciliation:

- Verified pre-task remote `master`: `bcf5574d16a433b7b1b3bcb6deea2d7ead402502` (`Isolate Step 1 headlines ingestion tool via CDP`).
- Accepted visual repair commit: `6a810aadadef4b3c9078173b32bed4b243f8552a`.
- Latest scoped visual repair run: `v6_pipeline_d49f6e14a856`, Substack + LinkedIn `DISPATCH_COMPLETE`.
- Prior full 8-platform run remains reconciled for unaffected lanes.
- Step 1 headline ingestion is isolated under `headline_ingestion/`; source list target is `https://x.com/i/lists/1843870469143048642`.

What changed:

- Added deterministic editorial quality audit module: `live_contentops/editorial_quality_audit_v6.py`.
- Article packets and dispatch audits now carry `editorial_acceptance_status` and `tier1_editorial_approved`.
- `pipeline_status=DISPATCH_COMPLETE` remains transport evidence only and must not imply `TIER1_EDITORIAL_APPROVED`.
- WTI deterministic article repair no longer promotes unrelated search-result URLs into canonical citations when structured FRED/EIA evidence is the real source base.

Latest Crude Awakenings audit:

- Dispatch status: `DISPATCH_COMPLETE` for scoped Substack + LinkedIn repair evidence.
- Editorial acceptance status: `EDITORIAL_BLOCKED`.
- `tier1_editorial_approved=false`.
- Blockers:
  - unrelated Yahoo Finance URLs in canonical `citations`
  - unrelated Yahoo Finance URLs in `source_notes_for_operator` / grounding source notes
- Review items:
  - `seo_target_keyword_not_topic_aligned`
  - `source_diversity_too_narrow:2<3`
  - `public_body_pipeline_internal_language:13`
- Evidence packet: `docs/automation/V6_EDITORIAL_QUALITY_AUDIT/editorial_quality_audit_v0.json`.

Recommended next task:

```text
TASK_CONTENTOPS_V6_MEDIA_DIVERSIFICATION_RIGHTS_PROVENANCE_AND_PUBLIC_VISUAL_QA_V0
```

Purpose: diversify source-backed visuals beyond single-series WTI charts, add media rights/provenance review fields, harden public screenshot/crop QA, and preserve the editorial QA gate before any new platform expansion.

Out of scope for the next task:

- Do not build TikTok.
- Do not build YouTube video, Shorts, or a video creator.
- Do not build YouTube Community yet. Record it only as a future text/image distribution platform after the current 8-platform QA lane is hardened.

Evidence to read before the next task:

- `docs/automation/V6_EDITORIAL_QUALITY_AUDIT/editorial_quality_audit_v0.json`
- `docs/automation/V6_LINKEDIN_SUBSTACK_VISUAL_REPAIR/linkedin_substack_visual_repair_evidence_v0.json`
- `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/latest_dispatch_audit.json`
- `docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json`
- `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/platform_variant_packet.json`
- `headline_ingestion/README.md`
- `headline_ingestion/Data_Ingestion.py`
