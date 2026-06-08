import json
import os

import pytest

from live_contentops import grounded_research_brief as grb

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
FIXT_DIR = os.path.join(REPO_ROOT, "fixtures", "grounded_research_briefs")
SCHEMA_PATH = os.path.join(REPO_ROOT, "schemas", "grounded_research_brief.schema.json")


def _fixt(name):
    return os.path.join(FIXT_DIR, name)


def test_schema_file_exists_and_parses():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["title"] == "GroundedResearchBrief"
    assert "brief_id" in data["required"]
    assert "safety_review" in data["required"]


def test_schema_matches_jsonschema_for_valid_fixture():
    jsonschema = pytest.importorskip("jsonschema")
    schema = grb.load_schema()
    with open(_fixt("valid_minimal_grounded_news_context.json"), "r", encoding="utf-8") as f:
        brief = json.load(f)
    jsonschema.validate(instance=brief, schema=schema)


def test_valid_minimal_brief_passes():
    res = grb.validate_brief_file(_fixt("valid_minimal_grounded_news_context.json"))
    assert res["valid"] is True, res["errors"]
    assert res["errors"] == []


def test_invalid_missing_source_url_fails():
    res = grb.validate_brief_file(_fixt("invalid_missing_source_url.json"))
    assert res["valid"] is False
    assert any(e.startswith("source_missing_field:url") for e in res["errors"])


def test_invalid_market_signal_claim_fails():
    res = grb.validate_brief_file(_fixt("invalid_market_signal_claim.json"))
    assert res["valid"] is False
    assert any(e.startswith("claim_forbidden_language") for e in res["errors"])


def test_invalid_artifact_backed_claim_fails():
    res = grb.validate_brief_file(_fixt("invalid_artifact_backed_claim_without_artifact.json"))
    assert res["valid"] is False
    assert any(e.startswith("claim_implies_alpha_output") for e in res["errors"])


def test_lane_must_be_pre_alpha_general_process():
    base = json.load(open(_fixt("valid_minimal_grounded_news_context.json"), encoding="utf-8"))
    base["lane"] = "future_artifact_backed"
    res = grb.validate_brief(base)
    assert res["valid"] is False
    assert "lane_must_be_pre_alpha_general_process" in res["errors"]


def test_public_postable_true_is_blocked():
    base = json.load(open(_fixt("valid_minimal_grounded_news_context.json"), encoding="utf-8"))
    base["safety_review"]["public_postable"] = True
    res = grb.validate_brief(base)
    assert res["valid"] is False
    assert "safety_flag_must_be_false:public_postable" in res["errors"]


def test_publish_ready_true_is_blocked():
    base = json.load(open(_fixt("valid_minimal_grounded_news_context.json"), encoding="utf-8"))
    base["safety_review"]["publish_ready"] = True
    res = grb.validate_brief(base)
    assert res["valid"] is False
    assert "safety_flag_must_be_false:publish_ready" in res["errors"]


def test_provider_search_platform_flags_blocked():
    for flag in ("provider_call_used_by_repo", "search_call_used_by_repo",
                 "platform_action_used_by_repo"):
        base = json.load(open(_fixt("valid_minimal_grounded_news_context.json"), encoding="utf-8"))
        base["safety_review"][flag] = True
        res = grb.validate_brief(base)
        assert res["valid"] is False
        assert ("safety_flag_must_be_false:%s" % flag) in res["errors"]


def test_forbidden_claim_type_is_blocked():
    base = json.load(open(_fixt("valid_minimal_grounded_news_context.json"), encoding="utf-8"))
    base["claims"][0]["claim_type"] = "forbidden_claim"
    res = grb.validate_brief(base)
    assert res["valid"] is False
    assert any(e.startswith("claim_is_forbidden_claim") for e in res["errors"])


def test_blocked_claim_risk_is_blocked():
    base = json.load(open(_fixt("valid_minimal_grounded_news_context.json"), encoding="utf-8"))
    base["claims"][0]["claim_risk"] = "blocked"
    res = grb.validate_brief(base)
    assert res["valid"] is False
    assert any(e.startswith("claim_risk_blocked") for e in res["errors"])


def test_current_factual_claim_requires_known_source():
    base = json.load(open(_fixt("valid_minimal_grounded_news_context.json"), encoding="utf-8"))
    # clm_2 is current_factual_claim; point it at an unknown source.
    base["claims"][1]["source_ids"] = ["does_not_exist"]
    res = grb.validate_brief(base)
    assert res["valid"] is False
    assert any(e.startswith("claim_source_id_unknown") for e in res["errors"])


def test_market_action_words_blocked_in_claim_text():
    base = json.load(open(_fixt("valid_minimal_grounded_news_context.json"), encoding="utf-8"))
    base["claims"][0]["claim_text"] = "Set a price target and go short here."
    res = grb.validate_brief(base)
    assert res["valid"] is False
    assert any(e.startswith("claim_forbidden_language") for e in res["errors"])
