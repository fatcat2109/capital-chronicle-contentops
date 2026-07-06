import pytest

from live_contentops.ai_research_canonical_article_engine_v6 import check_financial_advice


def test_financial_advice_scanner_allows_generic_targets_context():
    check_financial_advice("Policy targets and inflation targets are macro context, not a trade instruction.")


@pytest.mark.parametrize("text", ["buy now", "sell this", "hold position", "price target raised"])
def test_financial_advice_scanner_blocks_explicit_advice_language(text):
    with pytest.raises(ValueError):
        check_financial_advice(text)
