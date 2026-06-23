from pathlib import Path

from live_contentops.credential_hydration_gate import build_credential_inventory, credential_inventory_packet


def test_inventory_presence_only_no_raw_values(tmp_path: Path):
    (tmp_path / ".env").write_text("TELEGRAM_BOT_TOKEN=123456:SECRETSECRETSECRETSECRET\nX_API_KEY=abc123secret\n", encoding="utf-8")
    packet = credential_inventory_packet(tmp_path)
    text = str(packet)
    assert "SECRETSECRET" not in text
    assert "abc123secret" not in text
    rows = packet["rows"]
    assert any(row["env_key_name"] == "TELEGRAM_BOT_TOKEN" and row["env_presence_verified_redacted"] == "present_redacted" for row in rows)


def test_missing_credentials_block_but_registry_builds(tmp_path: Path):
    rows = build_credential_inventory(tmp_path)
    assert rows
    assert all(row.status == "missing_blocked" for row in rows)
    assert all("credential_env_key_missing" in row.blocked_reasons for row in rows)
