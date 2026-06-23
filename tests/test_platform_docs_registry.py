from live_contentops.platform_docs_registry import build_platform_docs_registry, docs_block_live_write

REQUIRED = {
    "telegram_remote_operator", "telegram_channel_destination", "x_profile",
    "linkedin_member_profile", "linkedin_organization_page", "substack_newsletter",
    "threads_profile", "instagram_professional_account", "facebook_page",
    "tiktok_account", "youtube_channel",
}


def test_registry_has_required_platform_rows_and_fields():
    rows = build_platform_docs_registry()
    ids = {row.platform_id for row in rows}
    assert ids == REQUIRED
    for row in rows:
        assert row.docs_snapshot_id
        assert row.docs_checked_at
        assert row.docs_source_type
        assert row.official_docs_url
        assert row.docs_status in {"official_docs_checked", "docs_unverified"}
        assert row.live_write_eligible is False
        assert docs_block_live_write(row.platform_id) is True


def test_x_has_paid_budget_classification_and_substack_manual_lab():
    by_id = {row.platform_id: row for row in build_platform_docs_registry()}
    assert "budget" in by_id["x_profile"].paid_plan_notes.lower()
    assert by_id["substack_newsletter"].manual_publish_supported is True
    assert by_id["substack_newsletter"].browser_assisted_supported is True
    assert by_id["substack_newsletter"].docs_status == "docs_unverified"
