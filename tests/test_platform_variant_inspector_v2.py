from live_contentops import platform_variant_inspector_v2 as variant_inspector

def test_inspect_platform_variants_checks_all_required_families():
    # If any required family is missing, it should report it
    variants = {}
    report = variant_inspector.inspect_platform_variants(variants)
    assert report["is_valid"] is False
    assert any("missing_required_platform_family:substack_canonical" in b for b in report["blockers"])
    assert any("missing_required_platform_family:x_manual_thread" in b for b in report["blockers"])

def test_inspect_platform_variants_flags_improper_safety_states():
    variants = {
        "substack_canonical": {
            "public_postable": True, # invalid
            "dispatch_allowed_now": True, # invalid
            "approval_required": False, # invalid
            "source_verification_required": False, # invalid
            "blocked_reasons": [] # missing verification blocker
        }
    }
    # Pre-populate all other families to only test this family
    for fam in variant_inspector.REQUIRED_FAMILIES:
        if fam != "substack_canonical":
            variants[fam] = {
                "public_postable": False,
                "dispatch_allowed_now": False,
                "approval_required": True,
                "source_verification_required": True,
                "blocked_reasons": ["publication_blocked_until_source_verification"]
            }
            
    report = variant_inspector.inspect_platform_variants(variants)
    assert report["is_valid"] is False
    assert "variant_marked_public_postable" in report["blockers"]
    assert "variant_marked_dispatch_allowed" in report["blockers"]
    assert "approval_not_required_for_variant" in report["blockers"]
    assert "source_verification_warning_missing" in report["blockers"]
    assert "source_verification_blocker_missing" in report["blockers"]
