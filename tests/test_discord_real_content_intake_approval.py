import json
from pathlib import Path

from live_contentops import discord_real_content_intake_approval as approval


def write(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def actions_packet():
    env_prefix = "DISCORD_"
    env_suffix = "_WEBHOOK_URL"
    return {
        "supervised_dispatch_actions_ready": True,
        "actions": [
            {"target_name": "announcements", "payload_type": "announcement", "destination_binding_id": "discord_announcements_capital_chronicle_01", "credential_handle_id": "discord_announcements_webhook_01", "env_key_name": env_prefix + "ANNOUNCEMENTS" + env_suffix},
            {"target_name": "substack_drops", "payload_type": "substack_drop", "destination_binding_id": "discord_substack_drops_capital_chronicle_01", "credential_handle_id": "discord_substack_drops_webhook_01", "env_key_name": env_prefix + "SUBSTACK_DROPS" + env_suffix},
            {"target_name": "product_updates", "payload_type": "product_update", "destination_binding_id": "discord_product_updates_capital_chronicle_01", "credential_handle_id": "discord_product_updates_webhook_01", "env_key_name": env_prefix + "PRODUCT_UPDATES" + env_suffix},
        ],
    }


def queue_packet(tmp_path: Path):
    actions = write(tmp_path / "actions.json", actions_packet())
    return write(tmp_path / "queue.json", {
        "task_label": "TASK_CONTENTOPS_V6_DISCORD_REAL_CONTENT_APPROVED_PAYLOAD_QUEUE_V0",
        "queue_materialization_status": "PASS",
        "real_content_queue_status": "BLOCKED_AWAITING_REAL_CONTENT_INPUT",
        "platform": "discord",
        "source_actions_packet": str(actions),
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "raw_secret_output": False,
        "dryrun_payload_reuse_blocked": True,
        "queue_records": [],
    })


def intake(**overrides):
    data = {
        "intake_id": "real_intake_001",
        "source_system": "operator",
        "source_artifact_path": "docs/operator/real_item.md",
        "content_title": "Capital Chronicle Operations Update",
        "content_body": "Capital Chronicle published an operator-reviewed workflow readiness update.",
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


def template_intake(**overrides):
    data = intake(
        template_only=True,
        not_approved=True,
        not_dispatchable=True,
        not_public_postable=True,
        intake_id="",
        content_title="",
        content_summary="",
        content_body="",
    )
    data.update(overrides)
    return data


def packet_for(tmp_path, intake_data=None, intake_path_name="intake.json"):
    qp = queue_packet(tmp_path)
    if intake_data is None:
        return approval.materialize_approval(qp, None)
    ip = write(tmp_path / intake_path_name, intake_data)
    return approval.materialize_approval(qp, ip)


def test_template_intake_produces_blocked_awaiting_filled_intake(tmp_path):
    packet = packet_for(tmp_path, template_intake())
    assert packet["approval_materialization_status"] == "PASS"
    assert packet["intake_approval_status"] == "BLOCKED_AWAITING_FILLED_INTAKE"


def test_missing_intake_produces_blocked_awaiting_filled_intake(tmp_path):
    packet = approval.materialize_approval(queue_packet(tmp_path), tmp_path / "missing.json")
    assert packet["approval_materialization_status"] == "PASS"
    assert packet["intake_approval_status"] == "BLOCKED_AWAITING_FILLED_INTAKE"


def test_filled_valid_intake_produces_candidate_not_approved_not_dispatchable(tmp_path):
    packet = packet_for(tmp_path, intake())
    assert packet["intake_approval_status"] == "APPROVAL_CANDIDATE_READY"
    assert packet["approval_state"] == "PENDING_OPERATOR_APPROVAL"
    assert packet["dispatch_state"] == "NOT_DISPATCHED"
    assert packet["ready_for_supervised_action"] is False


def test_template_is_rejected_as_public_content(tmp_path):
    packet = packet_for(tmp_path, template_intake())
    assert packet["validation"]["template_rejected"] is True
    assert packet["approval_state"] == "BLOCKED"


def test_dry_run_payload_ids_are_rejected(tmp_path):
    packet = packet_for(tmp_path, intake(intake_id="discord_dryrun_announcement_001"))
    assert packet["intake_approval_status"] == "FAIL_VALIDATION"
    assert "dryrun_payload_reuse_blocked" in packet["validation_errors"]


def test_empty_content_fails_validation(tmp_path):
    packet = packet_for(tmp_path, intake(content_title="", content_summary="", content_body=""))
    assert packet["intake_approval_status"] == "FAIL_VALIDATION"
    assert "empty_content" in packet["validation_errors"]


def test_unknown_target_fails_validation(tmp_path):
    packet = packet_for(tmp_path, intake(target_name="unknown"))
    assert packet["intake_approval_status"] == "FAIL_VALIDATION"
    assert "unknown_target" in packet["validation_errors"]


def test_target_content_type_mismatch_fails_validation(tmp_path):
    packet = packet_for(tmp_path, intake(target_name="announcements", content_type="product_update"))
    assert packet["intake_approval_status"] == "FAIL_VALIDATION"
    assert "target_payload_type_mismatch" in packet["validation_errors"]


def test_buy_sell_hold_trading_signal_language_fails_validation(tmp_path):
    for word in ["buy", "sell", "hold"]:
        packet = packet_for(tmp_path, intake(content_body=f"Do not {word} this asset."), f"{word}.json")
        assert packet["validation"]["no_trading_signal_passed"] is False
        assert "trading_signal_language_blocked" in packet["validation_errors"]


def test_position_sizing_language_fails_validation(tmp_path):
    packet = packet_for(tmp_path, intake(content_body="Allocate 10% as position size."))
    assert packet["validation"]["position_sizing_check_passed"] is False
    assert "position_sizing_language_blocked" in packet["validation_errors"]


def test_guaranteed_prediction_language_fails_validation(tmp_path):
    packet = packet_for(tmp_path, intake(content_body="This outcome is guaranteed."))
    assert packet["validation"]["guaranteed_prediction_check_passed"] is False
    assert "guaranteed_prediction_language_blocked" in packet["validation_errors"]


def test_source_evidence_pending_is_allowed_but_flagged(tmp_path):
    packet = packet_for(tmp_path, intake(source_evidence_paths=[]))
    assert packet["intake_approval_status"] == "APPROVAL_CANDIDATE_READY"
    assert packet["validation"]["source_evidence_present_or_pending"] == "PENDING"


def test_invented_numbers_without_source_evidence_remain_pending(tmp_path):
    packet = packet_for(tmp_path, intake(content_body="Revenue was 42% higher."))
    assert packet["intake_approval_status"] == "APPROVAL_CANDIDATE_READY"
    assert packet["validation"]["invented_number_safety_passed_or_pending"] == "PENDING"


def test_approval_packet_ready_for_supervised_action_false(tmp_path):
    assert packet_for(tmp_path, intake())["ready_for_supervised_action"] is False


def test_approval_packet_operator_authorization_required_true(tmp_path):
    assert packet_for(tmp_path, intake())["operator_authorization_required"] is True


def test_approval_packet_dispatch_state_not_dispatched(tmp_path):
    assert packet_for(tmp_path, intake())["dispatch_state"] == "NOT_DISPATCHED"


def test_packet_contains_no_webhook_url(tmp_path):
    text = json.dumps(packet_for(tmp_path, intake()))
    forbidden_url = "https://" + "discord.com" + "/api/" + "webhooks"
    forbidden_legacy_url = "discordapp.com" + "/api/" + "webhooks"
    assert forbidden_url not in text
    assert forbidden_legacy_url not in text


def test_packet_contains_no_env_value(tmp_path):
    text = json.dumps(packet_for(tmp_path, intake()))
    assert "SHOULD_NOT_APPEAR" not in text
    forbidden_env_key = "DISCORD_" + "ANNOUNCEMENTS" + "_WEBHOOK_URL"
    assert forbidden_env_key not in text


def test_no_live_request_in_this_task_true(tmp_path):
    assert packet_for(tmp_path, intake())["no_live_request_in_this_task"] is True


def test_no_env_read_in_this_task_true(tmp_path):
    assert packet_for(tmp_path, intake())["no_env_read_in_this_task"] is True


def test_no_network_env_function_exists_or_is_called():
    names = set(dir(approval))
    assert "urlopen" not in names
    assert "requests" not in names
    assert "post" not in names
    assert "environ" not in names
    assert "getenv" not in names


def test_panel_contains_no_active_live_button(tmp_path):
    packet = packet_for(tmp_path, intake())
    html = approval.render_panel(packet).lower()
    active_button_marker = "<" + "button"
    assert active_button_marker not in html
    assert "onclick" not in html
    assert "form" not in html
    assert "live dispatch" not in html


def test_operator_decision_required_for_candidate(tmp_path):
    packet = packet_for(tmp_path, intake())
    assert all(packet["operator_decision_required"].values())


def test_output_writer_creates_packet_schema_panel_and_reports(tmp_path):
    packet = packet_for(tmp_path, template_intake())
    out = tmp_path / "out" / "real_content_intake_approval_packet.json"
    approval.write_all_outputs(out, packet)
    assert out.exists()
    assert (out.parent / "real_content_intake_approval_schema.json").exists()
    assert (out.parent / "operator_approval_panel.html").exists()
    assert (out.parent / "implementation_report.md").exists()
    assert (out.parent / "next_task_pointer.md").exists()
