import json
from pathlib import Path
from live_contentops import readiness_evidence_bundle_v6 as bundle_lane


def write_temp_inputs(tmp_path, readiness_status="DISPATCH_READINESS_BLOCKED_PENDING_REQUIREMENTS", **kwargs):
    # Mimics packets for all 10 lanes
    intent_data = {"intent_status": "READY_FOR_CANONICAL_ARTICLE", "blockers": []}
    article_data = {"article_status": "READY_FOR_RESEARCH_GROUNDING", "blockers": []}
    grounding_data = {"grounding_status": "READY_FOR_SEO_EDITORIAL", "blockers": []}
    seo_data = {"refinement_status": "READY_FOR_PLATFORM_VARIANTS", "blockers": []}
    variant_data = {"variant_status": "READY_FOR_STAGING_DROP", "blockers": [], "platform_variant_packet_id": "var_8f0a1c"}
    drop_data = {"drop_status": "READY_FOR_SOURCE_EVIDENCE_PREFLIGHT", "blockers": [], "discord_drop_packet_id": "drop_ca78"}
    preflight_data = {"preflight_status": "AWAITING_OPERATOR_EVIDENCE", "blockers": []}
    submission_data = {"submission_status": "AWAITING_OPERATOR_EVIDENCE", "blockers": [], "operator_source_evidence_submission_packet_id": "sub_1a2b"}
    gate_data = {"approval_gate_status": "APPROVAL_GATE_BLOCKED_PENDING_REQUIREMENTS", "blockers": ["evidence_incomplete"], "operator_approval_gate_packet_id": "gate_3c4d"}
    
    readiness_data = {
        "supervised_dispatch_readiness_packet_id": "readiness_34edf10af116",
        "readiness_status": readiness_status,
        "evidence_complete": kwargs.get("evidence_complete", False),
        "blockers": ["evidence_incomplete"],
        "blocked_reasons": kwargs.get("blocked_reasons", [])
    }

    int_p = tmp_path / "operator_intent_packet.json"
    int_p.write_text(json.dumps(intent_data, indent=2), encoding="utf-8")

    art_p = tmp_path / "canonical_article_packet.json"
    art_p.write_text(json.dumps(article_data, indent=2), encoding="utf-8")

    grd_p = tmp_path / "research_grounding_packet.json"
    grd_p.write_text(json.dumps(grounding_data, indent=2), encoding="utf-8")

    seo_p = tmp_path / "seo_editorial_packet.json"
    seo_p.write_text(json.dumps(seo_data, indent=2), encoding="utf-8")

    var_p = tmp_path / "platform_variant_packet.json"
    var_p.write_text(json.dumps(variant_data, indent=2), encoding="utf-8")

    drp_p = tmp_path / "discord_drop_packet.json"
    drp_p.write_text(json.dumps(drop_data, indent=2), encoding="utf-8")

    pre_p = tmp_path / "source_evidence_intake_packet.json"
    pre_p.write_text(json.dumps(preflight_data, indent=2), encoding="utf-8")

    sub_p = tmp_path / "operator_source_evidence_submission_packet.json"
    sub_p.write_text(json.dumps(submission_data, indent=2), encoding="utf-8")

    gat_p = tmp_path / "operator_approval_gate_packet.json"
    gat_p.write_text(json.dumps(gate_data, indent=2), encoding="utf-8")

    red_p = tmp_path / "supervised_dispatch_readiness_packet.json"
    red_p.write_text(json.dumps(readiness_data, indent=2), encoding="utf-8")

    return int_p, art_p, grd_p, seo_p, var_p, drp_p, pre_p, sub_p, gat_p, red_p


def test_current_supervised_dispatch_readiness_blocked_produces_bundle_blocked(tmp_path):
    int_p, art_p, grd_p, seo_p, var_p, drp_p, pre_p, sub_p, gat_p, red_p = write_temp_inputs(
        tmp_path, readiness_status="DISPATCH_READINESS_BLOCKED_PENDING_REQUIREMENTS", blocked_reasons=["readiness_blocked"]
    )
    sub, matrix, rollup, manifest, _ = bundle_lane.materialize_readiness_bundle_packets(
        int_p, art_p, grd_p, seo_p, var_p, drp_p, pre_p, sub_p, gat_p, red_p
    )
    
    assert sub["bundle_status"] == "V6_READINESS_BUNDLE_BLOCKED_BY_DISPATCH_READINESS"
    assert sub["dispatch_allowed_now"] is False
    assert "readiness_blocked" in sub["blocked_reasons"]


def test_pipeline_matrix_includes_all_ten_lanes(tmp_path):
    int_p, art_p, grd_p, seo_p, var_p, drp_p, pre_p, sub_p, gat_p, red_p = write_temp_inputs(tmp_path)
    sub, matrix, rollup, manifest, _ = bundle_lane.materialize_readiness_bundle_packets(
        int_p, art_p, grd_p, seo_p, var_p, drp_p, pre_p, sub_p, gat_p, red_p
    )
    
    lanes = [row["lane_name"] for row in matrix]
    expected = [
        "operator_intent", "canonical_substack_article", "ai_research_grounding",
        "seo_editorial_refinement", "platform_native_variants", "discord_community_drop",
        "source_evidence_preflight", "operator_source_evidence_submission",
        "operator_approval_gate", "supervised_dispatch_readiness"
    ]
    for l in expected:
        assert l in lanes


def test_blocker_rollup_includes_all_known_blockers(tmp_path):
    int_p, art_p, grd_p, seo_p, var_p, drp_p, pre_p, sub_p, gat_p, red_p = write_temp_inputs(tmp_path)
    sub, matrix, rollup, manifest, _ = bundle_lane.materialize_readiness_bundle_packets(
        int_p, art_p, grd_p, seo_p, var_p, drp_p, pre_p, sub_p, gat_p, red_p
    )
    
    expected = [
        "operator_idea_source_ref_missing", "evidence_incomplete", "payload_hash_incomplete",
        "destination_binding_incomplete", "safety_review_incomplete", "operator_approval_incomplete",
        "kill_switch_active", "live_write_authorization_missing", "outbox_creation_blocked"
    ]
    for b in expected:
        assert b in rollup


def test_project_sources_manifest(tmp_path):
    int_p, art_p, grd_p, seo_p, var_p, drp_p, pre_p, sub_p, gat_p, red_p = write_temp_inputs(tmp_path)
    sub, matrix, rollup, manifest, _ = bundle_lane.materialize_readiness_bundle_packets(
        int_p, art_p, grd_p, seo_p, var_p, drp_p, pre_p, sub_p, gat_p, red_p
    )
    
    assert "project_sources_title" in manifest
    assert len(manifest["candidate_files"]) > 0
    for f in manifest["candidate_files"]:
        assert not f.startswith("A:")
        assert not f.startswith("C:")
        assert ".json" in f or ".md" in f


def test_markdown_reports_and_summaries(tmp_path):
    int_p, art_p, grd_p, seo_p, var_p, drp_p, pre_p, sub_p, gat_p, red_p = write_temp_inputs(tmp_path)
    sub, matrix, rollup, manifest, _ = bundle_lane.materialize_readiness_bundle_packets(
        int_p, art_p, grd_p, seo_p, var_p, drp_p, pre_p, sub_p, gat_p, red_p
    )
    
    summary = bundle_lane.generate_operator_review_summary_markdown(sub)
    assert "NO-PUBLICATION WARNING" in summary
    assert "Why Dispatch Remains Blocked" in summary
    assert "strictly blocked" in summary.lower()
    
    actions = bundle_lane.generate_next_operator_actions_markdown(sub)
    assert "future, supervised operations required by manual operators" in actions.lower()
    assert "Source Evidence Actions" in actions
    assert "Payload Hash Actions" in actions


def test_packet_contains_no_sensitive_values(tmp_path):
    int_p, art_p, grd_p, seo_p, var_p, drp_p, pre_p, sub_p, gat_p, red_p = write_temp_inputs(tmp_path)
    sub, matrix, rollup, manifest, _ = bundle_lane.materialize_readiness_bundle_packets(
        int_p, art_p, grd_p, seo_p, var_p, drp_p, pre_p, sub_p, gat_p, red_p
    )
    
    for obj in [sub, matrix, rollup, manifest]:
        dump = json.dumps(obj)
        assert "discord.com/api/webhooks" not in dump
        assert "token_value" not in dump.lower()
        assert "cookie_value" not in dump.lower()
        assert "secret_key" not in dump.lower() or "secret_keys_present" in dump
        if isinstance(obj, dict):
            assert obj.get("raw_secret_output", False) is False
            assert obj.get("webhook_url_printed", False) is False


def test_module_contains_no_forbidden_behavior():
    attrs = dir(bundle_lane)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
