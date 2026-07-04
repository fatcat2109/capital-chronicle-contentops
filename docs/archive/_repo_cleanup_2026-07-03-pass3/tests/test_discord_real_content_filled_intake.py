import json
from pathlib import Path

from live_contentops import discord_real_content_filled_intake as filled


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def template_path(tmp_path: Path):
    return write_json(tmp_path / "template.json", {"template_only": True, "target_name": "announcements", "content_type": "announcement"})


def source(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def materialize(tmp_path, source_path=None, target="announcements", content_type="announcement"):
    return filled.materialize_filled_intake(template_path(tmp_path), source_artifact=source_path, target=target, content_type=content_type)


def test_no_source_artifact_produces_blocked_awaiting_operator_content(tmp_path):
    packet = filled.materialize_filled_intake(template_path(tmp_path))
    assert packet["filled_intake_status"] == "BLOCKED_AWAITING_OPERATOR_CONTENT"


def test_blocked_packet_has_null_content_fields_and_template_only_true(tmp_path):
    packet = filled.materialize_filled_intake(template_path(tmp_path))
    assert packet["intake_id"] is None
    assert packet["content_title"] is None
    assert packet["content_body"] is None
    assert packet["content_summary"] is None
    assert packet["template_only"] is True


def test_blocked_packet_not_approved_not_dispatchable_not_public_postable(tmp_path):
    packet = filled.materialize_filled_intake(template_path(tmp_path))
    assert packet["not_approved"] is True
    assert packet["not_dispatchable"] is True
    assert packet["not_public_postable"] is True


def test_valid_real_source_artifact_ready_but_not_public_postable(tmp_path):
    src = source(tmp_path / "operator_content" / "capital_chronicle_update.md", "# Capital Chronicle Update\n\nOperator reviewed publication workflow note.")
    packet = materialize(tmp_path, src)
    assert packet["filled_intake_status"] == "READY_FOR_INTAKE_APPROVAL"
    assert packet["template_only"] is False
    assert packet["not_approved"] is True
    assert packet["not_dispatchable"] is True
    assert packet["not_public_postable"] is True
    assert packet["validation"]["real_content_present"] is True


def test_empty_source_artifact_fails_validation(tmp_path):
    src = source(tmp_path / "operator_content" / "empty.md", "")
    packet = materialize(tmp_path, src)
    assert packet["filled_intake_status"] == "FAIL_VALIDATION"
    assert "source_artifact_empty" in packet["validation_errors"]


def test_unknown_target_fails_validation(tmp_path):
    src = source(tmp_path / "operator_content" / "update.md", "Capital Chronicle operator update.")
    packet = materialize(tmp_path, src, target="unknown", content_type="announcement")
    assert packet["filled_intake_status"] == "FAIL_VALIDATION"
    assert "unknown_target" in packet["validation_errors"]


def test_content_type_mismatch_fails_validation(tmp_path):
    src = source(tmp_path / "operator_content" / "update.md", "Capital Chronicle operator update.")
    packet = materialize(tmp_path, src, target="announcements", content_type="product_update")
    assert packet["filled_intake_status"] == "FAIL_VALIDATION"
    assert "target_content_type_mismatch" in packet["validation_errors"]


def test_dry_run_payload_and_sample_paths_are_rejected(tmp_path):
    for name in ["discord_dryrun_payload.md", "sample_payload.md", "template_message.md", "prior_test_message.md"]:
        src = source(tmp_path / name, "Capital Chronicle operator update.")
        packet = materialize(tmp_path, src)
        assert packet["filled_intake_status"] == "FAIL_VALIDATION"
        assert "dryrun_sample_template_or_test_source_rejected" in packet["validation_errors"]


def test_operator_instructions_mention_no_secrets_webhooks():
    instructions = filled.operator_fill_instructions().lower()
    assert "secrets" in instructions
    assert "webhook" in instructions


def test_operator_instructions_mention_no_buy_sell_hold_or_position_sizing():
    instructions = filled.operator_fill_instructions().lower()
    assert "buy/sell/hold" in instructions
    assert "position sizing" in instructions


def test_packet_has_no_live_request_true(tmp_path):
    assert filled.materialize_filled_intake(template_path(tmp_path))["no_live_request_in_this_task"] is True


def test_packet_has_no_env_read_true(tmp_path):
    assert filled.materialize_filled_intake(template_path(tmp_path))["no_env_read_in_this_task"] is True


def test_module_contains_no_network_or_env_read_behavior():
    names = set(dir(filled))
    assert "urlopen" not in names
    assert "requests" not in names
    assert "post" not in names
    assert "environ" not in names
    assert "getenv" not in names


def test_blocked_packet_validation_real_content_present_false(tmp_path):
    packet = filled.materialize_filled_intake(template_path(tmp_path))
    assert packet["validation"]["real_content_present"] is False


def test_invalid_financial_signal_language_fails_validation(tmp_path):
    src = source(tmp_path / "operator_content" / "update.md", "Readers should buy and hold forever.")
    packet = materialize(tmp_path, src)
    assert packet["filled_intake_status"] == "FAIL_VALIDATION"
    assert "trading_signal_language_blocked" in packet["validation_errors"]


def test_position_sizing_language_fails_validation(tmp_path):
    src = source(tmp_path / "operator_content" / "update.md", "Allocate 10% to this idea.")
    packet = materialize(tmp_path, src)
    assert packet["filled_intake_status"] == "FAIL_VALIDATION"
    assert "position_sizing_language_blocked" in packet["validation_errors"]


def test_write_all_outputs_creates_required_docs(tmp_path):
    packet = filled.materialize_filled_intake(template_path(tmp_path))
    out = tmp_path / "out" / "filled_intake_packet.json"
    filled.write_all_outputs(out, packet)
    assert out.exists()
    assert (out.parent / "filled_intake_schema.json").exists()
    assert (out.parent / "operator_fill_instructions.md").exists()
    assert (out.parent / "implementation_report.md").exists()
    assert (out.parent / "next_task_pointer.md").exists()


def test_packet_contains_no_webhook_url(tmp_path):
    text = json.dumps(filled.materialize_filled_intake(template_path(tmp_path)))
    forbidden = "https://" + "discord.com" + "/api/" + "webhooks"
    assert forbidden not in text


def test_cli_main_generates_blocked_packet(tmp_path):
    out = tmp_path / "out" / "filled_intake_packet.json"
    rc = filled.main(["--template", str(template_path(tmp_path)), "--output", str(out)])
    assert rc == 0
    packet = json.loads(out.read_text(encoding="utf-8"))
    assert packet["filled_intake_status"] == "BLOCKED_AWAITING_OPERATOR_CONTENT"
