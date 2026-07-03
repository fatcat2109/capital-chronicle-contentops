import json

from live_contentops import final_product_readiness_v6 as lane


def test_final_product_readiness_packet_is_local_only(tmp_path):
    bundle = tmp_path / "bundle.json"
    matrix = tmp_path / "matrix.json"
    acceptance = tmp_path / "acceptance.json"
    bundle.write_text(json.dumps({"readiness_evidence_bundle_packet_id": "bundle_abc"}), encoding="utf-8")
    matrix.write_text(json.dumps([{"lane_name": "x", "unresolved_blockers": ["b"]}]), encoding="utf-8")
    acceptance.write_text(json.dumps({"can_accept_substack_live_publish_success": True}), encoding="utf-8")

    packet = lane.build_final_product_readiness_packet(bundle, matrix, acceptance)

    assert packet["task_label"] == "TASK_0059"
    assert packet["readiness_status"] == "FINAL_PRODUCT_READY_FOR_LOCAL_OPERATOR_REVIEW_ONLY"
    assert packet["substack_live_publish_success_accepted"] is True
    assert packet["substack_public_url_verified"] is False
    assert packet["dispatch_allowed_now"] is False
    assert packet["live_write_allowed_now"] is False
    assert packet["browser_or_cdp_action_performed"] is False
    assert packet["network_call_performed"] is False
    assert packet["env_or_credential_read_performed"] is False
    assert packet["raw_secret_output"] is False
    assert packet["private_url_or_dom_recorded"] is False


def test_final_product_readiness_blocks_when_inputs_missing(tmp_path):
    packet = lane.build_final_product_readiness_packet(
        tmp_path / "missing_bundle.json",
        tmp_path / "missing_matrix.json",
        tmp_path / "missing_acceptance.json",
    )

    assert packet["readiness_status"] == "FINAL_PRODUCT_READINESS_BLOCKED"
    assert len(packet["missing_inputs"]) == 3


def test_module_contains_no_forbidden_behavior():
    attrs = dir(lane)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
