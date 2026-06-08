def evaluate_citation_guardrail(prompt_packet: dict) -> dict:
    """Evaluates citation guardrails on a prompt packet."""
    
    warnings = []
    blockers = []
    
    source_context = prompt_packet.get("source_context", {})
    sources = source_context.get("source_items", [])
    
    # 1. A claim requires citation but has no source item
    citation_reqs = prompt_packet.get("citation_requirements", "")
    if "Required" in citation_reqs and not sources:
        blockers.append("Claim requires citation but has no source item.")
        
    # 2. A current-event claim has no grounded context
    if source_context.get("is_current_events") and not sources:
        blockers.append("Current-event claim has no grounded context.")
        
    # 3. A source item is synthetic_fixture but treated as public authority
    # If the packet has a synthetic source but no_public_post_reason is None, that's bad.
    has_synthetic_source = any(s.get("synthetic_fixture") for s in sources)
    if has_synthetic_source and not prompt_packet.get("no_public_post_reason"):
        blockers.append("Synthetic fixture source is treated as public authority.")
        
    # 4. Freshness window is stale or missing for current-news content
    if source_context.get("is_current_events") and not prompt_packet.get("freshness_requirements"):
        blockers.append("Freshness window is missing for current-news content.")
        
    # 5. Blocked claims appear in prompt instructions
    blocked = prompt_packet.get("blocked_claims", [])
    system_text = str(prompt_packet.get("prompt_sections", {}))
    for b in blocked:
        if f"tell the model to {b}" in system_text:
            blockers.append(f"Blocked claim '{b}' appears in prompt instructions.")
            
    # 6. Prompt packet asks the LLM to invent things
    invent_keywords = ["invent facts", "invent prices", "invent forecasts", "invent metrics", "invent URLs", "invent source IDs"]
    for keyword in invent_keywords:
        if keyword in system_text:
            blockers.append(f"Prompt packet asks the LLM to {keyword}.")
            
    # Check if prompt_packet tries to grant authority
    if prompt_packet.get("approval_granted") or prompt_packet.get("publish_ready"):
        blockers.append("Prompt packet improperly grants approval/publish authority.")
        
    return {
        "status": "BLOCKED" if blockers else ("WARNING" if warnings else "PASS"),
        "warnings": warnings,
        "blockers": blockers
    }
