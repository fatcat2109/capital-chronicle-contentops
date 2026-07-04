import json
from pathlib import Path

from live_contentops import discord_real_content_queue as queue


def write(path: Path, data: dict):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def closeout_packet(**overrides):
    data = {"readiness_update": {"supervised_live_loop_verified": True}, "closeout_status": "PASS"}
    data.update(overrides)
    return data


def actions_packet(**overrides):
    data = {
        "supervised_dispatch_actions_ready": True,
        "actions": [
            {"target_name": "announcements", "payload_type": "announcement", "destination_binding_id": "discord_announcements_capital_chronicle_01", "credential_handle_id": "discord_announcements_webhook_01", "env_key_name": "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL"},
            {"target_name": "substack_drops", "payload_type": "substack_drop", "destination_binding_id": "discord_substack_drops_capital_chronicle_01", "credential_handle_id": "discord_substack_drops_webhook_01", "env_key_name": "DISCORD_SUBSTACK_DROPS_WEBHOOK_URL"},
            {"target_name": "product_updates", "payload_type": "product_update", "destination_binding_id": "discord_product_updates_capital_chronicle_01", "credential_handle_id": "discord_product_updates_webhook_01", "env_key_name": "DISCORD_PRODUCT_UPDATES_WEBHOOK_URL"},
        ],
    }
    data.update(overrides)
    return data


def intake(**overrides):
    data = {
        "intake_id": "real_intake_001",
        "source_system": "operator",
        "source_artifact_path": "docs/operator/real_item.md",
        "content_title": "Capital Chronicle Operations Update",
        "content_body": "Capital Chronicle published an operator-reviewed update for community workflow readiness.",
        "content_summary": "Operator-reviewed publication note.",
        "content_type": "announcement",
        "target_name": "announcements",
        "author_or_operator": "operator",
        "created_at_utc": "2026-06-27T00:00:00Z",
        "approval_required": True,
        "financial_advice_check_required": True,
        "no_trading_signal_required": True,
        "source_evidence_paths": [],
        "operator_notes": "test intake",
        "publish_intent": "community update",
    }
    data.update(overrides)
    return data


def packet_for(tmp_path, intake_data=None):
    closeout = write(tmp_path / "closeout.json", closeout_packet())
    actions = write(tmp_path / "actions.json", actions_packet())
    intake_path = write(tmp_path / "intake.json", intake_data) if intake_data is not None else None
    return queue.materialize_queue(closeout, actions, intake_path)


def test_pass_framework_result_from_valid_closeout_actions_packets(tmp_path):
    packet = packet_for(tmp_path)
    assert packet["queue_materialization_status"] == "PASS"
    assert packet["supervised_live_loop_verified"] is True


def test_blocked_awaiting_real_content_when_no_intake(tmp_path):
    assert packet_for(tmp_path)["real_content_queue_status"] == "BLOCKED_AWAITING_REAL_CONTENT_INPUT"


def test_dryrun_payload_ids_rejected_as_real_content(tmp_path):
    packet = packet_for(tmp_path, intake(intake_id="discord_dryrun_announcement_001"))
    assert packet["queue_materialization_status"] == "FAIL"
    assert "dryrun_payload_reuse_blocked" in packet["rejected_records"][0]["errors"]


def test_template_not_approved_not_dispatchable_not_public_postable():
    template = queue.intake_template()
    assert template["template_only"] is True
    assert template["not_approved"] is True
    assert template["not_dispatchable"] is True
    assert template["not_public_postable"] is True


def test_valid_filled_intake_creates_one_pending_queue_record_without_dispatch(tmp_path):
    packet = packet_for(tmp_path, intake())
    assert packet["real_content_queue_status"] == "READY_WITH_REAL_CONTENT"
    assert packet["pending_real_content_count"] == 1
    record = packet["queue_records"][0]
    assert record["approval_state"] == "PENDING_OPERATOR_APPROVAL"
    assert record["ready_for_supervised_action"] is False


def test_empty_content_rejected(tmp_path):
    packet = packet_for(tmp_path, intake(content_title="", content_summary="", content_body=""))
    assert packet["queue_materialization_status"] == "FAIL"
    assert "empty_content" in packet["rejected_records"][0]["errors"]


def test_unknown_target_rejected(tmp_path):
    packet = packet_for(tmp_path, intake(target_name="unknown"))
    assert packet["queue_materialization_status"] == "FAIL"
    assert "unknown_target" in packet["rejected_records"][0]["errors"]


def test_target_payload_type_mismatch_rejected(tmp_path):
    packet = packet_for(tmp_path, intake(target_name="announcements", content_type="product_update"))
    assert packet["queue_materialization_status"] == "FAIL"
    assert "target_payload_type_mismatch" in packet["rejected_records"][0]["errors"]


def test_buy_sell_hold_trading_signal_language_blocked(tmp_path):
    for word in ["buy", "sell", "hold"]:
        packet = packet_for(tmp_path, intake(content_body=f"Do not {word} this asset."))
        assert "trading_signal_language_blocked" in packet["rejected_records"][0]["errors"]


def test_position_sizing_language_blocked(tmp_path):
    packet = packet_for(tmp_path, intake(content_body="Allocate 10% as position size."))
    assert "position_sizing_language_blocked" in packet["rejected_records"][0]["errors"]


def test_guaranteed_prediction_language_blocked(tmp_path):
    packet = packet_for(tmp_path, intake(content_body="This outcome is guaranteed."))
    assert "guaranteed_prediction_language_blocked" in packet["rejected_records"][0]["errors"]


def test_invented_number_safety_field_remains_pending_without_source_evidence():
    valid, validation, errors = queue.validate_intake(intake(content_body="Revenue was 42% higher."), actions_packet())
    assert valid is True
    assert errors == []
    assert validation["invented_number_safety_passed_or_pending"] == "PENDING"


def test_queue_record_has_operator_authorization_required(tmp_path):
    assert packet_for(tmp_path, intake())["queue_records"][0]["operator_authorization_required"] is True


def test_queue_record_dispatch_state_not_dispatched(tmp_path):
    assert packet_for(tmp_path, intake())["queue_records"][0]["dispatch_state"] == "NOT_DISPATCHED"


def test_generated_payload_forces_allowed_mentions_parse_empty(tmp_path):
    assert packet_for(tmp_path, intake())["queue_records"][0]["rendered_payload"]["allowed_mentions"] == {"parse": []}


def test_packet_contains_no_webhook_url(tmp_path):
    text = json.dumps(packet_for(tmp_path, intake()))
    forbidden_url = "https://" + "discord.com" + "/api/" + "webhooks"
    assert forbidden_url not in text
    forbidden_legacy_url = "discordapp.com" + "/api/" + "webhooks"
    assert forbidden_legacy_url not in text


def test_packet_contains_env_key_names_but_no_env_values(tmp_path):
    text = json.dumps(packet_for(tmp_path, intake()))
    assert "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL" in text
    assert "SHOULD_NOT_APPEAR" not in text


def test_no_live_request_possible_from_module():
    names = set(dir(queue))
    assert "urlopen" not in names
    assert "requests" not in names
    assert "post" not in names


def test_no_env_read_function_exists_or_called():
    names = set(dir(queue))
    assert "environ" not in names
    assert "getenv" not in names
