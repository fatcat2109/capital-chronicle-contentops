# -*- coding: utf-8 -*-
"""Boundary tests for the Daily Pipeline Fresh Codex Audit packet."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs" / "automation" / "DAILY_PIPELINE_FRESH_CODEX_AUDIT_V0"


def load_json(relative_path: str):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def normalized(value: str) -> str:
    return value.replace("\\", "/")


def test_audit_artifacts_exist_and_gate_passes():
    expected = [
        "README.md",
        "pipeline_audit_report_v0.md",
        "pipeline_audit_report_v0.json",
        "live_readiness_gate_v0.json",
        "run_evidence_v0.json",
    ]
    for name in expected:
        assert (AUDIT_DIR / name).exists(), name

    gate = load_json("docs/automation/DAILY_PIPELINE_FRESH_CODEX_AUDIT_V0/live_readiness_gate_v0.json")
    assert gate["pipeline_lineage_pass"] is True
    assert gate["candidate_only_state_pass"] is True
    assert gate["no_secret_read_pass"] is True
    assert gate["no_live_action_pass"] is True
    assert gate["no_platform_payload_pass"] is True
    assert gate["no_dispatch_pass"] is True
    assert gate["no_exact_numeric_truth_pass"] is True
    assert gate["telegram_meaningful_text_pass"] is True
    assert gate["media_generation_blocked_pass"] is True
    assert gate["source_lineage_repair_performed"] is True
    assert gate["ready_for_separate_operator_approved_live_run"] is True
    assert gate["live_run_must_be_separate_task"] is True
    assert gate["blockers"] == []

    report = load_json("docs/automation/DAILY_PIPELINE_FRESH_CODEX_AUDIT_V0/pipeline_audit_report_v0.json")
    assert report["readiness_classification"] == "PASS_READY_FOR_SEPARATE_OPERATOR_APPROVED_LIVE_RUN"
    assert report["exact_next_recommended_task"] == "TASK_CONTENTOPS_OPERATOR_APPROVED_SUPERVISED_LIVE_DAILY_RUN_V0"
    assert len(report["stages"]) == 9
    assert report["blockers"] == []


def test_daily_pipeline_lineage_and_candidate_boundaries():
    raw_headlines = load_json("docs/automation/DAILY_X_CDP_HEADLINE_CAPTURE_PACKET_V0/headlines_raw_v0.json")
    raw_ids = {row["headline_id"] for row in raw_headlines}

    selection = load_json("docs/automation/DAILY_HEADLINE_CLUSTER_RANK_ARTICLE_IDEA_PACKET_V0/article_idea_selection_v0.json")
    assert selection["selected_idea_id"] == "idea_macro_policy_rates_liquidity_20260709"
    assert selection["selected_topic_family"] == "macro_policy_rates_liquidity"
    assert all(headline_id in raw_ids for headline_id in selection["supporting_headline_ids"])

    support = load_json("docs/automation/DAILY_DATABASE_SUPPORT_PACKET_V0/database_support_packet_v0.json")
    assert support["selected_idea_id"] == selection["selected_idea_id"]
    assert support["support_families_resolved"] == []
    assert "Global Central Bank Liquidity Measures" in support["support_families_missing"]
    assert support["ready_for_article_draft"] is False
    assert support["external_fetch_performed"] is False
    assert support["exact_numeric_claims_made"] is False

    gap_plan = load_json("docs/automation/DAILY_DATABASE_SUPPORT_GAP_REPAIR_PLAN_V0/support_gap_repair_plan_v0.json")
    assert gap_plan["selected_idea_id"] == selection["selected_idea_id"]
    assert gap_plan["article_draft_blocked"] is True
    assert gap_plan["article_draft_allowed_as_candidate_only"] is False
    assert gap_plan["main_repo_mutated"] is False
    assert gap_plan["external_fetch_performed"] is False

    reselection = load_json("docs/automation/SUPPORT_AWARE_ARTICLE_IDEA_RESELECTION_V0/reselection_packet_v0.json")
    assert reselection["original_idea_blocked"] is True
    assert reselection["do_not_draft_original_idea"] is True
    assert reselection["original_selected_idea"]["selected_idea_id"] == selection["selected_idea_id"]
    assert reselection["reselected_idea_id"] == "idea_energy_commodities_20260709"
    assert reselection["reselected_topic_family"] == "energy_commodities"
    assert all(headline_id in raw_ids for headline_id in reselection["supporting_headline_ids"])
    assert reselection["no_dispatch_confirmation"] is True

    brief = load_json("docs/automation/DAILY_ARTICLE_BRIEF_GENERATION_V0/article_brief_v0.json")
    assert normalized(brief["source_reselection_packet"]) == "docs/automation/SUPPORT_AWARE_ARTICLE_IDEA_RESELECTION_V0/reselection_packet_v0.json"
    assert brief["selected_idea_id"] == reselection["reselected_idea_id"]
    assert brief["topic_family"] == "energy_commodities"
    assert brief["draft_readiness"] == "candidate_only"
    assert brief["no_dispatch_confirmation"] is True

    draft_meta = load_json("docs/automation/DAILY_SEO_ARTICLE_DRAFTING_V0/article_draft_metadata_v0.json")
    assert normalized(draft_meta["source_article_brief"]) == "docs/automation/DAILY_ARTICLE_BRIEF_GENERATION_V0/article_brief_v0.json"
    assert draft_meta["selected_idea_id"] == brief["selected_idea_id"]
    assert draft_meta["draft_status"] == "candidate_only"
    assert draft_meta["platform_payload_created"] is False
    assert draft_meta["dispatch_ready"] is False
    assert draft_meta["exact_numeric_claims_made"] is False
    assert draft_meta["financial_advice_detected"] is False

    media = load_json("docs/automation/DAILY_MEDIA_PLAN_SPEC_V0/media_plan_spec_v0.json")
    assert normalized(media["source_article_draft"]) == "docs/automation/DAILY_SEO_ARTICLE_DRAFTING_V0/article_draft_v0.md"
    assert media["draft_status"] == "candidate_only"
    assert media["media_generation_status"] == "planning_only"
    assert media["generation_allowed_now"] is False
    assert media["chart_render_allowed_now"] is False
    assert media["platform_payload_created"] is False
    assert media["dispatch_ready"] is False

    platform = load_json("docs/automation/DAILY_PLATFORM_VARIANT_CANDIDATE_COPY_V0/platform_variant_candidate_copy_v0.json")
    assert normalized(platform["source_article_draft"]) == "docs/automation/DAILY_SEO_ARTICLE_DRAFTING_V0/article_draft_v0.md"
    assert normalized(platform["source_media_plan"]) == "docs/automation/DAILY_MEDIA_PLAN_SPEC_V0/media_plan_spec_v0.json"
    assert "article_brief_v0.json" not in normalized(platform["source_article_draft"])
    assert platform["draft_status"] == "candidate_only"
    assert platform["platform_copy_status"] == "candidate_only"
    assert platform["platform_payload_created"] is False
    assert platform["dispatch_allowed_now"] is False

    telegram = next(v for v in platform["variants"] if v["platform"] == "telegram")
    assert len(telegram["body_copy"].split()) > 20
    assert telegram["dispatch_allowed_now"] is False


def test_daily_pipeline_safety_artifacts_remain_non_live():
    draft_safety = load_json("docs/automation/DAILY_SEO_ARTICLE_DRAFTING_V0/draft_safety_review_v0.json")
    media_plan = load_json("docs/automation/DAILY_MEDIA_PLAN_SPEC_V0/media_plan_spec_v0.json")
    media_safety = load_json("docs/automation/DAILY_MEDIA_PLAN_SPEC_V0/media_safety_review_v0.json")
    platform_safety = load_json("docs/automation/DAILY_PLATFORM_VARIANT_CANDIDATE_COPY_V0/platform_copy_safety_review_v0.json")
    platform_evidence = load_json("docs/automation/DAILY_PLATFORM_VARIANT_CANDIDATE_COPY_V0/run_evidence_v0.json")

    assert draft_safety["candidate_only"] is True
    assert draft_safety["platform_payload_created"] is False
    assert draft_safety["dispatch_ready"] is False
    assert draft_safety["exact_numeric_claims_made"] is False
    assert draft_safety["financial_advice_detected"] is False
    assert draft_safety["trading_signal_detected"] is False

    assert media_safety["actual_media_generated"] is False
    assert media_safety["chart_rendered"] is False
    assert media_plan["generation_allowed_now"] is False
    assert media_plan["chart_render_allowed_now"] is False
    assert media_safety["platform_payload_created"] is False
    assert media_safety["dispatch_ready"] is False

    assert platform_safety["candidate_only"] is True
    assert platform_safety["platform_payload_created"] is False
    assert platform_safety["dispatch_allowed_now"] is False
    assert platform_safety["actual_media_generated"] is False
    assert platform_safety["exact_numeric_claims_made"] is False
    assert platform_safety["financial_advice_detected"] is False
    assert platform_safety["trading_signal_detected"] is False
    assert platform_safety["price_target_detected"] is False
    assert platform_safety["telegram_has_meaningful_text_body"] is True

    assert normalized(platform_evidence["source_article_draft"]) == "docs/automation/DAILY_SEO_ARTICLE_DRAFTING_V0/article_draft_v0.md"
    assert platform_evidence["no_actual_media_generated_confirmation"] is True
    assert platform_evidence["no_platform_api_confirmation"] is True
    assert platform_evidence["no_platform_write_confirmation"] is True
    assert platform_evidence["no_dispatch_confirmation"] is True
    assert platform_evidence["no_raw_secret_read_confirmation"] is True


def test_audit_packet_contains_no_secret_shaped_material():
    secret_patterns = [
        re.compile(r"sk-[A-Za-z0-9]{16,}"),
        re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
        re.compile(r"ghp_[A-Za-z0-9]{20,}"),
        re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.IGNORECASE),
        re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b"),
    ]
    scanned_files = list(AUDIT_DIR.glob("*")) + list((ROOT / "docs" / "automation" / "DAILY_PLATFORM_VARIANT_CANDIDATE_COPY_V0").glob("*.json"))
    for path in scanned_files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in secret_patterns:
            assert pattern.search(text) is None, path
