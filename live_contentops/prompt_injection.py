import uuid

def generate_prompt_packet(req: dict) -> dict:
    """Generates a deterministic local prompt packet for LLM consumption."""
    
    # Cost policy injection
    cost_policy_notes = [
        "One search context per content packet, not per variant",
        "Reuse cached/freshness-window research",
        "Free/low-cost search before paid tools",
        "Paid/vendor observations are manual inputs until ROI is proven",
        "No live search in this task"
    ]
    
    # Grounded search authority boundary
    authority_boundary = [
        "Grounded search is research context only",
        "LLM output is not authority",
        "Citations are required for sourced claims",
        "Missing data stays missing",
        "Synthetic fixtures are not public evidence",
        "No approval/publishing/trading authority is granted"
    ]
    
    # Build prompt sections
    system_boundary_section = "System operates within safe, constrained parameters. " + " ".join(authority_boundary)
    grounded_context_section = "Context provided from local fixtures/search. "
    source_and_citation_section = "Sources must be cited. "
    freshness_and_limitations_section = "Respect freshness and limitations. "
    editorial_style_section = "Follow style guides. "
    safety_guardrail_section = "No blocked claims. "
    output_contract_section = "Output must be standard format. "
    no_public_post_section = "DO NOT PUBLICLY POST. "
    
    is_synthetic = req.get("is_synthetic", True)
    
    return {
        "prompt_packet_id": f"prompt_{uuid.uuid4().hex[:8]}",
        "task_intent": req.get("task_intent", "Unknown"),
        "content_type": req.get("content_type", "post"),
        "target_platforms": req.get("target_platforms", []),
        "audience_modes": req.get("audience_modes", []),
        "style_modes": req.get("style_modes", []),
        "grounded_research_context_id": req.get("grounded_research_context_id"),
        "source_context": req.get("source_context", {}),
        "citation_requirements": req.get("citation_requirements", "Required for all claims"),
        "freshness_requirements": req.get("freshness_requirements", "24h"),
        "allowed_claims": req.get("allowed_claims", []),
        "blocked_claims": req.get("blocked_claims", ["invent facts", "invent prices", "invent forecasts", "invent metrics", "invent URLs", "invent source IDs"]),
        "limitations_to_preserve": req.get("limitations_to_preserve", []),
        "source_references_to_preserve": req.get("source_references_to_preserve", []),
        "seo_hashtag_metadata_constraints": req.get("seo_hashtag_metadata_constraints", []),
        "cost_policy_notes": cost_policy_notes,
        "no_public_post_reason": "Synthetic prompt fixture" if is_synthetic else None,
        "advisory_only": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "prompt_sections": {
            "system_boundary_section": system_boundary_section,
            "grounded_context_section": grounded_context_section,
            "source_and_citation_section": source_and_citation_section,
            "freshness_and_limitations_section": freshness_and_limitations_section,
            "editorial_style_section": editorial_style_section,
            "safety_guardrail_section": safety_guardrail_section,
            "output_contract_section": output_contract_section,
            "no_public_post_section": no_public_post_section
        }
    }
