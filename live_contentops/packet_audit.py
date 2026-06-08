"""Local-only deterministic grounded packet audit (v0).

Reads an exported grounded editorial packet (from editorial_packet_export) and
produces a deterministic audit result: blockers, warnings, audit flags, missing
components, authority violations, and per-dimension status fields. Performs NO
network, provider, LLM, search, or platform calls.
"""

from . import editorial_packet_export

# Components that every exported packet must carry.
REQUIRED_COMPONENTS = [
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

# Prompt-invent phrases that must never appear as instructions to the model.
INVENT_PHRASES = [
    "invent facts",
    "invent prices",
    "invent forecasts",
    "invent metrics",
    "invent urls",
    "invent source ids",
]


def _find_missing_components(packet: dict) -> list:
    return [c for c in REQUIRED_COMPONENTS if c not in packet or packet.get(c) in (None, "")]


def _find_authority_violations(packet: dict) -> list:
    violations = []
    if packet.get("approval_granted"):
        violations.append("export_packet.approval_granted is True")
    if packet.get("publish_ready"):
        violations.append("export_packet.publish_ready is True")
    if packet.get("human_review_required") is False:
        violations.append("export_packet.human_review_required is False")
    if packet.get("provider_call_allowed"):
        violations.append("export_packet.provider_call_allowed is True")
    if packet.get("search_call_allowed"):
        violations.append("export_packet.search_call_allowed is True")
    if packet.get("platform_action_allowed"):
        violations.append("export_packet.platform_action_allowed is True")

    sel = packet.get("selection_packet", {})
    if sel.get("approval_granted") or sel.get("publish_ready"):
        violations.append("selection_packet grants approval/publish authority")
    if sel.get("auto_selected"):
        violations.append("selection_packet auto_selected a variant")

    prompt_packet = packet.get("prompt_packet", {})
    if prompt_packet.get("approval_granted") or prompt_packet.get("publish_ready"):
        violations.append("prompt_packet grants approval/publish authority")
    if prompt_packet.get("provider_call_allowed") or prompt_packet.get("search_call_allowed") \
            or prompt_packet.get("platform_action_allowed"):
        violations.append("prompt_packet allows provider/search/platform calls")
    return violations


def _check_prompt_invent(packet: dict) -> list:
    issues = []
    prompt_packet = packet.get("prompt_packet", {})
    sections_text = str(prompt_packet.get("prompt_sections", {})).lower()
    for phrase in INVENT_PHRASES:
        if f"tell the model to {phrase}" in sections_text or f"please {phrase}" in sections_text:
            issues.append(f"prompt packet instructs the model to {phrase}")
    return issues


def audit_packet(packet: dict) -> dict:
    """Deterministically audit an exported grounded editorial packet.

    Returns a structured audit result. Reuses the export module's validation
    and layers in component/authority/invent checks plus per-dimension status.
    """
    base = editorial_packet_export.validate_export_packet(packet)
    warnings = list(base.get("warnings", []))
    blockers = list(base.get("blockers", []))

    missing_components = _find_missing_components(packet)
    for component in missing_components:
        blockers.append(f"Export packet missing required component: {component}")

    authority_violations = _find_authority_violations(packet)
    blockers.extend(authority_violations)

    invent_issues = _check_prompt_invent(packet)
    blockers.extend(invent_issues)

    guardrail = packet.get("citation_guardrail_result", {})
    citation_guardrail_status = guardrail.get("status", "UNKNOWN")
    if citation_guardrail_status == "BLOCKED":
        # Surface, never hide. Block only if the packet pretends to be publishable.
        blockers.append("CITATION_GUARDRAIL_BLOCKED: export remains not public postable.")
        if packet.get("publish_ready"):
            blockers.append("Citation guardrail BLOCKED but export marked publishable.")

    research = packet.get("grounded_research_context", {})
    sources = research.get("source_items", [])
    source_reference_status = "PRESENT" if sources else "MISSING"
    if not sources:
        warnings.append("No source references present in grounded research context.")

    has_limitations = any(s.get("limitations") for s in sources)
    limitation_visibility_status = "PRESERVED" if (sources and has_limitations) else "MISSING"

    nps = packet.get("no_public_post_status", {})
    no_public_post_ok = bool(nps.get("not_public_postable"))
    no_public_post_status = "NOT_PUBLIC_POSTABLE" if no_public_post_ok else "MISSING"
    if not no_public_post_ok:
        blockers.append("no_public_post_status missing for fixture/demo/synthetic output.")

    # Synthetic/demo content must carry a not_public_postable_reason somewhere.
    if any(s.get("synthetic_fixture") for s in sources) and not research.get("not_public_postable_reason"):
        blockers.append("Synthetic research fixture lacks not_public_postable_reason.")

    qa = packet.get("editorial_qa_result", {})
    safety_risk = qa.get("score_summary", {}).get("safety_risk", 0)
    safety_status = "SAFE" if safety_risk < 10 else "BLOCKED_CLAIMS"
    if safety_status == "BLOCKED_CLAIMS":
        blockers.append("Editorial QA detected blocked/forbidden claims.")

    cost_notes = research.get("cost_budget_notes", "")
    cost_policy_status = "ENFORCED" if "Search once per content packet" in cost_notes else "UNKNOWN"

    audit_flags = list(packet.get("audit_flags", []))

    status = "BLOCKED" if blockers else ("WARNING" if warnings else "PASS")

    return {
        "audit_status": status,
        "blockers": blockers,
        "warnings": warnings,
        "audit_flags": audit_flags,
        "missing_components": missing_components,
        "authority_violations": authority_violations,
        "citation_guardrail_status": citation_guardrail_status,
        "source_reference_status": source_reference_status,
        "limitation_visibility_status": limitation_visibility_status,
        "no_public_post_status": no_public_post_status,
        "safety_status": safety_status,
        "cost_policy_status": cost_policy_status,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
    }

