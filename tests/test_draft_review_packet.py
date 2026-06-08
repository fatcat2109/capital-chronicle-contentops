import json
import os

import pytest

from live_contentops import draft_review_packet as drp

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
FIXT_DIR = os.path.join(REPO_ROOT, "fixtures", "draft_review_packets")
SCHEMA_PATH = os.path.join(REPO_ROOT, "schemas", "draft_review_packet.schema.json")


def _fixt(name):
    return os.path.join(FIXT_DIR, name)


def _load(name):
    with open(_fixt(name), "r", encoding="utf-8") as f:
        return json.load(f)


def test_schema_file_exists_and_parses():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["title"] == "DraftReviewPacket"
    assert "packet_id" in data["required"]
    assert "safety_review" in data["required"]
    assert "verdict" in data["required"]


def test_schema_matches_jsonschema_for_valid_fixture():
    jsonschema = pytest.importorskip("jsonschema")
    schema = drp.load_schema()
    packet = _load("valid_review_only_grounded_news_draft.json")
    jsonschema.validate(instance=packet, schema=schema)


def test_valid_review_only_packet_passes():
    res = drp.validate_packet_file(_fixt("valid_review_only_grounded_news_draft.json"))
    assert res["valid"] is True, res["errors"]
    assert res["errors"] == []


def test_invalid_publish_ready_true_fails():
    res = drp.validate_packet_file(_fixt("invalid_publish_ready_true.json"))
    assert res["valid"] is False
    assert "safety_flag_must_be_false:publish_ready" in res["errors"]


def test_invalid_uncited_current_claim_fails():
    res = drp.validate_packet_file(_fixt("invalid_uncited_current_claim.json"))
    assert res["valid"] is False
    assert any(e.startswith("claim_missing_citation") for e in res["errors"])


def test_invalid_forbidden_signal_language_fails():
    res = drp.validate_packet_file(_fixt("invalid_forbidden_signal_language.json"))
    assert res["valid"] is False
    assert "draft_text_forbidden_language" in res["errors"]


def test_invalid_artifact_backed_claim_fails():
    res = drp.validate_packet_file(_fixt("invalid_artifact_backed_claim.json"))
    assert res["valid"] is False
    assert "draft_text_implies_alpha_output" in res["errors"]


def test_lane_must_be_pre_alpha_general_process():
    base = _load("valid_review_only_grounded_news_draft.json")
    base["lane"] = "future_artifact_backed"
    res = drp.validate_packet(base)
    assert res["valid"] is False
    assert "lane_must_be_pre_alpha_general_process" in res["errors"]


def test_public_postable_true_is_blocked():
    base = _load("valid_review_only_grounded_news_draft.json")
    base["safety_review"]["public_postable"] = True
    res = drp.validate_packet(base)
    assert res["valid"] is False
    assert "safety_flag_must_be_false:public_postable" in res["errors"]


def test_review_only_false_is_blocked():
    base = _load("valid_review_only_grounded_news_draft.json")
    base["safety_review"]["review_only"] = False
    res = drp.validate_packet(base)
    assert res["valid"] is False
    assert "safety_flag_must_be_true:review_only" in res["errors"]


def test_jim_final_review_required_false_is_blocked():
    base = _load("valid_review_only_grounded_news_draft.json")
    base["safety_review"]["jim_final_review_required"] = False
    res = drp.validate_packet(base)
    assert res["valid"] is False
    assert "safety_flag_must_be_true:jim_final_review_required" in res["errors"]


def test_artifact_backed_true_is_blocked():
    base = _load("valid_review_only_grounded_news_draft.json")
    base["safety_review"]["artifact_backed"] = True
    res = drp.validate_packet(base)
    assert res["valid"] is False
    assert "safety_flag_must_be_false:artifact_backed" in res["errors"]


def test_provider_search_platform_flags_blocked():
    for flag in ("provider_call_used_by_repo", "search_call_used_by_repo",
                 "platform_action_used_by_repo"):
        base = _load("valid_review_only_grounded_news_draft.json")
        base["safety_review"][flag] = True
        res = drp.validate_packet(base)
        assert res["valid"] is False
        assert ("safety_flag_must_be_false:%s" % flag) in res["errors"]


def test_brief_not_validated_is_blocked():
    base = _load("valid_review_only_grounded_news_draft.json")
    base["linked_research_brief"]["brief_validated"] = False
    res = drp.validate_packet(base)
    assert res["valid"] is False
    assert "linked_research_brief_not_validated" in res["errors"]


def test_source_linkage_unknown_source_blocked():
    base = _load("valid_review_only_grounded_news_draft.json")
    # clm_2 is a current_factual_claim citing src_bls_cpi; remove that from
    # declared source_references_used so the linkage check fails.
    base["source_references_used"] = []
    res = drp.validate_packet(base)
    assert res["valid"] is False
    assert any(e.startswith("claim_source_not_in_brief") for e in res["errors"])


def test_forbidden_claim_type_is_blocked():
    base = _load("valid_review_only_grounded_news_draft.json")
    base["claim_reviews"][0]["claim_type"] = "forbidden_claim"
    res = drp.validate_packet(base)
    assert res["valid"] is False
    assert any(e.startswith("claim_is_forbidden_claim") for e in res["errors"])


def test_blocked_risk_level_is_blocked():
    base = _load("valid_review_only_grounded_news_draft.json")
    base["claim_reviews"][0]["risk_level"] = "blocked"
    res = drp.validate_packet(base)
    assert res["valid"] is False
    assert any(e.startswith("risk_level_blocked") for e in res["errors"])


def test_verdict_pass_with_blocking_issue_is_flagged():
    base = _load("valid_review_only_grounded_news_draft.json")
    base["draft_text"] = "Just go long here and set a price target."
    base["verdict"]["status"] = "local_review_pass"
    res = drp.validate_packet(base)
    assert res["valid"] is False
    assert "verdict_pass_with_blocking_issues" in res["errors"]
