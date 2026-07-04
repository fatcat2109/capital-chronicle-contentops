import json
from pathlib import Path

from live_contentops import discord_tri_target_dispatch_closeout as closeout


def packet(target_key, **overrides):
    expected = closeout.EXPECTED_TARGETS[target_key]
    data = {
        "target_name": expected.target_name,
        "payload_id": expected.payload_id,
        "payload_hash": expected.payload_hash,
        "result_status": "PASS",
        "http_status_code": 204,
        "status_code_class": "2xx",
        "diagnostic_interpretation": "success_2xx",
        "request_count_attempted": 1,
        "retry_count_attempted": 0,
        "live_write_completed": True,
    }
    data.update(overrides)
    return data


def write_packet(tmp_path, name, data):
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def run_with_packets(tmp_path, announcements=None, substack=None, product=None):
    return closeout.closeout_from_files(
        announcements_packet=write_packet(tmp_path, "announcements", announcements or packet("announcements")),
        substack_packet=write_packet(tmp_path, "substack", substack or packet("substack_drops")),
        product_updates_packet=write_packet(tmp_path, "product", product or packet("product_updates")),
        output=tmp_path / "out.json",
    )


def test_closeout_pass_when_all_three_packets_are_pass_204(tmp_path):
    result = run_with_packets(tmp_path)
    assert result["closeout_status"] == "PASS"
    assert result["readiness_summary"]["verified_target_count"] == 3


def test_closeout_blocked_when_required_input_packet_missing(tmp_path):
    result = closeout.closeout_from_files(
        announcements_packet=tmp_path / "missing.json",
        substack_packet=write_packet(tmp_path, "substack", packet("substack_drops")),
        product_updates_packet=write_packet(tmp_path, "product", packet("product_updates")),
        output=tmp_path / "out.json",
    )
    assert result["closeout_status"] == "BLOCKED"
    assert "required_input_packet_missing_or_unreadable" in result["blocker"]


def test_closeout_fail_when_any_result_status_is_not_pass(tmp_path):
    result = run_with_packets(tmp_path, substack=packet("substack_drops", result_status="FAIL"))
    assert result["closeout_status"] == "FAIL"
    assert result["failure_reason"] == "substack_drops_result_status_not_pass"


def test_closeout_fail_when_any_http_status_is_not_2xx(tmp_path):
    result = run_with_packets(tmp_path, product=packet("product_updates", http_status_code=403))
    assert result["closeout_status"] == "FAIL"
    assert result["failure_reason"] == "product_updates_http_status_not_2xx"


def test_closeout_fail_when_any_request_count_attempted_is_not_1(tmp_path):
    result = run_with_packets(tmp_path, announcements=packet("announcements", request_count_attempted=0))
    assert result["closeout_status"] == "FAIL"
    assert result["failure_reason"] == "announcements_request_count_mismatch"


def test_closeout_fail_when_any_retry_count_attempted_is_not_0(tmp_path):
    result = run_with_packets(tmp_path, substack=packet("substack_drops", retry_count_attempted=1))
    assert result["closeout_status"] == "FAIL"
    assert result["failure_reason"] == "substack_drops_retry_count_mismatch"


def test_closeout_fail_when_any_live_write_completed_is_not_true(tmp_path):
    result = run_with_packets(tmp_path, product=packet("product_updates", live_write_completed=False))
    assert result["closeout_status"] == "FAIL"
    assert result["failure_reason"] == "product_updates_live_write_not_completed"


def test_closeout_fail_when_target_name_mismatches_expected(tmp_path):
    result = run_with_packets(tmp_path, product=packet("product_updates", target_name="wrong"))
    assert result["closeout_status"] == "FAIL"
    assert result["failure_reason"] == "product_updates_target_name_mismatch"


def test_closeout_fail_when_payload_id_mismatches_expected(tmp_path):
    result = run_with_packets(tmp_path, substack=packet("substack_drops", payload_id="wrong"))
    assert result["closeout_status"] == "FAIL"
    assert result["failure_reason"] == "substack_drops_payload_id_mismatch"


def test_closeout_fail_when_payload_hash_mismatches_expected(tmp_path):
    result = run_with_packets(tmp_path, announcements=packet("announcements", payload_hash="wrong"))
    assert result["closeout_status"] == "FAIL"
    assert result["failure_reason"] == "announcements_payload_hash_mismatch"


def test_no_network_env_function_exists_or_is_called():
    module_text = Path(closeout.__file__).read_text(encoding="utf-8")
    forbidden = ["urlopen", "Request(", "__import__(\"os\")", "environ", "getenv"]
    assert all(token not in module_text for token in forbidden)


def test_generated_packet_marks_all_three_targets_ready_for_supervised_dispatch(tmp_path):
    result = run_with_packets(tmp_path)
    assert all(
        target["ready_for_supervised_dispatch"] is True
        for target in result["verified_targets"].values()
    )
    assert all(
        target["adapter_dispatch_verified"] is True
        for target in result["verified_targets"].values()
    )


def test_generated_packet_marks_supervised_discord_dispatch_ready_true(tmp_path):
    result = run_with_packets(tmp_path)
    assert result["readiness_summary"]["supervised_discord_dispatch_ready"] is True
    assert result["readiness_summary"]["remaining_discord_dispatch_pilots"] == 0


def test_generated_packet_contains_no_webhook_url(tmp_path):
    out = tmp_path / "out.json"
    result = closeout.closeout_from_files(
        announcements_packet=write_packet(tmp_path, "announcements", packet("announcements")),
        substack_packet=write_packet(tmp_path, "substack", packet("substack_drops")),
        product_updates_packet=write_packet(tmp_path, "product", packet("product_updates")),
        output=out,
    )
    text = out.read_text(encoding="utf-8") + json.dumps(result, sort_keys=True)
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text
    assert "webhook_url" not in text
    assert result["raw_secret_output"] is False
    assert result["response_body_recorded"] is False
    assert result["response_headers_recorded"] is False
