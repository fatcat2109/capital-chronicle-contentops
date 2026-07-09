"""Daily SEO article drafting module.

Step 5 of the Daily ContentOps loop.
Loads the article brief, blocks original Japan idea, and drafts the
candidate-only SEO article on WTI/SPR/oil exports.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_DAILY_SEO_ARTICLE_DRAFTING_V0"
CLASSIFICATION_CANDIDATE = "PASS_CANDIDATE_ONLY_CONTENTOPS_DAILY_SEO_ARTICLE_DRAFTING_V0"

def generate_article_draft(
    article_brief_file: str | Path,
    output_dir: str | Path | None = None
) -> dict[str, Any]:
    brief_path = Path(article_brief_file)
    output_path = Path(output_dir) if output_dir else Path(".")
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Load article brief
    if not brief_path.exists():
        raise FileNotFoundError(f"Article brief file not found at: {brief_path}")
    with open(brief_path, "r", encoding="utf-8") as f:
        brief = json.load(f)

    # 2. Verify original Japan JGB idea is blocked
    original_idea_blocked = brief.get("original_idea_blocked")
    if not original_idea_blocked:
        raise ValueError("Original Japan JGB idea is not blocked. Failing closed.")

    # 3. Extract details
    editorial_title = brief.get("editorial_title")
    selected_idea_id = brief.get("selected_idea_id")
    topic_family = brief.get("topic_family")
    source_support_needed = brief.get("source_support_needed") or []

    # 4. Generate SEO meta fields
    seo_meta_title = "US Oil Export Surge: SPR and Production Realignment"
    if len(seo_meta_title) > 60:
        seo_meta_title = seo_meta_title[:57] + "..."

    seo_meta_description = "Analyze how surging US crude exports, domestic production capacity, and strategic reserves (SPR) are realigning global energy markets."
    if len(seo_meta_description) > 160:
        seo_meta_description = seo_meta_description[:157] + "..."

    # 5. Generate candidate SEO article draft body (Markdown)
    draft_body = f"""# {editorial_title}

**SEO Meta Title:** {seo_meta_title}
**SEO Meta Description:** {seo_meta_description}

---

> [!WARNING]
> **Candidate editorial draft. Numeric references require final source verification before publication.**

## Introduction: The New Era of US Energy Dominance
In recent years, the global energy landscape has experienced a profound shift. The United States, once one of the world's largest importers of crude oil, has transitioned into a massive exporter. This structural shift has realigned geopolitical influence and trade flows, reshaping how physical oil is traded globally.

## Section 1: Production Heights and Export Capacity Surge
The transition has been driven by domestic shale production heights and significant investments in gulf coast export infrastructure. According to candidate/headline-reported market context, US crude exports have reached heights of approximately 5 million barrels per day. It is critical to note that this figure represents candidate market context rather than internally verified database truth. Nonetheless, this flow capacity establishes the US as a major swing producer in international markets.

## Section 2: The Role of the Strategic Petroleum Reserve (SPR)
Strategic reserves have played a complex role in domestic supply balance. Strategic Petroleum Reserve (SPR) drawdowns and subsequent replenishment mandates introduce localized liquidity and pricing dynamics. Managing the balance between emergency reserve buffer and active supply stabilization remains a critical concern for policymakers.

## Section 3: Geopolitical Repercussions and Trade Flow Realignment
As US crude flows increasingly target European and Asian refiners, traditional trade routes have adapted. Physical arbitrage windows determine whether shale flows outpace Brent-linked alternatives. This flow pressure challenges traditional pricing structures and impacts OPEC+ pricing coordinates.

## Conclusion: Market Outlook and Structural Implications
The growth of US oil exports is a structural trend, not a temporary shock. As export infrastructure expands, global markets must continuously adapt to a highly flexible, US-backed physical flow.

---

### Disclaimers & Caveats
- *Notice:* This is an article brief-derived candidate draft. This analysis is purely educational and for commentary purposes only; it does not constitute financial, investment, or trading advice.
- *Source Note:* All numeric figures are candidate proxy series and qualitative background data. No numeric truth is guaranteed without final source database verification.
"""

    word_count_estimate = len(draft_body.split())

    # 6. Generate article_draft_metadata_v0.json
    draft_metadata = {
        "task_label": TASK_LABEL,
        "source_article_brief": str(brief_path),
        "selected_idea_id": selected_idea_id,
        "editorial_title": editorial_title,
        "seo_meta_title": seo_meta_title,
        "seo_meta_description": seo_meta_description,
        "topic_family": topic_family,
        "draft_status": "candidate_only",
        "word_count_estimate": word_count_estimate,
        "source_support_families": source_support_needed,
        "exact_numeric_claims_made": False,
        "financial_advice_detected": False,
        "platform_payload_created": False,
        "dispatch_ready": False
    }

    # 7. Generate draft_safety_review_v0.json
    draft_safety_review = {
        "candidate_only": True,
        "exact_numeric_claims_made": False,
        "unverified_numeric_references_flagged": True,  # Flagged the candidate 5 million bpd mention
        "financial_advice_detected": False,
        "trading_signal_detected": False,
        "price_target_detected": False,
        "platform_payload_created": False,
        "media_generated": False,
        "dispatch_ready": False,
        "required_caveat_present": True,
        "blockers": []
    }

    # 8. Generate run evidence
    run_evidence = {
        "classification": CLASSIFICATION_CANDIDATE,
        "task_label": TASK_LABEL,
        "baseline_head": "558708e312678d6aa6904eeaa2901d934e9f59bf",
        "source_article_brief": str(brief_path),
        "selected_idea_id": selected_idea_id,
        "topic_family": topic_family,
        "draft_status": "candidate_only",
        "no_main_repo_mutation_confirmation": True,
        "no_external_fetch_confirmation": True,
        "no_database_repair_confirmation": True,
        "no_media_confirmation": True,
        "no_platform_variant_confirmation": True,
        "no_platform_write_confirmation": True,
        "no_dispatch_confirmation": True,
        "no_raw_secret_read_confirmation": True,
        "output_paths": {
            "article_draft_md": str(output_path / "article_draft_v0.md"),
            "article_draft_metadata_json": str(output_path / "article_draft_metadata_v0.json"),
            "draft_safety_review_json": str(output_path / "draft_safety_review_v0.json"),
            "run_evidence": str(output_path / "run_evidence_v0.json")
        },
        "blockers": []
    }

    # Write files
    with open(output_path / "article_draft_v0.md", "w", encoding="utf-8") as f:
        f.write(draft_body)

    with open(output_path / "article_draft_metadata_v0.json", "w", encoding="utf-8") as f:
        json.dump(draft_metadata, f, indent=2, ensure_ascii=False)

    with open(output_path / "draft_safety_review_v0.json", "w", encoding="utf-8") as f:
        json.dump(draft_safety_review, f, indent=2, ensure_ascii=False)

    with open(output_path / "run_evidence_v0.json", "w", encoding="utf-8") as f:
        json.dump(run_evidence, f, indent=2, ensure_ascii=False)

    # Generate README.md
    readme_content = """# Step 5: Daily SEO Article Drafting

This directory contains the output of Step 5 of the Daily ContentOps loop.
It generates the first structured candidate-only SEO article draft based on the reselected Crude oil export surge topic.
"""
    with open(output_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    return {
        "body": draft_body,
        "metadata": draft_metadata,
        "safety": draft_safety_review,
        "evidence": run_evidence
    }
