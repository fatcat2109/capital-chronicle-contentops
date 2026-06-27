import json
from pathlib import Path

from live_contentops import discord_real_content_filled_intake_from_source as bridge


def source(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_no_source_artifact_produces_blocked_awaiting_operator_artifact(tmp_path):
    packet = bridge.materialize_bridge(
        tmp_path / "source_artifact_packet.json",
        inbox=tmp_path / "inbox",
        template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
        filled_output=tmp_path / "filled_intake_packet.json",
    )
    assert packet["bridge_status"] == "BLOCKED_AWAITING_OPERATOR_ARTIFACT"
    assert packet["filled_intake_status"] == "BLOCKED_AWAITING_OPERATOR_CONTENT"


def test_multiple_inbox_artifacts_fail_validation(tmp_path):
    inbox = tmp_path / "inbox"
    source(inbox / "one.md", "# Update\n\nlaunch today")
    source(inbox / "two.md", "# Update\n\nlaunch today")
    packet = bridge.materialize_bridge(
        tmp_path / "source_artifact_packet.json",
        inbox=inbox,
        template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
        filled_output=tmp_path / "filled_intake_packet.json",
    )
    assert packet["bridge_status"] == "FAIL_VALIDATION"
    assert "multiple_source_artifacts_in_inbox" in packet["validation_errors"]


def test_inbox_readme_is_ignored_during_bridge_auto_discovery(tmp_path):
    inbox = tmp_path / "inbox"
    source(inbox / "README.md", "helper doc")
    source(inbox / "capital_chronicle_launch.md", "# Capital Chronicle Launch\n\nToday we launch editorial workflow upgrade.")
    packet = bridge.materialize_bridge(
        tmp_path / "source_artifact_packet.json",
        inbox=inbox,
        template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
        filled_output=tmp_path / "filled_intake_packet.json",
    )
    assert packet["bridge_status"] == "READY_FOR_INTAKE_APPROVAL"
    assert packet["source_artifact_path"].endswith("capital_chronicle_launch.md")


def test_placeholder_filler_source_does_not_reach_ready_state(tmp_path):
    inbox = tmp_path / "inbox"
    source(
        inbox / "capital_chronicle_real_announcement_001.md",
        "# Capital Chronicle — Product Update\n\n[Viết nội dung thật ở đây]\n\nSource evidence:\n- [đường dẫn tới artifact/source nếu có]\n\nOperator notes:\n- Target candidate: announcements\n- Content type candidate: announcement",
    )
    packet = bridge.materialize_bridge(
        tmp_path / "source_artifact_packet.json",
        inbox=inbox,
        template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
        filled_output=tmp_path / "filled_intake_packet.json",
    )
    assert packet["bridge_status"] == "FAIL_VALIDATION"
    assert packet["validation"]["source_artifact_ready"] is False


def test_valid_single_markdown_artifact_produces_ready_for_intake_approval(tmp_path):
    inbox = tmp_path / "inbox"
    src = source(inbox / "capital_chronicle_launch.md", "# Capital Chronicle Launch\n\nToday we launch editorial workflow upgrade.")
    packet = bridge.materialize_bridge(
        tmp_path / "source_artifact_packet.json",
        inbox=inbox,
        template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
        filled_output=tmp_path / "filled_intake_packet.json",
    )
    assert packet["bridge_status"] == "READY_FOR_INTAKE_APPROVAL"
    assert packet["source_artifact_path"].endswith(src.name)
    assert packet["recommended_target_name"] == "announcements"
    assert packet["recommended_content_type"] == "announcement"
    assert packet["filled_intake_status"] == "READY_FOR_INTAKE_APPROVAL"
    assert packet["intake_id"].startswith("discord_real_intake_")


def test_valid_artifact_with_no_inferable_target_blocks_for_operator_target_selection(tmp_path):
    inbox = tmp_path / "inbox"
    source(inbox / "capital_chronicle_note.md", "# Capital Chronicle Note\n\nEditorial process notes only.")
    packet = bridge.materialize_bridge(
        tmp_path / "source_artifact_packet.json",
        inbox=inbox,
        template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
        filled_output=tmp_path / "filled_intake_packet.json",
    )
    assert packet["bridge_status"] == "BLOCKED_AWAITING_OPERATOR_ARTIFACT"
    assert packet["block_reason"] == "operator_target_selection_required"


def test_template_dryrun_sample_test_paths_fail_validation(tmp_path):
    names = ["operator_template.md", "dryrun.md", "sample.md", "test_message.md"]
    for name in names:
        inbox = tmp_path / name.replace(".", "_")
        src = source(inbox / name, "# Real\n\nlaunch today")
        packet = bridge.materialize_bridge(
            tmp_path / f"{name}.json",
            inbox=inbox,
            source_artifact_path=src,
            template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
            filled_output=tmp_path / f"{name}_filled.json",
        )
        assert packet["bridge_status"] == "FAIL_VALIDATION"


def test_webhook_like_or_secret_like_text_fails_validation(tmp_path):
    inbox = tmp_path / "inbox"
    source(inbox / "real.md", "keep token hidden https://discord.com/api/webhooks/123/abc")
    packet = bridge.materialize_bridge(
        tmp_path / "source_artifact_packet.json",
        inbox=inbox,
        template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
        filled_output=tmp_path / "filled_intake_packet.json",
    )
    assert packet["bridge_status"] == "FAIL_VALIDATION"


def test_buy_sell_hold_trading_signal_language_fails_validation(tmp_path):
    inbox = tmp_path / "inbox"
    source(inbox / "real.md", "buy now for sure")
    packet = bridge.materialize_bridge(
        tmp_path / "source_artifact_packet.json",
        inbox=inbox,
        template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
        filled_output=tmp_path / "filled_intake_packet.json",
    )
    assert packet["bridge_status"] == "FAIL_VALIDATION"


def test_position_sizing_language_fails_validation(tmp_path):
    inbox = tmp_path / "inbox"
    source(inbox / "real.md", "Allocate 10% to this theme.")
    packet = bridge.materialize_bridge(
        tmp_path / "source_artifact_packet.json",
        inbox=inbox,
        template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
        filled_output=tmp_path / "filled_intake_packet.json",
    )
    assert packet["bridge_status"] == "FAIL_VALIDATION"


def test_guaranteed_prediction_language_fails_validation(tmp_path):
    inbox = tmp_path / "inbox"
    source(inbox / "real.md", "This will definitely win.")
    packet = bridge.materialize_bridge(
        tmp_path / "source_artifact_packet.json",
        inbox=inbox,
        template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
        filled_output=tmp_path / "filled_intake_packet.json",
    )
    assert packet["bridge_status"] == "FAIL_VALIDATION"


def test_generated_filled_intake_remains_not_approved_not_dispatchable_not_public_postable(tmp_path):
    inbox = tmp_path / "inbox"
    source(inbox / "real.md", "# Launch\n\nToday we launch new release.")
    packet = bridge.materialize_bridge(
        tmp_path / "source_artifact_packet.json",
        inbox=inbox,
        template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
        filled_output=tmp_path / "filled_intake_packet.json",
    )
    assert packet["not_approved"] is True
    assert packet["not_dispatchable"] is True
    assert packet["not_public_postable"] is True


def test_generated_packet_has_no_live_request_true(tmp_path):
    packet = bridge.materialize_bridge(
        tmp_path / "source_artifact_packet.json",
        inbox=tmp_path / "inbox",
        template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
        filled_output=tmp_path / "filled_intake_packet.json",
    )
    assert packet["no_live_request_in_this_task"] is True


def test_generated_packet_has_no_env_read_true(tmp_path):
    packet = bridge.materialize_bridge(
        tmp_path / "source_artifact_packet.json",
        inbox=tmp_path / "inbox",
        template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
        filled_output=tmp_path / "filled_intake_packet.json",
    )
    assert packet["no_env_read_in_this_task"] is True


def test_generated_packet_contains_no_webhook_url_or_env_value(tmp_path):
    inbox = tmp_path / "inbox"
    source(inbox / "real.md", "# Launch\n\nToday we launch new release.")
    packet = bridge.materialize_bridge(
        tmp_path / "source_artifact_packet.json",
        inbox=inbox,
        template=Path("docs/automation/DISCORD_REAL_CONTENT_APPROVED_QUEUE/real_content_operator_intake_template.json"),
        filled_output=tmp_path / "filled_intake_packet.json",
    )
    text = json.dumps(packet)
    assert "discord.com/api/webhooks" not in text
    assert "DISCORD_WEBHOOK" not in text


def test_module_contains_no_network_or_env_read_behavior():
    names = set(dir(bridge))
    assert "urlopen" not in names
    assert "requests" not in names
    assert "post" not in names
    assert "environ" not in names
    assert "getenv" not in names


def test_write_all_outputs_creates_required_docs(tmp_path):
    packet = bridge.blocked_packet()
    out = tmp_path / "out" / "filled_intake_from_source_packet.json"
    bridge.write_all_outputs(out, packet)
    assert out.exists()
    assert (out.parent / "implementation_report.md").exists()
    assert (out.parent / "next_task_pointer.md").exists()


def test_cli_main_generates_packet(tmp_path):
    out = tmp_path / "out" / "filled_intake_from_source_packet.json"
    rc = bridge.main([
        "--source-artifact-packet", str(tmp_path / "source_artifact_packet.json"),
        "--inbox", str(tmp_path / "inbox"),
        "--filled-output", str(tmp_path / "filled_intake_packet.json"),
        "--output", str(out),
    ])
    assert rc == 0
    packet = json.loads(out.read_text(encoding="utf-8"))
    assert packet["bridge_status"] == "BLOCKED_AWAITING_OPERATOR_ARTIFACT"
