import os

import pytest

from live_contentops import pipeline_trace as pt
from live_contentops import pipeline_trace_fixtures as ptf


SCENARIOS = ptf.load_scenarios()


def _by_label(label):
    return next(s for s in SCENARIOS if s["label"] == label)


def _trace(label):
    return pt.build_pipeline_trace(_by_label(label)["input"])


def test_trace_record_has_all_required_fields():
    rec = _trace("A_valid_synthetic_product_update")
    required = [
        "trace_id", "intake_id", "artifact_id", "artifact_family", "artifact_type",
        "artifact_origin", "intake_gate_status", "bridge_route", "bridge_status",
        "packet_input_allowed", "packet_input_projection", "packet_export_status",
        "audit_status", "review_queue_status", "operator_decision_status",
        "review_history_status", "registry_status", "ledger_status",
        "dashboard_handoff_status", "bundle_refresh_status", "blockers", "warnings",
        "lineage_refs", "source_artifact_ids", "freshness_as_of", "limitation_summary",
        "dqr_status", "data_sufficiency_status", "forecast_readiness_status",
        "proxy_data_status", "missing_data_status", "degradation_status",
        "not_public_postable_reason", "local_only", "advisory_only", "fixture_only",
        "requires_real_alpha_artifacts_now", "human_review_required",
        "approval_granted", "publish_ready", "provider_call_allowed",
        "search_call_allowed", "platform_action_allowed",
    ]
    for key in required:
        assert key in rec, f"missing field: {key}"


def test_all_required_scenarios_exist():
    labels = {s["label"] for s in SCENARIOS}
    for required in ("A_valid_synthetic_product_update",
                     "B_future_real_artifact_placeholder",
                     "C_approved_real_artifact_contract_sample",
                     "D_blocked_forecast_readiness_dqr_blocking",
                     "E_synthetic_attempting_approved_real",
                     "F_market_note_missing_freshness",
                     "G_forbidden_trading_language"):
        assert required in labels, f"missing scenario: {required}"


def test_valid_synthetic_reaches_local_review_not_public():
    rec = _trace("A_valid_synthetic_product_update")
    assert rec["packet_input_allowed"] is True
    assert rec["registry_status"] == "LOCAL_REVIEW_ONLY"
    assert rec["dashboard_handoff_status"] == "LOCAL_REVIEW_ONLY"
    assert rec["publish_ready"] is False
    assert rec["not_public_postable_reason"]


def test_future_placeholder_cannot_claim_real_approval():
    rec = _trace("B_future_real_artifact_placeholder")
    assert rec["bridge_route"] == pt.apb.FUTURE_REAL_ARTIFACT_PLACEHOLDER_ROUTE
    assert rec["real_artifact_route_allowed"] is False
    assert rec["approval_granted"] is False


def test_approved_real_contract_sample_requires_evidence_and_disclaimer():
    sc = _by_label("C_approved_real_artifact_contract_sample")
    assert sc.get("fixture_disclaimer")
    rec = pt.build_pipeline_trace(sc["input"])
    assert rec["bridge_route"] == pt.apb.APPROVED_REAL_ARTIFACT_CONTRACT_ROUTE
    assert rec["publish_ready"] is False
    assert rec["not_public_postable_reason"]
    # Without approval evidence it must NOT use the approved-real route.
    bad = dict(sc["input"])
    bad.pop("approval_source", None)
    bad["intake_id"] = "trace_approved_no_evidence"
    rec_bad = pt.build_pipeline_trace(bad)
    assert rec_bad["bridge_route"] == pt.apb.BLOCKED_ROUTE


@pytest.mark.parametrize("label", [
    "D_blocked_forecast_readiness_dqr_blocking",
    "E_synthetic_attempting_approved_real",
    "F_market_note_missing_freshness",
    "G_forbidden_trading_language"])
def test_blocked_scenarios_cannot_become_packet_input(label):
    rec = _trace(label)
    assert rec["bridge_route"] == pt.apb.BLOCKED_ROUTE
    assert rec["packet_input_allowed"] is False
    # All downstream stages must be NOT_REACHED.
    for stage in ("packet_export_status", "audit_status", "review_queue_status",
                  "registry_status", "ledger_status", "dashboard_handoff_status"):
        assert rec[stage] == "NOT_REACHED"


def test_dqr_blocking_cannot_be_bypassed():
    rec = _trace("D_blocked_forecast_readiness_dqr_blocking")
    assert rec["intake_gate_status"] == "BLOCKED"
    assert rec["packet_input_allowed"] is False


def test_synthetic_attempting_approved_real_blocked():
    rec = _trace("E_synthetic_attempting_approved_real")
    assert rec["bridge_route"] == pt.apb.BLOCKED_ROUTE
    assert rec["synthetic_route_guard_status"] == "BLOCKED"


def test_market_note_missing_freshness_blocked():
    rec = _trace("F_market_note_missing_freshness")
    assert rec["bridge_route"] == pt.apb.BLOCKED_ROUTE


def test_forbidden_trading_language_blocked():
    rec = _trace("G_forbidden_trading_language")
    assert rec["bridge_route"] == pt.apb.BLOCKED_ROUTE
    assert rec["packet_input_allowed"] is False


def test_packet_projection_preserves_fields():
    rec = _trace("C_approved_real_artifact_contract_sample")
    proj = rec["packet_input_projection"]
    assert proj["source_lineage_refs"] == rec["lineage_refs"]
    assert proj["content_type"] == rec["artifact_type"]
    assert proj["limitation_summary"] == rec["limitation_summary"]
    assert proj["freshness_as_of"] == rec["freshness_as_of"]
    assert proj["artifact_origin"] == rec["artifact_origin"]
    assert proj["bridge_route"] == rec["bridge_route"]
    assert proj["dqr_status"] == rec["dqr_status"]
    assert proj["data_sufficiency_status"] == rec["data_sufficiency_status"]
    assert proj["not_public_postable_reason"] == rec["not_public_postable_reason"]
    for flag in ("approval_granted", "publish_ready", "provider_call_allowed",
                 "search_call_allowed", "platform_action_allowed"):
        assert proj[flag] is False


def test_downstream_trace_exists_for_local_review_scenarios():
    for label in ("A_valid_synthetic_product_update",
                  "B_future_real_artifact_placeholder",
                  "C_approved_real_artifact_contract_sample"):
        rec = _trace(label)
        assert rec["review_queue_status"] == "LOCAL_REVIEW_ONLY"
        assert rec["operator_decision_status"] == "PENDING_MANUAL_REVIEW"
        assert rec["review_history_status"] == "LOCAL_REVIEW_ONLY"
        assert rec["registry_status"] == "LOCAL_REVIEW_ONLY"
        assert rec["ledger_status"] == "LOCAL_REVIEW_ONLY"
        assert rec["dashboard_handoff_status"] == "LOCAL_REVIEW_ONLY"


def test_all_traces_not_public_postable_and_no_authority():
    for t in ptf.build_all_traces():
        assert t["publish_ready"] is False
        assert t["approval_granted"] is False
        assert t["platform_action_allowed"] is False
        assert t["provider_call_allowed"] is False
        assert t["search_call_allowed"] is False
        assert t["not_public_postable_reason"]


def test_validate_blocks_gate_blocked_with_downstream_reached():
    rec = _trace("A_valid_synthetic_product_update")
    rec["packet_input_allowed"] = False  # contradiction: downstream still LOCAL_REVIEW
    res = pt.validate_pipeline_trace(rec)
    assert res["status"] == "BLOCKED"
    assert any("downstream stage" in b for b in res["blockers"])


def test_validate_clean_for_valid_trace():
    rec = _trace("A_valid_synthetic_product_update")
    res = pt.validate_pipeline_trace(rec)
    assert res["status"] in ("PASS", "WARNING")
    assert res["blockers"] == []


def test_validate_clean_for_all_traces():
    for t in ptf.build_all_traces():
        res = pt.validate_pipeline_trace(t)
        assert res["blockers"] == [], f"{t['trace_id']}: {res['blockers']}"


def test_summary_counts():
    s = pt.build_summary()
    assert s["scenario_count"] == 7
    assert s["blocked_scenario_count"] == 4
    assert s["local_review_only_scenario_count"] == 3
    assert s["fixture_only"] is True
    assert s["requires_real_alpha_artifacts_now"] is False
    assert s["all_fixture_outputs_not_public_postable"] is True


def test_refreshed_0072_bundle_docs_exist():
    docs = os.path.join(os.path.dirname(__file__), "..", "docs")
    for name in ("NEW_CHAT_CONTINUATION_AFTER_0072.md",
                 "UPLOAD_BUNDLE_MANIFEST_AFTER_0072.md",
                 "PROJECT_SOURCE_EXPORT_AFTER_0072.md",
                 "TASK_CONTENTOPS_0072_EXTREME_LOCAL_REAL_ARTIFACT_PIPELINE_TRACE_REVIEW_PACKET_AND_BUNDLE_REFRESH_V0.md"):
        path = os.path.join(docs, name)
        if not os.path.isfile(path):
            path = os.path.join(docs, "archive", "stale_prelaunch_reset_0174CG", name)
        assert os.path.isfile(path), f"missing doc: {name}"

