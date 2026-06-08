import json
import os

import pytest

from live_contentops import artifact_packet_bridge as apb


def load_fixtures():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "editorial",
                        "artifact_packet_bridge_input.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["fixtures"]


FIXTURES = load_fixtures()


def _by_label(label):
    return next(f for f in FIXTURES if f["label"] == label)


def test_bridge_record_has_all_required_fields():
    rec = apb.build_bridge_record(_by_label("valid_synthetic_product_update")["input"])
    required = [
        "bridge_id", "intake_id", "artifact_id", "artifact_family", "artifact_type",
        "artifact_origin", "intake_gate_status", "bridge_route", "bridge_status",
        "route_blockers", "route_warnings", "synthetic_route_guard_status",
        "real_artifact_route_allowed", "packet_input_allowed", "packet_input_mode",
        "packet_content_type", "source_artifact_ids", "source_lineage_refs",
        "limitation_summary", "freshness_as_of", "dqr_status",
        "data_sufficiency_status", "forecast_readiness_status", "proxy_data_status",
        "missing_data_status", "degradation_status", "not_public_postable_reason",
        "local_only", "advisory_only", "human_review_required", "approval_granted",
        "publish_ready", "provider_call_allowed", "search_call_allowed",
        "platform_action_allowed",
    ]
    for key in required:
        assert key in rec, f"missing field: {key}"


def test_route_mapping_deterministic_by_origin():
    syn = apb.build_bridge_record(_by_label("valid_synthetic_product_update")["input"])
    assert syn["bridge_route"] == apb.SYNTHETIC_LOCAL_REVIEW_ROUTE
    fut = apb.build_bridge_record(_by_label("future_real_artifact_placeholder")["input"])
    assert fut["bridge_route"] == apb.FUTURE_REAL_ARTIFACT_PLACEHOLDER_ROUTE
    appr = apb.build_bridge_record(_by_label("approved_real_artifact_contract_sample")["input"])
    assert appr["bridge_route"] == apb.APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE


def test_internal_test_origin_route():
    rec = apb.build_bridge_record({
        "artifact_id": "I1", "artifact_family": "product_update",
        "artifact_origin": "internal_test_fixture", "limitation_summary": "x",
        "freshness_as_of": "2026-01-01", "missing_data_status": "NONE",
        "proxy_data_status": "NONE", "degradation_status": "NONE"})
    assert rec["bridge_route"] == apb.INTERNAL_TEST_LOCAL_REVIEW_ROUTE


@pytest.mark.parametrize("origin", [
    "synthetic_fixture", "internal_test_fixture", "future_real_artifact_placeholder"])
def test_non_public_origins_cannot_use_approved_real_route(origin):
    rec = apb.build_bridge_record({
        "artifact_id": "X", "artifact_family": "product_update",
        "artifact_origin": origin, "approved_for_contentops": True,
        "limitation_summary": "x", "freshness_as_of": "2026-01-01",
        "missing_data_status": "NONE", "proxy_data_status": "NONE",
        "degradation_status": "NONE"})
    assert rec["bridge_route"] != apb.APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE
    assert rec["real_artifact_route_allowed"] is False


def test_summary_fixture_only_posture():
    s = apb.build_summary()
    assert s["fixture_only"] is True
    assert s["requires_real_alpha_artifacts_now"] is False
    assert s["artifact_packet_bridge_enabled"] is True
    assert s["synthetic_route_guard_enabled"] is True
    assert s["all_fixture_outputs_not_public_postable"] is True
    assert set(s["supported_routes"]) == set(apb.SUPPORTED_ROUTES)


def test_approved_real_route_requires_approval_evidence():
    rec = apb.build_bridge_record({
        "artifact_id": "R1", "artifact_family": "product_update",
        "artifact_origin": "approved_real_artifact", "limitation_summary": "x",
        "freshness_as_of": "2026-01-01", "missing_data_status": "NONE",
        "proxy_data_status": "NONE", "degradation_status": "NONE"})
    assert rec["bridge_route"] == apb.BLOCKED_ROUTE
    assert any("approval_source" in b for b in rec["route_blockers"])


def test_approved_real_contract_sample_local_review_only():
    rec = apb.build_bridge_record(
        _by_label("approved_real_artifact_contract_sample")["input"])
    assert rec["bridge_route"] == apb.APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE
    assert rec["packet_input_mode"] == "LOCAL_REVIEW_ONLY"
    assert rec["publish_ready"] is False
    assert rec["approval_granted"] is False
    assert rec["not_public_postable_reason"]


def test_packet_input_projection_preserves_fields():
    rec = apb.build_bridge_record(
        _by_label("approved_real_artifact_contract_sample")["input"])
    proj = apb.project_packet_input(rec)
    assert proj["source_lineage_refs"] == rec["source_lineage_refs"]
    assert proj["content_type"] == rec["packet_content_type"]
    assert proj["limitation_summary"] == rec["limitation_summary"]
    assert proj["freshness_as_of"] == rec["freshness_as_of"]
    assert proj["artifact_origin"] == rec["artifact_origin"]
    assert proj["not_public_postable_reason"] == rec["not_public_postable_reason"]
    assert proj["dqr_status"] == rec["dqr_status"]
    for flag in ("approval_granted", "publish_ready", "provider_call_allowed",
                 "search_call_allowed", "platform_action_allowed"):
        assert proj[flag] is False


def test_projection_marks_synthetic_origin():
    rec = apb.build_bridge_record(_by_label("valid_synthetic_product_update")["input"])
    proj = apb.project_packet_input(rec)
    assert proj["synthetic_origin"] is True


def test_intake_gate_blocked_prevents_packet_input():
    rec = apb.build_bridge_record(
        _by_label("blocked_forecast_readiness_dqr_blocking")["input"])
    assert rec["intake_gate_status"] == "BLOCKED"
    assert rec["bridge_route"] == apb.BLOCKED_ROUTE
    assert rec["packet_input_allowed"] is False


def test_dqr_blocking_cannot_be_bypassed():
    rec = apb.build_bridge_record(
        _by_label("blocked_forecast_readiness_dqr_blocking")["input"])
    assert rec["packet_input_allowed"] is False


def test_missing_proxy_degraded_data_cannot_be_hidden():
    rec = apb.build_bridge_record({
        "artifact_id": "P1", "artifact_family": "product_update",
        "artifact_origin": "synthetic_fixture", "limitation_summary": "x",
        "freshness_as_of": "2026-01-01", "missing_data_status": "",
        "proxy_data_status": "", "degradation_status": ""})
    assert rec["bridge_route"] == apb.BLOCKED_ROUTE
    assert rec["synthetic_route_guard_status"] == "BLOCKED"


def test_market_note_missing_freshness_blocked():
    rec = apb.build_bridge_record(
        _by_label("blocked_market_note_missing_freshness")["input"])
    assert rec["bridge_route"] == apb.BLOCKED_ROUTE
    assert rec["packet_input_allowed"] is False


def test_synthetic_claims_approved_real_blocked():
    rec = apb.build_bridge_record(
        _by_label("blocked_synthetic_claims_approved_real")["input"])
    assert rec["bridge_route"] == apb.BLOCKED_ROUTE
    assert rec["synthetic_route_guard_status"] == "BLOCKED"


def test_forbidden_trading_language_blocked():
    rec = apb.build_bridge_record(
        _by_label("blocked_forbidden_trading_language")["input"])
    assert rec["bridge_route"] == apb.BLOCKED_ROUTE
    assert rec["packet_input_allowed"] is False


def test_all_bridge_outputs_not_public_postable():
    for fx in FIXTURES:
        rec = apb.build_bridge_record(fx["input"])
        assert rec["publish_ready"] is False
        assert rec["approval_granted"] is False
        assert rec["platform_action_allowed"] is False
        assert rec["not_public_postable_reason"]
        proj = apb.project_packet_input(rec)
        assert proj["publish_ready"] is False
        assert proj["approval_granted"] is False


def test_validate_bridge_record_clean_for_valid():
    rec = apb.build_bridge_record(_by_label("valid_synthetic_product_update")["input"])
    res = apb.validate_bridge_record(rec)
    assert res["status"] in ("PASS", "WARNING")
    assert res["blockers"] == []


def test_validate_blocks_gate_blocked_with_packet_input():
    rec = apb.build_bridge_record(_by_label("valid_synthetic_product_update")["input"])
    rec["intake_gate_status"] = "BLOCKED"
    res = apb.validate_bridge_record(rec)
    assert res["status"] == "BLOCKED"
    assert any("intake gate BLOCKED" in b for b in res["blockers"])


def test_all_fixtures_match_expected_route():
    for fx in FIXTURES:
        rec = apb.build_bridge_record(fx["input"])
        assert rec["bridge_route"] == fx["expected_route"], \
            f"{fx['label']}: {rec['bridge_route']} != {fx['expected_route']}"

