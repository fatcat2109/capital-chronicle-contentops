# V6 Next Task Pointer

Current task: `TASK_CONTENTOPS_V6_MEDIA_JUDGMENT_AND_ARTICLE_VISUAL_STRUCTURE_GATE_V0` — Real media transport remains operational, but the latest screenshot audit showed that transport success is not editorial success. The pipeline now adds deterministic media-content audit checks for provenance, currentness, time coverage, relevance, and thesis/direction alignment; rejects branded fallback cards as launch visuals; can replace failed oil-topic search visuals with current source-backed WTI/FRED chart packs; and inserts multiple Substack in-body visual markers instead of appending one chart at the bottom.

North star: a dashboard-triggered full automation pipeline that generates a publication-quality, source-backed article, dispatches live to all supported lanes with real media/link evidence, or blocks loudly with exact reasons. No dry-run/simulated success and no quality-gate bypass are allowed on the launch path.

Recommended next task:

```text
TASK_CONTENTOPS_V6_NON_BYPASSED_LONGFORM_LIVE_RUN_AND_SOURCE_DEPTH_VALIDATION_V0
```

Purpose: Run the full live pipeline without `CONTENTOPS_BYPASS_QUALITY_GATES=true`, verify the provider can produce a publishable long-form article with source depth, SEO metadata, and multiple audited in-body visuals, then audit every public platform output for visual relevance, crop quality, attribution, link behavior, and platform-native editorial distribution quality.
