import json
from pathlib import Path
from live_contentops.grounded_research_brief import validate_brief

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "grounded_research_briefs"

def load_fixture(filename):
    with open(FIXTURES_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)

def test_valid_minimal_grounded_news_context():
    brief = load_fixture("valid_minimal_grounded_news_context.json")
    result = validate_brief(brief)
    assert result["packet_status"] == "pass"
    assert len(result["blocked_reasons"]) == 0

def test_invalid_missing_source_url():
    brief = load_fixture("invalid_missing_source_url.json")
    result = validate_brief(brief)
    assert result["packet_status"] == "blocked"
    assert any("source_missing_url" in r for r in result["blocked_reasons"])

def test_invalid_uncited_current_claim():
    brief = load_fixture("invalid_uncited_current_claim.json")
    result = validate_brief(brief)
    assert result["packet_status"] == "blocked"
    assert any("claim_missing_citation" in r for r in result["blocked_reasons"])

def test_invalid_market_signal_claim():
    brief = load_fixture("invalid_market_signal_claim.json")
    result = validate_brief(brief)
    assert result["packet_status"] == "blocked"
    assert any("claim_forbidden_language" in r for r in result["blocked_reasons"])

def test_invalid_artifact_backed_claim_without_artifact():
    brief = load_fixture("invalid_artifact_backed_claim_without_artifact.json")
    result = validate_brief(brief)
    assert result["packet_status"] == "blocked"
    assert any("claim_implies_alpha_output" in r for r in result["blocked_reasons"])

def test_invalid_public_postable_true():
    brief = load_fixture("invalid_public_postable_true.json")
    result = validate_brief(brief)
    assert result["packet_status"] == "blocked"
    assert any("safety_flag_must_be_false:public_postable" in r for r in result["blocked_reasons"])
