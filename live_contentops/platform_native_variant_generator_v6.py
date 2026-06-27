"""V6 Platform Native Variant Generator.

Consumes canonical article, research grounding, and SEO refinement packets
to output unapproved, safe platform-native draft scaffolds.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_PLATFORM_NATIVE_VARIANT_GENERATOR_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_ARTICLE_PACKET = Path("docs/automation/V6_CANONICAL_SUBSTACK_ARTICLE/canonical_article_packet.json")
DEFAULT_GROUNDING_PACKET = Path("docs/automation/V6_AI_RESEARCH_GROUNDING/research_grounding_packet.json")
DEFAULT_SEO_PACKET = Path("docs/automation/V6_SEO_EDITORIAL_REFINEMENT/seo_editorial_packet.json")

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_PLATFORM_NATIVE_VARIANTS")
DEFAULT_PACKET_OUTPUT = DEFAULT_OUTPUT_DIR / "platform_variant_packet.json"


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


def generate_scaffold_text(
    platform: str,
    packet: dict[str, Any]
) -> str:
    status = packet.get("variant_status", "unknown")
    source_mode = packet.get("source_mode", "unknown")
    missing_source_refs = packet.get("missing_source_refs", [])
    
    missing_str = ", ".join(f"`{r}`" for r in missing_source_refs) or "None"
    
    scaffolds = {
        "substack": f"""## Substack Variant Scaffold
- **Type**: Long-form editorial Substack post structure
- **Scaffold Title**: [Draft Title Placeholder]
- **Scaffold Body**:
  [Scaffold introduction exploring core thesis and design guidelines...]
- **Section Checklist**:
  - [ ] Validate V6 performance latency numbers.
  - [ ] Confirm compliance check and editor authorization rules.""",

        "discord": f"""## Discord Variant Scaffold
- **Type**: Short-form community drop announcements draft
- **Channel Target**: announcements
- **Draft content**:
  📢 [Community announcement placeholder: V6 platform update draft scaffold...]""",

        "linkedin": f"""## LinkedIn Variant Scaffold
- **Type**: Professional update / technical overview draft
- **LinkedIn draft**:
  [LinkedIn update placeholder: Explaining V6 system scaffolding to the network...]""",

        "x": f"""## X/Twitter Thread Scaffold
- **Type**: Concise multi-post tweet thread layout
- **Thread layout**:
  1/ [First tweet: topic core intro...]
  2/ [Second tweet: technical details and guidelines...]""",

        "threads": f"""## Threads Variant Scaffold
- **Type**: Conversational post / discussion thread layout
- **Draft layout**:
  [Threads conversational update placeholder...]""",

        "telegram": f"""## Telegram Operator Preview Scaffold
- **Type**: Operator review summary and dashboard checklist
- **Operator Review Status**: AWAITING_OPERATOR_DECISION
- **Source Gap Summary**: {status} (missing source references exist)
- **Target Platform Mapping**:
  - Substack: long_form_scaffold
  - Discord: short_form_drop_scaffold
  - LinkedIn: professional_update_scaffold
  - X: concise_thread_scaffold
  - Threads: conversational_scaffold
  - Telegram: operator_preview_scaffold
- **Missing Evidence Checklist**:
  - [ ] Resolve missing references: {missing_str}
- **Approval Hash/Destination Binding Reminder**: Valid authorization requires an exact operator approval hash matched against an active channel binding target. Do not approve without matching signatures.
- **Dispatch Blocked Status**: dispatch_allowed_now is strictly false."""
    }
    
    plat_key = platform.lower()
    if plat_key == "telegram_operator_preview":
        plat_key = "telegram"
        
    platform_scaffold = scaffolds.get(plat_key, "## Unknown Variant Scaffold")

    return f"""# Platform Native Draft Scaffold: {platform.upper()}

> [!IMPORTANT]
> **NO-PUBLICATION WARNING**: This document contains draft scaffolds and placeholder layouts. It is not publish-ready and must not be posted publicly.

## Safety & Limitation Note
- **Source Mode**: {source_mode}
- **Variant Status**: {status}
- **Missing Source References**: {missing_str}
- **Approval/Dispatch Blocked Note**: Dispatch of this variant is strictly blocked because `dispatch_allowed_now` is false.
- **Evidence Checklist**: Real-world references and human operator approval are required to unblock this scaffold.

{platform_scaffold}
"""



def materialize_variant_packet(
    article_packet_path: str | Path = DEFAULT_ARTICLE_PACKET,
    grounding_packet_path: str | Path = DEFAULT_GROUNDING_PACKET,
    seo_packet_path: str | Path = DEFAULT_SEO_PACKET
) -> dict[str, Any]:
    try:
        article_data = load_json(article_packet_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        return {
            "task_label": TASK_LABEL,
            "schema_version": SCHEMA_VERSION,
            "platform_variant_packet_id": "platform_variants_unreadable_art",
            "source_article_id": None,
            "source_research_packet_id": None,
            "source_seo_editorial_packet_id": None,
            "source_intent_id": None,
            "source_mode": "unknown",
            "source_article_status": None,
            "source_grounding_status": None,
            "source_refinement_status": None,
            "variant_status": "BLOCKED_BY_SOURCE_ARTICLE",
            "variant_stage": "platform_native_scaffold",
            "target_platforms": [],
            "variants": {},
            "variant_files": {},
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
            "platform_variant_packet_id": "platform_variants_unreadable_gnd",
            "source_article_id": article_data.get("article_id"),
            "source_research_packet_id": None,
            "source_seo_editorial_packet_id": None,
            "source_intent_id": article_data.get("source_intent_id"),
            "source_mode": article_data.get("source_mode", "unknown"),
            "source_article_status": article_data.get("article_status"),
            "source_grounding_status": None,
            "source_refinement_status": None,
            "variant_status": "BLOCKED_BY_RESEARCH_GROUNDING",
            "variant_stage": "platform_native_scaffold",
            "target_platforms": [],
            "variants": {},
            "variant_files": {},
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

    try:
        seo_data = load_json(seo_packet_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        return {
            "task_label": TASK_LABEL,
            "schema_version": SCHEMA_VERSION,
            "platform_variant_packet_id": "platform_variants_unreadable_seo",
            "source_article_id": article_data.get("article_id"),
            "source_research_packet_id": grounding_data.get("research_packet_id"),
            "source_seo_editorial_packet_id": None,
            "source_intent_id": article_data.get("source_intent_id"),
            "source_mode": article_data.get("source_mode", "unknown"),
            "source_article_status": article_data.get("article_status"),
            "source_grounding_status": grounding_data.get("grounding_status"),
            "source_refinement_status": None,
            "variant_status": "BLOCKED_BY_SEO_EDITORIAL",
            "variant_stage": "platform_native_scaffold",
            "target_platforms": [],
            "variants": {},
            "variant_files": {},
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
            "blocked_reasons": [f"seo_packet_unreadable:{exc.__class__.__name__}"],
            "next_recommended_task": "TASK_CONTENTOPS_V6_SEO_AND_EDITORIAL_REFINEMENT_LANE_V0"
        }

    article_id = article_data.get("article_id")
    research_id = grounding_data.get("research_packet_id")
    seo_id = seo_data.get("seo_editorial_packet_id")
    intent_id = article_data.get("source_intent_id")
    
    article_status = article_data.get("article_status")
    grounding_status = grounding_data.get("grounding_status")
    refinement_status = seo_data.get("refinement_status")
    
    source_mode = article_data.get("source_mode", "unknown")
    if source_mode == "unknown" or source_mode is None:
        source_mode = grounding_data.get("source_mode", "unknown")

    source_needed = grounding_data.get("source_needed", False)
    source_evidence_required = grounding_data.get("source_evidence_required", False)
    missing_source_refs = list(grounding_data.get("missing_source_refs", []))
    blocked_reasons = list(article_data.get("blocked_reasons", []))

    # Compute status
    if article_status == "BLOCKED_BY_OPERATOR_INTENT" or "article_packet_unreadable" in str(article_id):
        status = "BLOCKED_BY_SOURCE_ARTICLE"
    elif grounding_status == "BLOCKED_BY_SOURCE_ARTICLE" or "grounding_packet_unreadable" in str(research_id):
        status = "BLOCKED_BY_RESEARCH_GROUNDING"
    elif refinement_status in ["BLOCKED_BY_SOURCE_ARTICLE", "BLOCKED_BY_RESEARCH_GROUNDING"] or "seo_packet_unreadable" in str(seo_id):
        status = "BLOCKED_BY_SEO_EDITORIAL"
    elif missing_source_refs or source_needed:
        status = "VARIANT_SCAFFOLD_READY_WITH_SOURCE_GAP"
    else:
        status = "VARIANT_SCAFFOLD_READY"

    target_platforms = ["substack", "discord", "linkedin", "x", "threads", "telegram"]

    # Generate layout paths dictionary
    variant_files = {}
    for plat in target_platforms:
        suffix = "telegram_operator_preview.md" if plat == "telegram" else f"{plat}_variant.md"
        variant_files[plat] = f"docs/automation/V6_PLATFORM_NATIVE_VARIANTS/{suffix}"

    evidence_blockers = {
        "source_needed": source_needed,
        "missing_source_refs": missing_source_refs
    }

    hasher = hashlib.sha256(f"{article_id}_{research_id}_{seo_id}_{status}".encode("utf-8"))
    platform_variant_packet_id = f"platform_variants_{hasher.hexdigest()[:12]}"

    next_task = (
        "TASK_CONTENTOPS_V6_PLATFORM_NATIVE_VARIANT_GENERATOR_V0"
        if status in ["BLOCKED_BY_SOURCE_ARTICLE", "BLOCKED_BY_RESEARCH_GROUNDING", "BLOCKED_BY_SEO_EDITORIAL"]
        else "TASK_CONTENTOPS_V6_DISCORD_COMMUNITY_DROP_LANE_V0"
    )

    return {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "platform_variant_packet_id": platform_variant_packet_id,
        "source_article_id": article_id,
        "source_research_packet_id": research_id,
        "source_seo_editorial_packet_id": seo_id,
        "source_intent_id": intent_id,
        "source_mode": source_mode,
        "source_article_status": article_status,
        "source_grounding_status": grounding_status,
        "source_refinement_status": refinement_status,
        "variant_status": status,
        "variant_stage": "platform_native_scaffold",
        "target_platforms": target_platforms,
        "variants": {
            "substack": "long_form_scaffold",
            "discord": "short_form_drop_scaffold",
            "linkedin": "professional_update_scaffold",
            "x": "concise_thread_scaffold",
            "threads": "conversational_scaffold",
            "telegram": "operator_preview_scaffold"
        },
        "variant_files": variant_files,
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
    return f"""# V6 Platform Native Variant Generator

Status: `{blocked_flag}`

- No live request in this task: `true`
- No env read in this task: `true`
- No provider call in this task: `true`
- No network call in this task: `true`
- Platform native scaffolds generated: `true`
- Fake public-postable content created: `false`

The scaffolds for all 6 target platforms are mapped.
"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    next_task = packet.get("next_recommended_task")
    if packet.get("blocked_reasons"):
        goal = "Resolve operator intent, source evidence, grounding, or refinement block conditions."
    else:
        goal = "Trigger Discord community drop lane for V6 content staging."
    return f"""# Next Task Pointer

Recommended next task:

`{next_task}`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Platform Native Variant Generator")
    parser.add_argument("--article-packet", default=str(DEFAULT_ARTICLE_PACKET))
    parser.add_argument("--grounding-packet", default=str(DEFAULT_GROUNDING_PACKET))
    parser.add_argument("--seo-packet", default=str(DEFAULT_SEO_PACKET))
    parser.add_argument("--output-packet", default=str(DEFAULT_PACKET_OUTPUT))
    args = parser.parse_args(argv)
    
    packet = materialize_variant_packet(args.article_packet, args.grounding_packet, args.seo_packet)
    write_json(args.output_packet, packet)
    
    # Write the 6 variant files
    out_dir = Path(args.output_packet).parent
    for plat in packet["target_platforms"]:
        suffix = "telegram_operator_preview.md" if plat == "telegram" else f"{plat}_variant.md"
        out_file = out_dir / suffix
        out_file.write_text(generate_scaffold_text(plat, packet), encoding="utf-8")
        
    # Write report and pointer
    out_path = Path(args.output_packet)
    (out_path.parent / "implementation_report.md").write_text(implementation_report(packet), encoding="utf-8")
    (out_path.parent / "next_task_pointer.md").write_text(next_task_pointer(packet), encoding="utf-8")
    
    print(json.dumps({
        "platform_variant_packet_id": packet["platform_variant_packet_id"],
        "variant_status": packet["variant_status"],
        "blocked_reasons": packet["blocked_reasons"]
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
