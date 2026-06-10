import os
import json
from live_contentops.llm_content_writer_workbench import (
    validate_llm_content_writer_workbench_packet,
    summary,
)

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "llm_content_writer_workbench")


def _load(name):
    with open(os.path.join(FIX_DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _valid():
    return _load("llm_content_writer_workbench_valid.json")


def test_valid_packet_passes():
    res = validate_llm_content_writer_workbench_packet(_valid())
    assert res["valid"] is True
    assert res["errors"] == []


def test_invalid_provider_call_allowed():
    res = validate_llm_content_writer_workbench_packet(_load("llm_content_writer_workbench_invalid_provider_call.json"))
    assert res["valid"] is False
    assert any("provider_call_allowed_by_repo_must_be_false" in e for e in res["errors"])


def test_invalid_repo_executes_prompt():
    p = _valid()
    p["prompt_pack_templates"][0]["repo_executes_prompt"] = True
    res = validate_llm_content_writer_workbench_packet(p)
    assert res["valid"] is False
    assert any("repo_executes_prompt_must_be_false" in e for e in res["errors"])


def test_invalid_public_ready_allowed():
    res = validate_llm_content_writer_workbench_packet(_load("llm_content_writer_workbench_invalid_public_ready.json"))
    assert res["valid"] is False
    assert any("output_public_ready_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_publish_ready():
    p = _valid()
    p["output_policy"]["publish_ready"] = True
    res = validate_llm_content_writer_workbench_packet(p)
    assert res["valid"] is False
    assert any("publish_ready_must_be_false" in e for e in res["errors"])


def test_invalid_auto_approval_allowed():
    p = _valid()
    p["output_policy"]["auto_approval_allowed"] = True
    res = validate_llm_content_writer_workbench_packet(p)
    assert res["valid"] is False
    assert any("auto_approval_allowed_must_be_false" in e for e in res["errors"])


def test_invalid_platform_export_final_allowed():
    p = _valid()
    p["output_policy"]["platform_export_final_allowed_now"] = True
    res = validate_llm_content_writer_workbench_packet(p)
    assert res["valid"] is False
    assert any("platform_export_final_allowed_now_must_be_false" in e for e in res["errors"])


def test_invalid_manual_review_required_false():
    res = validate_llm_content_writer_workbench_packet(_load("llm_content_writer_workbench_invalid_missing_manual_review.json"))
    assert res["valid"] is False
    assert any("output_manual_review_required_must_be_true" in e for e in res["errors"])


def test_invalid_not_public_postable_false():
    p = _valid()
    p["output_policy"]["not_public_postable"] = False
    res = validate_llm_content_writer_workbench_packet(p)
    assert res["valid"] is False


def test_invalid_signal_language():
    res = validate_llm_content_writer_workbench_packet(_load("llm_content_writer_workbench_invalid_signal_language.json"))
    assert res["valid"] is False
    assert any("unsafe_signal_detected" in e for e in res["errors"])


def test_invalid_alpha_claim_without_artifact():
    res = validate_llm_content_writer_workbench_packet(_load("llm_content_writer_workbench_invalid_artifact_claim.json"))
    assert res["valid"] is False
    assert any("alpha_claim_without_real_artifact" in e for e in res["errors"])


def test_invalid_unsupported_numeric_claim():
    p = _valid()
    p["angle_taxonomy"].append({"angle_id": "bad", "note": "fake alpha performance numbers"})
    res = validate_llm_content_writer_workbench_packet(p)
    assert res["valid"] is False
    assert any("unsupported_numeric_market_claim" in e for e in res["errors"])


def test_invalid_missing_source_requirement():
    res = validate_llm_content_writer_workbench_packet(_load("llm_content_writer_workbench_invalid_missing_source_requirement.json"))
    assert res["valid"] is False
    assert any("source_references_required_must_be_true" in e for e in res["errors"])


def test_prompt_templates_are_template_only_and_external_use_only():
    p = _valid()
    for t in p["prompt_pack_templates"]:
        assert t["template_only"] is True
        assert t["external_llm_use_only"] is True
        assert t["provider_call_allowed_by_repo"] is False
        assert t["repo_executes_prompt"] is False
    p["prompt_pack_templates"][0]["template_only"] = False
    res = validate_llm_content_writer_workbench_packet(p)
    assert res["valid"] is False
    assert any("template_only_must_be_true" in e for e in res["errors"])


def test_summary_all_live_external_counters_zero_or_false():
    s = summary()
    zero_counts = [
        "provider_call_enabled_count",
        "repo_prompt_execution_enabled_count",
        "public_ready_allowed_count",
        "publish_ready_count",
        "auto_approval_enabled_count",
        "platform_export_final_enabled_count",
        "newsletter_send_enabled_count",
        "cms_integration_enabled_count",
        "unsafe_language_count",
        "unsupported_numeric_claim_count",
        "artifact_claim_without_real_artifact_count",
    ]
    for k in zero_counts:
        assert s[k] == 0
    assert s["manual_review_required_all"] is True
    assert s["not_public_postable_all"] is True
    false_flags = [
        "provider_call_used_by_repo",
        "search_call_used_by_repo",
        "network_call_used_by_repo",
        "platform_action_used_by_repo",
        "credential_or_env_read_used",
        "scheduler_accessed",
        "scraping_allowed_now",
        "autonomous_reply_dm_enabled",
    ]
    for k in false_flags:
        assert s[k] is False
    assert s["allowed_content_type_count"] == 10
    json.dumps(s)


def test_packet_status_pass_with_errors_flagged():
    p = _valid()
    p["output_policy"]["publish_ready"] = True
    p["packet_status"] = "pass"
    res = validate_llm_content_writer_workbench_packet(p)
    assert res["valid"] is False
    assert any("packet_status_pass_but_errors_exist" in e for e in res["errors"])
