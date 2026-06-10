
import pytest
import os
import json
from live_contentops.llm_assisted_draft_review import validate_review_packet_file

FIX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "llm_assisted_draft_reviews")

def _fixt(name):
    return os.path.join(FIX_DIR, name)

def test_valid_packet():
    res = validate_review_packet_file(_fixt("valid_review_only_grounded_news_draft.json"))
    assert res["valid"] is True

def test_invalid_publish_ready_true():
    res = validate_review_packet_file(_fixt("invalid_publish_ready_true.json"))
    assert res["valid"] is False
    assert any("safety_flag_must_be_false:publish_ready" in r for r in res["errors"])

def test_invalid_uncited_current_claim():
    res = validate_review_packet_file(_fixt("invalid_uncited_current_claim.json"))
    assert res["valid"] is False
    assert any("claim_missing_citation:clm-1" in r for r in res["errors"])

def test_invalid_forbidden_signal_language():
    res = validate_review_packet_file(_fixt("invalid_forbidden_signal_language.json"))
    assert res["valid"] is False
    assert any("forbidden_signal_in_draft:hold" in r for r in res["errors"])

def test_invalid_artifact_backed_claim():
    res = validate_review_packet_file(_fixt("invalid_artifact_backed_claim.json"))
    assert res["valid"] is False
    assert any("forbidden_alpha_implication_in_draft:artifact_id" in r for r in res["errors"])

def test_invalid_source_not_in_grounded_brief():
    res = validate_review_packet_file(_fixt("invalid_source_not_in_grounded_brief.json"))
    assert res["valid"] is False
    assert any("claim_source_not_in_grounded_brief:clm-1:src-unknown" in r for r in res["errors"])

def test_invalid_llm_provider_call_used_by_repo():
    res = validate_review_packet_file(_fixt("invalid_llm_provider_call_used_by_repo.json"))
    assert res["valid"] is False
    assert any("repo_must_not_call_llm" in r for r in res["errors"])
