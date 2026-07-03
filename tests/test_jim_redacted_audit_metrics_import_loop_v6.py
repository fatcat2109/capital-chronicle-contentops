import json
from pathlib import Path

from live_contentops.jim_redacted_audit_metrics_import_loop_v6 import build_jim_redacted_audit_metrics_import_loop


def _packet():
    return build_jim_redacted_audit_metrics_import_loop()


def test_redacted_audit_metrics_loop_counts_and_hashes():
    packet = _packet()

    assert packet["loop_status"] == "JIM_REVIEW_REQUIRED_OPERATOR_SUPPLIED_METRICS_ONLY"
    assert packet["operator_id"] == "Jim"
    assert packet["audit_card_count"] == packet["metrics_packet_count"] == packet["backlog_candidate_count"]
    assert packet["audit_card_count"] > 0
    assert packet["loop_hash_algorithm"] == "sha256"
    assert _packet()["loop_hash"] == packet["loop_hash"]


def test_operator_supplied_only_no_live_collection():
    packet = _packet()

    assert packet["safety_flags"]["operator_supplied_values_only"] is True
    assert packet["safety_flags"]["network_called"] is False
    assert packet["safety_flags"]["scraping_performed"] is False
    assert packet["safety_flags"]["metrics_api_called"] is False
    assert packet["safety_flags"]["platform_api_called"] is False
    assert packet["safety_flags"]["baseline_promoted"] is False

    for card in packet["manual_publish_record_packets"]:
        assert card["operator_supplied_reference_only"] is True
        assert card["public_reference_verified"] is False
        assert card["network_checked"] is False
        assert card["scraping_performed"] is False

    for metrics in packet["metrics_import_packets"]:
        assert metrics["metrics_source"] == "operator_supplied_manual_entry"
        assert metrics["metrics_network_verified"] is False
        assert metrics["metrics_api_called"] is False
        assert metrics["normalized_engagement_total"] == sum(metrics["metrics"].values())


def test_backlog_candidates_never_promote_baseline():
    packet = _packet()

    for candidate in packet["feedback_backlog_candidates"]:
        assert candidate["candidate_status"] == "FEEDBACK_CANDIDATE_NOT_PROMOTED"
        assert candidate["requires_jim_review"] is True
        assert candidate["baseline_promoted"] is False
        assert candidate["safety_flags"]["baseline_promoted"] is False


def test_fixture_matches_builder():
    fixture = json.loads((Path(__file__).parents[1] / "fixtures" / "v6" / "jim_redacted_audit_metrics_import_loop_sample_v6.json").read_text(encoding="utf-8"))
    assert fixture == _packet()


def test_no_link_fields_or_network_text():
    packet = _packet()
    text = json.dumps(packet, sort_keys=True).lower()
    forbidden_text = ("http://", "https://", "fetch live", "api sync", "dispatch-ready", "publish-ready")

    assert not any(term in text for term in forbidden_text)

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                assert "url" not in key.lower()
                assert "href" not in key.lower()
                assert "link" not in key.lower()
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(packet)
