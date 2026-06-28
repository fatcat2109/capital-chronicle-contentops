from live_contentops import redacted_operator_status_v6 as redacted

def test_redacted_status_properties():
    contract = {
        "variant_pack": {
            "substack_canonical": {},
            "discord_drop": {}
        },
        "draft_inspector": {
            "draft_inspector_status": "BLOCKED_REVIEW_ONLY_ISSUES_FOUND",
            "blockers": ["source_verification_required"]
        }
    }
    status = redacted.generate_redacted_status(contract)
    assert status["per_platform_payload_count"] == 2
    assert "substack_canonical" in status["platform_families"]
    assert "source_verification_required" in status["blockers"]
    assert status["publication_allowed"] is False
    assert status["dispatch_allowed_now"] is False
    assert status["redaction_policy"] == "NO_SECRET_VALUES_NO_IDS_NO_URLS"
