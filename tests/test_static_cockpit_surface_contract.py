import importlib
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _result():
    from live_contentops import static_cockpit_surface_contract as contract

    return contract.write_artifacts(REPO_ROOT)


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.static_cockpit_surface_contract")
    assert module.TASK_LABEL == "TASK_CONTENTOPS_0174YI_YJ_YK_STATIC_COCKPIT_SURFACE_CONTRACT_V0"


def test_surface_packet_statuses_and_counts():
    result = _result()
    packet = result["surface"]
    assert packet["readiness_class"] == "NOT_READY_FOR_LIVE_DISPATCH"
    assert packet["live_dispatch_status"] == "BLOCKED"
    assert packet["can_dispatch"] is False
    assert packet["public_postable"] is False
    assert packet["reviewable_now_count"] == 14
    assert packet["manual_export_queue_count"] == 6
    assert packet["x_preview_queue_count"] == 6
    assert packet["telegram_preview_queue_count"] == 2
    assert packet["blocked_live_dispatch_count"] == 5
    assert packet["html_file"] == "static_cockpit_surface.html"
    assert len(packet["payload_hash_index"]) == packet["reviewable_now_count"]


def test_queue_items_remain_review_only_and_hash_bound():
    result = _result()
    all_items = result["fixture_outputs"]
    assert all_items
    for item in all_items:
        assert item["can_dispatch"] is False
        assert item["public_postable"] is False
        assert item["human_review_required"] is True
        assert len(item["payload_hash"]) == 64
        assert item["payload_hash_short"] == item["payload_hash"][:12]
        assert item["allowed_operator_action"] in result["surface"]["allowed_actions"]


def test_html_is_screenshot_safe_static_and_contains_sections():
    result = _result()
    html_text = result["html"]
    lowered = html_text.lower()
    assert "static cockpit preview" in lowered
    assert "manual export queue" in lowered
    assert "x preview queue" in lowered
    assert "telegram preview queue" in lowered
    assert "blocked live dispatch" in lowered
    assert "payload hashes" in lowered
    assert "evidence index" in lowered
    assert "next safe operator action" in lowered
    assert "<script" not in lowered
    assert "<form" not in lowered
    assert "http://" not in lowered
    assert "https://" not in lowered
    assert ".env" not in lowered
    assert "provider_response" not in lowered
    assert "live-ready" not in lowered
    assert "dispatch-ready" not in lowered
    assert "public-postable" not in lowered


def test_checksums_and_next_handoff_present():
    result = _result()
    packet = result["surface"]
    next_packet = result["next_packet"]
    assert len(packet["static_cockpit_surface_checksum"]) == 64
    assert len(packet["static_cockpit_surface_fixture_outputs_checksum"]) == 64
    assert len(packet["html_checksum"]) == 64
    assert len(next_packet["next_cockpit_ui_shell_contract_checksum"]) == 64
    assert next_packet["static_cockpit_surface_checksum"] == packet["static_cockpit_surface_checksum"]
    assert next_packet["static_cockpit_surface_html_checksum"] == packet["html_checksum"]
    assert next_packet["live_dispatch_status"] == "BLOCKED"
    assert next_packet["ui_shell_must_remain_local_only"] is True


def test_generated_files_exist_and_are_deterministic():
    first = _result()
    second = _result()
    assert first["surface"] == second["surface"]
    assert first["fixture_outputs"] == second["fixture_outputs"]
    assert first["html"] == second["html"]
    out = REPO_ROOT / "docs" / "automation" / "0174YI_YJ_YK"
    assert (out / "static_cockpit_surface_packet.json").exists()
    assert (out / "static_cockpit_surface.html").exists()
    assert (out / "static_cockpit_surface_fixture_outputs.json").exists()
    assert (out / "next_cockpit_ui_shell_contract_packet.json").exists()


def test_unsafe_output_path_refused():
    from live_contentops import static_cockpit_surface_contract as contract

    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        contract.write_artifacts(REPO_ROOT, REPO_ROOT / "docs" / "automation")
