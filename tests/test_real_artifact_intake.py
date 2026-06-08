import json
import os

import pytest

from live_contentops import real_artifact_intake as ri


def load_fixtures():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "editorial",
                        "real_artifact_intake_input.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["fixtures"]


FIXTURES = load_fixtures()


def _by_label(label):
    return next(f for f in FIXTURES if f["label"] == label)


def test_intake_envelope_has_all_required_fields():
    fx = _by_label("valid_synthetic_product_update")
    env = ri.build_intake_envelope(fx["input"])
    required = [
        "intake_id", "artifact_id", "artifact_family", "artifact_type",
        "artifact_origin", "artifact_status", "approved_for_contentops",
        "approval_source", "approval_timestamp", "source_artifact_ids",
        "source_lineage_refs", "freshness_as_of", "limitation_summary",
        "data_sufficiency_status", "dqr_status", "forecast_readiness_status",
        "proxy_data_status", "missing_data_status", "degradation_status",
        "educational_general_only", "no_financial_advice",
        "not_public_postable_reason", "local_only", "advisory_only",
        "human_review_required", "approval_granted", "publish_ready",
        "provider_call_allowed", "search_call_allowed", "platform_action_allowed",
    ]
    for key in required:
        assert key in env, f"missing field: {key}"


def test_envelope_safety_flags():
    env = ri.build_intake_envelope(_by_label("valid_synthetic_product_update")["input"])
    assert env["local_only"] is True
    assert env["advisory_only"] is True
    assert env["human_review_required"] is True
    assert env["approval_granted"] is False
    assert env["publish_ready"] is False
    assert env["provider_call_allowed"] is False
    assert env["search_call_allowed"] is False
    assert env["platform_action_allowed"] is False
    assert env["no_financial_advice"] is True
    assert env["not_public_postable_reason"]


def test_summary_fixture_only_posture():
    s = ri.build_summary()
    assert s["fixture_only"] is True
    assert s["requires_real_alpha_artifacts_now"] is False
    assert s["real_artifact_intake_enabled"] is True
    assert s["readiness_gate_enabled"] is True
    assert s["all_fixture_outputs_not_public_postable"] is True


def test_supported_families_and_origins_deterministic():
    s = ri.build_summary()
    assert "market_note" in s["supported_artifact_families"]
    assert "forecast_readiness" in s["supported_artifact_families"]
    assert set(s["supported_artifact_origins"]) == {
        "synthetic_fixture", "internal_test_fixture",
        "future_real_artifact_placeholder", "approved_real_artifact"}


@pytest.mark.parametrize("origin", [
    "synthetic_fixture", "internal_test_fixture", "future_real_artifact_placeholder"])
def test_non_public_origins_stay_not_public_postable(origin):
    env = ri.build_intake_envelope({
        "artifact_id": "X", "artifact_family": "product_update",
        "artifact_origin": origin, "limitation_summary": "demo",
        "missing_data_status": "NONE", "proxy_data_status": "NONE",
        "degradation_status": "NONE"})
    gate = ri.evaluate_readiness_gate(env)
    assert gate["not_public_postable"] is True
    assert gate["publish_ready"] is False
    assert env["not_public_postable_reason"]


def test_valid_synthetic_product_update_local_review_only():
    fx = _by_label("valid_synthetic_product_update")
    env = ri.build_intake_envelope(fx["input"])
    gate = ri.evaluate_readiness_gate(env)
    assert gate["gate_status"] == "READY_FOR_LOCAL_REVIEW_ONLY"
    assert gate["contentops_allowed"] is True
    assert gate["not_public_postable"] is True
    assert env["publish_ready"] is False
    assert env["approval_granted"] is False


def test_future_placeholder_needs_operator_review_or_blocked():
    fx = _by_label("future_real_artifact_placeholder")
    env = ri.build_intake_envelope(fx["input"])
    gate = ri.evaluate_readiness_gate(env)
    assert gate["gate_status"] in ("NEEDS_OPERATOR_REVIEW", "BLOCKED")
    assert gate["contentops_allowed"] is False


def test_approved_real_artifact_requires_approval_source():
    env = ri.build_intake_envelope({
        "artifact_id": "R1", "artifact_family": "product_update",
        "artifact_origin": "approved_real_artifact", "limitation_summary": "x",
        "missing_data_status": "NONE", "proxy_data_status": "NONE",
        "degradation_status": "NONE"})
    gate = ri.evaluate_readiness_gate(env)
    assert gate["gate_status"] == "BLOCKED"
    assert any("approval_source" in b for b in gate["blockers"])


def test_market_note_missing_freshness_blocked():
    fx = _by_label("blocked_market_note_missing_freshness")
    gate = ri.evaluate_readiness_gate(ri.build_intake_envelope(fx["input"]))
    assert gate["gate_status"] == "BLOCKED"
    assert any("freshness" in b for b in gate["blockers"])
    assert any("limitation_summary" in b for b in gate["blockers"])


def test_forecast_readiness_with_dqr_blocking_blocked():
    fx = _by_label("blocked_forecast_readiness_dqr_blocking")
    gate = ri.evaluate_readiness_gate(ri.build_intake_envelope(fx["input"]))
    assert gate["gate_status"] == "BLOCKED"
    assert any("DQR/data sufficiency is blocking" in b for b in gate["blockers"])


def test_missing_source_ids_blocked_when_required():
    env = ri.build_intake_envelope({
        "artifact_id": "D1", "artifact_family": "data_sufficiency",
        "artifact_origin": "synthetic_fixture", "limitation_summary": "x",
        "freshness_as_of": "2026-01-01", "missing_data_status": "NONE",
        "proxy_data_status": "NONE", "degradation_status": "NONE"})
    gate = ri.evaluate_readiness_gate(env)
    assert gate["gate_status"] == "BLOCKED"
    assert any("source_artifact_ids" in b for b in gate["blockers"])


def test_proxy_missing_degraded_data_cannot_be_hidden():
    env = ri.build_intake_envelope({
        "artifact_id": "P1", "artifact_family": "product_update",
        "artifact_origin": "synthetic_fixture", "limitation_summary": "x",
        "missing_data_status": "", "proxy_data_status": "",
        "degradation_status": ""})
    gate = ri.evaluate_readiness_gate(env)
    assert gate["gate_status"] == "BLOCKED"
    assert any("missing_data_status is hidden" in b for b in gate["blockers"])
    assert any("proxy_data_status is hidden" in b for b in gate["blockers"])


def test_synthetic_claims_approved_real_blocked():
    fx = _by_label("blocked_synthetic_claims_approved_real")
    gate = ri.evaluate_readiness_gate(ri.build_intake_envelope(fx["input"]))
    assert gate["gate_status"] == "BLOCKED"
    assert any("real/approved/public-ready" in b or "publish_ready" in b
               for b in gate["blockers"])


def test_forbidden_trading_language_blocked():
    fx = _by_label("blocked_forbidden_trading_language")
    gate = ri.evaluate_readiness_gate(ri.build_intake_envelope(fx["input"]))
    assert gate["gate_status"] == "BLOCKED"
    assert any("forbidden finance/execution language" in b for b in gate["blockers"])


def test_gate_never_grants_authority():
    for fx in FIXTURES:
        gate = ri.evaluate_readiness_gate(ri.build_intake_envelope(fx["input"]))
        assert gate["publish_ready"] is False
        assert gate["approval_granted"] is False
        assert gate["platform_action_allowed"] is False
        assert gate["not_public_postable"] is True


def test_all_fixtures_match_expected_gate():
    for fx in FIXTURES:
        gate = ri.evaluate_readiness_gate(ri.build_intake_envelope(fx["input"]))
        if fx["expected_gate"] == "NEEDS_OPERATOR_REVIEW":
            assert gate["gate_status"] in ("NEEDS_OPERATOR_REVIEW", "BLOCKED")
        else:
            assert gate["gate_status"] == fx["expected_gate"], \
                f"{fx['label']}: {gate['gate_status']} != {fx['expected_gate']}"

