"""Local-only deterministic grounded editorial packet export (v0).

Packages the full offline editorial pipeline into a single operator-facing
review artifact. This module performs NO network, provider, LLM, search, or
platform calls. Every export it produces is explicitly NOT PUBLIC POSTABLE.
"""

import hashlib

from . import grounded_research
from . import seo_metadata
from . import prompt_injection
from . import citation_guardrail
from . import editorial_quality
from . import editorial_preview
from . import editorial_selection

EXPORT_FORMATS_SUPPORTED = ["json_dict", "markdown_report"]

COMPONENTS_INCLUDED = [
    "grounded_research_context",
    "seo_metadata_pack",
    "prompt_packet",
    "citation_guardrail_result",
    "editorial_qa_result",
    "preview_variants",
    "selection_packet",
    "no_public_post_status",
    "operator_review",
    "audit_flags",
]

# Visible banners that must always appear in the markdown report.
MARKDOWN_BANNERS = [
    "LOCAL ONLY",
    "ADVISORY ONLY",
    "NOT PUBLIC POSTABLE",
    "NO PROVIDER CALL",
    "NO SEARCH CALL",
    "NO PLATFORM ACTION",
    "HUMAN REVIEW REQUIRED",
]


def _deterministic_id(prefix: str, seed: str) -> str:
    """Deterministic short id so exports are reproducible (no uuid/clock)."""
    h = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{h}"


def build_export_packet(req: dict) -> dict:
    """Build one complete, deterministic, local-only editorial export packet.

    Composes the existing pipeline modules from a single local fixture input.
    No live capabilities are ever exercised. The returned packet is always
    advisory-only and not public postable.
    """
    source_id = req.get("source_fixture_id") or req.get("source_draft_id") or "export_fixture"
    content_type = req.get("content_type", "post")
    target_platforms = req.get("target_platforms", [])
    audience_modes = req.get("audience_modes", [])
    style_modes = req.get("style_modes", [])

    # 1. Grounded research context (search_performed stays False).
    research_ctx = grounded_research.generate_research_context(req.get("research", {}))
    research_ctx["research_context_id"] = _deterministic_id("res", source_id)
    for idx, src in enumerate(research_ctx.get("source_items", [])):
        if not src.get("source_id") or str(src.get("source_id", "")).startswith("src_"):
            src["source_id"] = _deterministic_id(f"src{idx}", source_id)

    # 2. SEO / hashtag metadata pack.
    seo_pack = seo_metadata.generate_seo_metadata_pack(req.get("seo", {}))
    seo_pack["metadata_pack_id"] = _deterministic_id("seo", source_id)

    # 3. Grounded LLM prompt injection packet (no provider/search/platform).
    prompt_packet = prompt_injection.generate_prompt_packet(req.get("prompt", {}))
    prompt_packet["prompt_packet_id"] = _deterministic_id("prompt", source_id)

    # 4. Citation guardrail result over the prompt packet.
    guardrail = citation_guardrail.evaluate_citation_guardrail(prompt_packet)

    # 5. Editorial QA score summary.
    qa_result = editorial_quality.evaluate_quality(req.get("qa", {}))

    # 6. Editorial preview variants (simulated, never public postable).
    variants = editorial_preview.generate_preview(req.get("preview", {}))
    for idx, variant in enumerate(variants):
        variant["preview_id"] = _deterministic_id(f"prev{idx}", source_id)

    # 7. Manual selection packet (auto-selection/approval disabled).
    selection = editorial_selection.generate_selection_packet(variants, source_id)
    selection["packet_id"] = _deterministic_id("sel", source_id)

    no_public_post_status = _build_no_public_post_status(
        research_ctx, seo_pack, prompt_packet, variants, selection
    )

    operator_review = {
        "operator_selected_preview_id": None,
        "selected_by_operator": False,
        "operator_notes": "",
        "review_status": "PENDING_MANUAL_REVIEW",
        "approval_status": "NOT_APPROVED",
        "publish_status": "NOT_PUBLIC_POSTABLE",
    }

    audit_flags = _collect_audit_flags(research_ctx, seo_pack, guardrail, selection)

    packet = {
        "export_packet_id": _deterministic_id("export", source_id),
        "source_fixture_id": source_id,
        "content_type": content_type,
        "target_platforms": target_platforms,
        "audience_modes": audience_modes,
        "style_modes": style_modes,
        "grounded_research_context": research_ctx,
        "seo_metadata_pack": seo_pack,
        "prompt_packet": prompt_packet,
        "citation_guardrail_result": guardrail,
        "editorial_qa_result": qa_result,
        "preview_variants": variants,
        "selection_packet": selection,
        "no_public_post_status": no_public_post_status,
        "operator_review": operator_review,
        "audit_flags": audit_flags,
        "advisory_only": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "human_review_required": True,
        "local_only": True,
        "generated_at_local": "DETERMINISTIC_TIMESTAMP",
        "export_formats_supported": list(EXPORT_FORMATS_SUPPORTED),
        "components_included": list(COMPONENTS_INCLUDED),
    }
    return packet



def _build_no_public_post_status(research_ctx, seo_pack, prompt_packet, variants, selection) -> dict:
    reasons = []
    if research_ctx.get("not_public_postable_reason"):
        reasons.append(("grounded_research_context", research_ctx["not_public_postable_reason"]))
    if seo_pack.get("not_public_postable_reason"):
        reasons.append(("seo_metadata_pack", seo_pack["not_public_postable_reason"]))
    if prompt_packet.get("no_public_post_reason"):
        reasons.append(("prompt_packet", prompt_packet["no_public_post_reason"]))
    for variant in variants:
        if variant.get("not_public_postable_reason"):
            reasons.append((variant.get("preview_id"), variant["not_public_postable_reason"]))
    if selection.get("no_public_post_reason"):
        reasons.append(("selection_packet", selection["no_public_post_reason"]))

    return {
        "not_public_postable": True,
        "all_fixture_outputs_not_public_postable": True,
        "reasons": [{"component": c, "reason": r} for c, r in reasons],
        "publish_status": "NOT_PUBLIC_POSTABLE",
    }


def _collect_audit_flags(research_ctx, seo_pack, guardrail, selection) -> list:
    flags = []
    flags.extend(research_ctx.get("warnings", []))
    flags.extend(research_ctx.get("blockers", []))
    flags.extend(seo_pack.get("warnings", []))
    flags.extend(seo_pack.get("blockers", []))
    flags.extend(guardrail.get("warnings", []))
    flags.extend(guardrail.get("blockers", []))
    flags.extend(selection.get("warnings", []))
    flags.extend(selection.get("blockers", []))
    if guardrail.get("status") == "BLOCKED":
        flags.append("CITATION_GUARDRAIL_BLOCKED: export remains not public postable.")
    return flags


def validate_export_packet(packet: dict) -> dict:
    """Local validation. Returns deterministic warnings/blockers.

    Blocks/warns when any component tries to grant authority, when synthetic
    content lacks a no_public_post_reason, when a BLOCKED citation guardrail is
    paired with a publishable status, when sources/limitations are missing,
    when current-event claims lack grounded context, when the prompt packet
    allows live calls, or when selection auto-selects/approves a variant.
    """
    warnings = []
    blockers = []

    # 1. No component may grant approval/publish authority.
    if packet.get("approval_granted") or packet.get("publish_ready"):
        blockers.append("Export packet improperly grants approval/publish authority.")
    sel = packet.get("selection_packet", {})
    if sel.get("approval_granted") or sel.get("publish_ready"):
        blockers.append("Selection packet improperly grants approval/publish authority.")
    prompt_packet = packet.get("prompt_packet", {})
    if prompt_packet.get("approval_granted") or prompt_packet.get("publish_ready"):
        blockers.append("Prompt packet improperly grants approval/publish authority.")

    # 2. Synthetic/demo/fixture content must carry a no_public_post_reason.
    research = packet.get("grounded_research_context", {})
    if any(s.get("synthetic_fixture") for s in research.get("source_items", [])) \
            and not research.get("not_public_postable_reason"):
        blockers.append("Synthetic research fixture lacks not_public_postable_reason.")
    for variant in packet.get("preview_variants", []):
        if not variant.get("not_public_postable_reason"):
            blockers.append(
                f"Preview variant {variant.get('preview_id')} lacks no_public_post_reason."
            )

    # 3. BLOCKED citation guardrail must not be paired with a publishable export.
    guardrail = packet.get("citation_guardrail_result", {})
    if guardrail.get("status") == "BLOCKED" and packet.get("publish_ready"):
        blockers.append("Citation guardrail BLOCKED but export marked publishable.")

    # 4. Source references / limitations must remain visible.
    if not research.get("source_items"):
        warnings.append("No source references present in grounded research context.")
    has_limitations = any(s.get("limitations") for s in research.get("source_items", []))
    if research.get("source_items") and not has_limitations:
        warnings.append("Source limitations are missing from grounded research context.")

    # 5. Current-event claims must have grounded context.
    if research.get("blockers"):
        for b in research["blockers"]:
            if "current event" in b.lower():
                blockers.append("Current-event claim lacks grounded context.")

    # 6. Prompt packet must not allow provider/search/platform calls.
    if prompt_packet.get("provider_call_allowed") or prompt_packet.get("search_call_allowed") \
            or prompt_packet.get("platform_action_allowed"):
        blockers.append("Prompt packet allows provider/search/platform calls.")

    # 7. Selection packet must remain manual only.
    if sel.get("auto_selected") or not sel.get("manual_selection_required", True):
        blockers.append("Selection packet auto-selects or skips manual review.")

    status = "BLOCKED" if blockers else ("WARNING" if warnings else "PASS")
    return {"status": status, "warnings": warnings, "blockers": blockers}


def to_json_dict(packet: dict) -> dict:
    """Return the JSON-compatible export dict (already plain types)."""
    return packet



def render_markdown_report(packet: dict) -> str:
    """Render a deterministic markdown report with mandatory safety banners."""
    lines = []
    lines.append("# Grounded Editorial Packet Export (v0)")
    lines.append("")
    lines.append("> " + " | ".join(MARKDOWN_BANNERS))
    lines.append("")
    lines.append(f"- export_packet_id: {packet.get('export_packet_id')}")
    lines.append(f"- source_fixture_id: {packet.get('source_fixture_id')}")
    lines.append(f"- content_type: {packet.get('content_type')}")
    lines.append(f"- target_platforms: {', '.join(packet.get('target_platforms', [])) or 'none'}")
    lines.append(f"- audience_modes: {', '.join(packet.get('audience_modes', [])) or 'none'}")
    lines.append(f"- style_modes: {', '.join(packet.get('style_modes', [])) or 'none'}")
    lines.append("")
    lines.append("## Safety Posture")
    lines.append(f"- advisory_only: {packet.get('advisory_only')}")
    lines.append(f"- approval_granted: {packet.get('approval_granted')}")
    lines.append(f"- publish_ready: {packet.get('publish_ready')}")
    lines.append(f"- provider_call_allowed: {packet.get('provider_call_allowed')}")
    lines.append(f"- search_call_allowed: {packet.get('search_call_allowed')}")
    lines.append(f"- platform_action_allowed: {packet.get('platform_action_allowed')}")
    lines.append(f"- human_review_required: {packet.get('human_review_required')}")
    lines.append("")
    lines.append("## Citation Guardrail")
    guardrail = packet.get("citation_guardrail_result", {})
    lines.append(f"- status: {guardrail.get('status')}")
    for b in guardrail.get("blockers", []):
        lines.append(f"  - BLOCKER: {b}")
    for w in guardrail.get("warnings", []):
        lines.append(f"  - WARNING: {w}")
    lines.append("")
    lines.append("## Components Included")
    for component in packet.get("components_included", []):
        lines.append(f"- {component}")
    lines.append("")
    lines.append("## Not Public Postable Reasons")
    nps = packet.get("no_public_post_status", {})
    reasons = nps.get("reasons", [])
    if reasons:
        for r in reasons:
            lines.append(f"- [{r.get('component')}] {r.get('reason')}")
    else:
        lines.append("- (no component-level reasons recorded; export remains not public postable)")
    lines.append("")
    lines.append("## Operator Review")
    review = packet.get("operator_review", {})
    lines.append(f"- operator_selected_preview_id: {review.get('operator_selected_preview_id')}")
    lines.append(f"- selected_by_operator: {review.get('selected_by_operator')}")
    lines.append(f"- review_status: {review.get('review_status')}")
    lines.append(f"- approval_status: {review.get('approval_status')}")
    lines.append(f"- publish_status: {review.get('publish_status')}")
    lines.append("")
    lines.append("## Audit Flags")
    flags = packet.get("audit_flags", [])
    if flags:
        for f in flags:
            lines.append(f"- {f}")
    else:
        lines.append("- (none)")
    lines.append("")
    return "\n".join(lines)


def build_summary() -> dict:
    """Deterministic CLI summary describing the export capability posture."""
    return {
        "status": "deterministic local grounded editorial packet export active",
        "local_only": True,
        "advisory_only": True,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "all_fixture_outputs_not_public_postable": True,
        "export_formats_supported": list(EXPORT_FORMATS_SUPPORTED),
        "components_included": list(COMPONENTS_INCLUDED),
    }

