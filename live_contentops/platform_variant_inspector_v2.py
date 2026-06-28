"""V6 Platform Variant Inspector.

Inspects all 9 required platform families to verify review-only draft status and verification warnings.
"""
from __future__ import annotations

from typing import Any

REQUIRED_FAMILIES = [
    "substack_canonical",
    "discord_drop",
    "telegram_operator_post",
    "x_manual_thread",
    "linkedin_manual_post",
    "threads_manual_post",
    "facebook_manual_post",
    "instagram_manual_caption",
    "manual_fallback_export"
]


def inspect_platform_variants(
    platform_variants: dict[str, Any]
) -> dict[str, Any]:
    """Inspects that all platform variants are present, review-only, and blocked from public publication."""
    blockers = []
    details = {}
    
    # Check for missing platform families
    for fam in REQUIRED_FAMILIES:
        if fam not in platform_variants:
            blockers.append(f"missing_required_platform_family:{fam}")
            
    for fam, var in platform_variants.items():
        var_blockers = []
        
        # Check review only flags
        if var.get("public_postable") is not False:
            var_blockers.append("variant_marked_public_postable")
        if var.get("dispatch_allowed_now") is not False:
            var_blockers.append("variant_marked_dispatch_allowed")
        if var.get("approval_required") is not True:
            var_blockers.append("approval_not_required_for_variant")
            
        # Check source verification required warning
        if var.get("source_verification_required") is not True:
            var_blockers.append("source_verification_warning_missing")
        if "publication_blocked_until_source_verification" not in var.get("blocked_reasons", []):
            var_blockers.append("source_verification_blocker_missing")
            
        if var_blockers:
            blockers.extend(var_blockers)
            details[fam] = sorted(list(set(var_blockers)))
            
    return {
        "is_valid": len(blockers) == 0,
        "blockers": sorted(list(set(blockers))),
        "details": details
    }
