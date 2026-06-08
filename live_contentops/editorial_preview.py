"""Deterministic local editorial variant preview generator."""

import uuid
from . import editorial_quality

STYLE_MODES = [
    "professional",
    "concise",
    "educational",
    "build_in_public",
    "technical_methodology",
    "beginner_friendly"
]

def generate_preview(payload: dict) -> list:
    """Generates preview variants deterministically from local fixture/draft.
    
    Expects payload:
    {
        "source_fixture_id": "...",
        "text": "...",
        "platforms": ["x", "linkedin"],
        "audience_modes": ["macro_professional"],
        "style_modes": ["concise"],
        "is_synthetic_demo": True
    }
    """
    source_id = payload.get("source_fixture_id", "draft_" + str(uuid.uuid4())[:8])
    base_text = payload.get("text", "")
    platforms = payload.get("platforms", ["linkedin"])
    audience_modes = payload.get("audience_modes", ["general_finance_reader"])
    style_modes = payload.get("style_modes", ["professional"])
    is_synthetic = payload.get("is_synthetic_demo", True)
    
    variants = []
    
    for platform in platforms:
        for audience in audience_modes:
            for style in style_modes:
                # Basic deterministic transformations for simulation
                body = base_text
                
                if style == "concise" and len(body) > 100:
                    # Keep the start and just add the caveat/source if they exist
                    parts = body.split("\n\n")
                    if len(parts) > 1:
                        body = parts[0] + "\n\n" + parts[-1]
                    else:
                        body = body[:97] + "..."
                elif style == "technical_methodology":
                    body = "Methodology Note:\n" + body
                    
                if platform == "linkedin":
                    body = body.replace(". ", ".\n\n")
                elif platform == "x":
                    body = body.replace("\n\n", " ")
                    
                # Ensure limitation preservation check
                limitations_preserved = any(k in body.lower() for k in editorial_quality.LIMITATION_KEYWORDS)
                
                # Ensure source preservation check
                source_references_preserved = "http" in body or "source:" in body.lower()
                
                qa_payload = {
                    "text": body,
                    "platform": platform,
                    "audience": audience,
                    "is_synthetic_demo": is_synthetic
                }
                
                qa_result = editorial_quality.evaluate_quality(qa_payload)
                
                # Determine warnings & blockers
                warnings = []
                blockers = qa_result.get("blocked_claims_detected", [])
                
                if not limitations_preserved:
                    warnings.append("Missing limitation visibility in this variant.")
                    
                if not source_references_preserved:
                    warnings.append("Source references may be missing.")
                    
                if qa_result.get("score_summary", {}).get("safety_risk", 0) >= 10:
                    blockers.append("High safety risk score.")
                    
                # ALL fixture/demo/synthetic must have a not_public_postable_reason
                not_postable_reason = qa_result.get("not_public_postable_reason")
                if not not_postable_reason and is_synthetic:
                    not_postable_reason = "Synthetic/demo preview generation."

                guardrail_status = "BLOCKED" if blockers else ("WARN" if warnings else "PASS")
                # Force BLOCKED if not postable
                if not_postable_reason:
                    guardrail_status = "NOT_PUBLIC_POSTABLE"

                variant = {
                    "preview_id": f"prev_{uuid.uuid4().hex[:8]}",
                    "source_fixture_id": source_id,
                    "platform": platform,
                    "audience_mode": audience,
                    "style_mode": style,
                    "body": f"[SIMULATED PREVIEW]\n{body}",
                    "hook_type": "standard", # default deterministic flag
                    "limitations_preserved": limitations_preserved,
                    "source_references_preserved": source_references_preserved,
                    "score_summary": qa_result.get("score_summary"),
                    "warnings": warnings,
                    "blockers": blockers,
                    "advisory_only": True,
                    "not_public_postable_reason": not_postable_reason,
                    "guardrail_status": guardrail_status
                }
                variants.append(variant)
                
    return variants
