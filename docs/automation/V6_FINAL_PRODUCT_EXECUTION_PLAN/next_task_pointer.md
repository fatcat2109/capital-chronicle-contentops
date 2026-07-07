# V6 Next Task Pointer

Current task just completed: `TASK_CONTENTOPS_V6_NON_BYPASSED_LONGFORM_LIVE_RUN_AND_SOURCE_DEPTH_VALIDATION_V0`.

Result: non-bypassed live validation run `v6_pipeline_77936ed4a048` was executed from verified remote HEAD `17c99cdd8bca27e084b9ca827d8fd6aed57958b0` with `CONTENTOPS_BYPASS_QUALITY_GATES=false`, live provider enabled, dispatch enabled, and the default 420s timeout. The run did not reach `DISPATCH_COMPLETE`; it correctly stopped at `DISPATCH_BLOCKED` before any platform dispatch because the article failed the long-form quality gate.

Exact dispatch blockers from `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/latest_dispatch_audit.json`:

- `article_provider_recovery_not_publishable`
- `article_too_short_words:127<2000`
- `too_few_sections`
- `source_trail_claims_too_generic`
- `missing_specific_numbers`

Media judgment status: `PASS`. The search-style candidate was rejected for weak provenance/time coverage, and the system selected current source-backed FRED/EIA WTI chart assets with latest observation date `2026-06-29`. Because article quality blocked the run before Substack publish, no new public Substack URL, public image URL, or platform IDs were produced.

North star: a dashboard-triggered full automation pipeline that generates a publication-quality, source-backed article, dispatches live to all supported lanes with real media/link evidence, or blocks loudly with exact reasons. No dry-run/simulated success and no quality-gate bypass are allowed on the launch path.

Recommended next task:

```text
TASK_CONTENTOPS_V6_PROVIDER_LONGFORM_SOURCE_DEPTH_AND_NUMERIC_EVIDENCE_FIX_V0
```

Purpose: Fix the live article provider/writer path so it reliably produces 2000+ word, 5+ section, source-specific, numeric-evidence-rich long-form articles with SEO metadata and purposeful visual slots, without falling back to non-publishable deterministic recovery. Then rerun the full live dispatch without `CONTENTOPS_BYPASS_QUALITY_GATES=true` and only claim success if the pipeline reaches true `DISPATCH_COMPLETE`.

Evidence to read before the next task:

- `docs/automation/V6_NON_BYPASSED_LONGFORM_LIVE_RUN/non_bypassed_live_run_evidence_v0.json`
- `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/latest_dispatch_audit.json`
- `docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json`
- `docs/automation/V6_PLATFORM_NATIVE_VARIANTS/platform_variant_packet.json`
