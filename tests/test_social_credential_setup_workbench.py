from pathlib import Path
from live_contentops import social_credential_setup_workbench as wb


def test_matrix_contains_required_keys():
    keys = set(wb.approved_key_names())
    required = ["TELEGRAM_BOT_TOKEN","TELEGRAM_CHANNEL_ID","TELEGRAM_OPERATOR_CHAT_ID","X_CLIENT_ID","X_CLIENT_SECRET","X_ACCESS_TOKEN","X_REFRESH_TOKEN","X_USER_ID","X_ACCESS_TIER_CLASS","LINKEDIN_CLIENT_ID","LINKEDIN_CLIENT_SECRET","LINKEDIN_ACCESS_TOKEN","LINKEDIN_MEMBER_URN","LINKEDIN_ORGANIZATION_URN","META_APP_ID","META_APP_SECRET","META_ACCESS_TOKEN","FACEBOOK_PAGE_ID","FACEBOOK_PAGE_ACCESS_TOKEN","INSTAGRAM_BUSINESS_ACCOUNT_ID","THREADS_USER_ID","TIKTOK_CLIENT_KEY","TIKTOK_CLIENT_SECRET","TIKTOK_ACCESS_TOKEN","TIKTOK_REFRESH_TOKEN","TIKTOK_OPEN_ID","YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET","YOUTUBE_REFRESH_TOKEN","YOUTUBE_CHANNEL_ID","YOUTUBE_CLIENT_SECRETS_JSON_PATH","SUBSTACK_PUBLICATION_URL","SUBSTACK_EMAIL_OR_ACCOUNT_HINT"]
    for key in required:
        assert key in keys


def test_inventory_local_env_redacted(tmp_path: Path):
    (tmp_path / ".env.local").write_text("TELEGRAM_CHANNEL_ID=-1001234567890\nX_CLIENT_ID=my-client-id\n", encoding="utf-8")
    report = wb.build_inventory(tmp_path)
    rows = {row["key_name"]: row for row in report["rows"]}
    assert rows["TELEGRAM_CHANNEL_ID"]["present"] is True
    assert rows["TELEGRAM_CHANNEL_ID"]["shape_class"] == "present_redacted_identifier_like"
    assert rows["X_CLIENT_ID"]["present"] is True
    assert rows["X_CLIENT_ID"]["live_ready"] is False
    assert all(row["live_ready"] is False for row in report["rows"])


def test_process_env_skipped_without_flag(tmp_path: Path):
    report = wb.build_inventory(tmp_path, include_process_env=False, env={"X_CLIENT_ID": "from-process"})
    row = next(row for row in report["rows"] if row["key_name"] == "X_CLIENT_ID")
    assert row["present"] is False
    report2 = wb.build_inventory(tmp_path, include_process_env=True, env={"X_CLIENT_ID": "from-process"})
    row2 = next(row for row in report2["rows"] if row["key_name"] == "X_CLIENT_ID")
    assert row2["present"] is True
    assert report2["process_env_checked"] is True


def test_oauth_callbacks_are_scaffold_only():
    report = wb.build_inventory(Path("."))
    assert report["oauth_callback_scaffold_only"] is True
    assert report["oauth_callbacks"]["x"] == "http://127.0.0.1:8765/oauth/x/callback"
