import json

from live_contentops.jim_manual_export_approval_workbench_v6 import (
    EXPORT_STATUS_BLOCKED,
    EXPORT_STATUS_READY,
    build_jim_manual_export_approval_workbench,
)


def test_workbench_builds_manual_export_and_approval_previews():
    packet = build_jim_manual_export_approval_workbench()

    assert packet["workbench_status"] == "JIM_APPROVAL_REQUIRED_MANUAL_EXPORT_ONLY"
    assert packet["operator_id"] == "jim"
    assert packet["export_packet_count"] == 12
    assert packet["approval_record_preview_count"] == 12
    assert packet["ready_export_packet_count"] > 0
    assert packet["blocked_export_packet_count"] > 0
    assert packet["workbench_hash_algorithm"] == "sha256"


def test_manual_export_packets_are_local_only_and_not_public_postable():
    packet = build_jim_manual_export_approval_workbench()
    statuses = {EXPORT_STATUS_READY, EXPORT_STATUS_BLOCKED}

    for export in packet["manual_export_packets"]:
        assert export["manual_export_status"] in statuses
        assert export["requires_jim_final_approval"] is True
        assert export["final_public_copy_created"] is False
        assert export["public_postable"] is False
        assert export["dispatch_ready"] is False
        assert export["public_url_verified"] is False
        assert export["safety_flags"]["manual_export_only"] is True
        assert export["safety_flags"]["network_called"] is False
        assert export["safety_flags"]["platform_api_called"] is False
        assert export["safety_flags"]["approval_valid_for_dispatch"] is False
        assert "No public URL verification" in export["markdown_body"]


def test_approval_records_never_become_dispatch_authority():
    packet = build_jim_manual_export_approval_workbench()

    for record in packet["approval_record_previews"]:
        assert record["approval_status"] == "APPROVAL_RECORD_PREVIEW_ONLY_NOT_VALID_FOR_DISPATCH"
        assert record["approval_channel"] == "local_ui_read_only_preview"
        assert record["operator_id"] == "Jim"
        assert record["valid_for_dispatch"] is False
        assert record["public_postable"] is False
        assert record["dispatch_ready"] is False
        assert "dispatch_revalidation_not_built" in record["blocked_reasons"]


def test_workbench_hash_is_stable_and_fixture_matches():
    packet = build_jim_manual_export_approval_workbench()
    fixture = json.loads((__import__("pathlib").Path(__file__).parents[1] / "fixtures" / "v6" / "jim_manual_export_approval_workbench_sample_v6.json").read_text(encoding="utf-8"))

    assert build_jim_manual_export_approval_workbench()["workbench_hash"] == packet["workbench_hash"]
    assert fixture == packet


def test_no_forbidden_public_or_live_claims():
    packet = build_jim_manual_export_approval_workbench()
    text = json.dumps(packet, sort_keys=True).lower()
    forbidden = ("publish-ready", "dispatch-ready", "ready for dispatch", "ready for publish", "public url verified")

    assert not any(term in text for term in forbidden)
    assert "https://" not in text
    assert "http://" not in text
