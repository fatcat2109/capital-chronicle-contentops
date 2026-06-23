from live_contentops.destination_binding_registry import build_destination_bindings


def test_bindings_are_separate_and_live_write_blocked():
    rows = build_destination_bindings()
    ids = {row.destination_binding_id for row in rows}
    assert "telegram_operator_inbox_default" in ids
    assert "telegram_channel_default" in ids
    assert "linkedin_member_default" in ids
    assert "linkedin_org_default" in ids
    assert "facebook_page_default" in ids
    assert "instagram_professional_default" in ids
    assert "threads_profile_default" in ids
    assert all(row.live_write_allowed is False for row in rows)
    assert all("batch_a_live_write_forbidden" in row.blocked_reasons for row in rows)


def test_destination_mismatch_blocks_live_write():
    row = build_destination_bindings()[0]
    assert row.wrong_account_detection_status == "not_checked_blocked"
    assert row.permission_status == "unverified_blocked"
