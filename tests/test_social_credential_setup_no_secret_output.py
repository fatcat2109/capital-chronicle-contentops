import json
from pathlib import Path
from live_contentops import social_credential_setup_workbench as wb


def test_token_shaped_values_are_not_output(tmp_path: Path):
    secret = "123456:abcdefghijklmnopqrstuvwxyzABCDEF123456"
    access = "abcdefghijklmnopqrstuvwxyzABCDEF1234567890"
    (tmp_path / ".env.local").write_text(f"TELEGRAM_BOT_TOKEN={secret}\nX_ACCESS_TOKEN={access}\n", encoding="utf-8")
    report = wb.build_inventory(tmp_path)
    text = json.dumps(report, sort_keys=True)
    assert secret not in text
    assert access not in text
    assert "present_redacted_token_like" in text
    assert report["credential_values_printed"] is False
    assert report["token_snippets_printed"] is False
    assert report["secret_hashes_printed"] is False


def test_report_blocks_secret_marker_if_injected():
    bad = {"value": "access_token=abc"}
    try:
        wb.assert_report_safe(bad)
    except ValueError as exc:
        assert "blocked" in str(exc)
    else:
        raise AssertionError("secret marker not blocked")
