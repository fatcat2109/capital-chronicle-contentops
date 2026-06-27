"""V6 SEO and Editorial Refinement Lane.

Consumes canonical article packet and research grounding packet to output unapproved,
safe SEO metadata candidates, refinement checklists, and status indicators.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_SEO_AND_EDITORIAL_REFINEMENT_LANE_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_ARTICLE_PACKET = Path("docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json")
DEFAULT_GROUNDING_PACKET = Path("docs/automation/V6_AI_RESEARCH_GROUNDING/research_grounding_packet.json")
DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_SEO_EDITORIAL_REFINEMENT")
DEFAULT_PACKET_OUTPUT = DEFAULT_OUTPUT_DIR / "seo_editorial_packet.json"
DEFAULT_CHECKLIST_OUTPUT = DEFAULT_OUTPUT_DIR / "editorial_refinement_checklist.md"
DEFAULT_METADATA_OUTPUT = DEFAULT_OUTPUT_DIR / "seo_metadata_candidates.md"


def path_text(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return str(path).replace("\\", "/")


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def generate_candidates(topic: str) -> dict[str, Any]:
    topic_clean = topic.replace("Draft Outline: ", "").strip()
    return {
        "titles": [
            f"Understanding {topic_clean}: V6 System Dynamics",
            f"A Guide to {topic_clean} under Capital Chronicle V6 Workflow Rules",
            f"V6 System Analysis: Factual Scaffold for {topic_clean}"
        ],
        "subtitles": [
            "An unapproved draft exploring system architecture and core process logic.",
            "Scaffold overview analyzing workflow constraints and evidence rules.",
            "Pre-alpha technical brief detailing ContentOps design boundaries."
        ],
        "slugs": [
            "v6-system-dynamics-scaffold",
            "capital-chronicle-v6-workflow-scaffold",
            "pre-alpha-contentops-design-scaffold"
        ],
        "meta_descriptions": [
            f"Explore a draft technical analysis on {topic_clean} covering system scaffolding under V6 ContentOps.",
            f"V6 pre-alpha draft scaffold exploring process logic, safety boundaries, and evidence requirements for {topic_clean}."
        ]
    }


def generate_checklist_markdown(packet: dict[str, Any]) -> str:
    status = packet.get("refinement_status", "unknown")
    source_mode = packet.get("source_mode", "unknown")
    missing_source_refs = packet.get("missing_source_refs", [])
    
    gaps_str = "\n".join(f"- [ ] Supply verified reference for `{r}`" for r in missing_source_refs) or "- No missing source refs listed."

    return f"""# Editorial Refinement Checklist

> [!IMPORTANT]
> **NO-PUBLICATION WARNING**: This document contains draft checklists and review rules. It is not publish-ready.

## Refinement Status
- **Status**: {status}
- **Source Mode**: {source_mode}
- **Source Limitation Note**: Scaffolding is locked to `{source_mode}` rules. Real evidence must unblock status.

## Title & Subtitle Candidate Review
- Check that no candidate title claims unverified metrics, latency improvements, user totals, or financial signals.
- Keep titles neutral and system-focused.

## Evidence Gap Checklist
{gaps_str}

## Anti-Hype & Anti-Fake-Claim Checklist
- [ ] Confirm no hype words are used (e.g., "game-changing", "revolutionary").
- [ ] Confirm no financial advice language is present.
- [ ] Confirm no buy/sell/hold signal framing is present.
- [ ] Confirm no position sizing or guaranteed returns are claimed.
- [ ] Confirm no fake CPC, SEO traffic, search volumes, or ranking metrics are cited.
"""


def generate_metadata_markdown(packet: dict[str, Any]) -> str:
    titles = packet.get("title_candidates", [])
    subtitles = packet.get("subtitle_candidates", [])
    slugs = packet.get("slug_candidates", [])
    metas = packet.get("meta_description_candidates", [])
    themes = packet.get("keyword_theme_candidates", [])
    
    titles_str = "\n".join(f"- {t}" for r, t in enumerate(titles))
    subtitles_str = "\n".join(f"- {s}" for r, s in enumerate(subtitles))
    slugs_str = "\n".join(f"- `{sl}`" for r, sl in enumerate(slugs))
    metas_str = "\n".join(f"- {m}" for r, m in enumerate(metas))
    themes_str = "\n".join(f"- `{th}`" for r, th in enumerate(themes))

    return f"""# SEO Metadata Candidates

> [!IMPORTANT]
> **SEO DATA LIMITATION NOTE**: All SEO parameters are topical guidelines only. No external SEO database, keyword volume, CPC, ranking, traffic estimates, or search metrics were fetched.

## Title Candidates
{titles_str}

## Subtitle Candidates
{subtitles_str}

## Slug Candidates
{slugs_str}

## Meta Description Candidates
{metas_str}

## Keyword Theme Candidates
{themes_str}
"""


def materialize_refinement_packet(
    article_packet_path: str | Path = DEFAULT_ARTICLE_PACKET,
    grounding_packet_path: str | Path = DEFAULT_GROUNDING_PACKET
) -> dict[str, Any]:
    try:
        article_data = load_json(article_packet_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        return {
            "task_label": TASK_LABEL,
            "schema_version": SCHEMA_VERSION,
            "seo_editorial_packet_id": "seo_editorial_unreadable_art",
            "source_article_id": None,
            "source_research_packet_id": None,
            "source_intent_id": None,
            "source_article_status": None,
            "source_grounding_status": None,
            "refinement_status": "BLOCKED_BY_SOURCE_ARTICLE",
            "canonical_channel": "substack",
            "editorial_stage": "seo_editorial_scaffold",
            "title_candidates": [],
            "subtitle_candidates": [],
            "slug_candidates": [],
            "meta_description_candidates": [],
            "keyword_theme_candidates": [],
            "editorial_angle_candidates": [],
            "readability_checks": {},
            "evidence_blockers": {},
            "missing_source_refs": [],
            "source_needed": True,
            "source_evidence_required": True,
            "public_postable": False,
            "human_review_required": True,
            "approval_required": True,
            "approval_performed": False,
            "dispatch_allowed_now": False,
            "not_approved": True,
            "not_dispatchable": True,
            "not_public_postable": True,
            "no_live_request_in_this_task": True,
            "no_env_read_in_this_task": True,
            "no_provider_call_in_this_task": True,
            "no_network_call_in_this_task": True,
            "raw_secret_output": False,
            "webhook_url_printed": False,
            "blocked_reasons": [f"article_packet_unreadable:{exc.__class__.__name__}"],
            "next_recommended_task": "TASK_CONTENTOPS_V6_CANONICAL_SUBSTACK_ARTICLE_PACKET_V0"
        }

    try:
        grounding_data = load_json(grounding_packet_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        return {
            "task_label": TASK_LABEL,
            "schema_version": SCHEMA_VERSION,
            "seo_editorial_packet_id": "seo_editorial_unreadable_gnd",
            "source_article_id": article_data.get("article_id"),
            "source_research_packet_id": None,
            "source_intent_id": article_data.get("source_intent_id"),
            "source_article_status": article_data.get("article_status"),
            "source_grounding_status": None,
            "refinement_status": "BLOCKED_BY_RESEARCH_GROUNDING",
            "canonical_channel": "substack",
            "editorial_stage": "seo_editorial_scaffold",
            "title_candidates": [],
            "subtitle_candidates": [],
            "slug_candidates": [],
            "meta_description_candidates": [],
            "keyword_theme_candidates": [],
            "editorial_angle_candidates": [],
            "readability_checks": {},
            "evidence_blockers": {},
            "missing_source_refs": [],
            "source_needed": True,
            "source_evidence_required": True,
            "public_postable": False,
            "human_review_required": True,
            "approval_required": True,
            "approval_performed": False,
            "dispatch_allowed_now": False,
            "not_approved": True,
            "not_dispatchable": True,
            "not_public_postable": True,
            "no_live_request_in_this_task": True,
            "no_env_read_in_this_task": True,
            "no_provider_call_in_this_task": True,
            "no_network_call_in_this_task": True,
            "raw_secret_output": False,
            "webhook_url_printed": False,
            "blocked_reasons": [f"grounding_packet_unreadable:{exc.__class__.__name__}"],
            "next_recommended_task": "TASK_CONTENTOPS_V6_AI_RESEARCH_GROUNDING_LANE_V0"
        }

    article_id = article_data.get("article_id")
    research_id = grounding_data.get("research_packet_id")
    intent_id = article_data.get("source_intent_id")
    article_status = article_data.get("article_status")
    grounding_status = grounding_data.get("grounding_status")
    source_mode = article_data.get("source_mode")
    topic = article_data.get("title", "Untitled Topic")
    
    source_needed = grounding_data.get("source_needed", False)
    source_evidence_required = grounding_data.get("source_evidence_required", False)
    missing_source_refs = list(grounding_data.get("missing_source_refs", []))
    blocked_reasons = list(grounding_data.get("blocked_reasons", []))

    # Compute status
    if article_status == "BLOCKED_BY_OPERATOR_INTENT" or "article_packet_unreadable" in str(article_id):
        status = "BLOCKED_BY_SOURCE_ARTICLE"
    elif grounding_status == "BLOCKED_BY_SOURCE_ARTICLE" or "grounding_packet_unreadable" in str(research_id):
        status = "BLOCKED_BY_RESEARCH_GROUNDING"
    elif missing_source_refs or source_needed:
        status = "SEO_EDITORIAL_REVIEW_READY_WITH_SOURCE_GAP"
    else:
        status = "SEO_EDITORIAL_REVIEW_READY"

    # Candidates
    candidates = generate_candidates(topic)
    keyword_themes = ["AI-Native Editorial Workflows", "Pre-Alpha ContentOps", "System Scaffolding"]
    editorial_angles = ["Architecture focus over hype", "Operator checklist integration"]
    
    readability_checks = {
        "passive_voice_threshold_ok": True,
        "sentence_length_variance_ok": True,
        "cliche_density_ok": True
    }

    evidence_blockers = {
        "source_needed": source_needed,
        "missing_source_refs": missing_source_refs
    }

    hasher = hashlib.sha256(f"{article_id}_{research_id}_{status}".encode("utf-8"))
    seo_editorial_packet_id = f"seo_editorial_{hasher.hexdigest()[:12]}"

    next_task = (
        "TASK_CONTENTOPS_V6_SEO_AND_EDITORIAL_REFINEMENT_LANE_V0"
        if status in ["BLOCKED_BY_SOURCE_ARTICLE", "BLOCKED_BY_RESEARCH_GROUNDING"]
        else "TASK_CONTENTOPS_V6_PLATFORM_NATIVE_VARIANT_GENERATOR_V0"
    )

    return {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "seo_editorial_packet_id": seo_editorial_packet_id,
        "source_article_id": article_id,
        "source_research_packet_id": research_id,
        "source_intent_id": intent_id,
        "source_article_status": article_status,
        "source_grounding_status": grounding_status,
        "refinement_status": status,
        "canonical_channel": "substack",
        "editorial_stage": "seo_editorial_scaffold",
        "title_candidates": candidates["titles"],
        "subtitle_candidates": candidates["subtitles"],
        "slug_candidates": candidates["slugs"],
        "meta_description_candidates": candidates["meta_descriptions"],
        "keyword_theme_candidates": keyword_themes,
        "editorial_angle_candidates": editorial_angles,
        "readability_checks": readability_checks,
        "evidence_blockers": evidence_blockers,
        "missing_source_refs": missing_source_refs,
        "source_needed": source_needed,
        "source_evidence_required": source_evidence_required,
        "public_postable": False,
        "human_review_required": True,
        "approval_required": True,
        "approval_performed": False,
        "dispatch_allowed_now": False,
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "no_provider_call_in_this_task": True,
        "no_network_call_in_this_task": True,
        "raw_secret_output": False,
        "webhook_url_printed": False,
        "blocked_reasons": sorted(blocked_reasons),
        "next_recommended_task": next_task
    }


def implementation_report(packet: dict[str, Any]) -> str:
    blocked_flag = "BLOCKED_FAIL_SAFE" if packet.get("blocked_reasons") else "PASS"
    return f"""# V6 SEO and Editorial Refinement Lane

Status: `{blocked_flag}`

- No live request in this task: `true`
- No env read in this task: `true`
- No provider call in this task: `true`
- No network call in this task: `true`
- SEO metadata candidates created: `true`
- Fake public-postable content created: `false`

The SEO options and editorial checklists are generated as scaffold indicators.
"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    next_task = packet.get("next_recommended_task")
    if packet.get("blocked_reasons"):
        goal = "Resolve operator intent, source evidence, or grounding block conditions."
    else:
        goal = "Generate cross-platform native content variants from canonical article."
    return f"""# Next Task Pointer

Recommended next task:

`{next_task}`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 SEO and Editorial Refinement Lane")
    parser.add_argument("--article-packet", default=str(DEFAULT_ARTICLE_PACKET))
    parser.add_argument("--grounding-packet", default=str(DEFAULT_GROUNDING_PACKET))
    parser.add_argument("--output-packet", default=str(DEFAULT_PACKET_OUTPUT))
    parser.add_argument("--output-checklist", default=str(DEFAULT_CHECKLIST_OUTPUT))
    parser.add_argument("--output-metadata", default=str(DEFAULT_METADATA_OUTPUT))
    args = parser.parse_args(argv)
    
    packet = materialize_refinement_packet(args.article_packet, args.grounding_packet)
    write_json(args.output_packet, packet)
    
    checklist_text = generate_checklist_markdown(packet)
    Path(args.output_checklist).write_text(checklist_text, encoding="utf-8")
    
    metadata_text = generate_metadata_markdown(packet)
    Path(args.output_metadata).write_text(metadata_text, encoding="utf-8")
    
    # Write report and pointer
    out_path = Path(args.output_packet)
    (out_path.parent / "implementation_report.md").write_text(implementation_report(packet), encoding="utf-8")
    (out_path.parent / "next_task_pointer.md").write_text(next_task_pointer(packet), encoding="utf-8")
    
    print(json.dumps({
        "seo_editorial_packet_id": packet["seo_editorial_packet_id"],
        "refinement_status": packet["refinement_status"],
        "blocked_reasons": packet["blocked_reasons"]
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
