import json
from pathlib import Path

from live_contentops import discord_real_content_source_artifact as source_artifact


def source(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def materialize(tmp_path, source_path=None):
    inbox = tmp_path / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    return source_artifact.materialize_source_artifact(source_path, inbox=inbox)


def test_no_source_artifact_produces_blocked_awaiting_operator_artifact(tmp_path):
    packet = materialize(tmp_path)
    assert packet["source_artifact_status"] == "BLOCKED_AWAITING_OPERATOR_ARTIFACT"


def test_blocked_packet_has_null_source_and_content_fields(tmp_path):
    packet = materialize(tmp_path)
    assert packet["source_artifact_path"] is None
    assert packet["source_artifact_sha256"] is None
    assert packet["content_title_detected"] is None
    assert packet["recommended_target_name"] is None
    assert packet["recommended_content_type"] is None


def test_valid_markdown_source_artifact_ready_but_not_public_postable(tmp_path):
    src = source(tmp_path / "inbox" / "capital_chronicle_update.md", "# Capital Chronicle Update\n\nToday we launched a new editorial workflow.")
    packet = materialize(tmp_path, src)
    assert packet["source_artifact_status"] == "READY_FOR_FILLED_INTAKE"
    assert packet["not_approved"] is True
    assert packet["not_dispatchable"] is True
    assert packet["not_public_postable"] is True
    assert packet["recommended_target_name"] == "announcements"
    assert packet["recommended_content_type"] == "announcement"


def test_inbox_readme_is_ignored_during_auto_discovery(tmp_path):
    source(tmp_path / "inbox" / "README.md", "helper doc")
    source(tmp_path / "inbox" / "capital_chronicle_update.md", "# Capital Chronicle Update\n\nToday we launched a new editorial workflow.")
    packet = materialize(tmp_path)
    assert packet["source_artifact_status"] == "READY_FOR_FILLED_INTAKE"
    assert packet["source_artifact_path"].endswith("capital_chronicle_update.md")


def test_placeholder_filler_text_fails_validation(tmp_path):
    src = source(
        tmp_path / "inbox" / "capital_chronicle_real_announcement_001.md",
        "# Capital Chronicle — Product Update\n\n[Viết nội dung thật ở đây]\n\nSource evidence:\n- [đường dẫn tới artifact/source nếu có]\n\nOperator notes:\n- Target candidate: announcements\n- Content type candidate: announcement",
    )
    packet = materialize(tmp_path, src)
    assert packet["source_artifact_status"] == "FAIL_VALIDATION"
    assert "placeholder_source_rejected" in packet["validation_errors"]
    assert packet["validation"]["no_placeholder_fillers"] is False


def test_empty_artifact_fails_validation(tmp_path):
    src = source(tmp_path / "inbox" / "empty.md", "")
    packet = materialize(tmp_path, src)
    assert packet["source_artifact_status"] == "FAIL_VALIDATION"
    assert "source_artifact_empty" in packet["validation_errors"]


def test_template_path_fails_validation(tmp_path):
    src = source(tmp_path / "inbox" / "operator_template.md", "Capital Chronicle operator note")
    packet = materialize(tmp_path, src)
    assert packet["source_artifact_status"] == "FAIL_VALIDATION"
    assert "source_path_disallowed" in packet["validation_errors"]


def test_dryrun_sample_test_paths_fail_validation(tmp_path):
    names = ["dryrun.md", "sample.md", "test_message.md", "fixture.json"]
    for name in names:
        src = source(tmp_path / "inbox" / name, "Capital Chronicle operator note")
        packet = materialize(tmp_path, src)
        assert packet["source_artifact_status"] == "FAIL_VALIDATION"
        assert "source_path_disallowed" in packet["validation_errors"]


def test_webhook_like_url_or_secret_like_text_fails_validation(tmp_path):
    src = source(tmp_path / "inbox" / "real.md", "keep token secret and never share https://discord.com/api/webhooks/123/abc")
    packet = materialize(tmp_path, src)
    assert packet["source_artifact_status"] == "FAIL_VALIDATION"
    assert "webhook_or_secret_like_text_blocked" in packet["validation_errors"]


def test_buy_sell_hold_trading_signal_language_fails_validation(tmp_path):
    src = source(tmp_path / "inbox" / "real.md", "Readers should buy and hold this asset.")
    packet = materialize(tmp_path, src)
    assert packet["source_artifact_status"] == "FAIL_VALIDATION"
    assert "trading_signal_language_blocked" in packet["validation_errors"]


def test_position_sizing_language_fails_validation(tmp_path):
    src = source(tmp_path / "inbox" / "real.md", "Allocate 10% to this idea.")
    packet = materialize(tmp_path, src)
    assert packet["source_artifact_status"] == "FAIL_VALIDATION"
    assert "position_sizing_language_blocked" in packet["validation_errors"]


def test_guaranteed_prediction_language_fails_validation(tmp_path):
    src = source(tmp_path / "inbox" / "real.md", "This launch will definitely succeed.")
    packet = materialize(tmp_path, src)
    assert packet["source_artifact_status"] == "FAIL_VALIDATION"
    assert "guaranteed_prediction_language_blocked" in packet["validation_errors"]


def test_numeric_claims_set_source_evidence_required_true(tmp_path):
    src = source(tmp_path / "inbox" / "real.md", "# Weekly Update\n\nWe published 3 research notes this week.")
    packet = materialize(tmp_path, src)
    assert packet["source_artifact_status"] == "READY_FOR_FILLED_INTAKE"
    assert packet["numeric_claims_detected"] is True
    assert packet["source_evidence_required"] is True
    assert packet["validation"]["numeric_claims_require_evidence"] is True


def test_operator_instructions_mention_no_secrets_webhooks():
    text = source_artifact.operator_source_artifact_instructions().lower()
    assert "secrets" in text
    assert "webhook" in text


def test_operator_instructions_mention_no_buy_sell_hold_or_position_sizing():
    text = source_artifact.operator_source_artifact_instructions().lower()
    assert "buy/sell/hold" in text
    assert "position sizing" in text


def test_packet_has_no_live_request_in_this_task_true(tmp_path):
    assert materialize(tmp_path)["no_live_request_in_this_task"] is True


def test_packet_has_no_env_read_in_this_task_true(tmp_path):
    assert materialize(tmp_path)["no_env_read_in_this_task"] is True


def test_module_contains_no_network_or_env_read_behavior():
    names = set(dir(source_artifact))
    assert "urlopen" not in names
    assert "requests" not in names
    assert "post" not in names
    assert "environ" not in names
    assert "getenv" not in names


def test_write_all_outputs_creates_required_docs(tmp_path):
    packet = materialize(tmp_path)
    out = tmp_path / "out" / "source_artifact_packet.json"
    source_artifact.write_all_outputs(out, packet)
    assert out.exists()
    assert (out.parent / "source_artifact_schema.json").exists()
    assert (out.parent / "operator_source_artifact_instructions.md").exists()
    assert (out.parent / "implementation_report.md").exists()
    assert (out.parent / "next_task_pointer.md").exists()
    assert (out.parent / "inbox" / "README.md").exists()


def test_packet_contains_no_webhook_url(tmp_path):
    text = json.dumps(materialize(tmp_path))
    forbidden = "https://" + "discord.com" + "/api/" + "webhooks"
    assert forbidden not in text


def test_cli_main_generates_blocked_packet(tmp_path):
    out = tmp_path / "out" / "source_artifact_packet.json"
    rc = source_artifact.main(["--output", str(out), "--inbox", str(tmp_path / "inbox")])
    assert rc == 0
    packet = json.loads(out.read_text(encoding="utf-8"))
    assert packet["source_artifact_status"] == "BLOCKED_AWAITING_OPERATOR_ARTIFACT"
