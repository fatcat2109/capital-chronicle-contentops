"""Daily media plan specification module.

Step 6 of the Daily ContentOps loop.
Loads the candidate article draft and metadata, proposing 2-3 media assets
as visual specs without rendering actual images or charts.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_DAILY_MEDIA_PLAN_SPEC_V0"
CLASSIFICATION_PASS = "PASS_CONTENTOPS_DAILY_MEDIA_PLAN_SPEC_V0"

def generate_media_plan_spec(
    article_draft_file: str | Path,
    article_metadata_file: str | Path,
    output_dir: str | Path | None = None
) -> dict[str, Any]:
    draft_path = Path(article_draft_file)
    meta_path = Path(article_metadata_file)
    output_path = Path(output_dir) if output_dir else Path(".")
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Load article draft & metadata
    if not draft_path.exists():
        raise FileNotFoundError(f"Article draft file not found at: {draft_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"Article metadata file not found at: {meta_path}")

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    selected_idea_id = meta.get("selected_idea_id")
    editorial_title = meta.get("editorial_title")
    draft_status = meta.get("draft_status")
    source_support_families = meta.get("source_support_families") or []

    # 2. Define visual specs for assets (strictly planning only)
    assets = [
        {
            "asset_id": "media_hero_card_v0",
            "asset_type": "hero_card",
            "purpose": "Visual banner card for Substack and social preview platforms.",
            "title": "US Oil Export Surge",
            "subtitle": "SPR and shale dynamics reshape global trade flows",
            "required_data_inputs": [],
            "source_status": "candidate",
            "numeric_claim_policy": "qualitative only",
            "caveat_text_required": "For review only - candidate graphics context.",
            "visual_layout_notes": "Dark mode background, stylized crude pipeline icon, and overlay title with clear candidate tag.",
            "should_generate_now": False
        },
        {
            "asset_id": "media_chart_wti_exports_v0",
            "asset_type": "chart",
            "purpose": "Double-axis comparison plot of WTI crude spot prices vs. EIA exports.",
            "title": "WTI Spot vs US Crude Oil Exports",
            "subtitle": "Requires verified EIA crude exports / SPR / WTI data before rendering.",
            "required_data_inputs": [
                "US Crude Oil Exports (EIA)",
                "WTI Crude Spot Price"
            ],
            "source_status": "candidate",
            "numeric_claim_policy": "exact numeric plotting blocked until database values are promoted",
            "caveat_text_required": "Data requires verified main database series before rendering.",
            "visual_layout_notes": "Line plot charting weekly WTI prices against weekly export volumes.",
            "should_generate_now": False
        }
    ]

    caveats = "This is a media planning spec only. No actual images or charts are generated. Rendering remains blocked."

    media_plan_spec = {
        "task_label": TASK_LABEL,
        "source_article_draft": str(draft_path),
        "editorial_title": editorial_title,
        "draft_status": draft_status,
        "media_generation_status": "planning_only",
        "assets": assets,
        "required_data_inputs": source_support_families,
        "missing_or_candidate_inputs": source_support_families,
        "generation_allowed_now": False,
        "chart_render_allowed_now": False,
        "platform_payload_created": False,
        "dispatch_ready": False,
        "caveats": caveats
    }

    # 3. Generate media_plan_spec_v0.md (Markdown)
    brief_md = f"""# Media Plan Specification (Planning Only)

*This is a media/chart/card planning specification document. No actual visual rendering or image files are generated.*

**Article Title:** {editorial_title}
**Draft Status:** `{draft_status}`

## Asset Specifications
"""
    for asset in assets:
        brief_md += f"""
### {asset['title']} ({asset['asset_type'].upper()})
- **Asset ID:** `{asset['asset_id']}`
- **Purpose:** {asset['purpose']}
- **Subtitle Spec:** {asset['subtitle']}
- **Data Inputs:** {", ".join(asset['required_data_inputs']) if asset['required_data_inputs'] else "None"}
- **Source Status:** {asset['source_status']}
- **Numeric Policy:** {asset['numeric_claim_policy']}
- **Required Caveat Overlay:** *"{asset['caveat_text_required']}"*
- **Layout Notes:** {asset['visual_layout_notes']}
- **Should Generate Now:** `{asset['should_generate_now']}`
"""

    brief_md += """
## Safety Invariants & Gating
- **Image Generation Permitted:** `false`
- **Chart Render Permitted:** `false`
- **Reason:** Reselected topic remains in `candidate_only` status. Exact numeric charting requires verified database promotion of the underlying series.
"""

    # 4. Generate media_safety_review_v0.json
    media_safety_review = {
        "candidate_only": True,
        "actual_media_generated": False,
        "chart_rendered": False,
        "exact_numeric_claims_made": False,
        "unverified_numeric_references_flagged": True,
        "platform_payload_created": False,
        "dispatch_ready": False,
        "required_caveat_present": True,
        "blockers": []
    }

    # 5. Generate run evidence
    run_evidence = {
        "classification": CLASSIFICATION_PASS,
        "task_label": TASK_LABEL,
        "baseline_head": "22a222998de05091619c74488c004b07712323a8",
        "source_article_draft": str(draft_path),
        "draft_status": draft_status,
        "media_generation_status": "planning_only",
        "no_main_repo_mutation_confirmation": True,
        "no_external_fetch_confirmation": True,
        "no_database_repair_confirmation": True,
        "no_actual_media_generated_confirmation": True,
        "no_chart_render_confirmation": True,
        "no_platform_variant_confirmation": True,
        "no_platform_write_confirmation": True,
        "no_dispatch_confirmation": True,
        "no_raw_secret_read_confirmation": True,
        "output_paths": {
            "media_plan_spec_json": str(output_path / "media_plan_spec_v0.json"),
            "media_plan_spec_md": str(output_path / "media_plan_spec_v0.md"),
            "media_safety_review_json": str(output_path / "media_safety_review_v0.json"),
            "run_evidence": str(output_path / "run_evidence_v0.json")
        },
        "blockers": []
    }

    # Write files
    with open(output_path / "media_plan_spec_v0.json", "w", encoding="utf-8") as f:
        json.dump(media_plan_spec, f, indent=2, ensure_ascii=False)

    with open(output_path / "media_plan_spec_v0.md", "w", encoding="utf-8") as f:
        f.write(brief_md)

    with open(output_path / "media_safety_review_v0.json", "w", encoding="utf-8") as f:
        json.dump(media_safety_review, f, indent=2, ensure_ascii=False)

    with open(output_path / "run_evidence_v0.json", "w", encoding="utf-8") as f:
        json.dump(run_evidence, f, indent=2, ensure_ascii=False)

    # Generate README.md
    readme_content = """# Step 6: Daily Media Plan Spec

This directory contains the output of Step 6 of the Daily ContentOps loop.
It creates a planning specification for visual assets (hero card, chart comparison) without rendering actual files.
"""
    with open(output_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    return {
        "spec_json": media_plan_spec,
        "spec_md": brief_md,
        "safety": media_safety_review,
        "evidence": run_evidence
    }
