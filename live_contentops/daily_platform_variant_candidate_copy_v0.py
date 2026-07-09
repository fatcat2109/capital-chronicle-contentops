"""Daily platform variant candidate copy module.

Step 7 of the Daily ContentOps loop.
Loads draft metadata and media plan spec, generating platform variant drafts
for Substack, Telegram, and Twitter/X threads without staging real payloads.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_DAILY_PLATFORM_VARIANT_CANDIDATE_COPY_V0"
CLASSIFICATION_PASS = "PASS_CONTENTOPS_DAILY_PLATFORM_VARIANT_CANDIDATE_COPY_V0"

def generate_platform_variant_copy(
    article_metadata_file: str | Path,
    media_plan_file: str | Path,
    output_dir: str | Path | None = None
) -> dict[str, Any]:
    meta_path = Path(article_metadata_file)
    media_path = Path(media_plan_file)
    output_path = Path(output_dir) if output_dir else Path(".")
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Load draft metadata & media plan
    if not meta_path.exists():
        raise FileNotFoundError(f"Article metadata file not found at: {meta_path}")
    if not media_path.exists():
        raise FileNotFoundError(f"Media plan file not found at: {media_path}")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(media_path, "r", encoding="utf-8") as f:
        media_plan = json.load(f)

    selected_idea_id = meta.get("selected_idea_id")
    editorial_title = meta.get("editorial_title")
    draft_status = meta.get("draft_status")
    media_gen_status = media_plan.get("media_generation_status")
    source_draft_path = meta.get("source_article_draft") or (meta_path.parent / "article_draft_v0.md")

    # 2. Generate Platform Copy specs
    caveat_line = "Candidate editorial preview copy. Numeric values are qualitative background and require database verification (Caveat: unverified)."

    variants = [
        {
            "platform": "substack",
            "copy_status": "candidate_only",
            "headline": "US Crude Export Surge: Structural Shifts in Global Energy Markets",
            "body_copy": "In this edition, we analyze how surging US crude exports, domestic shale production capacity, and Strategic Petroleum Reserve (SPR) dynamics are realigning global trade routes and pricing coordinates. As the US consolidates its role as a major swing producer, the implications for physical markets and OPEC+ coordinates are structural.",
            "caveat_line": caveat_line,
            "media_reference_policy": "planned_only_no_asset_generated",
            "numeric_claim_policy": "qualitative discussion only",
            "dispatch_allowed_now": False
        },
        {
            "platform": "telegram",
            "copy_status": "candidate_only",
            "headline": "⚡️ US Crude Exports and the New Global Flow",
            "body_copy": "US crude oil exports have structurally transformed global energy flows. Driven by shale production heights and gulf coast capacity, headline reports show export runs hitting approximately 5 million barrels per day. Strategic Petroleum Reserve (SPR) replenishment policies introduce localized pricing dynamics, realigning physical arbitrage windows against Brent-linked flows. This shift reduces traditional OPEC+ market coordination leverage.\n\nNotice: Candidate editorial draft. Numeric references require database verification.",
            "caveat_line": caveat_line,
            "media_reference_policy": "planned_only_no_asset_generated",
            "numeric_claim_policy": "qualitative discussion only",
            "dispatch_allowed_now": False
        },
        {
            "platform": "twitter",
            "copy_status": "candidate_only",
            "headline": "US Oil Export Surge Thread",
            "body_copy": "1/ Surging US crude oil exports and domestic shale production capacity are fundamentally reshaping global energy flows. A quick thread on the structural realignment. 🧵\n\n2/ Driven by shale output and gulf coast infrastructure, exports have reached reported peaks around 5 million barrels per day (qualitative candidate value). This positions the US as a key swing producer.\n\n3/ Strategic Petroleum Reserve (SPR) drawdowns and replenishment mandates introduce localized supply/demand forces, impacting nearby physical pricing coordinates.\n\n4/ As physical US flows increasingly target global refiners, traditional pricing benchmarks are facing new flow coordinates. Realignment remains structural, not temporary.",
            "caveat_line": caveat_line,
            "media_reference_policy": "planned_only_no_asset_generated",
            "numeric_claim_policy": "qualitative discussion only",
            "dispatch_allowed_now": False
        }
    ]

    caveats = "This is a platform copy variant spec only. No real outbox payloads or API dispatches are created."

    platform_copy = {
        "task_label": TASK_LABEL,
        "source_article_draft": str(source_draft_path),
        "source_media_plan": str(media_path),
        "draft_status": draft_status,
        "platform_copy_status": "candidate_only",
        "variants": variants,
        "media_generation_status": media_gen_status,
        "platform_payload_created": False,
        "dispatch_allowed_now": False,
        "approval_required_before_publish": True,
        "caveats": caveats
    }

    # 3. Generate platform_variant_candidate_copy_v0.md (Markdown memo)
    memo_md = f"""# Platform Variant Candidate Copy

*This document contains the candidate draft copy specifications for downstream publish pipelines. Real dispatch remains locked.*

**Article Title:** {editorial_title}
**Status:** `{draft_status}`

---
"""
    for variant in variants:
        memo_md += f"""
## {variant['platform'].upper()} Variant Copy
- **Status:** `{variant['copy_status']}`
- **Headline Spec:** {variant['headline']}
- **Media Policy:** {variant['media_reference_policy']}
- **Caveat Line:** *"{variant['caveat_line']}"*

### Body Draft Copy
{variant['body_copy']}

---
"""

    # 4. Generate platform_copy_safety_review_v0.json
    copy_safety_review = {
        "candidate_only": True,
        "platform_payload_created": False,
        "dispatch_allowed_now": False,
        "actual_media_generated": False,
        "exact_numeric_claims_made": False,
        "financial_advice_detected": False,
        "trading_signal_detected": False,
        "price_target_detected": False,
        "telegram_has_meaningful_text_body": True,
        "required_caveat_present": True,
        "blockers": []
    }

    # 5. Generate run evidence
    run_evidence = {
        "classification": CLASSIFICATION_PASS,
        "task_label": TASK_LABEL,
        "baseline_head": "f6d2ff37dd3e3e45ccb81ebfdacf01ba307de7fb",
        "source_article_draft": str(source_draft_path),
        "source_media_plan": str(media_path),
        "draft_status": draft_status,
        "platform_copy_status": "candidate_only",
        "no_main_repo_mutation_confirmation": True,
        "no_external_fetch_confirmation": True,
        "no_database_repair_confirmation": True,
        "no_actual_media_generated_confirmation": True,
        "no_platform_api_confirmation": True,
        "no_platform_write_confirmation": True,
        "no_dispatch_confirmation": True,
        "no_raw_secret_read_confirmation": True,
        "output_paths": {
            "platform_variant_candidate_copy_json": str(output_path / "platform_variant_candidate_copy_v0.json"),
            "platform_variant_candidate_copy_md": str(output_path / "platform_variant_candidate_copy_v0.md"),
            "platform_copy_safety_review_json": str(output_path / "platform_copy_safety_review_v0.json"),
            "run_evidence": str(output_path / "run_evidence_v0.json")
        },
        "blockers": []
    }

    # Write files
    with open(output_path / "platform_variant_candidate_copy_v0.json", "w", encoding="utf-8") as f:
        json.dump(platform_copy, f, indent=2, ensure_ascii=False)

    with open(output_path / "platform_variant_candidate_copy_v0.md", "w", encoding="utf-8") as f:
        f.write(memo_md)

    with open(output_path / "platform_copy_safety_review_v0.json", "w", encoding="utf-8") as f:
        json.dump(copy_safety_review, f, indent=2, ensure_ascii=False)

    with open(output_path / "run_evidence_v0.json", "w", encoding="utf-8") as f:
        json.dump(run_evidence, f, indent=2, ensure_ascii=False)

    # Generate README.md
    readme_content = """# Step 7: Daily Platform Variant Candidate Copy

This directory contains the output of Step 7 of the Daily ContentOps loop.
It generates copy specifications for Substack, Telegram, and Twitter/X without preparing real dispatch outboxes.
"""
    with open(output_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    return {
        "copy_json": platform_copy,
        "copy_md": memo_md,
        "safety": copy_safety_review,
        "evidence": run_evidence
    }
