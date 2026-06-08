"""Deterministic local editorial selection packet and variant comparison."""

import uuid

def generate_selection_packet(variants: list, source_id: str = None) -> dict:
    """Generates an operator-facing selection packet from a list of preview variants.
    
    Expects variants generated from editorial_preview.generate_preview.
    """
    if not source_id:
        source_id = "draft_" + str(uuid.uuid4())[:8]
        
    comparison_items = []
    
    for variant in variants:
        # Determine strengths and weaknesses based on score summary
        strengths = []
        weaknesses = []
        safety_notes = []
        
        score = variant.get("score_summary", {})
        
        if score.get("hook_strength", 0) >= 10:
            strengths.append("strong_hook")
        if score.get("platform_fit", 0) >= 10:
            strengths.append("platform_native")
        if score.get("specificity", 0) >= 10:
            strengths.append("highly_specific")
            
        if score.get("limitation_visibility", 0) < 5:
            weaknesses.append("poor_limitation_visibility")
        if score.get("source_discipline", 10) < 5:
            weaknesses.append("poor_source_discipline")
        if score.get("repetition_risk", 0) >= 10:
            weaknesses.append("high_repetition_risk")
            
        if score.get("safety_risk", 0) >= 10:
            safety_notes.append("contains_blocked_claims")
            
        limitation_status = "PRESERVED" if variant.get("limitations_preserved") else "MISSING"
        source_reference_status = "PRESERVED" if variant.get("source_references_preserved") else "MISSING"
        
        item = {
            "preview_id": variant.get("preview_id"),
            "platform": variant.get("platform"),
            "audience_mode": variant.get("audience_mode"),
            "style_mode": variant.get("style_mode"),
            "hook_type": variant.get("hook_type"),
            "score_summary": score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "safety_notes": safety_notes,
            "limitation_status": limitation_status,
            "source_reference_status": source_reference_status,
            "not_public_postable_reason": variant.get("not_public_postable_reason"),
            "operator_decision_placeholder": "PENDING_MANUAL_REVIEW"
        }
        comparison_items.append(item)
        
    # Sort variants to recommend review order (advisory only)
    # E.g., fewest weaknesses and highest platform fit first
    def sort_key(item):
        fit = item.get("score_summary", {}).get("platform_fit", 0)
        return (len(item.get("weaknesses", [])), -fit)
        
    recommended_review_order = [item["preview_id"] for item in sorted(comparison_items, key=sort_key)]
    
    # Global checks
    all_not_postable = all(item.get("not_public_postable_reason") for item in comparison_items)
    global_not_postable_reason = "All variants contain synthetic/demo/fixture content or safety blockers." if all_not_postable else None
    
    packet = {
        "packet_id": f"sel_{uuid.uuid4().hex[:8]}",
        "source_fixture_id": source_id,
        "generated_at_local": "DETERMINISTIC_TIMESTAMP",
        "variants_compared": len(variants),
        "comparison_items": comparison_items,
        "recommended_review_order": recommended_review_order,
        "manual_selection_required": True,
        "auto_selected": False,
        "approval_granted": False,
        "publish_ready": False, # Always false for fixture/demo/synthetic
        "no_public_post_reason": global_not_postable_reason,
        "warnings": ["Manual selection is required. Auto-selection is disabled."],
        "blockers": ["Live actions are disabled. Publishing is blocked."],
        "advisory_only": True,
        "guardrail_status": "NOT_PUBLIC_POSTABLE" if all_not_postable else "PENDING_OPERATOR",
        "manual_selection_placeholder": {
            "selected_preview_id": None,
            "selected_by_operator": False,
            "operator_notes": "",
            "selection_status": "PENDING_MANUAL_SELECTION"
        }
    }
    
    return packet
