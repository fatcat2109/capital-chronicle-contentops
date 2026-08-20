from live_contentops.editorial_portfolio_v1 import (
    ARTICLE_MODE_BREAKING_BRIEF,
    ARTICLE_MODE_STANDARD_NEWS_ANALYSIS,
    ARTICLE_MODE_WEEK_AHEAD_OR_WATCH,
    ARTICLE_MODE_WHAT_THE_MARKET_IS_MISSING,
    DECISION_BREAKING_NEW_STORY,
    select_growth_editorial_mode,
)


def _new_story_novelty() -> dict:
    return {
        "decision": DECISION_BREAKING_NEW_STORY,
        "recommended_article_mode": ARTICLE_MODE_BREAKING_BRIEF,
    }


def test_p0_g3_house_view_semantics_override_legacy_breaking_hint() -> None:
    cluster = {
        "article_mode": "breaking",
        "story_type": "reporting",
        "why_now": (
            "What the market may be missing in the July 28-29 FOMC minutes: the policy "
            "tradeoff is not a one-directional signal, and the document's mechanism, "
            "uncertainty and counter-case matter more than a release headline."
        ),
        "selection_case": "Fresh discovery item with a bounded public evidence path.",
        "needed_evidence": ["Corroborate the limited factual claim from public evidence."],
        "leaf_summaries": [
            "What the market may be missing in the July 28-29 FOMC minutes: the policy "
            "tradeoff is not a one-directional signal, and the document's mechanism, "
            "uncertainty and counter-case matter more than a release headline."
        ],
    }

    result = select_growth_editorial_mode(cluster, _new_story_novelty())

    assert result["mode"] == ARTICLE_MODE_WHAT_THE_MARKET_IS_MISSING
    assert result["reason_code"] == "EXPLICIT_CONSENSUS_CHALLENGE"
    assert result["changes_evidence_or_permission_standards"] is False
    assert result["grants_factual_or_numeric_authority"] is False


def test_p0_g3_upcoming_release_schedule_overrides_legacy_breaking_hint() -> None:
    cluster = {
        "article_mode": "breaking",
        "story_type": "reporting",
        "why_now": (
            "BEA release schedule: the next GDP and personal income-and-outlays releases are "
            "upcoming calendar events; what the data calendar can and cannot establish before "
            "the releases arrive."
        ),
        "selection_case": "Fresh discovery item with a bounded public evidence path.",
        "needed_evidence": ["Corroborate the limited factual claim from public evidence."],
        "leaf_summaries": [
            "BEA release schedule: the next GDP and personal income-and-outlays releases are "
            "upcoming calendar events; what the data calendar can and cannot establish before "
            "the releases arrive."
        ],
    }

    result = select_growth_editorial_mode(cluster, _new_story_novelty())

    assert result["mode"] == ARTICLE_MODE_WEEK_AHEAD_OR_WATCH
    assert result["reason_code"] == "UPCOMING_SCHEDULED_EVENT_WATCH"
    assert result["changes_evidence_or_permission_standards"] is False


def test_p0_g3_analysis_value_overrides_legacy_breaking_hint() -> None:
    cluster = {
        "article_mode": "breaking",
        "story_type": "reporting",
        "why_now": "The July FOMC minutes establish the current policy backdrop.",
        "selection_case": (
            "What the July FOMC minutes reveal about the inflation and labor-market policy "
            "tradeoff, mechanism, context and implications."
        ),
        "needed_evidence": ["Use the official minutes."],
        "leaf_summaries": [
            "The reader value is the policy tradeoff, mechanism, context and implications, "
            "not merely the fact that the minutes were released."
        ],
    }

    result = select_growth_editorial_mode(cluster, _new_story_novelty())

    assert result["mode"] == ARTICLE_MODE_STANDARD_NEWS_ANALYSIS
    assert result["reason_code"] == "EXPLICIT_ANALYTICAL_MAIN_READER_VALUE"


def test_genuine_narrow_new_fact_can_remain_breaking() -> None:
    cluster = {
        "article_mode": "breaking",
        "story_type": "reporting",
        "why_now": "The agency has just published one official decision.",
        "selection_case": "One narrow new official fact merits immediate concise reporting.",
        "needed_evidence": ["Confirm the official decision."],
        "leaf_summaries": ["The agency published the final rule today."],
    }

    result = select_growth_editorial_mode(cluster, _new_story_novelty())

    assert result["mode"] == ARTICLE_MODE_BREAKING_BRIEF
    assert result["reason_code"] == "ROUTED_MODE_NORMALIZED"
