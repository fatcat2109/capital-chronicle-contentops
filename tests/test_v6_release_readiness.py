import json
import pytest
from live_contentops.v6_release_readiness import REQUIRED_RED_TEAM_CASES, REQUIRED_RENEWAL_STEPS, build_final_release_packet, has_secret_like_key, stable_hash, validate_final_release_packet, write_final_release_evidence

def test_final_release_packet_covers_north_star_and_red_team_cases():
    packet = build_final_release_packet()
    assert packet["final_verdict"] == "PASS_FINAL_LOCAL_RELEASE_REVIEW"
    assert set(packet["north_star_loop"]) == set(REQUIRED_RENEWAL_STEPS)
    assert {c["case_id"] for c in packet["red_team_cases"]} == set(REQUIRED_RED_TEAM_CASES)
    assert all(c["result"] == "PASS_BLOCKED" for c in packet["red_team_cases"])
    validate_final_release_packet(packet)

def test_final_release_safety_flags_and_manual_fallback_are_locked():
    packet = build_final_release_packet()
    assert packet["manual_remains_fallback"] is True
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert all(value is False for value in packet["safety_flags"].values())

def test_secret_like_extra_input_blocks_packet():
    packet = build_final_release_packet({"api_key": "redacted"})
    assert "secret_like_key_blocked" in packet["blockers"]
    with pytest.raises(ValueError):
        validate_final_release_packet(packet)

def test_secret_like_key_detector_allows_named_capability_matrix_only():
    assert has_secret_like_key({"credential_capability_matrix": "disabled"}) is False
    assert has_secret_like_key({"nested": {"session_cookie": "redacted"}}) is True

def test_packet_hash_is_stable():
    first = build_final_release_packet()
    second = build_final_release_packet()
    assert first["packet_hash"] == second["packet_hash"]
    assert first["packet_hash"] == stable_hash({k: v for k, v in first.items() if k != "packet_hash"})

def test_metrics_do_not_use_api_or_scrape():
    packet = build_final_release_packet()
    assert {row["metric_id"] for row in packet["metrics_matrix"]} >= {"manual_metrics_entry", "discord_feedback_summary", "substack_url_record", "telegram_dispatch_result", "campaign_performance_notes"}
    assert all(row["api_or_scrape_used"] is False for row in packet["metrics_matrix"])

def test_write_final_release_evidence(tmp_path, monkeypatch):
    import live_contentops.v6_release_readiness as mod
    monkeypatch.setattr(mod, "OUT_DIR", tmp_path)
    monkeypatch.setattr(mod, "FINAL_PACKET_PATH", tmp_path / "final_release_evidence_packet.json")
    monkeypatch.setattr(mod, "RED_TEAM_REPORT_PATH", tmp_path / "red_team_report.md")
    monkeypatch.setattr(mod, "BROWSER_QA_REPORT_PATH", tmp_path / "browser_qa_report.md")
    monkeypatch.setattr(mod, "ACCEPTANCE_RECORD_PATH", tmp_path / "final_acceptance_record.md")
    packet = write_final_release_evidence()
    assert json.loads((tmp_path / "final_release_evidence_packet.json").read_text())["packet_id"] == packet["packet_id"]
    assert packet["write_summary"]["changed_count"] == 4
    assert "V6 Final Red-Team Report" in (tmp_path / "red_team_report.md").read_text()
    assert "Browser/CDP QA was intentionally not run" in (tmp_path / "browser_qa_report.md").read_text()
    assert "V6 Final Acceptance Record" in (tmp_path / "final_acceptance_record.md").read_text()


def test_write_final_release_evidence_is_idempotent(tmp_path, monkeypatch):
    import live_contentops.v6_release_readiness as mod
    monkeypatch.setattr(mod, "OUT_DIR", tmp_path)
    monkeypatch.setattr(mod, "FINAL_PACKET_PATH", tmp_path / "final_release_evidence_packet.json")
    monkeypatch.setattr(mod, "RED_TEAM_REPORT_PATH", tmp_path / "red_team_report.md")
    monkeypatch.setattr(mod, "BROWSER_QA_REPORT_PATH", tmp_path / "browser_qa_report.md")
    monkeypatch.setattr(mod, "ACCEPTANCE_RECORD_PATH", tmp_path / "final_acceptance_record.md")

    first = write_final_release_evidence()
    before = {path.name: path.read_text(encoding="utf-8") for path in tmp_path.iterdir()}
    second = write_final_release_evidence()
    after = {path.name: path.read_text(encoding="utf-8") for path in tmp_path.iterdir()}

    assert first["packet_id"] == second["packet_id"]
    assert first["packet_hash"] == second["packet_hash"]
    assert before == after
    assert second["write_summary"]["changed_count"] == 0
    assert all(item["changed"] is False for item in second["write_summary"]["files"])
